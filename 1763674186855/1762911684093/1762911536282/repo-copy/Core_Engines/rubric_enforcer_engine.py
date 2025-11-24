from typing import Dict, Any
from .rubric_enforcer import enforce as _enforce


class RubricEnforcer:
    name = "Rubric_Enforcer"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = payload.get("text") or ""
        try:
            out = _enforce(text)
            return {"ok": True, "text": out}
        except Exception as e:
            return {"ok": False, "reason": str(e)}


def factory():
    return RubricEnforcer()
