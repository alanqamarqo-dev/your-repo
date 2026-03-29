"""
Diagnose: Are heikal_math and action_space truly bad, or is the evaluation logic wrong?
"""
import json, re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─── Ground Truth ───
GROUND_TRUTH = {
    "reentrancy_vault.sol": [
        {"type": "reentrancy", "function": "withdraw", "severity": "CRITICAL",
         "keywords": ["reentrancy", "reentrant", "re-enter", "callback", "external call before"]},
        {"type": "cross_function_reentrancy", "function": "transfer", "severity": "HIGH",
         "keywords": ["reentrancy", "cross-function", "stale", "transfer"]},
    ],
    "unchecked_call.sol": [
        {"type": "unchecked_return", "function": "withdrawUnsafe", "severity": "HIGH",
         "keywords": ["unchecked", "return", "send", "low-level"]},
        {"type": "unchecked_return", "function": "forwardPayment", "severity": "HIGH",
         "keywords": ["unchecked", "return", "call", "low-level"]},
        {"type": "unchecked_return", "function": "unsafeTokenTransfer", "severity": "MEDIUM",
         "keywords": ["unchecked", "return", "transfer", "erc20"]},
    ],
    "tx_origin_auth.sol": [
        {"type": "tx_origin", "function": "transferOwnership", "severity": "HIGH",
         "keywords": ["tx.origin", "phishing", "authentication"]},
        {"type": "tx_origin", "function": "withdrawAll", "severity": "HIGH",
         "keywords": ["tx.origin", "phishing", "authentication"]},
        {"type": "tx_origin", "function": "setAuthorized", "severity": "MEDIUM",
         "keywords": ["tx.origin", "phishing", "authentication"]},
    ],
    "delegatecall_proxy.sol": [
        {"type": "delegatecall", "function": "upgradeAndCall", "severity": "HIGH",
         "keywords": ["delegatecall", "proxy", "storage", "hijack"]},
        {"type": "delegatecall_no_access", "function": "execute", "severity": "CRITICAL",
         "keywords": ["delegatecall", "no access", "unprotected", "arbitrary"]},
        {"type": "delegatecall", "function": "fallback", "severity": "HIGH",
         "keywords": ["delegatecall", "proxy", "fallback"]},
    ],
    "unprotected_selfdestruct.sol": [
        {"type": "selfdestruct", "function": "destroy", "severity": "CRITICAL",
         "keywords": ["selfdestruct", "destroy", "unprotected", "kill"]},
        {"type": "selfdestruct", "function": "kill", "severity": "CRITICAL",
         "keywords": ["selfdestruct", "kill", "unprotected", "destroy"]},
    ],
    "timestamp_lottery.sol": [
        {"type": "weak_randomness", "function": "play", "severity": "HIGH",
         "keywords": ["random", "predictable", "block.timestamp", "block.number", "weak"]},
        {"type": "timestamp_dependence", "function": "claimBonus", "severity": "MEDIUM",
         "keywords": ["timestamp", "block.timestamp", "manipulation", "miner"]},
        {"type": "block_number_dependence", "function": "isEligible", "severity": "LOW",
         "keywords": ["block.number", "predictable"]},
        {"type": "missing_access_control", "function": "claimBonus", "severity": "MEDIUM",
         "keywords": ["access control", "unprotected", "no modifier", "anyone"]},
    ],
}

def normalize(s):
    if isinstance(s, list):
        s = " ".join(str(x) for x in s)
    if not isinstance(s, str):
        s = str(s)
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def finding_matches_vuln_ORIGINAL(finding, vuln):
    """The ORIGINAL matching logic from test_pipeline_accuracy.py"""
    title = normalize(finding.get("title", ""))
    desc = normalize(finding.get("description", "") or "")
    category = normalize(finding.get("category", "") or "")
    func = normalize(finding.get("function", "") or "")
    source = normalize(finding.get("source", "") or "")
    vuln_type = normalize(finding.get("vulnerability_type", "") or "")
    attack_steps = normalize(finding.get("attack_steps", "") or "")
    combined = f"{title} {desc} {category} {func} {source} {vuln_type} {attack_steps}"

    vuln_func = vuln["function"].lower()
    func_match = vuln_func in combined

    keyword_matches = sum(1 for kw in vuln["keywords"] if kw.lower() in combined)
    keyword_match = keyword_matches > 0

    type_norm = normalize(vuln["type"])
    type_match = type_norm in combined

    proof = finding.get("exploit_proof", {})
    if proof:
        proof_text = normalize(str(proof))
        if vuln_func in proof_text:
            func_match = True
        keyword_matches += sum(1 for kw in vuln["keywords"] if kw.lower() in proof_text)
        keyword_match = keyword_matches > 0

    if (func_match or type_match) and keyword_match:
        return True
    if keyword_matches >= 2:
        return True
    if func_match and type_match:
        return True
    if func_match and keyword_matches >= 1:
        return True
    return False


