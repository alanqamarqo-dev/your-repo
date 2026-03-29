# AGL Security Tool — تقرير الفحص العميق المُصحَّح
## Deep Investigation Report v2.0

**تاريخ**: 2026-03-22  
**المُراجع**: GitHub Copilot (Claude Opus 4.6)  
**النطاق**: التشغيل الفعلي + تحليل الكود + أنماط التشغيل الثلاثة  

---

## ملخص تنفيذي

بعد فحص عميق يشمل:
- تشغيل فعلي للأدوات الخارجية (Slither, Mythril, Semgrep, solc)
- تتبع مسار التنفيذ عبر 4 ملفات محرك رئيسية (~5000+ سطر)
- فحص الفروقات بين أنماط التشغيل الثلاثة (full/deep/quick)
- اختبار SecurityOrchestrator vs tool_backends
- فحص HolographicLLM و OffensiveSecurityEngine

**الحكم**: الأداة ثورية هندسياً لكن بها **6 أخطاء حقيقية** (3 حرجة + 3 متوسطة).

---

## ⚠️ تصحيح نتائج سابقة خاطئة

| الادعاء السابق | الحقيقة |
|---|---|
| "solc يتجمد" | ❌ **خطأ** — solc يعمل خلال 0.3 ثانية من Python subprocess. التجمد يحدث فقط من PowerShell المباشر |
| "Slither/Mythril معطلة" | ❌ **خطأ** — كلاهما مثبت ويعمل (Slither 0.11.5, Mythril v0.24.8). Slither يجد 13 ثغرة عبر SecurityOrchestrator |
| "RiskCore P=0.000" | ❌ **خطأ** — كان خطأ في سكريبت الاختبار (مفتاح dict خاطئ). RiskCore يعمل بشكل صحيح (P=0.900, P=0.867) |
| "Z3 لا يعمل" | ❌ **خطأ جزئي** — Z3 يعمل ويثبت ثغرات رياضياً. لكنه يحتاج timeout أطول للعقود الكبيرة |

---

## 🔴 الأخطاء الحرجة المُثبتة (3)

### 1. `_detect_project_root()` — خطأ cwd يُسقط جميع نتائج tool_backends بصمت

**الموقع**: `tool_backends.py` سطر 198-210  
**الخطورة**: حرجة  
**مؤكدة**: ✅ أُثبتت تجريبياً

**المشكلة**:
```python
# tool_backends.py line 198
def _detect_project_root(file_path):
    markers = ("foundry.toml", "package.json", "hardhat.config.js", ".git")  # ← يبحث عن .git
    # يصعد من المجلدات حتى يجد .git → يجد D:\AGL (الجذر الخاطئ)
```

عندما يكون `.git` في `D:\AGL` والمشروع في `D:\AGL\agl_security_tool`:
- `_detect_project_root()` يُرجع `D:\AGL` 
- `subprocess.run(["slither", "relative/path"], cwd="D:\AGL")` → الملف غير موجود → 0 نتائج
- `result.success = True` → **إخفاق صامت**

**الإثبات التجريبي**:
```
Slither مباشر (بدون cwd):           13 ثغرة ✅
Slither عبر tool_backends (cwd خاطئ): 0 ثغرة ❌
Slither بنفس cwd + مسار مطلق:       13 ثغرة ✅  ← يثبت أن المشكلة في المسار النسبي
```

**التأثير**: لا يؤثر على المسار الرئيسي (SecurityOrchestrator) لأنه لا يستخدم cwd.
يؤثر على مسار fallback فقط (عندما يفشل تحميل AGL_NextGen).

**الإصلاح**:
```python
# في SlitherRunner.analyze(), سطر ~387:
cmd = ["slither", os.path.abspath(file_path), "--json", "-"]  # ← مسار مطلق دائماً
```

---

### 2. `skip_llm` لا يصل إلى OffensiveSecurityEngine → تجمد خط الأنابيب

**الموقع**: `core.py` سطر 304  
**الخطورة**: حرجة  
**مؤكدة**: ✅ أثبتت بتجمد العملية

**المشكلة**:
```python
# core.py line 304 — deep_scan()
offensive = self._engine.process_task(
    "smart_contract_audit", target,
    context={"skip_suite": True}  # ← يمرر skip_suite فقط، لا يمرر skip_llm!
)
```

OffensiveSecurityEngine يستدعي:
1. `holo_brain.chat_llm()` → Ollama بدون timeout (`requests.post(..., timeout=None)`)
2. `meta_planner.process_task()` → قد يستدعي Ollama أيضاً

عندما Ollama يُرجع خطأ 500 ("unable to allocate CPU buffer"):
- `_call_ollama()` يفشل ويعيد المحاولة بنموذج أصغر
- لكن محركات أخرى في offensive engine قد تتجمد

**الإثبات**: `deep_scan()` تجمد لأكثر من 10 دقائق مع 1.7 ثانية CPU فقط (I/O blocked).

