# -*- coding: utf-8 -*-
import os
from typing import Dict, Any
from .intent_generator import IntentGenerator
from .intent_planner import IntentPlanner
from .perception_loop import PerceptionLoop
from .state_logger import StateLogger


class CLayer:
    """
    حلقة إدراكية خفيفة:
    - يقرأ السياق (PerceptionLoop)
    - يولّد Intents (IntentGenerator)
    - يطبقها (IntentPlanner)
    - يحفظ لقطة (StateLogger) وفق إشارة/دورية
    """
    def __init__(self, registry, meta_learning, context_provider=None):
        self.enabled = os.getenv("AGL_C_LAYER", "0") == "1"
        self.perception = PerceptionLoop(context_provider)
        self.generator = IntentGenerator()
        self.planner = IntentPlanner(registry, meta_learning)
        self.logger = StateLogger()

        self.tick_count = 0

    def tick(self, extra_state: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"enabled": False}
        self.tick_count += 1

        ctx = self.perception.read()
        ctx["tick_count"] = self.tick_count

        intents = self.generator.generate(ctx)
        plan_log = self.planner.apply(intents)

        snap_path = ""
        # لقطة إذا وُجد Intent لذلك أو وفق الدورية
        if any(i.kind.name == "TRIGGER_SNAPSHOT" for i in intents) or os.getenv("AGL_C_LAYER_FORCE_SNAPSHOT", "0") == "1":
            state = {
                "tick": self.tick_count,
                "context": ctx,
                "plan_log": plan_log,
                **(extra_state or {})
            }
            snap_path = self.logger.snapshot(state)

        return {
            "enabled": True,
            "tick": self.tick_count,
            "intents": [i.kind.name for i in intents],
            "plan_log": plan_log,
            "snapshot": snap_path
        }
