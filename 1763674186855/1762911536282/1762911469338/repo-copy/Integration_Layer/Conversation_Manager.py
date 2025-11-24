# -- coding: utf-8 --
import json
import os
from datetime import datetime, timezone
from Integration_Layer.Intent_Recognizer import detect_intent
from Integration_Layer.Domain_Router import route_pipeline
from Integration_Layer.Pipeline_Orchestrator import execute_pipeline
from Integration_Layer.Output_Formatter import normalize

SESSIONS_DIR = os.path.join('artifacts', 'chat_sessions')
os.makedirs(SESSIONS_DIR, exist_ok=True)

# lightweight in-memory sessions for orchestrator-backed flows
_SESSIONS = {}


def _session_path(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, f'session_{session_id}.json')


def create_session(session_id: str) -> dict:
    path = _session_path(session_id)
    # if missing or empty file -> create new
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        s = {'id': session_id, 'created_at': datetime.now(timezone.utc).isoformat(), 'history': []}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
        return s
    # try to read, on JSON errors recreate clean session
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        s = {'id': session_id, 'created_at': datetime.now(timezone.utc).isoformat(), 'history': []}
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
        try:
            os.replace(tmp, path)
        except Exception:
            # best-effort fallback
            with open(path, 'w', encoding='utf-8') as f2:
                json.dump(s, f2, ensure_ascii=False, indent=2)
        return s


def start_session(session_id: str):
    # create persisted session and in-memory session
    s = create_session(session_id)
    _SESSIONS[session_id] = s
    return s


def auto_route(session_id: str, user_text: str, extra: dict | None = None):
    # ensure session exists
    s = _SESSIONS.get(session_id) or start_session(session_id)
    # detect intent and route
    intent = detect_intent(user_text)
    pipeline = route_pipeline(intent)

    ctx = {"text": user_text, "intent": intent, "extra": extra or {}}
    try:
        agent_resp = execute_pipeline(pipeline, ctx)
    except Exception as e:
        agent_resp = {"ok": False, "error": str(e)}

    # normalize envelope
    try:
        agent_resp = normalize(agent_resp if isinstance(agent_resp, dict) else {"result": agent_resp})
    except Exception:
        agent_resp = {"ok": False, "error": "normalization_failed", "result": str(agent_resp)}

    turn = {'ts': datetime.now(timezone.utc).isoformat(), 'user': user_text, 'agent': agent_resp, 'intent': intent}
    s['history'].append(turn)
    # persist to disk as well
    path = _session_path(session_id)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return agent_resp


def append_turn(session_id: str, user_text: str, agent_resp: dict) -> dict:
    path = _session_path(session_id)
    s = create_session(session_id)
    turn = {'ts': datetime.now(timezone.utc).isoformat(), 'user': user_text, 'agent': agent_resp}
    s['history'].append(turn)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    # Also persist a short-term linear memory file that keeps recent user utterances
    try:
        mem_path = os.path.join('artifacts', 'session_memory.txt')
        os.makedirs(os.path.dirname(mem_path), exist_ok=True)
        with open(mem_path, 'a', encoding='utf-8') as mf:
            mf.write(f"[{session_id}] {user_text}\n")
    except Exception:
        # best-effort: don't break main flow if memory append fails
        pass
    return s


def last_turn(session_id: str) -> dict | None:
    path = _session_path(session_id)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        s = json.load(f)
    if not s.get('history'):
        return None
    return s['history'][-1]


