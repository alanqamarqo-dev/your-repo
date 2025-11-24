# -*- coding: utf-8 -*-
try:
    from agl.rag.mock_provider import mock_answer # type: ignore
except Exception:
    # fall back to uppercase package if environment imports that
    from AGL.rag.mock_provider import mock_answer


def test_mock_answer_contains_keywords_ar():
    q = "لماذا انخفضت أسعار نفط 2020 مع COVID؟"
    out = mock_answer(q)
    assert out["ok"] is True
    assert out["contains_hints"] is True
    assert "2020" in out["text"] or "COVID" in out["text"] or "نفط" in out["text"]


def test_mock_answer_no_keywords():
    q = "سؤال عام بلا كلمات حاسمة."
    out = mock_answer(q)
    assert out["ok"] is True
    assert out["contains_hints"] is False
    assert "لا توجد كلمات مفتاحية" in out["text"]
