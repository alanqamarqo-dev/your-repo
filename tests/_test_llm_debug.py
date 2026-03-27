"""Debug: Test LLM enrichment directly to see what Ollama returns."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "AGL_NextGen", "src"))

# 1) Check Ollama availability
print("=" * 60)
print("  LLM BACKEND DIAGNOSTICS")
print("=" * 60)

try:
    import requests
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    print(f"\n  Ollama status: {r.status_code}")
    models = r.json().get("models", [])
    print(f"  Available models ({len(models)}):")
    for m in models:
        print(f"    - {m.get('name', '?')}  ({m.get('size', 0)//1024//1024}MB)")
except Exception as e:
    print(f"\n  ❌ Ollama not reachable: {e}")
    sys.exit(1)

# 2) Test direct LLM call
print(f"\n{'='*60}")
print("  DIRECT LLM CALL TEST")
print("='*60")

test_prompt = """أنت خبير أمان عقود ذكية. حلل هذه الثغرة:

## الثغرة
- النوع: reentrancy
- الخطورة: critical
- الوصف: External call before state update

## الكود
```solidity
function withdraw(uint amount) public {
    require(balances[msg.sender] >= amount);
    (bool ok, ) = msg.sender.call{value: amount}("");
    require(ok);
    balances[msg.sender] -= amount;
}
```

## المطلوب:
1. اشرح الثغرة بالتفصيل
2. اقترح إصلاحاً محدداً
3. اكتب PoC بسيط إن أمكن

أجب بـ JSON:
{"explanation": "...", "fix": "...", "poc": "..."}
"""

t0 = time.time()
try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:3b-instruct",
            "prompt": test_prompt,
            "stream": False,
        },
        timeout=60,
    )
    elapsed = time.time() - t0
    print(f"\n  Status: {response.status_code}")
    print(f"  Time: {elapsed:.1f}s")
    
    if response.status_code == 200:
        raw = response.json().get("response", "")
        print(f"  Response length: {len(raw)} chars")
        print(f"\n  --- RAW RESPONSE ---")
        print(raw[:2000])
        print(f"  --- END ---")
        
        # Try to parse JSON
        import re
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                print(f"\n  ✅ Parsed JSON successfully!")
                print(f"  Keys: {list(data.keys())}")
                if data.get("fix"):
                    print(f"  Fix: {data['fix'][:200]}")
                if data.get("poc"):
                    print(f"  PoC: {data['poc'][:200]}")
            except json.JSONDecodeError as e:
                print(f"\n  ⚠️ JSON parse error: {e}")
        else:
            print(f"\n  ⚠️ No JSON found in response")
    else:
        print(f"  ❌ Error: {response.text[:500]}")
except Exception as e:
    print(f"\n  ❌ Request failed: {e}")

# 3) Test the actual LLMBackend.analyze_finding
print(f"\n{'='*60}")
print("  LLMBackend.analyze_finding TEST")
print("=" * 60)

try:
    from agl.engines.security_orchestrator import (
        LLMBackend, Finding, Severity, VulnCategory
    )
    llm = LLMBackend()
    print(f"  LLM available: {llm.available}")
    
    if llm.available:
        test_finding = Finding(
            id="TEST-001",
            title="Reentrancy Vulnerability",
            severity=Severity.CRITICAL,
            category=VulnCategory.REENTRANCY,
            description="External call before state update in withdraw()",
            file_path="test.sol",
            line_start=18,
            line_end=23,
            code_snippet="msg.sender.call{value: amount}('');",
            source_tool="test",
            confidence=0.95,
        )
        
        code_ctx = """function withdraw(uint amount) public {
    require(balances[msg.sender] >= amount);
    (bool ok, ) = msg.sender.call{value: amount}("");
    require(ok);
    balances[msg.sender] -= amount;
}"""
        
        t1 = time.time()
        enriched = llm.analyze_finding(test_finding, code_ctx)
        print(f"  Time: {time.time()-t1:.1f}s")
        print(f"  recommendation: {enriched.recommendation[:200] if enriched.recommendation else '(empty)'}")
        print(f"  poc_code: {enriched.poc_code[:200] if enriched.poc_code else '(empty)'}")
        print(f"  description: {enriched.description[:200]}")
except Exception as e:
    import traceback
    print(f"  ❌ Error: {e}")
    traceback.print_exc()
