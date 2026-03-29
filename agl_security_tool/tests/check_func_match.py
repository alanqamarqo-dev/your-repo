"""Quick check: does the relaxed func_match cause false TPs?"""
import json, re, sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def normalize(s):
    if isinstance(s, list): s = " ".join(str(x) for x in s)
    if not isinstance(s, str): s = str(s)
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()

GT = {
    "reentrancy_vault.sol": [
        {"function": "withdraw"}, {"function": "transfer"},
    ],
    "unchecked_call.sol": [
        {"function": "withdrawUnsafe"}, {"function": "forwardPayment"}, {"function": "unsafeTokenTransfer"},
    ],
    "tx_origin_auth.sol": [
        {"function": "transferOwnership"}, {"function": "withdrawAll"}, {"function": "setAuthorized"},
    ],
    "delegatecall_proxy.sol": [
        {"function": "upgradeAndCall"}, {"function": "execute"}, {"function": "fallback"},
    ],
    "unprotected_selfdestruct.sol": [
        {"function": "destroy"}, {"function": "kill"},
    ],
    "timestamp_lottery.sol": [
        {"function": "play"}, {"function": "claimBonus"}, {"function": "isEligible"}, {"function": "claimBonus"},
    ],
}

candidates = glob.glob("D:\\AGL\\audit_results_agl_accuracy_*.json")
with open(candidates[-1], "r", encoding="utf-8") as f:
    data = json.load(f)
unified = data.get("results", {}).get("unified_findings", [])

# Check which findings have func_match=True (function name in combined text)
print("Findings where a GT function name appears in combined text:")
print()
for f_item in unified:
    contract_raw = f_item.get("_contract", "")
    contract_file = None
    for sol in GT:
        if sol.replace(".sol","").lower() in contract_raw.lower():
            contract_file = sol
            break
    if not contract_file:
        continue
    
    title = normalize(f_item.get("title", ""))
    desc = normalize(f_item.get("description", "") or "")
    cat = normalize(f_item.get("category", "") or "")
    func_f = normalize(f_item.get("function", "") or "")
    src = normalize(f_item.get("source", "") or "")
    combined = title + " " + desc + " " + cat + " " + func_f + " " + src
    
    for v in GT[contract_file]:
        vuln_func = v["function"].lower()
        if vuln_func in combined:
            layer = f_item.get("_layer", "")
            source = f_item.get("source", "")
            real_title = f_item.get("title", "")[:65]
            print("  " + contract_file + " | " + layer + "/" + source)
            print("    matched func: " + vuln_func)
            print("    title: " + real_title)
            # Check if this is a WRONG match (function name is substring of another word)
            # e.g. "transfer" appearing in "unsafeTokenTransfer" 
            words = combined.split()
            exact_word = vuln_func in words
            substring_only = not exact_word
            if substring_only:
                print("    WARNING: substring match only (not exact word)")
            print()
            break

print("\n--- Check for 'transfer' substring false matches on reentrancy_vault ---")
# GT for reentrancy_vault has function "transfer"
for f_item in unified:
    contract_raw = f_item.get("_contract", "")
    if "reentrancy_vault" not in contract_raw.lower():
        continue
    title = normalize(f_item.get("title", ""))
    desc = normalize(f_item.get("description", "") or "")
    func_f = normalize(f_item.get("function", "") or "")
    combined = title + " " + desc + " " + func_f
    if "transfer" in combined:
        real_title = f_item.get("title", "")[:65]
        layer = f_item.get("_layer", "")
        # Is "transfer" an exact function reference or a substring?
        print("  " + real_title + " (layer=" + layer + ")")
        print("    combined: " + combined[:100])
        print()
