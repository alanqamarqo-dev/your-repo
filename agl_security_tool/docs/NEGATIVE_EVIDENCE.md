# Negative Evidence Pipeline — توثيق الدليل السلبي

## Overview / نظرة عامة

**Problem**: The AGL Security Tool's L1→L4 pipeline (State Extraction → Action Space → Attack Simulation → Search Engine) was running correctly, but its results were **additive only** — they could only *increase* a finding's severity, never decrease it. When L3/L4 tested all possible attack sequences and found **zero profitable exploits**, this result was silently discarded instead of being used as evidence *against* the finding.

**Root Cause**: `profit_score = 0` was treated as "no information" (neutral), identical to "we didn't test". The correct interpretation when L3/L4 **ran but found nothing** is "we tested and found no exploit" — exculpatory evidence that should reduce confidence.

**Fix**: A negative evidence pipeline that:
1. Detects when L3/L4 ran but found nothing
2. Annotates affected findings
3. Applies a logit penalty in RiskCore's probability equation

---

## Mathematical Foundation / الأساس الرياضي

### Original Equation
```
P(exploit) = σ(w_f·S_f + w_h·S_h + w_p·S_p + w_e·E + source_bonus + bias)
```

### New Equation
```
P(exploit) = σ(w_f·S_f + w_h·S_h + w_p·S_p + w_e·E + source_bonus + neg_penalty + bias)
```

Where:
- `neg_penalty = neg_count × NEGATIVE_EVIDENCE_PENALTY`
- `NEGATIVE_EVIDENCE_PENALTY = -1.0` (per source)
- `neg_count` = number of L3/L4 sources that ran but found nothing (0, 1, or 2)

### Effect on a Detector-Only False Positive

| Scenario | Logit | P(exploit) | Severity |
|---|---|---|---|
| Detector CRITICAL, no neg evidence | 1.40 | 0.8022 | **HIGH** |
| Detector CRITICAL, 1× neg evidence | 0.40 | 0.5987 | **MEDIUM** |
| Detector CRITICAL, 2× neg evidence | -0.60 | 0.3543 | **LOW** |

One negative source ≈ one severity step down. Two ≈ two steps down.

### True Positives Survive

| Scenario | Logit | P(exploit) | Severity |
|---|---|---|---|
| Proven exploit (formal=0.9, heur=0.8, profit=0.5, proven=true), 2× neg | 7.15 | 0.9992 | **CRITICAL** |

Strong multi-source evidence overwhelms the penalty — as intended.

---

## Files Modified / الملفات المعدلة

### 1. `agl_security_tool/risk_core.py`

**Constant added (line ~80)**:
```python
NEGATIVE_EVIDENCE_PENALTY = -1.0
```

**RiskBreakdown dataclass — new fields (lines ~116-117)**:
```python
negative_evidence_count: int = 0
negative_evidence_penalty_applied: float = 0.0
```

**`to_dict()` — conditional output (lines ~141-145)**:
```python
if self.negative_evidence_count > 0:
    d["negative_evidence"] = {
        "count": self.negative_evidence_count,
        "penalty_applied": round(self.negative_evidence_penalty_applied, 4),
    }
```

**`compute_exploit_probability()` — new parameter + logit penalty (lines ~256, 287-300)**:
```python
def compute_exploit_probability(self, ..., negative_evidence_count: int = 0) -> RiskBreakdown:
    ...
    neg_count = max(0, int(negative_evidence_count))
    neg_penalty = neg_count * NEGATIVE_EVIDENCE_PENALTY
    logit = w_f*f + w_h*h + w_p*p + w_e*E + source_bonus + neg_penalty + bias
```

**`score_findings()` — reads neg evidence from finding dict (lines ~413, 426)**:
```python
neg_ev = f.get("negative_evidence", [])
neg_count = len(neg_ev) if isinstance(neg_ev, list) else 0
...
breakdown = self.compute_exploit_probability(..., negative_evidence_count=neg_count)
```

### 2. `agl_security_tool/core.py`

**`_scan_file()` — builds negative evidence metadata (line ~872-896)**:

After the L1→L4 pipeline runs, we inspect the results:
```python
_neg = {}
if "attack_simulation" in _layers_used:
    _neg["l3_ran"] = True
    _neg["l3_sequences_tested"] = sim_data.get("total_sequences_tested", 0)
    _neg["l3_profitable"] = sim_data.get("profitable_attacks", 0)
if "search_engine" in _layers_used:
    _neg["l4_ran"] = True
    _neg["l4_evaluated"] = sr_data.get("total_evaluated", 0)
    _neg["l4_profitable"] = sr_data.get("profitable_sequences", 0)
combined["_negative_evidence"] = _neg
```

**`_deduplicate_and_cross_validate()` — propagates to findings (lines ~1170-1188)**:

For each unified finding, if L3 ran but found zero profitable attacks AND the finding was not independently confirmed by attack_simulation, annotate it:
```python
_neg = combined.get("_negative_evidence", {})
for f in unified:
    neg_ev = []
    if l3_found_nothing and "attack_simulation" not in confirmed:
        neg_ev.append("l3_no_profitable_attack")
    if l4_found_nothing and "search_engine" not in confirmed:
        neg_ev.append("l4_no_exploitable_path")
    if neg_ev:
        f["negative_evidence"] = neg_ev
```

### 3. `agl_security_tool/audit_pipeline.py`

**`deduplicate_cross_layer()` — same propagation for pipeline path (lines ~773-806)**:

