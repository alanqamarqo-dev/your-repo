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
import io
import os
import sys
import json
import traceback
import hashlib
import os
import sys
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
import io
import os
import json
import traceback
import hashlib
import time
from typing import List, Dict, Any, Optional
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('LANG', 'en_US.UTF-8')
os.environ.setdefault('LC_ALL', 'en_US.UTF-8')
SYSTEM_PROMPT = 'أنت مُساعد منظّم: أجب بصيغة JSON فقط بالشكل التالي: {"answer": "...", "facts": [ {"text": "...", "source": "...", "confidence": 0.0} ] }. إذا كان بالإمكان توليد إجابة موجزة مبنية على الحقائق، ضعها في الحقل \'answer\'. لا تضع أي نص خارج JSON.'
class ExternalInfoProvider:
    """Facts-only external info provider using OpenAI v1 client.
    Returns dict: {ok: bool, answer: Optional[str], facts: list} on success or
    {ok: False, error: str} on failure.
    """
    def __init__(self, model: Optional[str]=None, cache_dir: Optional[str]=None, daily_limit: Optional[int]=None):
        self.mock = os.getenv('AGL_EXTERNAL_INFO_MOCK', '0') in ('1', 'true', 'True')
        self.client = None
        self._ok = False
        if not self.mock:
            try:
                key = os.getenv('OPENAI_API_KEY', '')
                if key and isinstance(key, str) and key.isascii() and key.startswith('sk-'):
                    try:
                        from openai import OpenAI
                        self.client = OpenAI(api_key=key)
                        self._ok = True
                    except Exception:
                        self.client = None
                        self._ok = False
                else:
                    self.client = None
                    self._ok = False
            except Exception:
                self.client = None
                self._ok = False
        self.model = model or os.getenv('AGL_EXTERNAL_INFO_MODEL') or 'gpt-4o-mini'
        self.cache_dir = cache_dir or os.getenv('AGL_EXTERNAL_INFO_CACHE_DIR') or 'artifacts/external_info_cache'
        self.daily_limit = daily_limit or (int(os.getenv('AGL_EXTERNAL_INFO_DAILY_LIMIT', '0')) or None)
        os.makedirs(self.cache_dir, exist_ok=True)
        if self.mock:
            self._ok = True
    def _cache_path(self, q: str) -> str:
        h = hashlib.sha256(q.encode('utf-8')).hexdigest()[:32]
        return os.path.join(self.cache_dir, f'{h}.json')
    def _inc_usage(self) -> int:
        p = os.path.join(self.cache_dir, 'usage.json')
        data = {'day': time.strftime('%Y-%m-%d'), 'count': 0}
        try:
            if os.path.exists(p):
                with io.open(p, 'r', encoding='utf-8-sig') as fh:
                    data = json.load(fh)
            if data.get('day') != time.strftime('%Y-%m-%d'):
                data = {'day': time.strftime('%Y-%m-%d'), 'count': 0}
        except Exception:
            data = {'day': time.strftime('%Y-%m-%d'), 'count': 0}
        data['count'] += 1
        json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        return data['count']
    def _mock_make_fact(self, question: str, domain: str):
        txt = f'حقيقة دقيقة وموثّقة حول «{question}» ضمن مجال {domain}.'
        return {'text': txt, 'source': 'mock-provider', 'confidence': 0.9, 'domain': domain}
    def fetch_facts(self, question: str, hints: List[str] | None=None) -> Dict[str, Any]:
        cp = self._cache_path(question)
        if os.path.exists(cp) and (not getattr(self, 'mock', False)):
            try:
                with open(cp, 'r', encoding='utf-8') as fh:
                    cached = json.load(fh)
                return {'ok': True, 'answer': cached.get('answer'), 'facts': cached.get('facts', [])}
            except Exception:
                pass
        if getattr(self, 'mock', False):
            answer = f'هذا ملخص تجريبي عن: {question[:_AGL_PREVIEW_120]}'
            facts = [self._mock_make_fact(question, domain=hints[0] if hints else 'general')]
            try:
                with open(cp, 'w', encoding='utf-8-sig') as fh:
                    json.dump({'answer': answer, 'facts': facts}, fh, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return {'ok': True, 'answer': answer, 'facts': facts}
        if not getattr(self, '_ok', False):
            return {'ok': False, 'error': 'no_external_provider_configured'}
        if self.daily_limit:
            used = self._inc_usage()
            if used > self.daily_limit:
                return {'ok': False, 'error': 'daily_limit_exceeded'}
        user_prompt = question
        if hints:
            user_prompt += '\n\nHints:\n- ' + '\n- '.join(hints)
        try:
            messages = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': user_prompt}]
            def _call_chat(messages_local):
                last_exc = None
                try:
                    if hasattr(self, 'client') and hasattr(self.client, 'chat'):
                        if hasattr(self.client.chat, 'completions') and hasattr(self.client.chat.completions, 'create'):
                            return self.client.chat.completions.create(model=self.model, messages=messages_local, response_format={'type': 'json_object'}, temperature=0.2)
                except Exception as e:
                    last_exc = e
                try:
                    import openai as _openai
                    if hasattr(_openai, 'ChatCompletion') and hasattr(_openai.ChatCompletion, 'create'):
                        return _openai.ChatCompletion.create(model=self.model, messages=messages_local, temperature=0.2)
                except Exception as e:
                    last_exc = e
                if last_exc:
                    raise last_exc
                raise RuntimeError('no_compatible_openai_client')
            resp = _call_chat(messages)
        except Exception as e:
            tb = traceback.format_exc()
            return {'ok': False, 'error': f'client_error: {repr(e)}', 'traceback': tb}
        content = '{}'
        try:
            content_obj = getattr(getattr(resp, 'choices', [None])[0], 'message', None)
            if content_obj and getattr(content_obj, 'content', None):
                content = content_obj.content
            else:
                content = '{}'
        except Exception:
            content = '{}'
        try:
            data = json.loads(content)
        except Exception as e:
            return {'ok': False, 'error': f'parse_error: {e}'}
        answer = data.get('answer') if isinstance(data.get('answer'), str) else None
        facts = []
        for f in data.get('facts', []):
            t = (f or {}).get('text', '')
            s = (f or {}).get('source', '')
            c = (f or {}).get('confidence', 0.0)
            try:
                conf = float(c)
            except Exception:
                conf = 0.0
            if isinstance(t, str) and len(t.strip()) > 5 and isinstance(s, str) and s and (0 <= conf <= 1):
                facts.append({'text': t.strip(), 'source': s.strip(), 'confidence': conf})
        if facts or answer:
            try:
                json.dump({'answer': answer, 'facts': facts}, open(cp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            except Exception:
                pass
            return {'ok': True, 'answer': answer, 'facts': facts}
        return {'ok': False, 'error': 'no_facts_parsed'}
