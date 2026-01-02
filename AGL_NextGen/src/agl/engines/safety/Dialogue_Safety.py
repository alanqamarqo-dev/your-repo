def guard(output: dict) -> dict:
    out = dict(output or {})
    if not out.get("ok"):
        out["message"] = out.get("message", "⚠️ تعذّر التأكد من النتيجة بأمان.")
    if out.get("confidence") is not None and out["confidence"] < 0.5:
        out["note"] = "تنبيه: الثقة منخفضة، يُفضّل توفير بيانات أكثر أو تجربة بديلة."
    return out
