class GK_Reasoner_Dummy:
    name = "GK_reasoner"

    def __init__(self, verifier=None):
        self.verifier = verifier

    def process_task(self, task):
        hits = task.get("hits") or []
        claim = task.get("claim") or "inferred"
        return {"name": self.name, "ok": True, "conclusion": claim, "support": hits, "meta": {"stub": True}}
