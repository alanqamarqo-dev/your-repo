# -*- coding: utf-8 -*-
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Any, Optional


class IntentKind(Enum):
    ADJUST_WEIGHT = auto()      # تعديل وزن/أولوية محرك
    REORDER_ENGINES = auto()    # إعادة ترتيب جدول التنفيذ
    TRIGGER_SNAPSHOT = auto()   # طلب حفظ لقطة حالة
    SET_SCOPE = auto()          # توجيه النطاق (stm/ltm/all)


@dataclass
class Intent:
    kind: IntentKind
    params: Dict[str, Any]
    trace_id: Optional[str] = None
    source: str = "C-Layer"
