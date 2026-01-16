import time
import json
from typing import Any, Dict

from agl.engines.self_improvement.Self_Improvement.hosted_llm_adapter import HostedLLMAdapter


PROJECT_TITLE_DEFAULT = "Ø§Ù„Ø£Ø¯ÙˆÙŠØ© Ø§Ù„Ù…Ù‡Ø±Ù‘Ø¨Ø© Ø¨ÙŠÙ† ØªØ­Ø¯Ù‘ÙŠØ§Øª Ø§Ù„Ø±Ù‚Ø§Ø¨Ø© Ø§Ù„Ø¯ÙˆØ§Ø¦ÙŠØ© ÙˆØ§Ù„Ø­Ø§Ø¬Ø© Ø§Ù„Ø¹Ù„Ø§Ø¬ÙŠØ© Ù„Ù„Ù…Ø±Ø¶Ù‰"


def _build_prompt(question: str, project_title: str, max_points: int) -> str:
    return (
        f"Ø£Ù†Øª ØªØ¹Ù…Ù„ ÙƒÙ†Ø¸Ø§Ù… Ø¯Ø¹Ù… Ù…Ø¹Ø±ÙÙŠ Ø¨Ø­Ø«ÙŠ (AGL) ÙŠØ³Ø§Ø¹Ø¯ Ø¨Ø§Ø­Ø«ÙŠÙ† ÙÙŠ Ø¥Ø¹Ø¯Ø§Ø¯ Ø¨Ø­Ø« Ù…ÙŠØ¯Ø§Ù†ÙŠ Ø¨Ø¹Ù†ÙˆØ§Ù†:\n"
        f"Â«{project_title}Â» ÙÙŠ Ù…Ø­Ø§ÙØ¸Ø© Ù…Ø£Ø±Ø¨ â€“ Ø§Ù„ÙŠÙ…Ù†.\n\n"
        f"Ø§Ù„Ù…Ø·Ù„ÙˆØ¨:\n- Ø¥Ø¹Ø·Ø§Ø¡ Ø¥Ø¬Ø§Ø¨Ø© Ø·Ø¨ÙŠØ©/Ø¯ÙˆØ§Ø¦ÙŠØ© Ø¹Ù„Ù…ÙŠØ© Ù‚Ø¯Ø± Ø§Ù„Ø¥Ù…ÙƒØ§Ù† (Ù…Ø¹ Ø¥Ø¯Ø±Ø§Ùƒ Ø£Ù†Ùƒ Ù†Ù…ÙˆØ°Ø¬ Ù„ØºÙˆÙŠ).\n"
        f"- ØªØ±ÙƒÙŠØ² Ø®Ø§Øµ Ø¹Ù„Ù‰: Ù…Ø±Ø¶Ù‰ Ø§Ù„ÙØ´Ù„ Ø§Ù„ÙƒÙ„ÙˆÙŠØŒ ÙˆØªØ¯Ø§Ø®Ù„Ø§Øª Ø§Ù„Ø£Ø¯ÙˆÙŠØ© Ø§Ù„Ù…Ù‡Ø±Ù‘Ø¨Ø© Ù…Ø¹Ù‡Ù….\n"
        f"- ØªÙ†Ø¸ÙŠÙ… Ø§Ù„Ø¥Ø¬Ø§Ø¨Ø© ÙÙŠ Ù†Ù‚Ø§Ø· ÙˆØ§Ø¶Ø­Ø© Ø­ØªÙ‰ Ø­Ø¯ Ø£Ù‚ØµÙ‰ â‰ˆ {max_points} Ù…Ø­Ø§ÙˆØ±.\n\n"
        f"Ø³Ø¤Ø§Ù„ Ø§Ù„Ø¨Ø§Ø­Ø« (Ø£Ø¬Ø¨ Ø¨Ø§Ù„Ø¹Ø±Ø¨ÙŠØ© Ø§Ù„ÙØµØ­Ù‰ ÙˆØ¨Ø´ÙƒÙ„ Ù…ÙˆØ¬Ø² ÙˆÙ…Ù†Ø¸Ù…):\n{question}"
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
        # no good whitespace found â€” hard cut
        return text[:max_chars].rstrip() + "..."
    return text[:cut].rstrip() + "..."


def local_fallback_rewrite(raw_text: str, question: str) -> str:
    # 1) clean line-by-line and remove leading bullets/markers
    lines = [
        line.strip(" -â€¢\u2022")
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
        f"ÙÙŠ Ø³ÙŠØ§Ù‚ Ø³Ø¤Ø§Ù„ Ø§Ù„Ø¨Ø§Ø­Ø« Ø­ÙˆÙ„: Â«{question}Â»ØŒ ÙŠÙ…ÙƒÙ† ØªÙ„Ø®ÙŠØµ Ø£Ø¨Ø±Ø² Ø§Ù„Ù†Ù‚Ø§Ø· Ø¹Ù„Ù‰ Ø§Ù„Ù†Ø­Ùˆ Ø§Ù„Ø¢ØªÙŠ: "
        f"{base} "
        f"ÙˆÙŠÙØ¸Ù‡Ø± Ø°Ù„Ùƒ Ø£Ù† Ø¸Ø§Ù‡Ø±Ø© ØªØ¯Ø§ÙˆÙ„ Ø§Ù„Ø£Ø¯ÙˆÙŠØ© Ø§Ù„Ù…Ù‡Ø±Ù‘Ø¨Ø© ØªÙ…Ø«Ù‘Ù„ Ù…Ø´ÙƒÙ„Ø© ØµØ­ÙŠØ© ÙˆØ³Ø±ÙŠØ±ÙŠØ© Ø­Ù‚ÙŠÙ‚ÙŠØ©ØŒ "
        f"Ø®ØµÙˆØµÙ‹Ø§ Ù„Ø¯Ù‰ Ø§Ù„ÙØ¦Ø§Øª Ø¹Ø§Ù„ÙŠØ© Ø§Ù„Ø®Ø·ÙˆØ±Ø©ØŒ Ù…Ø§ ÙŠØ³ØªØ¯Ø¹ÙŠ ØªØ¹Ø²ÙŠØ² Ø§Ù„Ø±Ù‚Ø§Ø¨Ø© Ø§Ù„Ø¯ÙˆØ§Ø¦ÙŠØ© "
        f"ÙˆØªÙˆØ¹ÙŠØ© Ø§Ù„Ù…Ø±Ø¶Ù‰ ÙˆÙ…Ù‚Ø¯Ù‘Ù…ÙŠ Ø§Ù„Ø®Ø¯Ù…Ø©."
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
                "Ø§Ù„Ø³ÙŠØ§Ù‚ Ø§Ù„Ù…Ø³ØªØ±Ø¬Ø¹ Ù…Ù† Ù…Ø±Ø¬Ø¹ Ø¨Ø­Ø«ÙŠ Ø¹Ù† Ø§Ù„Ø£Ø¯ÙˆÙŠØ© Ø§Ù„Ù…Ù‡Ø±Ù‘Ø¨Ø©:\n" + answer_text + "\n\n"
                "Ø§Ù„Ù…Ø·Ù„ÙˆØ¨:\n"
                "- Ø£Ø¹Ø¯ ØµÙŠØ§ØºØ© Ø¬ÙˆØ§Ø¨ Ø£ÙƒØ§Ø¯ÙŠÙ…ÙŠ Ù…Ù†Ø¸Ù… ÙˆÙˆØ§Ø¶Ø­ Ø¨Ø§Ù„Ø¹Ø±Ø¨ÙŠØ©.\n"
                "- Ø±ÙƒÙ‘Ø² ÙÙ‚Ø· Ø¹Ù„Ù‰ Ù…Ø§ ÙŠØ®Øµ Ø³Ø¤Ø§Ù„ Ø§Ù„Ø¨Ø§Ø­Ø« Ø§Ù„ØªØ§Ù„ÙŠØŒ ÙˆØ§Ø¨ØªØ¹Ø¯ Ø¹Ù† Ø§Ù„Ø­Ø´Ùˆ: \n"
                f"  \"{question}\"\n"
                "- Ø§Ù„Ù†ØªÙŠØ¬Ø©: 1) Ù…Ù‚Ø¯Ù…Ø© Ù‚ØµÙŠØ±Ø© ØªØ±Ø¨Ø· Ø§Ù„Ø³Ø¤Ø§Ù„ Ø¨Ø§Ù„Ø³ÙŠØ§Ù‚ØŒ 2) Ù†Ù‚Ø§Ø· Ø±Ø¦ÙŠØ³ÙŠØ© Ù…Ù†Ø¸Ù…Ø© (Ø³Ø¨Ø¨ â†’ Ø£Ø«Ø±ØŒ Ø³Ø±ÙŠØ±ÙŠÙ‹Ø§ ÙˆÙ…Ø¬ØªÙ…Ø¹ÙŠÙ‹Ø§)ØŒ 3) ÙÙ‚Ø±Ø© Ø®ØªØ§Ù…ÙŠØ© ØªÙ„Ø®Ù‘Øµ Ø§Ù„Ø¯Ù„Ø§Ù„Ø§Øª ÙˆØ§Ù„ØªÙˆØµÙŠØ§Øª.\n"
                "- ØªØ¬Ù†Ù‘Ø¨ Ø§Ù„Ù†Ø³Ø® Ø§Ù„Ø­Ø±ÙÙŠ Ù„Ù„Ø¬Ù…Ù„ Ù…Ù† Ø§Ù„Ù…ØµØ¯Ø± Ù‚Ø¯Ø± Ø§Ù„Ø¥Ù…ÙƒØ§Ù†Ø› Ø£Ø¹Ø¯ Ø§Ù„ØµÙŠØ§ØºØ© Ø¨Ø£Ø³Ù„ÙˆØ¨ ÙˆØ§Ø¶Ø­ ÙˆØ¨Ù„ÙŠØºØŒ ÙˆØ§Ø³ØªØ®Ø¯Ù… Ù„ØºØ© Ø£ÙƒØ§Ø¯ÙŠÙ…ÙŠØ© Ù…Ø®ØªØµØ±Ø©.\n"
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

