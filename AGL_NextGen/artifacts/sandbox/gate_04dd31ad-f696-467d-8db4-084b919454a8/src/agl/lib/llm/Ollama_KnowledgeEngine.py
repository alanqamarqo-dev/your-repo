# === AGL auto-injected knobs (idempotent) ===
import os
import json
import time
import hashlib
import subprocess
from typing import Any, Dict, List, Optional, Union

def _to_int(name: str, default: int) -> int:
    """
    Helper to safely convert environment variables to integers.
    """
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default

_AGL_PREVIEW_120 = _to_int('AGL_PREVIEW_120', 120)
_AGL_OLLAMA_TOP_K = _to_int('AGL_OLLAMA_TOP_K', 3)

from agl.lib.integration.rag_wrapper import rag_answer

class LocalKnowledgeEngine:
    """
    Ollama Knowledge Engine.
    
    This engine serves as an adapter for local LLM inference using Ollama.
    It supports RAG (Retrieval-Augmented Generation) and standard chat.
    
    Resonance Status:
    - Complexity (V): Low (Wrapper).
    - Coherence (E): High (Cleaned & Documented).
    """
    
    def __init__(self, **kwargs):
        self.name = 'Ollama_KnowledgeEngine'

    @staticmethod
    def create_engine(config: Optional[Dict[str, Any]] = None) -> 'LocalKnowledgeEngine':
        """Factory method to create the engine instance."""
        return LocalKnowledgeEngine()

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task payload (query/text) using the local Ollama model.
        
        Args:
            payload: Dict containing 'query', 'text', or 'user' keys.
            
        Returns:
            Dict with 'ok', 'engine', and 'text' (or 'error').
        """
        q = payload.get('query') or payload.get('text') or payload.get('user') or ''
        ctx = payload.get('context')
        
        # Mock mode check
        if os.getenv('AGL_OLLAMA_KB_MOCK', '0') == '1':
            return {
                'ok': True, 
                'engine': 'ollama:mock', 
                'text': f'محاكاة: {str(q)[:_AGL_PREVIEW_120]}'
            }
            
        try:
            # Call RAG wrapper (which calls Hosted_LLM -> Ollama)
            out = rag_answer(q, context=ctx)
            
            if isinstance(out, dict):
                return {
                    'ok': True, 
                    'engine': 'ollama', 
                    'text': out.get('answer') or out.get('text')
                }
            return {'ok': True, 'engine': 'ollama', 'text': str(out)}
            
        except Exception as e:
            return {'ok': False, 'engine': 'ollama', 'error': str(e)}
    _AGL_OLLAMA_TOP_K = 3
from .turn_contract import make_turn, normalize_engine_response
SYSTEM_PROMPT = 'أنت محرك معرفة: استجب بإجابة موجزة وموثوقة. أعِد نُسخة JSON مع الحقول: {"ok": true/false, "text": "...", "sources": [...]} ولا تخرج عن JSON.'
class LocalKnowledgeEngine:
    def __init__(self, model: Optional[str]=None, cache_dir: Optional[str]=None):
        self.mock = os.getenv('AGL_OLLAMA_KB_MOCK', '0') in ('1', 'true', 'True')
        self.model = model or os.getenv('AGL_OLLAMA_KB_MODEL') or os.getenv('AGL_EXTERNAL_INFO_MODEL') or 'ollama/qwen2.5'
        self.cache_dir = cache_dir or os.getenv('AGL_OLLAMA_KB_CACHE', 'artifacts/ollama_kb_cache')
        self.cache_enabled = os.getenv('AGL_OLLAMA_KB_CACHE_ENABLE', '1') in ('1', 'true', 'True')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.api_url = os.getenv('OLLAMA_API_URL') or os.getenv('AGL_LLM_BASEURL')
        self.api_endpoint = os.getenv('AGL_LLM_ENDPOINT', 'generate')
    def _cache_path(self, q: str) -> str:
        h = hashlib.sha256(q.encode('utf-8')).hexdigest()[:32]
        return os.path.join(self.cache_dir, f'{h}.json')
    def _call_model_via_http(self, prompt: str) -> Dict[str, Any]:
        try:
            import requests
        except Exception as e:
            return {'ok': False, 'error': f'requests not available: {e}'}
        try:
            if not self.api_url:
                return {'ok': False, 'error': 'no api_url configured'}
            def _ollama_url(base: str, endpoint: str='generate') -> str:
                b = base.rstrip('/')
                if not b.endswith('/api'):
                    b = b + '/api'
                if endpoint not in ('generate', 'chat'):
                    endpoint = 'generate'
                return f'{b}/{endpoint}'
            endpoint = self.api_endpoint or 'generate'
            url = _ollama_url(self.api_url, endpoint)
            payload = {'model': os.getenv('AGL_LLM_MODEL', self.model), 'prompt': prompt, 'stream': False, 'options': {'temperature': float(os.getenv('AGL_LLM_TEMPERATURE', 0.6)), 'top_p': float(os.getenv('AGL_LLM_TOP_P', 0.9))}}
            num_predict = os.getenv('AGL_LLM_NUM_PREDICT') or os.getenv('AGL_LLM_MAX_TOKENS')
            if num_predict:
                try:
                    payload.setdefault('options', {})['num_predict'] = int(num_predict)
                except Exception:
                    pass
            try:
                payload.setdefault('options', {})['top_k'] = int(os.getenv('AGL_OLLAMA_TOP_K', str(_AGL_OLLAMA_TOP_K)))
            except Exception:
                pass
            r = requests.post(url, json=payload, timeout=int(os.getenv('AGL_HTTP_TIMEOUT', 120)))
            if r.status_code == 405:
                url = _ollama_url(self.api_url, 'chat')
                chat_payload = {'model': payload['model'], 'messages': [{'role': 'user', 'content': prompt}], 'stream': False, 'options': payload.get('options', {})}
                r = requests.post(url, json=chat_payload, timeout=int(os.getenv('AGL_HTTP_TIMEOUT', 120)))
            r.raise_for_status()
            try:
                j = r.json()
                if isinstance(j, dict):
                    if 'response' in j and isinstance(j.get('response'), str):
                        return {'ok': True, 'text': (j.get('response') or '').strip(), 'raw_json': j}
                    if 'text' in j and isinstance(j.get('text'), str):
                        return {'ok': True, 'text': (j.get('text') or '').strip(), 'raw_json': j}
                return {'ok': True, 'text': str(j), 'raw_json': j}
            except Exception:
                txt = r.text
                return {'ok': True, 'text': txt.strip(), 'sources': []}
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    def _call_model_via_cli(self, prompt: str) -> Dict[str, Any]:
        try:
            proc = subprocess.run(['ollama', 'run', self.model, '--format', 'json'], input=prompt, text=True, capture_output=True, timeout=300)
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            if proc.returncode != 0 and (not out):
                return {'ok': False, 'error': f'ollama exit {proc.returncode}: {err}'}
            try:
                parsed = json.loads(out)
                if isinstance(parsed, dict):
                    def _unwrap(s: str) -> str:
                        s = s.strip()
                        if s.startswith('{') or s.startswith('['):
                            try:
                                inner = json.loads(s)
                                if isinstance(inner, dict):
                                    for v in inner.values():
                                        if isinstance(v, str) and v.strip():
                                            return v.strip()
                                    return str(inner)
                                return str(inner)
                            except Exception:
                                pass
                        try:
                            import ast
                            inner = ast.literal_eval(s)
                            if isinstance(inner, dict):
                                for v in inner.values():
                                    if isinstance(v, str) and v.strip():
                                        return v.strip()
                                return str(inner)
                        except Exception:
                            pass
                        return s
                    if 'response' in parsed and isinstance(parsed.get('response'), str):
                        txt = _unwrap(parsed.get('response', '').strip())
                        return {'ok': True, 'text': txt, 'answer': {'text': txt, 'citations': [], 'confidence': None}, 'raw_json': parsed}
                    if 'text' in parsed and isinstance(parsed.get('text'), str):
                        txt = _unwrap(parsed.get('text', '').strip())
                        return {'ok': True, 'text': txt, 'answer': {'text': txt, 'citations': [], 'confidence': None}, 'raw_json': parsed}
                if isinstance(parsed, dict):
                    first_str = None
                    for v in parsed.values():
                        if isinstance(v, str) and v.strip():
                            first_str = v.strip()
                            break
                    if first_str is not None:
                        try:
                            import ast, json as _json
                            unwrapped = first_str
                            if unwrapped.startswith('{') or unwrapped.startswith('['):
                                try:
                                    inner = _json.loads(unwrapped)
                                    if isinstance(inner, dict):
                                        for vv in inner.values():
                                            if isinstance(vv, str) and vv.strip():
                                                return {'ok': True, 'text': vv.strip(), 'answer': {'text': vv.strip(), 'citations': [], 'confidence': None}, 'raw_json': parsed}
                                        return {'ok': True, 'text': str(inner), 'answer': {'text': str(inner), 'citations': [], 'confidence': None}, 'raw_json': parsed}
                                except Exception:
                                    pass
                            try:
                                inner = ast.literal_eval(unwrapped)
                                if isinstance(inner, dict):
                                    for vv in inner.values():
                                        if isinstance(vv, str) and vv.strip():
                                            return {'ok': True, 'text': vv.strip(), 'answer': {'text': vv.strip(), 'citations': [], 'confidence': None}, 'raw_json': parsed}
                                    return {'ok': True, 'text': str(inner), 'answer': {'text': str(inner), 'citations': [], 'confidence': None}, 'raw_json': parsed}
                            except Exception:
                                pass
                        except Exception:
                            pass
                        txt = first_str
                        return {'ok': True, 'text': txt, 'answer': {'text': txt, 'citations': [], 'confidence': None}, 'raw_json': parsed}
                txt = str(parsed)
                return {'ok': True, 'text': txt, 'answer': {'text': txt, 'citations': [], 'confidence': None}, 'raw_json': parsed}
            except Exception:
                txt = out
                return {'ok': True, 'text': txt, 'answer': {'text': txt, 'citations': [], 'confidence': None}}
        except FileNotFoundError:
            return {'ok': False, 'error': 'ollama CLI not found'}
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    def _call_model(self, prompt: str, use_cache: bool=True) -> Dict[str, Any]:
        cp = self._cache_path(prompt)
        if use_cache and self.cache_enabled and os.path.exists(cp) and (not self.mock):
            try:
                with open(cp, 'r', encoding='utf-8') as fh:
                    return json.load(fh)
            except Exception:
                pass
        if self.mock:
            resp = {'ok': True, 'text': f'محاكاة: إجابة تجريبية عن: {prompt[:_AGL_PREVIEW_120]}', 'sources': ['mock']}
            if self.cache_enabled:
                try:
                    with open(cp, 'w', encoding='utf-8') as fh:
                        json.dump(resp, fh, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return resp
        if self.api_url:
            r = self._call_model_via_http(prompt)
        else:
            r = self._call_model_via_cli(prompt)
        if use_cache and self.cache_enabled and isinstance(r, dict) and r.get('ok', False):
            try:
                with open(cp, 'w', encoding='utf-8') as fh:
                    json.dump(r, fh, ensure_ascii=False, indent=2)
            except Exception:
                pass
        return r
    def ask(self, question: str, context: Optional[List[str]]=None, system_prompt: Optional[str]=None, cache: bool=True) -> Dict[str, Any]:
        q = (question or '').strip()
        if not q:
            turn = make_turn(q)
            return normalize_engine_response(turn, {'ok': False, 'error': 'empty_question'})
        prompt = q
        if context:
            prompt = f'Context:\n' + '\n'.join([str(c) for c in context]) + '\n\nQuestion:\n' + q
        turn = make_turn(q)
        turn.setdefault('working', {})['_start_ms'] = int(time.time() * 1000)
        local_system_prompt = system_prompt if system_prompt is not None else SYSTEM_PROMPT
        full_prompt = local_system_prompt + '\n\n' + prompt
        use_cache = bool(cache and self.cache_enabled)
        engine_res = self._call_model(full_prompt, use_cache=use_cache)
        return normalize_engine_response(turn, engine_res)
if not hasattr(LocalKnowledgeEngine, 'process_task'):
    def _ollama_process_task(self, payload: dict) -> dict:
        try:
            q = payload.get('query') or payload.get('text') or payload.get('user') or ''
            ctx = payload.get('context')
            if getattr(self, 'mock', False):
                return {'ok': True, 'engine': 'ollama:mock', 'text': f'محاكاة: {str(q)[:_AGL_PREVIEW_120]}'}
            res = self.ask(str(q), context=ctx)
            if isinstance(res, dict):
                return {'ok': res.get('ok', False), 'engine': 'ollama', 'text': res.get('text'), 'raw': res}
            return {'ok': True, 'engine': 'ollama', 'text': str(res)}
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    setattr(LocalKnowledgeEngine, 'process_task', _ollama_process_task)
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('question', nargs='?', default=None)
    p.add_argument('--mock', action='store_true')
    args = p.parse_args()
    if args.mock:
        os.environ['AGL_OLLAMA_KB_MOCK'] = '1'
    eng = LocalKnowledgeEngine()
    q = args.question or 'ما هو تعريف الذكاء الاصطناعي؟'
    print(json.dumps(eng.ask(q), ensure_ascii=False, indent=2))
def create_engine(config: dict | None=None):
    try:
        return LocalKnowledgeEngine()
    except Exception:
        class _Shim:
            def __init__(self):
                self.name = 'Ollama_KnowledgeEngine_Shim'
            def process_task(self, payload: dict) -> dict:
                q = payload.get('query') or payload.get('text') or ''
                return {'ok': True, 'engine': 'ollama:shim', 'text': f'mock:{str(q)[:_AGL_PREVIEW_120]}'}
        return _Shim()
