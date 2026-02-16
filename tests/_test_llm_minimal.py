"""Minimal LLM enrichment test — direct Ollama batch call."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agl_security_tool"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "AGL_NextGen", "src"))

import logging
logging.disable(logging.CRITICAL)  # Silence all loggers

# Quick Ollama check
import requests
print("[1] Checking Ollama...", flush=True)
try:
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    print(f"    Status: {r.status_code}", flush=True)
except Exception as e:
    print(f"    FAIL: {e}", flush=True)
    sys.exit(1)

# Warm up with tiny request
print("[2] Warm-up call...", flush=True)
t0 = time.time()
try:
    r = requests.post("http://localhost:11434/api/chat",
        json={"model": "qwen2.5:3b-instruct",
              "messages": [{"role": "user", "content": "Hi"}],
              "stream": False},
        timeout=120)
    print(f"    OK ({time.time()-t0:.1f}s): {r.json().get('message',{}).get('content','')[:50]}", flush=True)
except Exception as e:
    print(f"    FAIL ({time.time()-t0:.1f}s): {e}", flush=True)

# Test batch security analysis prompt
print("[3] Security analysis batch LLM call...", flush=True)
system_msg = (
    "You are a smart contract security expert. "
    "Analyze each vulnerability and provide: "
    "1) Detailed explanation, 2) Specific Solidity fix code, 3) Simple PoC if possible.\n"
    'Reply ONLY with a JSON array:\n'
    '[{"id": 1, "explanation": "...", "fix": "...", "poc": "..."}]'
)
user_msg = """### Finding 1
- Severity: CRITICAL
- Line: 18
- Title: Reentrancy Vulnerability
- Description: External call before state update — state change after .call()
```solidity
function withdraw(uint amount) public {
    require(balances[msg.sender] >= amount);
    (bool ok, ) = msg.sender.call{value: amount}("");
    require(ok);
    balances[msg.sender] -= amount;
}
```

### Finding 2
- Severity: HIGH
- Line: 26
- Title: tx.origin Authentication
- Description: Using tx.origin for authentication is vulnerable to phishing
```solidity
function changeOwner(address newOwner) public {
    require(tx.origin == owner);
    owner = newOwner;
}
```"""

t1 = time.time()
try:
    r = requests.post("http://localhost:11434/api/chat",
        json={"model": "qwen2.5:3b-instruct",
              "messages": [
                  {"role": "system", "content": system_msg},
                  {"role": "user", "content": user_msg},
              ],
              "stream": False},
        timeout=180)
    elapsed = time.time() - t1
    print(f"    Status: {r.status_code} ({elapsed:.1f}s)", flush=True)
    
    if r.status_code == 200:
        raw = r.json().get("message", {}).get("content", "")
        print(f"    Response length: {len(raw)} chars", flush=True)
        print(f"    --- RAW ---", flush=True)
        print(raw[:3000], flush=True)
        print(f"    --- END ---", flush=True)
        
        # Parse
        import re
        arr_match = re.search(r'\[.*\]', raw, re.DOTALL)
        if arr_match:
            try:
                arr = json.loads(arr_match.group())
                print(f"\n    PARSED {len(arr)} items from JSON array", flush=True)
                for item in arr:
                    print(f"    #{item.get('id','?')}: explanation={item.get('explanation','')[:100]}", flush=True)
                    print(f"           fix={item.get('fix','')[:100]}", flush=True)
            except json.JSONDecodeError as e:
                print(f"    JSON parse error: {e}", flush=True)
        else:
            print(f"    No JSON array found in response", flush=True)
except Exception as e:
    print(f"    FAIL ({time.time()-t1:.1f}s): {e}", flush=True)

# Now test full pipeline
print("\n[4] Full pipeline scan with LLM...", flush=True)
try:
    from agl_security_tool.core import AGLSecurityAudit
    audit = AGLSecurityAudit()
    t2 = time.time()
    result = audit.scan(os.path.join(os.path.dirname(__file__), "vulnerable.sol"))
    elapsed2 = time.time() - t2
    
    print(f"    Scan time: {elapsed2:.1f}s", flush=True)
    print(f"    Layers: {result.get('layers_used', [])}", flush=True)
    print(f"    LLM raw response present: {'llm_raw_response' in result}", flush=True)
    
    for i, f in enumerate(result.get("all_findings_unified", [])[:5], 1):
        sev = f.get("severity", "?").upper()
        title = f.get("title", "?")
        has_llm = "llm_explanation" in f
        has_fix = "fix" in f
        has_poc = "poc" in f
        print(f"    [{sev}] {title} | LLM:{has_llm} Fix:{has_fix} PoC:{has_poc}", flush=True)
        if has_llm:
            print(f"      > {f['llm_explanation'][:150]}", flush=True)
        if has_fix:
            print(f"      > FIX: {f['fix'][:150]}", flush=True)
    
    if result.get("warnings"):
        print(f"    Warnings: {result['warnings']}", flush=True)
except Exception as e:
    import traceback
    print(f"    FAIL: {e}", flush=True)
    traceback.print_exc()

print("\nDONE.", flush=True)
