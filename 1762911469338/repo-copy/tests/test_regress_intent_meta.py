from Integration_Layer.Intent_Recognizer import detect_intent


def test_meta_patterns_additional_phrases():
    sentences = [
        "تعلم بالتعميم",
        "لقطات قليلة",
        "تعلم بلقطات قليلة",
    ]
    for s in sentences:
        assert detect_intent(s) == "meta_learn"
