from typing import Dict, Any

class HumorIronyStylist:
    name = "Humor_Irony_Stylist"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = payload.get("draft") or (payload.get("text", ""))  # Simplify the condition
        tone = payload.get("tone", "light")

        if not draft:
            return {"ok": False, "reason": "no input"}

        humor_tip = "\n\n💡 Light Humor Tip: (A light-hearted note) — This is not official advice, use with caution." if tone == "light" else ""

        text = f"{draft}{humor_tip}"  # Simplify the condition check

        return {"ok": True, "engine": self.name, "text": text}


def factory():
    return HumorIronyStylist()