# -*- coding: utf-8 -*-
import os
from typing import Dict, Any, Callable, Optional


class PerceptionLoop:
    """
    يجمع مدخلات خارجية (سياق مستخدم/بيئة) كل tick.
    provider: دالة تُعيد dict سياقي (غير حتمي مسموح، لكن نستعمله بحذر).
    """
    def __init__(self, provider: Optional[Callable[[], Dict[str, Any]]] = None):
        self.enabled = os.getenv("AGL_C_LAYER_PERCEPTION", "0") == "1"
        self.provider = provider or (lambda: {})

    def read(self) -> Dict[str, Any]:
        if not self.enabled:
            return {}
        try:
            ctx = self.provider() or {}
            # تطبيع مفاتيح متوقعة:
            ctx.setdefault("user_intent", None)
            ctx.setdefault("load", 0.0)
            ctx.setdefault("stability_metric", 1.0)
            ctx.setdefault("trace_id", None)
            return ctx
        except Exception:
            return {}
