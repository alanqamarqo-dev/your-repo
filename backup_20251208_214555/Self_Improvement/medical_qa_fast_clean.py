import time
import json
from typing import Any, Dict

from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter


PROJECT_TITLE_DEFAULT = "الأدوية المهرّبة بين تحدّيات الرقابة الدوائية والحاجة العلاجية للمرضى"


def _build_prompt(question: str, project_title: str, max_points: int) -> str:
    return (
        f"أنت تعمل كنظام دعم معرفي بحثي (AGL) يساعد باحثين في إعداد بحث ميداني بعنوان:\n"
        f"«{project_title}» في محافظة مأرب – اليمن.\n\n"
        f"المطلوب:\n- إعطاء إجابة طبية/دوائية علمية قدر الإمكان (مع إدراك أنك نموذج لغوي).\n"
        f"- تركيز خاص على: مرضى الفشل الكلوي، وتداخلات الأدوية المهرّبة معهم.\n"
        f"- تنظيم الإجابة في نقاط واضحة حتى حد أقصى ≈ {max_points} محاور.\n\n"
        f"سؤال الباحث (أجب بالعربية الفصحى وبشكل موجز ومنظم):\n{question}"
    )


def _trim_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def _extract_response_from_stream(raw_answer: str) -> str:
    # Assemble newline-delimited JSON streaming responses into readable text.
    # Join chunks with a single space to avoid accidental word concatenation
    # while preserving streamed fragment boundaries.
    chunks = []
    for line in (raw_answer or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            # if the line isn't JSON, include it as a fallback
            chunks.append(line)
            continue
        # prefer common response keys
        resp = obj.get("response") or obj.get("content") or obj.get("answer")
        if isinstance(resp, str):
            chunks.append(resp.strip())
    if chunks:
        return " ".join(chunks).strip()
    return (raw_answer or "").strip()


def _trim_chars(text: str, max_chars: int) -> str:
    """Trim text to at most `max_chars` characters without cutting a word in half.

    If trimming is necessary, prefer to cut at the last whitespace before the limit
    and append an ellipsis.
    """
    if not text or len(text) <= max_chars:
        return text
    # try to cut at last whitespace before max_chars
    cut = text.rfind(" ", 0, max_chars)
    if cut == -1 or cut < int(max_chars * 0.6):
        # no good whitespace found — hard cut
        return text[:max_chars].rstrip() + "..."
    return text[:cut].rstrip() + "..."


def local_fallback_rewrite(raw_text: str, question: str) -> str:
    # 1) clean line-by-line and remove leading bullets/markers
    lines = [
        line.strip(" -•\u2022")
        for line in (raw_text or "").splitlines()
        if line.strip()
    ]
    base = " ".join(lines)

    # 2) shorten if too long
    max_len = 2000
    if len(base) > max_len:
        base = base[:max_len].rstrip() + "..."

    # 3) wrap into a simple academic Arabic template
    return (
        f"في سياق سؤال الباحث حول: «{question}»، يمكن تلخيص أبرز النقاط على النحو الآتي: "
        f"{base} "
        f"ويُظهر ذلك أن ظاهرة تداول الأدوية المهرّبة تمثّل مشكلة صحية وسريرية حقيقية، "
        f"خصوصًا لدى الفئات عالية الخطورة، ما يستدعي تعزيز الرقابة الدوائية "
        f"وتوعية المرضى ومقدّمي الخدمة."
    )


def medical_qa_fast(
    question: str,
    project_title: str = PROJECT_TITLE_DEFAULT,
    timeout_s: float = 120.0,
    max_points: int = 5,
    max_words: int = 300,
) -> Dict[str, Any]:
    adapter = HostedLLMAdapter()

    # Build the project-aware prompt and let the adapter handle RAG retrieval
    prompt = _build_prompt(question=question, project_title=project_title, max_points=max_points)

    t0 = time.time()
    try:
        # Use process_task so HostedLLMAdapter can prepend RAG context when available
        # Ask adapter to prefer RAG short-circuit so we can inspect retrieved passages
        task = {"question": prompt, "task_type": "qa_single", "engine_hint": "rag"}
        out = adapter.process_task(task, timeout_s=timeout_s)
    except Exception:
        # fallback to direct call if process_task isn't available for some reason
        try:
            raw = adapter.call_ollama(prompt, timeout=timeout_s)
            out = {"content": {"answer": raw}, "provenance": {}}
        except Exception:
            out = {"content": {"answer": ""}, "provenance": {}}
    t1 = time.time()
    elapsed = float(t1 - t0)

    # Normalize adapter output shapes
    if isinstance(out, dict):
        answer_text = out.get("answer") or (out.get("content") or {}).get("answer") or ""
        prov = out.get("provenance") or out.get("meta") or {}
    else:
        answer_text = str(out)
        prov = {}

    answer_text = answer_text if isinstance(answer_text, str) else str(answer_text)
    answer_text = _extract_response_from_stream(answer_text)

    # If adapter indicated a RAG short-circuit / RAG source, attempt hosted rewriter
    rewriter_info = {"engine": "hosted_llm", "method": "call_ollama", "rewritten": False}
    rewritten_answer = None
    try:
        raw_prov = prov if isinstance(prov, dict) else {}
        source = raw_prov.get("source") or (raw_prov.get("raw_provenance") or {}).get("source")
        if source in ("rag_shortcircuit", "rag_pipeline", "rag_hybrid", "rag") and answer_text:
            rewriter_prompt = (
                "السياق المسترجع من مرجع بحثي عن الأدوية المهرّبة:\n" + answer_text + "\n\n"
                "المطلوب:\n"
                "- أعد صياغة جواب أكاديمي منظم وواضح بالعربية.\n"
                "- ركّز فقط على ما يخص سؤال الباحث التالي، وابتعد عن الحشو: \n"
                f"  \"{question}\"\n"
                "- النتيجة: 1) مقدمة قصيرة تربط السؤال بالسياق، 2) نقاط رئيسية منظمة (سبب → أثر، سريريًا ومجتمعيًا)، 3) فقرة ختامية تلخّص الدلالات والتوصيات.\n"
                "- تجنّب النسخ الحرفي للجمل من المصدر قدر الإمكان؛ أعد الصياغة بأسلوب واضح وبليغ، واستخدم لغة أكاديمية مختصرة.\n"
            )
            try:
                hosted_out = adapter.call_ollama(rewriter_prompt, timeout=timeout_s)
                hosted_out = _extract_response_from_stream(hosted_out)
                # prefer safe character-based trimming to avoid mid-word cuts
                hosted_out = _trim_chars(hosted_out, max_chars=4000)
                if hosted_out and hosted_out.strip():
                    rewritten_answer = hosted_out
                    rewriter_info["rewritten"] = True
            except Exception as e:
                # record error and fall through to local fallback
                try:
                    rewriter_info["error"] = str(e)
                except Exception:
                    rewriter_info["error"] = "rewrite-hosted-exception"
    except Exception:
        # any unexpected error here shouldn't break the fast path
        try:
            rewriter_info["error"] = "rewrite-detection-exception"
        except Exception:
            pass

    # If hosted rewriter didn't produce usable text, use local fallback rewriter
    if not rewritten_answer:
        try:
            rewritten_answer = local_fallback_rewrite(answer_text, question)
            # note in provenance that local template was used
            rewriter_info["fallback_local"] = True
            rewriter_info["fallback_engine"] = "local_template"
        except Exception:
            # last-resort: keep original answer_text
            rewritten_answer = answer_text
            rewriter_info["fallback_local"] = False

    # final trimming / ensure length bound
    answer_text = _trim_chars(rewritten_answer or "", max_chars=4000)

    provenance: Dict[str, Any] = {
        "engine": "medical_qa_fast_clean",
        "steps": [{"t": "call_1", "ts": t0, "elapsed_s": elapsed}],
        "raw_provenance": prov,
    }
    # always attach rewriter info (hosted attempt + local-fallback status)
    provenance["rewriter"] = rewriter_info

    return {"answer": answer_text, "provenance": provenance, "latency_s": elapsed, "steps": [elapsed]}
