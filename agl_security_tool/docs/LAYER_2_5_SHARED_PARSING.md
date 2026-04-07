# المرحلة 2.5: التحليل الدلالي المشترك — Shared Semantic Parsing Layer

> **الإصدار:** 1.0.0  
> **تاريخ التوثيق:** أبريل 2026  
> **الملف المصدري:** `audit_pipeline.py` — الدالة `run_shared_parsing()` (سطر 798–898)  
> **حالة الاختبار:** ✅ 45 اختبار ناجح + اختبار تحقق حي

---

## 📑 فهرس المحتويات

1. [نظرة عامة](#1-نظرة-عامة)
2. [الملفات المصدرية](#2-الملفات-المصدرية)
3. [موقعها في خط الأنابيب](#3-موقعها-في-خط-الأنابيب)
4. [دالة التشغيل الرئيسية](#4-دالة-التشغيل-الرئيسية)
5. [نماذج البيانات المُستخدمة](#5-نماذج-البيانات-المُستخدمة)
6. [المتغيرات الداخلية](#6-المتغيرات-الداخلية)
7. [تدفق البيانات التفصيلي](#7-تدفق-البيانات-التفصيلي)
8. [ماذا تستقبل كل طبقة لاحقة](#8-ماذا-تستقبل-كل-طبقة-لاحقة)
9. [مثال حقيقي — فحص عقد ReentrancyVault](#9-مثال-حقيقي--فحص-عقد-reentrancyvault)
10. [البيئة والمكتبات](#10-البيئة-والمكتبات)
11. [نتائج الاختبارات](#11-نتائج-الاختبارات)
12. [مخطط تدفق البيانات الكامل](#12-مخطط-تدفق-البيانات-الكامل)

---

## 1. نظرة عامة

المرحلة 2.5 هي **طبقة تحضير مشتركة** (Shared Preprocessing Layer) تقع بين اكتشاف المشروع (Step 2) والفحص العميق (Step 3). وظيفتها **تحليل جميع ملفات Solidity مرة واحدة** ومشاركة النتائج مع كل الطبقات اللاحقة.

### لماذا تُوجد هذه الطبقة؟

بدون هذه الطبقة، كانت **كل طبقة تحليلية** (Deep Scan, Z3, Detectors, Exploit, Heikal) **تُحلل نفس الملفات مستقلة** — أي أن عقداً واحداً من 1000 سطر كان يُحلَّل 5 مرات. هذه الطبقة:

| المشكلة (قبل) | الحل (بعد) |
|----------------|------------|
| O(n×m) تحليل — n ملفات × m طبقات | O(n) تحليل — مرة واحدة لكل ملف |
| كل طبقة تقرأ الملفات من القرص | القراءة مرة واحدة + تخزين `source` في الذاكرة |
| لا تصنيف للدوال الآمنة | بناء `_safe_funcs` مبكراً لمنع FPs |
| لا فهرس مشترك للعقود | بناء `_all_contracts` و `_state_vars` |

**هذه ليست طبقة كشف ثغرات** — بل طبقة بنية تحتية تخدم كل الطبقات.

---

## 2. الملفات المصدرية

| العنصر | الملف | الوصف |
|--------|-------|-------|
| **الدالة الرئيسية** | `audit_pipeline.py:798–898` | `run_shared_parsing()` |
| **المحلل الأساسي** | `detectors/solidity_ast_parser.py` | `SolidityASTParserFull` — محلل AST كامل |
| **المحلل الاحتياطي** | `detectors/solidity_parser.py` | `SoliditySemanticParser` — محلل regex دلالي |
| **نماذج البيانات** | `detectors/__init__.py:1–210` | `ParsedContract`, `ParsedFunction`, `OpType`, `StateVar`, `ModifierInfo`, `Operation`, `Finding` |
| **كائن السياق** | `audit_pipeline.py:87–285` | `AuditContext` — يخزن ويوزع النتائج |
| **التحميل** | `audit_pipeline.py:494–640` | `load_engines()` — يُحمّل المحلل |
| **اختبار الطبقة** | `tests/test_shared_parsing_layer.py` | اختبار شامل على عقد Compound V3 Comet |
| **اختبار الإصلاحات** | `tests/test_shared_parse_fixes.py` | اختبارات interface cast وinheritance وoverloading |

---

## 3. موقعها في خط الأنابيب

```
run_full_audit()                              ← نقطة الدخول
  │
  ├── Step 0:   resolve_target()              ← تحليل الهدف
  ├── Step 1:   load_engines()                ← تحميل 12 محرك (يشمل parser)
  ├── Step 2:   discover_project()            ← اكتشاف بنية المشروع
  │
  ├── ★ Step 2.5: run_shared_parsing(ctx)     ← *** هنا تعمل هذه الطبقة ***
  │
  ├── Step 3:   run_core_deep_scan(ctx)       ← يستهلك parsed (يتجنب إعادة التحليل)
  ├── Step 4:   run_z3_symbolic(ctx)          ← يستهلك source (يتجنب قراءة القرص)
  ├── Step 5:   run_state_extraction(ctx)     ← (مقبول للتوافق)
  ├── Step 6:   run_detectors(ctx)            ← يستهلك parsed + _safe_funcs
  ├── Step 7:   run_exploit_reasoning(ctx)    ← يستهلك source + function_blocks
  ├── Step 8:   run_heikal_math(ctx)          ← يستهلك source + function_blocks + _safe_funcs
  ├── Step 8.5: deduplicate_cross_layer(ctx)  ← يستهلك _safe_funcs
  ├── Step 8.7: run_poc_generation(ctx)
  └── Step 9:   generate_final_report()
```

**هل تعمل ضمن الـ 14 طبقة؟** نعم — هي طبقة أساسية في خط الأنابيب. ليست طبقة تحليل أمني بذاتها، بل **طبقة خدمية** تُحضّر البيانات لجميع الطبقات التحليلية الـ 13 الأخرى.

---

## 4. دالة التشغيل الرئيسية

### `run_shared_parsing(ctx_or_engines, project=None) → Dict[str, Any]`

**الموقع:** `audit_pipeline.py` سطر 798

```python
def run_shared_parsing(ctx_or_engines, project: Dict = None) -> Dict[str, Any]:
```

**المدخلات:**
- `ctx_or_engines` — كائن `AuditContext` (الطريقة الحديثة) أو قاموس `engines` (للتوافق)
- `project` — بنية المشروع (اختياري إذا مرّر `AuditContext`)

**المخرجات:**
- `Dict[str, Any]` — قاموس مشترك يخزَّن في `ctx.shared_parse`

### خطوات التنفيذ التفصيلية:

```
الخطوة 1: استرجاع المحلل
  └── parser = engines.get("parser")
      └── SolidityASTParserFull (أو SoliditySemanticParser كاحتياطي)

الخطوة 2: تصفية الأهداف
  └── targets = {k: v for k, v in contracts.items() if not k.startswith("iface/")}
      └── يستبعد الواجهات (interfaces) — لا منطق أمني فيها

الخطوة 3: حلقة التحليل — لكل ملف:
  ├── 3a: قراءة الكود المصدري من القرص
  │     └── source = f.read()
  ├── 3b: تحليل الكود → قائمة عقود
  │     └── parsed = parser.parse(source, path)  →  List[ParsedContract]
  ├── 3c: بناء function_blocks
  │     └── {اسم_الدالة: الجسم_الخام (raw_body)}
  ├── 3d: بناء فهرس العقود
  │     └── all_contracts_index[contract.name] = contract
  ├── 3e: بناء فهرس متغيرات الحالة
  │     └── all_state_vars[contract.name] = contract.state_vars
  └── 3f: تخزين النتيجة
        └── shared[name] = {parsed, source, path, function_blocks}

الخطوة 4: بناء الدوال الآمنة
  └── safe_funcs = {fn_name.lower() for fn where
          visibility ∈ {internal, private} OR mutability ∈ {view, pure}}

الخطوة 5: إضافة المفاتيح الخاصة
  ├── shared["_safe_funcs"] = safe_funcs
  ├── shared["_all_contracts"] = all_contracts_index
  └── shared["_state_vars"] = all_state_vars

الخطوة 6: تخزين في AuditContext
  └── ctx.populate_from_shared_parse(shared)
      ├── ctx.shared_parse = shared
      ├── ctx._global_safe_funcs = shared["_safe_funcs"]
      └── ctx.remappings = shared["_remappings"] (إن وُجدت)
```

### دالة التخزين: `AuditContext.populate_from_shared_parse(shared)`

**الموقع:** `audit_pipeline.py` سطر 278

```python
def populate_from_shared_parse(self, shared_parse: Dict):
    self.shared_parse = shared_parse
    self._global_safe_funcs = shared_parse.get("_safe_funcs", set())
    self.remappings = shared_parse.get("_remappings", [])
```

---

## 5. نماذج البيانات المُستخدمة

### 5.1 `ParsedContract` — العقد المُحلّل

الوحدة الأساسية للتحليل. يصف عقداً واحداً بكل تفاصيله البنيوية.

**الموقع:** `detectors/__init__.py` سطر 157

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `name` | `str` | اسم العقد (مثل `ReentrancyVault`) |
| `contract_type` | `str` | نوع العقد: `contract` / `interface` / `library` / `abstract` |
| `inherits` | `List[str]` | قائمة العقود المُورَثة |
| `state_vars` | `Dict[str, StateVar]` | متغيرات الحالة: `{اسم: StateVar}` |
| `functions` | `Dict[str, ParsedFunction]` | الدوال: `{اسم: ParsedFunction}` |
| `modifiers` | `Dict[str, ModifierInfo]` | المُعدّلات: `{اسم: ModifierInfo}` |
| `events` | `List[str]` | الأحداث المُعلنة |
| `using_for` | `List[Dict]` | تعليمات `using SafeMath for uint256` |
| `pragma` | `str` | إصدار pragma المُحدّد |
| `is_upgradeable` | `bool` | هل العقد قابل للترقية |
| `uses_safe_math` | `bool` | هل يستخدم SafeMath |
| `solidity_version` | `str` | إصدار Solidity |
| `line_start` / `line_end` | `int` | نطاق الأسطر في الملف |
| `source_file` | `str` | مسار الملف المصدري |

### 5.2 `ParsedFunction` — الدالة المُحلّلة

القلب الدلالي للتحليل. تصف دالة واحدة مع **ترتيب عملياتها** الذي يكشف ثغرات CEI.

**الموقع:** `detectors/__init__.py` سطر 100

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `name` | `str` | اسم الدالة |
| `visibility` | `str` | `public` / `external` / `internal` / `private` |
| `mutability` | `str` | `view` / `pure` / `payable` / `""` (state-changing) |
| `modifiers` | `List[str]` | المُعدّلات المُطبقة (مثل `nonReentrant`, `onlyOwner`) |
| `parameters` | `List[Dict]` | المعاملات: `[{name, type}]` |
| `returns` | `List[Dict]` | أنواع الإرجاع |
| `line_start` / `line_end` | `int` | نطاق الأسطر |
| `raw_body` | `str` | **الكود الخام الكامل** — يُمرر لـ Z3/Exploit/Heikal |
| **التحليل الدلالي** | | |
| `operations` | `List[Operation]` | **العمود الفقري: قائمة العمليات مُرتّبة بترتيب التنفيذ** |
| `state_reads` | `List[str]` | أسماء متغيرات الحالة المقروءة |
| `state_writes` | `List[str]` | أسماء متغيرات الحالة المكتوبة |
| `external_calls` | `List[Operation]` | عمليات الاستدعاء الخارجي |
| `require_checks` | `List[str]` | شروط require المُستخرجة |
| `internal_calls` | `List[str]` | الدوال الداخلية المُستدعاة |
| **خصائص أمنية محسوبة** | | |
| `has_reentrancy_guard` | `bool` | حماية reentrancy موجودة |
| `has_access_control` | `bool` | تحكم بالوصول موجود |
| `sends_eth` | `bool` | ترسل ETH |
| `modifies_state` | `bool` | تُعدّل متغيرات الحالة |
| `has_loops` | `bool` | تحتوي حلقات |
| `has_selfdestruct` | `bool` | تحتوي selfdestruct |
| `has_delegatecall` | `bool` | تحتوي delegatecall |

### 5.3 `Operation` — عملية واحدة مُرتّبة

**الموقع:** `detectors/__init__.py` سطر 77

كل `ParsedFunction` تحتوي قائمة `operations` مُرتّبة — هذا الترتيب هو ما يكشف انتهاكات CEI.

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `op_type` | `OpType` | نوع العملية (من 22 نوعاً) |
| `line` | `int` | رقم السطر |
| `target` | `str` | الهدف (اسم المتغير أو عنوان الاستدعاء) |
| `details` | `str` | تفاصيل إضافية |
| `sends_eth` | `bool` | هل ترسل ETH |
| `in_loop` | `bool` | هل داخل حلقة |
| `in_condition` | `bool` | هل داخل شرط |
| `raw_text` | `str` | النص الخام من الكود |

### 5.4 `OpType` — أنواع العمليات (22 نوعاً)

**الموقع:** `detectors/__init__.py` سطر 42

```
STATE_READ       — قراءة متغير حالة
STATE_WRITE      — كتابة متغير حالة
EXTERNAL_CALL    — استدعاء خارجي (.call, .transfer, .send)
EXTERNAL_CALL_ETH — استدعاء خارجي مع ETH (.call{value:...})
DELEGATECALL     — استدعاء مُفوَّض
STATICCALL       — استدعاء ثابت
INTERNAL_CALL    — استدعاء داخلي
REQUIRE          — فحص require
ASSERT           — فحص assert
REVERT           — إرجاع revert
EMIT             — إطلاق حدث
SELFDESTRUCT     — تدمير ذاتي
LOOP_START       — بداية حلقة
LOOP_BODY_OP     — عملية داخل حلقة
LOOP_END         — نهاية حلقة
RETURN           — إرجاع قيمة
ASSEMBLY         — كتلة assembly
MAPPING_ACCESS   — وصول لـ mapping
ARRAY_PUSH       — إضافة لمصفوفة
ARRAY_LENGTH     — طول مصفوفة
ENCODE_PACKED    — abi.encodePacked
```

### 5.5 `StateVar` — متغير الحالة

**الموقع:** `detectors/__init__.py` سطر 87

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `name` | `str` | اسم المتغير |
| `var_type` | `str` | النوع (مثل `mapping(address => uint256)`) |
| `visibility` | `str` | `public` / `internal` / `private` |
| `is_constant` | `bool` | ثابت |
| `is_immutable` | `bool` | غير قابل للتعديل بعد النشر |
| `is_mapping` | `bool` | هل هو mapping |
| `is_array` | `bool` | هل هو مصفوفة |
| `line` | `int` | رقم السطر |

### 5.6 `ModifierInfo` — معلومات المُعدّل

**الموقع:** `detectors/__init__.py` سطر 138

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `name` | `str` | اسم المُعدّل |
| `params` | `List[str]` | المعاملات |
| `body` | `str` | الكود |
| `checks_owner` | `bool` | يفحص المالك |
| `checks_role` | `bool` | يفحص دوراً |
| `is_reentrancy_guard` | `bool` | حماية reentrancy |
| `is_paused_check` | `bool` | فحص إيقاف مؤقت |

---

## 6. المتغيرات الداخلية في `run_shared_parsing()`

| المتغير | النوع | الوظيفة |
|---------|-------|---------|
| `parser` | `SolidityASTParserFull` أو `SoliditySemanticParser` | المحلل المُحمّل من engines |
| `contracts` | `Dict[str, Path]` | كل ملفات .sol المُكتشفة |
| `targets` | `Dict[str, Path]` | الملفات المُستهدفة (بدون interfaces) |
| `shared` | `Dict[str, Dict]` | **القاموس الرئيسي** — نتيجة التحليل |
| `total_funcs` | `int` | عداد إجمالي الدوال المُحلّلة |
| `all_contracts_index` | `Dict[str, ParsedContract]` | فهرس عقد → ParsedContract |
| `all_state_vars` | `Dict[str, Dict]` | فهرس عقد → متغيرات الحالة |
| `inherited_count` | `int` | عقود يُحتمل لديها وراثة (state_vars > functions) |
| `function_blocks` | `Dict[str, str]` | لكل ملف: `{اسم_الدالة: الكود_الخام}` |
| `safe_funcs` | `set` | الدوال الآمنة (lowercase) |

### بنية القاموس المُخرَج `shared`:

```python
shared = {
    # ── مفاتيح الملفات (اسم → بيانات) ──
    "src/Vault.sol": {
        "parsed":          [ParsedContract(...)],    # العقود المُحلّلة
        "source":          "pragma solidity...",     # الكود الخام
        "path":            Path("contracts/Vault.sol"),
        "function_blocks": {"deposit": "function deposit()...", ...},
    },
    "src/Token.sol": { ... },
    
    # ── مفاتيح خاصة (تبدأ بـ _) ──
    "_safe_funcs":      {"getbalance", "_internal", ...},   # set
    "_all_contracts":   {"Vault": ParsedContract(...)},     # dict
    "_state_vars":      {"Vault": {"balance": StateVar}},   # dict
}
```

---

## 7. تدفق البيانات التفصيلي

```
   ┌──────────────────────────────────────────────────────────────────┐
   │                  ملفات .sol على القرص                            │
   │         (من discover_project → project["contracts"])             │
   │         مثال: {                                                  │
   │           "src/Vault": Path("contracts/Vault.sol"),              │
   │           "src/Token": Path("contracts/Token.sol"),              │
   │           "iface/IVault": Path("interfaces/IVault.sol"),←مستبعد │
   │         }                                                       │
   └──────────────────────────────┬───────────────────────────────────┘
                                  │
                      يستبعد interfaces (iface/)
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │          لكل ملف: يقرأ source ثم يُحلل                          │
   │                                                                  │
   │  source = open(path).read()                                      │
   │  parsed = parser.parse(source, path)                             │
   │         ↓                                                        │
   │  List[ParsedContract] لكل ملف                                   │
   │    ├── ParsedContract("Vault")                                   │
   │    │     ├── state_vars: {balance: StateVar(mapping...)}         │
   │    │     ├── functions:                                          │
   │    │     │     ├── deposit() →                                   │
   │    │     │     │     operations: [STATE_WRITE(balance)]          │
   │    │     │     ├── withdraw() →                                  │
   │    │     │     │     operations: [REQUIRE, EXT_CALL_ETH,         │
   │    │     │     │                  REQUIRE, STATE_WRITE]          │
   │    │     │     └── getBalance() →                                │
   │    │     │           operations: [RETURN]                        │
   │    │     └── modifiers: {onlyOwner: ModifierInfo(...)}           │
   │    └── ParsedContract("VaultLib") (إن وُجد)                     │
   └──────────────────────────────┬───────────────────────────────────┘
                                  │
                         يبني 4 فهارس
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                     shared dict (النتيجة)                        │
   │                                                                  │
   │  ┌─ لكل ملف ─────────────────────────────────────────────┐     │
   │  │  shared["src/Vault"] = {                               │     │
   │  │    "parsed": [ParsedContract(...)],                    │     │
   │  │    "source": "pragma solidity ^0.8...",                │     │
   │  │    "path":   Path("contracts/Vault.sol"),              │     │
   │  │    "function_blocks": {                                │     │
   │  │      "deposit": "balances[msg.sender] += msg.value;",  │     │
   │  │      "withdraw": "require(balances[...]); ...",        │     │
   │  │      "getBalance": "return balances[msg.sender];"      │     │
   │  │    }                                                   │     │
   │  │  }                                                     │     │
   │  └───────────────────────────────────────────────────────┘     │
   │                                                                  │
   │  ┌─ فهارس مشتركة ──────────────────────────────────────┐       │
   │  │  _safe_funcs:    {"getbalance"}  ← view/pure/internal │       │
   │  │  _all_contracts: {"Vault": ParsedContract}             │       │
   │  │  _state_vars:    {"Vault": {"balance": StateVar}}      │       │
   │  └───────────────────────────────────────────────────────┘       │
   └──────────────────────────────┬───────────────────────────────────┘
                                  │
                    ctx.populate_from_shared_parse(shared)
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                  AuditContext (السياق المركزي)                    │
   │                                                                  │
   │    ctx.shared_parse       = shared      ← القاموس الكامل       │
   │    ctx._global_safe_funcs = {"getbalance", ...}                 │
   │    ctx.remappings         = [...]       ← import remappings     │
   └──────────────────────────────┬───────────────────────────────────┘
                                  │
              يُوزَّع على كل الطبقات اللاحقة عبر ctx
                                  │
            ┌─────────┬───────────┼───────────┬────────────┐
            ▼         ▼           ▼           ▼            ▼
       ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
       │Step 3  │ │Step 4  │ │Step 6  │ │Step 7  │ │Step 8    │
       │Deep    │ │Z3      │ │Detect. │ │Exploit │ │Heikal   │
       │Scan    │ │Symbol. │ │        │ │Reason. │ │Math     │
       └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
                                  │
                                  ▼
                         ┌───────────────┐
                         │  Step 8.5     │
                         │  Dedup        │
                         │  (_safe_funcs)│
                         └───────────────┘
```

---

## 8. ماذا تستقبل كل طبقة لاحقة

### 8.1 Step 3 — `run_core_deep_scan()` (Layer 0-5)

```python
entry = shared_parse.get(name, {})
pre_parsed = entry.get("parsed", None)
# يُمرر لـ core.deep_scan(path, pre_parsed=pre_parsed)
# ← يتجنب إعادة تحليل الملف بالكامل
```

**الفائدة:** توفير وقت التحليل. العقد المُحلَّل مسبقاً يُمرر مباشرة.

### 8.2 Step 4 — `run_z3_symbolic()` (Layer 0.5)

```python
entry = shared_parse.get(name, {})
source = entry.get("source", "")
# إذا لم يوجد source → يقرأ من القرص (fallback)
```

**الفائدة:** يتجنب قراءة الملف من القرص مرة أخرى.

### 8.3 Step 6 — `run_detectors()` (Layer 5)

```python
entry = shared_parse.get(name, {})
parsed = entry.get("parsed", None)
# يستخدم parsed مباشرة + _safe_funcs لكبت FPs
_safe = ctx._global_safe_funcs
if fn.lower() in _safe:
    continue  # ← يتخطى النتيجة على دالة آمنة
```

**الفائدة:** (1) يتجنب إعادة التحليل (2) يمنع FPs على `view`/`pure`/`internal` دوال.

### 8.4 Step 7 — `run_exploit_reasoning()` (Layer 6)

```python
sp = shared_parse or {}
entry = sp.get(name, {})
source = entry.get("source", "")
```

**الفائدة:** يحصل على الكود المصدري بدون قراءة القرص.

### 8.5 Step 8 — `run_heikal_math()` (Layer 7)

```python
entry = shared_parse.get(name, {})
source = entry.get("source", "")
pre_blocks = entry.get("function_blocks", {})
func_blocks = pre_blocks if pre_blocks else extract_function_blocks(source)
# يتخطى الدوال الآمنة:
if fname.lower() in safe_funcs:
    skipped_safe += 1
    continue
```

**الفائدة:** (1) يعيد استخدام `function_blocks` (2) يتخطى الدوال الآمنة (3) يستخدم `source`.

### 8.6 Step 8.5 — `deduplicate_cross_layer()`

```python
safe_funcs = set((shared_parse or {}).get("_safe_funcs", set()))
# يكبت نتائج LOW/INFO على الدوال الآمنة:
if fn in safe_funcs and sev in ("LOW", "INFO"):
    suppressed += 1
    continue
```

**الفائدة:** إزالة النتائج الإيجابية الكاذبة على دوال لا يمكن استغلالها خارجياً.

### 8.7 Step 8.5 — `deduplicate_cross_layer()` (تصنيف الأنماط المعروفة)

```python
contract_sources = {}
if shared_parse:
    for name, entry in shared_parse.items():
        if isinstance(entry, dict) and "source" in entry:
            contract_sources[name] = entry["source"]
final, known_stats = classify_findings(final, contract_sources)
```

**الفائدة:** يمنح `classify_findings()` الكود المصدري لتصنيف الأنماط المعروفة بدقة.

---

## 9. مثال حقيقي — فحص عقد ReentrancyVault

### العقد المُدخل:
```solidity
pragma solidity ^0.8.0;
contract ReentrancyVault {
    mapping(address => uint256) public balances;
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        balances[msg.sender] -= amount;  // ← CEI violation!
    }
    
    function getBalance() external view returns (uint256) {
        return balances[msg.sender];
    }
}
```

### نتائج التحليل المُتحقّق منها:

```
Contracts parsed: 1
  Contract: ReentrancyVault (contract)
  State vars: ['balances']
  Functions: ['deposit', 'withdraw', 'getBalance']
  
    deposit(): vis=external, mut=payable, ops=1
      state_write: target=balances, sends_eth=False

    withdraw(): vis=external, mut=, ops=4
      require: target=balances[msg.sender] >= amount
      external_call_eth: target=msg.sender, sends_eth=True    ← op[1]
      require: target=ok
      state_write: target=balances                              ← op[3]

    getBalance(): vis=external, mut=view, ops=1
      return: target=

=== المخرجات المشتركة ===
  Safe functions: {'getbalance'}           ← view تُصنَّف آمنة
  Function blocks: [deposit, withdraw, getBalance]
  Contracts index: [ReentrancyVault]
  State vars: {ReentrancyVault: [balances]}

=== كشف انتهاك CEI ===
  ⚠️ CEI VIOLATION in withdraw(): write[3] AFTER call[1]
  ← كتابة state بعد استدعاء خارجي = reentrancy!
```

### ماذا تحصل كل طبقة:

| الطبقة | ما تحصل عليه | الفائدة |
|--------|-------------|---------|
| Deep Scan | `pre_parsed=[ParsedContract(ReentrancyVault)]` | لا يعيد التحليل |
| Z3 Symbolic | `source="pragma solidity..."` (535 حرف) | لا يقرأ القرص |
| Detectors | `parsed` + يتجاهل `getBalance` | لا FP على view |
| Exploit | `function_blocks={deposit:..., withdraw:..., getBalance:...}` | تحليل مسارات |
| Heikal | `function_blocks` + يتخطى `getBalance` | يركز على الدوال الخطرة |
| Dedup | `_safe_funcs={"getbalance"}` | يكبت LOW/INFO على view |

---

## 10. البيئة والمكتبات

### بيئة التشغيل

| الخاصية | القيمة |
|---------|--------|
| **اللغة** | Python 3.10+ |
| **بيئة Blockchain** | **لا تحتاج** — لا Foundry ولا solc ولا Hardhat |
| **التنفيذ** | تحليل نص مصدري فقط (static analysis) |
| **السرعة** | ~0.01 ثانية لـ 1000 سطر كود |

### المكتبات المُستخدمة

| المكتبة | الاستخدام | نوعها |
|---------|-----------|-------|
| `re` | Regex للتحليل الدلالي | Python stdlib |
| `pathlib` | التعامل مع المسارات | Python stdlib |
| `dataclasses` | نماذج البيانات (ParsedContract, etc.) | Python stdlib |
| `typing` | Type hints | Python stdlib |

**لا تعتمد على أي مكتبة خارجية** — كل التبعيات من المكتبة القياسية.

### المحلل الأساسي: `SolidityASTParserFull`

**الموقع:** `detectors/solidity_ast_parser.py`

يُحمَّل في `load_engines()` كأولوية أولى. إذا فشل تحميله، يُستخدم `SoliditySemanticParser` (regex-based) كاحتياطي:

```python
# في load_engines():
try:
    from agl_security_tool.detectors.solidity_ast_parser import SolidityASTParserFull
    engines["parser"] = SolidityASTParserFull()   # ← الأساسي
except Exception:
    from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
    engines["parser"] = SoliditySemanticParser()   # ← الاحتياطي
```

كلا المحللين يُنتجان نفس نماذج البيانات (`List[ParsedContract]`).

---

## 11. نتائج الاختبارات

### اختبارات آلية

| الاختبار | الملف | النتيجة |
|----------|-------|---------|
| 39 اختبار parser | `tests/test_solidity_parser.py` | ✅ ناجح |
| 6 اختبارات shared parse | `tests/test_shared_parse_fixes.py` | ✅ ناجح |
| اختبار تحقق حي | `_test_layer25_verify.py` | ✅ ناجح |
| اختبار Compound Comet | `tests/test_shared_parsing_layer.py` | ✅ ناجح |

### ما تم التحقق منه:

- ✅ استخراج العقود (اسم / نوع / وراثة)
- ✅ استخراج الدوال (visibility / mutability / modifiers)
- ✅ استخراج العمليات **بترتيبها** (operations ordering)
- ✅ كشف انتهاكات CEI (State Write بعد External Call)
- ✅ تصنيف الدوال الآمنة (view/pure/internal/private)
- ✅ استخراج متغيرات الحالة (mapping / array / constant / immutable)
- ✅ بناء function_blocks (الكود الخام لكل دالة)
- ✅ تمرير البيانات لكل طبقة لاحقة
- ✅ الأداء: <0.01 ثانية لـ 1000+ سطر

---

## 12. مخطط تدفق البيانات الكامل

```
╔══════════════════════════════════════════════════════════════════════════╗
║                        AGL AUDIT PIPELINE                              ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌─────────────────────┐                                               ║
║  │  Step 0: resolve    │                                               ║
║  │  (مسار/ملف/GitHub)  │                                               ║
║  └─────────┬───────────┘                                               ║
║            ▼                                                           ║
║  ┌─────────────────────┐    ┌──────────────────────┐                   ║
║  │  Step 1: load       │───→│ engines = {           │                   ║
║  │  engines             │    │   parser: ASTParser,  │                   ║
║  │  (12 محرك)          │    │   core, z3, exploit,  │                   ║
║  └─────────┬───────────┘    │   detectors, heikal.. │                   ║
║            ▼                └──────────┬───────────┘                   ║
║  ┌─────────────────────┐               │                               ║
║  │  Step 2: discover   │               │                               ║
║  │  project structure  │               │                               ║
║  │  (Foundry/Hardhat)  │               │                               ║
║  └─────────┬───────────┘               │                               ║
║            ▼                           │                               ║
║  ╔═════════════════════════════════════╧═══════════════════╗           ║
║  ║  ★ Step 2.5: SHARED SEMANTIC PARSING                   ║           ║
║  ║                                                         ║           ║
║  ║  parser.parse(source) ──→ List[ParsedContract]          ║           ║
║  ║    ├── functions{} → operations[] (ordered!)            ║           ║
║  ║    ├── state_vars{}                                     ║           ║
║  ║    └── modifiers{}                                      ║           ║
║  ║                                                         ║           ║
║  ║  يبني:                                                  ║           ║
║  ║    shared[file]       = {parsed, source, function_blocks}║           ║
║  ║    shared[_safe_funcs] = {view, pure, internal, private} ║           ║
║  ║    shared[_all_contracts] = {name → ParsedContract}     ║           ║
║  ║    shared[_state_vars]    = {name → {var → StateVar}}   ║           ║
║  ║                                                         ║           ║
║  ║  ctx.populate_from_shared_parse(shared)                 ║           ║
║  ╚═══════════════╤═══════════════════════════════════════╝           ║
║                  │                                                     ║
║    ┌─────────────┼─────────────┬──────────────┬────────────┐          ║
║    ▼             ▼             ▼              ▼            ▼          ║
║  ┌──────┐   ┌──────┐   ┌──────────┐   ┌──────────┐  ┌──────────┐   ║
║  │Step 3│   │Step 4│   │  Step 6  │   │  Step 7  │  │ Step 8   │   ║
║  │Deep  │   │ Z3   │   │Detectors │   │ Exploit  │  │ Heikal   │   ║
║  │Scan  │   │Symb. │   │(22 كاشف)│   │Reasoning │  │  Math    │   ║
║  │      │   │      │   │          │   │          │  │(4 خوارز.)│   ║
║  │يأخذ: │   │يأخذ: │   │ يأخذ:   │   │ يأخذ:   │  │ يأخذ:   │   ║
║  │parsed│   │source│   │ parsed + │   │ source + │  │ source + │   ║
║  │      │   │      │   │safe_funcs│   │func_blk  │  │func_blk +│   ║
║  │      │   │      │   │          │   │          │  │safe_funcs│   ║
║  └──┬───┘   └──┬───┘   └────┬─────┘   └────┬─────┘  └────┬─────┘   ║
║     │          │            │              │             │          ║
║     └──────────┴────────────┴──────────────┴─────────────┘          ║
║                              │                                       ║
║                              ▼                                       ║
║                    ┌──────────────────┐                              ║
║                    │  Step 8.5: Dedup │                              ║
║                    │  (_safe_funcs →  │                              ║
║                    │   كبت LOW/INFO) │                              ║
║                    └────────┬─────────┘                              ║
║                             ▼                                       ║
║                    ┌──────────────────┐                              ║
║                    │  Step 8.7: PoC   │                              ║
║                    └────────┬─────────┘                              ║
║                             ▼                                       ║
║                    ┌──────────────────┐                              ║
║                    │  Step 9: Report  │                              ║
║                    │  (JSON / MD)     │                              ║
║                    └──────────────────┘                              ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## الملخص

| الخاصية | القيمة |
|---------|--------|
| **الاسم** | المرحلة 2.5: التحليل الدلالي المشترك |
| **النوع** | طبقة تحضير مشتركة (Shared Preprocessing) |
| **الدالة الرئيسية** | `run_shared_parsing(ctx)` |
| **المحلل** | `SolidityASTParserFull` (أو `SoliditySemanticParser` كاحتياطي) |
| **المدخلات** | ملفات .sol من `discover_project()` + parser من `load_engines()` |
| **المخرجات** | `shared_parse` dict يُخزن في `AuditContext` |
| **الطبقات المستفيدة** | 6 طبقات: Deep Scan, Z3, Detectors, Exploit, Heikal, Dedup |
| **البيئة** | Python خالص — لا Foundry ولا solc |
| **الأداء** | ~0.01 ثانية لكل 1000 سطر |
| **الاختبارات** | 45 اختبار ناجح |
