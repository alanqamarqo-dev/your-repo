# -*- coding: utf-8 -*-
import os
from typing import List

from .intent_types import Intent, IntentKind


class IntentPlanner:
    """
    يترجم الـ Intents إلى أفعال على سجلّ المحركات/Meta_Learning.
    يتوقّع واجهة مبسّطة من registry و meta_learning (محاكاة هنا).
    """
    def __init__(self, registry, meta_learning):
        self.registry = registry
        self.meta_learning = meta_learning
        self.enabled = os.getenv("AGL_C_LAYER_INTENT", "0") == "1"

    def apply(self, intents: List[Intent]) -> List[str]:
        if not self.enabled:
            return []
        log: List[str] = []
        for it in intents:
            if it.kind is IntentKind.ADJUST_WEIGHT:
                eng, delta = it.params.get("engine"), it.params.get("delta", 0.0)
                if eng:
                    # delegate to meta_learning
                    try:
                        self.meta_learning.adjust_engine_weight(eng, delta)
                    except Exception:
                        pass
                    log.append(f"Adjusted weight: {eng} += {delta}")
            elif it.kind is IntentKind.REORDER_ENGINES:
                front = it.params.get("priority_front", [])
                if front:
                    try:
                        self.registry.prioritize(front)
                    except Exception:
                        pass
                    log.append(f"Reordered engines (front): {front}")
            elif it.kind is IntentKind.TRIGGER_SNAPSHOT:
                # يُنفَّذ فعليًا من C-Layer tick بالدمج مع StateLogger
                log.append("Snapshot requested")
            elif it.kind is IntentKind.SET_SCOPE:
                scope = it.params.get("scope", "stm")
                try:
                    self.meta_learning.set_scope(scope)
                except Exception:
                    pass
                log.append(f"Scope set to {scope}")
        return log
