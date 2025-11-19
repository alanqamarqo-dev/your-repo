import pytest
from Integration_Layer.Output_Formatter import normalize


def test_normalize_cleans_neutral_prefix():
    payload = {"ok": True, "text": "(neutral) مرحبًا بك"}
    out = normalize(payload)
    assert out["reply_text"] == "مرحبًا بك"
    assert out["text"] == "مرحبًا بك"


def test_normalize_fallback_design():
    payload = {"ok": True, "design": {"type": "floorplan"}}
    out = normalize(payload)
    assert "تم توليد تصميم" in out["reply_text"]