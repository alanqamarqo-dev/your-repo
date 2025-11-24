# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
import math
import os
import numpy as np

# configurable small knobs for visual/spatial helpers
try:
    _AGL_VISUAL_SPATIAL_OBJECTS_LIMIT = int(os.environ.get('AGL_VISUAL_SPATIAL_OBJECTS_LIMIT', '2'))
except Exception:
    _AGL_VISUAL_SPATIAL_OBJECTS_LIMIT = 2
try:
    _AGL_VISUAL_SPATIAL_DEFAULT_DIM = int(os.environ.get('AGL_VISUAL_SPATIAL_DEFAULT_DIM', '5'))
except Exception:
    _AGL_VISUAL_SPATIAL_DEFAULT_DIM = 5

try:
    from Core_Engines.engine_base import Engine  # type: ignore
    from Core_Engines.engine_base import EngineRegistry
except Exception:
    class Engine:
        name: str = "EngineBase"
        version: str = "0.0"
        capabilities: List[str] = []
        def info(self) -> Dict[str, Any]:
            return {"name": self.name, "version": self.version, "capabilities": self.capabilities}
        def configure(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)
        def healthcheck(self) -> Dict[str, Any]:
            return {"ok": True}


class VisualSpatialEngine(Engine):
    """
    محرك التصور البصري والمكاني:
    - تحليل العلاقات المكانية من أوصاف أو مصفوفات.
    - بناء تمثيل ثلاثي الأبعاد تقريبي.
    - تقييم التناسق المكاني بين الأجسام.
    - محاكاة دوران وتحريك الأجسام.
    """
    name = "VisualSpatialEngine"
    version = "2.0.0"
    capabilities = [
        "spatial_relation_analysis",
        "3d_scene_representation",
        "geometric_reasoning",
        "motion_simulation"
    ]

    def analyze_spatial_description(self, text: str) -> Dict[str, Any]:
        t = (text or "").lower()
        rel = "unknown"
        if "فوق" in t or "above" in t:
            rel = "above"
        elif "تحت" in t or "below" in t:
            rel = "below"
        elif "داخل" in t or "inside" in t:
            rel = "inside"
        elif "خارج" in t or "outside" in t:
            rel = "outside"
        elif "بجانب" in t or "near" in t:
            rel = "near"
        elif "أمام" in t or "in front" in t:
            rel = "front"
        elif "خلف" in t or "behind" in t:
            rel = "behind"

        # استخراج الكائنات المحتملة (حذف علامات بسيطة)
            tokens = [w.strip(".,") for w in t.split()]
            stop = {"فوق","تحت","داخل","خارج","بجانب","أمام","خلف","the","on","in","under","near","above","below","inside","outside","front","behind"}
            objects = [w for w in tokens if w.isalpha() and w not in stop]
            objs = list(dict.fromkeys(objects))
            return {"relation": rel, "objects": objs[:_AGL_VISUAL_SPATIAL_OBJECTS_LIMIT], "description": text.strip()}

    def describe_or_generate(self, text: str) -> Dict[str, Any]:
        t = (text or "").lower()
        if any(k in t for k in ["صف", "وصف", "مشهد", "شارع", "غرفة"]):
            desc = "وصف مشهد: " + (text or "مشهد عام")
            return {"ok": True, "description": desc, "text": desc}

        if any(k in t for k in ["3d", "ثلاثي", "تخطيط", "صوّر", "صمم", "غرفة"]):
            design = {
                "type": "room-layout-3D",
                "objects": [
                    {"name": "bed", "pos": [1.2, 0.0, 2.4]},
                    {"name": "desk", "pos": [0.8, 0.0, 1.0]},
                ],
            }
            caption = "تم توليد تخطيط غرفة ثلاثي الأبعاد مبسّط."
            return {"ok": True, "design": design, "caption": caption, "text": caption}

        return {"ok": True, "text": "تحليل بصري: " + (text or "")}

    def generate_3d_matrix(self, width:int=_AGL_VISUAL_SPATIAL_DEFAULT_DIM, height:int=_AGL_VISUAL_SPATIAL_DEFAULT_DIM, depth:int=_AGL_VISUAL_SPATIAL_DEFAULT_DIM) -> np.ndarray:
        return np.zeros((width, height, depth), dtype=int)

    def place_object(self, scene: np.ndarray, pos: Tuple[int,int,int], size: Tuple[int,int,int]=(1,1,1)) -> np.ndarray:
        x,y,z = pos
        sx,sy,sz = size
        # clamp indices to scene bounds
        x2 = max(0, min(x, scene.shape[0]-1))
        y2 = max(0, min(y, scene.shape[1]-1))
        z2 = max(0, min(z, scene.shape[2]-1))
        x_end = max(x2+1, min(scene.shape[0], x2+sx))
        y_end = max(y2+1, min(scene.shape[1], y2+sy))
        z_end = max(z2+1, min(scene.shape[2], z2+sz))
        scene[x2:x_end, y2:y_end, z2:z_end] = 1
        return scene

    def simulate_rotation(self, point: Tuple[float,float,float], axis:str="z", angle_deg:float=90.0) -> Tuple[float,float,float]:
        x,y,z = point
        angle = math.radians(angle_deg)
        if axis == "x":
            y2 = y*math.cos(angle) - z*math.sin(angle)
            z2 = y*math.sin(angle) + z*math.cos(angle)
            return (x, y2, z2)
        elif axis == "y":
            x2 = x*math.cos(angle) + z*math.sin(angle)
            z2 = -x*math.sin(angle) + z*math.cos(angle)
            return (x2, y, z2)
        elif axis == "z":
            x2 = x*math.cos(angle) - y*math.sin(angle)
            y2 = x*math.sin(angle) + y*math.cos(angle)
            return (x2, y2, z)
        return (x, y, z)

    def compute_spatial_consistency(self, relations: List[Dict[str,Any]]) -> float:
        score = 100.0
        seen_pairs = set()
        for rel in relations:
            r = rel.get("relation")
            objs = tuple(sorted(rel.get("objects",[])))
            if objs in seen_pairs:
                score -= 10.0
            else:
                seen_pairs.add(objs)
            if r == "unknown":
                score -= 5.0
        return max(0.0, min(100.0, score))

    # backward-compatible wrapper
    def image_describe(self, image_obj: object) -> str:
        # lightweight textual description for tests: returns a brief Arabic label
        return "وصف بسيط للصورة: لا يتوفر تنفيذ كامل"

    # compatibility helper expected by tests
    def project_3d(self, dims: Dict[str, int]) -> Tuple[int,int,int]:
        w = int(dims.get("w", dims.get("width", _AGL_VISUAL_SPATIAL_DEFAULT_DIM)))
        h = int(dims.get("h", dims.get("height", _AGL_VISUAL_SPATIAL_DEFAULT_DIM)))
        d = int(dims.get("d", dims.get("depth", _AGL_VISUAL_SPATIAL_DEFAULT_DIM)))
        return (w, h, d)