**الإصلاح**:
```python
# core.py line 304:
offensive = self._engine.process_task(
    "smart_contract_audit", target,
    context={"skip_suite": True, "skip_llm": self.config.get("skip_llm", False)}
)
```
```python
# holographic_llm.py line 289:
response = requests.post(..., timeout=120)  # ← بدلاً من timeout=None
```

---

### 3. `resolve_target()` — ملف واحد → يفحص المجلد بأكمله

**الموقع**: `audit_pipeline.py` سطر 326  
**الخطورة**: حرجة (نتائج مضللة)  
**مؤكدة**: ✅

**المشكلة**:
```python
# audit_pipeline.py line 326
if target_path.is_file() and target_path.suffix == ".sol":
    return str(target_path.parent), False  # ← يُرجع المجلد الأب!
```

عند تمرير `contract.sol`:
- يُفحص كل ملف `.sol` في نفس المجلد
- التقرير يظهر ثغرات من عقود أخرى كأنها من العقد المطلوب
- مُضلل خصوصاً في مجلد `test_contracts/vulnerable/` (22 ملف)

**لا يتم التعامل مع هذا في أي نمط تشغيل** — يحدث في full وdeep وquick.

---

## 🟡 الأخطاء المتوسطة (3)

### 4. Semgrep — فشل إنشاء ملف القواعد

**الموقع**: `tool_backends.py` SemgrepRunner  
**المشكلة**: `[Errno 28] No space left on device` عند كتابة ملف YAML المؤقت  
**ملاحظة**: مشكلة بيئة (قرص ممتلئ)، ليست خطأ كود. لكن لا يوجد fallback.

### 5. ±5 سطر tolerance في إزالة التكرارات

**الموقع**: `audit_pipeline.py` سطر ~915-922  
```python
for delta in range(-5, 6):
    deep_sigs.add((title_n, line + delta))
```
نطاق واسع جداً — يمكن أن يُسقط ثغرات حقيقية على أسطر قريبة.

### 6. Mythril timeout 360 ثانية يبطئ خط الأنابيب

**الموقع**: `security_orchestrator.py` سطر 382  
**المشكلة**: `timeout=config.mythril_timeout + 60` = 360 ثانية  
الأدوات الأخرى تنتهي في ثوانٍ بينما Mythril يُعطل `as_completed()` لـ 6 دقائق.

---

## 🏗️ هيكل المحركات الفعلي (مُثبت بالتشغيل)

### ترتيب أولويات المحركات في `core.py`:

```
الأولوية 1: SecurityOrchestrator (AGL_NextGen)
    ├── SlitherBackend     → subprocess بدون cwd → يعمل ✅ (13 نتيجة)
    ├── MythrilBackend     → timeout 360s → يعمل ✅ (0 نتيجة على عقد صغير)
    ├── SemgrepBackend     → 60s timeout → يعمل ✅
    ├── Z3Backend          → 10s timeout → يعمل ✅
    └── LLM (Ollama)       → معطل عند skip_llm=True ✅

الأولوية 2: SecuritySuite (AGL_NextGen) — fallback 1
    └── scan_file() → AST + Pattern

الأولوية 3: tool_backends (مستقل) — fallback 2
    ├── SlitherRunner      → cwd bug → 0 نتائج ❌
    ├── MythrilRunner      → cwd bug → 0 نتائج ❌
    └── SemgrepRunner      → disk full → خطأ ❌

OffensiveSecurityEngine (Layer 3) — يعمل دائماً:
    ├── Heuristic Analysis → regex → يعمل ✅
    ├── HolographicLLM     → Ollama → يفشل/يتجمد ❌
    ├── MetaPlanner        → Ollama → يفشل/يتجمد ❌
    ├── QuantumHunter      → Ollama → يفشل/يتجمد ❌
    ├── FormalVerifier     → Z3 (timeout 5s) → يعمل ✅
    └── EVM Simulation     → يعمل ✅
```

### الفرق الجوهري بين الأولوية 1 و 3:

| الجانب | SecurityOrchestrator (يعمل) | tool_backends (fallback) |
|---|---|---|
| cwd | لا يعيّن → يستخدم cwd الحالي | يعيّن `cwd=D:\AGL` (خاطئ) |
| المسار | يستلم absolute path من core.py | قد يستلم نسبي |
| `.git` كمؤشر جذر | لا — يبحث عن foundry.toml فقط | نعم — يجد `.git` في `D:\AGL` |
| النتيجة | ✅ 13 ثغرة | ❌ 0 ثغرة |

---

## 📊 أنماط التشغيل الثلاثة — مقارنة مفصلة

