# 🛡️ AGL Security Tool — دليل التشغيل وتدفق البيانات الكامل

> **الإصدار:** 2.1.0  
> **آخر تحديث:** مارس 2026  
> **المؤلف:** AGL Team

---

## 📑 فهرس المحتويات

1. [نظرة عامة](#1-نظرة-عامة)
1.1. [التبعيات الخارجية — External Dependencies](#11-external-dependencies--التبعيات-الخارجية)
2. [هيكل الملفات](#2-هيكل-الملفات)
3. [طرق التشغيل الثلاث](#3-طرق-التشغيل-الثلاث)
4. [خط أنابيب التحليل — الطبقات الثمان](#4-خط-أنابيب-التحليل--الطبقات-الثمان)
5. [تدفق البيانات خطوة بخطوة](#5-تدفق-البيانات-خطوة-بخطوة)
6. [الطبقة 1: محلل العقود الذكية](#6-الطبقة-1-محلل-العقود-الذكية)
7. [الطبقة 2: منسق الأمان](#7-الطبقة-2-منسق-الأمان)
8. [الطبقة 4: الكاشفات الدلالية (22 كاشف)](#8-الطبقة-4-الكاشفات-الدلالية-22-كاشف)
9. [الطبقة 5: إثبات الاستغلال](#9-الطبقة-5-إثبات-الاستغلال)
10. [إزالة التكرارات وتعزيز الثقة](#10-إزالة-التكرارات-وتعزيز-الثقة)
11. [الطبقة 6: إثراء بالنموذج اللغوي](#11-الطبقة-6-إثراء-بالنموذج-اللغوي)
12. [هيكل البيانات المُخرَجة](#12-هيكل-البيانات-المُخرَجة)
13. [فحص المشاريع الكاملة](#13-فحص-المشاريع-الكاملة)
14. [جسر VS Code](#14-جسر-vs-code)
15. [أمثلة عملية](#15-أمثلة-عملية)

---

## 1. نظرة عامة

AGL Security Tool هي أداة تحليل أمان للعقود الذكية (Solidity) تعمل عبر **8 طبقات متتالية** (Layer 0-7)، كل طبقة تضيف عمقاً للتحليل:

```
┌────────────────────────────────────────────────────────────────────┐
│                     ملف .sol  (المدخل)                             │
└────────────┬───────────────────────────────────────────────────────┘
             ▼
┌────────────────────────────────────────────────────────────────────┐
│  الطبقة 0: SolidityFlattener + Z3SymbolicEngine                   │
│  (تسطيح الاستيرادات + 8 فحوصات رمزية Z3 SMT)                      │
│  المخرج: merged_source + symbolic_findings[]                       │
└────────────┬───────────────────────────────────────────────────────┘
             ▼
┌────────────────────────────────────────────────────────────────────┐
│  الطبقة 1: SmartContractAnalyzer + SecurityOrchestrator            │
│  (Lexer + Regex + CFG + Taint + Slither + Mythril + Semgrep)       │
│  المخرج: findings[] + suite_findings[]                             │
└────────────┬───────────────────────────────────────────────────────┘
             ▼
┌────────────────────────────────────────────────────────────────────┐
│  الطبقة 1-4: State Extraction → Action Space → Attack Sim → Search │
│  (استخراج حالة مالية → فضاء أفعال → محاكاة هجمات → بحث ذكي)       │
│  المخرج: state_graph + action_space + attacks + search_results     │
└────────────┬───────────────────────────────────────────────────────┘
             ▼
┌────────────────────────────────────────────────────────────────────┐
│  الطبقة 5: AGL Semantic Detectors (22 كاشف)                        │
│  (Reentrancy×5 + Access×5 + DeFi×4 + Common×4 + Token×4)          │
│  المخرج: detector_findings[]                                       │
└────────────┬───────────────────────────────────────────────────────┘
             ▼
┌────────────────────────────────────────────────────────────────────┐
│  الطبقة 6: Exploit Reasoning — إثبات الاستغلال                     │
│  (PathExtractor → Z3 SAT → InvariantChecker → ExploitAssembler)    │
│  المخرج: exploit_proofs[] (مرفقة بال findings)                     │
└────────────┬───────────────────────────────────────────────────────┘
             ▼
┌────────────────────────────────────────────────────────────────────┐
│  الطبقة 7: Heikal Math — خوارزميات الفيزياء                        │
│  (نفق كمومي + موجة + هولوغرام FFT + رنين)                          │
│  المخرج: tunneling_confidence + wave_score + holo_matches          │
└────────────┬───────────────────────────────────────────────────────┘
             ▼
┌────────────────────────────────────────────────────────────────────┐
│  إزالة التكرارات + RiskCore P(exploit) + Negative Evidence         │
│  المخرج: all_findings_unified[] + severity_summary                 │
└────────────┬───────────────────────────────────────────────────────┘
             ▼
┌────────────────────────────────────────────────────────────────────┐
│  PoC Generation + LLM Enrichment (Ollama / HolographicLLM)        │
│  (Foundry .t.sol + شرح + إصلاح لكل CRITICAL/HIGH)                 │
│  المخرج: poc_files[] + llm_explanation + fix                       │
└────────────┬───────────────────────────────────────────────────────┘
             ▼
┌────────────────────────────────────────────────────────────────────┐
│                   النتيجة النهائية (Dict)                           │
│  all_findings_unified, severity_summary, exploit_reasoning,        │
│  heikal_math, poc_files, layers_used, time_seconds                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## 1.1 External Dependencies — التبعيات الخارجية

### Required Packages — الحزم المطلوبة
| الحزمة | الإصدار | الغرض |
|--------|---------|-------|
| `requests` | >= 2.28.0 | اتصالات HTTP مع الواجهات الخارجية |
| `z3-solver` | >= 4.12.0 | محرك التنفيذ الرمزي Z3 SMT |

### Optional Packages — حزم اختيارية (تعزز النتائج)
| الحزمة | الغرض |
|--------|-------|
| `slither-analyzer` | تحليل ثابت عبر Slither |
| `mythril` | تنفيذ رمزي عبر EVM |
| `semgrep` | فحص بقواعد Semgrep |
| `numpy` | تسريع FFT في الذاكرة الهولوغرامية (Layer 7) |

### External AGL Engines — محركات AGL الخارجية (اختيارية بالكامل)

> **مهم:** الأداة تعمل **مستقلة 100%** بدون هذه المحركات. كل الاستيرادات في `core.py` محمية بـ `try/except`.

> **Important:** This tool works **100% standalone** without these engines. All imports in `core.py` are wrapped in `try/except`.

عند توفر مشروع AGL الكامل، يستورد `core.py` (السطور 79–115) أربعة محركات اختيارية:

| المحرك | مسار الاستيراد | الغرض |
|--------|----------------|-------|
| `SmartContractAnalyzer` | `agl.engines.smart_contract_analyzer` | Lexer + CFG + Taint + 8 أنماط (الطبقة 1) |
| `AGLSecuritySuite` | `agl.engines.agl_security` | Slither/Mythril wrapper (الطبقة 2) |
| `AGLSecurityOrchestrator` | `agl.engines.security_orchestrator` | تنسيق التحليل بالتوازي (الطبقة 2+) |
| `OffensiveSecurityEngine` | `agl.engines.offensive_security` | خط أنابيب الهجوم الكامل (الطبقة 3) |

هذه المحركات موجودة في `AGL_NextGen/src/agl/engines/`. إذا لم تتوفر، تعمل الأداة بمحركاتها الداخلية:
- `state_extraction/` بدلاً من `SmartContractAnalyzer`
- `detectors/` (22 كاشف) بدلاً من `AGLSecuritySuite`
- `attack_engine/` + `search_engine/` بدلاً من `OffensiveSecurityEngine`

---

## 2. هيكل الملفات

```
agl_security_tool/
├── __init__.py                  # يصدّر AGLSecurityAudit + ProjectScanner
├── __main__.py                  # نقطة الدخول CLI (python -m agl_security_tool)
├── core.py                      # ★ النواة — يربط كل الطبقات ويدير خط الأنابيب
├── exploit_reasoning.py         # ★ طبقة إثبات الاستغلال (4 وحدات + Z3)
├── project_scanner.py           # ماسح المشاريع الكاملة (Foundry/Hardhat/Truffle)
├── vscode_bridge.py             # جسر JSON لإضافة VS Code
└── detectors/                   # 22 كاشف دلالي
    ├── __init__.py              # BaseDetector + DetectorRunner + Finding + ParsedContract
    ├── solidity_parser.py       # محلل دلالي → ParsedContract
    ├── reentrancy.py            # 4 كاشفات: ETH, NoETH, ReadOnly, CrossFunction
    ├── access_control.py        # 4 كاشفات: Withdraw, SelfDestruct, TxOrigin, Delegatecall
    ├── defi.py                  # 5 كاشفات: FirstDepositor, Oracle, PriceStale, DivideB4Multiply, FlashLoan
    ├── common.py                # 6 كاشفات: UncheckedCall, UnboundedLoop, DuplicateCond, Shadow, EncodePacked, Event
    └── token.py                 # 3 كاشفات: UncheckedERC20, ArbitrarySend, FeeOnTransfer

المحركات الخارجية (AGL_NextGen/src/agl/engines/):
├── smart_contract_analyzer.py   # 2565 سطر — Lexer + CFG + 8 أنماط + AdvancedAnalysis
├── security_orchestrator.py     # 1105 سطر — Slither/Mythril/Semgrep/Z3/LLM بالتوازي
├── agl_security.py              # ~700 سطر — AGLSecuritySuite (بديل احتياطي)
├── offensive_security.py        # 1839 سطر — HolographicLLM + Z3 + EVM + Logic Gates
└── formal_verifier.py           # 1086 سطر — Z3 SMT Solver + 8 ثوابت DeFi
```

---

## 3. طرق التشغيل الثلاث

### 3.1 سطر الأوامر (CLI)

```bash
# المتطلبات
pip install -r requirements.txt   # يشمل z3-solver

# فحص قياسي — كل الطبقات
python -m agl_security_tool scan contract.sol

# فحص سريع — أنماط regex فقط (ثوانٍ)
python -m agl_security_tool quick contract.sol

# فحص عميق — كل الطبقات + Z3 + EVM + LLM
python -m agl_security_tool deep contract.sol

# فحص مجلد كامل
python -m agl_security_tool scan contracts/ --recursive

# فحص مشروع Foundry/Hardhat كامل
python -m agl_security_tool project ./my-defi-project
python -m agl_security_tool project ./my-defi-project -m deep -f markdown -o report.md

# معلومات المشروع بدون فحص
python -m agl_security_tool info ./my-project

# شجرة التبعيات
python -m agl_security_tool graph ./my-project -o deps.json

# اختيار تنسيق الإخراج
python -m agl_security_tool scan contract.sol -f json       # JSON
python -m agl_security_tool scan contract.sol -f markdown   # Markdown
python -m agl_security_tool scan contract.sol -f text       # نص عادي (افتراضي)

# حفظ في ملف
python -m agl_security_tool scan contract.sol -f markdown -o report.md
```

**أكواد الخروج (Exit Codes):**
| Code | المعنى |
|------|--------|
| `0`  | لا ثغرات خطيرة |
| `1`  | يوجد HIGH findings |
| `2`  | يوجد CRITICAL findings |

### 3.2 استدعاء من Python (API)

```python
from agl_security_tool import AGLSecurityAudit

# إنشاء المحرك (يحمّل كل الطبقات تلقائياً)
audit = AGLSecurityAudit()

# فحص قياسي
result = audit.scan("contract.sol")

# فحص سريع
result = audit.quick_scan("contract.sol")

# فحص عميق
result = audit.deep_scan("contract.sol")

# فحص مجلد
result = audit.scan("contracts/", recursive=True)

# فحص مشروع كامل
result = audit.scan_project("./my-project", mode="deep", output_format="markdown")

# إعدادات مخصصة
audit = AGLSecurityAudit({
    "skip_llm": True,              # تخطي النموذج اللغوي
    "mythril_timeout": 120,        # مهلة Mythril بالثواني
    "generate_poc": True,          # توليد PoC
    "suite": {
        "severity_filter": ["critical", "high"],
        "confidence_threshold": 0.7,
    }
})
result = audit.scan("contract.sol")

# توليد تقرير
report = audit.generate_report(result, format="markdown")
print(report)
```

### 3.3 إضافة VS Code (عبر vscode_bridge.py)

الإضافة ترسل أوامر JSON عبر stdin وتستقبل JSON عبر stdout:

```json
// فحص ملف
{"action": "scan_file", "target": "contract.sol", "mode": "scan"}

// فحص مشروع كامل
{"action": "scan_project", "target": "/path/to/project", "mode": "deep", "config": {}}

// اكتشاف بنية المشروع
{"action": "discover", "target": "/path/to/project"}

// فحص الأدوات المتاحة
{"action": "check"}
```

---

## 4. خط أنابيب التحليل — الطبقات الثمان

عند استدعاء `audit.scan("contract.sol")`، تحدث السلسلة التالية بالضبط:

```
scan("contract.sol")
  │
  ├─ Path.resolve() → مسار مطلق
  ├─ os.path.isfile? → _scan_file(path)
  │
  └─ _scan_file(path):
      │
      ├── combined = {} ← القاموس الرئيسي (يُملأ تدريجياً)
      │
      ├── [1] الطبقة 1: self._analyzer.analyze(code)
      │   └── → combined["findings"], ["contracts"], ["functions"]
      │
      ├── [2] الطبقة 2: self._orchestrator.analyze_file(path)
      │   └── → combined["suite_findings"]
      │   └── (احتياطي: self._suite.scan_file(path))
      │
      ├── [3] الطبقة 4: self._detector_runner.run(contracts)
      │   └── → combined["detector_findings"]
      │
      ├── [4] الطبقة 5: self._run_exploit_reasoning(combined, path)
      │   └── → combined["exploit_reasoning"]
      │   └── يُلحق exploit_proof بكل finding مُثبتة
      │   └── يرفع severity إلى CRITICAL للثغرات المُثبتة
      │
      ├── [5] الدمج: self._deduplicate_and_cross_validate(combined)
      │   └── → combined["all_findings_unified"]
      │   └── → combined["severity_summary"]
      │   └── → combined["duplicates_removed"]
      │
      ├── [6] الطبقة 6: self._llm_enrich_findings(combined, path)
      │   └── → llm_explanation, fix, poc لكل CRITICAL/HIGH
      │
      └── return combined
```

---

## 5. تدفق البيانات خطوة بخطوة

### الخطوة 0: التهيئة (`__init__`)

```python
audit = AGLSecurityAudit()
```

تحدث التهيئة التالية في `_init_engines()`:

| الترتيب | ما يُحمَّل | النجاح/الفشل | السلوك عند الفشل |
|---------|-----------|------------|----------------|
| 1 | `SmartContractAnalyzer` | ✅ دائماً | — |
| 2 | `AGLSecuritySuite` | ✅ دائماً | — |
| 3 | `AGLSecurityOrchestrator` | ✅ (Z3 مطلوب) | تخطي |
| 4 | `OffensiveSecurityEngine` | ✅ دائماً | تخطي |
| 5 | `DetectorRunner + SoliditySemanticParser` | ✅ دائماً | تخطي |

> **ملاحظة مهمة:** كل محرك يُحمَّل داخل `try/except`. إذا فشل أي محرك، يتم تجاوزه بصمت ويستمر التحليل بالمحركات المتاحة.

### الخطوة 1: قراءة الملف

```python
with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    code = f.read()
```

الكود الخام (`str`) يُقرأ مرة ويُمرَّر لعدة طبقات.

### الخطوة 2: الطبقة 1 — `SmartContractAnalyzer.analyze(code)`

**المدخل:** نص Solidity خام  
**المخرج:**
```python
{
    "findings": [                    # قائمة الثغرات المكتشفة
        {
            "title": "Reentrancy Vulnerability",
            "severity": "high",
            "line": 18,
            "description": "..."
        }
    ],
    "contracts": ["VulnerableBank"],  # أسماء العقود
    "functions": ["withdraw", "..."], # أسماء الدوال
    "warnings": [],                   # تحذيرات
    "advanced_analysis": True         # هل CFG عمل؟
}
```

**ما يحدث داخلياً:**
1. **Lexer** — يقسم الكود لرموز (tokens)
2. **Regex Patterns** — 8 أنماط أساسية (reentrancy, overflow, tx.origin, ...)
3. **CFG Builder** — يبني `CFGNode` graph لكل دالة:
   - كل node يحتوي: `external_calls`, `state_writes`, `state_reads`
   - BFS على CFG: هل يوجد `external_call` قبل `state_write`؟
4. **Taint Analysis** — يتتبع انتقال بيانات المستخدم

### الخطوة 3: الطبقة 2 — `AGLSecurityOrchestrator.analyze_file(path)`

**المدخل:** مسار ملف  
**المخرج:** قائمة `Finding` objects  

**ما يحدث داخلياً (بالتوازي عبر ThreadPoolExecutor):**

| Backend | ما يفعل | المخرج |
|---------|---------|--------|
| Slither | تحليل AST + CFG + 80+ كاشف | findings |
| Mythril | تنفيذ رمزي symbolic execution | findings |
| Semgrep | مطابقة أنماط | findings |
| Z3 | تحقق رياضي رسمي | findings |
| LLM | تحليل بالنموذج اللغوي | findings |

> ⚠️ Slither/Mythril/Semgrep تتطلب تثبيتاً منفصلاً. إذا لم تكن مثبتة، يعمل Z3 + LLM فقط.

**تحويل المخرج:** كل `Finding` object يُحوَّل لقاموس:
```python
{
    "id": "z3-reentrancy-001",
    "title": "Reentrancy in withdraw()",
    "severity": "high",           # من Severity enum
    "category": "reentrancy",     # من VulnCategory enum
    "line": 18,
    "description": "...",
    "confidence": 0.85,
    "source": "z3",
    "recommendation": "...",
    "poc": "..."
}
```

**الاحتياطي:** إذا فشل المنسق، تعمل `AGLSecuritySuite` كبديل (نفس الأدوات لكن بدون توازي).

### الخطوة 4: الطبقة 4 — 22 كاشف دلالي

**المدخل:** نص Solidity خام  
**المعالجة على مرحلتين:**

**المرحلة أ: التحليل الدلالي — `SoliditySemanticParser.parse(code, path)`**

يحوّل الكود إلى `ParsedContract` objects:
```python
ParsedContract:
    name: str                           # "VulnerableBank"
    contract_type: str                  # "contract" / "interface" / "library"
    file_path: str
    inherits: List[str]                 # ["Ownable", "ReentrancyGuard"]
    state_variables: List[StateVar]     # كل متغير حالة مع نوعه
    functions: List[ParsedFunction]     # كل دالة بالتفصيل
    modifiers: List[Modifier]
    events: List[Event]
```

كل `ParsedFunction` يحتوي:
```python
ParsedFunction:
    name: str                           # "withdraw"
    visibility: str                     # "external" / "public" / "internal" / "private"
    modifiers: List[str]                # ["nonReentrant", "onlyOwner"]
    parameters: List[Parameter]
    operations: List[Operation]         # ★ قائمة مرتبة بالعمليات
    raw_body: str                       # جسم الدالة الخام
```

كل `Operation` مصنَّف:
```python
Operation:
    op_type: OpType     # STATE_READ / STATE_WRITE / EXTERNAL_CALL / REQUIRE / ...
    line: int
    raw: str            # السطر الخام
    target: str         # الهدف (مثلاً "balances[msg.sender]")
    value: str          # القيمة
```

**المرحلة ب: تشغيل الكاشفات — `DetectorRunner.run(contracts)`**

```
لكل كاشف (22 كاشف):
    لكل عقد (غير interface):
        findings = detector.detect(contract, all_contracts)
```

**قائمة الكاشفات الـ22:**

| # | الكاشف | الخطورة | ماذا يبحث عن |
|---|--------|---------|-------------|
| 1 | `ReentrancyETH` | CRITICAL | external call مع ETH قبل state update |
| 2 | `ReentrancyNoETH` | HIGH | external call بدون ETH قبل state update |
| 3 | `ReentrancyReadOnly` | HIGH | view function تُقرأ أثناء reentrancy |
| 4 | `ReentrancyCrossFunction` | HIGH | reentrancy عبر دالتين مختلفتين |
| 5 | `UnprotectedWithdraw` | CRITICAL | سحب بدون modifier حماية |
| 6 | `UnprotectedSelfDestruct` | CRITICAL | selfdestruct بدون حماية |
| 7 | `TxOriginAuth` | HIGH | توثيق بـ tx.origin بدل msg.sender |
| 8 | `DangerousDelegatecall` | CRITICAL | delegatecall لعنوان متغير |
| 9 | `FirstDepositorAttack` | HIGH | هجوم أول مودِع في vault |
| 10 | `OracleManipulation` | HIGH | تلاعب بأسعار Oracle |
| 11 | `PriceStaleCheck` | MEDIUM | عدم فحص حداثة السعر |
| 12 | `DivideBeforeMultiply` | MEDIUM | قسمة قبل ضرب (خسارة دقة) |
| 13 | `FlashLoanCallbackValidation` | HIGH | عدم التحقق من callback القرض السريع |
| 14 | `UncheckedLowLevelCall` | HIGH | .call() بدون فحص القيمة الراجعة |
| 15 | `UnboundedLoop` | MEDIUM | حلقة بطول غير محدود (DoS) |
| 16 | `DuplicateCondition` | LOW | شرط مكرر في if |
| 17 | `ShadowedStateVariable` | MEDIUM | متغير يُخفي متغير حالة |
| 18 | `EncodePacked` | MEDIUM | abi.encodePacked مع أنواع متغيرة الطول |
| 19 | `MissingEventEmission` | LOW | تغيير حالة بدون emit event |
| 20 | `UncheckedERC20Transfer` | HIGH | transfer() بدون فحص النجاح |
| 21 | `ArbitrarySendERC20` | HIGH | إرسال tokens لعنوان يتحكم فيه المستخدم |
| 22 | `FeeOnTransferToken` | MEDIUM | عدم دعم tokens مع رسوم تحويل |

**المخرج:** قائمة `Finding`:
```python
Finding:
    detector_id: str        # "reentrancy-eth"
    title: str              # "Reentrancy vulnerability with ETH transfer"
    severity: Severity      # CRITICAL
    confidence: Confidence  # HIGH
    line: int               # 18
    end_line: int           # 22
    description: str        # شرح تفصيلي
    recommendation: str     # اقتراح الإصلاح
    contract_name: str      # "VulnerableBank"
    function_name: str      # "withdraw"
```

### الخطوة 5: الطبقة 5 — إثبات الاستغلال (`ExploitReasoningEngine`)

> **السؤال الذي تجيب عنه هذه الطبقة:**  
> ليس "هل هناك ثغرة؟" — بل: **"هل يمكن سرقة مال فعلاً؟ وكيف؟"**

**المدخل:**
- كل findings من الطبقات الثلاث السابقة (مجمّعة)
- الكود المصدري الكامل

**الفلترة:** تُحلَّل فقط الثغرات `CRITICAL` و `HIGH`.

**4 وحدات متتالية:**

#### الوحدة 1: PathExtractor — استخراج المسارات

```
جسم الدالة → تصنيف كل سطر → مسار تنفيذ مرتب
```

كل سطر يُصنَّف:
| التصنيف | المثال |
|---------|--------|
| `require` | `require(balances[msg.sender] >= amount)` |
| `external_call` | `msg.sender.call{value: amount}("")` |
| `state_write` | `balances[msg.sender] -= amount` |
| `state_read` | (ضمني في require) |

**المخرج:** `ExecutionPath` مع أعلام:
```python
ExecutionPath:
    function: "withdraw"
    steps: [require, external_call, state_write]
    has_external_call: True
    has_state_write_after_call: True   # ★ خطر!
    has_guard: False                   # لا nonReentrant
```

#### الوحدة 2: ConstraintSolver — التحقق بـ Z3

```
مسار التنفيذ → شروط Z3 → SAT / UNSAT
```

يُنشئ متغيرات رمزية 256-bit (مثل Solidity):
```
balance_sender: BitVec(256)    — رصيد المهاجم
amount: BitVec(256)            — المبلغ المسحوب
contract_balance: BitVec(256)  — رصيد العقد
caller: BitVec(160)            — عنوان المُستدعي
owner: BitVec(160)             — عنوان المالك
```

يُضيف شروطاً حسب المسار:
```
require(balance >= amount)  →  solver.add(balance_sender >= amount)
external_call + state_write_after  →  solver.add(withdraw1 + withdraw2 > balance_sender)
tx.origin == owner  →  solver.add(tx_origin == owner, caller != owner)
```

**القيود الواقعية:**
- `0 < amount < 10,000 ETH`
- `0 < contract_balance < 10,000 ETH`
- حد زمني: 10 ثوانٍ

**المخرج:**
```python
("SAT", {"amount": "221720000000000000000", "balance_sender": "350000...", ...})
#  أو
("UNSAT", {})   # المسار مستحيل — الثغرة نظرية فقط
```

#### الوحدة 3: InvariantChecker — فحص الثوابت الاقتصادية

6 ثوابت اقتصادية مُشفَّرة يدوياً:

| الثابت | القاعدة | متى ينكسر |
|--------|---------|----------|
| `balance_conservation` | الرصيد بعد ≥ الرصيد قبل − السحب | reentrancy بدون guard |
| `reentrancy_no_double_spend` | لا يمكن سحب نفس المبلغ مرتين | external_call قبل state_write |
| `no_free_money` | لا يمكن استخراج أكثر مما أُودع | unchecked call |
| `access_gated` | العمليات الحساسة تتطلب msg.sender == owner | tx.origin auth |
| `total_supply_constant` | totalSupply ثابت (إلا mint/burn) | — |
| `sum_balances_le_contract` | مجموع أرصدة المستخدمين ≤ رصيد العقد | — |

**المخرج:** قائمة `InvariantViolation`:
```python
InvariantViolation:
    invariant: "balance_conservation"
    description: "External call before state update allows re-entering..."
    pre_value: "balances[attacker] = deposit_amount"
    post_value: "balances[attacker] = deposit_amount (unchanged during reentry)"
    delta: "attacker extracts N * deposit_amount"
    violated: True
```

#### الوحدة 4: ExploitAssembler — تجميع الهجوم

يأخذ: مسار + نتيجة Z3 + ثابت مكسور → يُنتج خطوات هجوم كاملة.

**مثال — reentrancy:**
```
1. Attacker deploys malicious contract with receive()/fallback()
2. Attacker deposits 221.72 ETH → withdraw() records balance
3. Attacker calls withdraw()
4. Contract sends 221.72 ETH via .call{value} BEFORE updating state
5. Attacker's receive() re-enters withdraw()
6. require(balances[attacker] >= amount) PASSES — balance not yet decremented
7. Contract sends 221.72 ETH AGAIN
8. State finally updates — but attacker already received 2x
9. INVARIANT BROKEN: balance_after < balance_before - withdraw_amount
10. Repeat steps 5-8 to drain entire contract
```

**حساب الثقة:**
| العامل | الوزن |
|--------|-------|
| Z3 SAT | +40% |
| ثابت مكسور | +30% |
| خطوات هجوم | +15% |
| مسار قابل للتنفيذ | +10% |
| قيم ملموسة (counterexample) | +5% |
| **المجموع (أقصى)** | **100%** |

**الحكم النهائي:**
```
EXPLOITABLE   → Z3 SAT + ثابت مكسور
LIKELY EXPLOITABLE → Z3 SAT بدون ثابت واضح
SUSPICIOUS    → ثابت مكسور لكن Z3 لم يؤكد
LOW RISK      → لا مسار قابل للاستغلال
```

**إلحاق الإثبات بالنتائج:**
بعد تجميع كل الإثباتات، تعود للنتائج وتُلحق `exploit_proof` بكل finding:
```python
finding["exploit_proof"] = proof.to_dict()
if proof.exploitable:
    finding["severity"] = "critical"      # ★ ترقية تلقائية
    finding["confidence"] += 0.15         # ★ تعزيز الثقة
```

### الخطوة 6: إزالة التكرارات

ثلاث قوائم من ثلاث طبقات → قائمة واحدة موحّدة:

```
findings[]          + "pattern_engine"
suite_findings[]    + "security_suite"
detector_findings[] + "agl_22_detectors"
         │
         ▼
    Bucketing: (line ÷ 20, normalized_category) → key
         │
         ▼
    لكل key متكرر:
      - أضف المصدر لـ confirmed_by[]
      - ارفع confidence +10%
      - احتفظ بالوصف الأطول
      - احتفظ بالخطورة الأعلى
         │
         ▼
    ترتيب: severity ▶ confidence (تنازلي)
         │
         ▼
    all_findings_unified[]
```

**مثال:** 12 findings قبل الدمج → 8 بعد الدمج (4 مكررة من عدة طبقات).

### الخطوة 7: إثراء بالنموذج اللغوي

**المدخل:** أعلى 5 findings بخطورة CRITICAL/HIGH  
**استراتيجية الاستدعاء:**

```
المحاولة 1: Ollama /api/chat مباشرة
    ↓ (فشل؟)
المحاولة 2: HolographicLLM عبر OffensiveSecurityEngine
    ↓ (template response؟)
المحاولة 3: Ollama /api/generate كملاذ أخير
```

**المخرج (لكل finding):**
```python
finding["llm_explanation"] = "تحليل تقني مفصل..."
finding["fix"] = "كود Solidity للإصلاح"
finding["poc"] = "كود هجوم PoC"
```

---

## 6. الطبقة 1: محلل العقود الذكية

**الملف:** `AGL_NextGen/src/agl/engines/smart_contract_analyzer.py` (2565 سطر)

```
code (str)
  │
  ├── _detect_contracts()        → أسماء العقود
  ├── _detect_functions()        → أسماء الدوال + signatures
  ├── _pattern_scan()            → 8 regex patterns
  │     ├── reentrancy: .call{value قبل state=
  │     ├── overflow: unchecked block / SafeMath missing
  │     ├── tx.origin: require(tx.origin
  │     ├── timestamp: block.timestamp
  │     ├── delegatecall: .delegatecall(
  │     ├── selfdestruct: selfdestruct(
  │     ├── assembly: assembly {
  │     └── uninitialized: (storage pointer)
  │
  ├── _advanced_analysis()       → لكل function:
  │     ├── _find_function_body()     → حدود الدالة
  │     ├── _build_lightweight_cfg()  → CFGNode graph
  │     │     ├── كل node: external_calls, state_writes, state_reads
  │     │     ├── entry → [block1, block2, ...] → exit
  │     │     └── predecessors/successors linked
  │     ├── ReentrancyPattern.check() → BFS على CFG
  │     └── unchecked external calls check
  │
  └── return {findings, contracts, functions, advanced_analysis}
```

---

## 7. الطبقة 2: منسق الأمان

**الملف:** `AGL_NextGen/src/agl/engines/security_orchestrator.py` (1105 سطر)

```
file_path
  │
  ├── ThreadPoolExecutor(max_workers=3)
  │     ├── SlitherBackend.analyze()    → subprocess → JSON parse
  │     ├── MythrilBackend.analyze()    → subprocess → JSON parse
  │     ├── SemgrepBackend.analyze()    → subprocess → JSON parse
  │     └── Z3Backend.analyze()         → FormalVerificationEngine
  │
  ├── جمع النتائج + توحيد الصيغة → List[Finding]
  │
  ├── LLMBackend.analyze()              → Ollama API
  │
  └── return List[Finding]
```

**Finding dataclass:**
```python
@dataclass
class Finding:
    id: str
    title: str
    severity: Severity          # Enum: critical/high/medium/low
    category: VulnCategory      # Enum: reentrancy/access_control/...
    description: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    source_tool: str
    confidence: float
    recommendation: str = ""
    poc_code: str = ""
```

---

## 8. الطبقة 4: الكاشفات الدلالية (22 كاشف)

**بنية الكاشف (BaseDetector):**
```python
class BaseDetector(ABC):
    DETECTOR_ID: str        # معرف فريد
    TITLE: str              # عنوان الكاشف
    SEVERITY: Severity      # الخطورة الافتراضية
    CONFIDENCE: Confidence  # مستوى الثقة
    DESCRIPTION: str        # وصف مختصر

    @abstractmethod
    def detect(self, contract: ParsedContract,
               all_contracts: List[ParsedContract]) -> List[Finding]:
        ...
```

**كيف يعمل كاشف ReentrancyETH مثلاً:**
```
1. لكل دالة في العقد:
2.   هل فيها external_call مع ETH (op_type == EXTERNAL_CALL_ETH)؟
3.   هل فيها state_write بعد ذلك الـ call؟
4.   هل الدالة عليها nonReentrant modifier؟
5.   إذا: call_with_eth + state_write_after + no_guard → Finding(CRITICAL)
```

---

## 9. الطبقة 5: إثبات الاستغلال

**الملف:** `agl_security_tool/exploit_reasoning.py` (810 سطر)

```
ExploitReasoningEngine.analyze(findings, source_code, file_path)
  │
  ├── _extract_functions(source)        → [(name, body, line, modifiers)]
  │
  ├── لكل finding بخطورة CRITICAL/HIGH:
  │     │
  │     ├── _match_finding_to_function()  → ربط الثغرة بالدالة
  │     │     ├── اسم الدالة مباشرة
  │     │     ├── قرب رقم السطر
  │     │     └── الاسم في العنوان/الوصف
  │     │
  │     ├── PathExtractor.extract_paths()
  │     │     ├── تصنيف كل سطر: require / external_call / state_write
  │     │     └── أعلام: has_external_call, has_state_write_after_call, has_guard
  │     │
  │     ├── ConstraintSolver.check_path_feasibility()
  │     │     ├── إنشاء Z3 Solver + BitVec(256)
  │     │     ├── شروط require → Z3 constraints
  │     │     ├── نمذجة الهجوم (reentrancy: withdraw1 + withdraw2 > balance)
  │     │     └── solver.check() → SAT + counterexample أو UNSAT
  │     │
  │     ├── InvariantChecker.check_invariants()
  │     │     ├── balance_conservation
  │     │     ├── reentrancy_no_double_spend
  │     │     ├── no_free_money
  │     │     └── access_gated
  │     │
  │     └── ExploitAssembler.assemble()
  │           ├── اختيار نوع الهجوم (reentrancy / tx.origin / unchecked)
  │           ├── بناء خطوات الهجوم
  │           ├── حساب التكلفة والربح
  │           ├── حساب الثقة (0-100%)
  │           └── الحكم النهائي (EXPLOITABLE / LOW RISK)
  │
  ├── إزالة تكرارات الإثباتات (أفضل إثبات لكل دالة)
  │
  └── return {exploit_proofs, exploitable_count, total_analyzed, time_seconds}
```

---

## 10. إزالة التكرارات وتعزيز الثقة

```python
# مفتاح التجميع:
key = (line // 20, normalized_category)

# التوحيد:
"reentrancy-eth" → "reentrancy"
"access_control" → "access"
"unchecked-return-value" → "unchecked"

# القواعد:
إذا key موجود مسبقاً:
    confirmed_by.append(source_label)
    confidence += 0.10                    # ★ دليل من مصدر إضافي
    severity = max(existing, new)         # الأعلى خطورة
    description = longest(existing, new)  # الأكثر تفصيلاً
إذا key جديد:
    أنشئ merged finding
```

---

## 11. الطبقة 6: إثراء بالنموذج اللغوي

```
all_findings_unified
  │
  ├── فلترة: أعلى 5 بخطورة CRITICAL/HIGH
  │
  ├── لكل finding: استخراج 15 سطر كود محيط (line-5 إلى line+10)
  │
  ├── بناء Prompt واحد يشمل كل الـ5 findings
  │     ├── System: "You are a smart contract security expert..."
  │     └── User: "### Finding 1\n- Severity: CRITICAL\n- Line: 18\n```solidity\n...\n```"
  │
  ├── الاستدعاء:
  │     ├── المحاولة 1: POST http://localhost:11434/api/chat
  │     │     model: "qwen2.5:3b-instruct", timeout: 180s
  │     ├── المحاولة 2: HolographicLLM.chat_llm(messages)
  │     └── المحاولة 3: POST /api/generate (fallback)
  │
  ├── تحليل الاستجابة:
  │     ├── تنظيف control characters
  │     ├── استخراج JSON array من النص
  │     ├── فك التداخل: [[{},{}]] → [{},{}]
  │     └── ربط كل item بالـ finding حسب "id"
  │
  └── إلحاق: finding["llm_explanation"], finding["fix"], finding["poc"]
```

---

## 12. هيكل البيانات المُخرَجة

```python
{
    # الحالة
    "status": "COMPLETE",
    "file": "D:\\project\\contract.sol",
    "scan_mode": "standard",
    "time_seconds": 62.22,

    # الطبقات المستخدمة
    "layers_used": [
        "smart_contract_analyzer",     # الطبقة 1
        "cfg_analysis",                # ضمن الطبقة 1
        "security_orchestrator",       # الطبقة 2
        "agl_detectors",               # الطبقة 4
        "exploit_reasoning",           # الطبقة 5
        "llm_analysis"                 # الطبقة 6 (اختياري)
    ],

    # النتائج الخام (قبل الدمج)
    "findings": [...],                  # من الطبقة 1
    "suite_findings": [...],            # من الطبقة 2
    "detector_findings": [...],         # من الطبقة 4

    # النتائج الموحّدة (بعد الدمج)
    "all_findings_unified": [
        {
            "title": "Reentrancy Vulnerability",
            "severity": "critical",
            "line": 18,
            "description": "...",
            "confidence": 0.95,
            "confirmed_by": ["pattern_engine", "security_suite", "agl_22_detectors"],
            "exploit_proof": {                    # ★ من الطبقة 5
                "exploitable": true,
                "function": "withdraw",
                "z3_result": "SAT",
                "counterexample": {"amount": "221720...", ...},
                "invariant_violated": {
                    "name": "balance_conservation",
                    "description": "...",
                    "violated": true
                },
                "attack_steps": ["1. Deploy malicious...", ...],
                "attack_cost": "221.72 ETH (initial deposit)",
                "attack_profit": "443.44+ ETH",
                "confidence": 1.0,
                "verdict": "EXPLOITABLE: withdraw() — Z3 SAT..."
            },
            "llm_explanation": "...",             # ★ من الطبقة 6
            "fix": "...",
            "poc": "..."
        },
        ...
    ],

    # الإحصائيات
    "severity_summary": {"CRITICAL": 3, "HIGH": 1, "MEDIUM": 0, "LOW": 2},
    "total_findings": 6,
    "total_before_dedup": 12,
    "duplicates_removed": 6,

    # إثبات الاستغلال
    "exploit_reasoning": {
        "exploit_proofs": [...],
        "exploitable_count": 3,
        "total_analyzed": 9,
        "time_seconds": 0.118
    },

    # بيانات إضافية
    "contracts": ["VulnerableBank"],
    "functions": ["withdraw", "transferTo", "ping", "isLucky"],
    "parsed_contracts": 1,
    "warnings": [...]
}
```

---

## 13. فحص المشاريع الكاملة

**الملف:** `agl_security_tool/project_scanner.py` (1083 سطر)

```bash
python -m agl_security_tool project ./aave-v3-core -m deep -f markdown -o report.md
```

```
ProjectScanner(project_path)
  │
  ├── discover()
  │     ├── اكتشاف النوع:
  │     │     foundry.toml → Foundry
  │     │     hardhat.config.ts → Hardhat
  │     │     truffle-config.js → Truffle
  │     │     (غيرها) → Bare
  │     │
  │     ├── حل Remappings:
  │     │     @openzeppelin/ → node_modules/@openzeppelin/
  │     │     @aave/ → lib/aave/
  │     │
  │     ├── جمع ملفات .sol (مع استثناء tests/mocks/deps)
  │     │
  │     └── لكل ملف: parse → contracts, imports, inherits, LOC
  │
  ├── get_dependency_graph()
  │     └── {nodes: [...], edges: [{from, to, type}]}
  │
  ├── get_project_stats()
  │     └── {total_files, total_contracts, total_functions, total_loc, ...}
  │
  └── full_scan() / quick_scan() / deep_scan()
        │
        └── لكل ملف .sol:
              AGLSecurityAudit().scan(file)
              → جمع النتائج في تقرير موحّد
```

---

## 14. جسر VS Code

**الملف:** `agl_security_tool/vscode_bridge.py` (269 سطر)

```
VS Code Extension
    │
    │  stdin: {"action": "scan_file", "target": "x.sol", "mode": "deep"}
    ▼
vscode_bridge.py
    │
    ├── يقرأ JSON من stdin
    ├── يوجّه stdout → stderr (العرض الداخلي)
    ├── يستدعي AGLSecurityAudit أو ProjectScanner
    └── يكتب النتيجة JSON على real stdout
    │
    │  stdout: {"status": "COMPLETE", "findings": [...]}
    ▼
VS Code Extension
    └── يعرض النتائج في panel
```

**الأوامر المدعومة:**

| Action | الوظيفة | المُستدعى |
|--------|---------|----------|
| `check` | فحص صحة التثبيت | `detect_engines()` |
| `scan_file` | فحص ملف واحد | `AGLSecurityAudit.scan()` / `.deep_scan()` / `.quick_scan()` |
| `scan_project` | فحص مشروع كامل | `ProjectScanner.full_scan()` |
| `discover` | اكتشاف بنية المشروع | `ProjectScanner.discover()` |
| `stats` | إحصائيات المشروع | `ProjectScanner.get_project_stats()` |
| `graph` | شجرة التبعيات | `ProjectScanner.get_dependency_graph()` |

---

## 15. أمثلة عملية

### مثال 1: فحص عقد واحد مع إثبات الاستغلال

```bash
python -m agl_security_tool scan vulnerable.sol -f json -o result.json
```

**الخرج المختصر:**
```
EXPLOITABLE: withdraw() — Z3 SAT, invariant balance_conservation broken
  Cost: 221.72 ETH | Profit: 443.44+ ETH
  Steps: deploy → deposit → withdraw → reenter → drain

EXPLOITABLE: transferTo() — Z3 SAT, invariant access_gated broken
  Cost: ~0 ETH | Profit: Full contract balance

EXPLOITABLE: ping() — Z3 SAT, invariant no_free_money broken
  Cost: 0 ETH | Profit: State inconsistency
```

### مثال 2: فحص سريع لمئات الملفات

```bash
python -m agl_security_tool scan contracts/ --recursive -f text
```

الفحص السريع يستخدم الطبقة 1 فقط (regex + CFG) — ثوانٍ لكل ملف.

### مثال 3: فحص مشروع Aave V3 بالكامل

```bash
python -m agl_security_tool project ./aave-v3-core -m scan -f markdown -o aave_report.md
```

### مثال 4: استخدام من Python مع إعدادات مخصصة

```python
from agl_security_tool import AGLSecurityAudit

audit = AGLSecurityAudit({"skip_llm": True})
result = audit.scan("contract.sol")

# الوصول للنتائج
for finding in result["all_findings_unified"]:
    proof = finding.get("exploit_proof")
    if proof and proof["exploitable"]:
        print(f"🔴 {finding['title']}")
        print(f"   Verdict: {proof['verdict']}")
        for step in proof["attack_steps"]:
            print(f"   {step}")
```

### مثال 5: استخدام فقط طبقة إثبات الاستغلال

```python
from agl_security_tool.exploit_reasoning import ExploitReasoningEngine

engine = ExploitReasoningEngine()

findings = [
    {
        "title": "Reentrancy in withdraw()",
        "severity": "critical",
        "category": "reentrancy",
        "line": 18,
        "function": "withdraw"
    }
]

with open("contract.sol") as f:
    code = f.read()

result = engine.analyze(findings, code)
for proof in result["exploit_proofs"]:
    print(proof["verdict"])
```

---

## ملاحظات تقنية

- **Python 3.10+** مطلوب
- **Z3** مطلوب لطبقة إثبات الاستغلال: `pip install z3-solver`
- **Ollama** اختياري للتحليل بالنموذج اللغوي (المنفذ الافتراضي: `localhost:11434`)
- **Slither/Mythril/Semgrep** اختيارية — الأداة تعمل بدونها عبر Z3 + الكاشفات الداخلية
- كل طبقة مستقلة — فشل أي طبقة لا يوقف البقية
- الزمن النموذجي: ~1 ثانية (بدون LLM/أدوات خارجية) إلى ~60 ثانية (كل الطبقات)
