import pytest
from Core_Engines.NLP_Advanced import NLPAdvanced


def test_nlp_advanced_intent_and_tone():
    nlp = NLPAdvanced()
    out = nlp.respond("من فضلك ترجم هذا النص إلى الإنجليزية: مرحباً بكم")
    assert out["intent"]["label"] in {"translate", "explain", "qa", "chitchat"}
    assert "text" in out and isinstance(out["text"], str)


def test_nlp_memory_context_summary():
    nlp = NLPAdvanced({"memory": {"max_turns": 3}})
    nlp.respond("السلام عليكم")
    nlp.respond("أريد شرح مبسّط للنسبية")
    res = nlp.respond("كم عمر الكون؟")
    assert len(nlp.mem.get_recent()) <= 3
    assert isinstance(res["context_used"], str)


def test_style_adapter_formal_vs_friendly():
    nlp = NLPAdvanced()
    formal = nlp.respond("اشرح الانحدار اللوجستي بنبرة رسمية ومختصرة")
    friendly = nlp.respond("اشرحها لكن بأسلوب بسيط وودّي")
    assert formal["text"] != friendly["text"]
