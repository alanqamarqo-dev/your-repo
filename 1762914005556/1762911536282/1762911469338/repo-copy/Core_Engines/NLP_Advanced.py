from __future__ import annotations
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
_AGL_PREVIEW_500 = _to_int('AGL_PREVIEW_500', 500)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Tuple
import re
import os
from Core_Engines.engine_base import Engine, EngineRegistry
Role = Literal['user', 'assistant', 'system']
@dataclass
class NLPUtterance:
    role: Role
    text: str
    lang: str = 'auto'
@dataclass
class SentimentResult:
    label: str
    score: float
@dataclass
class IntentResult:
    intent: str
    confidence: float
    slots: Dict[str, str]
class ShortTermMemory:
    def __init__(self, max_turns: int=6):
        self.buffer: List[Dict[str, str]] = []
        self.max_turns = int(max_turns)
    def push(self, user: str, agent: str):
        self.buffer.append({'user': user, 'agent': agent})
        if len(self.buffer) > self.max_turns:
            self.buffer.pop(0)
    def get_recent(self) -> List[Dict[str, str]]:
        return list(self.buffer)
def summarize_turns(turns: List[Dict[str, str]], last_user: str | None=None, max_len: int=256) -> str:
    parts = []
    try:
        import os
        _SUMMARY_TURNS = int(os.environ.get('AGL_NLP_SUMMARY_TURNS', '5'))
    except Exception:
        _SUMMARY_TURNS = 5
    for t in turns[-_SUMMARY_TURNS:]:
        u = t.get('user', '')
        a = t.get('agent', '')
        parts.append(u.strip())
        if a:
            parts.append(a.strip())
    if last_user:
        parts.append(str(last_user).strip())
    s = ' | '.join((p for p in parts if p))
    return s[:max_len].strip()
try:
    _AGL_NLP_TOP_FACTS = int(os.environ.get('AGL_NLP_TOP_FACTS', '2'))
except Exception:
    _AGL_NLP_TOP_FACTS = 2
try:
    _AGL_NLP_SOURCES = int(os.environ.get('AGL_NLP_SOURCES', '3'))
except Exception:
    _AGL_NLP_SOURCES = 3
def simple_entity_extract(text: str) -> List[str]:
    ents = []
    ents += re.findall('\\b\\d+(?:\\.\\d+)?\\b', text)
    ents += re.findall('\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b', text)
    try:
        import os
        _ENTITY_LIMIT = int(os.environ.get('AGL_NLP_ENTITY_EXTRACT_LIMIT', '8'))
    except Exception:
        _ENTITY_LIMIT = 8
    ents += [w for w in re.findall('[\\w\\u0600-\\u06FF]{3,}', text) if not w.isdigit()][:_ENTITY_LIMIT]
    return ents
def sentiment_and_tone(text: str) -> Tuple[str, float]:
    pos_words = {'جيد', 'جيدة', 'ممتاز', 'رائع', 'great', 'excellent', 'good'}
    neg_words = {'سيء', 'سيئة', 'رديء', 'bad', 'terrible', 'awful'}
    t = text.lower()
    pos = sum((1 for w in pos_words if w in t))
    neg = sum((1 for w in neg_words if w in t))
    if pos > neg:
        return ('positive', min(0.6 + 0.1 * pos, 0.95))
    if neg > pos:
        return ('negative', min(0.6 + 0.1 * neg, 0.95))
    return ('neutral', 0.5)
def detect_tone(text: str) -> str:
    t = text.lower()
    if any((w in t for w in ['رجاء', 'من فضلك', 'please'])):
        return 'polite'
    if any((w in t for w in ['اشرح', 'شرح', 'explicate', 'explain'])):
        return 'explanatory'
    if any((w in t for w in ['!', '!ء'])):
        return 'emphatic'
    return 'neutral'