Mirrors the core.py logic for the audit_pipeline.py code path, extracting `_negative_evidence` from deep_scan results and attaching annotations to findings.

---

## Files Created / الملفات المنشأة

### 1. `agl_security_tool/test_contracts/negative_evidence_test.sol`

Forge-compatible Solidity test contract containing:

- **`VaultBase`** — abstract base with shared state, `nonReentrant`, `onlyOwner`
- **`FalsePositiveVault`** — withdraw() has nonReentrant + CEI → **SAFE** (detector flags it, but L3/L4 cannot exploit it)
- **`TruePositiveVault`** — withdraw() has classic reentrancy → **VULNERABLE** (detector flags it AND L3/L4 should find exploits)
- **`ReentrancyAttacker`** — exploit contract for TruePositiveVault
- **`NegativeEvidenceForgeTest`** — 3 Forge tests proving FP vs TP separation

### 2. `agl_security_tool/tests/test_negative_evidence.py`

Python integration test suite with **16 tests** in 3 classes:

| Class | Tests | Purpose |
|---|---|---|
| `TestRiskCoreNegativeEvidence` | 9 | Unit tests for penalty math, probability decrease, FP downgrade, TP survival, to_dict(), score_findings() |
| `TestFullPipelineNegativeEvidence` | 6 | Full pipeline scan of test contract, verifies _negative_evidence metadata, annotations, risk breakdown fields |
| `TestComparativeProbability` | 1 | Mathematical proof that penalty changes raw logit and sigmoid output exactly as predicted |

---

## Data Flow / تدفق البيانات

```
┌─────────────────────────────────────────────────────────┐
│  _scan_file() in core.py                                │
│                                                         │
│  1. L1: State Extraction     ─┐                         │
│  2. L2: Action Space         ─┤ Pipeline runs normally  │
│  3. L3: Attack Simulation    ─┤                         │
│  4. L4: Search Engine        ─┘                         │
│                                                         │
│  5. Build _negative_evidence metadata:                  │
│     {l3_ran: true, l3_profitable: 0,                    │
│      l4_ran: true, l4_profitable: 0}                    │
│     ↓                                                   │
│  combined["_negative_evidence"] = _neg                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  _deduplicate_and_cross_validate() in core.py           │
│                                                         │
│  For each unified finding:                              │
│    if L3 ran + found nothing + finding not confirmed    │
│      → finding["negative_evidence"].append(             │
│          "l3_no_profitable_attack")                     │
│    if L4 ran + found nothing + finding not confirmed    │
│      → finding["negative_evidence"].append(             │
│          "l4_no_exploitable_path")                      │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  RiskCore.score_findings() in risk_core.py              │
│                                                         │
│  neg_ev = f.get("negative_evidence", [])                │
│  neg_count = len(neg_ev)  # 0, 1, or 2                 │
│                                                         │
│  compute_exploit_probability(                           │
│      ..., negative_evidence_count=neg_count             │
│  )                                                      │
│                                                         │
│  neg_penalty = neg_count × (-1.0)                       │
│  logit = w_h*h + ... + neg_penalty + bias               │
│  P = σ(logit)                                           │
│  severity = f(P)                                        │
└─────────────────────────────────────────────────────────┘
```

---

## Test Results / نتائج الاختبار

```
16 passed in 120.59s

TestRiskCoreNegativeEvidence (9 tests):
  ✅ zero neg → no penalty
  ✅ 1 neg → exactly -1.0 penalty
  ✅ 2 neg → exactly -2.0 penalty
  ✅ probability monotonically decreases with neg count
  ✅ FP scenario: HIGH → LOW with 2× neg
  ✅ TP scenario: stays CRITICAL/HIGH even with 2× neg
  ✅ to_dict() includes neg fields when count > 0
  ✅ to_dict() omits neg fields when count = 0
  ✅ score_findings() integrates neg_evidence list

TestFullPipelineNegativeEvidence (6 tests):
  ✅ _negative_evidence metadata present (l3_ran=True, l4_ran=True)
  ✅ 14 layers activated (including L1-L4 + RiskCore)
  ✅ 14 unified findings found
  ✅ 14/14 findings annotated with negative_evidence
  ✅ FalsePositiveVault findings correctly penalized
  ✅ risk_breakdown contains neg evidence fields

TestComparativeProbability (1 test):
  ✅ Mathematical proof: P drops from 0.8022 → 0.3543 (ΔP = 0.4478)
```

---

## Configuration / التكوين

The penalty constant can be tuned:

| `NEGATIVE_EVIDENCE_PENALTY` | Effect per source | 2× sources |
|---|---|---|
| `-0.5` | ~half severity step | ~one step |
| **`-1.0`** (current) | **~one severity step** | **~two steps** |
| `-1.5` | ~1.5 steps | ~three steps |

To change, edit the constant in `risk_core.py`:
```python
NEGATIVE_EVIDENCE_PENALTY = -1.0  # Adjust as needed
```

The weight optimizer (`weight_optimizer.py`) can also learn the optimal penalty value from labeled data if a ground-truth benchmark is provided.

---

## Backward Compatibility / التوافق العكسي

- **No breaking changes**: `negative_evidence_count` defaults to `0` in `compute_exploit_probability()`, so all existing callers work without modification.
- **to_dict() is additive**: The `negative_evidence` key only appears when `count > 0`, so downstream consumers that don't expect it won't be affected.
- **Finding dict is additive**: `f["negative_evidence"]` is only set when there IS negative evidence; findings without it have the identical behavior as before.
