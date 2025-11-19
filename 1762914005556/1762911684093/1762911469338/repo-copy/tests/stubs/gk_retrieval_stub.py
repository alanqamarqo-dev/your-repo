class _DummyKB:
    def query(self, q: str):
        return [{"fact": "COVID أثر اقتصادياً واجتماعياً", "confidence": 0.82}]


class GK_Retriever_Dummy:
    name = "GK_retriever"

    def __init__(self, kb=None):
        self.kb = kb or _DummyKB()

    def process_task(self, task):
        q = task.get("query") or task.get("text") or ""
        return {"name": self.name, "ok": True, "hits": self.kb.query(q), "meta": {"stub": True}}
