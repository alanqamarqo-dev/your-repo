from Core_Engines.NLP_Advanced import NLPAdvancedEngine, NLPUtterance

def test_nlp_end_to_end():
    eng = NLPAdvancedEngine()
    hist = [NLPUtterance("user","ترجم hello الى ar","ar")]
    ctx = eng.understand_context(hist); assert ctx["dominant_lang"] == "ar"
    intent = eng.analyze_intent(hist[0].text); assert intent.intent in {"translate","ask_info"}
    out,_ = eng.translate("hello","en","ar"); assert "مرحب" in out or out.startswith("[en->ar]")
    rep = eng.generate_reply(hist); assert isinstance(rep,str) and len(rep)>0 # type: ignore
