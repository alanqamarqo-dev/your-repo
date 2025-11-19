"""Minimal, stable FastAPI server for local development.

This file intentionally keeps a small, single app instance and
normalizes backend engine responses so the UI can always render
`reply`/`reply_text` fields without crashing.
"""

import os
import sys
import uuid
import json
import time
import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

# expose project root for imports
sys.path.append(os.getcwd())

# Try importing the integration layer; provide safe fallbacks for local dev
try:
    from Integration_Layer.Conversation_Manager import (
        start_session, create_session, append_turn, auto_route_and_respond # type: ignore
    )
except Exception:
    def start_session(sid: str):
        return {'session_id': sid, 'history': []}
    def create_session(sid: str):
        return {'session_id': sid, 'history': []}
    def append_turn(sid: str, user: str, resp: dict):
        return None
    def auto_route_and_respond(sid: str, text: str) -> dict:
        return {'text': 'backend not ready', 'engine': 'noop'}


app = FastAPI(title="AGL Dev Server")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

WEB_DIR = os.path.join(os.getcwd(), 'web')
if not os.path.isdir(WEB_DIR):
    os.makedirs(WEB_DIR, exist_ok=True)
app.mount('/static', StaticFiles(directory=WEB_DIR), name='static')

# Directory to persist per-session JSON files
SESSIONS_DIR = os.path.join(os.getcwd(), 'sessions')
if not os.path.isdir(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR, exist_ok=True)

# Setup simple request/latency logger
LOGS_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    handlers=[logging.FileHandler(os.path.join(LOGS_DIR, 'requests.log'), encoding='utf-8'), logging.StreamHandler()]
)

# Try to load runtime config flags from config.yaml when available
_CONFIG = {}
try:
    import yaml
    cfg_path = os.path.join(os.getcwd(), 'config.yaml')
    if os.path.exists(cfg_path):
        with open(cfg_path, 'r', encoding='utf-8') as f:
            _CONFIG = yaml.safe_load(f) or {}
except Exception:
    _CONFIG = {}