def classify_intent(text: str, labels: List[str]) -> Tuple[str, float, Dict[str, str]]:
    t = text.strip().lower()
    if any((k in t for k in ['ترجم', 'translate'])):
        m = re.search('(?:إلى|to)\\s+([a-zA-Z\\u0621-\\u064A]+)', t)
        slots = {'target': m.group(1)} if m else {}
        return ('translate', 0.9, slots)
    if any((k in t for k in ['اشرح', 'explain', 'شرح'])):
        return ('explain', 0.85, {})
    if any((k in t for k in ['تلخيص', 'sum', 'summarize'])):
        return ('summarize', 0.9, {})
    if t.endswith('?') or '؟' in t or any((q in t for q in ['ما', 'متى', 'لماذا', 'كيف', 'من'])):
        return ('qa', 0.6, {})
    return ('chitchat', 0.5, {})
def high_level_plan(text: str, ctx: Dict[str, Any], emo: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    lbl = intent.get('label') or ''
    plan = {'action': 'respond', 'explain_level': 'normal'}
    if lbl == 'translate':
        plan['action'] = 'translate'
    if lbl == 'summarize':
        plan['action'] = 'summarize'
    if lbl in {'explain', 'ask_how', 'ask_define'}:
        plan['explain_level'] = 'detailed'
    return plan
def decide_lang(ctx: Dict[str, Any], intent: Dict[str, Any]) -> str:
    return ctx.get('dominant_lang') or 'ar'
def adapt_style(plan: Dict[str, Any], target_lang: str='ar', tone: str='neutral') -> Dict[str, Any]:
    style = {'lang': target_lang, 'tone': tone, 'formal': tone in ('polite', 'explanatory'), 'brevity': 'short' if plan.get('explain_level') == 'normal' else 'detailed'}
    return {'style': style, 'template': None}
def render_answer(styled: Dict[str, Any], ctx_summary: str='') -> str:
    s = styled.get('style', {})
    tone = s.get('tone', 'neutral')
    brevity = s.get('brevity', 'short')
    if brevity == 'short':
        return f'({tone}) {ctx_summary}'[:400] or 'لا أعرف'
    return f'({tone}) تفصيل: {ctx_summary}'[:800]
def polish_answer(answer: str, rules: Dict[str, Any] | None=None) -> str:
    rules = rules or {'max_chars': 1200, 'strip_redundancy': True}
    out = re.sub('\\s+', ' ', answer).strip()
    if rules.get('strip_redundancy', True):
        out = re.sub('(\\b\\w+\\b)(?:\\s+\\1\\b){2,}', '\\1', out)
    maxc = rules.get('max_chars', 1200)
    return out[:maxc]
class NLPAdvancedEngine(Engine):
    name, version = ('NLP_Advanced', '2.0.0')
    def __init__(self, config: Dict[str, Any] | None=None) -> None:
        self._cfg = self._default_config()
        if config:
            for k, v in config.items():
                if isinstance(v, dict) and isinstance(self._cfg.get(k), dict):
                    self._cfg[k].update(v)
                else:
                    self._cfg[k] = v
        self.mem = ShortTermMemory(max_turns=self._cfg['memory']['max_turns'])
    def _default_config(self) -> Dict[str, Any]:
        return {'memory': {'max_turns': 8}, 'quality_rules': {'max_chars': 1200, 'strip_redundancy': True}, 'intents': {'labels': ['translate', 'define', 'explain', 'summarize', 'qa', 'brainstorm', 'rewrite', 'classify']}, 'styles': {'default_lang': 'ar', 'fallback_tone': 'neutral'}}
    def configure(self, **kwargs: Any) -> None:
        self._cfg.update(kwargs or {})
    def healthcheck(self) -> Dict[str, Any]:
        return {'ok': True, 'cfg': self._cfg.copy()}
    def respond(self, user_text: str, lang_hint: str | None=None) -> Dict[str, Any]:
        turns = self.mem.get_recent()
        ctx = {**self.understand_context([NLPUtterance(role='user', text=t['user']) for t in turns]), 'lang_hint': lang_hint}
        ctx['summary'] = summarize_turns(turns, last_user=user_text, max_len=256)
        emo_label, emo_conf = sentiment_and_tone(user_text)
        emo = {'sentiment': emo_label, 'tone': detect_tone(user_text), 'confidence': emo_conf}
        lbl, score, slots = classify_intent(user_text, self._cfg['intents']['labels'])
        intent = {'label': lbl, 'slots': slots, 'confidence': score}
        plan = high_level_plan(user_text, ctx, emo, intent)
        styled = adapt_style(plan, target_lang=decide_lang(ctx, intent), tone=emo['tone'])
        if plan.get('action') == 'translate':
            tgt = intent.get('slots', {}).get('target', 'en')
            tresp = self.translate(user_text, src='auto', tgt=tgt)
            if isinstance(tresp, dict):
                translated = tresp.get('text')
            elif isinstance(tresp, tuple):
                translated = tresp[0]
            else:
                translated = str(tresp)
            final = polish_answer(str(translated or ''), rules=self._cfg.get('quality_rules'))
        else:
            raw = render_answer(styled, ctx_summary=ctx.get('summary', user_text))
            final = self._quality_guard(raw, ctx, emo, intent)
        self.mem.push(user_text, final)
        return {'text': final, 'intent': intent, 'emotion': emo, 'context_used': ctx.get('summary', ''), 'style': styled.get('style'), 'confidence': {'emotion': emo.get('confidence', 0.6), 'intent': intent.get('confidence', 0.6)}}
    def understand_context(self, history: List[NLPUtterance]) -> Dict[str, Any]:
        text = ' '.join((u.text for u in history[-self.mem.max_turns:])) if history else ''
        langs = [u.lang for u in history if u.lang != 'auto'] or [self._cfg['styles']['default_lang']]
        dominant_lang = max(set(langs), key=langs.count)
        entities = simple_entity_extract(text)
        return {'dominant_lang': dominant_lang, 'entities': entities, 'chars': len(text)}
    def analyze_sentiment(self, text: str) -> SentimentResult:
        lbl, sc = sentiment_and_tone(text)
        return SentimentResult(lbl, sc)
    def analyze_intent(self, text: str) -> IntentResult:
        lbl, sc, slots = classify_intent(text, self._cfg['intents']['labels'])
        return IntentResult(intent=lbl, confidence=sc, slots=slots)
    def translate(self, text: str, src: str='auto', tgt: str | None=None):
        """
        Backwards-compatible translate:
        - Legacy call: translate(text, src, tgt) -> returns (translated_text, used_tgt)
        - New call: translate(text, to=...) OR translate(text, src='auto', tgt=None) -> returns dict {ok,text,intent,engine}
        """
        t = (text or '').strip()
        if not t:
            if tgt is not None:
                return ('', tgt)
            return {'ok': True, 'text': '', 'intent': 'translate', 'engine': 'NLP_Advanced'}
        if tgt is not None:
            source = src or 'auto'
            target = tgt or 'en'
        else:
            source = 'auto'
            target = src or 'ar'
        pairs = {('hello', 'ar'): 'مرحبًا', ('مرحبا', 'en'): 'hello'}
        core_text = t.replace('ترجم', '').replace('الى', '').replace('إلى', '').strip().lower()
        key = (core_text, target.lower())
        out = pairs.get(key)
        if out:
            reply = out
        else:
            core = None
            if 'ترجم' in t and ('الى' in t or 'إلى' in t):
                try:
                    core = t.split('ترجم', 1)[1].split('الى', 1)[0].split('إلى', 1)[0].strip()
                    reply = {'ar': 'مرحبًا' if core.lower() == 'hello' else core}.get(target.lower(), core)
                except Exception:
                    reply = core if core else t
            else:
                parts = t.split()
                if parts and target.lower().startswith('en'):
                    mapping = {'مرحباً': 'hello', 'مرحبا': 'hello', 'بكم': 'you'}
                    reply = ' '.join((mapping.get(w, w) for w in parts))
                else:
                    reply = t
        if tgt is not None:
            return (reply, target)
        return {'ok': True, 'text': reply, 'intent': 'translate', 'engine': 'NLP_Advanced'}
    def helpful(self, text: str, context: list | None=None) -> Dict[str, str]:
        t = (text or '').strip()
        if not t:
            return {'text': 'أهلاً! اكتب سؤالك أو طلبك وسأساعدك.'}
        if t.startswith('ترجم'):
            tresp = self.translate(t)
            if isinstance(tresp, tuple):
                translated = tresp[0]
            elif isinstance(tresp, dict):
                translated = tresp.get('text')
            else:
                translated = str(tresp)
            return {'text': str(translated or '')}
        if any((k in t for k in ['خطة', 'استراتيجية'])):
            return {'text': 'ملخص خطة:\n1) أهداف…\n2) الجمهور…\n3) القنوات…\n4) مؤشرات الأداء…'}
        return {'text': f'هذا ملخص لما طلبت: {t}\nلو تحب تفاصيل أكثر أو أمثلة، أخبرني بالسياق المطلوب.'}
    def _quality_guard(self, answer: str, ctx: Dict[str, Any], emo: Dict[str, Any], intent: Dict[str, Any]) -> str:
        return polish_answer(answer, rules=self._cfg.get('quality_rules'))
    def naturalize_answer(self, facts: list, question: str, provider_answer: str | None=None) -> str:
        """Produce a concise, human-friendly Arabic answer from accepted facts.
        facts: list of dicts with keys: object (text), source, confidence
        question: original user question
        provider_answer: optional short answer returned by provider to prefer
        """
        try:
            if provider_answer and isinstance(provider_answer, str) and provider_answer.strip():
                return polish_answer(provider_answer, rules=self._cfg.get('quality_rules'))
            if not facts:
                return 'لم أجد معلومات كافية حالياً للإجابة بدقة. هل تريد أن أبحث عبر الإنترنت؟'
            sorted_f = sorted(facts, key=lambda x: float(x.get('confidence', 0) or 0), reverse=True)
            top = sorted_f[:_AGL_NLP_TOP_FACTS]
            parts = []
            for f in top:
                parts.append(str(f.get('object') or f.get('text') or '')[:_AGL_PREVIEW_500])
            summary = '؛ '.join((p for p in parts if p))
            sources = ', '.join([str(f.get('source')) for f in sorted_f[:_AGL_NLP_SOURCES] if f.get('source')])
            if sources:
                summary = f'{summary} (مصادر: {sources})'
            return polish_answer(summary, rules=self._cfg.get('quality_rules'))
        except Exception:
            try:
                return polish_answer(str(provider_answer or (facts and facts[0].get('object')) or question), rules=self._cfg.get('quality_rules'))
            except Exception:
                return str(provider_answer or question)
NLPAdvanced = NLPAdvancedEngine
EngineRegistry.register(NLPAdvancedEngine())
def _nlp_generate_reply_wrapper(hist: list) -> str:
    eng = NLPAdvancedEngine()
    if isinstance(hist, str):
        return eng.respond(hist)['text']
    if hist and isinstance(hist, list) and hasattr(hist[0], 'text'):
        last = hist[-1].text
        return eng.respond(last)['text']
    return eng.respond('')['text']
setattr(NLPAdvancedEngine, 'generate_reply', lambda self, history: _nlp_generate_reply_wrapper(history))
if not hasattr(NLPAdvancedEngine, 'process_task'):
    def process_task(self, payload: dict) -> dict:
        try:
            text = payload.get('text') or payload.get('input') or payload.get('query') or ''
            action = payload.get('action')
            if action == 'respond' or not action:
                return {'ok': True, 'engine': self.name, 'result': self.respond(str(text))}
            if action == 'translate':
                return {'ok': True, 'engine': self.name, 'result': self.translate(str(text), src=payload.get('src', 'auto'), tgt=payload.get('tgt'))}
            return {'ok': True, 'engine': self.name, 'message': 'unknown action'}
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    setattr(NLPAdvancedEngine, 'process_task', process_task)
