---
description: "Run the full benchmark suite and report detector accuracy metrics"
tools: [read, search, execute]
argument-hint: "Scope (e.g. full suite, specific detector, regression check)"
---
Run the benchmark suite and report comprehensive accuracy metrics.

Steps:
1. Run `python -m pytest tests/ -v` for unit test baseline
2. Run benchmark against all training contracts
3. Calculate: recall, precision, F1, false positive rate per detector
4. Compare against baseline metrics (recall 92.3%, precision 12.9%)
5. Flag any regressions in existing detectors
6. Report results in tabular format