# --- Simple auto-router that dispatches to Core_Engines based on NLP intent ---
def auto_route_and_respond(session_id: str, user_text: str) -> dict:
    """Route the user_text using the Domain_Router and include session history in the context.

    This wrapper ensures history is passed to routing so engines can be contextual.
    Returns a dict with keys: engine, intent, output, reply_text
    """
    # ensure session exists and load history
    s = _SESSIONS.get(session_id) or create_session(session_id)
    history = s.get('history', []) if isinstance(s, dict) else []

    # prepare short recent context lines (user + agent) to pass to router
    try:
        ctx = recent_context(session_id)
    except Exception:
        ctx = []

    out = {}
    try:
        # Domain_Router.route expects (text, context)
        from Integration_Layer import Domain_Router
        out = Domain_Router.route(user_text, context=ctx)
        # Debug: if router returned no engine or no textual reply, log raw output for diagnosis
        try:
            if not isinstance(out, dict) or out.get('engine') is None or not out.get('reply_text'):
                print('[CM DEBUG] Domain_Router returned:', repr(out))
        except Exception:
            print('[CM DEBUG] Domain_Router returned (uninspectable)')
    except Exception:
        # fallback to simple echo via NLP with robust handling
        try:
            from Core_Engines.NLP_Advanced import NLPAdvancedEngine
            nlp = NLPAdvancedEngine()
            reply = None
            try:
                resp = nlp.respond(user_text)
                if isinstance(resp, dict):
                    reply = resp.get('text') or resp.get('reply') or resp.get('answer')
                elif isinstance(resp, str):
                    reply = resp
            except Exception:
                reply = None
            reply = reply or str(user_text)
            out = {"engine": "NLP_Advanced", "intent": "fallback", "output": {"reply": reply}, "reply_text": reply}
        except Exception:
            out = {"engine": None, "intent": "unknown", "output": None, "reply_text": str(user_text)}

    # append turn and persist
    # Normalize/clean the returned payload to avoid noisy or repeated replies
    try:
        def _clean_reply_text(s: str) -> str:
            try:
                if not s:
                    return s
                import re
                text = str(s).strip()
                # strip leading parenthetical status like (neutral)
                text = re.sub(r"^\([^)]*\)\s*", '', text)
                # split on '|' and dedupe preserving order
                parts = [p.strip() for p in text.split('|') if p and p.strip()]
                seen = set(); uniq = []
                for p in parts:
                    if p in seen: continue
                    seen.add(p); uniq.append(p)
                if uniq:
                    text = ' | '.join(uniq)
                # truncate long outputs
                if len(text) > 600:
                    text = text[:600].rsplit(' ', 1)[0] + '...'
                return text
            except Exception:
                return str(s)[:600]

        if isinstance(out, dict):
            # prefer common textual fields used by different engines
            candidate = out.get('reply_text') or out.get('text') or None
            # try nested output fields safely
            if candidate is None:
                od = out.get('output') if isinstance(out.get('output'), dict) else None
                if od:
                    candidate = od.get('reply') or od.get('text') or None

            if candidate:
                cleaned = _clean_reply_text(candidate)
                out['reply_text'] = cleaned
                out['text'] = cleaned
            else:
                # ensure we always provide a user-visible reply_text so the UI
                # doesn't show a generic 'empty reply' message. Attach the raw
                # engine payload under 'raw' for debugging/inspection.
                try:
                    original = dict(out)  # shallow copy of the engine payload
                except Exception:
                    original = {'payload': str(out)}
                fallback = "لم أتمكن من توليد رد نصي واضح. راجع حقل 'raw' للمزيد."
                out['reply_text'] = fallback
                out['text'] = fallback
                # keep the original payload for diagnostics
                out['raw'] = original
                try:
                    _intent = out.get('intent') if isinstance(out, dict) else None
                    print(f"[Conversation_Manager] missing textual reply, attached raw payload for session. intent={_intent}")
                except Exception:
                    pass
    except Exception:
        pass

    # Relevance check: ensure the engine reply is reasonably related to the user question.
    try:
        def _tok_set(s: str):
            return set([t for t in (s or '').lower().split() if t])

        user_tokens = _tok_set(user_text)
        reply_tokens = _tok_set(out.get('reply_text') or out.get('text') or '')
        overlap = 0.0
        if user_tokens and reply_tokens:
            overlap = len(user_tokens & reply_tokens) / float(len(user_tokens))

        # If low overlap for informational intents, try an NLP fallback to avoid unrelated answers
        intent = out.get('intent') or None
        if (intent == 'ask_info' or intent is None) and overlap < 0.15:
            try:
                from Core_Engines.NLP_Advanced import NLPAdvancedEngine
                nlp = NLPAdvancedEngine()
                resp = nlp.respond(user_text)
                if isinstance(resp, dict):
                    alt = resp.get('text') or resp.get('reply') or None
                else:
                    alt = str(resp)
                if alt:
                    out['reply_text'] = alt
                    out['text'] = alt
                    out['engine'] = out.get('engine') or 'NLP_Advanced'
                    out['intent'] = out.get('intent') or 'fallback'
                    out['note'] = 'used_nlp_fallback_due_to_low_relevance'
            except Exception:
                pass
    except Exception:
        pass

    # OpenAI fallback: if the router/engines returned no usable text, try the OpenAI KB engine
    try:
        # Consider a broader set of signals that indicate the engine returned
        # an unhelpful placeholder so we should try a fallback generator.
        reply_txt = out.get('reply_text') if isinstance(out.get('reply_text'), str) else ''
        raw_payload = out.get('raw') if isinstance(out.get('raw'), dict) else {}
        BAD_PLACEHOLDERS = [
            "لم أتمكن",
            "لم أجد معلومات",
            "لم أجد",
            "no_evidence",
            "لا توجد معلومات",
            "لا أجد",
        ]
        need_fallback = (
            (out.get('engine') is None)
            or (isinstance(reply_txt, str) and any(ph in reply_txt for ph in BAD_PLACEHOLDERS))
            or (isinstance(raw_payload, dict) and any(ph in json.dumps(raw_payload, ensure_ascii=False) for ph in BAD_PLACEHOLDERS))
        )
        if need_fallback:
            openai_ok = False
            try:
                from Core_Engines.OpenAI_KnowledgeEngine import OpenAIKnowledgeEngine
                oeng = OpenAIKnowledgeEngine()
                resp = oeng.ask(user_text, context=ctx if isinstance(ctx, list) else None)
                if isinstance(resp, dict) and resp.get('ok') and resp.get('text'):
                    out['reply_text'] = resp.get('text')
                    out['text'] = resp.get('text')
                    out['engine'] = 'OpenAI_KB'
                    note = out.get('note') or ''
                    out['note'] = (note + ';') + 'used_openai_fallback' if note else 'used_openai_fallback'
                    openai_ok = True
            except Exception:
                openai_ok = False

            # If OpenAI fallback is not available or returned nothing, try a local NLP fallback as a safe fallback
            if not openai_ok:
                try:
                    from Core_Engines.NLP_Advanced import NLPAdvancedEngine
                    nlp = NLPAdvancedEngine()
                    r = nlp.respond(user_text)
                    alt = None
                    if isinstance(r, dict):
                        alt = r.get('text') or r.get('reply') or r.get('answer')
                    elif isinstance(r, str):
                        alt = r
                    if alt:
                        out['reply_text'] = alt
                        out['text'] = alt
                        out['engine'] = out.get('engine') or 'NLP_Advanced'
                        note = out.get('note') or ''
                        out['note'] = (note + ';') + 'used_nlp_fallback_after_openai' if note else 'used_nlp_fallback_after_openai'
                except Exception:
                    pass
    except Exception:
        pass

    append_turn(session_id, user_text, out)
    return out




def recent_context(session_id: str, k: int = 8):
    """Retrieve last k items from session history as a short textual context list.

    Returns a list of strings (user and agent texts interleaved) up to k items.
    """
    try:
        s = create_session(session_id)
    except Exception:
        return []
    hist = s.get('history', [])[-k:]
    ctx = []
    for t in hist:
        u = t.get('user')
        a = t.get('agent', {})
        if u:
            ctx.append(str(u))
        if isinstance(a, dict):
            txt = a.get('text') or a.get('reply')
            if not txt:
                out = a.get('output')
                if isinstance(out, dict):
                    txt = out.get('reply') or out.get('text')
            if txt:
                ctx.append(str(txt))
    return [c for c in ctx if c][:k]
