## SelfModel, ReflectiveCortex and PerceptionLoop — developer notes

This document explains the new self-model and reflection plumbing added to the codebase,
how it's wired, the opt-in flags, and how to run relevant tests (including the bridge/embeddings
tests that exercise FAISS when available).

Where the code lives

- Core_Consciousness/Self_Model.py — the SelfModel class, EmotionModel, and helper APIs:
  - generate_personal_goal(seed=None)
  - intrinsic_reward(event)
  - learn_from_experience(history)
  - consolidate_memory(br=None, to="ltm")
- Core_Consciousness/Perception_Loop.py — the perception loop now calls SelfModel hooks
  (emotion update, intrinsic reward, and rate-limited goal generation). These hooks are
  best-effort and opt-in via environment variables.
- Core/C_Layer/state_logger.py — snapshot writer; milestone/success/failure snapshots
  emit short biography events and (optionally) trigger memory consolidation.
- Core_Memory/Conscious_Bridge.py — LTM/STM bridge and semantic index code (embeddings → FAISS
  preferred, sklearn/TF-IDF fallbacks).

Opt-in environment flags

- AGL_ENABLE_INTRINSIC_GOAL=1  — enable PerceptionLoop intrinsic goal generation hooks.
- AGL_INTRINSIC_GOAL_INTERVAL=3600  — minimum seconds between automatic personal goals.
- AGL_ENABLE_AUTO_CONSOLIDATE=1 — enable StateLogger to call `consolidate_memory` on
  milestone snapshots.

Design & safety notes

- All new hooks are wrapped in try/except and are best-effort: if they raise, the main
  PerceptionLoop or state logger will continue unaffected.
- The SelfModel keeps a small recent-context buffer to compute novelty and curiosity-based
  intrinsic rewards. The exact algorithm is intentionally lightweight; tests assume
  deterministic behavior where possible.

Running tests locally (Windows PowerShell)

1) Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2) Install base requirements and pytest:

```powershell
python -m pip install -r requirements.txt; python -m pip install pytest
```

3) Run the existing integration tests for the self profile:

```powershell
pytest -q tests/test_self_profile_integration.py
```

Embedding / FAISS tests

- The repository includes a separate `requirements-embeddings.txt` which lists
  sentence-transformers, faiss-cpu, scikit-learn and numpy. Installing those packages
  enables the bridge's embedding → FAISS pipeline. On CI it's optional and the bridge
  tests will skip embeddings if the libraries are not available.

To run the bridge/embeddings test locally (after installing the embedding requirements):

```powershell
python -m pip install -r requirements-embeddings.txt
pytest -q tests/test_bridge_memory.py
```

CI notes

- A GitHub Actions workflow `/.github/workflows/ci-bridge-memory.yml` runs the
  `tests/test_bridge_memory.py` job on pushes and PRs to main/master. The workflow
  installs `requirements-embeddings.txt` so the FAISS path will be exercised when
  the packages can be installed on the runner.

Next steps & follow-ups

- Reconcile the unit-test expectation for `intrinsic_reward` (some earlier test runs
  showed a mismatch in how novelty/curiosity nudges were expected). If tests are
  flaky, add deterministic seeds or relax numeric assertions.
- If you want FAISS to run in CI reliably, ensure the runner architecture has a
  wheel available (faiss-cpu has wheels for many linux+python combos) or build from
  source (slower). Alternatively, run the embedding tests in a separate matrix job
  that uses a runner where the packages are known to install successfully.

If anything here is unclear or you want a deeper walk-through (sequence diagrams,
example payloads, or more thorough tests), tell me which part to expand and I'll
add it.
