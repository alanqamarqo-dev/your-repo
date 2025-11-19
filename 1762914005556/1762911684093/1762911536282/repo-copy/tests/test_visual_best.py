from Core_Engines.Visual_Spatial import VisualSpatialEngine

def test_visual():
    v = VisualSpatialEngine()
    assert v.image_describe(object()).startswith("وصف")
    assert v.project_3d({"w":2,"h":3,"d":4}) == (2,3,4)
