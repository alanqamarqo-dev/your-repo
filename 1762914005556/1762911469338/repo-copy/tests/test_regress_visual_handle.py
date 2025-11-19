from Core_Engines.Visual_Spatial import Visual_Spatial


def test_visual_handle_routing_describe():
    v = Visual_Spatial()
    out = v.handle({"text": "صف هذا المشهد"})
    assert out.get("ok") is True or "description" in out


def test_visual_handle_routing_generate():
    v = Visual_Spatial()
    out = v.handle({"text": "ولّد تخطيط غرفة"})
    assert out.get("ok") is True or "design" in out
