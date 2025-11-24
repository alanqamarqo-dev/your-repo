def test_agl_pipeline_injects_rag_context(monkeypatch):
    from Self_Improvement.Knowledge_Graph import agl_pipeline

    class FakeCollective:
        def query_shared_memory(self, keywords=None, limit=10):
            return [{"learning": {"note": "You once said: Bring an umbrella."}}]

        def synthesize(self, records):
            return {"summary": "You once said: Bring an umbrella.", "concepts": ["umbrella"]}

    class FakeCIE:
        def __init__(self):
            # provide collective fallback used by agl_pipeline when rag_lite is absent
            self.collective = FakeCollective()
            self.called_problem = None

        def collaborative_solve(self, problem, domains_needed=None):
            self.called_problem = problem
            return {"winner": {"engine": "hosted_storyqa", "content": {"answer": "raw answer"}}, "top": []}

        def format_final_answer(self, problem, res, **kwargs):
            # mimic formatting behavior: pull answer from res.winner.content.answer
            ans = ''
            try:
                ans = (res.get('winner') or {}).get('content', {}).get('answer', '')
            except Exception:
                ans = ''
            return "FINAL: " + str(ans)

    fake = FakeCIE()
    result = agl_pipeline("Do I need an umbrella?", cie=fake)

    assert fake.called_problem is not None, "collaborative_solve was not called"
    context = fake.called_problem.get("context", "") or ""
    assert "umbrella" in context.lower(), "RAG context not injected"
    assert result["answer"].startswith("FINAL:"), "Final answer formatter not used"
