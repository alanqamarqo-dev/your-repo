import os
from Integration_Layer.rag_wrapper import rag_answer

# Hosted LLM knobs
try:
    _AGL_HOSTED_LLM_TOP_K = int(os.environ.get('AGL_HOSTED_LLM_TOP_K', '3'))
except Exception:
    _AGL_HOSTED_LLM_TOP_K = 3

try:
    _AGL_HOSTED_LLM_MAX_TOKENS = int(os.environ.get('AGL_HOSTED_LLM_MAX_TOKENS', '512'))
except Exception:
    _AGL_HOSTED_LLM_MAX_TOKENS = 512

class HostedLLM:
    @staticmethod
    def create_engine(config=None):
        return HostedLLM()

    @staticmethod
    def chat_llm(system_message: str, user_message: str, **kwargs):
        try:
            out = rag_answer(user_message, context=system_message)
            if isinstance(out, dict):
                return out.get("answer") or out.get("text") or ""
            return str(out)
        except Exception:
            # fallback: return empty string
            return ""

    def process_task(self, payload: dict):
        sys = payload.get("system") or "You are HostedLLM"
        usr = payload.get("user") or payload.get("query") or payload.get("text") or ""
        ans = HostedLLM.chat_llm(sys, usr)
        return {"ok": bool(ans), "engine": "hosted_llm:shim", "text": ans}
import os
import hashlib
from typing import List, Dict, Any

from .Ollama_KnowledgeEngine import OllamaKnowledgeEngine


def _prompt_hash(s: str) -> str:
    try:
        return hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]
    except Exception:
        return ""


