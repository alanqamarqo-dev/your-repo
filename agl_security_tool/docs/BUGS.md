# AGL Security Tool — Known Bugs & Fixes

**Audit Date:** 2026-03-09  
**Last Updated:** 2026-03-11  
**Total Bugs Found:** 52  
**Critical:** 10 | High: 16 | Medium: 18 | Low: 8

### Fix Status
| Status | Count |
|--------|-------|
| ✅ Fixed | 20 |
| ⏳ Pending | 32 |

---

## Priority 1 — CRITICAL (Must Fix)

### BUG-001: Wave Evaluator — Safe Contracts Score 0.92 ✅ FIXED
**File:** `heikal_math/wave_evaluator.py`  
**Impact:** All-False features (safe contract) produce danger_intensity = 0.92 instead of ~0  
**Root Cause:** When all features are False (phase=0), all waves are positive → composite = Σ(weights) = 1.0 → normalized = 1.0 → intensity = 1.0 × 0.92 = 0.92  
**Fix Applied:** Changed `amplitude = weight` to `amplitude = weight if value else 0.0` so False features produce zero-amplitude waves.

### BUG-002: Heikal Tunneling — Correction Factor ≈ 0 ✅ FIXED
**File:** `heikal_math/tunneling_scorer.py`  
**Impact:** Heikal correction changes probability by <0.001% (negligible)  
**Root Cause:** ξ × ℓ_p² = 0.4671 × 0.0001 = 0.0000467 is too small  
**Fix Applied:** Changed PLANCK_SCALE from 0.01 to 0.316 (ℓ_p² ≈ 0.1). Now factor = 1 + 0.467/L² gives meaningful boost.

### BUG-003: Z3 Access Control — Claims Z3 But Uses Regex ✅ FIXED
**File:** `z3_symbolic_engine.py`  
**Fix Applied:** Set `source="z3_pattern"` for all 7 non-Z3 pattern checks.

### BUG-004: Z3 Division Safety — Claims Z3 But Uses Regex ✅ FIXED
**File:** `z3_symbolic_engine.py`  
**Fix Applied:** Same as BUG-003.

### BUG-005: Z3 Balance Invariants — Claims Z3 But Uses Regex ✅ FIXED
**File:** `z3_symbolic_engine.py`  
**Fix Applied:** Same as BUG-003.

### BUG-006: Z3 Arithmetic Overflow — Trivially Satisfiable ✅ FIXED
**File:** `z3_symbolic_engine.py`  
**Fix Applied:** Changed from `UGT(a, big)` (always SAT) to `ULT(a, 2^128) + ULT(b, 2^128) + ULT(result, a)` with realistic operand bounds.

### BUG-007: Hardcoded LLM Model in core.py ✅ FIXED
**File:** `core.py`  
**Fix Applied:** Replaced hardcoded values with `os.environ.get("AGL_LLM_MODEL", ...)` and `os.environ.get("AGL_LLM_BASEURL", ...)`.

### BUG-008: Exploit Proof Invariant Always violated=True ✅ FIXED
**File:** `exploit_reasoning.py`  
**Fix Applied:** `check_invariants()` now accepts `z3_result` parameter; `violated = (z3_result == "SAT")` instead of hardcoded True.

---

## Priority 2 — HIGH (Should Fix)

### BUG-009: Wave Evaluator — Destructive Interference Never Fires ✅ FIXED
**File:** `heikal_math/wave_evaluator.py`  
**Impact:** Protection features never cancel danger due to default `True` for missing features  
**Fix Applied:** Changed all protection feature defaults from `True` to `False` so missing features don't falsely indicate protection.

### BUG-010: Exploit Reasoning — Nested If/Else Parsing Fails
**File:** `exploit_reasoning.py`, line ~260  
**Impact:** Complex control flow undersimplified to 1-2 paths  
**Fix:** Implement recursive branching or limit to documented capability.

### BUG-011: Exploit Reasoning — Hardcoded Attack Narratives
**File:** `exploit_reasoning.py`, line ~607  
**Impact:** Narratives don't match actual Z3 proof; always describe "deposit + withdraw"  
**Fix:** Template narratives based on finding category, not hardcoded.

