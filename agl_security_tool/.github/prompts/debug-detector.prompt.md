---
description: "Debug and fix false positive or missed detection for a specific detector on a specific contract"
tools: [read, edit, search, execute]
argument-hint: "Detector ID + contract path (e.g. MISSING-EVENT safe_vault.sol)"
---
Debug why a detector fires incorrectly (false positive) or misses a real vulnerability (false negative).

Steps:
1. Parse the target contract with `SoliditySemanticParser`
2. Run only the target detector via `DetectorRunner.run_single(detector_id, contracts)`
3. Inspect parsed functions: operations, raw_body, state_writes
4. Identify why the detection/protection pattern matches/misses
5. Fix the pattern in the detector file
6. Verify fix on both vulnerable and safe contracts
7. Run full detector suite to check for regression

Key files:
- `detectors/common.py` — common detectors
- `detectors/defi.py` — DeFi detectors
- `detectors/reentrancy.py` — reentrancy detectors
- `detectors/access_control.py` — access control detectors
- `detectors/token.py` — token detectors
