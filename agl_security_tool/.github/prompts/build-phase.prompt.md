---
description: "Execute one complete phase from the detector build plan (phase 1, 2, or 3)"
tools: [read, edit, search, execute]
argument-hint: "Phase number (1=critical detectors, 2=medium detectors, 3=warnings)"
---
Execute the specified phase from `docs/DETECTOR_BUILD_PLAN.md` section 7.

**Phase 1 (Critical — 5 detectors):**
MISSING-SLIPPAGE, SIGNATURE-REPLAY, UNINITIALIZED-PROXY, MISSING-DEADLINE, ARRAY-LENGTH-MISMATCH

**Phase 2 (Medium — 5 detectors):**
UNSAFE-DOWNCAST, RETURN-BOMB, DOUBLE-VOTING, ROUNDING-DIRECTION, FROZEN-FUNDS

**Phase 3 (Warnings — 4 detectors):**
CENTRALIZATION-RISK, MISSING-ZERO-ADDRESS, FORCE-FEED-ETH, PERMIT-FRONT-RUN

For each detector in the phase:
1. Build the detector class
2. Register in `detectors/__init__.py`
3. Create 3 training contracts (vulnerable, safe, edge)
4. Write unit test
5. Run regression check
6. Report progress