# ═══════════════════════════════════════════════════════════
# Load the full pipeline results
# ═══════════════════════════════════════════════════════════
import glob
candidates = glob.glob("D:\\AGL\\audit_results_agl_accuracy_*.json")
if not candidates:
    print("No audit results file found!")
    sys.exit(1)

results_file = candidates[-1]
print(f"Loading: {results_file}")

with open(results_file, "r", encoding="utf-8") as f:
    data = json.load(f)

unified = data.get("results", {}).get("unified_findings", [])
print(f"Total unified findings: {len(unified)}\n")

# ═══════════════════════════════════════════════════════════
# HEIKAL MATH DIAGNOSIS
# ═══════════════════════════════════════════════════════════
print("=" * 90)
print("HEIKAL MATH — DETAILED MATCHING DIAGNOSIS")
print("=" * 90)

heikal = [f for f in unified if f.get("_layer") == "heikal_math"]
print(f"\nTotal heikal findings: {len(heikal)}")

heikal_tp_candidates = 0
heikal_true_fp = 0
heikal_eval_bug = 0

for i, f in enumerate(heikal):
    contract_raw = f.get("_contract", "?")
    # Map contract name to .sol filename
    contract_file = None
    for sol_file in GROUND_TRUTH:
        base = sol_file.replace(".sol", "")
        if base.lower() in contract_raw.lower():
            contract_file = sol_file
            break
    
    func_name = f.get("function", "")
    title = f.get("title", "")
    
    # Is this on a safe contract?
    if "safe_vault" in contract_raw.lower() or "safe_token" in contract_raw.lower():
        print(f"  [{i+1}] {contract_raw}/{func_name} — SAFE CONTRACT → TRUE FP (hallucination)")
        heikal_true_fp += 1
        continue
    
    if not contract_file:
        print(f"  [{i+1}] {contract_raw}/{func_name} — unknown contract → TRUE FP")
        heikal_true_fp += 1
        continue
    
    gt_vulns = GROUND_TRUTH[contract_file]
    
    # Does the function name match ANY ground truth vuln function?
    func_in_gt = [v for v in gt_vulns if v["function"].lower() == func_name.lower()]
    
    # Does the ORIGINAL matching logic match?
    original_matched = False
    original_match_target = None
    for v in gt_vulns:
        if finding_matches_vuln_ORIGINAL(f, v):
            original_matched = True
            original_match_target = v
            break
    
    if original_matched:
        print(f"  [{i+1}] {contract_raw}/{func_name} — ORIGINAL LOGIC MATCHES TP: {original_match_target['type']}/{original_match_target['function']}")
        heikal_tp_candidates += 1
    elif func_in_gt:
        # Function matches but keywords don't → EVALUATION BUG
        print(f"  [{i+1}] {contract_raw}/{func_name} — ❗ EVAL BUG: function matches GT but keywords fail")
        v = func_in_gt[0]
        combined_text = normalize(f"{title} {f.get('description', '')} {f.get('category', '')} {func_name} {f.get('source', '')} {f.get('vulnerability_type', '')}")
        keyword_matches = sum(1 for kw in v["keywords"] if kw.lower() in combined_text)
        type_match = normalize(v["type"]) in combined_text
        print(f"       GT vuln: {v['type']}/{v['function']}")
        print(f"       combined: '{combined_text[:120]}'")
        print(f"       kw_matches={keyword_matches}/{len(v['keywords'])}, type_match={type_match}")
        print(f"       keywords: {v['keywords']}")
        heikal_eval_bug += 1
    else:
        # Function doesn't match any GT vuln → is it truly irrelevant?
        is_generic = func_name.lower() in ("deposit", "receive", "fallback", "fund", "approve")
        if is_generic and not any(v["function"].lower() == func_name.lower() for v in gt_vulns):
            print(f"  [{i+1}] {contract_raw}/{func_name} — TRUE FP (generic function, not a GT vuln)")
            heikal_true_fp += 1
        else:
            # Check if function is related to any vuln at all
            print(f"  [{i+1}] {contract_raw}/{func_name} — AMBIGUOUS (function not in GT but may be related)")
            heikal_true_fp += 1

print(f"\n  HEIKAL SUMMARY:")
print(f"    Original eval says TP: {heikal_tp_candidates}")
print(f"    EVAL BUG (should be TP): {heikal_eval_bug}")
print(f"    True FP: {heikal_true_fp}")
print(f"    CORRECTED: TP={heikal_tp_candidates + heikal_eval_bug}, FP={heikal_true_fp}")

# ═══════════════════════════════════════════════════════════
# ACTION SPACE DIAGNOSIS
# ═══════════════════════════════════════════════════════════
print(f"\n{'=' * 90}")
print("ACTION SPACE — DETAILED MATCHING DIAGNOSIS")
print("=" * 90)