def chat_llm(messages: List[Dict[str, str]], max_new_tokens: int | None = None, temperature: float = 0.2, top_p: float = 0.9) -> Dict[str, Any]:
    """Lightweight hosted chat wrapper that reuses OllamaKnowledgeEngine.ask.

    messages: list of {'role':..., 'content':...} expected. We build a single prompt by combining system and user.
    Returns a dict with keys: ok, text, prompt_hash
    """
    if not messages:
        return {"ok": False, "error": "no_messages"}

    # combine system + user into a single prompt; prefer system first
    system = next((m['content'] for m in messages if m.get('role') == 'system'), "")
    user = next((m['content'] for m in messages if m.get('role') == 'user'), "")

    full_prompt = (system or "") + "\n\n" + (user or "")

    # apply defaults from env-driven knobs
    if max_new_tokens is None:
        max_new_tokens = int(os.getenv('AGL_HOSTED_LLM_MAX_TOKENS', str(_AGL_HOSTED_LLM_MAX_TOKENS)))

    # Choose provider based on environment. If AGL_LLM_PROVIDER == 'ollama' use HTTP API
    provider = os.getenv('AGL_LLM_PROVIDER', os.getenv('AGL_EXTERNAL_INFO_IMPL', 'ollama')).lower()
    model = os.getenv('AGL_LLM_MODEL') or os.getenv('AGL_OLLAMA_KB_MODEL')
    base = os.getenv('AGL_LLM_BASEURL') or os.getenv('OLLAMA_API_URL')

    resp = None
    if provider in ('ollama', 'http') and base and model:
        # attempt HTTP POST to Ollama-like API, prefer non-streaming JSON
        try:
            import requests, json, time

            def _ollama_url(base: str, endpoint: str = "generate") -> str:
                b = base.rstrip('/')
                if not b.endswith('/api'):
                    b = b + '/api'
                if endpoint not in ("generate", "chat"):
                    endpoint = 'generate'
                return f"{b}/{endpoint}"

            endpoint = os.getenv('AGL_LLM_ENDPOINT', 'generate')
            urls_to_try = [base]
            # try normalized api path as well
            urls_to_try.append(_ollama_url(base, endpoint))

            payload = {"model": model, "prompt": full_prompt, "stream": False, "options": {"temperature": float(os.getenv('AGL_LLM_TEMPERATURE', 0.6)), "top_p": float(os.getenv('AGL_LLM_TOP_P', 0.9))}}
            num_predict = os.getenv('AGL_LLM_NUM_PREDICT') or os.getenv('AGL_LLM_MAX_TOKENS')
            if num_predict:
                try:
                    payload.setdefault('options', {})['num_predict'] = int(num_predict)
                except Exception:
                    pass
            # expose hosted-specific knobs where supported
            try:
                payload.setdefault('options', {})['max_tokens'] = int(os.getenv('AGL_HOSTED_LLM_MAX_TOKENS', str(_AGL_HOSTED_LLM_MAX_TOKENS)))
            except Exception:
                pass
            try:
                payload.setdefault('options', {})['top_k'] = int(os.getenv('AGL_HOSTED_LLM_TOP_K', str(_AGL_HOSTED_LLM_TOP_K)))
            except Exception:
                pass

            max_attempts = int(os.getenv('AGL_HTTP_RETRIES', '3'))
            backoff = float(os.getenv('AGL_HTTP_BACKOFF', '0.5'))
            timeout = int(os.getenv('AGL_HTTP_TIMEOUT', '120'))
            last_exception = None
            resp = None
            for attempt in range(1, max_attempts + 1):
                for url in urls_to_try:
                    try:
                        r = requests.post(url, json=payload, timeout=timeout, stream=True)
                        # if 405 try chat endpoint
                        if r.status_code == 405:
                            chat_url = _ollama_url(base, 'chat')
                            chat_payload = {"model": model, "messages": [{"role": "user", "content": full_prompt}], "stream": False, "options": payload.get('options', {})}
                            r = requests.post(chat_url, json=chat_payload, timeout=timeout, stream=False)

                        r.raise_for_status()
                        # parse single JSON response
                        try:
                            # If streamed/chunked, assemble lines
                            if r.headers.get('Content-Type', '').startswith('text/event-stream') or r.headers.get('Transfer-Encoding', '') == 'chunked' or getattr(r, 'iter_lines', None):
                                try:
                                    body = ''
                                    for chunk in r.iter_lines(decode_unicode=True):
                                        if chunk:
                                            body += (chunk if isinstance(chunk, str) else chunk.decode('utf-8', 'ignore')) + '\n'
                                except Exception:
                                    body = r.text
                            else:
                                body = r.text
                            j = json.loads(body)
                            # prefer response or text
                            if isinstance(j, dict):
                                if 'response' in j and isinstance(j.get('response'), str):
                                    ans = j.get('response', '').strip()
                                    resp = {"ok": True, "text": ans, "answer": {"text": ans, "citations": [], "confidence": None}, "raw_json": j}
                                elif 'text' in j and isinstance(j.get('text'), str):
                                    ans = j.get('text', '').strip()
                                    resp = {"ok": True, "text": ans, "answer": {"text": ans, "citations": [], "confidence": None}, "raw_json": j}
                                else:
                                    resp = {"ok": True, "text": str(j), "answer": {"text": str(j), "citations": [], "confidence": None}, "raw_json": j}
                            else:
                                resp = {"ok": True, "text": str(j), "answer": {"text": str(j), "citations": [], "confidence": None}}
                            break
                        except Exception:
                            # fallback: if r has text attribute use it
                            try:
                                body = getattr(r, 'text', '')
                            except Exception:
                                body = ''
                            resp = {"ok": True, "text": body, "answer": {"text": body, "citations": [], "confidence": None}}
                            break
                    except Exception as e:
                        last_exception = e
                        continue
                if resp is not None:
                    break
                import time
                time.sleep(min(backoff * attempt, 8.0))

            if resp is None:
                if last_exception is not None:
                    resp = {"ok": False, "error": f'http_provider_all_attempts_failed: {last_exception}'}
                else:
                    resp = {"ok": False, "error": 'http_provider_all_attempts_failed'}
        except Exception as e:
            # fall back to local engine wrapper
            resp = {"ok": False, "error": f"http_provider_error: {e}"}

    if not resp or not isinstance(resp, dict) or resp.get('ok') is False:
        # fallback to existing OllamaKnowledgeEngine wrapper (CLI or HTTP inside)
        try:
            eng = OllamaKnowledgeEngine()
            resp = eng.ask(full_prompt, context=None, system_prompt=system or None, cache=(os.getenv('AGL_OLLAMA_KB_CACHE_ENABLE', '1') in ('1','true')))
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # Normalize common engine return shapes: prefer resp['answer']['text'] (turn contract), then resp['text'] or resp['answer']
    text = ''
    if isinstance(resp, dict):
        if isinstance(resp.get('answer'), dict) and resp['answer'].get('text'):
            text = resp['answer'].get('text')
        elif resp.get('text'):
            text = resp.get('text')
        elif resp.get('answer'):
            text = str(resp.get('answer'))
        else:
            # try nested working.calls
            wc = resp.get('working') or {}
            calls = wc.get('calls') if isinstance(wc, dict) else None
            if calls and isinstance(calls, list) and calls:
                first = calls[0].get('engine_result') or {}
                text = first.get('text') or first.get('answer') or ''
    else:
        text = str(resp)
    text = str(text or '')
    return {"ok": True, "text": text, "prompt_hash": _prompt_hash(full_prompt), "engine_result": resp}