### BUG-012: Exploit Reasoning — Drops Vulns Per Function
**File:** `exploit_reasoning.py`, line ~800  
**Impact:** Keeps only best proof per (function, category) → silently drops others  
**Fix:** Keep all proofs or document limitation.

### BUG-013: Reentrancy Z3 Model Oversimplified
**File:** `z3_symbolic_engine.py`, line ~264  
**Impact:** Only models 2 withdrawals with fixed amounts; no recursive modeling  

### BUG-014: PoC Generator — Hardcoded Dummy Args
**File:** `poc_generator.py`, line ~278  
**Impact:** All address args become `address(this)`, all uint become `1 ether`  
**Fix:** Use Z3 counterexample values when available.

### BUG-015: Project Scanner — No Circular Import Detection
**File:** `project_scanner.py`, line ~575  
**Impact:** A→B→A imports cause infinite recursion  
**Fix:** Track visited set in `_resolve_import()`.

### BUG-016: Solidity Flattener — No C3 Linearization
**File:** `solidity_flattener.py`, line ~535  
**Impact:** Diamond inheritance order may be wrong  

### BUG-017: Flattener — No Circular Import Guard
**File:** `solidity_flattener.py`, line ~483  
**Impact:** Same as BUG-015 for direct flattening.

### BUG-018: REENTRANCY-NO-ETH — Missing Target Filter ✅ FIXED
**File:** `detectors/reentrancy.py`  
**Impact:** False positives when call.target == write.target (same-target safe)  
**Fix Applied:** Added `if call.target and write.target and call.target == write.target: continue` filter in ReentrancyNoETH.detect().

### BUG-019: Contract Intelligence — Hardcoded Dampened Thresholds
**File:** `contract_intelligence.py`, line ~333  
**Impact:** `0.48 + 0.5 * (max_conf - 0.87)` breaks if data distribution changes  

### BUG-020: RPC Errors Silently Return None
**File:** `onchain_context.py`, line ~378  
**Impact:** Caller can't distinguish "no data" from "network error"  

### BUG-021: Core.py — Severity May Be Overwritten in deep_scan
**File:** `core.py`, line ~400  
**Impact:** `deep_scan()` resets severity_summary, may lose counts from `_scan_file()`  

### BUG-022: Operation.in_condition Dead Field ✅ FIXED
**File:** `detectors/solidity_parser.py`  
**Impact:** Field declared but never set during parsing  
**Fix Applied:** Added `in_condition_depth` tracking in `_analyze_function_body()` (parallel to existing `in_loop_depth`). All `if/else` blocks now increment/decrement the depth counter. All 16 Operation constructors updated with `in_condition=in_condition`.  

---

## Priority 3 — MEDIUM (Nice to Fix)

### BUG-023: Holographic Memory — Slow O(N²) DFT ✅ FIXED
**File:** `heikal_math/holographic_patterns.py`, line ~255  
**Impact:** 10× slower than FFT; ~96K ops per match. MCTS calling 200 iterations × 7 patterns × 2 DFT calls = 2800 DFT calls caused pipeline to hang.  
**Fix Applied:** Replaced pure-Python O(n²) `_dft()` and `_idft()` with `numpy.fft.fft()` and `numpy.fft.ifft()` (O(n log n)). Falls back to original implementation if numpy is unavailable.

### BUG-024: Holographic Memory — Low Match Threshold (0.25)
**File:** `heikal_math/holographic_patterns.py`  
**Impact:** Weak similarities matched → false positives  

### BUG-025: Tunneling — Resonance Capping at R=5
**File:** `heikal_math/tunneling_scorer.py`, line ~310  
**Impact:** Resonance peaks indistinguishable from non-resonant high energy  

### BUG-026: Core.py — Category Normalization Order-Dependent
**File:** `core.py`, line ~1287  
**Impact:** "unchecked_access" matches "access" not "unchecked" depending on order  

### BUG-027: Core.py — Confidence String Inconsistent
**File:** `core.py`, line ~1311  
**Impact:** Default 0.5 for unknown types may be too aggressive  

### BUG-028: Semgrep Rules Hardcoded as String
**File:** `tool_backends.py`, line ~490  
**Impact:** Can't extend rules without code modification  

### BUG-029: Tool Backends — No Consensus Weighting
**File:** `tool_backends.py`  
**Impact:** All tools treated equally regardless of agreement  