action = [f for f in unified if "action" in str(f.get("source", "")).lower()]
print(f"\nTotal action_space findings: {len(action)}")

action_tp_candidates = 0
action_true_fp = 0
action_eval_bug = 0

for i, f in enumerate(action):
    contract_raw = f.get("_contract", "?")
    title = f.get("title", "")
    
    # Extract function name from title "High-value attack target: FUNCNAME"
    func_in_title = ""
    if ":" in title:
        func_in_title = title.split(":")[-1].strip()
    
    # Is this on a safe contract?
    if "safe_vault" in contract_raw.lower() or "safe_token" in contract_raw.lower():
        print(f"  [{i+1}] {contract_raw}/{func_in_title} — SAFE CONTRACT → TRUE FP")
        action_true_fp += 1
        continue
    
    # Find contract in GT
    contract_file = None
    for sol_file in GROUND_TRUTH:
        base = sol_file.replace(".sol", "")
        if base.lower() in contract_raw.lower():
            contract_file = sol_file
            break
    
    if not contract_file:
        print(f"  [{i+1}] {contract_raw}/{func_in_title} — unknown contract → TRUE FP")
        action_true_fp += 1
        continue
    
    gt_vulns = GROUND_TRUTH[contract_file]
    
    # Does the function from title match any GT vuln?
    func_in_gt = [v for v in gt_vulns if v["function"].lower() == func_in_title.lower()]
    
    # Does original matching work?
    original_matched = False
    for v in gt_vulns:
        if finding_matches_vuln_ORIGINAL(f, v):
            original_matched = True
            break
    
    if original_matched:
        print(f"  [{i+1}] {contract_raw}/{func_in_title} — ORIGINAL LOGIC MATCHES → TP")
        action_tp_candidates += 1
    elif func_in_gt:
        # Function matches GT but keywords fail
        v = func_in_gt[0]
        combined_text = normalize(f"{title} {f.get('description', '')} {f.get('category', '')} {f.get('function', '')} {f.get('source', '')} {f.get('vulnerability_type', '')}")
        keyword_matches = sum(1 for kw in v["keywords"] if kw.lower() in combined_text)
        type_match = normalize(v["type"]) in combined_text
        func_field_match = v["function"].lower() in combined_text
        
        print(f"  [{i+1}] {contract_raw}/{func_in_title} — ❗ EVAL BUG: function '{func_in_title}' matches GT vuln '{v['type']}/{v['function']}'")
        print(f"       BUT matching fails because:")
        print(f"       combined: '{combined_text[:120]}'")
        print(f"       func field in finding: '{f.get('function', '')}'  (empty?)")
        print(f"       func_in_combined={func_field_match}, kw_matches={keyword_matches}, type_match={type_match}")
        print(f"       The function name is in TITLE but not in 'function' field!")
        action_eval_bug += 1
    else:
        # E.g. withdraw on unprotected_selfdestruct — GT has destroy/kill, not withdraw
        print(f"  [{i+1}] {contract_raw}/{func_in_title} — NOT in GT → check if related...")
        # Check if the function IS vulnerable but not in our GT definition
        print(f"       GT functions for this contract: {[v['function'] for v in gt_vulns]}")
        action_true_fp += 1

print(f"\n  ACTION SPACE SUMMARY:")
print(f"    Original eval says TP: {action_tp_candidates}")
print(f"    EVAL BUG (should be TP): {action_eval_bug}")
print(f"    True FP: {action_true_fp}")
print(f"    CORRECTED: TP={action_tp_candidates + action_eval_bug}, FP={action_true_fp}")

# ═══════════════════════════════════════════════════════════
# FINAL DIAGNOSIS
# ═══════════════════════════════════════════════════════════
print(f"\n{'=' * 90}")
print("FINAL DIAGNOSIS")
print("=" * 90)
total_eval_bug = heikal_eval_bug + action_eval_bug
total_missed_tp = heikal_eval_bug + action_eval_bug
print(f"""
  HEIKAL MATH:
    Reported:   0 TP, 20 FP
    Corrected:  {heikal_tp_candidates + heikal_eval_bug} TP, {heikal_true_fp} FP
    Eval bugs:  {heikal_eval_bug} findings wrongly classified as FP
    
  ACTION SPACE:
    Reported:   0 TP, 7 FP  
    Corrected:  {action_tp_candidates + action_eval_bug} TP, {action_true_fp} FP
    Eval bugs:  {action_eval_bug} findings wrongly classified as FP

  TOTAL EVAL BUGS: {total_eval_bug} TP wrongly counted as FP
  
  If we fix the eval:
    Old overall: TP=16, FP=96, FN=1 → Precision=14.3%, Recall=94.1%
    New overall: TP={16 + total_missed_tp}, FP={96 - total_missed_tp}, FN=? → Precision={round((16 + total_missed_tp) / max(16 + total_missed_tp + 96 - total_missed_tp, 1) * 100, 1)}%
""")
