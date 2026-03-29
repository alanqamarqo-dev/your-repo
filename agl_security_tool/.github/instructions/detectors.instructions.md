---
description: "Use when writing, reviewing, or debugging code in the detectors/ directory. Covers detection patterns, protection patterns, BaseDetector inheritance, ParsedContract/ParsedFunction data model, OpType operations, and Finding creation."
---
# Detector Development Guidelines

## BaseDetector Interface
Every detector must inherit `BaseDetector` from `detectors/__init__.py` and define:
- `DETECTOR_ID`: Unique ID in `UPPER-CASE-WITH-DASHES` format
- `TITLE`: Human-readable title
- `SEVERITY`: `Severity.CRITICAL | HIGH | MEDIUM | LOW | INFO`
- `CONFIDENCE`: `Confidence.HIGH | MEDIUM | LOW`
- `detect(contract: ParsedContract, all_contracts: List[ParsedContract]) -> List[Finding]`

## Data Model Quick Reference
- `contract.name`, `contract.contract_type`, `contract.inherits`, `contract.is_upgradeable`
- `contract.functions[fname]` → `ParsedFunction` with `.operations`, `.raw_body`, `.state_reads`, `.state_writes`, `.external_calls`, `.require_checks`, `.modifiers`, `.parameters`, `.visibility`, `.mutability`
- `contract.state_vars[name]` → `StateVar` with `.var_type`, `.is_constant`, `.is_immutable`, `.is_mapping`
- `OpType`: STATE_READ, STATE_WRITE, EXTERNAL_CALL, EXTERNAL_CALL_ETH, DELEGATECALL, REQUIRE, EMIT, LOOP_START, etc.

## Detection Logic Pattern
```python
def detect(self, contract, all_contracts):
    findings = []
    if contract.contract_type in ("interface", "library"):
        return findings
    for fname, func in contract.functions.items():
        if func.mutability in ("view", "pure"):
            continue
        body = func.raw_body or ""
        # 1. Check detection patterns
        # 2. Check protection patterns (skip if protected)
        # 3. Create finding via self._make_finding()
    return findings
```

## Rules
- Use `self._make_finding()` — never construct `Finding()` directly
- Include 3-5 protection patterns to reduce false positives
- Set `confidence_override` based on pattern strength (HIGH for explicit, MEDIUM for inferred)
- Use bilingual comments (Arabic + English) in core logic
