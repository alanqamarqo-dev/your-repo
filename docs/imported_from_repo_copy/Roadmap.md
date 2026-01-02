AGL Project Roadmap
===================

Goal: evolve AGL from a modular assistant to a robust knowledge-enabled assistant with continuous harvesting, verification, and high-quality Arabic naturalization. This is NOT AGI, but a pragmatic path to a powerful assistant.

Milestones (short-to-mid term)
-------------------------------

1) Stabilize External Provider and RAG (1-2 weeks)
   - Ensure ExternalInfoProvider works with a real ASCII OPENAI_API_KEY.
   - Add a simple retriever (FAISS or file-based) and connect provider to RAG pipeline.
   - Measure: 50 manual QA queries with sources shown; aim >=70% useful answers.

2) Improve Answer Naturalization & Fallbacks (2 weeks)
   - Fine-tune `NLP_Advanced.naturalize_answer` rules; add templating for Arabic.
   - Implement friendly fallback messages and follow-up clarifying questions.
   - Measure: user satisfaction score via quick manual review.

3) Harvester + Verifier Loop (2-4 weeks)
   - Run `workers/knowledge_harvester.py` periodically (mock then real).
   - Build verifier pipeline for confidence thresholding and review queue.
   - Persist accepted facts into Knowledge Graph and update retriever index.
   - Measure: daily facts ingested and % accepted vs reviewed.

4) Planner & Tooling (3-6 weeks)
   - Add Planner that composes multi-step tasks and calls tools (web search, db queries, code execution).
   - Safety wrappers and rate limits for external calls.
   - Measure: success on 3 multi-step tasks end-to-end.

5) Continuous Learning & Evaluation (ongoing)
   - Track metrics, build retraining/finetuning pipeline for local models (optional).
   - Add tests, monitoring dashboards, and safety checks.

Practical Resources
-------------------

- Compute: RAG and fine-tuning require CPU/GPU resources and storage for indices.
- Data: Harvested facts, curated sources, review labels for verifier.
- People: At least one reviewer for initial harvest queue, a developer to integrate FAISS/Elastic, and an ML engineer for finetuning workflows.

Next immediate steps (today)
---------------------------

- Run smoke tests (mock provider + General_Knowledge.ask) — already implemented in code base).
- If you want, run the harvester in mock mode and inspect `artifacts/harvested_facts.jsonl`.

Contact
-------

If you want I can implement the next milestone (RAG + retriever) and add tests and a basic CI job for the smoke tests.
