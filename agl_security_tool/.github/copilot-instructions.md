# AGL Security Tool — Project Instructions

## Overview
AGL Security Tool is a Solidity smart contract security analyzer with 8 analysis layers, 24+ semantic detectors, Z3 symbolic engine, exploit reasoning, and risk scoring.

## Architecture
See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for full pipeline details.

Key modules:
- `detectors/` — Semantic vulnerability detectors inheriting `BaseDetector`
- `core.py` — `SmartContractAnalyzer` + `SecurityOrchestrator`
- `audit_pipeline.py` — Full 8-layer pipeline
- `risk_core.py` — `RiskCore` probability scoring with trained weights
- `weight_optimizer.py` — `WeightOptimizer` for weight training via SGD
- `exploit_reasoning.py` — Z3 + path analysis exploit proofs
- `benchmark_runner.py` — `BenchmarkRunner` with `SWC_GROUND_TRUTH`
- `z3_symbolic_engine.py` — Z3 SMT solver symbolic checks

## Code Style
- Python 3.10+, type hints on public APIs
- Bilingual comments (Arabic + English) in core modules
- Detector IDs: `UPPER-CASE-WITH-DASHES`
- Every detector inherits `BaseDetector` from `detectors/__init__.py`

## Detector Pattern
Every detector must follow this structure:
```python
class MyDetector(BaseDetector):
    DETECTOR_ID = "MY-DETECTOR"
    TITLE = "Human-readable title"
    SEVERITY = Severity.HIGH
    CONFIDENCE = Confidence.MEDIUM

    def detect(self, contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []
        # Detection logic using contract.functions, contract.state_vars, etc.
        # Use self._make_finding() to create results
        return findings
```

Register in `detectors/__init__.py` → `_register_all_detectors()`.

## Build & Test
```bash
pip install -e .
python -m pytest tests/
python -m agl_security_tool --file contract.sol
```

## Conventions
- Detection patterns: semantic analysis via `ParsedContract.functions[].operations`, not surface regex
- Protection patterns: each detector checks 3-5 safe patterns before reporting
- Confidence: HIGH if pattern is explicit (e.g. literal `0`), MEDIUM if inferred
- Skip `interface` and `library` contract types in detectors
- Skip `view`/`pure` functions for state-changing vulnerability detectors
- Use `_make_finding()` helper — never construct `Finding()` directly
- Weight training data: `training_contracts/<category>/{vulnerable,safe,edge}/`
