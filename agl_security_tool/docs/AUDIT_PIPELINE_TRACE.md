# تتبع مسارات جميع دوال audit_pipeline.py

**تاريخ التحديث:** 2026-03-12  
**الملف المصدري:** `agl_security_tool/audit_pipeline.py` — ~2900 سطر، 24 دالة  
**الغرض:** تتبع كامل لكل دالة — الملف المُستدعى، سلسلة الاستدعاء، طريقة العمل، كيفية التشغيل.

---

## الفهرس

| # | الدالة | السطر | التصنيف |
|---|--------|-------|---------|
| 1 | [`banner()`](#1-banner) | 90 | أداة طباعة |
| 2 | [`is_github_url()`](#2-is_github_url) | 98 | أداة فحص |
| 3 | [`is_git_url()`](#3-is_git_url) | 103 | أداة فحص |
| 4 | [`clone_repo()`](#4-clone_repo) | 113 | أداة استنساخ |
| 5 | [`install_dependencies()`](#5-install_dependencies) | 192 | أداة تثبيت |
| 6 | [`resolve_target()`](#6-resolve_target) | 242 | موجّه |
| 7 | [`load_engines()`](#7-load_engines) | 286 | مُحمِّل |
| 8 | [`discover_project()`](#8-discover_project) | 403 | اكتشاف |
| 9 | [`run_shared_parsing()`](#9-run_shared_parsing) | 580 | تحليل مشترك |
| 10 | [`deduplicate_cross_layer()`](#10-deduplicate_cross_layer) | 656 | تنقية |
| 11 | [`run_core_deep_scan()`](#11-run_core_deep_scan) | 819 | فحص عميق |
| 12 | [`run_z3_symbolic()`](#12-run_z3_symbolic) | 886 | Z3 |
| 13 | [`run_state_extraction()`](#13-run_state_extraction) | 961 | استخراج حالة |
| 14 | [`run_detectors()`](#14-run_detectors) | 1038 | كواشف |
| 15 | [`run_exploit_reasoning()`](#15-run_exploit_reasoning) | 1128 | تحليل استغلال |
| 16 | [`extract_function_blocks()`](#16-extract_function_blocks) | 1227 | استخراج دوال |
| 17 | [`analyze_function_security()`](#17-analyze_function_security) | 1255 | تحليل أمني |
| 18 | [`build_attack_scenarios()`](#18-build_attack_scenarios) | 1504 | سيناريوهات |
| 19 | [`run_heikal_math()`](#19-run_heikal_math) | 1875 | هيكل رياضيات |
| 20 | [`run_poc_generation()`](#20-run_poc_generation) | 2184 | توليد PoC |
| 21 | [`generate_final_report()`](#21-generate_final_report) | 2292 | تقرير |
| 22 | [`generate_markdown_report()`](#22-generate_markdown_report) | 2446 | تقرير MD |
| 23 | [`run_audit()`](#23-run_audit) | 2551 | المنسّق الرئيسي |
| 24 | [`main()`](#24-main) | 2775 | نقطة الدخول |

---

## مخطط الاستدعاء الكامل

```
main()  ← CLI (python agl_audit_api.py <target>)
  └── run_audit(target, ...)
        ├── resolve_target()
        │     ├── is_git_url() → is_github_url()
        │     ├── clone_repo()              ← subprocess: git clone
        │     └── install_dependencies()    ← subprocess: forge/npm install
        ├── load_engines()
        │     ├── core.AGLSecurityAudit()   ← agl_security_tool/core.py
        │     ├── Z3SymbolicEngine()        ← agl_security_tool/z3_symbolic_engine.py
        │     ├── StateExtractionEngine()   ← agl_security_tool/state_extraction/engine.py
        │     ├── ExploitReasoningEngine()  ← agl_security_tool/exploit_reasoning.py
        │     ├── SolidityFlattener()       ← agl_security_tool/solidity_flattener.py
        │     ├── DetectorRunner()          ← agl_security_tool/detectors/__init__.py
        │     ├── SoliditySemanticParser()  ← agl_security_tool/detectors/solidity_parser.py
        │     ├── HeikalTunnelingScorer()   ← agl_security_tool/heikal_math/tunneling_scorer.py
        │     ├── WaveDomainEvaluator()     ← agl_security_tool/heikal_math/wave_evaluator.py
        │     ├── HolographicVulnerabilityMemory() ← agl_security_tool/heikal_math/holographic_patterns.py
        │     └── ResonanceProfitOptimizer() ← agl_security_tool/heikal_math/resonance_optimizer.py
        ├── discover_project()
        │     ├── ProjectScanner()          ← agl_security_tool/project_scanner.py
        │     ├── should_skip()             (داخلية)
        │     └── is_test_file()            (داخلية)
        ├── run_shared_parsing()
        │     └── parser.parse()            ← SoliditySemanticParser.parse()
        ├── run_core_deep_scan()
        │     └── core.deep_scan()          ← AGLSecurityAudit.deep_scan()
        │           └── _scan_file()        ← (شرح تفصيلي أدناه)
        ├── run_z3_symbolic()
        │     └── z3_engine.analyze()       ← Z3SymbolicEngine.analyze()
        ├── run_state_extraction()
        │     └── state_engine.extract_project() ← StateExtractionEngine.extract_project()
        ├── run_detectors()
        │     └── runner.run(parsed)        ← DetectorRunner.run()
        ├── run_exploit_reasoning()
        │     └── exploit.analyze()         ← ExploitReasoningEngine.analyze()
        ├── run_heikal_math()
        │     ├── extract_function_blocks() (داخلية — regex)
        │     ├── analyze_function_security() (داخلية)
        │     ├── build_attack_scenarios()  (داخلية)
        │     ├── tunneling.compute()       ← HeikalTunnelingScorer.compute()
        │     ├── wave.evaluate()           ← WaveDomainEvaluator.evaluate()
        │     ├── holographic.match()       ← HolographicVulnerabilityMemory.match()
        │     └── resonance.optimize_amount() ← ResonanceProfitOptimizer.optimize_amount()
        ├── deduplicate_cross_layer()       (داخلية)
        ├── run_poc_generation()
        │     ├── PoCGenerator()            ← agl_security_tool/poc_generator.py
        │     ├── generator.generate()      ← PoCGenerator.generate()
        │     └── run_foundry_pocs()        ← subprocess: forge test
        ├── generate_final_report()         (داخلية)
        └── generate_markdown_report()      (داخلية)
```

---

## التفاصيل لكل دالة

---

### 1. `banner()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 90-96 |
| **الملف المُستدعى** | لا يوجد — دالة طباعة مستقلة |
| **مَن يستدعيها** | `run_shared_parsing()`, `deduplicate_cross_layer()`, `run_core_deep_scan()`, `run_z3_symbolic()`, `run_state_extraction()`, `run_detectors()`, `run_exploit_reasoning()`, `run_heikal_math()`, `run_poc_generation()`, `generate_final_report()` |
| **طريقة عملها** | تطبع عنوان مُحاط بإطار من أحرف `═` بعرض 80 حرف |
| **المدخلات** | `text: str`, `char: str = "═"` |
| **المخرجات** | لا شيء (طباعة فقط) |

---

### 2. `is_github_url()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 98-100 |
| **الملف المُستدعى** | لا يوجد — regex فقط |
| **مَن يستدعيها** | `is_git_url()`, `clone_repo()`, `run_audit()` |
| **طريقة عملها** | `re.match(r"https?://github\.com/[\w\-\.]+/[\w\-\.]+", target)` |
| **المدخلات** | `target: str` |
| **المخرجات** | `bool` |

---

### 3. `is_git_url()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 103-110 |
| **الملف المُستدعى** | `is_github_url()` (أعلاه) |
| **مَن يستدعيها** | `resolve_target()`, `run_audit()` |
| **طريقة عملها** | يتحقق من 4 أنماط: GitHub URL, `.git` suffix, `git@` prefix, `git://` prefix |
| **المدخلات** | `target: str` |
| **المخرجات** | `bool` |

---

### 4. `clone_repo()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 113-190 |
| **الملف المُستدعى** | `subprocess.run(["git", "clone", ...])` — أمر نظام |
| **مَن يستدعيها** | `resolve_target()` |
| **طريقة عملها** | 1. ينظّف URL ويضيف `.git` إن لزم. 2. يُنشئ مجلد مؤقت عبر `tempfile.mkdtemp()`. 3. يُشغّل `git clone --depth 1 --recurse-submodules`. 4. إذا فشل يُعيد بدون submodules. مهلة 5 دقائق. |
| **المدخلات** | `url: str, dest: str = None, branch: str = None, depth: int = 1` |
| **المخرجات** | `str` — مسار المستودع المُستنسَخ |
| **كيفية التشغيل** | تُستدعى تلقائياً عند `run_audit("https://github.com/user/repo")` |

---

### 5. `install_dependencies()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 192-239 |
| **الملف المُستدعى** | `subprocess.run()` — أوامر: `forge install`, `yarn install`, `npm install` |
| **مَن يستدعيها** | `resolve_target()` |
| **طريقة عملها** | 1. يتحقق من وجود `foundry.toml` → `forge install`. 2. يتحقق من `package.json` → `yarn install` (إن وُجد yarn.lock) أو `npm install`. الأخطاء تُبتلع بصمت. |
| **المدخلات** | `project_path: str` |
| **المخرجات** | لا شيء |

---

### 6. `resolve_target()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 242-284 |
| **الملف المُستدعى** | `clone_repo()`, `install_dependencies()` |
| **مَن يستدعيها** | `run_audit()` — الخطوة 0 |
| **طريقة عملها** | ثلاث حالات: (1) Git URL → `clone_repo()` + `install_dependencies()` → مسار مؤقت. (2) ملف `.sol` → `Path.parent`. (3) مجلد → مباشرة. |
| **المدخلات** | `target: str, branch: str = None, no_deps: bool = False` |
| **المخرجات** | `Tuple[str, bool]` — (المسار, هل_مؤقت) |

---

### 7. `load_engines()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 286-402 |
| **الملفات المُستدعاة** | **11 مكون من 7 ملفات** |
| **مَن يستدعيها** | `run_audit()` — الخطوة 1 |
| **طريقة عملها** | يستورد كل محرك في `try/except` مستقل — إذا فشل يُتجاوَز |

**الملفات والكائنات المُحمَّلة:**

| المفتاح | الكائن | الملف المصدري | الـ method الرئيسي |
|---------|--------|--------------|-------------------|
| `engines["core"]` | `AGLSecurityAudit()` | `agl_security_tool/core.py` L42 | `.deep_scan(path) → Dict` |
| `engines["z3"]` | `Z3SymbolicEngine()` | `agl_security_tool/z3_symbolic_engine.py` L63 | `.analyze(source, path) → List[SymExecFinding]` |
| `engines["state"]` | `StateExtractionEngine({...})` | `agl_security_tool/state_extraction/engine.py` L106 | `.extract_project(dir) → ExtractionResult` |
| `engines["exploit"]` | `ExploitReasoningEngine()` | `agl_security_tool/exploit_reasoning.py` L844 | `.analyze(findings, source, path) → Dict` |
| `engines["flattener"]` | `SolidityFlattener(root)` | `agl_security_tool/solidity_flattener.py` L407 | `.flatten(path) → FlattenResult` |
| `engines["detectors"]` | `DetectorRunner()` | `agl_security_tool/detectors/__init__.py` L329 | `.run(contracts) → List[Finding]` |
| `engines["parser"]` | `SoliditySemanticParser()` | `agl_security_tool/detectors/solidity_parser.py` L25 | `.parse(source, path) → List[ParsedContract]` |
| `engines["tunneling"]` | `HeikalTunnelingScorer()` | `agl_security_tool/heikal_math/tunneling_scorer.py` L94 | `.compute(barriers, energy, chain) → TunnelingResult` |
| `engines["wave"]` | `WaveDomainEvaluator()` | `agl_security_tool/heikal_math/wave_evaluator.py` L96 | `.evaluate(features) → WaveEvaluationResult` |
| `engines["holographic"]` | `HolographicVulnerabilityMemory()` | `agl_security_tool/heikal_math/holographic_patterns.py` L75 | `.match(features) → List[PatternMatch]` |
| `engines["resonance"]` | `ResonanceProfitOptimizer()` | `agl_security_tool/heikal_math/resonance_optimizer.py` L80 | `.optimize_amount(value, fn, min, max) → ResonanceOptimizationResult` |

**ملاحظة:** `StateExtractionEngine` يُهيَّأ بإعدادات: `action_space=True, attack_simulation=True, search_engine=True` — لتفعيل L2-L4 داخلياً.

---

### 8. `discover_project()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 403-578 |
| **الملف المُستدعى** | `agl_security_tool/project_scanner.py` → `ProjectScanner` |
| **مَن يستدعيها** | `run_audit()` — الخطوة 2 |
| **طريقة عملها** | 1. يحاول `ProjectScanner(path).discover()` — ماسح ذكي. 2. إذا فشل → fallback يدوي: يبحث عن `src/`, `contracts/`, `.` بترتيب. 3. يمشي `os.walk()` على كل الملفات مع استثناءات: `node_modules, .git, cache, out, build, artifacts, typechain, coverage, crytic-export`. 4. يُصنّف كل `.sol`: مكتبة (lib/) أو واجهة (interfaces/ أو اسم يبدأ بـ I) أو رئيسي. 5. يكتشف نوع المشروع: foundry.toml → foundry، hardhat.config → hardhat، إلخ. |
| **المدخلات** | `project_path: str, config: Dict` — config يحتوي `exclude_tests`, `scan_dependencies` |
| **المخرجات** | `Dict` بهذه المفاتيح: |

```python
{
    "project_type": "foundry" | "hardhat" | "truffle" | "bare",
    "contracts_dir": str,
    "contracts": {name: Path, ...},          # كل العقود
    "main_contracts": [name, ...],           # العقود الرئيسية
    "libraries": [name, ...],               # المكتبات (lib/)
    "interfaces": [name, ...],              # الواجهات (iface/)
    "info": ProjectInfo | None,             # من ProjectScanner
}
```

**الدوال الداخلية:**
- `should_skip(dirpath)` — يفحص إذا المجلد مستثنى
- `is_test_file(name)` — يفحص `.t.sol`, `test*`, `mock*`, `harness*`, `helper*`

---

### 9. `run_shared_parsing()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 580-654 |
| **الملف المُستدعى** | `SoliditySemanticParser.parse()` ← `agl_security_tool/detectors/solidity_parser.py` L25 |
| **مَن يستدعيها** | `run_audit()` — الخطوة 2.5 |
| **طريقة عملها** | 1. يأخذ `engines["parser"]` (SoliditySemanticParser). 2. يحلل كل عقد (ما عدا الواجهات) بـ `parser.parse(source, path)`. 3. يُخزّن النتائج في قاموس `shared[name] = {"parsed": [...], "source": str, "path": Path}`. 4. يبني مجموعة `_safe_funcs` — كل دالة `internal/private/view/pure` — لاستخدامها في كبت النتائج الآمنة لاحقاً. |
| **المدخلات** | `engines: Dict, project: Dict` |
| **المخرجات** | `Dict[str, Any]` — مفتاح خاص `_safe_funcs: set` |

**أهمية هذه الدالة:**
- تمنع تكرار التحليل — كل طبقة تستخدم نفس البيانات المُحلَّلة
- تُستخدم نتائجها في: `run_z3_symbolic()`, `run_detectors()`, `run_heikal_math()`, `deduplicate_cross_layer()`

---

### 10. `deduplicate_cross_layer()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 656-854 |
| **الملف المُستدعى** | لا يوجد — منطق داخلي |
| **مَن يستدعيها** | `run_audit()` — الخطوة 8.5 |
| **طريقة عملها** | 1. يجمع كل النتائج من `deep_scan` → `all_findings_unified`. 2. يجمع نتائج `z3_symbolic` (مكتبات). 3. يجمع نتائج `detectors` (مكتبات). 4. يبني توقيعات deep_scan: `(title_normalized, line ±5)`. 5. يحذف التكرارات من z3_standalone و detectors_standalone. 6. يكبت نتائج الدوال الآمنة (`_safe_funcs`). 7. يُنشر negative_evidence من `_negative_evidence` metadata. 8. يحسب `severity_unified`. |

**ما يدخل unified_findings:**
- ✅ `deep_scan` findings (كل نتائج core.deep_scan)
- ✅ `z3_symbolic` (مكتبات — بعد إزالة التكرارات)
- ✅ `detectors` (مكتبات — بعد إزالة التكرارات)

**ما لا يدخل (وسبب ذلك):**
- ❌ `state_extraction` (project-wide) — لأن نتائج L1-L4 **موجودة بالفعل** داخل deep_scan per-file
- ❌ `exploit_reasoning` (pipeline) — لأن exploit reasoning **يعمل بالفعل** داخل core.py `_run_exploit_reasoning()`
- ❌ `heikal_math` — نوعية مخرجات مختلفة (احتمالات، ليست findings)

**المدخلات** | `all_results: Dict, shared_parse: Dict` |
**المخرجات** | `all_results` مُحدَّث بـ: `unified_findings`, `dedup_stats`, `severity_unified` |

**الدوال الداخلية:**
- `normalize_title(t)` — يحذف أحرف خاصة ويأخذ أول 8 كلمات
- `extract_func_from_finding(f)` — يستخرج اسم الدالة من Finding بـ regex

---

### 11. `run_core_deep_scan()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 855-921 |
| **الملف المُستدعى** | `AGLSecurityAudit.deep_scan()` ← `agl_security_tool/core.py` L255 |
| **مَن يستدعيها** | `run_audit()` — الخطوة 3 |
| **طريقة عملها** | يُشغّل `core.deep_scan(str(path))` على كل عقد رئيسي (≤20 عقد). |

**ما يفعله `deep_scan()` داخلياً (في core.py):**

```
deep_scan(path)
  └── _scan_file(path)
        ├── Layer 0:   SolidityFlattener.flatten()          — دمج الاستيرادات
        ├── Layer 0.5: Z3SymbolicEngine.analyze()           — 8 فحوصات Z3
        ├── Layer 1:   SmartContractAnalyzer.analyze()      — أنماط + CFG
        │              ← agl/engines/smart_contract_analyzer.py
        ├── Layer 2:   SecurityOrchestrator.analyze_file()  — Slither/Mythril/Semgrep
        │              ← agl/engines/security_orchestrator.py
        │              أو ToolBackendRunner.analyze()       — بديل
        │              ← agl_security_tool/tool_backends.py
        ├── Layer 2:   DetectorRunner.run()                 — 22 كاشف
        ├── L1-L4:     StateExtractionEngine.extract()      — لكل ملف على حدة
        │   ├── L1: Financial Graph (entities, relationships, fund_flows)
        │   ├── L1+: Temporal Analysis (CEI violations, reentrancy risks)
        │   ├── L2: ActionSpaceBuilder (actions, attack_sequences)
        │   ├── L3: AttackSimulationEngine (profitable_attacks, best_attack)
        │   └── L4: SearchOrchestrator (profitable_sequences)
        ├── Negative Evidence: _negative_evidence metadata
        ├── Layer 5:   ExploitReasoningEngine.analyze()     — inject proofs
        │              ← agl_security_tool/exploit_reasoning.py
        ├── Dedup:     _deduplicate_and_cross_validate()    — دمج + كبت FP
        ├── RiskCore:  score_findings()                     — P(exploit)
        │              ← agl_security_tool/risk_core.py
        └── LLM:       _llm_enrich_findings()               — شرح (اختياري)
  └── OffensiveSecurityEngine.process_task()                — Layer 3 إضافي
        ← agl/engines/offensive_security.py
  └── RiskCore.score_findings() مرة ثانية                    — إعادة تسجيل
```

**المدخلات** | `engines: Dict, project: Dict` |
**المخرجات** | `Dict[name, result]` — كل result يحتوي `all_findings_unified`, `severity_summary`, `layers_used` |
**وجهة النتائج** | → `all_results["deep_scan"]` → **unified_findings** عبر `deduplicate_cross_layer()` |

---

### 12. `run_z3_symbolic()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 922-996 |
| **الملف المُستدعى** | `Z3SymbolicEngine.analyze()` ← `agl_security_tool/z3_symbolic_engine.py` L63 |
| **مَن يستدعيها** | `run_audit()` — الخطوة 4 |
| **طريقة عملها** | 1. يأخذ قائمة المكتبات فقط (`project["libraries"]`). 2. لكل مكتبة يقرأ الكود (من shared_parse أو القرص). 3. يُشغّل `z3_engine.analyze(source, path)`. 4. يُحوّل النتائج لقواميس. |

**لماذا المكتبات فقط؟** لأن العقود الرئيسية **تُفحص بـ Z3 بالفعل** داخل `core.deep_scan()` → `_scan_file()` → Layer 0.5.

**ماذا يفحص Z3:**
| الفحص | Z3 حقيقي؟ |
|------|----------|
| Reentrancy | ✅ BitVec(256) SAT/UNSAT |
| Unchecked Arithmetic | ✅ BitVec overflow |
| Access Control | ❌ Pattern فقط |
| Division by Zero | ❌ Pattern فقط |
| Balance Invariants | ❌ Pattern فقط |
| Storage Collision | ❌ Pattern فقط |
| Timestamp | ❌ Pattern فقط |
| tx.origin | ✅ SAT/UNSAT |

**المدخلات** | `engines: Dict, project: Dict, shared_parse: Dict` |
**المخرجات** | `List[Dict]` — كل finding يحتوي `is_proven, counterexample` |
**وجهة النتائج** | → `all_results["z3_symbolic"]` → **unified_findings** عبر `deduplicate_cross_layer()` |

---

### 13. `run_state_extraction()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 997-1073 |
| **الملف المُستدعى** | `StateExtractionEngine.extract_project()` ← `agl_security_tool/state_extraction/engine.py` L106 |
| **مَن يستدعيها** | `run_audit()` — الخطوة 5 (فقط في وضع `full`) |
| **طريقة عملها** | 1. يُشغّل `state_engine.extract_project(contracts_dir)`. 2. يطبع إحصائيات: contracts_parsed, entities_found, relationships_found, fund_flows_found. 3. يطبع نتائج Action Space و Attack Simulation و Search Engine إن وُجدت. |

**ما يفعله `extract_project()` داخلياً (10 خطوات):**
```
1. SoliditySemanticParser.parse()   → ParsedContract[]
2. EntityExtractor.extract()         → Entity[] (14 نوع)
3. RelationshipMapper.map()          → Relationship[] (30+ نوع)
4. FundMapper.map()                  → BalanceEntry[] + FundFlow[]
5. FinancialGraphBuilder.build()     → FinancialGraph
6. ConsistencyValidator.validate()   → ValidationResult (6 فحوصات)
7a. ExecutionSemanticsExtractor      → CEI violations
7b. StateMutationTracker             → State deltas
7c. FunctionEffectModeler            → Cross-function deps
7d. TemporalDependencyGraph          → Reentrancy windows
8. ActionSpaceBuilder (L2)           → ActionSpace
9. AttackSimulationEngine (L3)       → SimulationResult
10. SearchOrchestrator (L4)          → SearchResult
```

**لماذا النتائج "منفصلة":**
- **نفس L1-L4 تعمل لكل ملف داخل `core.deep_scan()`** وتُنتج findings تدخل unified_findings
- هذه الدالة تُشغّل L1-L4 على **المشروع كاملاً** (يكتشف العلاقات بين العقود)
- المخرجات مختلفة النوع: entities, relationships, fund_flows — ليست findings

**المدخلات** | `engines: Dict, project: Dict` |
**المخرجات** | `Dict` — إحصائيات الرسم البياني أو `{"error": str}` |
**وجهة النتائج** | → `all_results["state_extraction"]` → **JSON report** (قسم مستقل) |

---

### 14. `run_detectors()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 1074-1163 |
| **الملفات المُستدعاة** | `DetectorRunner.run()` ← `agl_security_tool/detectors/__init__.py` L329 و `SoliditySemanticParser.parse()` |
| **مَن يستدعيها** | `run_audit()` — الخطوة 6 |
| **طريقة عملها** | 1. يأخذ المكتبات فقط. 2. لكل مكتبة: يستخدم shared_parse (أو يحلل جديداً). 3. يُشغّل `runner.run(parsed)` — 22 كاشف. |

**لماذا المكتبات فقط؟** لأن العقود الرئيسية **تُفحص بالكواشف بالفعل** داخل `core.deep_scan()` → `_scan_file()` → Layer 4.

**الكواشف الـ 22:**
| المجموعة | العدد | أمثلة |
|---------|-------|-------|
| Reentrancy | 4 | REENTRANCY-ETH, READ-ONLY, CROSS-FUNCTION |
| Access Control | 4 | UNPROTECTED-WITHDRAW, TX-ORIGIN-AUTH |
| DeFi | 5 | FIRST-DEPOSITOR, ORACLE-MANIPULATION, FLASH-LOAN |
| Common | 6 | UNCHECKED-CALL, UNBOUNDED-LOOP, SHADOWED-STATE |
| Token | 3 | UNCHECKED-ERC20, FEE-ON-TRANSFER |

**المدخلات** | `engines: Dict, project: Dict, shared_parse: Dict` |
**المخرجات** | `List[Dict]` |
**وجهة النتائج** | → `all_results["detectors"]` → **unified_findings** عبر `deduplicate_cross_layer()` |

---

### 15. `run_exploit_reasoning()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 1164-1262 |
| **الملف المُستدعى** | `ExploitReasoningEngine.analyze()` ← `agl_security_tool/exploit_reasoning.py` L844 |
| **مَن يستدعيها** | `run_audit()` — الخطوة 7 |
| **طريقة عملها** | 1. يأخذ أعلى 10 عقود رئيسية. 2. يقرأ كود كل عقد. 3. يأخذ findings من deep_scan لهذا العقد. 4. يُشغّل `exploit.analyze(findings, source, path)`. |

**ما يفعله `analyze()` داخلياً (4 مراحل):**
```
PathExtractor(source)      → execution paths for each function
  ↓
ConstraintSolver(Z3)       → SAT/UNSAT لكل مسار
  ↓
InvariantChecker           → هل invariant مُخترَق؟
  ↓
ExploitAssembler           → exploit_proof {exploitable: bool, steps: [...], counterexample: str}
```

**لماذا يوجد مستويان من exploit reasoning:**
1. **داخل core.py** (`_run_exploit_reasoning` سطر 1310): يعمل لكل ملف ويحقن `exploit_proof` في findings → يرفع severity → يؤثر على unified_findings **مباشرة**
2. **في audit_pipeline** (هذه الدالة): يُعيد التشغيل على العقود الرئيسية ويُنتج proofs تُستخدم بواسطة **PoCGenerator**

**المدخلات** | `engines: Dict, project: Dict, deep_scan_results: Dict` |
**المخرجات** | `Dict[name, result]` — كل result يحتوي `exploit_proofs, exploitable_count` |
**وجهة النتائج** | → `all_results["exploit_reasoning"]` → **PoCGenerator** (خطوة 8.7) |

---

### 16. `extract_function_blocks()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 1263-1289 |
| **الملف المُستدعى** | لا يوجد — regex داخلي |
| **مَن يستدعيها** | `run_heikal_math()` |
| **طريقة عملها** | يستخدم regex `function\s+(\w+)\s*\(([^)]*)\)[^{]*\{` للعثور على بداية كل دالة، ثم يتبع الأقواس `{}` لالتقاط الجسم الكامل. |

**ملاحظة:** يستخدم regex وليس SoliditySemanticParser — لأن الحاجة هنا لاستخراج **نص الدالة الكامل** وليس الهيكل المُحلَّل وهذا غرض مختلف عن shared_parse.

**المدخلات** | `source: str` |
**المخرجات** | `Dict[str, str]` — `{function_name: full_function_body}` |

---

### 17. `analyze_function_security()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 1291-1539 |
| **الملف المُستدعى** | `SecurityBarrier` ← `agl_security_tool/heikal_math/tunneling_scorer.py` |
| **مَن يستدعيها** | `run_heikal_math()` |
| **طريقة عملها** | تحليل **250 سطر** يبني نموذجاً أمنياً من الكود المصدري: |

**ما يستخرجه:**
| الفحص | الطريقة |
|------|---------|
| عدد require | `_RE_REQUIRE.findall(func_body)` |
| استدعاءات خارجية | `_RE_EXTERNAL_CALL.findall(func_body)` |
| كتابات حالة | `_RE_STATE_WRITE.findall(func_body)` |
| حماية reentrancy | `"nonReentrant" in func_body` + `"_status"` + `"ReentrancyGuard"` |
| صلاحيات | `_RE_ACCESS_CHECK.search(func_body)` |
| انتهاك CEI | فحص ترتيب مواقع الاستدعاءات vs كتابات الحالة |
| oracle reads | كلمات مفتاحية: `oracle, TWAP, getPrice, latestAnswer` |
| delegatecall | `_RE_DELEGATECALL.search(func_body)` |
| إرسال ETH | `_RE_SEND_ETH.search(func_body)` |

**المخرجات (نموذج أمني لكل دالة):**
```python
{
    "barriers": [SecurityBarrier(type, height, thickness, source), ...],
    "wave_features": {moves_funds, cei_violation, sends_eth, ...},       # لـ WaveDomainEvaluator
    "holo_features": {complexity_ratio, protection_ratio, ...},          # لـ HolographicVulnerabilityMemory
    "energy": float,            # 0.0-1.0 طاقة الهجوم
    "chain_length": int,        # عدد الاستدعاءات الخارجية
    "description": str,
}
```

---

### 18. `build_attack_scenarios()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 1540-1910 |
| **الملف المُستدعى** | `SecurityBarrier` ← `tunneling_scorer.py` |
| **مَن يستدعيها** | `run_heikal_math()` |
| **طريقة عملها** | يبني حتى 7 سيناريوهات هجوم بناءً على الدوال المُكتشفة: |

| السيناريو | شرط التفعيل | الحواجز |
|----------|------------|---------|
| **Reentrancy Attack** | دوال تحرك أموال | guard عالي إذا nonReentrant، ضعيف إذا لا |
| **Flash Loan Attack** | flash أو swap موجود | fee + balance check + single-block |
| **Oracle Manipulation** | oracle reads | TWAP + multi-block + lag |
| **Sandwich/Frontrun** | swap أو mint | slippage + public mempool + fee |
| **Governance Takeover** | access control موجود | owner + no timelock |
| **JIT Liquidity** | mint + burn + swap كلهم | mempool + narrow range + instant withdraw |
| **Unguarded Fund Flow** | دوال بدون حماية تحرك أموال | guard ضعيف (bypassable) |

**المدخلات** | `functions_analysis: Dict, source_map: Dict` |
**المخرجات** | `Dict[scenario_name, {barriers, wave_features, holo_features, energy, chain_length}]` |

---

### 19. `run_heikal_math()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 1911-2219 |
| **الملفات المُستدعاة** | `tunneling_scorer.py`, `wave_evaluator.py`, `holographic_patterns.py`, `resonance_optimizer.py` + الدوال الداخلية أعلاه |
| **مَن يستدعيها** | `run_audit()` — الخطوة 8 (فقط في وضع `full` بدون `skip_heikal`) |
| **طريقة عملها** | **4 مراحل:** |

**المرحلة 1 — استخراج الدوال:**
```
لكل عقد (ما عدا iface/):
  source → extract_function_blocks() → func_blocks
  لكل دالة (ما عدا constructor, _, safe_funcs):
    analyze_function_security() → model أمني
```

**المرحلة 2 — بناء السيناريوهات:**
```
build_attack_scenarios(all_functions, source_map) → 7 سيناريوهات
```

**المرحلة 3 — تشغيل 4 خوارزميات على أخطر 50 دالة:**
```
لكل دالة (مرتبة بالخطورة ← energy):
  1. tunneling.compute(barriers, energy, chain)  → TunnelingResult
  2. wave.evaluate(wave_features)                 → WaveEvaluationResult
  3. holographic.match(holo_features)             → List[PatternMatch]
  4. resonance.optimize_amount(value, eval_fn)    → ResonanceOptimizationResult
  → severity = max(tunnel_confidence, wave_score) > 0.9 ? HIGH : ...
```

**المرحلة 4 — تشغيل 3 خوارزميات على سيناريوهات الهجوم:**
```
لكل سيناريو:
  1. tunneling.compute()
  2. wave.evaluate()
  3. holographic.match()
  → severity = max(confidence, wave_score) > 0.9 ? CRITICAL : ...
```

**المدخلات** | `engines: Dict, project: Dict, shared_parse: Dict` |
**المخرجات** | `{"functions": {key: results}, "attacks": {name: results}, "summary": {...}}` |
**وجهة النتائج** | → `all_results["heikal_math"]` → **قسم مستقل في التقرير** (جداول الدوال والسيناريوهات) |

---

### 20. `run_poc_generation()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 2220-2327 |
| **الملفات المُستدعاة** | `PoCGenerator` ← `agl_security_tool/poc_generator.py` L88 و `run_foundry_pocs()` ← نفس الملف L1429 |
| **مَن يستدعيها** | `run_audit()` — الخطوة 8.7 |
| **طريقة عملها** | 1. `PoCGenerator(project_path)` يُهيَّأ. 2. `generator.generate(all_results)` يأخذ **كل النتائج** (unified + exploit_proofs). 3. يُولّد ملفات `.t.sol` من 9 قوالب (reentrancy, access, oracle, flash_loan, etc.). 4. إذا `run_forge=True` → `run_foundry_pocs()` يُشغّل `forge test` على كل ملف PoC. |

**القوالب الـ 9:**
| القالب | الثغرة | الملف |
|-------|--------|------|
| `_poc_reentrancy()` | reentrancy مع `receive()` callback | `Test_Reentrancy_*.t.sol` |
| `_poc_access_control()` | bypass صلاحيات | `Test_AccessControl_*.t.sol` |
| `_poc_oracle_manipulation()` | MockOracle مع أسعار مُتلاعب بها | `Test_Oracle_*.t.sol` |
| `_poc_oracle_stale()` | `vm.warp()` تقدم الوقت | `Test_StaleOracle_*.t.sol` |
| `_poc_flash_loan()` | flash loan callback | `Test_FlashLoan_*.t.sol` |
| `_poc_tx_origin()` | phishing relay | `Test_TxOrigin_*.t.sol` |
| `_poc_unchecked_call()` | CallRejecter | `Test_UncheckedCall_*.t.sol` |
| `_poc_first_depositor()` | share inflation | `Test_FirstDepositor_*.t.sol` |
| `_poc_generic()` | fallback عام | `Test_Generic_*.t.sol` |

**المدخلات** | `all_results: Dict, project: Dict, run_forge: bool` |
**المخرجات** | `{"poc_generation": {poc_files, count, skipped}, "foundry_results": {...} | None}` |

---

### 21. `generate_final_report()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 2328-2481 |
| **الملف المُستدعى** | لا يوجد — تجميع داخلي |
| **مَن يستدعيها** | `run_audit()` — الخطوة 9 |
| **طريقة عملها** | 1. يجمع كل النتائج في قاموس واحد. 2. يستخدم `unified_findings` لحساب severity (أو fallback من الطبقات الفردية). 3. يطبع صندوق ملخص بصري يشمل: الهدف، النوع، الملفات، الوقت، severity، dedup stats، طبقات مُنفَّذة، أخطر نتائج Heikal. |

**هيكل التقرير:**
```python
{
    "audit_name": str,
    "timestamp": str,
    "target": str,
    "project_type": str,
    "contracts_scanned": int,
    "audit_time_seconds": float,
    "total_findings": int,
    "severity_total": {"CRITICAL": N, "HIGH": N, ...},
    "dedup_stats": {...},
    "heikal_analyses": int,
    "poc_generated": int,
    "foundry_passed": int,
    "foundry_failed": int,
    "results": {                    # كل النتائج الخام
        "deep_scan": {...},
        "z3_symbolic": [...],
        "state_extraction": {...},
        "detectors": [...],
        "exploit_reasoning": {...},
        "heikal_math": {...},
        "unified_findings": [...],
        "poc_generation": {...},
        "foundry_results": {...},
    }
}
```

---

### 22. `generate_markdown_report()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 2482-2586 |
| **الملف المُستدعى** | لا يوجد — تنسيق نصي |
| **مَن يستدعيها** | `run_audit()` (إذا `output_format == "markdown"`) |
| **طريقة عملها** | يُحوّل `report` dict إلى Markdown: عنوان، جدول severity، جداول Heikal (سيناريوهات + دوال)، نتائج deep_scan مختصرة. |
| **المخرجات** | `str` — نص Markdown جاهز للحفظ كملف `.md` |

---

### 23. `run_audit()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 2587-2810 |
| **المكوّنات المُستدعاة** | كل الدوال أعلاه بالترتيب |
| **مَن يستدعيها** | `main()` أو أي كود خارجي |
| **طريقة عملها** | **11 خطوة بالترتيب** مع `try/finally` لتنظيف المجلدات المؤقتة: |

```
Step 0:   resolve_target()           → project_path
Step 1:   load_engines()             → engines dict (11 مكون)
Step 2:   discover_project()         → project dict
Step 2.5: run_shared_parsing()       → shared_parse
Step 3:   run_core_deep_scan()       → deep_scan results         [full/deep فقط]
Step 4:   run_z3_symbolic()          → z3 library results        [full/deep فقط]
Step 5:   run_state_extraction()     → project-wide state        [full فقط]
Step 6:   run_detectors()            → detector library results
Step 7:   run_exploit_reasoning()    → exploit proofs            [full/deep فقط]
Step 8:   run_heikal_math()          → heikal analyses           [full فقط, بدون skip_heikal]
Step 8.5: deduplicate_cross_layer()  → unified_findings
Step 8.7: run_poc_generation()       → PoC files + foundry       [full/deep فقط]
Step 9:   generate_final_report()    → report dict
Step 10:  حفظ الملف (JSON أو Markdown)
```

**الأوضاع:**
| الوضع | الطبقات | الوقت التقريبي |
|------|---------|---------------|
| `full` | كل الطبقات (0-8.7) | بطيء |
| `deep` | بدون state_extraction وبدون heikal_math | متوسط |
| `quick` | deep_scan و state_extraction ملغيان | سريع |

**المدخلات** | 12 معامل (target, branch, mode, skip_heikal, include_deps, ...) |
**المخرجات** | `Dict` — التقرير النهائي الكامل |

---

### 24. `main()`

| الحقل | القيمة |
|-------|--------|
| **السطر** | 2811-2930 |
| **الملف المُستدعى** | `run_audit()` |
| **مَن يستدعيها** | `if __name__ == "__main__"` أو نقطة دخول `agl-audit` |
| **طريقة عملها** | `argparse` CLI كامل يقبل: |

```bash
python audit_pipeline.py <target>                              # أساسي
python audit_pipeline.py <target> --mode deep                  # بدون heikal
python audit_pipeline.py <target> --mode quick                 # أنماط فقط
python audit_pipeline.py <target> --skip-heikal                # تخطي Layer 7
python audit_pipeline.py <target> --include-deps               # فحص node_modules/lib
python audit_pipeline.py <target> --include-tests              # فحص ملفات test
python audit_pipeline.py <target> --format markdown -o report.md
python audit_pipeline.py <target> --no-poc                     # بدون PoC
python audit_pipeline.py <target> --run-poc                    # تشغيل forge test
python audit_pipeline.py https://github.com/user/repo          # GitHub مباشر
python audit_pipeline.py https://github.com/user/repo -b main  # فرع محدد
```

---

## ملخص تدفق البيانات

```
                    ┌────────────────────────────────────┐
                    │         run_audit() — 11 خطوات     │
                    └────────────┬───────────────────────┘
                                 │
         ┌───────────────────────┼─────────────────────────────┐
         ▼                       ▼                             ▼
   load_engines()        discover_project()          run_shared_parsing()
   (11 محرك)             (تصنيف .sol)                (parse مرة واحدة)
         │                       │                             │
         │              ┌────────┴────────┐                    │
         │              ▼                 ▼                    │
         │        main_contracts    libraries                  │
         │              │                 │                    │
         ▼              ▼                 ▼                    │
   ┌─────────────────────────┐  ┌──────────────────┐          │
   │ run_core_deep_scan()    │  │ run_z3_symbolic() │ ← ──────┤
   │ ← core.deep_scan()     │  │ (مكتبات فقط)      │          │
   │   يحتوي داخلياً:        │  └────────┬─────────┘          │
   │   L0: Flattener         │           │                    │
   │   L0.5: Z3              │  ┌──────────────────┐          │
   │   L1: Pattern/CFG       │  │ run_detectors()   │ ← ──────┘
   │   L2: Slither/Mythril   │  │ (مكتبات فقط)      │
   │   L2: 22 Detectors      │  └────────┬─────────┘
   │   L1-L4: State/Action/  │           │
   │     Attack/Search       │           │
   │   L5: ExploitReasoning  │           │
   │   Dedup + RiskCore      │           │
   └─────────┬───────────────┘           │
             │                            │
             ▼                            ▼
   ┌─────────────────────────────────────────────────┐
   │        deduplicate_cross_layer()                 │
   │  يجمع: deep_scan + z3_libs + detector_libs      │
   │  يزيل: تكرارات + دوال آمنة                      │
   │  يُنتج: unified_findings + severity_unified     │
   └──────────────────────┬──────────────────────────┘
                          │
         ┌────────────────┼─────────────────┐
         ▼                ▼                 ▼
   run_state_extraction() run_exploit_reasoning() run_heikal_math()
   (مشروع كامل)         (proofs لـ PoC)        (4 خوارزميات)
   → JSON report         → run_poc_generation() → report section
                               │
                               ▼
                    generate_final_report()
                    ← JSON / Markdown
```

---

## ملاحظات مهمة

### 1. "تكرار" مقصود وليس خطأ
- **Z3**: يعمل داخل deep_scan (main) + مرة أخرى هنا (libs) → لا تكرار
- **Detectors**: يعمل داخل deep_scan (main) + مرة أخرى هنا (libs) → لا تكرار  
- **State Extraction**: يعمل داخل deep_scan (per-file) + هنا (project-wide) → مكمّل
- **Exploit Reasoning**: يعمل داخل core.py (per-file) + هنا (for PoC gen) → مكمّل

### 2. shared_parse يُقلل التكرار
`run_shared_parsing()` يحلل كل الملفات **مرة واحدة** بـ SoliditySemanticParser. النتائج تُشارك مع: `run_z3_symbolic()`, `run_detectors()`, `run_heikal_math()`. بدون هذا، كل طبقة كانت ستقرأ وتحلل كل ملف من جديد.

### 3. Heikal يستخدم regex لأن حاجته مختلفة
`extract_function_blocks()` يحتاج **نص الدالة الكامل** (لحساب require count, external calls, etc). SoliditySemanticParser يستخرج **هيكل** (operations, visibility) — لا يُرجع نص الجسم الكامل.