# Backwards-compatible facade expected by older tests/modules
class Visual_Spatial:
    """Lightweight facade providing describe/generate/handle entrypoints used by tests."""
    def __init__(self):
        try:
            self._impl = VisualSpatialEngine()
        except Exception:
            self._impl = None

    def describe(self, text: str) -> Dict[str, Any]:
        if self._impl and hasattr(self._impl, 'describe_or_generate'):
            return self._impl.describe_or_generate(text)
        return {"ok": True, "description": "مشهد افتراضي: لا تنفيذ كامل"}

    def generate(self, text: str) -> Dict[str, Any]:
        if self._impl and hasattr(self._impl, 'generate_3d_matrix'):
            return {"ok": True, "design": {"note": "generated (stub)"}}
        return {"ok": True, "design": {"note": "no impl"}}

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # accept dict with 'text' or 'scene'
        text = payload.get('text') if isinstance(payload, dict) else str(payload)
        return self.describe(text or "")

    # alias used by some integration points
    def describe_or_generate(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            text = payload.get('text') or payload.get('scene') or ''
        else:
            text = str(payload)
        return self.handle({'text': text})

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.handle(payload)

# Backwards-compatible alias expected by bootstrap/ENGINE_SPECS
# Some parts of the code expect a class named `VisualSpatial` — alias it here.
VisualSpatial = Visual_Spatial  # type: ignore

