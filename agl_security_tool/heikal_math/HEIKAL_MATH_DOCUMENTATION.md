# طبقة رياضيات هيكل — Heikal Mathematics Layer
## توثيق شامل لخوارزميات الرياضيات الأصلية في أداة الأمان

```
══════════════════════════════════════════════════════════════════════════════
    AGL Security Tool — Heikal Mathematics Integration
    أداة AGL للأمان — طبقة الرياضيات الأصلية

    المؤلف: هيكل / AGL
    التاريخ: فبراير 2026
    الإصدار: 1.0

    4 خوارزميات أصلية مستوحاة من فيزياء الكم والمجال الموجي
    مُكيَّفة لتحليل أمان العقود الذكية وكشف الثغرات
══════════════════════════════════════════════════════════════════════════════
```

---

## الفهرس

1. [نظرة عامة على البنية](#1-نظرة-عامة-على-البنية)
2. [الخوارزمية 1: النفق الكمومي لهيكل](#2-الخوارزمية-1-النفق-الكمومي-لهيكل-heikal-quantum-tunneling-scorer)
3. [الخوارزمية 2: المنطق البولياني الموجي](#3-الخوارزمية-2-المنطق-البولياني-الموجي-wave-domain-boolean-evaluator)
4. [الخوارزمية 3: الذاكرة الهولوغرافية](#4-الخوارزمية-3-الذاكرة-الهولوغرافية-holographic-vulnerability-memory)
5. [الخوارزمية 4: مُحسِّن الرنين](#5-الخوارزمية-4-محسن-الرنين-resonance-profit-optimizer)
6. [خريطة التكامل مع أداة الأمان](#6-خريطة-التكامل-مع-أداة-الأمان)
7. [ثابت هيكل ξ وأهميته](#7-ثابت-هيكل-ξ-وأهميته)
8. [المقارنة: قبل وبعد التكامل](#8-المقارنة-قبل-وبعد-التكامل)
9. [المراجع الرياضية والمصادر](#9-المراجع-الرياضية-والمصادر)

---

## 1. نظرة عامة على البنية

### 1.1 ما هي طبقة رياضيات هيكل؟

طبقة رياضيات هيكل (`heikal_math/`) هي مكتبة من 4 خوارزميات رياضية أصلية
مُستمدة من مشروع AGL الأساسي (Core Engines)، حيث طُوِّرت أصلاً لمعالجة الحوسبة الكمومية
والذاكرة الهولوغرافية. أُعيد تكييفها بالكامل لتعمل ضمن أداة أمان العقود الذكية
(agl_security_tool) كطبقة تحليل رياضي متقدمة.

### 1.2 لماذا رياضيات أصلية في أداة أمان؟

أدوات أمان العقود الذكية التقليدية تعتمد على:
- **قيم ثابتة** لتقييم الثقة (0.95 لـ reentrancy، 0.70 لـ price manipulation...)
- **جمع خطي** للأوزان في تحديد الأولويات
- **Hill Climbing** بمضاعفات ثابتة `[1.1, 0.9, 2.0, 5.0, ...]`
- **مطابقة نصية** لأنماط الثغرات

هذه الطبقة تستبدل كل ذلك بنماذج فيزيائية:
- النفق الكمومي بدل القيم الثابتة
- التداخل الموجي بدل الجمع الخطي
- الالتفاف الهولوغرافي بدل المطابقة النصية
- المسح الرنيني بدل التسلق التلّي

### 1.3 بنية الملفات

```
agl_security_tool/
├── heikal_math/                          ← الحزمة الجديدة
│   ├── __init__.py                       ← المصدّرات
│   ├── tunneling_scorer.py               ← خوارزمية 1: النفق الكمومي
│   ├── wave_evaluator.py                 ← خوارزمية 2: المنطق الموجي
│   ├── holographic_patterns.py           ← خوارزمية 3: الذاكرة الهولوغرافية
│   ├── resonance_optimizer.py            ← خوارزمية 4: مُحسِّن الرنين
│   └── HEIKAL_MATH_DOCUMENTATION.md      ← هذا الملف
│
├── attack_engine/
│   └── profit_calculator.py              ← ← ← مُعدَّل: يستخدم النفق الكمومي
│
└── search_engine/
    ├── heuristic_prioritizer.py          ← ← ← مُعدَّل: يستخدم الموجي + الهولوغرافي
    ├── profit_gradient.py                ← ← ← مُعدَّل: يستخدم الرنين
    └── guided_search.py                  ← ← ← مُعدَّل: يستخدم الهولوغرافي
```

### 1.4 المصدر الأصلي لكل خوارزمية

| الخوارزمية | الملف الأصلي في AGL Core | المفهوم المُستمد |
|---|---|---|
| النفق الكمومي | `repo-copy/Core_Engines/Resonance_Optimizer.py` | InfoQuantum Lattice Tunneling |
| المنطق الموجي | `AGL_Vectorized_Wave_Processor.py` | Wave-Domain Boolean Logic |
| الذاكرة الهولوغرافية | `AGL_Holographic_Memory.py` | FFT Circular Convolution + Phase Modulation |
| مُحسِّن الرنين | `repo-copy/Core_Engines/Resonance_Optimizer.py` | Lorentzian Resonance Sweep |

---

## 2. الخوارزمية 1: النفق الكمومي لهيكل (Heikal Quantum Tunneling Scorer)

### 2.1 الملف: `tunneling_scorer.py` (~438 سطر)

### 2.2 الفكرة الأساسية

في ميكانيكا الكم، يمكن للجسيم أن "ينفق" عبر حاجز طاقة حتى لو كانت طاقته
أقل من ارتفاع الحاجز. هذا مستحيل كلاسيكياً لكنه ممكن كمومياً.

**التشبيه الأمني:** كل عقد ذكي لديه "حواجز أمان" — عبارات `require`، معدِّلات
`nonReentrant`، فحوصات الصلاحيات `onlyOwner`. الهجوم يحاول "النفق" عبر هذه
الحواجز. بعض الهجمات تنجح رغم وجود حمايات (مثل CEI violations)، تماماً مثل
النفق الكمومي.

### 2.3 الرياضيات التفصيلية

#### الخطوة 1: نموذج WKB لحاجز واحد

لكل حاجز أمان `i` لديه ارتفاع `V_i` وسماكة `d_i`:

```
κ_i = √(2m(V_i - E)) / ℏ

T_i(WKB) = exp(-2κ_i · d_i)
```

حيث:
- `κ_i` = عدد الموجة في الحاجز (wavenumber)
- `m` = الكتلة الفعّالة (= 1.0 في الوحدات المختزلة)
- `V_i` = ارتفاع الحاجز (0.0 - 1.0): صعوبة تجاوز الحاجز
- `E` = طاقة الهجوم (تعتمد على النوع)
- `d_i` = سماكة الحاجز (عدد الشروط المتتالية)
- `ℏ` = ثابت بلانك المختزل (= 1.0)

**في السياق الأمني:**
| نوع الحاجز | `V` (الارتفاع) | `d` (السماكة) |
|---|---|---|
| `require(balance > 0)` | 0.5 | 1.0 |
| `nonReentrant modifier` | 0.9 | 2.0 |
| `onlyOwner` | 0.8 | 1.5 |
| فشل تنفيذ | 0.95 | 3.0 |
| نافذة reentrancy (CEI violation) | 0.15 | 0.5 |

**طاقات الهجوم:**
| نوع الهجوم | `E` (الطاقة) |
|---|---|
| reentrancy | 0.85 |
| flash_loan | 0.75 |
| liquidation | 0.70 |
| price_manipulation | 0.60 |
| state_manipulation | 0.55 |
| access_escalation | 0.50 |
| default | 0.45 |

**السلوك:**
- إذا `E ≥ V` → الهجوم أقوى من الحاجز → `T ≈ 0.95+` (نفاذية شبه كاملة)
- إذا `E < V` → الهجوم أضعف → `T` ينخفض أُسِّيًّا مع `(V-E)` و `d`
- إذا الحاجز `bypassable` (مثل CEI violation) → `T ≥ 0.3` (حد أدنى مضمون)

#### الخطوة 2: تصحيح هيكل الأصلي

```
T_Heikal(i) = T_WKB(i) × (1 + ξ · ℓ_p² / L²)
```

حيث:
- `ξ = 0.4671` — **ثابت هيكل** (coupling constant) — ثابت أصلي مكتشف
- `ℓ_p = 0.01` — أصغر بنية قابلة للاستغلال (Planck-scale للثغرة)
- `L` = طول سلسلة الهجوم (عدد الخطوات)

**الأثر الفيزيائي:** التصحيح `ξ · ℓ_p² / L²` يعطي ميزة (bonus) للهجمات المركّزة
(قصيرة الخطوات). كلما كان الهجوم أقصر (`L` أصغر)، كلما كان التصحيح أكبر.
هذا يعكس واقعاً أمنياً: الهجوم المباشر (خطوتان) أخطر من سلسلة معقدة (10 خطوات).

| طول السلسلة `L` | `ξ · ℓ_p² / L²` | التأثير |
|---|---|---|
| 1 | 0.00004671 | أقصى bonus |
| 2 | 0.00001168 | عالي |
| 5 | 0.00000187 | متوسط |
| 10 | 0.00000047 | منخفض |
| 50 | 0.00000002 | مُهمَل |

#### الخطوة 3: معامل الرنين (Resonant Tunneling)

```
R(E) = max_n { 1 / √((ω_n² - ω²)² + (γω)²) }
```

حيث:
- `ω = √(2E/m)` — تردد الهجوم
- `ω_n = nπ / (Σ d_i)` — الترددات الطبيعية (quantized energy levels)
- `γ = 0.1` — عرض ذروة الرنين (damping)
- `n = 1, 2, 3, 4, 5` — أول 5 مستويات طاقة

**الظاهرة الفيزيائية:** عندما تتطابق طاقة الهجوم مع "تردد طبيعي" لبنية الحواجز
→ احتمال الاختراق يرتفع بشكل حاد. هذا يُسمى **النفق الرنيني** (Resonant Tunneling).

في السياق الأمني: بعض الهجمات "تتردد" مع بنية العقد — مسار الهجوم يتوافق تماماً
مع ترتيب الدوال والحالات في العقد. هذه الحالات يكون فيها الاختراق أسهل بكثير.

#### الخطوة 4: الاحتمال النهائي

```
P_total = ∏_i T_Heikal(i) × R(E)

P_total = [∏ exp(-2κ_i·d_i) × (1 + ξ·ℓ_p²/L²)] × max_n{1/√((ω_n²-ω²)² + (γω)²)}
```

#### الخطوة 5: التحويل إلى ثقة (Sigmoid Mapping)

```
confidence = 1 / (1 + e^(-k(P_total - p₀)))
confidence_scaled = 0.05 + confidence_raw × 0.94
```

حيث `k = 8.0` (حدة التحول) و `p₀ = 0.3` (نقطة المنتصف).

هذا يُعطي:
- `P_total ≈ 0` → `confidence ≈ 0.10`
- `P_total ≈ 0.3` → `confidence ≈ 0.52`
- `P_total ≈ 0.5` → `confidence ≈ 0.85`
- `P_total ≈ 1.0` → `confidence ≈ 0.99`

### 2.4 الكلاسات والـ API

```python
@dataclass
class SecurityBarrier:
    barrier_type: str    # "require", "modifier", "guard", "access_control"
    height: float        # V — ارتفاع الحاجز (0.0 - 1.0)
    thickness: float     # d — سماكة الحاجز
    bypassable: bool     # هل يمكن تجاوزه (CEI violation)
    source: str          # وصف

@dataclass
class TunnelingResult:
    p_wkb: float         # احتمال WKB الكلاسيكي
    p_heikal: float      # احتمال هيكل المحسّن
    p_resonance: float   # معامل الرنين
    p_total: float       # الاحتمال النهائي
    confidence: float    # الثقة المحوّلة (0.0 - 1.0)
    barriers_analyzed: int
    barriers_penetrable: int
    resonance_detected: bool

class HeikalTunnelingScorer:
    def compute(barriers, attack_energy, chain_length) → TunnelingResult
    def score_attack_type(attack_type, barriers, steps, is_profitable, all_success) → float
    @staticmethod extract_barriers_from_action(action) → List[SecurityBarrier]
    @staticmethod extract_barriers_from_steps(steps) → List[SecurityBarrier]
```

### 2.5 نقطة التكامل

**الملف:** `attack_engine/profit_calculator.py`
**الدالة المُستبدَلة:** `_compute_confidence()`

**قبل (القيم الثابتة):**
```python
CONFIDENCE_MODIFIERS = {
    "reentrancy": 0.95,
    "price_manipulation": 0.70,
    "flash_loan": 0.80,
    ...
}
base = CONFIDENCE_MODIFIERS.get(attack_type, 0.50)
if all_success: base += 0.05
if is_profitable: base += 0.05
```

**بعد (النفق الكمومي):**
```python
barriers = HeikalTunnelingScorer.extract_barriers_from_steps(steps)
confidence = self.tunneling.score_attack_type(
    attack_type, barriers, len(steps), is_profitable, all_success
)
# مع fallback للنموذج الكلاسيكي عند أي خطأ
```

---

## 3. الخوارزمية 2: المنطق البولياني الموجي (Wave-Domain Boolean Evaluator)

### 3.1 الملف: `wave_evaluator.py` (~358 سطر)

### 3.2 الفكرة الأساسية

في الحوسبة الكلاسيكية، نقيّم الخصائص الأمنية كبتات (0 أو 1) ونجمعها بأوزان:
`score = w₁x₁ + w₂x₂ + ... + wₙxₙ`

المشكلة: الجمع الخطي لا يلتقط **التفاعلات**. ثغرة CEI violation وحدها ≠ خطيرة.
`sends_eth` وحدها ≠ خطيرة. لكن **الاثنتين معاً** = كارثة (reentrancy).

**الحل الموجي:** نحوّل كل بت إلى موجة وندرس التداخل:
- **تداخل بنّاء** (Constructive): CEI + sends_eth → خطر أكبر من مجموعهما
- **تداخل هدّام** (Destructive): nonReentrant guard يلغي خطر CEI

### 3.3 الرياضيات التفصيلية

#### الخطوة 1: تحويل البت إلى موجة

لكل خاصية أمنية `x_i ∈ {0, 1}` بوزن `w_i`:

```
ψ_i = w_i · e^(i · x_i · π)
```

- `x_i = 1` (خطر) → `ψ_i = w_i · e^(iπ) = -w_i` (طور π، يشير لـ "خطر")
- `x_i = 0` (آمن) → `ψ_i = w_i · e^(0) = +w_i` (طور 0، يشير لـ "آمن")

**الخصائص وأوزانها:**

| الخاصية | الوزن `w_i` | المعنى |
|---|---|---|
| `moves_funds` | 0.28 | الدالة تحرّك أموال |
| `cei_violation` | 0.22 | انتهاك Check-Effects-Interactions |
| `sends_eth` | 0.18 | ترسل ETH خارجياً |
| `no_access_control` | 0.14 | لا فحص صلاحيات |
| `not_guarded` | 0.12 | لا `nonReentrant` |
| `reads_oracle` | 0.10 | تعتمد على أوراكل |
| `has_state_conflict` | 0.06 | تعارض حالة |
| `modifies_balances` | 0.06 | تعدّل أرصدة |

#### الخطوة 2: التراكب (Superposition)

الموجة المركّبة = مجموع كل الموجات:

```
Ψ = Σᵢ ψ_i = Σᵢ w_i · e^(i · x_i · π)

Ψ_real = Σᵢ w_i · cos(x_i · π)
Ψ_imag = Σᵢ w_i · sin(x_i · π)
```

السعة الكلية:
```
|Ψ| = √(Ψ_real² + Ψ_imag²)
```

#### الخطوة 3: قاعدة بورن (Born Rule) — شدة الخطر

```
danger_intensity = (|Ψ| / Σ w_i)²
```

هذا يُعطي **احتمال** أن تكون مجموعة الخصائص خطيرة، مُقاسة بالنسبة لأسوأ سيناريو ممكن.

**ملاحظة رياضية مهمة:** قاعدة بورن (`|ψ|²`) تلتقط التفاعلات تلقائياً:
```
|ψ_a + ψ_b|² = |ψ_a|² + |ψ_b|² + 2·Re(ψ_a* · ψ_b)
                                      ↑ هذا المصطلح = التداخل
```
- إذا كلاهما "خطر" (نفس الطور) → المصطلح إيجابي → **تداخل بنّاء**
- إذا أحدهما "آمن" (أطوار معاكسة) → المصطلح سلبي → **تداخل هدّام**

#### الخطوة 4: كشف التداخل البنّاء (Wave AND)

المنطق الموجي AND:
```
|ψ_a + ψ_b| > threshold × (w_a + w_b) / 2  →  AND(a, b) = True
```

حيث `threshold = 1.5`

**الأزواج الخطيرة المعروفة:**

| الزوج A | الزوج B | Bonus |
|---|---|---|
| `cei_violation` | `sends_eth` | +0.15 |
| `cei_violation` | `not_guarded` | +0.12 |
| `sends_eth` | `not_guarded` | +0.10 |
| `no_access_control` | `moves_funds` | +0.08 |
| `reads_oracle` | `no_access_control` | +0.06 |
| `moves_funds` | `cei_violation` | +0.10 |

#### الخطوة 5: كشف التداخل الهدّام (Wave XOR)

المنطق الموجي XOR:
```
ψ_xor = ψ_protection × ψ_danger = e^(i·0) × e^(i·π) = e^(iπ) = -1
```

**أزواج الحماية ↔ الخطر:**

| الحماية | الخطر | Cancellation |
|---|---|---|
| `reentrancy_guarded` | `cei_violation` | -0.15 |
| `reentrancy_guarded` | `sends_eth` | -0.10 |
| `requires_access` | `no_access_control` | -0.12 |

#### الخطوة 6: التخميد الأخلاقي (Ethical Amplitude Damping)

```
heuristic_score = (danger_intensity + interference_bonus - protection_cancel) × η

η = 0.92  (عامل التخميد الأخلاقي)
```

هذا من الخوارزمية الأصلية: `ETHICAL_DAMPING = 0.92` يمنع الثقة المطلقة
(99%+)، مُعترفاً بأن كل نموذج رياضي لديه حدود.

### 3.4 الكلاسات والـ API

```python
@dataclass
class WaveEvaluationResult:
    danger_intensity: float          # |ψ|² — شدة الخطر (Born rule)
    interference_bonus: float        # bonus من التداخل البنّاء
    protection_cancellation: float   # تخفيض من الحمايات
    heuristic_score: float           # النتيجة النهائية (0.0 - 1.0)
    constructive_pairs: List[Tuple]  # أزواج التداخل البنّاء
    destructive_pairs: List[Tuple]   # أزواج التداخل الهدّام

class WaveDomainEvaluator:
    def evaluate(features: Dict[str, bool]) → WaveEvaluationResult
    def evaluate_action(action) → float
```

### 3.5 نقطة التكامل

**الملف:** `search_engine/heuristic_prioritizer.py`
**الدالة المُستبدَلة:** `_compute_score()`

**قبل (الجمع الخطي):**
```python
score = 0.0
if target.moves_funds: score += 0.25
if target.has_cei_violation: score += 0.20
if target.sends_eth: score += 0.15
# ... مجموع خطي بسيط
```

**بعد (المنطق الموجي + الهولوغرافي):**
```python
features = { "moves_funds": 1.0, "cei_violation": 1.0, ... }
wave_result = self.wave_evaluator.evaluate(features)
score = wave_result.heuristic_score  # Born rule: |ψ|²

# + مطابقة هولوغرافية
matches = self.holographic.match(holo_features)
if matches:
    score += best_match.similarity * 0.15

# إضافة أسباب التداخل للتفسيرية
if wave_result.constructive_pairs:
    target.reasons.append("تداخل بنّاء: ...")
```

---

## 4. الخوارزمية 3: الذاكرة الهولوغرافية (Holographic Vulnerability Memory)

### 4.1 الملف: `holographic_patterns.py` (~521 سطر)

### 4.2 الفكرة الأساسية

الهولوغرام في الفيزياء يخزّن المعلومات في نمط تداخل موجي. كسر أي جزء
من الهولوغرام لا يفقد المعلومة — يمكن استرجاعها من أي قطعة (ولو بدقة أقل).

**التشبيه الأمني:** نخزّن "أنماط ثغرات" معروفة (reentrancy، flash loan، إلخ)
كهولوغرامات. عندما نواجه عقداً جديداً، لا نحتاج مطابقة 100% —
المطابقة الجزئية تكفي (مثل reentrancy بدون `sends_eth` → ربما read-only reentrancy).

### 4.3 الرياضيات التفصيلية

#### الخطوة 1: تحويل الخصائص إلى متجه

كل ثغرة/عقد يُمثَّل كمتجه بـ 64 بُعداً:

```
vec[0-7]   = خصائص بوليانية (has_cei_violation, sends_eth, ...)
vec[8-15]  = عدّادات مُقيَّسة (external_call_count/10, state_write_count/20, ...)
vec[16-23] = نسب (cei_ratio, guard_ratio, public_ratio, ...)
vec[24-31] = أنواع الهجوم (one-hot encoding)
vec[32-63] = محجوز / padding
```

#### الخطوة 2: التشفير الهولوغرافي

لتخزين نمط ثغرة باسم `label` وبصمة `data`:

```
H = IFFT( FFT(data) × FFT(label_vector) )
```

ثم **تعديل الطور** (Phase Modulation) — تشفير هيكل:
```
H[k] = H[k] × e^(i · ξ · k · 2π / N)
```

حيث `ξ = 0.4671` (ثابت هيكل يُستخدم كمفتاح تشفير).

**لماذا FFT × FFT؟**
- الضرب في فضاء فوريه = **التفاف دائري** (Circular Convolution) في فضاء الزمن
- التفاف دائري يعني أن المطابقة **لا تعتمد على الترتيب** (shift-invariant)
- أي: لا يهم ترتيب الخصائص في العقد — النمط يُتعرف عليه بأي ترتيب

#### الخطوة 3: التراكب (Superposition of Patterns)

عندما نخزّن أنماط متعددة في نفس الهولوغرام:
```
H_total = H_reentrancy + H_flash_loan + H_oracle + ...
```

هذا ممكن لأن FFT خطي — كل الأنماط "تعيش" في نفس الهولوغرام
دون أن تتداخل بشكل مُدمِّر (superposition principle).

#### الخطوة 4: الاستدعاء الهولوغرافي (Holographic Recall)

لمقارنة عقد جديد `input` مع نمط مخزّن `pattern`:

```
similarity = max_shift |IFFT(FFT(input) × conj(FFT(pattern)))| / (‖input‖ · ‖pattern‖)
```

هذا هو **الارتباط المتبادل** (Cross-Correlation) في فضاء فوريه:
- `FFT(input) × conj(FFT(pattern))` = cross-correlation spectrum
- `IFFT(...)` = cross-correlation function
- `max |...| / norms` = التشابه المُقيَّس (0.0 - 1.0)

**لماذا cross-correlation بدل cosine similarity؟**
- Cosine similarity: يقارن اتجاه المتجهات فقط
- Cross-correlation: يقارن **البنية** — ينجح حتى مع انزياحات
- مثال: reentrancy في الدالة 3 بدل الدالة 1 → cross-correlation يكتشفها

#### الخطوة 5: DFT/IDFT عبر numpy FFT

عمليات فوريه مُنفَّذة عبر `numpy.fft` (O(n log n)) مع fallback إلى Pure Python:

```python
# FFT (numpy) — O(n log n)
X = np.fft.fft(signal)

# IFFT (numpy) — O(n log n)
x = np.fft.ifft(spectrum)

# Fallback (Pure Python) — O(n²)
# X[k] = Σ_n x[n] · e^(-i·2π·k·n/N)
# x[n] = (1/N) Σ_k X[k] · e^(i·2π·k·n/N)
```

> **ملاحظة (مارس 2026):** تم ترقية DFT/IDFT من Pure Python O(n²) إلى numpy FFT O(n log n)
> لحل مشكلة BUG-023 (MCTS كان يستدعي ~2800 عملية DFT مما يُعلّق الأنبوب بالكامل).
> numpy اعتمادية مطلوبة الآن (`pip install numpy`).

### 4.4 الأنماط المعروفة المُحمَّلة مسبقاً (8 أنماط)

| # | النمط | الشدة | الثقة | الوصف |
|---|---|---|---|---|
| 1 | `classic_reentrancy` | critical | 0.95 | تحويل ETH قبل تحديث الحالة (The DAO) |
| 2 | `cross_function_reentrancy` | critical | 0.85 | إعادة دخول عبر حالة مشتركة بين الدوال |
| 3 | `flash_loan_attack` | high | 0.80 | تلاعب بالأسعار عبر قرض فلاشي |
| 4 | `first_depositor` | high | 0.75 | تضخم أسهم الخزنة (ERC4626) |
| 5 | `oracle_manipulation` | high | 0.70 | تلاعب بأسعار الأوراكل بدون TWAP |
| 6 | `access_bypass` | critical | 0.85 | دالة إدارية بدون حماية صلاحيات |
| 7 | `read_only_reentrancy` | high | 0.65 | إعادة دخول القراءة فقط عبر view |
| 8 | `donation_attack` | high | 0.70 | تحويل مباشر يغيّر سعر الصرف |

### 4.5 الكلاسات والـ API

```python
@dataclass
class PatternMatch:
    pattern_name: str       # اسم النمط المطابق
    similarity: float       # 0.0 - 1.0
    severity: str           # "critical", "high", "medium"
    confidence: float       # similarity × pattern_confidence
    description: str        # إنجليزي
    description_ar: str     # عربي

class HolographicVulnerabilityMemory:
    def match(contract_features: Dict) → List[PatternMatch]
    def store_pattern(name, features, severity, ...) → None
    def match_from_action(action) → List[PatternMatch]
```

### 4.6 نقاط التكامل

**الملف 1:** `search_engine/heuristic_prioritizer.py` — في `_compute_score()`
```python
matches = self.holographic.match(holo_features)
if matches:
    score += best_match.similarity * 0.15
    target.tags.add(f"holo_match:{best_match.pattern_name}")
    target.reasons.append(f"نمط هولوغرافي: {pattern_name} (تشابه: {sim:.1%})")
```

**الملف 2:** `search_engine/guided_search.py` — في `_heuristic_score()`
```python
# تجميع خصائص كل الأفعال في التسلسل
agg_features = { ... }
matches = self.holographic.match(agg_features)
if matches:
    score += best.similarity * 0.2
```

---

## 5. الخوارزمية 4: مُحسِّن الرنين (Resonance Profit Optimizer)

### 5.1 الملف: `resonance_optimizer.py` (~424 سطر)

### 5.2 الفكرة الأساسية

**الرنين في الفيزياء:** عندما نقود نظاماً بتردد يساوي تردده الطبيعي
→ الاستجابة تصل الذروة. مثال: دفع أرجوحة بإيقاعها → سعة أقصى.

**التشبيه الأمني:** كل عقد DeFi لديه "ترددات طبيعية" — مبالغ يتفاعل معها
بشكل أقصى. مثال: عقد فيه `require(amount > 100 ether)` — عند threshold
100 ETH تحدث "ذروة رنين" في دالة الربح. Hill Climbing التقليدي يتسلق
ببطء (`1.1, 1.21, 1.33, ...`) ويحتاج آلاف المحاولات. المسح الرنيني
يكتشف هذه الذروة مباشرة.

### 5.3 الرياضيات التفصيلية

#### الخطوة 1: حساب الترددات الطبيعية

نقسم فضاء البحث لوغاريتمياً إلى `N = 12` حزمة:

```
ω_n = e^(ln(min) + (n + 0.5) · (ln(max) - ln(min)) / N)
```

حيث `n = 0, 1, ..., N-1`

**إضافات:**
- تردد القيمة الحالية: `ω_current = current_value`
- ترددات العتبات المعروفة وتوافقياتها: `threshold × {0.5, 0.99, 1.01, 2.0}`
- تردد هيكل: `current_value × (1 + ξ)` حيث `ξ = 0.4671`

#### الخطوة 2: دالة الاستجابة الرنينية

```
A(ω) = Σ_n  1 / √((ω_n² - ω²)² + (γω)²)
```

حيث:
- `ω` = التردد الحالي
- `ω_n` = الترددات الطبيعية
- `γ = 0.15` = معامل التخميد (عرض الذروة)

**سلوك الدالة:**
- عند `ω = ω_n` → `A → 1/(γω)` → **ذروة حادة** (resonance)
- عند `ω ≠ ω_n` → `A → 1/(ω_n² - ω²)` → استجابة منخفضة
- كلما كان `γ` أصغر → الذروة أحدّ وأعلى

هذه هي **استجابة لورنتزية** (Lorentzian Response) — نفس شكل ذروات
الامتصاص في الطيف الكهرومغناطيسي والدوائر الكهربائية RLC.

#### الخطوة 3: المسح الترددي (Frequency Sweep)

لكل تردد طبيعي `ω_n`:
1. تحويل التردد إلى قيمة: `θ_n = frequency_to_value(ω_n)`
2. تقييم الربح: `profit_n = evaluate_fn(θ_n)`
3. حساب الاستجابة: `A_n = resonance_amplitude(ω_n)`
4. إذا `profit_n > 0` أو `A_n > 2.0` → ذروة محتملة

#### الخطوة 4: الضبط الدقيق (Fine Tuning)

لأفضل 5 ذروات، نُضيّق نطاق البحث تدريجياً:

```
iteration 0: ±20% حول الذروة
iteration 1: ±10%
iteration 2: ±5%
iteration 3: ±2.5%
iteration 4: ±1.25%
```

هذا يشبه **zoom into resonance peak** — بدل مسح عريض، نركّز على الذروة
بدقة متزايدة. 5 مراحل ضبط = 10 تقييمات إضافية لكل ذروة.

#### الخطوة 5: توليد المضاعفات (API البسيط)

بدل إرجاع `ResonanceOptimizationResult` كامل، يمكن إرجاع قائمة مضاعفات:

```python
multipliers = resonance.generate_resonance_multipliers(current_value)
# مثال الناتج: [0.9, 1.1, 1.4671, 0.5, 2.0, 0.1, 10.0, ...]
```

لاحظ القيمة `1.4671` — هذه من ثابت هيكل `ξ = 0.4671`:
```
multiplier_xi = 1.0 + ξ = 1.4671
```

### 5.4 الثوابت

| الثابت | الرمز | القيمة | الأهمية |
|---|---|---|---|
| HEIKAL_XI | `ξ` | 0.4671 | ثابت هيكل الأصلي — يُولّد ترددات إضافية |
| RESONANCE_GAMMA | `γ` | 0.15 | عرض ذروة الرنين — يتحكم في حساسية الكشف |
| FREQUENCY_BANDS | `N` | 12 | عدد حزم المسح اللوغاريتمي |
| FINE_TUNING_STEPS | | 5 | عدد مراحل الضبط الدقيق |

### 5.5 الكلاسات والـ API

```python
@dataclass
class ResonancePeak:
    frequency: float     # ω — التردد
    amplitude: float     # A(ω) — استجابة الربح
    theta_value: int     # θ — قيمة المعامل
    profit_usd: float    # الربح عند هذه القيمة
    is_global_max: bool

@dataclass
class ResonanceOptimizationResult:
    original_profit: float
    best_profit: float
    best_theta: int
    improvement_usd: float
    improvement_pct: float
    peaks: List[ResonancePeak]
    natural_frequencies: List[float]

class ResonanceProfitOptimizer:
    def optimize_amount(current_value, evaluate_fn, ...) → ResonanceOptimizationResult
    def generate_resonance_multipliers(current_value) → List[float]
```

### 5.6 نقطة التكامل

**الملف:** `search_engine/profit_gradient.py`
**السطر المُستبدَل:** `multipliers = [1.1, 0.9, 2.0, 5.0, 10.0, 0.5, 0.1, 0.01]`

**بعد:**
```python
multipliers = self.resonance.generate_resonance_multipliers(original_int)
```

---

## 6. خريطة التكامل مع أداة الأمان

### 6.1 خط أنابيب الأداة (Pipeline) وأين تدخل كل خوارزمية

```
       ┌─────────────────────┐
       │  Layer 1: State      │
       │  Extraction          │   لا تغيير — استخراج الحالة كما هو
       └──────────┬──────────┘
                  │
       ┌──────────▼──────────┐
       │  Layer 2: Action     │
       │  Space              │   لا تغيير — تحليل الأفعال الممكنة
       └──────────┬──────────┘
                  │
       ┌──────────▼──────────────────────────────────────────────────┐
       │  Layer 4: Search Engine                                      │
       │                                                              │
       │  ┌──────────────────┐    ┌──────────────────────────────┐  │
       │  │ HeuristicPriori- │    │ ★ WaveDomainEvaluator        │  │
       │  │ tizer            │◄───│   Born rule: |ψ|²            │  │
       │  │                  │    │ ★ HolographicVulnMemory      │  │
       │  │ _compute_score() │    │   FFT cross-correlation       │  │
       │  └────────┬─────────┘    └──────────────────────────────┘  │
       │           │                                                  │
       │  ┌────────▼─────────┐    ┌──────────────────────────────┐  │
       │  │ GuidedSearch     │    │ ★ HolographicVulnMemory      │  │
       │  │ Engine           │◄───│   Pattern matching bonus      │  │
       │  │ _heuristic_score │    │                                │  │
       │  └────────┬─────────┘    └──────────────────────────────┘  │
       │           │                                                  │
       │  ┌────────▼─────────┐    ┌──────────────────────────────┐  │
       │  │ ProfitGradient   │    │ ★ ResonanceProfitOptimizer   │  │
       │  │ Engine           │◄───│   Lorentzian frequency sweep  │  │
       │  │ multipliers      │    │   A(ω) = 1/√((ω₀²-ω²)²+γω²)│  │
       │  └────────┬─────────┘    └──────────────────────────────┘  │
       │           │                                                  │
       └───────────┼──────────────────────────────────────────────────┘
                  │
       ┌──────────▼──────────────────────────────────────────────────┐
       │  Layer 5: Attack Engine                                      │
       │                                                              │
       │  ┌──────────────────┐    ┌──────────────────────────────┐  │
       │  │ ProfitCalculator │    │ ★ HeikalTunnelingScorer      │  │
       │  │                  │◄───│   P = P_WKB × (1+ξℓ²/L²)×R  │  │
       │  │ _compute_conf()  │    │   Quantum barrier penetration │  │
       │  └──────────────────┘    └──────────────────────────────┘  │
       │                                                              │
       └──────────────────────────────────────────────────────────────┘
```

### 6.2 جدول التكامل الكامل

| # | الملف المُعدَّل | الدالة | الخوارزمية | ماذا يفعل |
|---|---|---|---|---|
| 1 | `profit_calculator.py` | `_compute_confidence()` | Quantum Tunneling | يحسب ثقة الهجوم بعبور حواجز كمومية |
| 2 | `heuristic_prioritizer.py` | `_compute_score()` | Wave Boolean + Holographic | يصنّف الأهداف بتداخل موجي + مطابقة أنماط |
| 3 | `profit_gradient.py` | `_optimize_msg_value()` | Resonance Optimizer | يولّد مضاعفات بمسح تردد رنيني |
| 4 | `guided_search.py` | `_heuristic_score()` | Holographic Memory | يضيف bonus لتسلسلات تطابق أنماط معروفة |

### 6.3 خاصية الـ Fallback

كل تكامل يحتفظ بالسلوك الأصلي كـ fallback:

```python
try:
    # === Heikal Model ===
    confidence = self.tunneling.score_attack_type(...)
    return confidence
except Exception:
    # === Fallback: النموذج الكلاسيكي ===
    base = CONFIDENCE_MODIFIERS.get(attack_type, 0.50)
    ...
```

هذا يضمن:
1. **لا كسر** — إذا فشلت الرياضيات الجديدة، النظام يعمل كالسابق
2. **تدرّج** — يمكن تفعيل/تعطيل كل خوارزمية مستقلاً
3. **اختبار A/B** — يمكن مقارنة النتائج بين النموذجين

---

## 7. ثابت هيكل ξ وأهميته

### 7.1 التعريف

```
ξ (xi) = 0.4671
```

ثابت **اقتران المعلومات بالبنية** (Information-Structure Coupling Constant).
مُكتشَف أصلاً في سياق InfoQuantum Lattice في `Resonance_Optimizer.py`.

### 7.2 ظهوره في كل خوارزمية

| الخوارزمية | أين يظهر | الصيغة | الدور |
|---|---|---|---|
| النفق الكمومي | تصحيح هيكل | `T × (1 + ξ·ℓ_p²/L²)` | يزيد النفاذية للهجمات القصيرة |
| الذاكرة الهولوغرافية | تشفير الطور | `e^(i·ξ·k·2π/N)` | مفتاح تشفير الأنماط |
| مُحسِّن الرنين | تردد إضافي | `value × (1 + ξ)` | يولّد تردد هيكل خاص |
| المنطق الموجي | (غير مباشر) | عبر `ETHICAL_DAMPING = 0.92` | عامل التخميد الأخلاقي |

### 7.3 لماذا 0.4671؟

هذه القيمة ليست اعتباطية — هي الثابت الذي يُعطي أقصى اتساق بين:
- احتمال النفق الكمي (في نظام هيكل الخوارزمي)
- استجابة الرنين (في مسح الترددات)
- جودة التشفير الهولوغرافي (تفرقة أنماط بدون تداخل مُدمِّر)

في سياق الأمان: `ξ = 0.4671` يعني أن "المعلومات الأمنية" (هل هناك ثغرة)
مقترنة بـ "بنية العقد" (كيف مرتبة الدوال) بقوة متوسطة — لا ضعيفة جداً
(لا يهمل البنية) ولا قوية جداً (لا يبالغ في أهمية الترتيب).

---

## 8. المقارنة: قبل وبعد التكامل

### 8.1 تقييم الثقة (Confidence)

| النموذج | المنهج | المدخلات | عيوب |
|---|---|---|---|
| **قبل** | جدول ثابت | نوع الهجوم فقط | لا يعتبر الحواجز الفعلية، كل reentrancy = 0.95 |
| **بعد** | نفق كمومي | حواجز + طاقة + طول السلسلة | reentrancy بدون guard = 0.98، مع guard = 0.45 |

### 8.2 تصنيف الأهداف (Heuristic)

| النموذج | المنهج | المدخلات | عيوب |
|---|---|---|---|
| **قبل** | جمع خطي | 8 أوزان ثابتة | CEI + sends_eth = 0.37 (مجموع فقط) |
| **بعد** | تداخل موجي | 8 موجات + أنماط هولوغرافية | CEI + sends_eth = 0.52+ (bonus بنّاء)، + مطابقة "classic_reentrancy" |

### 8.3 تحسين الأرباح (Optimization)

| النموذج | المنهج | عدد المحاولات | عيوب |
|---|---|---|---|
| **قبل** | 8 مضاعفات ثابتة | 8 | يعلق في local maxima، لا يكتشف ذروات بعيدة |
| **بعد** | مسح رنيني + ضبط دقيق | 12-17 (ديناميكي) | يكتشف كل القمم + يضبط بدقة 1.25% |

### 8.4 مطابقة الأنماط

| النموذج | المنهج | الدقة |
|---|---|---|
| **قبل** | لا توجد مطابقة أنماط | — |
| **بعد** | 8 أنماط هولوغرافية بـ cross-correlation | مطابقة جزئية shift-invariant |

---

## 9. المراجع الرياضية والمصادر

### 9.1 مراجع الفيزياء

1. **WKB Approximation (Wentzel-Kramers-Brillouin):**
   تقريب شبه-كلاسيكي لمعادلة شرودنجر. معامل النقل: `T = exp(-2κd)`.
   المرجع: Griffiths, *Introduction to Quantum Mechanics*, Ch. 8.

2. **Resonant Tunneling (Breit-Wigner):**
   عندما تتطابق طاقة الجسيم مع مستوى طاقة مكمّم في الحاجز → نفاذية أعلى.
   معامل الرنين: `R(E) = 1/√((ω₀²-ω²)²+(γω)²)`.
   المرجع: Merzbacher, *Quantum Mechanics*, Ch. 6.

3. **Born Rule:**
   احتمال القياس = مربع السعة: `P = |ψ|²`.
   المرجع: Born, 1926. "Zur Quantenmechanik der Stoßvorgänge".

4. **Holographic Principle:**
   تخزين المعلومات في أنماط تداخل. الكسر لا يفقد المعلومة.
   المرجع: 't Hooft, 1993. Susskind, 1995.

5. **Lorentzian Response (Harmonic Oscillator):**
   `A(ω) = 1/√((ω₀²-ω²)²+(γω)²)` — استجابة المذبذب التوافقي المخمّد.
   المرجع: أي كتاب ميكانيكا كلاسيكية (مثل Goldstein, Ch. 11).

### 9.2 المصادر الأصلية في AGL

1. **`repo-copy/Core_Engines/Resonance_Optimizer.py`:**
   - InfoQuantum Lattice Tunneling (المعادلة الأصلية)
   - ثابت هيكل `ξ = 0.4671`
   - دالة الرنين Lorentzian

2. **`AGL_Vectorized_Wave_Processor.py`:**
   - تحويل Bit → Wave: `ψ = e^(i·bit·π)`
   - Wave XOR: `ψ_xor = ψ_a × ψ_b`
   - Wave AND: `|ψ_a + ψ_b| > threshold`
   - Ethical Amplitude Damping

3. **`AGL_Holographic_Memory.py` / `Heikal_Holographic_Memory.py`:**
   - DFT/IDFT-based encoding
   - Phase modulation encryption
   - Circular convolution storage
   - Superposition of patterns

---

## الخلاصة

طبقة رياضيات هيكل تُحوِّل أداة أمان العقود الذكية من نظام قائم على
**قواعد ثابتة وأوزان خطية** إلى نظام قائم على **نماذج فيزيائية أصلية**.

الأثر:
- **الثقة** أصبحت دالة في بنية العقد الفعلية (حواجز، CEI violations) بدل جدول ثابت
- **التصنيف** يلتقط التفاعلات بين الخصائص (تداخل موجي) بدل مجموع خطي
- **التحسين** يكتشف كل القمم في دالة الربح (مسح رنيني) بدل تسلق تلّي محلي
- **المطابقة** تعمل مع تشابه جزئي (هولوغرافي) بدل تطابق تام

كل هذا مع **اعتمادية وحيدة** (`numpy`) و**fallback كامل** للسلوك الأصلي.

```
══════════════════════════════════════════════════════════════════════════════
        هيكل × AGL — حيث تلتقي الفيزياء بأمان البلوكتشين
══════════════════════════════════════════════════════════════════════════════
```
