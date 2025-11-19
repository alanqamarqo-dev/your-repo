from Core_Engines.Social_Interaction import SocialInteractionEngine

def test_social():
    s = SocialInteractionEngine()
    m = s.group_dynamics(["لا أوافق!","أوافق","تمام"])
    assert 0.0 <= m["cohesion"] <= 1.0 and 0.0 <= m["conflict"] <= 1.0
    assert isinstance(s.empathic_reply(""), str)
