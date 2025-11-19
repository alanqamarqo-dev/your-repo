# -*- coding: utf-8 -*-
import os
from typing import List

from .intent_types import Intent, IntentKind


class IntentGenerator:
    """
    بسيط: يولّد Intentات خفيفة وفق إشارات داخلية/سياقية.
    يمكن استبداله لاحقًا بنموذج تعلم.
    """
    def __init__(self):
        self.enabled = os.getenv("AGL_C_LAYER_INTENT", "0") == "1"

    def generate(self, context: dict) -> List[Intent]:
        if not self.enabled:
            return []
        intents: List[Intent] = []

        # مثال: إذا رأى تذبذبًا في الاستقرار، زد وزن Consistency_Checker
        if context.get("stability_metric", 1.0) < 0.9:
            intents.append(Intent(
                kind=IntentKind.ADJUST_WEIGHT,
                params={"engine": "Consistency_Checker", "delta": +0.15},
                trace_id=context.get("trace_id"),
                source="IntentGenerator"
            ))

        # مثال: إذا زاد الحمل، قدّم Meta_Learning مبكرًا
        if context.get("load", 0.0) > 0.7:
            intents.append(Intent(
                kind=IntentKind.REORDER_ENGINES,
                params={"priority_front": ["Meta_Learning", "Reasoning_Planner"]},
                trace_id=context.get("trace_id"),
            ))

        # لقطة دورية مشروطة
        if context.get("tick_count", 0) % max(1, int(os.getenv("AGL_C_LAYER_SNAPSHOT_EVERY", "5"))) == 0:
            intents.append(Intent(
                kind=IntentKind.TRIGGER_SNAPSHOT,
                params={},
                trace_id=context.get("trace_id"),
            ))

        return intents