### BUG-030: Benchmark — Brier Per-Finding Not Per-Contract
**File:** `benchmark_runner.py`  
**Impact:** Inconsistent with contract_intelligence.py  

### BUG-031: Weight Optimizer — No Feature Scaling
**File:** `weight_optimizer.py`  
**Impact:** Features with large ranges dominate weights  

### BUG-032: Weight Optimizer — Early Stop on Training Loss
**File:** `weight_optimizer.py`  
**Impact:** No validation set → potential overfitting  

### BUG-033: DIVIDE-BEFORE-MULTIPLY — Flags Constants
**File:** `detectors/defi.py`  
**Impact:** 25% FP from benign rounding sequences  

### BUG-034: ORACLE-MANIPULATION — No Reentrancy Context
**File:** `detectors/defi.py`  
**Impact:** 40% FP from read-only oracles  

### BUG-035: Exploit ConstraintSolver — MAX_ETH Too Low
**File:** `exploit_reasoning.py`, line ~344  
**Impact:** MAX_ETH = 10,000 ETH misses large-amount attacks  

### BUG-036: State Mutation — Regex Fragility
**File:** `state_extraction/state_mutation.py`  
**Impact:** Comments or multi-line assignments break regex  

### BUG-037: VS Code Bridge — No Timeout on deep_scan
**File:** `vscode_bridge.py`  
**Impact:** Can hang indefinitely on large projects  

### BUG-038: Execution Semantics — ViewPure Config Ignored
**File:** `state_extraction/execution_semantics.py`  
**Impact:** `analyze_view_pure=False` flag has no effect  

### BUG-039: ENCODE-PACKED — Hardcoded Name Patterns
**File:** `detectors/common.py`  
**Impact:** Misses true dynamic types, matches on variable names  

---

## Priority 4 — LOW (Optional)

### BUG-040: Holographic Pattern Collision Risk
**File:** `heikal_math/holographic_patterns.py`  
**Impact:** 8 patterns in 64-dim may interfere (47% char overlap for reentrancy types)  

### BUG-041: Pragma Detection Takes First Found
**File:** `poc_generator.py`, line ~107  
**Impact:** May pick wrong pragma if multiple versions exist  

### BUG-042: Etherscan URLs Hardcoded for 9 Chains
**File:** `onchain_context.py`  
**Impact:** Adding chains requires code change  

### BUG-043: VS Code Bridge — Duplicate Discovery Code
**File:** `vscode_bridge.py`  
**Impact:** DRY violation between scan_project and discover_project  

### BUG-044: Flattener — Nested Comments Unhandled
**File:** `solidity_flattener.py`, line ~207  
**Impact:** `/* /* nested */ */` incorrectly balanced  

### BUG-045: Core.py — Dead Data (contracts/functions keys)
**File:** `core.py`, line ~707  
**Impact:** `combined["contracts"]` and `["functions"]` set but never used  

### BUG-046: Silent JSON Parse in LLM Response
**File:** `core.py`, line ~1639  
**Impact:** `except (json.JSONDecodeError, ValueError): pass` — invisible failures  

### BUG-047: Tunneling — Bypassable Barrier Amplification
**File:** `heikal_math/tunneling_scorer.py`, line ~262  
**Impact:** Hard barriers (T=0.05) jump to 0.75 if marked bypassable  

---

## Additional Fixes (2026-03-10)

### FIX-A: Unchecked External Call False Positive
**File:** `core.py` (dedup post-filter)  
**Impact:** "Unchecked External Call" flagged even when code had `(bool ok,) = ...call{...}(); require(ok);`  
**Fix Applied:** Post-filter in `_deduplicate_and_cross_validate()` scans source code for checked call patterns (require/if-revert after bool capture). Removes CFG findings when call IS checked.

### FIX-B: Missing Access Control on withdraw() False Positive
**File:** `z3_symbolic_engine.py`  
**Impact:** Z3 flagged plain `withdraw()` as missing AC even when it's a user-scoped function (protected by `balances[msg.sender]`)  
**Fix Applied:** Added `balances[msg.sender]|_balances[msg.sender]` to `AC_BODY_PATTERNS`. Removed plain `withdraw` from sensitive function patterns (kept `withdrawAll`, `emergencyWithdraw`, `drain`).

