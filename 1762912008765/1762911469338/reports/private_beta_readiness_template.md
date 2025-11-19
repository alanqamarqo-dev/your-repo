# Private Beta Readiness Report (Template)

Repository: your-repo
Commit / Tag:
Date:
Run by:

---

## 1) Executive Summary

- Goal: Verify system readiness for a closed/private beta.
- Metric targets:
  - mean latency (per endpoint) < 1.5 s
  - p95 latency (per endpoint) < 2.5 s
- Short conclusions: (fill after run)

---

## 2) Environment

- Host OS / CPU / RAM:
- Python:
- venv:
- Ollama / Qwen model: (e.g. qwen2.5:7b-instruct)
- AGL commit:
- Env vars used:
  - AGL_LLM_PROVIDER=
  - AGL_LLM_BASEURL=
  - AGL_LLM_MODEL=

---

## 3) Latency Results (network measurements)

Include `logs/latency_summary.json` snapshot.

- /process:
  - runs:
  - mean_ms:
  - p95_ms:
  - success_count / runs:

- /rag/answer:
  - runs:
  - mean_ms:
  - p95_ms:
  - success_count / runs:
  - nonempty_sources_count / runs:
  - example source snippet(s):

- /meta/evaluate:
  - runs:
  - mean_ms:
  - p95_ms:
  - success_count / runs:
  - meta_score distribution (min/mean/max):

Compliance vs targets: (PASS / FAIL per endpoint)

---

## 4) Functional checks

- Smoke tests: (attach pytest output)
  - test_smoke_config_and_registry.py:
  - test_rag_smoke.py:
  - test_safety_smoke.py:
  - test_self_improvement_smoke.py:
  - test_meta_cognition_smoke.py:

- RAG: confirm sources are non-empty and plausible. Example response:

```
{ "query": "...", "answer": "...", "sources": ["kb://doc/123", "web://..." ] }
```

- Meta-Cognition: sample evaluations with differing scores:

```
{ "evaluation": { "score": 0.62, "notes": "..." } }
{ "evaluation": { "score": 0.42, "notes": "..." } }
```

---

## 5) UI snapshots

- Attach screenshots: `web/test_ui.html` (interaction), `web/index.html` (if used), admin flags view.

---

## 6) Issues & Recommendations

- Any failures, flakiness, or high latency explanations.
- Suggested mitigations (model sizing, caching, local LLM, async/batching, pre-warming).

---

## 7) Go/No-Go recommendation

- Recommendation: (Partial beta / Hold / Full beta)
- Rationale:

*End of template*
