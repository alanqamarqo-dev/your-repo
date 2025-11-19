import os
import re
import json
from typing import Any, Dict, List, Optional

import sys
sys.path.append(os.getcwd())

class KnowledgeOrchestrator:
    """Minimal orchestrator that dispatches to retriever, calculator, external provider,
    and a naturalizer to produce a final answer envelope.

    This is intentionally lightweight: it uses available components when present and
    falls back to simple heuristics.
    """

    def __init__(self, retriever=None, reasoner=None, external_provider=None, naturalizer=None):
        self.retriever = retriever
        self.reasoner = reasoner
        self.external_provider = external_provider
        self.naturalizer = naturalizer

    @staticmethod
    def _looks_like_math(q: str) -> bool:
        if not q:
            return False
        # simple heuristic: contains digits and math symbols or Arabic word for calculate
        if re.search(r'[0-9].*[\+\-\*/=]', q):
            return True
        if any(w in q for w in ['احسب', 'حساب', 'كم', 'اجمالي', 'sum', 'calculate']):
            return True
        return False

    def _safe_eval(self, expr: str) -> Optional[str]:
        # very small safe evaluator supporting basic arithmetic
        try:
            import ast, operator as op

            # supported operators
            operators = {
                ast.Add: op.add,
                ast.Sub: op.sub,
                ast.Mult: op.mul,
                ast.Div: op.truediv,
                ast.Pow: op.pow,
                ast.USub: op.neg,
                ast.Mod: op.mod,
            }

            def _eval(node):
                if isinstance(node, ast.Num):
                    return node.n
                if isinstance(node, ast.BinOp):
                    return operators[type(node.op)](_eval(node.left), _eval(node.right))
                if isinstance(node, ast.UnaryOp):
                    return operators[type(node.op)](_eval(node.operand))
                raise ValueError('Unsupported expression')

            node = ast.parse(expr, mode='eval').body
            val = _eval(node)
            return str(val)
        except Exception:
            return None

    def orchestrate(self, question: str, context: Optional[List[str]] = None) -> Dict[str, Any]:
        question = (question or '').strip()
        trace = []
        evidence = []
        sources = []

        # honor force-external flag to bypass local retriever and always use external LLM
        force_external = str(os.environ.get('AGL_FORCE_EXTERNAL', '0')).lower() in ('1', 'true', 'yes')
        if force_external:
            trace.append({'engine': 'control', 'note': 'force_external=True - skipping retriever'})

        if not question:
            return {'ok': False, 'text': 'Empty question', 'engine_trace': trace}

        # 1) quick math handling
        if self._looks_like_math(question):
            calc_res = self._safe_eval(re.sub(r'[^0-9\.+\-\*/() ]', '', question))
            if calc_res is not None:
                trace.append({'engine': 'calculator', 'result': calc_res})
                final = f"النتيجة: {calc_res}"
                return {'ok': True, 'text': final, 'sources': [], 'evidence': [], 'engine_trace': trace}

        # 2) attempt local retrieval if retriever available (skipped when force_external)
        local_facts = []
        if not force_external:
            try:
                if self.retriever is None:
                    try:
                        from Integration_Layer.retriever import SimpleFactsRetriever
                        self.retriever = SimpleFactsRetriever()
                    except Exception:
                        self.retriever = None
                if self.retriever:
                    try:
                        k_limit = int(os.getenv('AGL_ROUTER_RESULT_LIMIT', '15'))
                    except Exception:
                        k_limit = 15
                    local_facts = self.retriever.retrieve(question, k=k_limit) or []
                    trace.append({'engine': 'retriever', 'count': len(local_facts)})
                    for f in local_facts:
                        if isinstance(f, dict):
                            evidence.append({'text': f.get('text'), 'source': f.get('source'), 'confidence': f.get('confidence', 0)})
                            sources.append(f.get('source'))
                        elif isinstance(f, (list, tuple)) and len(f) > 1:
                            evidence.append({'text': f[1], 'source': f[0], 'confidence': f[2] if len(f) > 2 else 0})
                            sources.append(f[0])
            except Exception as e:
                trace.append({'engine': 'retriever', 'error': str(e)})

        # If we have decent local evidence, return synthesized answer using reasoner if available
        if evidence:
            try:
                if self.reasoner is None:
                    try:
                        from Core_Engines.GK_reasoner import GKReasoner
                        self.reasoner = GKReasoner(None, None)
                    except Exception:
                        self.reasoner = None
                # simple naturalization: join top N facts (configurable)
                try:
                    evidence_limit = int(os.getenv('AGL_EVIDENCE_LIMIT', '8'))
                except Exception:
                    evidence_limit = 8
                top = evidence[:evidence_limit]
                ans = '؛ '.join([t['text'] for t in top if t.get('text')])
                trace.append({'engine': 'synthesizer', 'method': 'local_top'})
                return {'ok': True, 'text': ans, 'sources': sources[:evidence_limit], 'evidence': evidence, 'engine_trace': trace}
            except Exception:
                pass

        # 3) fallback to external provider
        try:
            if self.external_provider is None:
                # prefer OpenAIAdapter if configured
                impl = os.environ.get('AGL_EXTERNAL_INFO_IMPL', '').lower()
                if impl in ('openai_engine', 'openai_adapter'):
                    from Core_Engines.OpenAI_Adapter import OpenAIAdapter
                    self.external_provider = OpenAIAdapter(model=os.environ.get('AGL_EXTERNAL_INFO_MODEL'))
                elif impl in ('ollama_engine', 'ollama_adapter'):
                    # Use the Ollama adapter when requested
                    try:
                        from Core_Engines.Ollama_Adapter import OllamaAdapter
                        self.external_provider = OllamaAdapter(model=os.environ.get('AGL_EXTERNAL_INFO_MODEL'))
                    except Exception:
                        # fallback to generic ExternalInfoProvider
                        from Core_Engines.External_InfoProvider import ExternalInfoProvider
                        self.external_provider = ExternalInfoProvider(model=os.environ.get('AGL_EXTERNAL_INFO_MODEL'))
                else:
                    from Core_Engines.External_InfoProvider import ExternalInfoProvider
                    self.external_provider = ExternalInfoProvider(model=os.environ.get('AGL_EXTERNAL_INFO_MODEL'))
            # decide whether to allow engine-level caching for this external call
            cache_for_ext = not force_external
            # allow injecting a system prompt from environment (or orchestrator could build one)
            system_prompt = os.environ.get('AGL_EXTERNAL_SYSTEM_PROMPT')

            try:
                ext_res = self.external_provider.fetch_facts(question, hints=context or [], system_prompt=system_prompt, cache=cache_for_ext) # type: ignore
            except TypeError:
                # adapter does not support extended kwargs, fallback to legacy call
                ext_res = self.external_provider.fetch_facts(question, hints=context or [])

            trace.append({'engine': 'external_provider', 'response_keys': list(ext_res.keys()) if isinstance(ext_res, dict) else None, 'used_system_prompt': ext_res.get('used_system_prompt') if isinstance(ext_res, dict) else None, 'prompt_hash': ext_res.get('prompt_hash') if isinstance(ext_res, dict) else None})
            if ext_res.get('ok'):
                # unify candidate final text from known fields
                candidate = ''
                facts = ext_res.get('facts', [])
                if facts:
                    evidence = []
                    for f in facts:
                        evidence.append({'text': f.get('text'), 'source': f.get('source'), 'confidence': f.get('confidence', 0)})
                        if f.get('source'):
                            sources.append(f.get('source'))
                    # naturalize using NLP_Advanced if available
                    try:
                        from Core_Engines.NLP_Advanced import NLPAdvancedEngine
                        nat = NLPAdvancedEngine()
                        natural = getattr(nat, 'naturalize_answer', None)
                        if callable(natural):
                            candidate = natural(evidence, question, None)
                        else:
                            candidate = evidence[0]['text']
                    except Exception:
                        candidate = evidence[0]['text'] if evidence else ''

                # if external provided an 'answer' or 'text' directly, prefer it when no facts
                if not candidate:
                    candidate = ext_res.get('answer') or ext_res.get('text') or ''

                # Post-processing layer: Language/Locale Guard + Self-Analysis + Output Formatter
                def is_arabic_only(s) -> bool:
                    s = str(s or '')
                    # Allow Arabic letters, Arabic-Indic digits, basic punctuation and whitespace
                    # Note: keep the whitelist conservative to detect any Latin/CJK characters
                    return re.search(r"[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\d\s\.,؛:\-\(\)\"'`]", s) is None

                def contains_non_arabic(s) -> bool:
                    return not is_arabic_only(s)

                # simple self-evaluation metrics
                def self_evaluate(s) -> Dict[str, Any]:
                    s = str(s or '')
                    length = len(s)
                    arabic = is_arabic_only(s)
                    has_steps = bool(re.search(r'(^|\n)\s*\d+\.', s)) or bool(re.search(r'خطو|خطوة|1\.', s))
                    completeness = 1.0 if length > 20 else 0.0
                    score = 0.0
                    score += 40.0 if arabic else 0.0
                    score += 30.0 if has_steps else 0.0
                    score += 30.0 * completeness
                    return {'length': length, 'arabic_only': arabic, 'has_steps': has_steps, 'quality_score': round(score, 1)}

                eval1 = self_evaluate(candidate)
                trace.append({'engine': 'self_evaluation', 'result': eval1})

                # If output contains non-Arabic fragments or low quality, attempt one retry with a stricter system prompt
                retried = False
                if contains_non_arabic(candidate) or eval1['quality_score'] < 60.0:
                    # if adapter supports system_prompt, request a regeneration with a strict Arabic-only system directive
                    stricter_prompt = (
                        "أنت نظام AGL. أعد الصياغة فقط باللغة العربية الفصحى، لا تستخدم أي كلمات أو أحرف من لغات أخرى، لا تستخدم رموز برمجية أو علامات لغة أجنبية. "
                        "إذا طُلِبَت خطوات فقدمها مرقّمة بالعربية. استجب بإجابة مُنظَّمة وواضحة."
                    )
                    try:
                        func = getattr(self.external_provider, 'fetch_facts')
                        try:
                            # attempt positional form: (question, hints, system_prompt, cache)
                            regen = func(question, context or [], stricter_prompt, False)
                        except TypeError:
                            # fallback to legacy two-arg form
                            regen = func(question, context or [])
                        retried = True
                        trace.append({'engine': 'self_rewrite_attempt', 'response_keys': list(regen.keys()) if isinstance(regen, dict) else None, 'prompt_hash': regen.get('prompt_hash') if isinstance(regen, dict) else None})
                        # prefer regen's answer
                        cand2 = ''
                        if regen.get('facts'):
                            f = regen.get('facts')
                            if isinstance(f, list) and f:
                                cand2 = f[0].get('text') or ''
                        if not cand2:
                            cand2 = regen.get('answer') or regen.get('text') or ''
                        if cand2:
                            candidate = cand2
                            eval2 = self_evaluate(candidate)
                            trace.append({'engine': 'self_evaluation_after_regen', 'result': eval2})
                    except Exception as e:
                        trace.append({'engine': 'self_rewrite_error', 'error': str(e)})

                # Output formatter enforcement: ensure we return a clean Arabic text block; if still empty, fail
                final_text = str(candidate or '')
                if not final_text.strip():
                    return {'ok': False, 'text': 'empty_answer_after_external', 'engine_trace': trace}

                # assemble final response envelope including evaluation metadata
                meta = {'self_eval': eval1, 'retried': retried}
                return {'ok': True, 'text': final_text, 'sources': list(dict.fromkeys(sources))[:evidence_limit], 'evidence': evidence, 'engine_trace': trace, 'meta': meta}
            return {'ok': False, 'text': 'external_provider_failed', 'engine_trace': trace}
        except Exception as e:
            trace.append({'engine': 'external_provider', 'error': str(e)})
            return {'ok': False, 'text': 'orchestrator_error', 'error': str(e), 'engine_trace': trace}
