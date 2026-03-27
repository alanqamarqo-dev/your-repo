AGI Evaluation runner
=====================

What this does
--------------
- Presents an Arabic multi-part evaluation (language, math, creativity, knowledge, problem-solving, programming).
- Records response time and saves answers and heuristic scores to JSON.
- Supports `--auto` to run using included reference answers (useful for self-test).

Usage
-----
Interactive (paste the system's answer for each question, end with a blank line):

```powershell
python .\scripts\run_agi_evaluation.py --output artifacts/agi_eval_result.json
```

Auto (simulate using reference answers):

```powershell
python .\scripts\run_agi_evaluation.py --auto --output artifacts/agi_eval_result_auto.json
```

Outputs
-------
- JSON file with per-question answers, response times, heuristic scores, and references.

Next steps
----------
- Use the generated JSON to compare system responses to references.
- Optionally extend scoring heuristics (e.g., semantic similarity, unit tests for code answers).
