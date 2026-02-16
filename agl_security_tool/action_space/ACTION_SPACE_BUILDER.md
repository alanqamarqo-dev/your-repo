# Action Space Builder — التوثيق الشامل
## AGL Security Tool — Layer 2 (v1.0.0)

---

## جدول المحتويات

1. [نظرة عامة](#1-نظرة-عامة)
2. [الدافع — لماذا هذه الطبقة](#2-الدافع)
3. [العمارة الهندسية](#3-العمارة-الهندسية)
4. [المكوّن الأول: Action Enumerator](#4-action-enumerator)
5. [المكوّن الثاني: Parameter Generator](#5-parameter-generator)
6. [المكوّن الثالث: State Linker](#6-state-linker)
7. [المكوّن الرابع: Action Classifier](#7-action-classifier)
8. [المكوّن الخامس: Action Graph Builder](#8-action-graph-builder)
9. [المنسّق الرئيسي: ActionSpaceBuilder](#9-builder)
10. [نماذج البيانات (Data Models)](#10-نماذج-البيانات)
11. [Pipeline التنفيذ في المحرك](#11-pipeline-التنفيذ)
12. [أمثلة عملية مع مخرجات حقيقية](#12-أمثلة-عملية)
13. [الـ API المتاح](#13-api)
14. [بنية الملفات](#14-بنية-الملفات)
15. [مخرج JSON الكامل](#15-مخرج-json)
16. [نتائج الاختبار](#16-نتائج-الاختبار)
17. [التطوير المستقبلي: Layer 3](#17-layer-3)

---

## 1. نظرة عامة

**Action Space Builder** هو Layer 2 في محرك AGL Security Tool. بينما Layer 1 يستخرج **حالة العالم** (كيانات مالية، علاقات، أرصدة، تبعيات زمنية)، هذه الطبقة تحوّل تلك المعرفة إلى **فضاء أفعال** — كل الحركات الممكنة التي يمكن للمهاجم فعلها.

### التشبيه

فكّر في الأمر كمحرك شطرنج:

| الطبقة | الشطرنج | AGL Security Tool |
|--------|---------|-------------------|
| **Layer 1** | يفهم حالة الرقعة: أين كل قطعة، ما القواعد | يفهم حالة العقد: الكيانات، الأرصدة، التبعيات الزمنية |
| **Layer 2** | يولّد كل الحركات الممكنة | يولّد كل الأفعال + variants + يصنفها + يبني رسم اعتماديات |
| **Layer 3** | يلعب الحركات فعلياً ويرى النتيجة | ينفذ المعاملات في EVM حقيقي ويقيس الربح |

### ملخص القدرات

| القدرة | الوصف |
|--------|-------|
| Action Enumeration | استخراج كل دالة قابلة لاستدعاء خارجي مع كشف access control |
| Parameter Variants | توليد 8 variants استراتيجية لكل دالة (بدون Cartesian explosion) |
| State Linking | ربط كل فعل بـ ΔState + balance effects + temporal constraints |
| Attack Classification | 13 نوع هجوم × severity × profit potential |
| Action Graph | رسم بياني: 5 أنواع أضلاع (state_enables, temporal, reentrancy, conflict, profit_chain) |
| Attack Path DFS | بحث عمق-أول عن مسارات هجوم مرتبة بالأوزان |
| Attack Surface Summary | ملخص لكل عقد: أسطح الهجوم + أهداف عالية القيمة |

---

## 2. الدافع

بعد بناء Layer 1 بالكامل (State Extraction Engine + Dynamic State Transition Model)، أصبح المحرك يفهم:

- ✅ ما الكيانات الموجودة (tokens, pools, vaults, oracles)
- ✅ كيف تتبدل الحالة (State(t+1) = State(t) + Σ(deltas))
- ✅ متى تتبدل (Temporal Dependency Graph)
- ✅ أين توجد CEI violations و reentrance windows

لكنه **لا يعرف ماذا يفعل بهذه المعلومات**:

1. ❌ لا يعرف ما الدوال التي يمكن للمهاجم استدعاءها
2. ❌ لا يعرف ما القيم التي يجب تمريرها كمعاملات
3. ❌ لا يعرف ترتيب الاستدعاءات الأمثل
4. ❌ لا يصنف الهجمات بشكل هرمي (نوع + خطورة + ربحية)
5. ❌ لا يبني رسماً للبحث عن تسلسلات هجوم مربحة

Layer 2 يحل كل هذا: يحول **معرفة سلبية** إلى **خطة هجوم قابلة للتنفيذ**.

---

## 3. العمارة الهندسية

### Pipeline من 6 مراحل

```
ParsedContracts + FinancialGraph + TemporalAnalysis
                    │
                    ▼
        ┌─── Step 1: ActionEnumerator ───┐
        │  لكل دالة public/external:     │
        │  → هل المهاجم يستطيع استدعاءها؟│
        │  → أنشئ Action أساسي واحد      │
        └────────────┬───────────────────┘
                     │ List[Action] (base)
                     ▼
        ┌─── Step 2: ParameterGenerator ──┐
        │  لكل Action أساسي:              │
        │  → وَلِّد ≤8 variants           │
        │  → قيم حدية + هجومية + عادية    │
        └────────────┬────────────────────┘
                     │ List[Action] (expanded)
                     ▼
        ┌─── Step 3: StateLinker ─────────┐
        │  لكل Action:                    │
        │  → ربط بـ balance_effects       │
        │  → ربط بـ temporal_constraints  │
        │  → كشف state_enables           │
        │  → كشف value_flow              │
        └────────────┬────────────────────┘
                     │ List[Action] (enriched)
                     ▼
        ┌─── Step 4: ActionClassifier ────┐
        │  لكل Action:                    │
        │  → category (17 فئة)           │
        │  → attack_types (13 نوع هجوم)  │
        │  → severity + profit_potential  │
        └────────────┬────────────────────┘
                     │ List[Action] (classified)
                     ▼
        ┌─── Step 5: ActionGraphBuilder ──┐
        │  → أضف كل Action كعقدة         │
        │  → ابنِ 5 أنواع أضلاع           │
        │  → احسب الأوزان                │
        └────────────┬────────────────────┘
                     │ ActionGraph
                     ▼
        ┌─── Step 6: Summary ─────────────┐
        │  → attack_surfaces per contract │
        │  → high_value_targets (sorted)  │
        │  → attack_sequences (DFS paths) │
        └────────────┬────────────────────┘
                     │
                     ▼
              ActionSpace (final output)
                → graph: ActionGraph
                → attack_surfaces: List[Dict]
                → high_value_targets: List[Dict]
                → attack_sequences: List[Dict]
```

### التكامل مع Layer 1

```
Layer 1 outputs        →    Layer 2 inputs
─────────────────────────────────────────
ParsedContract         →    ActionEnumerator (functions, state_vars, modifiers)
FunctionEffect         →    ActionEnumerator (reads, writes, net_delta, external_calls)
StateMutation          →    ActionEnumerator (deltas, call_points)
ExecutionTimeline      →    ActionEnumerator (CEI violations, reentrancy detection)
TemporalAnalysis       →    StateLinker (temporal_edges → constraints)
                            ActionGraphBuilder (temporal edges → graph edges)
FinancialGraph         →    StateLinker (fund_flows, balances → balance_effects)
```

---

## 4. Action Enumerator

**ملف:** `action_enumerator.py` (~394 سطر)

### الوظيفة

يمسح كل دالة في كل عقد ويولّد `Action` أساسي واحد لكل دالة يمكن للمهاجم استدعاءها.

### القرار: هل المهاجم يستطيع الاستدعاء؟

```
الدالة قابلة للاستدعاء إذا:
  visibility ∈ {public, external}
  OR is_fallback = true
  OR is_receive = true

  AND ليست constructor/initializer
```

### كشف Access Control

يكشف 14+ نمط modifier يمنع المهاجم العادي:

```python
_ACCESS_MODIFIERS = {
    "onlyOwner", "onlyAdmin", "onlyRole", "onlyGovernance",
    "onlyMinter", "onlyPauser", "onlyOperator", "onlyKeeper",
    "onlyAuthorized", "onlyController", "onlyManager",
    "onlyGuardian", "onlyWhitelisted", "onlyDAO",
}
```

بالإضافة إلى فحص `require` checks:
- `msg.sender == owner`
- `hasRole(...)`
- `_checkRole(...)`

إذا وُجد access control ← `action.is_valid = False` + `disabled_reason`.

### ربط بيانات Layer 1

لكل Action، يبحث في lookup maps:

```python
effect_map:   "Contract.function" → FunctionEffect
mutation_map: "Contract.function" → StateMutation  
timeline_map: "Contract.function" → ExecutionTimeline
```

ويملأ الحقول:
- `state_reads`, `state_writes` ← من `FunctionEffect.reads/writes` أو `ParsedFunction`
- `net_delta` ← من `FunctionEffect.net_delta`
- `external_calls` ← من `FunctionEffect.external_calls` أو `ParsedFunction`
- `has_cei_violation`, `cei_violation_count` ← من `ExecutionTimeline.cei_violations`
- `reentrancy_window` ← CEI + لا `nonReentrant` guard
- `cross_function_risk` ← من `FunctionEffect.conflicts_with`

### المخرج

```python
List[Action]  # عدد الأفعال = عدد الدوال القابلة للاستدعاء (بدون variants)
```

### مثال مع Vault.sol

```
Input:  Vault contract (9 functions)
Output: 8 Actions (constructor مُستثنى)
  → deposit        (is_valid=True,  caller=anyone)
  → withdraw       (is_valid=True,  has_cei=True, reentrancy_window=True)
  → safeWithdraw   (is_valid=True,  reentrancy_guarded=True)
  → calculateReward(is_valid=True,  mutability=view)
  → claimReward    (is_valid=True,  caller=anyone)
  → setRewardRate  (is_valid=False, reason="onlyOwner")
  → emergencyWithdraw (is_valid=True, caller=anyone)
  → receive        (is_valid=True,  payable)
```

---

## 5. Parameter Generator

**ملف:** `parameter_generator.py` (~290 سطر)

### الوظيفة

لكل `Action` أساسي، يولّد ≤8 نسخ (variants) بمعاملات مختلفة استراتيجياً.

### لماذا لا نستخدم Cartesian Product؟

```
withdraw(uint256 amount, address to)
  amount: 5 قيم ممكنة
  to:     4 قيم ممكنة
  Cartesian: 5 × 4 = 20 variant

عقد بـ 10 دوال × 20 variant = 200 action
× 3 عقود = 600 action → explosion!
```

### الاستراتيجية: Smart Combine

بدلاً من Cartesian، نأخذ 4 أنواع variants فقط:

| النوع | الشرح | مثال (withdraw) |
|-------|-------|----------------|
| **Default** | أول قيمة لكل معامل | `withdraw(0)` |
| **One-at-a-time** | غيّر معامل واحد فقط | `withdraw(balance)`, `withdraw(max)` |
| **Attack** | أخطر قيمة لكل معامل | `withdraw(balance+1)` |
| **Edge case** | كل المعاملات بـ zero/min | `withdraw(0)` |

### القيم الاستراتيجية حسب النوع

**مبالغ مالية (uint256 amount):**

| القيمة | السبب |
|--------|-------|
| `0` | edge case — ماذا يحدث مع صفر؟ |
| `1` | dust amount — minimum |
| `balance_of_sender` | drain all — سحب كل الرصيد |
| `type(uint256).max` | overflow attempt |
| `balance_of_sender + 1` | underflow attempt — أكثر من الرصيد |
| `address(this).balance` | drain contract (إذا payable) |

**عناوين (address):**

| القيمة | السبب |
|--------|-------|
| `attacker` | self-benefit — يوجه الأموال لنفسه |
| `address(0)` | zero address — burn أو خطأ |
| `address(this)` | self-call — استدعاء العقد لنفسه |
| `malicious_token` | token substitution (إذا هو token param) |

### المخرج

```python
# مثلاً: 8 دوال أساسية → 25 action variant
List[Action]  # كل variant بـ action_id فريد: "Contract.function#v0", "#v1", ...
```

---

## 6. State Linker

**ملف:** `state_linker.py` (~353 سطر)

### الوظيفة

يربط كل Action بتأثيره الحقيقي على حالة النظام، مستخدماً بيانات Layer 1.

### 4 مراحل إخصاء

#### 6.1 Balance Effects

يربط كل Action بتأثيره على الأرصدة:

```python
# من net_delta (Layer 1)
for var, delta_expr in action.net_delta.items():
    if "balance" or "deposit" or "reserve" in var:
        action.balance_effects[var] = delta_expr

# من fund_flows (FinancialGraph)
for flow in flow_map.get(action.function_name):
    action.balance_effects[src→tgt] = "flow_type: amount_expr"
    action.tokens_involved.append(flow.token_id)
```

#### 6.2 Temporal Constraints

يربط كل Action بالقيود الزمنية من Temporal Graph:

```python
# إذا هذا Action هو مصدر ضلع زمني
for edge in temporal.temporal_edges:
    if edge.source == this_action:
        action.temporal_constraints.append(edge)
        if edge.is_vulnerability → action.reentrancy_window = True
        action.must_execute_before.append(target_actions)

# من CEI violations
for violation in timeline.cei_violations:
    action.temporal_constraints.append(
        "CEI: call@step{X} → write@step{Y}"
    )
```

#### 6.3 Value Flow Estimation

يحسب تقدير تدفق القيمة:

```
sends_eth → "sends_eth"
net_delta[balance] contains "-" → "decreases_balance"
net_delta[balance] contains "+" → "increases_balance"
```

#### 6.4 State Enables Detection

أهم ميزة: اكتشف أي Action يفتح preconditions لـ Actions أخرى:

```
deposit() writes balances[user] += amount
withdraw() reads balances[user]
→ deposit ENABLES withdraw
```

المنطق:

```python
writers: {variable → [action_ids that write]}
readers: {variable → [action_ids that read]}
enables = [{source, target, shared_var}
           for var in writers ∩ readers
           for writer in writers[var]
           for reader in readers[var]]
```

### المخرج

نفس `List[Action]` لكن كل Action مُخصّب بـ:
- `balance_effects: Dict[str, str]`
- `tokens_involved: List[str]`
- `estimated_value_flow: str`
- `temporal_constraints: List[str]`
- `must_execute_before / after: List[str]`

بالإضافة إلى:
- `List[Dict]` — state_enables (يُمرر لـ ActionGraphBuilder)

---

## 7. Action Classifier

**ملف:** `action_classifier.py` (~371 سطر)

### الوظيفة

تصنيف ثلاثي لكل Action:

1. **ActionCategory** — ماذا تفعل هذه الدالة وظيفياً
2. **AttackType** — ما أنماط الهجوم المحتملة
3. **severity + profit_potential** — ما الخطورة والربحية

### 7.1 تصنيف الفئة (ActionCategory)

17 فئة ممكنة، يُحدد بمطابقة اسم الدالة:

| الفئة | أنماط الأسماء |
|-------|---------------|
| FUND_INFLOW | deposit, supply, addLiquidity, provide, fund |
| FUND_OUTFLOW | withdraw, redeem, removeLiquidity, drain |
| BORROW | borrow, flashLoan, flashBorrow, leverage |
| REPAY | repay, payBack, close, settle |
| SWAP | swap, exchange, trade, convert |
| LIQUIDATE | liquidate, liquidation, seize, auction |
| STAKE | stake, delegate, lock, bond |
| UNSTAKE | unstake, undelegate, unlock, unbond |
| CLAIM | claim, harvest, collect, getReward |
| GOVERNANCE_VOTE | vote, propose, castVote, queue |
| ADMIN | setOwner, transferOwnership, pause, setFee |
| ORACLE_UPDATE | updatePrice, setPrice, updateOracle |
| FLASH_LOAN | flashLoan, flash, flashBorrow |
| APPROVAL | approve, permit, increaseAllowance |
| STATE_CHANGE | أي دالة تكتب حالة بدون تطابق أعلاه |
| VIEW | دوال view/pure |
| UNKNOWN | كل ما تبقى |

### 7.2 تصنيف نوع الهجوم (AttackType)

13 نوع هجوم يُكتشف بالمنطق التالي:

| النوع | شرط الكشف |
|-------|-----------|
| **REENTRANCY** | `has_cei_violation=True` AND `reentrancy_guarded=False` |
| **CROSS_FUNCTION** | `cross_function_risk=True` AND `reentrancy_window=True` |
| **DIRECT_PROFIT** | category ∈ {OUTFLOW, LIQUIDATE, CLAIM} AND no access control |
| **STATE_MANIPULATION** | يكتب متغيرات حساسة (balance, reserve, price, rate, supply, debt) |
| **FLASH_LOAN** | category=FLASH_LOAN OR (parameters تتضمن مبالغ كبيرة) |
| **PRICE_MANIPULATION** | اسم الدالة or state_writes تتضمن price/oracle/rate |
| **LIQUIDATION** | category=LIQUIDATE |
| **ACCESS_ESCALATION** | delegatecall بدون access control OR initialize بدون guard |
| **GOVERNANCE** | category=GOVERNANCE_VOTE |
| **FRONT_RUNNING** | swap/liquidate/approve بدون access control |
| **DONATION** | deposit+payable + يكتب share/supply vars |
| **GRIEFING** | external call + reentrancy window + لا guard |
| **SANDWICH** | (يُضاف لاحقاً عبر تحليل أعمق) |

### 7.3 تقييم الخطورة (severity)

| الخطورة | الشرط |
|---------|-------|
| **critical** | REENTRANCY + sends_eth, أو ACCESS_ESCALATION, أو delegatecall بدون guard |
| **high** | REENTRANCY, أو CROSS_FUNCTION, أو (DIRECT_PROFIT + sends_eth), أو (FLASH_LOAN + PRICE_MANIPULATION) |
| **medium** | PRICE_MANIPULATION, أو STATE_MANIPULATION, أو FRONT_RUNNING, أو DONATION |
| **low** | GRIEFING, أو DIRECT_PROFIT بدون ETH |
| **info** | لا يوجد attack_types |

### 7.4 تقييم الربحية (profit_potential)

| الربحية | الشرط |
|---------|-------|
| **high** | (sends_eth + CEI), أو LIQUIDATE/FLASH_LOAN, أو (REENTRANCY + ETH) |
| **medium** | DIRECT_PROFIT, أو (sends_eth بدون access), أو PRICE_MANIPULATION |
| **low** | CLAIM, UNSTAKE, أو FRONT_RUNNING |
| **none** | كل ما تبقى |

---

## 8. Action Graph Builder

**ملف:** `action_graph.py` (~422 سطر)

### الوظيفة

يبني رسماً بيانياً حيث:
- **العقد (Nodes)** = كل Action صالح (`is_valid=True`)
- **الأضلاع (Edges)** = 5 أنواع اعتمادية

### 8.1 أنواع الأضلاع

#### `state_enables` — A يفتح precondition لـ B

```
deposit() writes balances[user]
withdraw() reads balances[user]
→ edge(deposit → withdraw, type=state_enables, weight=0.5)
```

#### `temporal` — من Temporal Graph (Layer 1)

```
TemporalEdge: A.call → B.write (reentrancy risk)
→ edge(A → B, type=temporal, weight=2.0 if vulnerability, 0.3 otherwise)
→ is_attack_path = true if vulnerability
```

#### `reentrancy` — A يفتح نافذة reentry → B يستغلها

```
شرط: A.reentrancy_window=True AND A.has_cei_violation=True
      AND B يقرأ متغير سيكون stale أثناء external call

→ edge(A → B, type=reentrancy, weight=3.0, is_attack_path=True)

حالة خاصة — Self-reentrancy:
→ edge(A → A, type=reentrancy, weight=4.0, is_attack_path=True)
```

#### `conflict` — Write-write على نفس المتغير

```
A.state_writes ∩ B.state_writes ≠ ∅
→ edge(A ↔ B, type=conflict, weight=0.8)
→ is_attack_path = true if (one is public AND one has reentrancy_window)
```

#### `profit_chain` — A يُمهد → B يحقق الربح

```
شرط: A.attack_types contains STATE_MANIPULATION
      B.is_profitable = True
      A.state_writes ∩ B.state_reads ≠ ∅

→ edge(A → B, type=profit_chain, weight=2.5, is_attack_path=True)
```

### 8.2 حساب الأوزان

بعد بناء كل الأضلاع، يُعاد حساب الأوزان:

```python
weight = base_weight
× 1.5 if source.severity == "critical"
× 1.5 if target.severity == "critical"
× 1.2 if source.is_profitable
× 1.3 if target.is_profitable
× 1.5 if edge_type == "reentrancy"
```

### 8.3 Attack Path Search (DFS)

```python
graph.get_attack_paths() → List[List[str]]  # قائمة من action_id paths

الخوارزمية:
1. اختر أضلاع is_attack_path=True فقط
2. ابحث عن نقاط بداية (actions ليست targets)
3. DFS من كل نقطة بداية
4. كل مسار بطول > 1 هو مسار هجوم محتمل
```

---

## 9. المنسّق الرئيسي: ActionSpaceBuilder

**ملف:** `builder.py` (~350 سطر)

### الوظيفة

ينسّق كل المكونات الخمسة ويُنتج `ActionSpace` النهائي.

### Pipeline

```python
builder = ActionSpaceBuilder()
space = builder.build(contracts, graph, temporal)
```

| الخطوة | المكوّن | الدخل | الخرج |
|--------|---------|-------|-------|
| 1 | ActionEnumerator | contracts + L1 data | List[Action] (base) |
| 2 | ParameterGenerator | base actions | List[Action] (expanded) |
| 3 | StateLinker | expanded + graph + temporal | List[Action] (enriched) + state_enables |
| 4 | ActionClassifier | enriched | List[Action] (classified) |
| 5 | ActionGraphBuilder | classified + state_enables + temporal | ActionGraph |
| 6 | Summary | ActionGraph + all_actions | attack_surfaces + targets + sequences |

### ملخص المخرج

#### Attack Surfaces (per contract)

```json
{
  "contract": "Vault",
  "total_actions": 23,
  "valid_actions": 22,
  "profitable_actions": 14,
  "critical_or_high": 13,
  "attack_types": ["direct_profit", "flash_loan"],
  "has_reentrancy": true,
  "has_unguarded_reentrancy": true,
  "sends_eth": true,
  "exposed_functions": [...]
}
```

#### High-Value Targets (sorted)

مرتب: critical → high، ثم بالربحية (high → medium → low)

```json
{
  "action_id": "Vault.withdraw#v2",
  "severity": "high",
  "attack_types": ["direct_profit", "flash_loan"],
  "profit_potential": "medium",
  "sends_eth": true,
  "has_cei_violation": false,
  "description": "sends ETH; cross-function risk; flash loan amplifiable"
}
```

#### Attack Sequences (DFS paths, sorted by weight)

```json
{
  "sequence_id": "seq_1",
  "steps": [
    {"step": 1, "action": "Vault.deposit#v2", "function": "Vault.deposit"},
    {"step": 2, "action": "Vault.claimReward#5", "function": "Vault.claimReward"}
  ],
  "severity": "low",
  "attack_types": ["direct_profit", "flash_loan"],
  "total_weight": 2.6
}
```

---

## 10. نماذج البيانات

### Enums

```python
class AttackType(Enum):     # 13 قيمة
class ActionCategory(Enum): # 17 قيمة
class ParamDomain(Enum):    # 13 قيمة — مجال القيم لمعاملات الدوال
```

### Dataclasses

```python
@dataclass
class ActionParameter:
    name: str                    # اسم المعامل
    param_type: str              # نوع Solidity
    domains: List[ParamDomain]   # مجال القيم الممكنة
    concrete_values: List[str]   # القيم المحددة
    is_amount: bool              # مبلغ مالي
    is_address: bool             # عنوان
    is_token: bool               # توكن
    constraints: List[str]       # قيود require

@dataclass
class Action:
    action_id: str               # "Contract.function#variant"
    contract_name: str
    function_name: str
    signature: str               # "function(type1,type2)"
    parameters: List[ActionParameter]
    msg_value: Optional[str]     # ETH إذا payable
    preconditions: List[str]     # require checks
    access_requirements: List[str]
    requires_access: bool
    caller_must_be: str          # "anyone"/"owner"/"role"
    state_reads: List[str]
    state_writes: List[str]
    net_delta: Dict[str, str]
    external_calls: List[Dict]
    sends_eth: bool
    has_delegatecall: bool
    temporal_constraints: List[str]
    must_execute_before: List[str]
    must_execute_after: List[str]
    reentrancy_window: bool
    category: ActionCategory
    attack_types: List[AttackType]
    severity: str                # critical/high/medium/low/info
    profit_potential: str        # high/medium/low/none
    is_profitable: bool
    balance_effects: Dict[str, str]
    tokens_involved: List[str]
    estimated_value_flow: str
    reentrancy_guarded: bool
    has_cei_violation: bool
    cei_violation_count: int
    cross_function_risk: bool
    visibility: str
    mutability: str
    line_start: int
    source_file: str
    is_valid: bool
    disabled_reason: str

@dataclass
class ActionEdge:
    edge_id: str
    source_action: str           # action_id من
    target_action: str           # action_id إلى
    edge_type: str               # state_enables/temporal/reentrancy/conflict/profit_chain
    shared_variable: str
    description: str
    weight: float                # وزن لتوجيه البحث
    is_attack_path: bool         # هل ضمن مسار هجوم

@dataclass
class ActionGraph:
    actions: Dict[str, Action]   # action_id → Action
    edges: Dict[str, ActionEdge] # edge_id → ActionEdge
    successors: Dict[str, List[str]]   # adjacency list outgoing
    predecessors: Dict[str, List[str]] # adjacency list incoming
    
    # Methods:
    add_action(action), add_edge(edge)
    get_successors(action_id) → List[Action]
    get_predecessors(action_id) → List[Action]
    get_attack_paths() → List[List[str]]  # DFS
    stats() → Dict  # إحصائيات
    to_dict(), to_json()

@dataclass
class ActionSpace:
    graph: ActionGraph
    build_time: float
    version: str
    source_files: List[str]
    attack_surfaces: List[Dict]
    high_value_targets: List[Dict]
    attack_sequences: List[Dict]
    errors: List[str]
    warnings: List[str]
    
    to_dict(), to_json()
```

---

## 11. Pipeline التنفيذ في المحرك

Layer 2 مدمج في `StateExtractionEngine` كـ **Step 8** في pipeline v3.0.0:

```python
# state_extraction/engine.py

class StateExtractionEngine:
    VERSION = "3.0.0"
    
    def __init__(self):
        # ... Layer 1 components ...
        if ActionSpaceBuilder:
            self._action_builder = ActionSpaceBuilder(config)
    
    def extract(self, source_path):
        # Steps 1-5: Layer 1 (entities, relationships, funds, graph, validation)
        # Steps 6-7: Dynamic State Transition Model
        # Step 8: Action Space Builder ← NEW
        if self._action_builder:
            action_space = self._action_builder.build(contracts, graph, temporal)
            graph.action_space = action_space
```

`FinancialGraph.action_space` field مُضاف في models.py ويتم تضمينه في `to_dict()`.

---

## 12. أمثلة عملية مع مخرجات حقيقية

### Vault.sol — اختبار فعلي

```
Contract: Vault (9 functions, 123 lines)
Vulnerabilities: Reentrancy in withdraw(), tx.origin in emergencyWithdraw()
```

**نتائج ActionEnumerator:**

```
8 actions extracted:
  deposit          → is_valid=True,  caller=anyone
  withdraw         → is_valid=True,  sends_eth=True, CEI_violations=True
  safeWithdraw     → is_valid=True,  reentrancy_guarded=True
  calculateReward  → is_valid=True,  view
  claimReward      → is_valid=True,  caller=anyone
  setRewardRate    → is_valid=False, reason="requires onlyOwner"
  emergencyWithdraw→ is_valid=True,  caller=anyone
  receive          → is_valid=True,  payable
```

**نتائج ParameterGenerator:**

```
25 action variants generated (from 8 base):
  deposit: 4 variants (0, 1, balance, max)
  withdraw: 5 variants (0, 1, balance, max, balance+1)
  ...
```

**نتائج StateLinker:**

```
withdraw state_writes: ['deposits', 'totalDeposits']
withdraw external_calls: [{target: msg.sender, type: external_call_eth}]
Total state_enables links: 114
```

**نتائج ActionClassifier:**

```
withdraw:
  category: fund_outflow
  attack_types: [direct_profit, flash_loan]
  severity: high
  profit_potential: medium

emergencyWithdraw:
  category: fund_outflow
  attack_types: [direct_profit]
  severity: high
```

**نتائج ActionGraphBuilder:**

```
Graph: 24 nodes, 549 edges
Edge distribution: temporal=222, conflict=327
Attack paths: 6 (deposit → claimReward patterns)
```

**نتائج ActionSpaceBuilder (Full pipeline):**

```
ActionSpace:
  graph: 22 actions, 549 edges
  attack_surfaces: 1 contract
  high_value_targets: 13
  attack_sequences: 6
  JSON size: 310,677 bytes
```

---

## 13. الـ API المتاح

### استخدام مباشر

```python
from agl_security_tool.action_space import ActionSpaceBuilder
from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser

# Parse
parser = SoliditySemanticParser()
contracts = parser.parse(source, filename)

# Build action space
builder = ActionSpaceBuilder()
space = builder.build(contracts)
print(space.to_json())
```

### استخدام مع Layer 1 (موصى)

```python
from agl_security_tool.state_extraction import StateExtractionEngine

engine = StateExtractionEngine()
result = engine.extract("path/to/contract.sol")

# Action space متاح تلقائياً
action_space = result.graph.action_space
print(action_space.to_json())

# الوصول للبيانات
for action_id, action in action_space.graph.actions.items():
    if action.severity in ("critical", "high"):
        print(f"⚠️ {action.function_name}: {action.attack_types}")

for seq in action_space.attack_sequences:
    print(f"Attack: {seq['steps']} → weight={seq['total_weight']}")
```

### استخدام كل مكوّن على حدة

```python
from agl_security_tool.action_space import (
    ActionEnumerator, ParameterGenerator, StateLinker,
    ActionClassifier, ActionGraphBuilder,
)

enumerator = ActionEnumerator()
actions = enumerator.enumerate(contracts, effects, mutations, timelines)

param_gen = ParameterGenerator()
actions = param_gen.generate(actions)

linker = StateLinker()
actions = linker.link(actions, graph, temporal)
state_enables = linker.find_state_enables(actions)

classifier = ActionClassifier()
actions = classifier.classify(actions)

graph_builder = ActionGraphBuilder()
graph = graph_builder.build(actions, state_enables, temporal)

paths = graph.get_attack_paths()
```

### الإعدادات

```python
config = {
    "max_variants": 8,          # حد أقصى variants لكل دالة
    "include_invalid": False,   # هل تُضمّن Actions المعطلة
    "skip_view": True,          # هل تتجاهل view/pure
    "action_space": True,       # تفعيل/تعطيل في المحرك
}
builder = ActionSpaceBuilder(config)
```

---

## 14. بنية الملفات

```
agl_security_tool/
├── action_space/
│   ├── __init__.py              # exports, __version__="1.0.0"
│   ├── models.py                # 449 lines — Enums + Dataclasses
│   ├── action_enumerator.py     # 394 lines — استخراج Actions من العقود
│   ├── parameter_generator.py   # 290 lines — توليد variants استراتيجية
│   ├── state_linker.py          # 353 lines — ربط بـ ΔState + temporal
│   ├── action_classifier.py     # 371 lines — تصنيف ثلاثي
│   ├── action_graph.py          # 422 lines — بناء الرسم + DFS
│   ├── builder.py               # 350 lines — المنسّق الرئيسي
│   └── ACTION_SPACE_BUILDER.md  # هذا الملف
│
├── state_extraction/
│   ├── engine.py                # v3.0.0 — Step 8 يستدعي ActionSpaceBuilder
│   ├── models.py                # FinancialGraph.action_space field مُضاف
│   └── __init__.py              # v3.0.0 — ActionSpaceBuilder مُصدَّر
│
└── detectors/                   # Layer 0 — Parser
    ├── __init__.py              # ParsedContract, ParsedFunction, OpType
    └── solidity_parser.py       # SoliditySemanticParser
```

**إجمالي الكود:** ~2,629 سطر في 7 ملفات.

---

## 15. مخرج JSON الكامل

```json
{
  "version": "1.0.0",
  "build_time_ms": 42.5,
  "source_files": ["Vault.sol"],
  "graph": {
    "actions": {
      "Vault.withdraw#v0": {
        "action_id": "Vault.withdraw#v0",
        "contract_name": "Vault",
        "function_name": "withdraw",
        "signature": "withdraw(uint256)",
        "parameters": [{
          "name": "amount",
          "param_type": "uint256",
          "domains": ["uint256_zero", "small_amount", "balance_of_sender", "uint256_max"],
          "concrete_values": ["0"],
          "is_amount": true
        }],
        "state_writes": ["deposits", "totalDeposits"],
        "external_calls": [{"target": "msg.sender", "type": "external_call_eth", "sends_eth": true}],
        "sends_eth": true,
        "category": "fund_outflow",
        "attack_types": ["direct_profit", "flash_loan"],
        "severity": "high",
        "profit_potential": "medium",
        "is_valid": true
      }
    },
    "edges": {
      "ae_1": {
        "source_action": "Vault.deposit#v1",
        "target_action": "Vault.claimReward#5",
        "edge_type": "temporal",
        "weight": 2.6,
        "is_attack_path": true
      }
    },
    "stats": {
      "total_actions": 24,
      "total_edges": 549,
      "valid_actions": 24,
      "attack_edges": 6,
      "categories": {"fund_inflow": 7, "fund_outflow": 13, "view": 3, "claim": 1},
      "severities": {"info": 10, "high": 13, "low": 1}
    }
  },
  "attack_surfaces": [...],
  "high_value_targets": [...],
  "attack_sequences": [...]
}
```

---

## 16. نتائج الاختبار

اختبار شامل على Vault.sol (تاريخ: فبراير 2026):

| المكوّن | النتيجة | التفاصيل |
|---------|---------|----------|
| ActionEnumerator | ✅ PASS | 8 actions, setRewardRate معطل (onlyOwner) |
| ParameterGenerator | ✅ PASS | 25 variants, withdraw بـ 4 domains |
| StateLinker | ✅ PASS | 114 state_enables, external_calls مكتشف |
| ActionClassifier | ✅ PASS | 13 high severity, distribution: {info:10, high:13, low:1} |
| ActionGraphBuilder | ✅ PASS | 24 nodes, 549 edges, 6 attack paths |
| Full Pipeline | ✅ PASS | ActionSpace كامل مع 22 actions |
| JSON Export | ✅ PASS | 310KB valid JSON |
| Engine Integration | ✅ PASS | v3.0.0, Step 8 يعمل, 608KB full JSON |

---

## 17. التطوير المستقبلي: Layer 3

Layer 2 يبني **خريطة الحركات الممكنة**. Layer 3 سيستخدم هذه الخريطة لـ **تنفيذ الهجمات فعلياً**:

```
Layer 2 ActionSpace
       │
       ▼
Layer 3: Transaction Execution Engine
       │
       ├── Blockchain Fork Engine (Anvil)
       │     تشغيل fork محلي من mainnet
       │
       ├── Action → Transaction Compiler
       │     تحويل Action → ABI-encoded calldata
       │
       ├── State Snapshot Manager
       │     snapshot/revert للأداء
       │
       ├── Sequence Executor
       │     تنفيذ Tx1 → Tx2 → Tx3 بترتيب
       │
       └── Profit Analyzer
             Profit = Δ balances across tokens
             → إذا موجب = هجوم ناجح
```

**Layer 3 لن يكون محاكاة رياضية أو تحليل رمزي — بل تنفيذ حقيقي داخل EVM fork.**
