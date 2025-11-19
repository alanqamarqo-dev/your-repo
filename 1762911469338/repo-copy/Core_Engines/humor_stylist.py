"""Humor/Irony Stylist
Adds a light, context-appropriate tone when requested.
"""
from typing import Dict, Any

class HumorIronyStylist:
    name = "Humor_Irony_Stylist"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = payload.get("draft") or payload.get("text") or ""
        tone = payload.get("tone", "light")
        if not draft:
            return {"ok": False, "reason": "no input"}
        if tone == "light":
            text = draft + "\n\nملاحظة خفيفة: (نبرة مرِحة) — هذه ليست توصية رسمية، اجربها بحذر." 
        else:
            text = draft
        return {"ok": True, "engine": self.name, "text": text}


def factory():
    return HumorIronyStylist()