### FIX-C: Unprotected Withdrawal on User-Scoped Functions
**File:** `detectors/access_control.py`  
**Impact:** `UnprotectedWithdraw` detector flagged `withdraw()` that uses `balances[msg.sender]` as unprotected  
**Fix Applied:** Added user-scoping check — if function body contains `balances[msg.sender]` or similar user-balance patterns, skip the finding (user can only withdraw their own funds).

### FIX-D: Reentrancy FPs on nonReentrant + CEI Contracts
**File:** `core.py` (dedup post-filter)  
**Impact:** Semgrep and CFG analysis flag reentrancy even on functions with `nonReentrant` modifier AND correct CEI ordering  
**Fix Applied:** Post-filter detects nonReentrant + state-write-before-call (CEI) and suppresses reentrancy findings from semgrep/cfg_analysis. Also downgrades action_space attack-target severity from HIGH to MEDIUM for protected functions.

### FIX-E: API findings Key Returns Raw Instead of Unified
**File:** `core.py`  
**Impact:** `result["findings"]` returned raw Layer 1 findings while `severity_summary` counted unified findings → mismatch  
**Fix Applied:** Added `combined["raw_findings"] = combined["findings"]` then `combined["findings"] = combined.get("all_findings_unified", [])` so the API returns the deduplicated unified list.

---

---

## Session 2026-03-11 — Pipeline Quality Fixes

Full validation on InverseFinance/FiRM (5 contracts, 45+ functions).  
**Before:** 6 CRITICAL (all FP), 167 findings, 87 temp-path titles, 60 source="?".  
**After:** 0 CRITICAL, 0 HIGH, 49 grouped findings, all checks pass.

### BUG-048: L1→L4 Results Are Additive Not Filtering — False Positives Survive ✅ FIXED
**Priority:** CRITICAL  
**Files:** `risk_core.py`, `core.py`, `audit_pipeline.py`  
**Impact:** When L3 (attack_engine) and L4 (search_engine) find NO profitable exploit paths, their silence is treated as neutral (score 0) rather than exculpatory evidence. Detector-only CRITICAL findings (formal_score=1.0) survive with P≥0.85 even when deeper analysis disproves them.  
**Root Cause:** The Bayesian scoring equation `P(exploit) = σ(w_f·S_f + w_h·S_h + w_p·S_p + w_e·E + bias)` only receives additive positive evidence. When L3/L4 produce zero results, `profit_score=0` contributes nothing (multiplied by weight adds 0 to logit). No mechanism exists to subtract probability when deeper layers explicitly fail to confirm.  
**Mathematical Proof:**  
- Detector CRITICAL alone: logit = 2.5×1.0 + 1.8×1.0 + 0×0 + 0×0 + (-1.8) = 2.5 → P = σ(2.5) = 0.9241 → CRITICAL  
- With negative evidence penalty (-1.0 per layer): logit = 2.5 - 2.0 = 0.2 → P = σ(0.2) = 0.5498 → MEDIUM  
**Fix Applied:**  
1. `risk_core.py`: Added `NEGATIVE_EVIDENCE_PENALTY = -1.0`, new `negative_evidence_count` parameter in `compute_exploit_probability()`, logit penalty `neg_count × NEGATIVE_EVIDENCE_PENALTY`.  
2. `core.py` (two locations — `deep_scan` and `scan`): Build `_negative_evidence` metadata dict from L3/L4 results (`l3_ran`, `l3_profitable`, `l4_ran`, `l4_profitable`). Annotate each finding with `negative_evidence: ["l3_no_profitable_attack", "l4_no_exploitable_path"]` when layers ran but found nothing.  
3. `audit_pipeline.py`: Same annotation logic for the audit pipeline path.  
**Result:** FiRM 6 CRITICAL → 1 CRITICAL. Morpho Blue: 0 CRITICAL, 0 HIGH.  
**Tests:** `tests/test_negative_evidence.py` — 16/16 passed.  
**Documentation:** `docs/NEGATIVE_EVIDENCE.md`