def _write_session_file(session_id: str):
    """Persist session data (as returned by create_session) to a JSON file.

    Writes atomically to sessions/<session_id>.json (uses a tmp file + replace).
    """
    try:
        s = None
        try:
            s = create_session(session_id)
        except Exception:
            s = None
        if not s:
            # If there's no session object available, write a minimal one
            s = {'session_id': session_id, 'history': []}
        # defensive fix: convert common UTF-8->latin1 mojibake back to UTF-8
        def _attempt_fix_str(st: str):
            try:
                if not isinstance(st, str):
                    return st
                # if string contains high-latin characters (common sign of mojibake)
                if any(0xC0 <= ord(c) <= 0xFF for c in st):
                    try:
                        fixed = st.encode('latin-1').decode('utf-8')
                        # if fixed contains Arabic characters, accept it
                        if any(0x0600 <= ord(ch) <= 0x06FF for ch in fixed):
                            return fixed
                    except Exception:
                        pass
                return st
            except Exception:
                return st

        def _fix_mojibake(obj):
            if isinstance(obj, dict):
                return {k: _fix_mojibake(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_fix_mojibake(v) for v in obj]
            if isinstance(obj, str):
                return _attempt_fix_str(obj)
            return obj

        try:
            s = _fix_mojibake(s)
        except Exception:
            pass
        # ensure ASCII is not forced and preserve Unicode
        out_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        tmp_path = out_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
        # atomic replace
        try:
            os.replace(tmp_path, out_path)
        except Exception:
            # fallback to rename if replace not available
            os.remove(out_path) if os.path.exists(out_path) else None
            os.rename(tmp_path, out_path)
    except Exception:
        # Do not fail the request if persisting the session fails; log and continue
        try:
            print('[WARN] Failed to write session file for', session_id, traceback.format_exc())
        except Exception:
            pass


def json_response(content: Any, status_code: int = 200):
    body = json.dumps(content, ensure_ascii=False)
    return Response(content=body, status_code=status_code, media_type='application/json; charset=utf-8')


@app.get('/health')
async def health():
    # reflect some runtime flags if present
    features = _CONFIG.get('features', {}) if isinstance(_CONFIG, dict) else {}
    return json_response({"ok": True, "service": "AGL Chat", "status": "healthy", "features": features})


@app.get('/api/system/status')
async def api_system_status():
    """Lightweight system status that includes engine monitoring stats when available.

    Returns: { ok: bool, engines: {...} }
    """
    try:
        try:
            from infra.engine_monitor import system_status as _system_status  # type: ignore
        except Exception:
            _system_status = None
        if _system_status is None:
            return json_response({"ok": False, "reason": "monitor-not-available"}, status_code=200)
        st = _system_status()
        return json_response({"ok": True, "engines": st.get('engines', st) if isinstance(st, dict) else st})
    except Exception as e:
        return json_response({"ok": False, "error": str(e)}, status_code=500)


@app.get('/admin/flags')
async def get_flags():
    """Return current runtime feature flags (from in-memory config).

    This endpoint is intended for the UI to show current toggles.
    """
    features = _CONFIG.get('features', {}) if isinstance(_CONFIG, dict) else {}
    return json_response({"ok": True, "features": features})


@app.post('/admin/flags')
async def set_flags(req: Request):
    """Update runtime feature flags. Body should be JSON with either
    {"features": {...}} or a plain mapping of flag->value.

    The server attempts to persist `config.yaml` when possible.
    """
    # Ensure we refer to the module-level _CONFIG variable
    global _CONFIG
    try:
        data = await req.json()
    except Exception:
        data = {}
    # Support both {"features": {...}} and direct mapping
    features = data.get('features') if isinstance(data.get('features'), dict) else data if isinstance(data, dict) else {}
    if not isinstance(_CONFIG, dict):
        # reinitialize
        try:
            _CONFIG = {}
        except Exception:
            pass
    _CONFIG['features'] = features
    # try to persist to config.yaml if possible
    try:
        cfg_path = os.path.join(os.getcwd(), 'config.yaml')
        try:
            import yaml
            with open(cfg_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(_CONFIG, f, sort_keys=False, allow_unicode=True)
        except Exception:
            # fallback: write as JSON if PyYAML not available
            with open(cfg_path, 'w', encoding='utf-8') as f:
                json.dump(_CONFIG, f, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception('failed to persist config.yaml')
    return json_response({"ok": True, "features": _CONFIG.get('features', {})})


def _timed_call_and_log(name: str, func, *args, **kwargs):
    start = time.perf_counter()
    try:
        res = func(*args, **kwargs)
    except Exception as e:
        end = time.perf_counter()
        dur = int((end - start) * 1000)
        logging.exception("%s failed: %s (latency_ms=%d)", name, e, dur)
        raise
    end = time.perf_counter()
    dur = int((end - start) * 1000)
    # Basic structured log for latency and outcome
    try:
        engine = (res or {}).get('engine') if isinstance(res, dict) else None
    except Exception:
        engine = None
    logging.info("endpoint=%s latency_ms=%d engine=%s", name, dur, engine)
    return res, dur



@app.get('/')
async def index():
    index_path = os.path.join(WEB_DIR, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html')
    return json_response({"ok": False, "error": "index_missing"}, status_code=404)


def _pick_text(d: dict):
    data_field = d.get('data') if isinstance(d.get('data'), dict) else None
    return (
        d.get('text') or
        d.get('reply_text') or
        d.get('reply') or
        d.get('message') or
        d.get('description') or
        (data_field.get('text') if data_field and data_field.get('text') else None)
    )


def _clean_reply(s: str) -> str:
    if not s:
        return s
    try:
        import re
        text = str(s).lstrip().replace('\u00a0', ' ')
        text = re.sub(r"^\([^)]*\)\s*", '', text)
        parts = [p.strip() for p in text.split('|') if p and p.strip()]
        seen = set(); uniq = []
        for p in parts:
            if p in seen: continue
            seen.add(p); uniq.append(p)
        if uniq:
            text = ' | '.join(uniq)
        if len(text) > 800:
            text = text[:800].rsplit(' ', 1)[0] + '...'
        return text
    except Exception:
        return str(s)[:800]


@app.post('/chat')
async def chat(req: Request):
    try:
        data = await req.json()
    except Exception:
        data = {}
    text = (data.get('text') or '').strip()
    sid = data.get('session_id') or f'web_{uuid.uuid4().hex[:8]}'

    start_session(sid)
    # persist initial session state to disk
    try:
        _write_session_file(sid)
    except Exception:
        pass
    # Debug: print raw incoming text (repr) so we can see invisible characters/encoding
    try:
        print('[INCOMING_TEXT_REPR]', repr(text))
        # print codepoints for diagnosis (trim long inputs)
        cps = ' '.join(str(ord(c)) for c in (text or '')[:80])
        if cps:
            print('[INCOMING_TEXT_CODEPOINTS]', cps)
    except Exception:
        pass
    # Quick client-side intent guard: handle simple greetings locally to
    # avoid routing them to heavyweight knowledge engines which may return
    # unrelated answers for very short salutations.
    try:
        tl = text.lower()
    except Exception:
        tl = text
    if tl and any(g in tl for g in ("اهلا", "أهلا", "مرحبا", "السلام", "هاي", "hello", "hi")):
        greet = "مرحبا! كيف يمكنني مساعدتك اليوم؟"
        append_turn(sid, text, {"ok": True, "text": greet})
        try:
            _write_session_file(sid)
        except Exception:
            pass
        return json_response({
            "ok": True,
            "session_id": sid,
            "reply": greet,
            "reply_text": greet,
            "meta": {"engine": "local", "intent": "greeting"},
            "raw": {"text": greet}
        })
    if not text:
        return json_response({"ok": True, "session_id": sid, "reply": "أرسل رسالة..."})

    try:
        # call the integration layer through timed wrapper so latency is logged
        resp, dur = _timed_call_and_log('auto_route_and_respond', auto_route_and_respond, sid, text)
    except Exception as e:
        tb = traceback.format_exc()
        print('[ERROR] auto_route_and_respond exception:\n', tb)
        return json_response({"ok": False, "error": "backend_error", "detail": str(e)}, status_code=500)

    try:
        candidate = _pick_text(resp or {}) or "تم — لكن لم يصل نص قابل للعرض."
        candidate = _clean_reply(candidate)
    except Exception:
        candidate = (resp or {}).get('text') or (resp or {}).get('reply_text') or "لم أفهم، هل يمكنك التوضيح؟"

    reply = (resp or {}).get('reply_text') or (resp or {}).get('text') or (resp or {}).get('reply') or candidate
    # NOTE: Conversation_Manager / Integration_Layer is responsible for appending
    # turns and persisting session history to avoid duplicate entries. The server
    # keeps an initial session write and persists greeting turns locally, but
    # should not double-append the main engine responses here.

    out = {
        "ok": True,
        "session_id": sid,
        "reply": reply,
        "reply_text": candidate,
        "meta": {"engine": (resp or {}).get('engine'), "intent": (resp or {}).get('intent')},
        "raw": resp or {}
    }
    try:
        print('[ROUTE]', out.get('meta', {}).get('intent'), '->', out.get('meta', {}).get('engine'), 'ctx:', text[:140])
    except Exception:
        pass
    return json_response(out)


@app.post('/process')
async def process(req: Request):
    """General /process endpoint: accepts {'text','session_id'} and returns {answer,sources,meta} with timing."""
    try:
        data = await req.json()
    except Exception:
        data = {}
    text = (data.get('text') or '').strip()
    sid = data.get('session_id') or f'web_{uuid.uuid4().hex[:8]}'
    if not text:
        return json_response({"ok": False, "error": "no_text"}, status_code=400)
    try:
        resp, dur = _timed_call_and_log('process.auto_route', auto_route_and_respond, sid, text)
    except Exception as e:
        return json_response({"ok": False, "error": "backend_error", "detail": str(e)}, status_code=500)
    return json_response({"ok": True, "session_id": sid, "reply": resp.get('text') if isinstance(resp, dict) else str(resp), "meta": resp.get('meta', {}) if isinstance(resp, dict) else {}, "engine": resp.get('engine') if isinstance(resp, dict) else None, "latency_ms": dur, "raw": resp})


# RAG answer endpoint (tries to use Integration_Layer.rag_wrapper if available)
try:
    from Integration_Layer.rag_wrapper import rag_answer  # type: ignore
except Exception:
    def rag_answer(query: str):
        # minimal fallback: return a canned response with empty sources
        return {"answer": "RAG not available", "sources": [], "engine": "noop"}


@app.post('/rag/answer')
async def rag_answer_endpoint(req: Request):
    try:
        data = await req.json()
    except Exception:
        data = {}
    q = (data.get('query') or data.get('text') or '').strip()
    if not q:
        return json_response({"ok": False, "error": "no_query"}, status_code=400)
    try:
        res, dur = _timed_call_and_log('rag_answer', rag_answer, q)
    except Exception as e:
        return json_response({"ok": False, "error": "rag_error", "detail": str(e)}, status_code=500)
    return json_response({"ok": True, "query": q, "answer": res.get('answer') if isinstance(res, dict) else res, "sources": res.get('sources') if isinstance(res, dict) else [], "engine": res.get('engine') if isinstance(res, dict) else None, "latency_ms": dur})


@app.post('/improve/run-once')
async def run_improve_once(req: Request):
    # Try calling a known self-improvement entrypoint if available
    try:
        data = await req.json()
    except Exception:
        data = {}
    # optional: accept mode or params
    params = data or {}
    try:
        # try to import a standard hook
        from Learning_System.Self_Improver import run_once  # type: ignore
        res, dur = _timed_call_and_log('self_improve.run_once', run_once, params)
        return json_response({"ok": True, "result": res, "latency_ms": dur})
    except Exception:
        # fallback: simulate a no-op improvement that returns success if flag enabled
        enabled = _CONFIG.get('features', {}).get('enable_self_improvement', False) if isinstance(_CONFIG, dict) else False
        if not enabled:
            return json_response({"ok": False, "error": "self_improvement_disabled"}, status_code=400)
        logging.info("simulate self-improvement run (no real impl)")
        return json_response({"ok": True, "result": "simulated", "note": "no real self-improvement implementation available locally"})


@app.get('/memory/stats')
async def memory_stats():
    # Basic fallback: count session files and sum sizes
    try:
        files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.json')]
        total = 0
        for f in files:
            total += os.path.getsize(os.path.join(SESSIONS_DIR, f))
        return json_response({"ok": True, "sessions": len(files), "total_bytes": total})
    except Exception as e:
        return json_response({"ok": False, "error": str(e)}, status_code=500)


@app.post('/meta/evaluate')
async def meta_evaluate(req: Request):
    try:
        data = await req.json()
    except Exception:
        data = {}
    plan = data.get('plan') or data.get('text') or ''
    if not plan:
        return json_response({"ok": False, "error": "no_plan"}, status_code=400)
    try:
        from Integration_Layer.Meta_Cognition import evaluate  # type: ignore
        res, dur = _timed_call_and_log('meta.evaluate', evaluate, plan)
        return json_response({"ok": True, "evaluation": res, "latency_ms": dur})
    except Exception:
        # simple heuristic fallback: return a neutral score
        return json_response({"ok": True, "evaluation": {"score": 0.5, "notes": "fallback: no meta-cognition impl"}})


@app.get('/history/{session_id}')
async def history(session_id: str):
    # Prefer reading persisted session file if present to reflect exactly what was stored
    try:
        path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                s = json.load(f)
            return json_response({"ok": True, "session_id": session_id, "history": s.get('history', [])})
    except Exception:
        # fall back to in-memory/Integration layer
        pass
    s = create_session(session_id)
    return json_response({"ok": True, "session_id": session_id, "history": s.get('history', [])})


if __name__ == '__main__':
    try:
        import uvicorn
        uvicorn.run('server:app', host='127.0.0.1', port=8000, reload=True)
    except Exception as e:
        print('Failed to start uvicorn:', e)
 
