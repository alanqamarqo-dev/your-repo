# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_PREVIEW_120 = _to_int('AGL_PREVIEW_120', 120)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import os
from Integration_Layer.rag_wrapper import rag_answer
class OpenAI_KnowledgeEngine:
    def __init__(self, **kwargs):
        self.name = 'OpenAI_KnowledgeEngine'
    @staticmethod
    def create_engine(config=None):
        return OpenAI_KnowledgeEngine()
    def process_task(self, payload: dict):
        q = payload.get('query') or payload.get('text') or payload.get('user') or ''
        ctx = payload.get('context')
        if os.getenv('AGL_OPENAI_KB_MOCK', '0') == '1':
            return {'ok': True, 'engine': 'openai:mock', 'text': f'محاكاة: {str(q)[:_AGL_PREVIEW_120]}'}
        try:
            out = rag_answer(q, context=ctx)
            if isinstance(out, dict):
                return {'ok': True, 'engine': 'openai', 'text': out.get('answer') or out.get('text')}
            return {'ok': True, 'engine': 'openai', 'text': str(out)}
        except Exception as e:
            return {'ok': False, 'engine': 'openai', 'error': str(e)}
import os
import json
import time
import hashlib
from typing import Any, Dict, List, Optional
try:
    _AGL_OPENAI_TOP_K = int(os.environ.get('AGL_OPENAI_TOP_K', '3'))
except Exception:
    _AGL_OPENAI_TOP_K = 3
try:
    _AGL_OPENAI_MAX_TOKENS = int(os.environ.get('AGL_OPENAI_MAX_TOKENS', '512'))
except Exception:
    _AGL_OPENAI_MAX_TOKENS = 512
SYSTEM_PROMPT = 'أنت محرك معرفة: استجب بإجابة موجزة وموثوقة. أعد نُسخة JSON مع الحقول: {"ok": true/false, "text": "...", "sources": [...]} ولا تخرج عن JSON.'
class OpenAIKnowledgeEngine:
    def __init__(self, model: Optional[str]=None, cache_dir: Optional[str]=None):
        self.mock = os.getenv('AGL_OPENAI_KB_MOCK', '0') in ('1', 'true', 'True')
        self.model = model or os.getenv('AGL_OPENAI_KB_MODEL') or os.getenv('AGL_EXTERNAL_INFO_MODEL') or 'gpt-4'
        self.cache_dir = cache_dir or os.getenv('AGL_OPENAI_KB_CACHE', 'artifacts/openai_kb_cache')
        self.cache_enabled = os.getenv('AGL_OPENAI_KB_CACHE_ENABLE', '1') in ('1', 'true', 'True')
        os.makedirs(self.cache_dir, exist_ok=True)
        if not self.mock:
            key = os.getenv('OPENAI_API_KEY', '')
            if not key:
                raise RuntimeError('OPENAI_API_KEY not set for OpenAIKnowledgeEngine')
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=key)
            except Exception:
                try:
                    import openai as _openai
                    _openai.api_key = key
                    self.client = _openai
                except Exception as e:
                    raise RuntimeError('openai client not available: ' + str(e))
                    try:
                        _AGL_OPENAI_TOP_K = int(os.environ.get('AGL_OPENAI_TOP_K', '3'))
                    except Exception:
                        _AGL_OPENAI_TOP_K = 3
                    try:
                        _AGL_OPENAI_MAX_TOKENS = int(os.environ.get('AGL_OPENAI_MAX_TOKENS', '512'))
                    except Exception:
                        _AGL_OPENAI_MAX_TOKENS = 512
    def _cache_path(self, q: str) -> str:
        h = hashlib.sha256(q.encode('utf-8')).hexdigest()[:32]
        return os.path.join(self.cache_dir, f'{h}.json')
    def _call_model(self, prompt: str) -> Dict[str, Any]:
        cp = self._cache_path(prompt)
        if self.cache_enabled and os.path.exists(cp) and (not self.mock):
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
        try:
            messages = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': prompt}]
            try:
                max_tokens = int(os.getenv('AGL_OPENAI_MAX_TOKENS', str(_AGL_OPENAI_MAX_TOKENS)))
            except Exception:
                max_tokens = None
            if hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions'):
                try:
                    if max_tokens is not None:
                        r = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.0, max_tokens=max_tokens)
                    else:
                        r = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.0)
                except Exception:
                    r = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.0)
                content = getattr(getattr(r, 'choices', [None])[0], 'message', None)
                text = content.content if content and getattr(content, 'content', None) else ''
            else:
                try:
                    if max_tokens is not None:
                        r = self.client.ChatCompletion.create(model=self.model, messages=messages, temperature=0.0, max_tokens=max_tokens)
                    else:
                        r = self.client.ChatCompletion.create(model=self.model, messages=messages, temperature=0.0)
                except Exception:
                    r = self.client.ChatCompletion.create(model=self.model, messages=messages, temperature=0.0)
                text = r.choices[0].message.content if hasattr(r, 'choices') else r['choices'][0]['message']['content'] if isinstance(r, dict) else ''
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    out = {'ok': bool(data.get('text') or data.get('answer') or data.get('ok', True)), 'text': data.get('text') or data.get('answer') or '', 'sources': data.get('sources') or []}
                else:
                    out = {'ok': True, 'text': str(data), 'sources': []}
            except Exception:
                out = {'ok': True, 'text': text.strip() if isinstance(text, str) else '', 'sources': []}
            if self.cache_enabled:
                try:
                    with open(cp, 'w', encoding='utf-8') as fh:
                        json.dump(out, fh, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return out
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    def ask(self, question: str, context: Optional[List[str]]=None) -> Dict[str, Any]:
        q = (question or '').strip()
        if not q:
            return {'ok': False, 'text': '', 'error': 'empty_question'}
        prompt = q
        if context:
            prompt = f'Context:\n' + '\n'.join([str(c) for c in context]) + '\n\nQuestion:\n' + q
        return self._call_model(prompt)
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('question', nargs='?', default=None)
    p.add_argument('--mock', action='store_true')
    args = p.parse_args()
    if args.mock:
        os.environ['AGL_OPENAI_KB_MOCK'] = '1'
    eng = OpenAIKnowledgeEngine()
    q = args.question or 'ما هو تعريف الذكاء الاصطناعي؟'
    print(json.dumps(eng.ask(q), ensure_ascii=False, indent=2))
def create_engine(config: dict | None=None):
    try:
        return OpenAI_KnowledgeEngine()
    except Exception:
        class _Shim:
            def __init__(self):
                self.name = 'OpenAI_KnowledgeEngine_Shim'
            def process_task(self, payload: dict) -> dict:
                q = payload.get('query') or payload.get('text') or ''
                return {'ok': True, 'engine': 'openai:shim', 'text': f'mock:{str(q)[:_AGL_PREVIEW_120]}'}
        return _Shim()
