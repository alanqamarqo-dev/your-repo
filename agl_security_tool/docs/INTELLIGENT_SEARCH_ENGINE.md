# Layer 4: Intelligent Economic Search Engine
# محرك البحث الاقتصادي الذكي — التوثيق التفصيلي الممل

---

## الفهرس

| # | القسم | الصفحة |
|---|-------|--------|
| 1 | [الفلسفة والمبرر](#1-الفلسفة-والمبرر) | لماذا Layer 4 |
| 2 | [المعادلة الأساسية](#2-المعادلة-الأساسية) | Search(ActionSpace) → Profit |
| 3 | [مشكلة الانفجار التوليفي](#3-مشكلة-الانفجار-التوليفي) | (20×10)^5 = 3.2×10¹³ |
| 4 | [الهندسة المعمارية](#4-الهندسة-المعمارية) | 4 مكونات + منسق |
| 5 | [البنية الملفية](#5-البنية-الملفية) | 7 ملفات / 3,465 سطر |
| 6 | [نماذج البيانات (models.py)](#6-نماذج-البيانات) | 4 enums + 8 dataclasses |
| 7 | [محرك الاستدلال (heuristic_prioritizer.py)](#7-محرك-الاستدلال) | أين نبدأ البحث |
| 8 | [كاشف الضعف الاقتصادي (weakness_detector.py)](#8-كاشف-الضعف-الاقتصادي) | 14 نوع ضعف |
| 9 | [محرك البحث الموجّه (guided_search.py)](#9-محرك-البحث-الموجّه) | 5 استراتيجيات |
| 10 | [محرك تدرج الربح (profit_gradient.py)](#10-محرك-تدرج-الربح) | Hill Climbing |
| 11 | [المنسق الرئيسي (engine.py)](#11-المنسق-الرئيسي) | Pipeline كامل |
| 12 | [Beam Search بالتفصيل](#12-beam-search-بالتفصيل) | العرض × العمق |
| 13 | [MCTS بالتفصيل](#13-mcts-بالتفصيل) | UCB1 + Rollout |
| 14 | [Evolutionary بالتفصيل](#14-evolutionary-بالتفصيل) | طفرة + تهجين + انتقاء |
| 15 | [Gradient Optimization بالتفصيل](#15-gradient-optimization-بالتفصيل) | Hill Climbing |
| 16 | [تدفق البيانات الكامل](#16-تدفق-البيانات-الكامل) | من Solidity إلى النتيجة |
| 17 | [التكامل مع الطبقات السابقة](#17-التكامل-مع-الطبقات-السابقة) | L1→L2→L3→L4 |
| 18 | [نتائج الاختبارات](#18-نتائج-الاختبارات) | 93/93 |
| 19 | [أمثلة استخدام](#19-أمثلة-استخدام) | كود حي |
| 20 | [المعادلات الرياضية](#20-المعادلات-الرياضية) | كل الصيغ |
| 21 | [ضبط الأداء](#21-ضبط-الأداء) | SearchConfig |
| 22 | [القيود والحدود](#22-القيود-والحدود) | ما لا يفعله |

---

## 1. الفلسفة والمبرر

### لماذا نحتاج Layer 4؟

```
Layer 1 = عيون ترى العقد (State Extraction)
Layer 2 = خريطة لكل الحركات الممكنة (Action Space)
Layer 3 = مخبر يختبر: "هل هذه الحركة مربحة؟" (Simulation)
Layer 4 = عقل يقرر: "أي الحركات أختبر أصلاً؟" (Search)
```

#### التشبيه:
- **Layer 1–3** = امتلاك **رادار قوي جداً** يرى كل شيء
- **Layer 4** = امتلاك **صاروخ ذكي** يصيب الهدف

**بدون Layer 4**: عندك رادار بلا صاروخ — ترى التهديدات لكن لا تصيبها بدقة.

### المبدأ الأساسي

الطبقات 1–3 تبني **فضاء الاحتمالات** (Action Space).
الطبقة 4 **تبحث في هذا الفضاء بذكاء** — لا بالقوة الغاشمة.

> لا يمكنك تجربة 3.2×10¹³ تسلسل.
> لكن يمكنك اختيار أذكى 500 تسلسل واختبار تلك فقط.
> هذا هو جوهر Layer 4.

---

## 2. المعادلة الأساسية

```
Search(ActionSpace) → Find profitable attack sequences
```

بشكل أدق:

```
Input:
    ActionSpace    ← من Layer 2 (كل الأفعال + الروابط + التصنيفات)
    SimulationFn   ← من Layer 3 (دالة تقيّم أي تسلسل → ربح)
    FinancialGraph ← من Layer 1 (الحالة الأولية)

Output:
    SearchResult {
        profitable_attacks: [{candidate_id, steps, profit, attack_type, severity}]
        weaknesses:         [{type, hint, entry/exit actions, estimated_profit}]
        targets:            [{function, score, reasons, tags}]
        stats:              {seeds, nodes, simulations, timing}
    }
```

### لماذا ليس Brute Force؟

| المقياس | Brute Force | Layer 4 |
|---------|-------------|---------|
| تسلسلات مختبرة | 3.2×10¹³ | ~500 |
| الوقت | ∞ | < 60 ثانية |
| الاستراتيجية | عشوائي | ذكي (Heuristic + MCTS + Beam + Evo) |
| النتيجة | نفسها (نظرياً) | أفضل 500 تسلسل الأكثر احتمالاً |

---

## 3. مشكلة الانفجار التوليفي

### الحساب

عقد ذكي نموذجي يحتوي:
- ~20 action (دالة قابلة للاستدعاء)
- ~10 variants لكل action (قيم مختلفة للمعامل)
- تسلسلات بعمق 5 خطوات كحد أقصى

$$\text{Total sequences} = (20 \times 10)^5 = 200^5 = 3.2 \times 10^{13}$$

**3.2 تريليون تسلسل** — مستحيل اختبارها كلها حتى لو كل اختبار استغرق 1ms.

$$\text{Time} = \frac{3.2 \times 10^{13} \times 1\text{ms}}{1000 \times 3600 \times 24 \times 365} \approx 1,015 \text{ سنة}$$

### الحل: ذكاء بدل قوة

```
بدل 3.2×10¹³ → اختبر 500 فقط
لكن: اختر الـ 500 الأذكى

كيف تختار الأذكى؟
    1. ابدأ حيث تفوح رائحة الأموال (Heuristics)
    2. ابحث عن نقاط ضعف اقتصادية (Weakness Detection)
    3. وسّع بذكاء (Beam/MCTS/Evolutionary Search)
    4. حسّن المعاملات (Profit Gradient)
```

---

## 4. الهندسة المعمارية

### الرسم البياني الكامل

```
                    ┌──────────────────────────────────────────────┐
                    │           SearchOrchestrator                 │
                    │              (engine.py)                     │
                    └──────┬───────────┬──────────┬───────────┬────┘
                           │           │          │           │
                    ┌──────▼──────┐ ┌──▼────────┐ │    ┌──────▼──────┐
                    │  Heuristic  │ │ Weakness  │ │    │   Profit    │
                    │ Prioritizer │ │ Detector  │ │    │  Gradient   │
                    └──────┬──────┘ └──┬────────┘ │    └──────▲──────┘
                           │           │          │           │
                           ▼           ▼          │           │
                    ┌──────────────────────┐      │           │
                    │     Seed Pool        │      │           │
                    │ (merged + deduped)   │      │           │
                    └──────────┬───────────┘      │           │
                               │                  │           │
                               ▼                  │           │
                    ┌──────────────────────┐       │           │
                    │   Guided Search      │───────┘           │
                    │  ┌─────┐ ┌──────┐   │                   │
                    │  │Beam │ │ MCTS │   │   simulate_fn     │
                    │  └─────┘ └──────┘   │ ◄─── Layer 3      │
                    │  ┌──────┐ ┌───────┐ │                   │
                    │  │ Evo  │ │Greedy │ │                   │
                    │  └──────┘ └───────┘ │                   │
                    └──────────┬──────────┘                   │
                               │                              │
                               │ candidates                   │
                               └──────────────────────────────┘
                                                    │
                                                    ▼
                                            ┌──────────────┐
                                            │ SearchResult │
                                            └──────────────┘
```

### تدفق البيانات

```
Step 1: Prioritizer.analyze(ActionSpace, Graph)
            → targets: List[HeuristicTarget]
            → heuristic_seeds: List[SearchSeed]

Step 2: WeaknessDetector.detect(ActionSpace, Graph)
            → weaknesses: List[EconomicWeakness]
            → weakness_seeds: List[SearchSeed]

Step 3: merge_seeds(heuristic_seeds + weakness_seeds)
            → all_seeds: List[SearchSeed]  (مرتبة + مزالة التكرار)

Step 4: GuidedSearch.search(seeds, ActionGraph, Actions, simulate_fn, State)
            → candidates: List[CandidateSequence]

Step 5: ProfitGradient.optimize(candidates, simulate_fn, State)
            → optimized_candidates: List[CandidateSequence]

Step 6: Build SearchResult
            → profitable_attacks, stats, timing
```

---

## 5. البنية الملفية

```
search_engine/
├── __init__.py                  # 65 سطر  — تصدير كل المكونات
├── models.py                    # 543 سطر — 4 enums + 8 dataclasses
├── heuristic_prioritizer.py     # 393 سطر — محرك الاستدلال
├── weakness_detector.py         # 769 سطر — 14 كاشف ضعف اقتصادي
├── guided_search.py             # 996 سطر — 5 استراتيجيات بحث
├── profit_gradient.py           # 367 سطر — Hill Climbing
└── engine.py                    # 332 سطر — المنسق الرئيسي
                                ───────────
                          المجموع: 3,465 سطر
```

| الملف | الأسطر | الفئات | الدوال | الغرض |
|-------|--------|--------|--------|-------|
| models.py | 543 | 0 classes, 4 enums, 8 dataclasses | 7 `to_dict()` + 1 `to_json()` + 1 `generate_seed_sequences()` | كل الهياكل |
| heuristic_prioritizer.py | 393 | 1 class | 7 methods | تحديد الأهداف |
| weakness_detector.py | 769 | 1 class | 17 methods (14 detectors) | كشف الضعف |
| guided_search.py | 996 | 1 class | 21 methods | البحث الموجّه |
| profit_gradient.py | 367 | 1 class | 8 methods | تحسين الربح |
| engine.py | 332 | 1 class | 8 methods | التنسيق |
| \_\_init\_\_.py | 65 | — | — | تصدير |

---

## 6. نماذج البيانات

### 6.1 الـ Enums (4 تعدادات)

#### WeaknessType — أنواع الضعف الاقتصادي (14 قيمة)

| القيمة | المعنى | الوصف |
|--------|--------|-------|
| `REENTRANCY_DRAIN` | سرقة بإعادة الدخول | CEI violation + sends ETH بدون guard |
| `PRICE_IMBALANCE` | اختلال سعري | Oracle + Swap = فرصة تلاعب |
| `INVARIANT_BREAK` | كسر الثابت | totalDeposits ≠ sum(deposits) |
| `UNDER_COLLATERALIZATION` | نقص الضمان | اقتراض بأقل من الضمان المطلوب |
| `LIQUIDITY_ASYMMETRY` | عدم تماثل السيولة | الإيداع سهل + السحب صعب (أو العكس) |
| `REWARD_MISPRICING` | خطأ تسعير المكافأة | المكافأة أعلى من تكلفة الإيداع |
| `ACCESS_LEAK` | تسريب الصلاحيات | دالة admin بدون onlyOwner |
| `ORACLE_STALENESS` | بيانات قديمة | Oracle بدون فحص حداثة |
| `ORACLE_MANIPULATION` | تلاعب بالأوراكل | Oracle + Flash Loan |
| `FLASH_LOAN_VECTOR` | متجه القرض الفلاش | Callback + تغيير حالة |
| `CROSS_FUNCTION_STATE` | حالة مشتركة بين الدوال | Shared state + ETH send |
| `DONATION_ATTACK` | هجوم التبرع | Direct transfer يغيّر exchange rate |
| `FIRST_DEPOSITOR` | هجوم أول مودع | أول مودع يتحكم بسعر الأسهم |
| `ROUNDING_ERROR` | خطأ تقريب | قسمة في ratio/rate/price |

#### SearchStrategy — استراتيجيات البحث (6 قيم)

| القيمة | المعنى | الوصف |
|--------|--------|-------|
| `BEAM_SEARCH` | بحث شعاعي | أفضل K مسارات فقط |
| `MCTS` | شجرة مونت كارلو | استكشاف + استغلال (UCB1) |
| `GREEDY_BEST_FIRST` | أفضل أولاً | دائماً وسّع الأعلى درجة |
| `EVOLUTIONARY` | تطوري | طفرة + تهجين + انتقاء |
| `GRADIENT_ASCENT` | صعود التدرج | Hill Climbing على المعاملات |
| `HYBRID` | هجين | **الافتراضي** — كل الاستراتيجيات معاً |

#### SeedSource — مصدر البذرة (6 قيم)

| القيمة | المعنى |
|--------|--------|
| `HEURISTIC` | من محرك الاستدلال |
| `WEAKNESS` | من كاشف الضعف |
| `LAYER2_PATH` | من مسارات Layer 2 (get_attack_paths) |
| `LAYER3_NEAR_MISS` | تسلسل كان قريباً من الربح |
| `MUTATION` | طفرة من تسلسل موجود |
| `GRADIENT` | من محرك التدرج |

#### NodeState — حالة عقدة البحث (6 قيم)

| القيمة | المعنى |
|--------|--------|
| `UNEXPLORED` | لم تُستكشف بعد |
| `EXPANDING` | يتم توسيعها |
| `EVALUATED` | تم تقييمها |
| `PROFITABLE` | مربحة! |
| `PRUNED` | تم تقليمها |
| `DEAD` | مستحيلة (revert) |

---

### 6.2 SearchConfig — إعدادات البحث

```python
@dataclass
class SearchConfig:
    # === Budget (الميزانية) ===
    max_sequences_to_test: int = 500         # حد أقصى للتسلسلات المُختبرة
    max_search_time_seconds: float = 60.0    # حد زمني بالثوان
    max_depth: int = 6                       # أقصى عمق تسلسل (عدد الخطوات)

    # === Beam Search ===
    beam_width: int = 10                     # عدد المسارات المحتفظ بها في كل عمق
    beam_depth: int = 5                      # عدد مرات التوسيع

    # === MCTS ===
    mcts_iterations: int = 200               # عدد تكرارات SELECT→EXPAND→ROLLOUT→BACKPROP
    mcts_exploration_weight: float = 1.414   # C في UCB1 = √2
    mcts_rollout_depth: int = 4              # عمق Rollout العشوائي

    # === Evolutionary ===
    population_size: int = 30                # حجم المجتمع الأولي
    generations: int = 20                    # عدد الأجيال
    mutation_rate: float = 0.3               # احتمال الطفرة (30%)
    crossover_rate: float = 0.5              # احتمال التهجين (50%)
    elite_count: int = 5                     # عدد المتفوقين المحتفظ بهم (Elitism)

    # === Gradient ===
    gradient_steps: int = 20                 # خطوات التحسين
    amount_step_pct: float = 0.1             # 10% تغيير لكل خطوة
    min_improvement_usd: float = 10.0        # أقل تحسن لاستمرار التدرج

    # === Pruning (التقليم) ===
    min_profit_threshold_usd: float = -500.0 # اقطع إذا الخسارة > $500
    prune_reverted_branches: bool = True     # اقطع فرع إذا أي خطوة فشلت
    max_gas_budget_usd: float = 1000.0       # ميزانية غاز قصوى

    # === Strategy ===
    strategy: SearchStrategy = SearchStrategy.HYBRID  # الافتراضي: هجين
    enable_gradient_optimization: bool = True         # تحسين المعاملات
    enable_weakness_seeding: bool = True               # بذور من الضعف
    enable_near_miss_mutation: bool = True              # طفرات من Near-Miss
```

### 6.3 HeuristicTarget — هدف عالي القيمة

```python
@dataclass
class HeuristicTarget:
    target_id: str                    # "Vault.withdraw"
    contract_name: str = ""           # "Vault"
    function_name: str = ""           # "withdraw"
    action_ids: List[str]             # ["Vault_withdraw_0", "Vault_withdraw_1"]

    # === Scoring ===
    score: float = 0.0                # 0.0–1.0 — أولوية الهدف
    reasons: List[str]                # ["CEI violation", "sends ETH", ...]
    tags: Set[str]                    # {"fund_mover", "cei_violation", "unguarded"}

    # === Features (خصائص مستخرجة) ===
    has_cei_violation: bool = False    # هل تنتهك CEI؟
    sends_eth: bool = False           # هل ترسل ETH؟
    reentrancy_guarded: bool = False  # هل محمية بـ nonReentrant؟
    requires_access: bool = False     # هل تحتاج صلاحية؟
    moves_funds: bool = False         # هل تحرّك أموال؟
    reads_oracle: bool = False        # هل تقرأ oracle؟
    estimated_value_at_risk: float    # تقدير $ للمخاطرة
```

### 6.4 EconomicWeakness — ضعف اقتصادي

```python
@dataclass
class EconomicWeakness:
    weakness_id: str                   # "reent_1"
    weakness_type: WeaknessType        # REENTRANCY_DRAIN
    severity: str = "medium"           # critical/high/medium/low
    confidence: float = 0.5            # 0.0–1.0

    # === الاستغلال ===
    exploit_hint: str = ""             # "Reentrancy: withdraw has CEI+ETH"
    exploit_hint_ar: str = ""          # "إعادة الدخول: withdraw ينتهك CEI"
    entry_actions: List[str]           # ["Vault_deposit_0"]
    exit_actions: List[str]            # ["Vault_withdraw_0"]
    auxiliary_actions: List[str]       # خطوات وسيطة

    # === التقدير الاقتصادي ===
    estimated_profit_usd: float = 0.0
    affected_variable: str = ""        # "balances"
    affected_contract: str = ""        # "Vault"
    invariant_expression: str = ""     # "sum(balances) == totalDeposits"

    # === سياق ===
    requires_flash_loan: bool = False
    requires_multiple_blocks: bool = False
    requires_price_manipulation: bool = False
```

**الدالة المهمة: `generate_seed_sequences()`**
```
ينتج بذرتين لكل ضعف:
    Seed 1: entry → exit (مباشر)
        لكل (entry, exit) في entry_actions × exit_actions

    Seed 2: entry → aux → exit (مع خطوة وسيطة)
        لكل (entry, aux, exit) في entry[:2] × aux[:2] × exit[:2]
        الربح المقدّر × 0.8
        الثقة × 0.9
```

### 6.5 SearchSeed — بذرة بحث

```python
@dataclass
class SearchSeed:
    seed_id: str                       # "reent_deposit_withdraw"
    source: SeedSource                 # HEURISTIC / WEAKNESS / LAYER2_PATH / ...
    action_sequence: List[str]         # ["deposit_0", "withdraw_0"]
    weakness_ref: str = ""             # reference إلى EconomicWeakness
    estimated_profit: float = 0.0      # تقدير
    priority: float = 0.5             # 0.0–1.0 — أولوية البذرة
    parameter_hints: Dict[str, Any]    # إرشادات للمعاملات
    notes: str = ""                    # ملاحظات
```

### 6.6 SearchNode — عقدة في شجرة البحث

```python
@dataclass
class SearchNode:
    node_id: str                       # "mcts_a1b2c3d4"
    parent_id: Optional[str] = None
    depth: int = 0
    state: NodeState = UNEXPLORED

    # === التسلسل ===
    sequence_so_far: List[str]         # ["deposit_0", "withdraw_0"]
    last_action: str = ""              # آخر فعل

    # === الدرجات ===
    profit_so_far_usd: float = 0.0     # ربح متراكم
    heuristic_score: float = 0.0       # تقييم إرشادي
    ucb_score: float = 0.0             # UCB1 score

    # === MCTS ===
    visits: int = 0                    # عدد الزيارات
    total_reward: float = 0.0          # مجموع المكافآت
    children: List[str]                # عقد أبناء

    # === تقليم ===
    is_terminal: bool = False
    pruned_reason: str = ""
    gas_used_so_far: int = 0

    @property
    average_reward → float:
        return total_reward / max(visits, 1)
```

### 6.7 CandidateSequence — تسلسل مرشح

```python
@dataclass
class CandidateSequence:
    candidate_id: str                   # "cand_a1b2c3d4"
    steps: List[Dict[str, Any]]         # step_info dicts (L2→L3 format)
    action_ids: List[str]               # ["deposit_0", "withdraw_0"]
    source: SeedSource                  # من أين جاء

    # === قبل المحاكاة ===
    estimated_profit_usd: float = 0.0
    priority_score: float = 0.0

    # === بعد المحاكاة (يملأها المحرك) ===
    simulated: bool = False
    actual_profit_usd: float = 0.0      # ← الربح الحقيقي من Layer 3
    simulation_success: bool = False
    attack_type: str = ""               # "reentrancy"
    severity: str = ""                  # "critical"

    # === بعد التحسين ===
    optimized: bool = False
    optimization_iterations: int = 0
    profit_before_optimization: float = 0.0
```

### 6.8 SearchStats — إحصائيات

```python
@dataclass
class SearchStats:
    # === البذور ===
    total_seeds: int = 0
    seeds_from_heuristic: int = 0
    seeds_from_weakness: int = 0
    seeds_from_layer2: int = 0
    seeds_from_near_miss: int = 0
    seeds_from_mutation: int = 0

    # === البحث ===
    nodes_explored: int = 0
    nodes_pruned: int = 0
    sequences_generated: int = 0
    sequences_simulated: int = 0        # ← عدد الاستدعاءات لـ Layer 3
    sequences_profitable: int = 0

    # === التحسين ===
    gradient_steps_taken: int = 0
    improved_by_gradient: int = 0
    total_improvement_usd: float = 0.0

    # === الأداء ===
    search_time_ms: float = 0.0
    simulation_time_ms: float = 0.0
    optimization_time_ms: float = 0.0
    total_time_ms: float = 0.0

    # === التفصيل حسب الاستراتيجية ===
    by_strategy: Dict[str, int]         # {"beam_search": 15, "mcts": 8, ...}
```

### 6.9 SearchResult — النتيجة النهائية

```python
@dataclass
class SearchResult:
    version: str = "1.0.0"

    # === الهجمات المربحة ===
    profitable_attacks: List[Dict]      # كل CandidateSequence.to_dict() المربحة
    total_profitable: int = 0
    total_profit_usd: float = 0.0
    best_profit_usd: float = 0.0

    # === المكتشفات ===
    weaknesses: List[EconomicWeakness]
    targets: List[HeuristicTarget]

    # === الإحصائيات ===
    seeds_generated: int = 0
    candidates_tested: int = 0
    candidates_profitable: int = 0
    stats: SearchStats

    # === أخطاء ===
    errors: List[str]
    warnings: List[str]
    execution_time_ms: float = 0.0
```

---

## 7. محرك الاستدلال

### heuristic_prioritizer.py — "أين نبدأ البحث أصلاً؟"

### 7.1 الفكرة

بدلاً من البحث عشوائياً في 20 دالة:
- **رتّب الدوال بالأولوية**
- **ابدأ بالدالة الأكثر خطورة**
- **أعطِ كل دالة درجة 0.0–1.0**

### 7.2 أوزان التقييم

```python
HEURISTIC_WEIGHTS = {
    "moves_funds":       0.25,    # الدالة تحرّك أموال ← أهم شيء
    "cei_violation":     0.20,    # CEI violation ← reentrancy vector
    "sends_eth":         0.15,    # ترسل ETH ← callback ممكن
    "no_access_control": 0.12,    # أي شخص يستدعيها
    "not_guarded":       0.10,    # لا يوجد nonReentrant
    "reads_oracle":      0.08,    # تعتمد على oracle ← manipulation
    "has_state_conflict": 0.05,   # conflict مع دالة أخرى
    "modifies_balances": 0.05,    # تغير أرصدة
}
```

### 7.3 معادلة التقييم

$$\text{score} = \sum_{i} w_i \cdot \mathbb{1}[\text{feature}_i]$$

مع إضافات خاصة:

$$\text{score} += 0.03 \quad \text{if external\_calls}$$

$$\text{score} += 0.15 \quad \text{if CEI} \wedge \text{sends\_ETH} \wedge \neg\text{guarded} \quad \text{(الكنز)}$$

مع عقوبة:

$$\text{if requires\_access: } \text{score} \times= 0.3$$

$$\text{score} = \min(\text{score}, 1.0)$$

### 7.4 مثال حي: Vault.withdraw

| الخاصية | الحالة | الوزن |
|---------|--------|-------|
| moves_funds | ✅ (fund_outflow) | +0.25 |
| cei_violation | ✅ | +0.20 |
| sends_eth | ✅ | +0.15 |
| no_access_control | ✅ (public) | +0.12 |
| not_guarded | ✅ (no nonReentrant) | +0.10 |
| external_calls | ✅ (msg.sender.call) | +0.03 |
| **الكنز bonus** | ✅ (CEI+ETH+!guard) | +0.15 |
| **المجموع** | | **1.00** (capped) |

### 7.5 استراتيجيات توليد البذور

| # | الاستراتيجية | الأولوية | الربح المقدر | الشرط |
|---|-------------|---------|------------|-------|
| 1 | **Reentrancy** | 0.95 | $100,000 | CEI + ETH + !guard + inflow exists on same contract |
| 2 | **Drain** | 0.70 | $10,000 | inflow → outflow على نفس العقد |
| 3 | **Graph Path** | 0.60 | $5,000 | من `ActionGraph.get_attack_paths()` |
| 4 | **Target Explore** | score | estimated_var | أعلى 5 targets مع score ≥ 0.5 |

### 7.6 التاغات (Tags)

| Tag | المعنى | مصدر |
|-----|--------|------|
| `fund_mover` | تحرّك أموال | category ∈ {fund_inflow, fund_outflow, borrow, swap, ...} |
| `cei_violation` | CEI violation | action.has_cei_violation |
| `sends_eth` | ترسل ETH | action.sends_eth |
| `unguarded` | بدون حماية | !reentrancy_guarded && (sends_eth \|\| cei) |
| `public` | أي شخص يستدعيها | !requires_access |
| `restricted` | تحتاج صلاحية | requires_access |
| `oracle_dependent` | تعتمد على oracle | state_reads contains oracle/price/feed |
| `external_calls` | استدعاءات خارجية | action.external_calls not empty |
| `flow_linked` | مرتبطة بتدفق أموال | من FinancialGraph.fund_flows |
| `category:X` | فئة الفعل | من ActionCategory |
| `attack:X` | نوع الهجوم المحتمل | من AttackType |

---

## 8. كاشف الضعف الاقتصادي

### weakness_detector.py — "ما نقاط الضعف الاقتصادية؟"

### 8.1 الفكرة

لا يبحث هذا المكوّن عن bugs عادية.
يبحث عن **نقاط ضعف اقتصادية** يمكن استغلالها لتحقيق ربح.

الفرق:
```
Bug عادي:    array out of bounds → revert
ضعف اقتصادي: deposit → withdraw × 3 لأن CEI violation → $300K profit
```

### 8.2 تصنيف الأفعال (17 فئة)

قبل أي كشف، يصنّف الكاشف كل الأفعال إلى 17 قائمة:

| الفئة | المصدر | الاستخدام |
|-------|--------|----------|
| `inflows` | category == fund_inflow | كل كاشف reentrancy/drain |
| `outflows` | category == fund_outflow | كل كاشف drain |
| `borrows` | category == borrow | under_collateralization |
| `repays` | category == repay | — |
| `swaps` | category == swap | price_imbalance |
| `claims` | category == claim | reward_mispricing |
| `oracles` | category == oracle_update | oracle_manipulation |
| `admins` | category == admin | access_leak |
| `flash_loans` | category == flash_loan | flash_loan_vector |
| `stakes` | category == stake | reward_mispricing |
| `unstakes` | category == unstake | — |
| `views` | category == view | (مستثناة) |
| `cei_violators` | has_cei_violation | reentrancy_drain |
| `eth_senders` | sends_eth | reentrancy_drain, cross_function |
| `unguarded` | !reentrancy_guarded | reentrancy_drain |
| `public` | !requires_access | access_leak, most detectors |
| `state_changers` | category ≠ view | flash_loan_vector |

### 8.3 الكاشفات الـ 14 (تفصيل كامل)

---

#### 8.3.1 REENTRANCY_DRAIN — الأخطر

```
الشرط المثالي (critical, confidence 0.9):
    action ∈ cei_violators ∩ eth_senders ∩ unguarded

الشرط الأقل (medium, confidence 0.4):
    action ∈ (cei_violators ∩ eth_senders) − prime_targets
    أي: لديها guard لكن ربما cross-function

الناتج:
    entry_actions: inflows على نفس العقد ∩ public
    exit_actions: [vulnerable action]
    estimated_profit: $100,000 (critical) / $20,000 (medium)
```

---

#### 8.3.2 INVARIANT_BREAK — كسر الثابت

```
المنطق:
    لكل عقد: اجمع كل state_writes وstate_reads
    ابحث عن shared = writes ∩ reads
    فلتر: الأسماء التي تحتوي balance/deposit/supply/total/reserve/amount

الناتج:
    مثال: "Shared balance variables in Pool: ['balances', 'totalDeposits']"
    invariant_expression: "sum(balances) == totalDeposits"
    estimated_profit: $50,000
```

---

#### 8.3.3 ACCESS_LEAK — تسريب الصلاحيات

```
الشرط:
    action ∈ admins ∩ public
    أي: دالة admin يمكن لأي شخص استدعاؤها!

الخطورة: critical, confidence 0.85
الربح المقدر: $500,000 (يمكن تغيير المالك)
```

---

#### 8.3.4 CROSS_FUNCTION_STATE — حالة مشتركة بين الدوال

```
المنطق:
    لكل عقد → لكل زوج دوال public:
        if state_writes(f1) ∩ state_reads(f2) ≠ ∅:
            if f1 ∈ eth_senders OR f2 ∈ eth_senders:
                → CROSS_FUNCTION_STATE weakness

الفكرة: دالة تكتب متغير، ودالة أخرى تقرأه وترسل ETH
    = reentrancy عبر الدوال (cross-function reentrancy)
```

---

#### 8.3.5 ORACLE_MANIPULATION — تلاعب بالأوراكل

```
الشرط:
    action reads oracle (state_reads contains oracle/price/feed)
    AND flash_loans not empty

الفكرة: flash loan → تلاعب بالسعر → استغلال الدالة → سداد القرض
estimated_profit: $200,000
```

---

#### 8.3.6 FLASH_LOAN_VECTOR — متجه القرض الفلاش

```
الشرط:
    flash_loan action exists on contract
    AND state_changers on same contract ∩ public

الفكرة: Flash loan callback يسمح باستدعاء دوال تغيير الحالة
estimated_profit: $150,000
```

---

#### 8.3.7 LIQUIDITY ASYMMETRY — عدم تماثل السيولة

```
السيناريوهات:
    1. inflows exist + NO outflows → أموال عالقة (medium)
    2. outflows exist (public) + NO inflows → سحب بلا إيداع! (high, $50K)
```

---

#### 8.3.8 DONATION_ATTACK — هجوم التبرع

```
الشرط:
    العقد يستخدم shares/totalSupply
    AND العقد يقرأ balance/reserve/totalAssets

الفكرة: تحويل مباشر للعقد يغيّر exchange rate
estimated_profit: $30,000
```

---

#### 8.3.9 FIRST_DEPOSITOR — أول مودع

```
الشرط:
    inflow action touches totalSupply/supply/shares/ratio/rate/price/exchange

الفكرة: أول مودع يتحكم بسعر الأسهم
estimated_profit: $10,000
```

---

#### 8.3.10 ROUNDING_ERROR — خطأ تقريب

```
الشرط:
    public fund action (inflow/outflow/swap/claim)
    state vars contain ratio/rate/price/pershare/exchange

estimated_profit: $5,000 (عادة صغير)
```

---

#### 8.3.11–14 الباقي

| # | النوع | الشرط | الخطورة | الثقة |
|---|-------|-------|---------|-------|
| 11 | REWARD_MISPRICING | claim + (stake\|inflow) same contract | medium | 0.40 |
| 12 | PRICE_IMBALANCE | swap + oracle same contract | high | 0.55 |
| 13 | UNDER_COLLATERALIZATION | public borrow | high | 0.45 |
| 14 | ORACLE_STALENESS | oracle read without timestamp check | medium | 0.50 |

---

## 9. محرك البحث الموجّه

### guided_search.py — "القلب الذكي"

### 9.1 الفكرة الجوهرية

```
لديك بذور (seeds) = نقاط بداية واعدة
لديك ActionGraph = خريطة الأفعال + الروابط
لديك simulate_fn = دالة تقيّم أي تسلسل → ربح

المهمة: ابحث من البذور عبر الروابط عن أفضل تسلسل مربح
```

### 9.2 واجهة الاستخدام

```python
engine = GuidedSearchEngine(config)
candidates = engine.search(
    seeds=all_seeds,          # بذور من الخطوة السابقة
    action_graph=graph,       # Layer 2 ActionGraph
    actions=actions_dict,     # {action_id → Action}
    simulate_fn=sim_fn,       # Layer 3 simulate_sequence
    initial_state=state,      # Layer 3 ProtocolState
)
# candidates: List[CandidateSequence] مرتبة بالربح
```

### 9.3 الاستراتيجيات الخمسة

| # | الاستراتيجية | السرعة | العمق | التنوع | متى تستخدم |
|---|-------------|--------|--------|--------|-----------|
| 1 | Beam | ⚡⚡⚡ | ◉◉◉ | ◉ | تسلسلات مركّزة وعميقة |
| 2 | MCTS | ⚡⚡ | ◉◉◉◉ | ◉◉◉ | استكشاف عميق مع توازن |
| 3 | Evolutionary | ⚡ | ◉◉ | ◉◉◉◉ | تنويع وابتكار تسلسلات جديدة |
| 4 | Greedy | ⚡⚡⚡⚡ | ◉◉ | ◉ | نتائج أولية سريعة |
| 5 | Hybrid | ⚡⚡ | ◉◉◉◉ | ◉◉◉◉ | **الأفضل — يستخدم الكل** |

---

## 10. محرك تدرج الربح

### profit_gradient.py — "حسّن المعاملات"

### 10.1 الفكرة

بعد أن وجدت تسلسلاً واعداً:
```
deposit(1 ETH) → withdraw() → profit = $50,000
```

هل يمكنك الحصول على أكثر بتغيير المبلغ؟
```
deposit(10 ETH) → withdraw() → profit = $500,000?
deposit(0.1 ETH) → withdraw() → profit = $5,000?
```

### 10.2 الخوارزمية

```
Hill Climbing on profit(θ)
θ = {msg_value, concrete_values for is_amount params}

for each step in sequence:
    for each θ_dimension:
        try θ × multiplier  for multiplier in [1.1, 0.9, 2, 5, 10, 0.5, 0.1, 0.01]
        if profit(θ_new) > profit(θ_old) + min_improvement:
            accept θ_new
```

### 10.3 المضاعفات المُجرَّبة

| لـ msg_value | لـ parameter amounts |
|-------------|---------------------|
| × 1.1 (+ 10%) | × 1.5 |
| × 0.9 (- 10%) | × 2.0 |
| × 2.0 | × 5.0 |
| × 5.0 | × 0.5 |
| × 10.0 | × 0.1 |
| × 0.5 | |
| × 0.1 | |
| × 0.01 | |

### 10.4 شروط القبول

```python
if new_profit > old_profit + min_improvement_usd:  # $10 default
    accept new parameters
else:
    keep old parameters
```

### 10.5 شروط التحسين

- يُحسّن فقط التسلسلات مع `actual_profit_usd > -200`
- يُحسّن أعلى 20 مرشح فقط (لتجنب timeout)
- يتتبع عدد التحسينات وإجمالي التحسّن بالدولار

---

## 11. المنسق الرئيسي

### engine.py — SearchOrchestrator

### 11.1 Pipeline كامل (7 خطوات)

```python
def search(graph, action_space, attack_engine) → SearchResult:

    # Step 1: Validate
    if no action_space/engine/graph/actions → error

    # Step 2: Load State
    initial_state = attack_engine.state_loader.load_from_graph(graph)

    # Step 3: Heuristic Prioritization
    targets, h_seeds = prioritizer.analyze(action_space, graph)

    # Step 4: Weakness Detection
    weaknesses, w_seeds = weakness_detector.detect(action_space, graph)

    # Step 5: Merge Seeds
    all_seeds = merge(h_seeds + w_seeds)  # dedup + sort by priority

    # Step 6: Guided Search
    candidates = search_engine.search(all_seeds, graph, actions, sim_fn, state)

    # Step 7: Gradient Optimization (if enabled)
    if enable_gradient:
        promising = [c for c in candidates if profit > -$200][:20]
        optimized = gradient_engine.optimize(promising, sim_fn, state)
        candidates = optimized + rest

    # Build Result
    return SearchResult(profitable_attacks, weaknesses, targets, stats)
```

### 11.2 التوقيت المستقل

```
total_time = t(prioritizer) + t(weakness) + t(search) + t(gradient)

stats.search_time_ms       ← الوقت الفعلي للبحث
stats.simulation_time_ms   ← الوقت المستهلك في Layer 3
stats.optimization_time_ms ← الوقت المستهلك في Gradient
stats.total_time_ms        ← الكل
```

---

## 12. Beam Search بالتفصيل

### الخوارزمية

```
beam_width = K (عدد المسارات المحتفظ بها)
beam_depth = D (عدد مرات التوسيع)

beams = convert seeds to initial sequences

for depth = 0 to D-1:
    next_beams = []
    for each (sequence, score) in beams:
        # 1. Evaluate current sequence
        candidate = simulate(sequence)

        # 2. Expand: get successors of last action
        for succ in get_successors(sequence[-1]):
            if succ not in sequence:  # avoid cycles
                new_seq = sequence + [succ]
                h = heuristic_score(new_seq)
                next_beams.append((new_seq, h))

    # 3. Prune: keep only top K
    next_beams.sort(by score, descending)
    beams = next_beams[:K]

# Evaluate remaining beams
for beam in beams:
    simulate(beam)
```

### مثال مرئي

```
seed: [deposit, withdraw]    score=0.9

Depth 0: expand withdraw's successors
    [deposit, withdraw, deposit]   score=0.7  ← cycle, skip
    → keep [deposit, withdraw]

Depth 1: evaluate and expand
    [deposit, withdraw] → simulate → profit=$50K

width=5 means: at each depth, keep only 5 best
```

---

## 13. MCTS بالتفصيل

### معادلة UCB1

$$UCB1_i = \bar{x}_i + C \cdot \sqrt{\frac{\ln N}{n_i}}$$

حيث:
- $\bar{x}_i$ = متوسط المكافأة للعقدة $i$ (exploitation)
- $C$ = ثابت الاستكشاف = $\sqrt{2} \approx 1.414$
- $N$ = عدد زيارات الأب
- $n_i$ = عدد زيارات العقدة $i$
- الحد الثاني = exploration bonus (يتناقص مع الزيارات)

### الحلقة الرباعية

```
for iteration = 1 to 200:

    1. SELECT: ابدأ من الجذر، اتبع UCB1 حتى تصل لورقة
        while node.children and node.state != DEAD:
            node = argmax(child.ucb_score for child in node.children)
        if any child.visits == 0: return that child  ← unexplored first

    2. EXPAND: أضف أبناء (successor actions)
        for succ in get_successors(node.last_action):
            if succ not in node.sequence:
                create child node with sequence + [succ]
        return random unexplored child

    3. ROLLOUT: العب عشوائياً حتى عمق 4
        seq = node.sequence
        for _ in range(rollout_depth):
            succs = get_successors(seq[-1])
            valid = [s for s in succs if s not in seq]
            if not valid: break
            seq.append(random.choice(valid))
        reward = simulate(seq).profit

    4. BACKPROPAGATE: حدّث إحصائيات الآباء
        current = node
        while current:
            current.visits += 1
            current.total_reward += reward
            if reward > current.profit_so_far:
                current.profit_so_far = reward
                current.state = PROFITABLE
            current = current.parent
```

### مثال مرئي

```
                    root (visits=50)
                   /            \
            seed_s1 (v=30)    seed_s2 (v=20)
           /       \             \
       mcts_a (v=15) mcts_b(v=15) mcts_c(v=20)
         UCB=3.2      UCB=2.8        UCB=4.1 ← SELECT this

    UCB(mcts_c) = 80000/20 + 1.414 × √(ln(50)/20)
                = 4000 + 1.414 × √(3.91/20)
                = 4000 + 1.414 × 0.442
                = 4000.63
    (simplified — actual is normalized reward)
```

---

## 14. Evolutionary بالتفصيل

### الخوارزمية

```
population = initialize from seeds (+ random fill to pop_size=30)

for generation = 1 to 20:

    1. EVALUATE fitness:
        for each individual in population:
            fitness = simulate(individual).profit

    2. SORT by fitness (descending)

    3. ELITISM: keep top 5

    4. BREED until population full:
        if random < crossover_rate (0.5):
            parent1 = tournament_select(k=3)
            parent2 = tournament_select(k=3)
            child = crossover(parent1, parent2)
        else:
            child = tournament_select(k=3)

        if random < mutation_rate (0.3):
            child = mutate(child)

        add child to next generation
```

### التهجين (Crossover)

```
parent1:  [A, B, C, D]
parent2:  [E, F, G, H]

Single-point crossover:
    cut1 = random(1..3) → e.g., 2
    cut2 = random(1..3) → e.g., 1

    child = parent1[:2] + parent2[1:]
          = [A, B] + [F, G, H]
          = [A, B, F, G, H]

Deduplicate (keep first occurrence)
Cap at max_depth
```

### الطفرة (Mutation)

| النوع | الشرح | المثال |
|-------|-------|--------|
| **insert** | أدخل successor لعنصر عشوائي | [A, B] → [A, **C**, B] |
| **delete** | احذف عنصر عشوائي | [A, B, C] → [A, C] |
| **swap** | بدّل موقع عنصرين | [A, B, C] → [C, B, A] |
| **replace** | استبدل عنصر بآخر عشوائي | [A, B, C] → [A, **X**, C] |

### Tournament Selection

```
Pick 3 random individuals
Return the one with highest fitness

لماذا 3 وليس 2؟
    → selection pressure معتدل
    → أقوى من random (2)
    → لكن ليس elitist (all)
```

---

## 15. Gradient Optimization بالتفصيل

### العملية

```
لكل candidate (profit > -$200):
    لكل step في التسلسل:

        # === تحسين msg_value ===
        original_value = step.msg_value (أو 1 ETH إذا كان 0)
        لكل multiplier في [1.1, 0.9, 2, 5, 10, 0.5, 0.1, 0.01]:
            new_value = original × multiplier
            new_profit = simulate(modified_candidate)
            if new_profit > best_profit + $10:
                accept!

        # === تحسين parameter amounts ===
        لكل param مع is_amount=True:
            لكل concrete_value:
                لكل multiplier في [1.5, 2, 5, 0.5, 0.1]:
                    new_value = original × multiplier
                    new_profit = simulate(modified_candidate)
                    if new_profit > best_profit + $10:
                        accept!

    إذا تم أي تحسين:
        candidate.optimized = True
        candidate.optimization_iterations = count
```

### مثال

```
قبل التحسين:
    deposit(1 ETH) → withdraw() → profit = $50,000

المحرك يجرب:
    deposit(1.1 ETH) → withdraw() → profit = $52,000  ← تحسن!
    deposit(2 ETH) → withdraw() → profit = $98,000    ← أفضل! ✓
    deposit(5 ETH) → withdraw() → profit = $45,000    ← أسوأ (pool أصغر)
    deposit(10 ETH) → withdraw() → profit = $30,000   ← أسوأ

النتيجة:
    deposit(2 ETH) → withdraw() → profit = $98,000
    تحسّن: +$48,000
```

---

## 16. تدفق البيانات الكامل

### من Solidity إلى SearchResult

```
contract.sol
    │
    ▼ Parser
ParsedContract[]
    │
    ▼ Layer 1: State Extraction (9 steps)
FinancialGraph {entities, flows, balances, temporal_analysis}
    │
    ▼ Layer 2: Action Space Builder
ActionSpace {graph: ActionGraph {actions, edges}, attack_sequences}
    │
    ▼ Layer 3: Attack Simulation
SimulationSummary {profitable_attacks, best_attack}
    │
    ▼ Layer 4: Search Engine (7 steps)
    │
    ├─ Step 1: Load ProtocolState from FinancialGraph
    │
    ├─ Step 2: HeuristicPrioritizer.analyze(ActionSpace)
    │   → targets: [{Vault.withdraw: score=1.0, "CEI+ETH+!guard"}]
    │   → seeds: [{deposit→withdraw, priority=0.95}]
    │
    ├─ Step 3: WeaknessDetector.detect(ActionSpace)
    │   → weaknesses: [{REENTRANCY_DRAIN, critical, conf=0.9}]
    │   → seeds: [{deposit→withdraw, source=weakness}]
    │
    ├─ Step 4: merge_seeds → 15 unique seeds
    │
    ├─ Step 5: GuidedSearch.search(seeds)
    │   ├── Greedy (10% budget) → 3 candidates
    │   ├── Beam (40% budget) → 12 candidates
    │   ├── MCTS (30% budget) → 8 candidates
    │   └── Evolutionary (20% budget) → 7 candidates
    │   → 25 unique candidates (after dedup)
    │
    ├─ Step 6: ProfitGradient.optimize(top 20)
    │   → 3 improved by gradient
    │   → total improvement: +$48,000
    │
    └─ Step 7: Build SearchResult
        → profitable_attacks: 5
        → best_profit: $98,000
        → total_profit: $250,000
        → execution_time: 3.2s
```

### أنواع البيانات عبر الطبقات

```
Layer 2 Action
    ↓ _action_to_step()
step_info dict {action_id, function_name, category, parameters, ...}
    ↓ simulate_fn()
Layer 3 AttackResult {net_profit_usd, is_profitable, attack_type, severity}
    ↓ fill candidate
CandidateSequence {actual_profit_usd, attack_type, severity}
    ↓ to_dict()
SearchResult.profitable_attacks: List[Dict]
```

---

## 17. التكامل مع الطبقات السابقة

### 17.1 التغييرات في state_extraction/engine.py

```python
# Version bumped: 4.0.0 → 5.0.0

# === New import ===
from search_engine import SearchOrchestrator

# === New init ===
self._search_engine = SearchOrchestrator(config)

# === New Step 10 ===
# ─── Step 10: Intelligent Search (Layer 4) ───
if self._search_engine and self._attack_engine and graph.action_space:
    search_result = self._search_engine.search(
        graph, graph.action_space, self._attack_engine
    )
    graph.search_results = search_result
```

### 17.2 التغييرات في state_extraction/models.py

```python
# New field in FinancialGraph:
search_results: Optional[Any] = None  # SearchResult from search_engine

# New in to_dict():
"search_results": self.search_results.to_dict() if self.search_results ...
```

### 17.3 التغييرات في state_extraction/\_\_init\_\_.py

```python
__version__ = "5.0.0"

# === Layer 4: Search Engine ===
from search_engine import SearchOrchestrator

__all__ = [..., "SearchOrchestrator"]
```

### 17.4 Pipeline الكامل (12 خطوة)

| Step | Module | Layer | الوظيفة |
|------|--------|-------|---------|
| 1 | EntityExtractor | L1 | استخلاص الكيانات |
| 2 | RelationshipMapper | L1 | رسم العلاقات |
| 3 | FundMapper | L1 | خريطة الأموال |
| 4 | FinancialGraphBuilder | L1 | بناء الرسم البياني |
| 5 | ConsistencyValidator | L1 | التحقق من التناسق |
| 6 | ExecutionSemanticsExtractor | L1 | ترتيب العمليات |
| 7a-d | Dynamic State Transition | L1 | التبعيات الزمنية |
| 8 | ActionSpaceBuilder | L2 | فضاء الأفعال |
| 9 | AttackSimulationEngine | L3 | محاكاة الهجوم |
| **10** | **SearchOrchestrator** | **L4** | **البحث الذكي** |

---

## 18. نتائج الاختبارات

### 93/93 اختبار — كلها نجحت

| المجموعة | الاختبارات | النتيجة |
|---------|-----------|--------|
| 1. Models | 22 | ✅ 22/22 |
| 2. Heuristic Prioritizer | 15 | ✅ 15/15 |
| 3. Weakness Detector | 14 | ✅ 14/14 |
| 4. Guided Search | 16 | ✅ 16/16 |
| 5. Profit Gradient | 4 | ✅ 4/4 |
| 6. Search Orchestrator | 16 | ✅ 16/16 |
| 7. Integration | 6 | ✅ 6/6 |

### تفصيل اختبارات المكونات

#### Models (22 test)
- WeaknessType has 14 values
- SearchStrategy has 6 values
- SearchConfig defaults (500, 10, 200, 30)
- HeuristicTarget to_dict (score, tags)
- EconomicWeakness generates seeds (entry→exit, entry→aux→exit)
- SearchSeed, SearchNode, CandidateSequence, SearchStats, SearchResult to_dict/to_json

#### Heuristic Prioritizer (15 tests)
- None input → empty
- Vault: finds targets, withdraw is target, has CEI tag, sends ETH
- Score > 0.7, has reasons, NOT guarded, top target
- Admin deprioritized
- Seeds generated (reentrancy seeds)
- DeFi scenario targets + seeds
- Works with FinancialGraph

#### Weakness Detector (14 tests)
- None input → empty
- REENTRANCY_DRAIN: detected, critical, confidence > 0.8, entry/exit actions
- Seeds from weaknesses
- DeFi: invariant break, flash loan vector detected
- ACCESS_LEAK: detected
- Critical first ordering

#### Guided Search (16 tests)
- Beam: candidates, some profitable, stats
- MCTS: candidates, stats (nodes explored)
- Evolutionary: candidates
- Greedy: candidates, sorted order
- Hybrid: candidates, by_strategy has "hybrid"
- Empty seeds → empty results
- Heuristic scoring: CEI + ETH → high score
- Action to step conversion (4 field checks)

#### Profit Gradient (4 tests)
- Optimized list returned
- Candidate optimized or unchanged
- Very unprofitable left as-is (< -$200)
- Non-simulated passed through

#### Search Orchestrator (16 tests)
- Returns SearchResult, version 1.0.0
- Stats populated, targets found, weaknesses found
- Seeds generated, candidates tested
- None inputs → errors
- Empty actions → error
- to_json works
- DeFi results, execution time tracked
- With gradient: completes, optimization time tracked

#### Integration (6 tests)
- All 5 components importable
- search_engine version 1.0.0
- Main engine version 5.0.0
- FinancialGraph has search_results field (defaults to None)
- SearchOrchestrator in \_\_all\_\_

---

## 19. أمثلة استخدام

### 19.1 استخدام مباشر

```python
from agl_security_tool.search_engine import SearchOrchestrator

# إنشاء المنسق
orchestrator = SearchOrchestrator({
    "max_search_time_seconds": 30,
    "max_sequences_to_test": 200,
    "strategy": "hybrid",
    "enable_gradient_optimization": True,
})

# تشغيل البحث
result = orchestrator.search(
    graph=financial_graph,        # من Layer 1
    action_space=action_space,    # من Layer 2
    attack_engine=attack_engine,  # من Layer 3
)

# النتائج
print(f"هجمات مربحة: {result.total_profitable}")
print(f"أفضل ربح: ${result.best_profit_usd:,.2f}")

for attack in result.profitable_attacks:
    print(f"  {attack['attack_type']}: ${attack['actual_profit_usd']:,.2f}")
```

### 19.2 استخدام المكونات منفصلة

```python
from agl_security_tool.search_engine import (
    HeuristicPrioritizer,
    EconomicWeaknessDetector,
    GuidedSearchEngine,
    ProfitGradientEngine,
    SearchConfig, SearchStrategy,
)

# 1. تحديد الأهداف
prioritizer = HeuristicPrioritizer()
targets, h_seeds = prioritizer.analyze(action_space, graph)

for t in targets[:3]:
    print(f"{t.target_id}: score={t.score:.2f}, reasons={t.reasons}")

# 2. كشف الضعف
detector = EconomicWeaknessDetector()
weaknesses, w_seeds = detector.detect(action_space, graph)

for w in weaknesses:
    print(f"{w.weakness_type.value}: {w.exploit_hint}")

# 3. بحث موجّه
config = SearchConfig()
config.strategy = SearchStrategy.MCTS
config.mcts_iterations = 100

search = GuidedSearchEngine(config)
candidates = search.search(
    seeds=h_seeds + w_seeds,
    action_graph=action_space.graph,
    actions=action_space.graph.actions,
    simulate_fn=attack_engine.simulate_sequence,
    initial_state=state,
)

# 4. تحسين
gradient = ProfitGradientEngine()
optimized = gradient.optimize(candidates, simulate_fn, state)
```

### 19.3 استخدام عبر Pipeline الكامل

```python
from agl_security_tool.state_extraction import StateExtractionEngine

# كل شيء تلقائي — 12 خطوة
engine = StateExtractionEngine({
    "project_root": "/path/to/project",
    "search_engine": True,  # تفعيل Layer 4
})

result = engine.extract("contract.sol")

# Layer 4 results
search = result.graph.search_results
if search and search.total_profitable > 0:
    print(f"🎯 وُجدت {search.total_profitable} هجمة مربحة!")
    print(f"💰 أفضل ربح: ${search.best_profit_usd:,.2f}")
```

---

## 20. المعادلات الرياضية

### 20.1 Heuristic Score

$$\text{score}(f) = \sum_{i=1}^{8} w_i \cdot \mathbb{1}[\text{feat}_i(f)] + 0.03 \cdot \mathbb{1}[\text{ext}] + 0.15 \cdot \mathbb{1}[\text{CEI} \wedge \text{ETH} \wedge \neg G]$$

$$\text{score}(f) \leftarrow \begin{cases} \text{score}(f) \times 0.3 & \text{if requires\_access} \\ \min(\text{score}(f), 1.0) & \text{otherwise} \end{cases}$$

### 20.2 UCB1 (MCTS)

$$UCB1(i) = \frac{\sum_{j=1}^{n_i} r_{i,j}}{n_i} + C \sqrt{\frac{\ln N}{n_i}}$$

$$C = \sqrt{2} \approx 1.414$$

### 20.3 Tournament Selection

$$P(\text{select best}) = 1 - \left(1 - \frac{1}{N}\right)^k$$

مع $k = 3$: pressure معتدل.

### 20.4 Gradient Step

$$\theta_{t+1} = \begin{cases} \theta_t \times m & \text{if } \pi(\theta_t \times m) > \pi(\theta_t) + \delta \\ \theta_t & \text{otherwise} \end{cases}$$

حيث:
- $\theta$ = المعامل (msg_value أو amount)
- $m \in \{1.1, 0.9, 2, 5, 10, 0.5, 0.1, 0.01\}$
- $\pi(\theta)$ = profit
- $\delta = 10$ USD (minimum improvement)

### 20.5 Hybrid Budget Allocation

$$T_{\text{total}} = T_{\text{greedy}}(10\%) + T_{\text{beam}}(40\%) + T_{\text{MCTS}}(30\%) + T_{\text{evo}}(20\%)$$

### 20.6 Near-Miss Filter

$$\text{near\_miss}(c) = \mathbb{1}[-500 < \pi(c) \leq 0]$$

---

## 21. ضبط الأداء

### 21.1 إعدادات للسرعة (عقد بسيط)

```python
SearchConfig(
    max_sequences_to_test=100,
    max_search_time_seconds=10,
    strategy=SearchStrategy.GREEDY_BEST_FIRST,
    beam_width=5,
    mcts_iterations=50,
    enable_gradient_optimization=False,
)
```

### 21.2 إعدادات للدقة (عقد معقد)

```python
SearchConfig(
    max_sequences_to_test=1000,
    max_search_time_seconds=120,
    strategy=SearchStrategy.HYBRID,
    beam_width=20,
    beam_depth=8,
    mcts_iterations=500,
    mcts_rollout_depth=6,
    population_size=50,
    generations=30,
    enable_gradient_optimization=True,
    gradient_steps=30,
)
```

### 21.3 إعدادات متوازنة (الافتراضي)

```python
SearchConfig()  # كل القيم الافتراضية
# 500 sequences, 60s, hybrid, beam_width=10, mcts=200, pop=30
```

### 21.4 جدول الأداء المتوقع

| الإعداد | الوقت | التسلسلات | الدقة |
|---------|-------|----------|-------|
| سريع | < 10s | ~100 | 70% |
| متوازن | < 60s | ~500 | 90% |
| دقيق | < 120s | ~1000 | 98% |

---

## 22. القيود والحدود

### 22.1 ما يفعله Layer 4

✅ يبحث بذكاء في فضاء الأفعال
✅ يكتشف 14 نوع ضعف اقتصادي
✅ يستخدم 5 استراتيجيات بحث مختلفة
✅ يحسّن المعاملات لزيادة الربح
✅ يتكامل مع Layers 1–3 بسلاسة
✅ يعمل ضمن ميزانية زمنية وحسابية

### 22.2 ما لا يفعله

❌ لا يكتشف bugs غير اقتصادية (مثل integer overflow بدون impact مالي)
❌ لا يُنفذ هجمات فعلية (فقط محاكاة)
❌ لا يغطي 100% من الفضاء (3.2×10¹³ مستحيل)
❌ لا يحسب gas costs الحقيقية (يستخدم تقديرات)
❌ لا يتعامل مع multi-block attacks بعمق
❌ لا يفهم business logic خارج pattern matching

### 22.3 الافتراضات

1. **ActionSpace صحيح**: يعتمد على Layer 2 لتقديم أفعال كاملة
2. **Simulation موثوقة**: يعتمد على Layer 3 لتقييم دقيق
3. **Single-block**: معظم الهجمات في block واحد
4. **Fixed gas price**: لا يتتبع gas price ديناميكيا

---

## الخلاصة

**Layer 4** يُكمل النظام بأربعة مكونات ذكية:

1. **Heuristic Prioritizer** — لا تبحث عشوائياً، ابدأ حيث تفوح رائحة الأموال
2. **Weakness Detector** — 14 نوع ضعف اقتصادي مع exploit hints بالعربية والإنجليزية
3. **Guided Search** — 5 استراتيجيات (Beam/MCTS/Evolutionary/Greedy/Hybrid) بدل brute force
4. **Profit Gradient** — Hill Climbing يحسّن المعاملات بعد إيجاد تسلسل واعد

**الأرقام:**
- 7 ملفات / 3,465 سطر كود
- 4 تعدادات / 8 هياكل بيانات / 5 فئات
- 14 كاشف ضعف / 5 استراتيجيات بحث
- 93 اختبار → 93 نجحوا
- إصدار المحرك: **v5.0.0**

```
Layer 1–3 = الرادار ← يرى كل الأهداف
Layer 4   = الصاروخ ← يصيب الهدف بدقة

الآن: تملك رادار + صاروخ.
```
