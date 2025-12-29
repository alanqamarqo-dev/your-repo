import os
import json
from datetime import datetime
from typing import Callable, Dict, Any, List, Optional

from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
# حاول استخدام rag_answer من Integration_Layer إن وُجد (الأنبوب القديم)
try:
    from Integration_Layer.rag_wrapper import rag_answer as _rag_answer_fn  # type: ignore
except Exception:
    _rag_answer_fn = None

DEFAULT_DOMAINS = ("language", "reason", "knowledge", "planning")


def _default_pipeline_merge(proposals: List[Dict[str, Any]], question: str, context: Optional[str]) -> Dict[str, Any]:
    """دمج افتراضي لمخرجات المحركات إلى إجابة نهائية بسيطة وقابلة للاستبدال.

    الخوارزمية الافتراضية:
    - أخذ أعلى مقترح (score) كقاعدة
    - جمع ملخصات من أعلى 3 مقترحات وضمها إلى قسم "synthesis"
    - إرجاع بنية تحتوي final_answer و synthesis و provenance
    """
    if not proposals:
        return {
            "final_answer": "لا توجد مقترحات.",
            "synthesis": "",
            "provenance": []
        }

    # ترتيب المقترحات بحسب score أو novelty
    sorted_props = sorted(proposals, key=lambda p: p.get('score', 0), reverse=True)

    top = sorted_props[0]
    top3 = sorted_props[:3]

    # بناء إجابة نهائية بسيطة
    final_parts = []
    provenance = []
    for p in top3:
        engine = p.get('engine')
        content = p.get('content')
        summary = ''
        # إذا كان المحتوى dict وحوي على 'ideas' أو 'plan' حاول استخلاص سطر ملخّص
        if isinstance(content, dict):
            if 'ideas' in content and content['ideas']:
                first = content['ideas'][0]
                if isinstance(first, dict):
                    summary = first.get('idea') or str(first)
                else:
                    summary = str(first)
            elif 'plan' in content:
                summary = str(content.get('plan'))
            else:
                summary = str(content)
        else:
            summary = str(content)

        final_parts.append(f"- [{engine}] {summary}")
        provenance.append({
            'engine': engine,
            'score': p.get('score'),
            'novelty': p.get('novelty'),
            'domains': p.get('domains')
        })

    final_answer = f"الملخص المركب للسؤال: {question}\n\n" + "\n".join(final_parts)

    synthesis = {
        'method': 'default_merge_v1',
        'top_choice': top.get('engine'),
        'top_score': top.get('score')
    }

    return {
        'final_answer': final_answer,
        'synthesis': synthesis,
        'provenance': provenance
    }


def _proposals_to_context(proposals: List[Dict[str, Any]], question: str, max_chars: int = 1800) -> str:
    """حوّل قائمة الاقتراحات إلى نص سياقي يُمرّر إلى rag_answer.

    نأخذ أعلى 5 اقتراحات ونلخّص كل واحدة سطراً واحداً، مع وزن score/novelty.
    """
    if not proposals:
        return question

    sorted_props = sorted(proposals, key=lambda p: p.get('score', 0), reverse=True)
    parts = [f"سؤال: {question}"]
    parts.append("ملخص الاقتراحات الأعلى:")
    for p in sorted_props[:5]:
        engine = p.get('engine')
        score = p.get('score', 0)
        novelty = p.get('novelty', 0)
        content = p.get('content')
        # extract a short summary
        summary = ''
        if isinstance(content, dict):
            if 'ideas' in content and content['ideas']:
                first = content['ideas'][0]
                summary = first.get('idea') if isinstance(first, dict) else str(first)
            elif 'plan' in content:
                summary = str(content.get('plan'))
            else:
                # fallback: stringify a short slice
                summary = str(content)[:200]
        else:
            summary = str(content)[:200]

        parts.append(f"- [{engine}] score={score:.3f} novelty={novelty:.3f} -> {summary}")

    ctx = "\n".join(parts)
    if len(ctx) > max_chars:
        return ctx[:max_chars]
    return ctx


