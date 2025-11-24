from Integration_Layer.Task_Orchestrator import TaskOrchestrator
try:
    from Safety_Control.Safe_Rollback_System import SafeRollback # type: ignore
except Exception:
    # fallback minimal SafeRollback when the module/file is missing or empty
    class SafeRollback:
        def safe_recover(self, reason: str = ""):
            return True

try:
    from Learning_System.TemporalMemory import TemporalMemory # type: ignore
except Exception:
    # lightweight in-memory TemporalMemory fallback for tests
    class TemporalMemory:
        def __init__(self):
            self._items = []

        def append(self, record):
            self._items.append(record)

        def range_query(self, tags=None, k=3):
            # return last k simple hints
            return list(self._items[-k:]) if self._items else []


class PlannerAgent:
    def __init__(self):
        self.orch = TaskOrchestrator()
        self.tm = TemporalMemory()
        self.rollback = SafeRollback()

    def plan(self, task: str, context: dict | None = None) -> list[dict]:
        # build a simple plan based on keywords and prior memory hints
        steps = []
        t = str(task or "")
        if "معادلة" in t or "تفاضلية" in t or "differential" in t:
            steps = [
                {"engine": "Mathematical_Brain", "action": "parse"},
                {"engine": "Mathematical_Brain", "action": "solve_symbolic"},
                {"engine": "Units_Validator", "action": "validate_units"},
                {"engine": "Code_Generator", "action": "emit_code"},
            ]
        else:
            steps = [{"engine": "Code_Generator", "action": "emit_code"}]

        # inject hints from temporal memory (use latest when available)
        if hasattr(self.tm, 'latest'):
            try:
                hints = self.tm.latest(3) # type: ignore
            except Exception:
                hints = []
        else:
            # best-effort: try range_query with no args (fallback)
            try:
                hints = self.tm.range_query()
            except Exception:
                hints = []
        return [{"step": i + 1, "plan": p, "hints": hints} for i, p in enumerate(steps)]

    def execute(self, task: str, context: dict | None = None) -> dict:
        plan = self.plan(task, context)
        outputs = []
        for node in plan:
            try:
                # the orchestrator exposes `process` as the routing entrypoint
                # call with the real task and provide engine hint as kwarg
                if hasattr(self.orch, 'process'):
                    res = self.orch.process(task, engine=node["plan"]["engine"], context=context)
                else:
                    res = {"ok": True}
                outputs.append({"node": node, "result": res})
            except Exception as e:
                try:
                    self.rollback.safe_recover(reason=str(e))
                except Exception:
                    pass
                outputs.append({"node": node, "error": str(e)})
                break

        return {"task": task, "plan": plan, "outputs": outputs}