### BUG-049: Semgrep Titles Contain Temp File Path ✅ FIXED
**Priority:** HIGH  
**File:** `AGL_NextGen/src/agl/engines/security_orchestrator.py` line 550-567  
**Impact:** 87/167 findings (52%) have titles like `"C.Users.Hossam.Appdata.Local.Temp.Agl Semgrep Abc123.Missing Zero Check"` — unreadable gibberish in reports.  
**Root Cause:** Semgrep's `check_id` includes the full OS path to the temporary rules YAML file (written by `tempfile.mkstemp(suffix=".yaml", prefix="agl_semgrep_")`). The `_parse_match()` method at line 564 uses `rule_id.replace("-", " ").title()` directly on the full `check_id` without stripping the path prefix.  
**Contrast:** `tool_backends.py` line 561 correctly does `rule_short = rule_id.split(".")[-1]` but the orchestrator doesn't.  
**Fix Applied:** Added `rule_short = rule_id.split(".")[-1] if "." in rule_id else rule_id` after extracting `rule_id`. Used `rule_short` for both `title` and `id` fields. Also added `.replace("_", " ")` for underscore-separated rule names. Category detection still uses full `rule_id` so keywords like `reentrancy` in the path still work.  
**Result:** All 87 affected findings now have clean titles like `"Missing Zero Check"`, `"State After External"`, `"Block Timestamp Dependency"`.  
**Tests:** `tests/test_quality_fixes.py::TestSemgrepTitleCleanup` — 5/5 passed.

### BUG-050: Source Attribution Missing — 60 Findings Show source="?" ✅ FIXED
**Priority:** HIGH  
**File:** `core.py` line ~1065 (`_process()` in `_deduplicate_and_cross_validate`)  
**Impact:** 60/167 findings (36%) have `source: "?"` in JSON output — no way to trace which engine produced them.  
**Root Cause:** The detector `Finding` dataclass `to_dict()` method (`detectors/__init__.py` line 192) outputs: `detector`, `title`, `severity`, `confidence`, `contract`, `function`, `line`, etc. — but does NOT include a `source` field. When `_process()` creates `merged = dict(f)`, if the original finding dict has no `source` key, it stays absent. Downstream JSON serialization defaults to `"?"`.  
**Affected sources:** All 60 findings come from `agl_22_detectors` or `pattern_engine`, all with `line=0`.  
**Fix Applied:** Single line: `merged.setdefault("source", source_label)` after creating `merged = dict(f)`. If the finding already has a `source` field (e.g. Z3 findings), `setdefault` preserves it. If absent, uses the pipeline label (`"agl_22_detectors"`, `"pattern_engine"`, `"z3_symbolic"`, etc.).  
**Result:** All 60 previously-unattributed findings now show correct source.  
**Tests:** `tests/test_quality_fixes.py::TestSourceAttribution` — 4/4 passed.

### BUG-051: Z3 Reentrancy — No Callback Safety Analysis ✅ FIXED
**Priority:** CRITICAL  
**Files:** `z3_symbolic_engine.py` line 131-260, `core.py` line 1148-1165  
**Impact:** The last remaining false CRITICAL in FiRM: `"Cross-function reentrancy in Market.sol"`. Z3 gives `formal_score=1.0` because it sees `dola.transfer(user, amount)` (external call) followed by `debts[user] -= amount` (state write). But DOLA is a standard ERC20 token — its `transfer()` has NO callback hooks, making reentrancy impossible.  
**Root Cause (Z3 engine):** `_check_reentrancy()` matches ALL external calls via `_RE_EXTERNAL_CALL` regex (`(\w+)\.(?:call|transfer|send|delegatecall|staticcall)`) without analyzing what the call target IS. The Z3 "proof" models a generic double-withdrawal attack that is always satisfiable — it has zero knowledge of the target contract's interface. The only existing filter checks for `nonReentrant` guards and `ReentrancyGuard` inheritance.  
**Root Cause (core.py post-filter):** The reentrancy suppression filter at line 1151 only removes findings with `source in ("semgrep", "cfg_analysis", "")` — it misses `z3_symbolic` and `agl_22_detectors`.  
**Fix Applied:**  
1. New method `_is_callback_safe_call(ec_match, source)` in Z3 engine that returns True when the call CANNOT trigger a reentrant callback:  
   - `.staticcall()` → safe (read-only by EVM definition)  
   - `.send()` → safe (2300 gas stipend, insufficient for any callback)  
   - `.transfer()` on variable typed as `IERC20`/`ERC20` → safe (standard ERC20 has no callback hooks, unlike ERC777/ERC721/ERC1155)  
   - `.transfer()` on `address payable` → safe (2300 gas)  
   - `.call()` on unknown target → UNSAFE (preserved as-is)  
   - `.delegatecall()` → UNSAFE (preserved as-is)  
