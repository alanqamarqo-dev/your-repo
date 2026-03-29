---
description: "Create training contracts (vulnerable, safe, edge) for a specific detector category"
tools: [read, edit, search, execute]
argument-hint: "Category name (e.g. slippage, signature_replay, proxy)"
---
Create training contracts for the specified detector category.

For each category, create:
1. 3+ vulnerable contracts in `training_contracts/<category>/vulnerable/`
2. 3+ safe contracts in `training_contracts/<category>/safe/`
3. 2+ edge-case contracts in `training_contracts/<category>/edge/`
4. A `ground_truth.jsonl` file with labels

Follow the patterns described in `docs/DETECTOR_BUILD_PLAN.md` section 5.
