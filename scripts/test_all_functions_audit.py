#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
🔬 اختبار شامل لكل دالة في offensive_security.py
   - اختبار فردي لكل دالة
   - اختبار جماعي (التكامل)
   - تحديد الدوال المنفصلة عن هدف اصطياد الثغرات
═══════════════════════════════════════════════════════════════════════
"""
import sys, os, time, json, traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "AGL_NextGen", "src"))
sys.path.insert(0, os.path.join(ROOT, "AGL_NextGen", "src", "agl", "engines", "strict_logic"))
sys.path.insert(0, ROOT)
os.environ.setdefault('AGL_SKIP_TORCH', '1')

# ═══════════════ ملف الاختبار ═══════════════
TEST_SOL = os.path.join(ROOT, "vulnerable.sol")

# ═══════════════ حالة الاختبارات ═══════════════
results = {}

def test(name, func, *args, **kwargs):
    """مغلف اختبار: يُشغّل دالة ويسجل النتيجة"""
    print(f"\n{'─'*70}")
    print(f"🧪 اختبار: {name}")
    print(f"{'─'*70}")
    t0 = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - t0
        
        # تحقق من النتيجة
        is_dict = isinstance(result, dict)
        has_error = is_dict and "error" in result
        is_empty = result is None or result == {} or result == []
        
        if has_error:
            status = "⚠️ ERROR"
            detail = result["error"][:100]
        elif is_empty:
            status = "❌ EMPTY"
            detail = "الدالة ترجع نتيجة فارغة"
        else:
            status = "✅ PASS"
            # ملخص ذكي
            if is_dict:
                keys = list(result.keys())[:5]
                detail = f"keys={keys}"
                # عد النتائج إن وُجدت
                if "findings" in result:
                    n = len(result["findings"])
                    detail += f" | findings={n}"
                if "call_chains" in result:
                    n = len(result["call_chains"])
                    detail += f" | chains={n}"
                if "survivors" in result:
                    n = len(result["survivors"])
                    detail += f" | survivors={n}"
            else:
                detail = f"type={type(result).__name__} len={len(str(result)[:200])}"
        
        results[name] = {"status": status, "time": elapsed, "detail": detail}
        print(f"   {status} ({elapsed:.2f}s) → {detail}")
        return result
        
    except Exception as e:
        elapsed = time.time() - t0
        results[name] = {"status": "💀 CRASH", "time": elapsed, "detail": str(e)[:150]}
        print(f"   💀 CRASH ({elapsed:.2f}s) → {e}")
        traceback.print_exc()
        return None


# ═══════════════════════════════════════════════════════════════════════
print("╔" + "═"*68 + "╗")
print("║" + " 🔬 اختبار شامل لـ OffensiveSecurityEngine ".center(68) + "║")
print("╚" + "═"*68 + "╝")

# ═══════════════ تحميل المحرك ═══════════════
from agl.engines.offensive_security import OffensiveSecurityEngine
engine = test("__init__", OffensiveSecurityEngine)

if not engine:
    print("\n💀 فشل التحميل — لا يمكن الاستمرار")
    sys.exit(1)

# قراءة كود الاختبار
with open(TEST_SOL, 'r') as f:
    sol_code = f.read()

# ═══════════════════════════════════════════════════════════════════════
# الجزء 1: اختبار كل دالة بشكل فردي
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "═"*70)
print("📋 الجزء 1: اختبار كل دالة بشكل فردي")
print("═"*70)

# --- 1. _strict_classify_severity ---
test("_strict_classify_severity (CRITICAL)",
     engine._strict_classify_severity,
     {"text": "Reentrancy with external call drains funds"})

test("_strict_classify_severity (LOW)",
     engine._strict_classify_severity,
     {"text": "Informational: missing NatSpec comment"})

test("_strict_classify_severity (MEDIUM)",
     engine._strict_classify_severity,
     {"text": "DoS: unbounded loop in withdrawal"})

# --- 2. _strict_validate_exploit ---
test("_strict_validate_exploit (EXPLOITABLE)",
     engine._strict_validate_exploit,
     {"vector": ".call{value:", "impact": "fund drain", "severity": "CRITICAL", "mitigated": False})

test("_strict_validate_exploit (FALSE_POSITIVE)",
     engine._strict_validate_exploit,
     {"vector": None, "impact": None, "severity": "LOW", "mitigated": True})

test("_strict_validate_exploit (NEEDS_REVIEW)",
     engine._strict_validate_exploit,
     {"vector": "transfer call", "impact": None, "severity": "LOW", "mitigated": False})

# --- 3. _formal_verify_vulnerability ---
test("_formal_verify_vulnerability (reentrancy)",
     engine._formal_verify_vulnerability,
     {"type": "Reentrancy external call", "severity": "CRITICAL"},
     sol_code)

test("_formal_verify_vulnerability (overflow)",
     engine._formal_verify_vulnerability,
     {"type": "Integer overflow unchecked", "severity": "HIGH"},
     sol_code)

test("_formal_verify_vulnerability (access_control)",
     engine._formal_verify_vulnerability,
     {"type": "Access control bypass via tx.origin", "severity": "HIGH"},
     sol_code)

# --- 4. _formal_check_invariants ---
test("_formal_check_invariants (reentrancy)",
     engine._formal_check_invariants,
     sol_code,
     {"type": "reentrancy", "function": "withdraw"})

test("_formal_check_invariants (delta)",
     engine._formal_check_invariants,
     sol_code,
     {"type": "delta balance unlock", "function": "settle"})

# --- 5. _quantum_deep_audit ---
test("_quantum_deep_audit",
     engine._quantum_deep_audit,
     sol_code[:2000])

# --- 6. _dynamic_evm_simulation ---
test("_dynamic_evm_simulation",
     engine._dynamic_evm_simulation,
     TEST_SOL, {})

# --- 7. EVM sub-functions ---
test("_evm_extract_contracts",
     engine._evm_extract_contracts, sol_code)

test("_evm_extract_state_vars",
     engine._evm_extract_state_vars, sol_code)

test("_evm_extract_functions",
     engine._evm_extract_functions, sol_code)

test("_evm_extract_money_operations",
     engine._evm_extract_money_operations, sol_code)

funcs = engine._evm_extract_functions(sol_code)
ops = engine._evm_extract_money_operations(sol_code)
svars = engine._evm_extract_state_vars(sol_code)
chains = test("_evm_build_call_chains",
              engine._evm_build_call_chains, funcs, ops, svars)

if chains:
    test("_evm_z3_prove_money_flow (chain[0])",
         engine._evm_z3_prove_money_flow, chains[0], sol_code)
    
    z3r = engine._evm_z3_prove_money_flow(chains[0], sol_code)
    test("_evm_logic_gate_classify (chain[0])",
         engine._evm_logic_gate_classify, chains[0], z3r)

# --- 8. _analyze_smart_contracts (الدالة الرئيسية) ---
test("_analyze_smart_contracts",
     engine._analyze_smart_contracts, TEST_SOL)

# --- 9. _ai_analyze_target (LLM) ---
test("_ai_analyze_target",
     engine._ai_analyze_target, "127.0.0.1",
     {"scan": {"open_ports": [80]}, "headers": {"Server": "nginx"}})

# --- 10. _generate_attack_plan ---
test("_generate_attack_plan",
     engine._generate_attack_plan, "vulnerable.sol",
     {"findings": [{"severity": "CRITICAL", "text": "reentrancy"}]})

# --- 11. _resonance_select_exploit ---
test("_resonance_select_exploit",
     engine._resonance_select_exploit, "ctf.example.com",
     {"scan": {"open_ports": [80, 443, 8080]}})

# --- 12-14. (REMOVED: _scan_ports, _analyze_headers, _grab_banner — disconnected functions deleted)

# --- 15. process_task: smart_contract_audit ---
test("process_task('smart_contract_audit')",
     engine.process_task, "smart_contract_audit", TEST_SOL)

# --- 16. process_task: generate_attack_plan ---
test("process_task('generate_attack_plan')",
     engine.process_task, "generate_attack_plan", TEST_SOL,
     {"findings": [{"severity": "CRITICAL"}]})

# --- 17. process_task: resonance_exploit_match ---
test("process_task('resonance_exploit_match')",
     engine.process_task, "resonance_exploit_match", "ctf.test.com")

# --- 18. process_task: quantum_deep_audit ---
test("process_task('quantum_deep_audit')",
     engine.process_task, "quantum_deep_audit", sol_code[:1500])

# --- 19. process_task: port_scan ---
test("process_task('port_scan')",
     engine.process_task, "port_scan", "127.0.0.1")

# --- 20. process_task: header_analysis ---
test("process_task('header_analysis')",
     engine.process_task, "header_analysis", "http://127.0.0.1:11434")

# --- 21. process_task: banner_grab ---
test("process_task('banner_grab')",
     engine.process_task, "banner_grab", "127.0.0.1")

# --- 22. process_task: unknown ---
test("process_task('unknown_task')",
     engine.process_task, "nonexistent_task", "test")

# ═══════════════════════════════════════════════════════════════════════
# الجزء 2: اختبار جماعي (تدفق كامل)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "═"*70)
print("📋 الجزء 2: اختبار التكامل الجماعي (Full Pipeline)")
print("═"*70)

def full_pipeline_test():
    """تشغيل التدفق الكامل كما يحدث في الإنتاج"""
    # 1. التحليل الثابت
    audit = engine._analyze_smart_contracts(TEST_SOL)
    findings = audit.get("findings", [])
    suite = audit.get("suite_findings", [])
    
    # 2. تصنيف بالمنطق الصارم
    classified = []
    for f in findings:
        for issue in f.get("issues", []):
            if isinstance(issue, dict):
                classified.append(issue)
    
    # 3. إثبات رياضي
    proven = [c for c in classified if c.get("mathematically_proven")]
    
    # 4. المحاكاة الديناميكية
    evm = engine._dynamic_evm_simulation(TEST_SOL, audit)
    dangerous = [c for c in evm.get("call_chains", []) if c.get("z3_proof", {}).get("proven_dangerous")]
    
    # 5. التحليل الكمي (إن توفر)
    quantum = engine._quantum_deep_audit(sol_code[:2000])
    
    # 6. خطة الهجوم
    plan = engine._generate_attack_plan(TEST_SOL, {"findings": findings})
    
    return {
        "static_findings": len(findings),
        "suite_findings": len(suite),
        "classified_issues": len(classified),
        "mathematically_proven": len(proven),
        "evm_chains": len(evm.get("call_chains", [])),
        "evm_dangerous": len(dangerous),
        "quantum_findings": len(quantum.get("findings", [])) if isinstance(quantum, dict) else 0,
        "attack_plan": "generated" if plan and "error" not in plan else "failed",
        "severity_summary": audit.get("severity_summary", {}),
    }

test("FULL_PIPELINE (collective)", full_pipeline_test)


# ═══════════════════════════════════════════════════════════════════════
# الجزء 3: التقرير النهائي
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "═"*70)
print("📊 التقرير النهائي — نتائج كل الدوال")
print("═"*70)

passed = 0
failed = 0
crashed = 0
errors = 0

for name, res in results.items():
    icon = res["status"][:2]
    print(f"   {res['status']:15s} | {res['time']:6.2f}s | {name}")
    if "PASS" in res["status"]:
        passed += 1
    elif "ERROR" in res["status"]:
        errors += 1
    elif "CRASH" in res["status"]:
        crashed += 1
    else:
        failed += 1

total = len(results)
print(f"\n{'═'*70}")
print(f"   ✅ نجحت: {passed}/{total}")
print(f"   ⚠️ أخطاء: {errors}/{total}")
print(f"   ❌ فارغة: {failed}/{total}")
print(f"   💀 انهارت: {crashed}/{total}")
print(f"{'═'*70}")

# ═══ تصنيف الدوال: مرتبطة بالهدف أم منفصلة ═══
print("\n" + "═"*70)
print("🔍 تصنيف الدوال: هل مرتبطة بهدف اصطياد الثغرات؟")
print("═"*70)

vuln_hunting_core = {
    "_analyze_smart_contracts": "🎯 النواة: المحلل الثابت + Heuristic + AI + Z3",
    "_strict_classify_severity": "🎯 بوابات منطقية صارمة لتصنيف الخطورة",
    "_strict_validate_exploit": "🎯 بوابات منطقية لتصفية الإيجابيات الكاذبة",
    "_formal_verify_vulnerability": "🎯 Z3 SMT Solver لإثبات الثغرات رياضياً",
    "_formal_check_invariants": "🎯 Z3 لفحص الثوابت الرياضية (DeFi)",
    "_dynamic_evm_simulation": "🎯 محاكاة تدفق المال + Z3 + Logic Gates",
    "_evm_extract_contracts": "🎯 استخراج بنية العقد",
    "_evm_extract_state_vars": "🎯 استخراج متغيرات الحالة",
    "_evm_extract_functions": "🎯 استخراج الدوال وتحليلها",
    "_evm_extract_money_operations": "🎯 استخراج عمليات المال",
    "_evm_build_call_chains": "🎯 بناء سلاسل الاستدعاء",
    "_evm_z3_prove_money_flow": "🎯 إثبات Z3 لتدفق المال",
    "_evm_logic_gate_classify": "🎯 تصنيف بالمنطق الصارم",
    "_quantum_deep_audit": "🟡 LLM wrapper — يولد فرضيات عبر Ollama",
    "process_task": "🎯 نقطة الدخول الرئيسية",
}

support_functions = {
    "_ai_analyze_target": "🔵 دعم: تحليل AI عبر HolographicLLM — لـ CTF",
    "_generate_attack_plan": "🔵 دعم: تخطيط استراتيجي عبر MetaReasoner",
    "_resonance_select_exploit": "🔵 دعم: تصفية بالرنين الكمي — لـ CTF",
}

disconnected = {
    "_scan_ports": "🔴 منفصلة: فحص منافذ TCP — لا علاقة بتحليل العقود",
    "_run_nmap_orchestration": "🔴 منفصلة: تنسيق Nmap — لا علاقة بتحليل العقود",
    "_analyze_headers": "🔴 منفصلة: فحص HTTP headers — لا علاقة بتحليل العقود",
    "_grab_banner": "🔴 منفصلة: Banner grabbing — لا علاقة بتحليل العقود",
    "_launch_figma_trap": "🔴 منفصلة: خادم SSRF لـ Figma bounty محدد",
    "_launch_figma_redirect_server": "🔴 منفصلة: نفس السابق (alias)",
    "_launch_wallet_poc": "🔴 منفصلة: خادم phishing لـ Xverse bounty محدد",
    "_orchestrate_ctf_solve": "🔴 منفصلة: حل CTF لـ 1Password — Selenium+XSS+SQLi",
    "_GMX_simulation_in_scan_ports": "🔴 مسرحية: محاكاة GMX مبرمجة مسبقاً داخل _scan_ports",
}

print("\n🎯 دوال أساسية (مرتبطة بالهدف مباشرة):")
for fn, desc in vuln_hunting_core.items():
    r = results.get(fn, results.get(fn.lstrip('_'), {}))
    status = "?"
    for k, v in results.items():
        if fn in k:
            status = v["status"][:2]
            break
    print(f"   {status} {desc}")

print(f"\n🔵 دوال داعمة (تضيف قيمة غير مباشرة):")
for fn, desc in support_functions.items():
    print(f"      {desc}")

print(f"\n🔴 دوال منفصلة (لا تخدم هدف اصطياد ثغرات العقود):")
for fn, desc in disconnected.items():
    print(f"      {desc}")

print(f"\n📊 الإحصائيات:")
print(f"   أساسية: {len(vuln_hunting_core)} دالة")
print(f"   داعمة:  {len(support_functions)} دالة")
print(f"   منفصلة: {len(disconnected)} دالة")
pct = len(vuln_hunting_core) / (len(vuln_hunting_core) + len(support_functions) + len(disconnected)) * 100
print(f"   نسبة الدوال المرتبطة بالهدف: {pct:.0f}%")