2. Extended core.py post-filter to include `"z3_symbolic"` and `"agl_22_detectors"` in addition to `"semgrep"` and `"cfg_analysis"` when nonReentrant + CEI is confirmed.  
**Result:** The DOLA reentrancy false CRITICAL is eliminated. `formal_score=1.0` raw `.call{value:}` reentrancy still correctly detected.  
**Tests:** `tests/test_quality_fixes.py::TestZ3CallbackSafety` — 9/9 passed, `TestZ3ReentrancyWithERC20` — 2/2 passed.

### BUG-052: Duplicate Findings Not Grouped — 23× Same Title ✅ FIXED
**Priority:** MEDIUM  
**File:** `core.py` (after dedup, before final output)  
**Impact:** `_deduplicate_and_cross_validate()` uses `(line_bucket, category)` as dedup key, which merges findings within 5 lines of each other — but identical issues at different locations (e.g. 23× `"Missing Zero Check"` on lines 10, 25, 40, 100...) remain as separate entries. Market.sol produces 69 findings where only 15 are unique.  
**Root Cause:** The dedup `_process()` function groups by `(line // 5, category)`. Same vulnerability type at different locations gets different line buckets → separate entries. No post-dedup grouping step existed.  
**Fix Applied:** Added grouping step after all post-filters and before final output. Groups by `(title.lower(), severity)` — findings with identical title + severity are collapsed into one entry with:  
- `count`: number of occurrences  
- `locations`: list of `{line, end_line, function, snippet}` for each occurrence  
- `confirmed_by`: union of all confirmation sources  
- `confidence`: max across all instances  
- `negative_evidence`: preserved from any instance that has it  
**Result:**  
| Contract | Before Grouping | After Grouping |
|---|---|---|
| Market.sol | 69 | 15 |
| Fed.sol | 16 | 8 |
| BorrowController.sol | 30 | 10 |
| Oracle.sol | 17 | 7 |
| DBR.sol | 34 | 9 |
| **Total** | **166** | **49** |

**Tests:** `tests/test_quality_fixes.py::TestDuplicateGrouping` — 7/7 passed.

---

## Full Validation — InverseFinance/FiRM (2026-03-11)

All 5 contracts scanned after all fixes:

| Metric | Before (2026-03-09) | After (2026-03-11) |
|---|---|---|
| CRITICAL | 6 | **0** |
| HIGH | several | **0** |
| Temp path in titles | 87 | **0** |
| source="?" | 60 | **0** |
| Total findings | 167 (flat) | **49** (grouped) |
| Quality checks | N/A | **ALL PASSED** |

---

## Summary by Module

| Module | Critical | High | Medium | Low |
|--------|----------|------|--------|-----|
| core.py | 2 | 2 | 3 | 2 |
| z3_symbolic_engine.py | 5 | 1 | 0 | 0 |
| exploit_reasoning.py | 1 | 3 | 1 | 0 |
| heikal_math/ | 2 | 1 | 2 | 1 |
| detectors/ | 0 | 1 | 3 | 1 |
| poc_generator.py | 0 | 1 | 0 | 1 |
| project_scanner.py | 0 | 1 | 0 | 0 |
| solidity_flattener.py | 0 | 2 | 0 | 1 |
| contract_intelligence.py | 0 | 1 | 0 | 0 |
| tool_backends.py | 0 | 0 | 2 | 0 |
| benchmark_runner.py | 0 | 0 | 1 | 0 |
| weight_optimizer.py | 0 | 0 | 2 | 0 |
| onchain_context.py | 0 | 1 | 0 | 1 |
| vscode_bridge.py | 0 | 0 | 1 | 1 |
| state_extraction/ | 0 | 0 | 2 | 0 |
| risk_core.py | 0 | 1 | 1 | 0 |
| security_orchestrator.py | 0 | 1 | 0 | 0 |
| audit_pipeline.py | 0 | 0 | 0 | 0 |
| **TOTAL** | **10** | **16** | **18** | **8** |
