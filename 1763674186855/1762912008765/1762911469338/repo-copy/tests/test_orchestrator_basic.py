import pytest

from Core_Engines.orchestrator import Orchestrator


class MockEngine:
    def __init__(self, name: str, score: float = 0.5):
        self.name = name
        self._score = score

    def process_task(self, payload: dict):
        # simple deterministic response using provided name and score
        return {"answer": f"resp from {self.name}", "score": float(self._score), "meta": payload.get("meta")}


def test_orchestrator_basic_routing_and_aggregation():
    engines = {
        "General_Knowledge": MockEngine("General_Knowledge", score=0.2),
        "Hosted_LLM": MockEngine("Hosted_LLM", score=0.9),
        "GK_retriever": MockEngine("GK_retriever", score=0.4),
    }

    orch = Orchestrator(engines=engines)

    result = orch.run_task("general_question", {"question": "what is AI?"})
    assert result["task_type"] == "general_question"
    assert isinstance(result["answers"], list)
    # best should be the Hosted_LLM with highest score
    assert result["best"]["engine"] == "Hosted_LLM"
    assert any("resp from Hosted_LLM" in a.get("answer", "") for a in result["answers"]) 


def test_update_priorities_changes_routing_order():
    engines = {
        "A": MockEngine("A", score=0.7),
        "B": MockEngine("B", score=0.6),
    }
    orch = Orchestrator(engines=engines)
    # initially weights are equal -> ordering by incoming route (domain_router controls candidates)
    # simulate domain_router.route by monkeypatching the function used by orchestrator
    from Core_Engines import domain_router

    orig_route = domain_router.route

    try:
        domain_router.route = lambda task_type: ["A", "B"]
        r1 = orch.run_task("some_task", {})
        assert r1["best"]["engine"] in ("A", "B")

        # give feedback that B should be preferred
        orch.update_priorities({"B": 5.0})
        routed = orch.route("some_task")
        assert routed[0] == "B"
    finally:
        domain_router.route = orig_route