| الخطوة | full | deep | quick |
|---|:---:|:---:|:---:|
| 0: resolve_target | ✅ | ✅ | ✅ |
| 1: load_engines | ✅ | ✅ | ✅ |
| 2: discover_project | ✅ | ✅ | ✅ |
| 2.5: shared_parsing | ✅ | ✅ | ✅ |
| 3: deep_scan (Layer 0-5) | ✅ | ✅ | ❌ |
| 4: Z3 symbolic (مكتبات) | ✅ | ✅ | ❌ |
| 5: state_extraction | ✅ | ✅ | ❌ |
| 6: semantic detectors | ✅ | ✅ | ✅ |
| 7: exploit_reasoning | ✅ | ✅ | ❌ |
| 8: heikal_math | ✅ | ❌ | ❌ |
| 8.5: cross-layer dedup | ✅ | ✅ | ✅ |
| 8.7: PoC generation | ✅ | ✅ | ❌ |

**هل المشاكل المبلغ عنها تُعالج في أنماط مختلفة?**

| المشكلة | full | deep | quick | الحكم |
|---|---|---|---|---|
| `_detect_project_root` cwd bug | يُتجاوز (Orchestrator) | يُتجاوز (Orchestrator) | يُتجاوز (Orchestrator) | ✅ الخطأ موجود لكن لا يؤثر عندما Orchestrator متاح |
| `skip_llm` لا يصل offensive engine | يتجمد | يتجمد | لا يعمل deep_scan | ❌ الخطأ يؤثر في full و deep |
| `resolve_target` ملف→مجلد | ❌ | ❌ | ❌ | ❌ يؤثر في الثلاثة |
| ±5 dedup tolerance | ❌ | ❌ | ❌ | ❌ يؤثر في الثلاثة |
| Mythril 360s timeout | يبطئ | يبطئ | لا يعمل | ⚠️ يبطئ full و deep |
| Heikal→RiskCore integration | لا يُعد | Heikal لا يعمل | Heikal لا يعمل | ⚠️ فقط في full |

---

## ✅ ما يعمل بشكل ممتاز (مُثبت بالتشغيل)

1. **SecurityOrchestrator** — يُشغل 4 أدوات متوازية، Slither يجد 13 ثغرة ✅
2. **RiskCore** — تسجيل احتمالي دقيق (P=0.900 لـ reentrancy, P=0.867 لـ Z3) ✅
3. **SolidityASTParserFull** — محلل recursive descent حقيقي (1371 سطر) ✅
4. **22 semantic detectors** — reentrancy, access control, defi patterns ✅
5. **Z3 symbolic engine** — إثبات رياضي BitVec(256) ✅
6. **Exploit reasoning** — 38 قانون موزون ✅
7. **State extraction** — رسم بياني مالي + CEI analysis ✅
8. **Action space builder** — تحويل state→actions→attack sequences ✅
9. **Attack simulation engine** — محاكاة اقتصادية بفيزياء ✅
10. **Fallback chain** — 3 مستويات (Orchestrator→Suite→tool_backends) ✅

---

## 🔍 اكتشاف مهم: Ollama لا يعمل فعلياً

```
Ollama API: http://localhost:11434 → 200 OK
Models: agl-conscious-core, qwen2.5:7b, qwen2.5:3b, qwen2.5:0.5b

لكن عند التشغيل الفعلي:
POST /api/generate → 500 Internal Server Error
"unable to allocate CPU buffer" — ذاكرة غير كافية
```

كل المحركات التي تعتمد على Ollama (HolographicLLM, MetaPlanner, QuantumHunter) تفشل.
المشكلة ليست في الكود بل في الأجهزة — لكن `timeout=None` في `requests.post` يعني
أنه إذا كان Ollama بطيئاً (بدلاً من خطأ 500 فوري)، خط الأنابيب يتجمد للأبد.

---

## 🎯 الأولويات للإصلاح

### أعلى أولوية (تؤثر على خط الأنابيب الرئيسي):
1. **إضافة timeout لاستدعاءات Ollama** → `holographic_llm.py:289` → `timeout=120`
2. **تمرير skip_llm إلى OffensiveSecurityEngine** → `core.py:304`
3. **إصلاح `_detect_project_root()` أو استخدام مسار مطلق** → `tool_backends.py:198` أو `:387`

### أولوية متوسطة:
4. **إصلاح `resolve_target()` للملف الواحد** → `audit_pipeline.py:326`
5. **تقليل dedup tolerance من ±5 إلى ±2** → `audit_pipeline.py:920`
6. **تقليل Mythril timeout أو جعله قابل للتكوين** → `security_orchestrator.py:382`

---

## الخلاصة

الأداة **ثورية من ناحية التصميم** — 8 طبقات تحليل، محركات متوازية، إثبات رياضي.
كل الأدوات الخارجية مثبتة وتعمل (Slither ✅, Mythril ✅, Semgrep ✅, solc ✅, Z3 ✅).

**المسار الرئيسي (SecurityOrchestrator) يعمل بشكل صحيح** — 13 ثغرة من Slither.
**مسار الـ fallback (tool_backends) معطل** بسبب خطأ `_detect_project_root()`.
**OffensiveSecurityEngine يتجمد** لأن `skip_llm` لا يصل إليه و Ollama ليس لديه ذاكرة كافية.

الإصلاحات الـ 3 الحرجة يمكن تنفيذها في أقل من 20 سطر كود.