def _rag_adapter(proposals: List[Dict[str, Any]], question: str, context: Optional[str]) -> Dict[str, Any]:
    """Adapter: يحول proposals إلى context ويستدعي rag_answer لإنتاج الإجابة النهائية."""
    # بناء السياق من المقترحات + السياق الأصلي
    ctx_from_props = _proposals_to_context(proposals, question)
    full_context = (context or "") + "\n\n" + ctx_from_props if context else ctx_from_props

    if _rag_answer_fn is None:
        # لا يوجد rag؛ عد لآلية الدمج الافتراضية
        return _default_pipeline_merge(proposals, question, context)

    try:
        out = _rag_answer_fn(question, full_context)
        # تقليل وتطبيع النتيجة إلى الشكل المتوقع
        answer_text = out.get('answer') if isinstance(out, dict) else str(out)
        engine_tag = out.get('engine') if isinstance(out, dict) else None
        merged = {
            'final_answer': answer_text,
            'synthesis': {'method': 'rag_adapter', 'rag_engine': engine_tag},
            'provenance': proposals
        }
        return merged
    except Exception:
        # في حال فشل rag نرجع الدمج الافتراضي كاحتياط
        return _default_pipeline_merge(proposals, question, context)


def agl_universal_answer(question: str,
                         context: Optional[str] = None,
                         cie: Optional[CognitiveIntegrationEngine] = None,
                         domains_needed: Optional[List[str]] = None,
                         pipeline_fn: Optional[Callable[[List[Dict[str, Any]], str, Optional[str]], Dict[str, Any]]] = None,
                         log_path: str = 'artifacts/experiments.jsonl') -> Dict[str, Any]:
    """البوابة الموحدة: تشغّل CIE، تجمع المقترحات، تمررها إلى الـ Pipeline، وتُسجّل التجربة.

    المعطيات:
    - question: نص السؤال المطروح للمجتمع المعرفي
    - context: سياق إضافي إن وُجد
    - cie: كائن CognitiveIntegrationEngine مُسبق الإنشاء (يمكن ترك None لإنشائه)
    - domains_needed: قائمة المجالات المطلوبة للمحركات
    - pipeline_fn: دالة مدمجة أو خارجية لتحويل المقترحات إلى إجابة نهائية
    - log_path: مكان حفظ سجل التجارب (JSONL)

    ترجع بنية تحتوي final_answer، raw_proposals، merged_result، و metadata.
    """
    if domains_needed is None:
        domains_needed = list(DEFAULT_DOMAINS)

    if pipeline_fn is None:
        pipeline_fn = _default_pipeline_merge

    created_cie = False
    if cie is None:
        cie = CognitiveIntegrationEngine()
        created_cie = True

    problem = {
        'type': 'user_question',
        'title': question[:120],
        'description': context or question,
        'constraints': [],
        'expected_output': 'concise structured answer + supporting proposals'
    }

    # تشغيل CIE
    result = cie.collaborative_solve(problem=problem, domains_needed=tuple(domains_needed))

    # جمع المقترحات (top) بصيغة قياسية
    raw_top = result.get('top', []) if isinstance(result, dict) else []

    proposals = []
    for p in raw_top:
        proposals.append({
            'engine': p.get('engine'),
            'content': p.get('content'),
            'score': p.get('score', 0),
            'novelty': p.get('novelty', 0),
            'domains': p.get('domains', [])
        })

    # استدعاء الأنبوب (يمكن أن يكون أنبوبك القديم)
    merged = pipeline_fn(proposals, question, context)

    # سجل التجربة
    os.makedirs(os.path.dirname(log_path), exist_ok=True) if os.path.dirname(log_path) else None
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'question': question,
        'context': context,
        'domains_requested': domains_needed,
        'raw_result_summary': {
            'winner': result.get('winner') if isinstance(result, dict) else None,
            'top_count': len(proposals)
        },
        'proposals': proposals,
        'final': merged,
        'cie_instantiated_here': created_cie
    }

    # append as jsonl
    try:
        with open(log_path, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        # لا نفشل عند فشل التسجيل
        pass

    # إن أردت تنظيف cie (إذا أنشأناه هنا) فليس ضروريًا لكنه ممكن
    return {
        'final_answer': merged.get('final_answer'),
        'merged': merged,
        'proposals': proposals,
        'raw_result': result
    }


if __name__ == '__main__':
    # مثال سريع للتشغيل اليدوي
    q = "كيف يمكن إعادة تشغيل شبكة كهربائية بسيطة باستخدام مخلفات البناء خلال 6 أشهر في قرية؟"
    out = agl_universal_answer(q, context="سكان: 1000، موارد: حطام بناء، شمس قوية")
    print('\n--- FINAL ANSWER ---\n')
    print(out['final_answer'])
    print('\n--- PROVENANCE ---\n')
    print(json.dumps(out['merged']['provenance'], ensure_ascii=False, indent=2))
