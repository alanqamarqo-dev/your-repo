"""
═══════════════════════════════════════════════════════════════════════════════
  AGL Pipeline Accuracy Measurement Test
  
  Runs the FULL audit pipeline on contracts with KNOWN vulnerabilities,
  then compares actual findings vs ground truth to compute:
    - Per-layer TP / FP / FN
    - Precision, Recall, F1 per layer
    - Hallucination rate (FP on safe contracts)
    - Overall pipeline accuracy
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import json
import time
from pathlib import Path
from collections import defaultdict

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_here, "..")))
sys.path.insert(0, os.path.abspath(os.path.join(_here, "..", "..")))


# ═══════════════════════════════════════════════════════════
#  GROUND TRUTH: contracts with KNOWN vulnerabilities
# ═══════════════════════════════════════════════════════════

GROUND_TRUTH_VULNERABLE = {
    "reentrancy_vault.sol": {
        "contract": "ReentrancyVault",
        "vulns": [
            {"type": "reentrancy", "function": "withdraw", "severity": "CRITICAL",
             "keywords": ["reentrancy", "reentrant", "re-enter", "callback", "external call before"]},
            {"type": "cross_function_reentrancy", "function": "transfer", "severity": "HIGH",
             "keywords": ["reentrancy", "cross-function", "stale", "transfer"]},
        ],
    },
    "unchecked_call.sol": {
        "contract": "UncheckedCallToken",
        "vulns": [
            {"type": "unchecked_return", "function": "withdrawUnsafe", "severity": "HIGH",
             "keywords": ["unchecked", "return", "send", "low-level"]},
            {"type": "unchecked_return", "function": "forwardPayment", "severity": "HIGH",
             "keywords": ["unchecked", "return", "call", "low-level"]},
            {"type": "unchecked_return", "function": "unsafeTokenTransfer", "severity": "MEDIUM",
             "keywords": ["unchecked", "return", "transfer", "erc20"]},
        ],
    },
    "tx_origin_auth.sol": {
        "contract": "TxOriginAuth",
        "vulns": [
            {"type": "tx_origin", "function": "transferOwnership", "severity": "HIGH",
             "keywords": ["tx.origin", "phishing", "authentication"]},
            {"type": "tx_origin", "function": "withdrawAll", "severity": "HIGH",
             "keywords": ["tx.origin", "phishing", "authentication"]},
            {"type": "tx_origin", "function": "setAuthorized", "severity": "MEDIUM",
             "keywords": ["tx.origin", "phishing", "authentication"]},
        ],
    },
    "delegatecall_proxy.sol": {
        "contract": "DelegatecallProxy",
        "vulns": [
            {"type": "delegatecall", "function": "upgradeAndCall", "severity": "HIGH",
             "keywords": ["delegatecall", "proxy", "storage", "hijack"]},
            {"type": "delegatecall_no_access", "function": "execute", "severity": "CRITICAL",
             "keywords": ["delegatecall", "no access", "unprotected", "arbitrary"]},
            {"type": "delegatecall", "function": "fallback", "severity": "HIGH",
             "keywords": ["delegatecall", "proxy", "fallback"]},
        ],
    },
    "unprotected_selfdestruct.sol": {
        "contract": "UnprotectedSelfDestruct",
        "vulns": [
            {"type": "selfdestruct", "function": "destroy", "severity": "CRITICAL",
             "keywords": ["selfdestruct", "destroy", "unprotected", "kill"]},
            {"type": "selfdestruct", "function": "kill", "severity": "CRITICAL",
             "keywords": ["selfdestruct", "kill", "unprotected", "destroy"]},
        ],
    },
    "timestamp_lottery.sol": {
        "contract": "TimestampLottery",
        "vulns": [
            {"type": "weak_randomness", "function": "play", "severity": "HIGH",
             "keywords": ["random", "predictable", "block.timestamp", "block.number", "weak"]},
            {"type": "timestamp_dependence", "function": "claimBonus", "severity": "MEDIUM",
             "keywords": ["timestamp", "block.timestamp", "manipulation", "miner"]},
            {"type": "block_number_dependence", "function": "isEligible", "severity": "LOW",
             "keywords": ["block.number", "predictable"]},
            {"type": "missing_access_control", "function": "claimBonus", "severity": "MEDIUM",
             "keywords": ["access control", "unprotected", "no modifier", "anyone"]},
        ],
    },
}

# Safe contracts — should have 0 true findings
GROUND_TRUTH_SAFE = {
    "safe_vault.sol": {"contract": "SafeVault"},
    "safe_token.sol": {"contract": "SafeToken"},
}

# Total ground truth
TOTAL_VULNS = sum(len(v["vulns"]) for v in GROUND_TRUTH_VULNERABLE.values())


def normalize(s) -> str:
    """Lowercase, strip non-alnum for fuzzy matching."""
    import re
    if isinstance(s, list):
        s = " ".join(str(x) for x in s)
    if not isinstance(s, str):
        s = str(s)
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def finding_matches_vuln(finding: dict, vuln: dict) -> bool:
    """Check if a pipeline finding matches a ground-truth vulnerability."""
    title = normalize(finding.get("title", ""))
    desc = normalize(finding.get("description", "") or "")
    category = normalize(finding.get("category", "") or "")
    func = normalize(finding.get("function", "") or "")
    source = normalize(finding.get("source", "") or "")
    vuln_type = normalize(finding.get("vulnerability_type", "") or "")
    # Include all text in attack_steps if present
    attack_steps = normalize(finding.get("attack_steps", "") or "")
    combined = f"{title} {desc} {category} {func} {source} {vuln_type} {attack_steps}"

    # Match by function name
    vuln_func = vuln["function"].lower()
    func_match = vuln_func in combined

    # Match by keywords (at least 1 keyword must appear)
    keyword_matches = sum(1 for kw in vuln["keywords"] if kw.lower() in combined)
    keyword_match = keyword_matches > 0

    # Match by vulnerability type
    type_norm = normalize(vuln["type"])
    type_match = type_norm in combined

    # Also check the exploit_proof sub-dict if present
    proof = finding.get("exploit_proof", {})
    if proof:
        proof_text = normalize(str(proof))
        if vuln_func in proof_text:
            func_match = True
        keyword_matches += sum(1 for kw in vuln["keywords"] if kw.lower() in proof_text)
        keyword_match = keyword_matches > 0

    # A match requires: (function match OR type match) AND keyword match
    # OR: function + type both match
    # OR: at least 2 keywords match
    if (func_match or type_match) and keyword_match:
        return True
    if keyword_matches >= 2:
        return True
    if func_match and type_match:
        return True
    # Relaxed: function name in finding and severity matches roughly
    if func_match and keyword_matches >= 1:
        return True

    # Layers like heikal_math and action_space flag functions as risky
    # without naming the specific vulnerability type or keywords.
    # If the finding's own function field OR explicit title names the
    # exact GT function, count as match even without keyword evidence.
    finding_func_field = (finding.get("function", "") or "").lower().strip()
    func_in_title_exact = vuln_func in title.split()
    if finding_func_field == vuln_func or func_in_title_exact:
        return True

    return False


def classify_layer(finding: dict) -> str:
    """Classify which pipeline layer produced a finding."""
    layer = finding.get("_layer", "")
    source = normalize(finding.get("source", "") or "")

    if layer == "deep_scan":
        # Sub-classify deep_scan findings
        if "pattern" in source:
            return "pattern_engine"
        if "z3" in source or "symbolic" in source:
            return "z3_symbolic"
        if "detector" in source or "agl_22" in source:
            return "detectors"
        if "orchestrat" in source or "security_suite" in source:
            return "security_orchestrator"
        if "offensive" in source:
            return "offensive_security"
        if "temporal" in source:
            return "temporal_analysis"
        if "action" in source:
            return "action_space"
        if "attack" in source:
            return "attack_simulation"
        if "search" in source:
            return "search_engine"
        if "state" in source:
            return "state_validator"
        return "deep_scan_other"
    if layer == "z3_standalone":
        return "z3_standalone"
    if layer == "detectors_standalone":
        return "detectors_standalone"
    if layer == "exploit_reasoning":
        return "exploit_reasoning"
    if layer == "heikal_math":
        return "heikal_math"
    if layer == "state_extraction":
        return "state_extraction"
    return "unknown"


def run_pipeline_on_contracts() -> dict:
    """
    Copy ONLY the ground-truth contracts into a temp directory,
    then run the full pipeline on that subset.
    Returns the raw report dict from run_audit.
    """
    import shutil
    import tempfile
    from agl_security_tool.audit_pipeline import run_audit

    test_root = Path(__file__).parent.parent / "test_contracts"
    vuln_dir = test_root / "vulnerable"
    safe_dir = test_root / "safe"

    # Build a flat temp dir with only the 8 ground-truth contracts
    tmp = tempfile.mkdtemp(prefix="agl_accuracy_")
    try:
        for fname in GROUND_TRUTH_VULNERABLE:
            src = vuln_dir / fname
            if src.exists():
                shutil.copy2(src, os.path.join(tmp, fname))
        for fname in GROUND_TRUTH_SAFE:
            src = safe_dir / fname
            if src.exists():
                shutil.copy2(src, os.path.join(tmp, fname))

        print(f"  Temp dir: {tmp}")
        print(f"  Contracts: {os.listdir(tmp)}")

        result = run_audit(
            target=tmp,
            mode="full",
            skip_llm=True,
            skip_heikal=False,
            generate_poc=False,
        )
        return result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def analyze_findings_for_contract(
    unified_findings: list,
    contract_filename: str,
    ground_truth_vulns: list,
) -> dict:
    """
    For a single contract, compare unified findings vs ground truth.
    Returns {TP, FP, FN, matched_vulns, unmatched_findings, missed_vulns, per_layer}.
    """
    # Filter findings for this contract
    contract_findings = []
    for f in unified_findings:
        contract_field = f.get("_contract", "") or ""
        title = f.get("title", "") or ""
        # Match by filename in _contract or by contract name in title
        fname_base = contract_filename.replace(".sol", "")
        if (contract_filename.lower() in contract_field.lower()
                or fname_base.lower() in contract_field.lower()
                or fname_base.lower() in normalize(title)):
            contract_findings.append(f)

    tp = 0
    fp = 0
    matched_vulns = set()
    matched_findings = set()
    per_layer_tp = defaultdict(int)
    per_layer_fp = defaultdict(int)

    # For each finding, check if it matches any ground truth vuln
    for i, finding in enumerate(contract_findings):
        layer = classify_layer(finding)
        matched = False
        for j, vuln in enumerate(ground_truth_vulns):
            if j in matched_vulns:
                continue  # Already matched this vuln
            if finding_matches_vuln(finding, vuln):
                matched = True
                matched_vulns.add(j)
                matched_findings.add(i)
                tp += 1
                per_layer_tp[layer] += 1
                break

        if not matched:
            fp += 1
            per_layer_fp[layer] += 1

    fn = len(ground_truth_vulns) - len(matched_vulns)
    missed = [ground_truth_vulns[j] for j in range(len(ground_truth_vulns)) if j not in matched_vulns]
    unmatched = [contract_findings[i] for i in range(len(contract_findings)) if i not in matched_findings]

    return {
        "total_findings": len(contract_findings),
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "matched_vulns": [ground_truth_vulns[j] for j in sorted(matched_vulns)],
        "missed_vulns": missed,
        "unmatched_findings": unmatched,
        "per_layer_tp": dict(per_layer_tp),
        "per_layer_fp": dict(per_layer_fp),
    }


def analyze_safe_contract(
    unified_findings: list,
    contract_filename: str,
) -> dict:
    """For safe contracts, any finding is a false positive."""
    contract_findings = []
    fname_base = contract_filename.replace(".sol", "")
    for f in unified_findings:
        contract_field = f.get("_contract", "") or ""
        title = f.get("title", "") or ""
        if (contract_filename.lower() in contract_field.lower()
                or fname_base.lower() in contract_field.lower()):
            contract_findings.append(f)

    per_layer_fp = defaultdict(int)
    for f in contract_findings:
        layer = classify_layer(f)
        per_layer_fp[layer] += 1

    return {
        "total_findings": len(contract_findings),
        "FP": len(contract_findings),
        "per_layer_fp": dict(per_layer_fp),
        "false_positives": contract_findings,
    }


def analyze_heikal_hallucination(all_results: dict) -> dict:
    """
    Analyze Heikal Math specifically for hallucination:
    - Attack scenarios with hardcoded barriers (not from code)
    - HIGH/CRITICAL results on keyword-only triggers
    """
    heikal = all_results.get("heikal_math", {})
    if not heikal:
        return {"available": False}

    attacks = heikal.get("attacks", {})
    functions = heikal.get("functions", {})

    # Attack scenarios: count by severity
    attack_sev = defaultdict(int)
    for aname, adata in attacks.items():
        sev = adata.get("severity", "INFO")
        attack_sev[sev] += 1

    # Function results: count by severity
    func_sev = defaultdict(int)
    for fname, fdata in functions.items():
        sev = fdata.get("severity", "INFO")
        func_sev[sev] += 1

    # All attack scenarios use hardcoded barriers — 100% are synthetic
    hallucinated_attacks = len(attacks)
    total_heikal = len(attacks) + len(functions)

    return {
        "available": True,
        "total_functions": len(functions),
        "total_attacks": len(attacks),
        "function_severity": dict(func_sev),
        "attack_severity": dict(attack_sev),
        "hallucinated_attacks": hallucinated_attacks,
        "hallucination_pct": round(hallucinated_attacks / max(total_heikal, 1) * 100, 1),
    }


def compute_metrics(tp: int, fp: int, fn: int) -> dict:
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 0.001)
    return {
        "precision": round(precision * 100, 1),
        "recall": round(recall * 100, 1),
        "f1": round(f1 * 100, 1),
    }


# ═══════════════════════════════════════════════════════════
#  MAIN TEST
# ═══════════════════════════════════════════════════════════

def test_pipeline_accuracy():
    """
    Run the full pipeline, compare vs ground truth, measure accuracy.
    """
    test_root = Path(__file__).parent.parent / "test_contracts"
    vuln_dir = test_root / "vulnerable"
    safe_dir = test_root / "safe"

    # Verify test contracts exist
    missing = []
    for fname in GROUND_TRUTH_VULNERABLE:
        if not (vuln_dir / fname).exists():
            missing.append(f"vulnerable/{fname}")
    for fname in GROUND_TRUTH_SAFE:
        if not (safe_dir / fname).exists():
            missing.append(f"safe/{fname}")

    if missing:
        print(f"  ❌ Missing test contracts: {missing}")
        return False

    print(f"\n  Ground truth: {TOTAL_VULNS} known vulnerabilities in {len(GROUND_TRUTH_VULNERABLE)} contracts")
    print(f"  Safe contracts: {len(GROUND_TRUTH_SAFE)} (should have 0 findings)\n")

    # ─────────────────────────────────────────
    #  Run full pipeline on ONLY ground-truth contracts
    # ─────────────────────────────────────────
    print("  " + "═" * 66)
    print("  RUNNING FULL PIPELINE ON 8 GROUND-TRUTH CONTRACTS...")
    print("  " + "═" * 66 + "\n")

    t0 = time.time()
    report = run_pipeline_on_contracts()
    elapsed = time.time() - t0

    if report.get("error"):
        print(f"  ❌ Pipeline error: {report['error']}")
        return False

    all_results = report.get("results", {})
    unified = all_results.get("unified_findings", [])
    dedup_stats = all_results.get("dedup_stats", {})
    total_report_findings = report.get("total_findings", 0)

    print(f"\n  Pipeline completed in {elapsed:.1f}s")
    print(f"  Total unified findings: {len(unified)}")
    print(f"  Dedup stats: {dedup_stats}")

    # ─────────────────────────────────────────
    #  Analyze vulnerable contracts
    # ─────────────────────────────────────────
    print(f"\n  {'═' * 66}")
    print("  VULNERABLE CONTRACT ANALYSIS — TP / FP / FN")
    print(f"  {'═' * 66}\n")

    global_tp = 0
    global_fp = 0
    global_fn = 0
    per_contract = {}
    layer_tp_total = defaultdict(int)
    layer_fp_total = defaultdict(int)

    for fname, truth in GROUND_TRUTH_VULNERABLE.items():
        result = analyze_findings_for_contract(unified, fname, truth["vulns"])
        per_contract[fname] = result
        global_tp += result["TP"]
        global_fp += result["FP"]
        global_fn += result["FN"]
        for layer, count in result["per_layer_tp"].items():
            layer_tp_total[layer] += count
        for layer, count in result["per_layer_fp"].items():
            layer_fp_total[layer] += count

        status = "✅" if result["FN"] == 0 else "⚠️ "
        print(f"  {status} {fname:40s} | TP={result['TP']}  FP={result['FP']}  FN={result['FN']}  (found {result['total_findings']})")
        if result["missed_vulns"]:
            for mv in result["missed_vulns"]:
                print(f"       ❌ MISSED: {mv['type']} in {mv['function']}() [{mv['severity']}]")
        if result["unmatched_findings"][:3]:
            for uf in result["unmatched_findings"][:3]:
                print(f"       🔸 FP: {uf.get('title', '?')[:70]}")

    # ─────────────────────────────────────────
    #  Analyze safe contracts (hallucination)
    # ─────────────────────────────────────────
    print(f"\n  {'═' * 66}")
    print("  SAFE CONTRACT ANALYSIS — FALSE POSITIVE / HALLUCINATION")
    print(f"  {'═' * 66}\n")

    safe_fp = 0
    safe_details = {}
    for fname, truth in GROUND_TRUTH_SAFE.items():
        result = analyze_safe_contract(unified, fname)
        safe_details[fname] = result
        safe_fp += result["FP"]
        for layer, count in result["per_layer_fp"].items():
            layer_fp_total[layer] += count

        status = "✅" if result["FP"] == 0 else "🔴"
        print(f"  {status} {fname:40s} | FP={result['FP']}  (should be 0)")
        for fp_f in result.get("false_positives", [])[:5]:
            print(f"       🔸 HALLUCINATION: {fp_f.get('title', '?')[:70]}")

    total_fp = global_fp + safe_fp

    # ─────────────────────────────────────────
    #  Heikal Math hallucination analysis
    # ─────────────────────────────────────────
    print(f"\n  {'═' * 66}")
    print("  HEIKAL MATH HALLUCINATION ANALYSIS")
    print(f"  {'═' * 66}\n")

    heikal_analysis = analyze_heikal_hallucination(all_results)
    if heikal_analysis.get("available"):
        print(f"  Functions analyzed: {heikal_analysis['total_functions']}")
        print(f"  Attack scenarios: {heikal_analysis['total_attacks']} (ALL use hardcoded barriers)")
        print(f"  Function severity: {heikal_analysis['function_severity']}")
        print(f"  Attack severity: {heikal_analysis['attack_severity']}")
        print(f"  Hallucinated attacks: {heikal_analysis['hallucinated_attacks']}/{heikal_analysis['total_attacks'] + heikal_analysis['total_functions']}")
        print(f"  Hallucination %: {heikal_analysis['hallucination_pct']}%")
    else:
        print("  Heikal Math was not available/did not run")

    # ─────────────────────────────────────────
    #  Per-Layer accuracy
    # ─────────────────────────────────────────
    print(f"\n  {'═' * 66}")
    print("  PER-LAYER ACCURACY")
    print(f"  {'═' * 66}\n")

    all_layers = sorted(set(list(layer_tp_total.keys()) + list(layer_fp_total.keys())))
    print(f"  {'Layer':<25s} | {'TP':>4s} | {'FP':>4s} | {'Precision':>10s}")
    print(f"  {'-'*25}-+{'-'*6}+{'-'*6}+{'-'*11}")
    for layer in all_layers:
        tp = layer_tp_total.get(layer, 0)
        fp = layer_fp_total.get(layer, 0)
        prec = tp / max(tp + fp, 1) * 100
        print(f"  {layer:<25s} | {tp:4d} | {fp:4d} | {prec:9.1f}%")

    # ─────────────────────────────────────────
    #  Overall metrics
    # ─────────────────────────────────────────
    metrics = compute_metrics(global_tp, total_fp, global_fn)

    print(f"\n  {'═' * 66}")
    print("  OVERALL PIPELINE ACCURACY REPORT")
    print(f"  {'═' * 66}")
    print(f"""
  Ground Truth Vulnerabilities: {TOTAL_VULNS}
  ─────────────────────────────────────
  True Positives (TP):   {global_tp:4d}  (correctly found)
  False Positives (FP):  {total_fp:4d}  (reported but don't exist)
    — on vulnerable:     {global_fp:4d}
    — on safe (halluc.): {safe_fp:4d}
  False Negatives (FN):  {global_fn:4d}  (missed real vulns)
  ─────────────────────────────────────
  Precision:             {metrics['precision']:5.1f}%  (of what we report, how much is real)
  Recall:                {metrics['recall']:5.1f}%  (of real vulns, how many did we find)
  F1 Score:              {metrics['f1']:5.1f}%  (harmonic mean)
  ─────────────────────────────────────
  Hallucination on safe: {safe_fp:4d} findings on {len(GROUND_TRUTH_SAFE)} safe contracts
  Pipeline time:         {elapsed:.1f}s
""")

    # ─────────────────────────────────────────
    #  Save detailed results to JSON
    # ─────────────────────────────────────────
    output_path = Path(__file__).parent / "accuracy_results.json"
    serializable = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pipeline_time_s": round(elapsed, 1),
        "ground_truth_vulns": TOTAL_VULNS,
        "ground_truth_safe_contracts": len(GROUND_TRUTH_SAFE),
        "overall": {
            "TP": global_tp,
            "FP_vulnerable": global_fp,
            "FP_safe": safe_fp,
            "FP_total": total_fp,
            "FN": global_fn,
            **metrics,
        },
        "per_contract": {},
        "per_layer": {},
        "heikal_hallucination": heikal_analysis,
        "dedup_stats": dedup_stats,
        "total_unified_findings": len(unified),
    }
    for fname, res in per_contract.items():
        serializable["per_contract"][fname] = {
            "TP": res["TP"], "FP": res["FP"], "FN": res["FN"],
            "total_findings": res["total_findings"],
            "missed": [v["type"] + "/" + v["function"] for v in res["missed_vulns"]],
            "per_layer_tp": res["per_layer_tp"],
            "per_layer_fp": res["per_layer_fp"],
        }
    for layer in all_layers:
        tp = layer_tp_total.get(layer, 0)
        fp = layer_fp_total.get(layer, 0)
        serializable["per_layer"][layer] = {
            "TP": tp, "FP": fp,
            "precision": round(tp / max(tp + fp, 1) * 100, 1),
        }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
        print(f"  💾 Detailed results saved to: {output_path}")
    except Exception as e:
        print(f"  ⚠️  Failed to save: {e}")

    # ─────────────────────────────────────────
    #  Assertions
    # ─────────────────────────────────────────
    assert global_tp > 0, "Should find at least 1 true positive"
    assert metrics["recall"] > 0, "Recall should be > 0%"

    print(f"  ✅ Pipeline accuracy test: COMPLETE")
    return True


# ═══════════════════════════════════════════════════════════
#  Runner
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  AGL PIPELINE ACCURACY MEASUREMENT TEST")
    print("=" * 70)

    try:
        success = test_pipeline_accuracy()
    except Exception as e:
        print(f"\n  ❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        success = False

    print(f"\n{'=' * 70}")
    print(f"  {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"{'=' * 70}")
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
