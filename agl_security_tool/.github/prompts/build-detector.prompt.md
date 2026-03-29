---
description: "Build a new vulnerability detector following the DETECTOR_BUILD_PLAN specification"
tools: [read, edit, search, execute]
argument-hint: "Detector name from the plan (e.g. MISSING-SLIPPAGE)"
---
Build the specified detector from `docs/DETECTOR_BUILD_PLAN.md`.

Steps:
1. Read the detector specification from the build plan
2. Create the detector class in the appropriate module file under `detectors/`
3. Include all detection patterns and protection patterns from the spec
4. Register the detector in `detectors/__init__.py`
5. Run `python -m pytest tests/` to verify no regression
6. Report: detector ID, file, pattern counts, test results
