# -*- coding: utf-8 -*-
from Core_Engines.Visual_Spatial import VisualSpatialEngine
import numpy as np

def test_analyze_spatial_description():
    eng = VisualSpatialEngine()
    r = eng.analyze_spatial_description("الكرة فوق الطاولة")
    assert r["relation"] == "above"
    assert isinstance(r["objects"], list)

def test_generate_and_place_object():
    eng = VisualSpatialEngine()
    scene = eng.generate_3d_matrix(4,4,4)
    assert scene.shape == (4,4,4)
    scene = eng.place_object(scene, (1,1,1), (2,1,1))
    assert int(scene.sum()) > 0

def test_simulate_rotation_and_consistency():
    eng = VisualSpatialEngine()
    p = (1.0, 0.0, 0.0)
    rotated = eng.simulate_rotation(p, axis="z", angle_deg=90)
    assert isinstance(rotated, tuple) and len(rotated)==3
    rels = [
        {"relation":"above","objects":["ball","table"]},
        {"relation":"inside","objects":["box","drawer"]}
    ]
    score = eng.compute_spatial_consistency(rels)
    assert 0.0 <= score <= 100.0
