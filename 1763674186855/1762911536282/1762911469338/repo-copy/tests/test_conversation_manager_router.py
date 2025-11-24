from Integration_Layer.Conversation_Manager import auto_route_and_respond, create_session, last_turn


def test_auto_route_translate_and_history(tmp_path):
    sid = 'test_auto'
    # create session
    create_session(sid)
    resp = auto_route_and_respond(sid, "ترجم hello الى ar")
    assert isinstance(resp, dict)
    assert 'intent' in resp and resp['intent'] in ("translate", "ask_info", "chitchat")
    lt = last_turn(sid)
    assert lt is not None and lt['user'] == "ترجم hello الى ar"
