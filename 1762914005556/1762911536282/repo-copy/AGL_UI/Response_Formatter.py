def humanize(out: dict, lang="ar") -> str:
    if not out:
        return "لم يتم العثور على نتيجة."
    if not out.get("ok"):
        return out.get("message") or "لم تُنجز العملية."
    parts = []
    if "result" in out:
        parts.append(f"النتيجة: {out['result']}")
    if "explain" in out:
        parts.append(f"الشرح: {out['explain']}")
    if "confidence" in out:
        try:
            parts.append(f"الثقة: {out['confidence']:.2f}")
        except Exception:
            parts.append(f"الثقة: {out.get('confidence')}")
    if out.get("note"):
        parts.append(out["note"])
    return " | ".join(parts)
