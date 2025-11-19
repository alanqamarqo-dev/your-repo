from Integration_Layer.Conversation_Manager import start_session, auto_route

def test_session_creation_and_history_iso():
    s = start_session("s_test_1")
    assert "created_at" in s and isinstance(s["history"], list)
    r = auto_route("s_test_1", "ما هو قانون نيوتن؟")
    assert r.get("ok", True)
    assert len(s["history"]) == 1
    ts = s["history"][0]["ts"]
    # تحقق بسيط من تقريب ISO 8601 (وجود T) ومن الأثر الزمني
    assert "T" in ts
