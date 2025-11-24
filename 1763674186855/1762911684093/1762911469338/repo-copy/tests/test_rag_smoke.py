import pytest
from fastapi.testclient import TestClient

from server import app


client = TestClient(app)


def test_rag_answer_endpoint_basic():
    """Smoke test for the /rag/answer endpoint.

    The test accepts either the real RAG implementation or the server's
    fallback. We assert the HTTP 200 and that the JSON payload contains
    the expected keys: ok, answer and sources.
    """
    res = client.post('/rag/answer', json={"query": "What is the capital of France?"})
    assert res.status_code == 200
    j = res.json()
    assert isinstance(j, dict)
    assert j.get('ok') is True
    assert 'answer' in j
    assert 'sources' in j
