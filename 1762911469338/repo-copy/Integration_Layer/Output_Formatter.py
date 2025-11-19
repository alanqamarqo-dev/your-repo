# Integration_Layer/Output_Formatter.py
class OutputFormatter:
    def _safe_engine_block(self, block):
        # None/empty -> not run
        if not block:
            return {"status": "not_run", "result": None}

        # If it's an error dict with an explicit error
        if isinstance(block, dict) and block.get('error'):
            return {"status": "error", "result": None, "error": block.get('error')}

        # If the engine returned a normalized envelope (ok/score/confidence/result), unpack it
        if isinstance(block, dict) and ("ok" in block or "confidence" in block or "score" in block):
            ok = bool(block.get('ok', True))
            status = "ok" if ok and not block.get('error') else "error"
            return {
                "status": status,
                "ok": ok,
                "score": float(block.get('score', 0.0) or 0.0),
                "confidence": float(block.get('confidence', block.get('score', 0.0) or 0.0)),
                "result": block.get('result'),
                "error": block.get('error')
            }

        # Fallback: return raw block as result
        return {"status": "ok", "result": block}

    def format_output(self, integrated_solution, audience="technical", purpose="solution"):
        """Return a structured output object without stringifying internal dicts.

        integrated_solution: dict expected to contain keys like 'result', 'details', 'confidence', etc.
        audience: target audience string
        purpose: purpose string
        """
        # Expect integrated_solution to have engine keys at top-level
        formatted_result = {
            "mathematical_brain": self._safe_engine_block(integrated_solution.get('mathematical_brain')),
            "quantum_processor": self._safe_engine_block(integrated_solution.get('quantum_processor')),
            "code_generator": self._safe_engine_block(integrated_solution.get('code_generator')),
            "protocol_designer": self._safe_engine_block(integrated_solution.get('protocol_designer')),
        }

        # Collect optional misc fields (verification/artifact/architecture/components)
        misc_fields = {}
        if integrated_solution.get('verification') is not None or integrated_solution.get('code_artifact') is not None:
            misc_fields = {
                'verification': integrated_solution.get('verification'),
                'artifact_path': integrated_solution.get('code_artifact'),
                'artifact_validated': integrated_solution.get('artifact_validated'),
                'artifact_sha256': integrated_solution.get('artifact_sha256'),
                'architecture': integrated_solution.get('architecture'),
                'components': integrated_solution.get('components')
            }

        return {
            "audience": audience,
            "purpose": purpose,
            "result": formatted_result,
            "details": integrated_solution.get("details", []),
            "misc": misc_fields,
            "confidence": float(integrated_solution.get("confidence", 0.0)),
            "complexity_level": integrated_solution.get("complexity_level", "adjusted"),
        }


def normalize(payload: dict) -> dict:
    # ensure a consistent envelope: {ok, text, data, meta}
    ok = bool(payload.get("ok", True))
    d = payload or {}
    import re
    def _clean(txt: str) -> str:
        if not isinstance(txt, str):
            return txt
        txt = re.sub(r'^\((neutral|positive|negative)\)\s*', '', txt, flags=re.I)
        return txt.strip()
    # Prefer 'answer' if present, then text/reply/message etc. Only pick the first valid string.
    candidates = []
    if isinstance(d.get('answer'), str) and d.get('answer').strip(): # type: ignore
        candidates.append(d.get('answer'))
    # common fallbacks
    candidates += [d.get("text"), d.get("reply"), d.get("translation"), d.get("description"), d.get("caption"), d.get("message"), d.get("reply_text")]
    reply = next((x for x in candidates if isinstance(x, str) and x.strip()), None)
    # لو مافيش نص واضح، جرب وجود تصميم بصري
    if not reply and isinstance(d.get("design"), dict):
        reply = "تم توليد تصميم بصري (انظر data.design)."
    text = reply or d.get("message") or d.get("reply_text") or ""
    # clean neutral/positive/negative prefixes
    text = _clean(text)

    # helper: remove repeated separators like '|' and collapse duplicated adjacent phrases
    import re
    def clean_text(s: str, max_len=3000) -> str:
        if not isinstance(s, str):
            return s
        # collapse repeated separators '|' ' - ' and long runs
        s = re.sub(r"\|{2,}", " | ", s)
        s = re.sub(r"(\s*\|\s*)+", " | ", s)
        s = re.sub(r"\s{2,}", " ", s)
        # collapse repeated adjacent substrings (simple heuristic)
        parts = s.split(' | ')
        seen = []
        out_parts = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if out_parts and p == out_parts[-1]:
                continue
            out_parts.append(p)
        s = ' | '.join(out_parts)
        # aggressive n-gram repeat collapse: if a phrase repeats twice in a row, keep one
        s = re.sub(r"(\b.+?\b)(?:\s+\1\b)+", r"\1", s)
        # trim to max_len
        if len(s) > max_len:
            s = s[:max_len-1] + '…'
        return s

    text = clean_text(text)
    data = d.get("data") or d.get("result") or d
    meta = {k: v for k, v in payload.items() if k not in ("ok", "text", "message", "data", "result", "reply_text")}
    # ensure reply_text is present for UI
    return {"ok": ok, "text": text, "reply_text": text, "data": data, "meta": meta}


def contains_cjk(s: str) -> bool:
    # detect CJK ranges to identify non-Arabic noise
    try:
        return bool(__import__('re').search(r"[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]", str(s)))
    except Exception:
        return False


def excessive_ascii_noise(s: str, threshold: float = 0.3) -> bool:
    # returns True if a high fraction of characters are non-Unicode-letters (ASCII symbols), indicating noise
    st = str(s or '')
    if not st:
        return False
    ascii_count = sum(1 for ch in st if ord(ch) < 128 and not ch.isalnum() and not ch.isspace())
    return (ascii_count / max(1, len(st))) > threshold


def ensure_relevance(ans: str, must_contain: list[str]):
    s = str(ans or '')
    ok = all(k in s for k in must_contain)
    foreign_noise = contains_cjk(s) or excessive_ascii_noise(s)
    if (not ok) or foreign_noise:
        raise ValueError("IrrelevantOrNoisyOutput")


def format_md(ans: str, must_contain: list[str] | None = None) -> str:
    if must_contain:
        ensure_relevance(ans, must_contain)
    return str(ans).strip()