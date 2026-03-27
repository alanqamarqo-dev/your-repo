# Dynamic State Transition Model — التوثيق الشامل
## AGL State Extraction Engine v2.0

---

## جدول المحتويات

1. [نظرة عامة](#1-نظرة-عامة)
2. [الدافع — لماذا هذه الطبقة](#2-الدافع)
3. [العمارة الهندسية](#3-العمارة-الهندسية)
4. [المكوّن الأول: Execution Semantics Layer](#4-execution-semantics-layer)
5. [المكوّن الثاني: State Mutation Tracker](#5-state-mutation-tracker)
6. [المكوّن الثالث: Function Effect Model](#6-function-effect-model)
7. [المكوّن الرابع: Temporal Dependency Graph](#7-temporal-dependency-graph)
8. [نماذج البيانات (Data Models)](#8-نماذج-البيانات)
9. [Pipeline التنفيذ في المحرك](#9-pipeline-التنفيذ)
10. [أنواع الثغرات المكتشفة](#10-أنواع-الثغرات)
11. [أمثلة عملية مع مخرجات حقيقية](#11-أمثلة-عملية)
12. [الـ API المتاح](#12-api)
13. [بنية الملفات](#13-بنية-الملفات)
14. [مخرج JSON الكامل](#14-مخرج-json)
15. [القيود والتطوير المستقبلي](#15-القيود)

---

## 1. نظرة عامة

**Dynamic State Transition Model** هي طبقة تحليل زمني تُضاف فوق محرك استخراج الحالة المالية (Layer 1). بينما Layer 1 يستخرج **ماذا يوجد** (كيانات، علاقات، أرصدة)، هذه الطبقة تحلل **كيف ومتى تتغير** الحالة.

### المشكلة التي يحلّها

المحرك القديم (v1.0) كان يرى:
```
withdraw() → تقرأ balances → تكتب balances → تُرسل ETH
```

لكنه **لا يفهم الترتيب**. الفرق بين العقد الآمن والعقد المُخترَق هو فقط ترتيب السطور:

```solidity
// ⛔ مُخترَق — call قبل update
function withdraw(uint256 amount) external {
    require(balances[msg.sender] >= amount);
    msg.sender.call{value: amount}("");      // ← INTERACTION أولاً
    balances[msg.sender] -= amount;          // ← EFFECT بعدها (متأخر!)
}

// ✅ آمن — update قبل call
function withdraw(uint256 amount) external {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;          // ← EFFECT أولاً
    msg.sender.call{value: amount}("");      // ← INTERACTION بعدها (آمن)
}
```

الـ Dynamic State Transition Model **يفهم هذا الفرق** ويكشفه تلقائياً.

### ملخص القدرات

| القدرة | الوصف |
|--------|-------|
| Execution Timeline | خط زمني مرقم لكل عملية في كل دالة |
| CEI Violation Detection | كشف استدعاء خارجي قبل كتابة حالة |
| State(t+1) = State(t) + Δ | نموذج رياضي لتحولات الحالة |
| ΔState = f(inputs) | نموذج تأثير كل دالة على الحالة |
| Temporal Dependency Graph | رسم تبعيات زمنية عبر الدوال |
| Cross-function Reentrancy | كشف reentrancy عبر دوال مختلفة |
| Write-Write Conflicts | كشف تعارض كتابة بين دالتين |
| Attack Surface Analysis | تحليل سطح الهجوم المالي |

---

## 2. الدافع

نقد خارجي أشار إلى أن Layer 1 يغطي ~40% فقط من التحليل المطلوب لكشف ثغرات حقيقية. المكونات الناقصة كانت:

1. **Execution Semantics** — ترتيب العمليات، call stack، ترتيب الكتابة
2. **State Mutation Tracker** — نموذج State(t+1) = State(t) + delta
3. **Function Effect Model** — ΔState = f(inputs) لكل دالة
4. **Temporal Dependency Graph** — متى تحدث التغييرات بالنسبة لأحداث أخرى

**ملاحظة مهمة**: الـ `SoliditySemanticParser` الموجود مسبقاً في `detectors/solidity_parser.py` **كان يستخرج ترتيب العمليات فعلاً** عبر `ParsedFunction.operations: List[Operation]`. الإضافة الجديدة هي **استهلاك** هذه البيانات في نماذج رياضية وزمنية بدلاً من تركها غير مستخدمة.

---

## 3. العمارة الهندسية

### مخطط تدفق البيانات

```
┌─────────────────────────────────────────────────────────────┐
│                    SoliditySemanticParser                     │
│         (detectors/solidity_parser.py — 934 سطر)            │
│                                                              │
│  Input: Solidity Source Code                                 │
│  Output: List[ParsedContract]                                │
│    ├── ParsedFunction.operations: List[Operation]  ← مرتبة  │
│    ├── ParsedFunction.state_reads / state_writes             │
│    ├── ParsedFunction.external_calls                         │
│    └── ParsedFunction.has_reentrancy_guard                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Layer 1: State Extraction (v1.0)                │
│                                                              │
│  EntityExtractor → RelationshipMapper → FundMapper →         │
│  FinancialGraphBuilder → ConsistencyValidator                │
│                                                              │
│  Output: FinancialGraph (nodes, edges, balances, flows)      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│      Layer 2: Dynamic State Transition Model (v2.0)          │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────────┐     │
│  │  ExecutionSemantics   │  │  StateMutationTracker     │     │
│  │  ExtractOr            │  │                           │     │
│  │                       │  │  Input: ParsedContracts   │     │
│  │  Input: ParsedContr.  │  │  Output: StateMutation[]  │     │
│  │  Output: ExecTimeline │  │    ├── deltas[]           │     │
│  │    ├── steps[]        │  │    ├── call_points[]      │     │
│  │    ├── cei_violations │  │    └── net_effect{}       │     │
│  │    └── stats          │  └────────────┬──────────────┘     │
│  └────────────┬──────────┘               │                    │
│               │                          │                    │
│               ▼                          ▼                    │
│  ┌──────────────────────┐  ┌──────────────────────────┐     │
│  │  FunctionEffect       │  │  TemporalDependency       │     │
│  │  Modeler              │  │  Graph                     │     │
│  │                       │  │                           │     │
│  │  Input: Contracts +   │  │  Input: All of above      │     │
│  │         Mutations     │  │  Output: TemporalAnalysis │     │
│  │  Output: FuncEffect[] │  │    ├── temporal_edges[]   │     │
│  │    ├── reads/writes   │  │    ├── vuln_candidates[]  │     │
│  │    ├── net_delta{}    │  │    └── summary stats      │     │
│  │    ├── conflicts[]    │  └────────────┬──────────────┘     │
│  │    └── depends_on[]   │               │                    │
│  └───────────────────────┘               │                    │
│                                          ▼                    │
│                              FinancialGraph.temporal_analysis  │
└─────────────────────────────────────────────────────────────┘
```

### تسلسل التنفيذ في pipeline المحرك

```
Step 1: Parse Solidity              → List[ParsedContract]
Step 2: Extract Entities            → List[Entity]
Step 3: Map Relationships           → List[Relationship]
Step 4: Map Funds                   → (List[BalanceEntry], List[FundFlow])
Step 5: Build Financial Graph       → FinancialGraph
Step 6: Validate Consistency        → ValidationResult
Step 7: Dynamic State Transition    → TemporalAnalysis    ← الجديد
  ├── 7a: Execution Semantics      → List[ExecutionTimeline]
  ├── 7b: State Mutations          → List[StateMutation]
  ├── 7c: Function Effects         → List[FunctionEffect]
  └── 7d: Temporal Graph           → TemporalAnalysis (final)
```

---

## 4. Execution Semantics Layer

**الملف**: `state_extraction/execution_semantics.py` — 402 سطر  
**الكلاس**: `ExecutionSemanticsExtractor`

### الغرض

تحويل العمليات المرتبة (`ParsedFunction.operations`) إلى **خط زمني مرقم** (`ExecutionTimeline`) لكل دالة، مع كشف انتهاكات نمط **Checks-Effects-Interactions (CEI)**.

### المدخلات والمخرجات

```python
# المدخل
contracts: List[ParsedContract]  # من SoliditySemanticParser

# المخرج  
timelines: List[ExecutionTimeline]  # واحد لكل دالة
```

### ماذا يفعل بالتحديد

#### 1. بناء ExecutionTimeline

لكل دالة، يمر على `func.operations` بالترتيب ويحوّل كل `Operation` إلى `ExecutionStep`:

```python
# مثال: withdraw(amount)
ExecutionTimeline(
    function_name="withdraw",
    contract_name="VulnerableVault",
    steps=[
        ExecutionStep(step_index=0, op_type="require",          target="balances[msg.sender] >= amount"),
        ExecutionStep(step_index=1, op_type="external_call_eth", target="msg.sender", sends_eth=True),
        ExecutionStep(step_index=2, op_type="require",          target="success"),
        ExecutionStep(step_index=3, op_type="state_write",      target="balances"),
        ExecutionStep(step_index=4, op_type="state_write",      target="totalDeposits"),
        ExecutionStep(step_index=5, op_type="emit",             target="Withdraw"),
    ]
)
```

الترتيب واضح: الاستدعاء الخارجي (step 1) يقع **قبل** كتابة الحالة (step 3, 4).

#### 2. كشف CEI Violations

يبحث عن كل حالة يكون فيها `is_external_call=True` في step قبل `is_state_write=True`:

```python
CEIViolation(
    call_step=1,          # الاستدعاء الخارجي
    write_step=3,         # كتابة الحالة (بعد الاستدعاء)
    call_target="msg.sender",
    write_target="balances",
    sends_eth=True,
    violation_type="classic_reentrancy",  # لأنه يرسل ETH
    severity="critical"
)
```

**أنواع الـ violations المكتشفة:**

| النوع | الشرط | الخطورة |
|-------|-------|---------|
| `classic_reentrancy` | `EXTERNAL_CALL_ETH` قبل `STATE_WRITE` | Critical |
| `non_eth_reentrancy` | `EXTERNAL_CALL` (بدون ETH) قبل `STATE_WRITE` | High |
| `read_only_reentrancy_surface` | دالة view تقرأ حالة | Medium |

#### 3. إحصائيات الترتيب

| الإحصائية | المعنى |
|-----------|--------|
| `external_calls_before_writes` | عدد الاستدعاءات الخارجية قبل أول كتابة حالة |
| `state_reads_before_calls` | عدد القراءات قبل أول استدعاء خارجي |
| `writes_in_loops` | كتابات حالة داخل حلقات (gas griefing risk) |
| `delegatecalls_count` | عدد delegatecall (storage collision risk) |

#### 4. Cross-Function Risk Analysis

الدالة `find_cross_function_risks()` تكشف:

```
withdraw() يستدعي msg.sender.call{value:...}
    ← أثناء الاستدعاء، المهاجم يستدعي →
getBalance() يقرأ balances[user]
    ← القيمة لم تُحدَّث بعد! →
```

### API

```python
extractor = ExecutionSemanticsExtractor(config={
    "analyze_view_pure": True,  # هل تحلل view/pure (default: True)
})

# استخراج timelines لكل الدوال
timelines = extractor.extract(contracts)

# استخراج لدالة واحدة
timeline = extractor.extract_for_function("VaultContract", func)

# كشف مخاطر cross-function
risks = extractor.find_cross_function_risks(timelines, contracts)
```

---

## 5. State Mutation Tracker

**الملف**: `state_extraction/state_mutation.py` — 463 سطر  
**الكلاس**: `StateMutationTracker`

### الغرض

بناء نموذج رياضي لتحولات الحالة:

$$State(t+1) = State(t) + \sum_{i=0}^{n} \delta_i$$

حيث كل $\delta_i$ هو تغيير واحد مرتب (`StateDelta`).

### المدخلات والمخرجات

```python
# المدخل
contracts: List[ParsedContract]

# المخرج
mutations: List[StateMutation]  # واحد لكل دالة تكتب حالة
```

### ماذا يفعل بالتحديد

#### 1. بناء StateMutation

لكل دالة، يمر على عملياتها المرتبة ويصنفها إلى:

- **Preconditions** (شروط مسبقة): كل `require` / `assert` / `revert`
- **State Reads** (قراءات): كل `STATE_READ` / `MAPPING_ACCESS`
- **Deltas** (تغييرات مرتبة): كل `STATE_WRITE` مع تحليل العملية
- **Call Points** (نقاط استدعاء): كل `EXTERNAL_CALL` / `DELEGATECALL`

```python
# مثال: withdraw(amount) — المُخترَق
StateMutation(
    function_name="withdraw",
    contract_name="VulnerableVault",
    preconditions=["balances[msg.sender] >= amount", "success"],
    state_reads=[],
    deltas=[
        StateDelta(delta_index=0, variable="balances",       operation="-=", expression="amount", line=9),
        StateDelta(delta_index=1, variable="totalDeposits",  operation="-=", expression="amount", line=10),
    ],
    call_points=[
        ExternalCallPoint(
            call_index=0, target="msg.sender", call_type="call_eth",
            sends_eth=True, line=5,
            deltas_before=0,  # ← لا تغييرات قبل الاستدعاء!
            deltas_after=2,   # ← تغييران بعد الاستدعاء!
        ),
    ],
    net_effect={
        "balances": "-amount",
        "totalDeposits": "-amount",
    },
    writes_after_calls=True,   # ← ⚠️ هذا خطير
    calls_between_deltas=False,
)
```

#### 2. تحليل نوع العملية (Delta Parsing)

يحلل النص الخام لكل كتابة حالة لتحديد نوع العملية الرياضية:

| النمط في الكود | العملية | التعبير |
|----------------|---------|---------|
| `balance += amount` | `+=` | `amount` |
| `balance -= amount` | `-=` | `amount` |
| `balance *= factor` | `*=` | `factor` |
| `balance /= divisor` | `/=` | `divisor` |
| `balance = newValue` | `=` | `newValue` |
| `delete mapping[key]` | `delete` | `0` |
| `array.push(item)` | `push` | `...` |
| `array.pop()` | `pop` | `...` |
| `counter++` | `+=` | `1` |
| `counter--` | `-=` | `1` |

#### 3. ExternalCallPoint — نافذة إعادة الدخول

الأهم في `StateMutation` هو `call_points[]` — كل نقطة استدعاء خارجي تحتوي:

```python
ExternalCallPoint(
    call_index=0,
    target="msg.sender",
    call_type="call_eth",     # call / call_eth / delegatecall
    sends_eth=True,
    value_expression="amount",
    line=5,
    step_index=3,             # موقعها في ExecutionTimeline
    deltas_before=0,          # كم delta قبل هذا Call
    deltas_after=2,           # كم delta بعد هذا Call
    reads_consumed=["balances"],
)
```

**القاعدة الحرجة:**
- إذا `deltas_before=0` و `deltas_after>0` → **Classic CEI violation** (كل التغييرات بعد الاستدعاء)
- إذا `deltas_before>0` و `deltas_after>0` → **Partial state reentrancy** (حالة مجزأة أثناء الاستدعاء)
- إذا `deltas_before>0` و `deltas_after=0` → **CEI compliant** (آمن)

#### 4. Net Effect — التأثير الصافي

يحسب التأثير الصافي لكل متغير عبر كل الـ deltas:

```python
net_effect = {
    "balances": "-amount",        # balance -= amount
    "totalDeposits": "-amount",   # totalDeposits -= amount
}
```

#### 5. مؤشرات المخاطر

| المؤشر | المعنى |
|--------|--------|
| `writes_after_calls=True` | كتابة حالة بعد استدعاء خارجي → CEI violation |
| `calls_between_deltas=True` | استدعاء بين تغييرين → partial state reentrancy |
| `reads_before_calls=True` | قراءة قبل استدعاء → stale read risk |

### API

```python
tracker = StateMutationTracker()

# تتبع كل الدوال
mutations = tracker.track(contracts)

# تتبع دالة واحدة
mutation = tracker.track_function(contract, func)
```

---

## 6. Function Effect Model

**الملف**: `state_extraction/function_effects.py` — 365 سطر  
**الكلاس**: `FunctionEffectModeler`

### الغرض

بناء نموذج:

$$\Delta State = f(inputs)$$

لكل دالة — يصف بالكامل ماذا تأخذ، ماذا تقرأ، ماذا تكتب، وماذا تؤثر على الخارج.

### المدخلات والمخرجات

```python
# المدخل
contracts: List[ParsedContract]
mutations: Optional[List[StateMutation]]  # من المرحلة السابقة

# المخرج
effects: List[FunctionEffect]  # واحد لكل دالة
```

### ماذا يفعل بالتحديد

#### 1. بناء FunctionEffect

```python
FunctionEffect(
    function_name="withdraw",
    contract_name="VulnerableVault",
    signature="withdraw(uint256)",
    
    # المدخلات
    parameters=[{"name": "amount", "type": "uint256"}],
    msg_value_used=False,
    msg_sender_used=True,
    
    # القراءات
    reads=["balances"],
    reads_from_external=[],
    
    # الكتابات (مع Net Delta من StateMutation)
    writes=["balances", "totalDeposits"],
    net_delta={
        "balances": "-amount",
        "totalDeposits": "-amount",
    },
    
    # التأثيرات الخارجية
    external_calls=[
        {"target": "msg.sender", "type": "external_call_eth", "sends_eth": True, "line": 5}
    ],
    eth_sent=True,
    events_emitted=["Withdraw"],
    
    # متطلبات الوصول
    requires_access=False,
    access_roles=[],
    reentrancy_guarded=False,
    
    # التبعيات عبر الدوال
    conflicts_with=["deposit", "safeWithdraw", "executeStrategy"],
    depends_on=[],
)
```

#### 2. Cross-Function Dependencies

بعد بناء كل الـ effects، يحل التبعيات:

**conflicts_with** — دوال تكتب نفس المتغير (Write-Write conflict):
```
withdraw() writes: [balances, totalDeposits]
deposit()  writes: [balances, totalDeposits]
→ withdraw.conflicts_with = ["deposit", ...]
```

**depends_on** — دوال تكتب ما نقرأه (Read-After-Write dependency):
```
getBalance() reads: [balances]
withdraw()   writes: [balances]
→ getBalance.depends_on = ["withdraw", ...]
```

#### 3. Attack Surface Analysis

الدالة `analyze_attack_surface(effects)` تُنتج:

```python
{
    "exposed_financial": [
        # دوال public تكتب balances بدون access control
        {"function": "Vault.withdraw", "writes": ["balances"], "guarded": False}
    ],
    "unguarded_writes": [
        # دوال بدون access control تكتب أي حالة
        {"function": "Vault.deposit", "writes": ["balances", "totalDeposits"]}
    ],
    "eth_senders": [
        # دوال ترسل ETH
        {"function": "Vault.withdraw", "guarded": False, "access_required": False}
    ],
    "delegatecall_risks": [
        # دوال تستخدم delegatecall
        {"function": "Vault.executeStrategy", "target": "strategy"}
    ],
    "high_impact": [
        # دوال تكتب أكثر من 3 متغيرات
    ]
}
```

### API

```python
modeler = FunctionEffectModeler()

# بناء نماذج لكل الدوال
effects = modeler.model(contracts, mutations)

# تحليل سطح الهجوم
surface = modeler.analyze_attack_surface(effects)
```

---

## 7. Temporal Dependency Graph

**الملف**: `state_extraction/temporal_graph.py` — 513 سطر  
**الكلاس**: `TemporalDependencyGraph`

### الغرض

بناء **رسم بياني للتبعيات الزمنية** يربط بين العمليات عبر الدوال والعقود. هذا هو المكون الذي يجيب على سؤال الناقد: **"متى تحدث التغييرات بالنسبة لأحداث أخرى"**.

### المدخلات والمخرجات

```python
# المدخل
timelines: List[ExecutionTimeline]      # من Step 7a
mutations: List[StateMutation]          # من Step 7b
effects: List[FunctionEffect]           # من Step 7c
contracts: List[ParsedContract]         # الأساسي

# المخرج
analysis: TemporalAnalysis  # يجمع كل شيء
```

### ماذا يفعل بالتحديد

يبني 4 أنواع من الأضلاع الزمنية (`TemporalEdge`):

#### Step 1: Intra-Function Temporal Edges

أضلاع **داخل الدالة الواحدة** — يربط بين العمليات حسب الترتيب:

```
call_then_update:
  withdraw.step[1] (external_call_eth → msg.sender)
    ──temporal──→
  withdraw.step[3] (state_write → balances)
  
  Description: "External call to msg.sender (step 1, line 5)
  happens BEFORE state update balances (step 3, line 9).
  Reentrancy window: attacker can re-enter while balances
  still has old value."
  
  is_vulnerability: True
  vulnerability_type: "reentrancy"
  vulnerability_severity: "critical"
```

```
reads_then_calls:
  withdraw.step[0] (state_read → balances)
    ──temporal──→
  withdraw.step[1] (external_call_eth)
  
  Description: "State balances read before external call.
  Value may be stale if re-entered."
```

#### Step 2: Mutation Ordering Edges

أضلاع من **نقاط الاستدعاء بين التغييرات** في `StateMutation`:

```
call_between_deltas:
  إذا كان هناك:
    delta[0]: balance -= amount     (step 3)
    call_point: strategy.delegatecall()  (step 5) ← بين التغييرين!
    delta[1]: totalSupply -= amount (step 7)
  
  → Edge: "External call at step 5 splits state updates:
     balance updated before call, totalSupply updated after.
     State is partially updated during call."

classic_cei_violation:
  إذا كان كل التغييرات بعد الاستدعاء (deltas_before=0):
  → Edge: "All state writes happen AFTER external call.
     Classic CEI violation."
```

#### Step 3: Cross-Function Dependency Edges

أضلاع **بين دوال مختلفة** عبر متغيرات مشتركة:

```
cross_function:
  withdraw() writes [balances] + makes external call
  getBalance() reads [balances] (public/external)
  
  → Edge: "withdraw writes balances and makes external call.
     getBalance reads balances. If write happens after call,
     attacker can re-enter via getBalance to read stale balances."
  
  is_vulnerability: True
  vulnerability_type: "cross_function_reentrancy"
```

#### Step 4: Write-Write Conflict Edges

أضلاع **تعارض الكتابة** بين دالتين:

```
write_write:
  withdraw() writes [balances]
  deposit()  writes [balances]
  
  → Edge: "Both Vault.withdraw and Vault.deposit write to balances.
     Concurrent or reentrant calls may cause inconsistent state."
```

#### 5. Vulnerability Aggregation

يجمع كل الأضلاع التي `is_vulnerability=True` ويبني قائمة `vulnerability_candidates`:

```python
vulnerability_candidates = [
    {
        "type": "reentrancy",
        "severity": "critical",
        "source": "VulnerableVault.withdraw",
        "target": "VulnerableVault.withdraw",
        "variable": "balances",
        "dependency": "call_then_update",
        "description": "External call to msg.sender (step 1) happens BEFORE..."
    },
    # ...
]
```

مرتبة حسب الخطورة: critical → high → medium → low.

### API

```python
tdg = TemporalDependencyGraph()
analysis = tdg.build(timelines, mutations, effects, contracts)

# الوصول للنتائج
print(analysis.total_cei_violations)
print(analysis.total_reentrancy_risks)
print(analysis.vulnerability_candidates)
```

---

## 8. نماذج البيانات

جميع النماذج معرّفة في `state_extraction/models.py`. هنا الإضافات الجديدة (v2.0):

### ExecutionStep

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `step_index` | `int` | ترتيب التنفيذ (0, 1, 2, ...) |
| `op_type` | `str` | نوع العملية (قيمة من OpType) |
| `target` | `str` | المتغير أو العنوان الهدف |
| `line` | `int` | رقم السطر في المصدر |
| `function_name` | `str` | اسم الدالة |
| `contract_name` | `str` | اسم العقد |
| `is_external_call` | `bool` | هل استدعاء خارجي |
| `is_state_write` | `bool` | هل كتابة حالة |
| `is_state_read` | `bool` | هل قراءة حالة |
| `sends_eth` | `bool` | هل يرسل ETH |
| `in_loop` | `bool` | هل داخل حلقة |
| `in_condition` | `bool` | هل داخل شرط |
| `raw_text` | `str` | النص الخام من المصدر |

### CEIViolation

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `call_step` | `int` | رقم خطوة الاستدعاء |
| `write_step` | `int` | رقم خطوة الكتابة (بعد الاستدعاء) |
| `call_target` | `str` | هدف الاستدعاء |
| `write_target` | `str` | المتغير المكتوب |
| `sends_eth` | `bool` | هل يرسل ETH |
| `violation_type` | `str` | `classic_reentrancy` / `non_eth_reentrancy` / `read_only_reentrancy_surface` |
| `severity` | `str` | `critical` / `high` / `medium` |

### ExecutionTimeline

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `function_name` | `str` | اسم الدالة |
| `contract_name` | `str` | اسم العقد |
| `visibility` | `str` | public / external / internal / private |
| `mutability` | `str` | view / pure / payable / "" |
| `has_reentrancy_guard` | `bool` | هل محمية بـ nonReentrant |
| `steps` | `List[ExecutionStep]` | كل الخطوات مرتبة |
| `cei_violations` | `List[CEIViolation]` | كل انتهاكات CEI |
| `external_calls_before_writes` | `int` | استدعاءات خارجية قبل أول كتابة |
| `state_reads_before_calls` | `int` | قراءات قبل أول استدعاء |
| `writes_in_loops` | `int` | كتابات حالة داخل حلقات |
| `delegatecalls_count` | `int` | عدد delegatecall |

### StateDelta

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `delta_index` | `int` | ترتيب التغيير |
| `variable` | `str` | اسم المتغير |
| `operation` | `str` | `=` / `+=` / `-=` / `*=` / `/=` / `delete` / `push` / `pop` / `custom` |
| `expression` | `str` | التعبير الرياضي |
| `preconditions` | `List[str]` | الشروط المتراكمة قبل هذا التغيير |
| `depends_on_reads` | `List[str]` | المتغيرات المقروءة قبل هذا التغيير |
| `line` | `int` | رقم السطر |
| `step_index` | `int` | إحالة إلى ExecutionStep |
| `in_loop` | `bool` | هل داخل حلقة |
| `conditional` | `bool` | هل داخل شرط if |

### ExternalCallPoint

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `call_index` | `int` | ترتيبها بين call points |
| `target` | `str` | هدف الاستدعاء |
| `call_type` | `str` | `call` / `call_eth` / `delegatecall` |
| `sends_eth` | `bool` | هل يرسل ETH |
| `value_expression` | `str` | تعبير المبلغ المرسل |
| `line` | `int` | رقم السطر |
| `step_index` | `int` | إحالة إلى ExecutionStep |
| `deltas_before` | `int` | عدد الـ deltas قبل هذا الاستدعاء |
| `deltas_after` | `int` | عدد الـ deltas بعد هذا الاستدعاء |
| `reads_consumed` | `List[str]` | القراءات التي حدثت قبل الاستدعاء |

### StateMutation

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `function_name` | `str` | اسم الدالة |
| `contract_name` | `str` | اسم العقد |
| `preconditions` | `List[str]` | كل require/assert |
| `state_reads` | `List[str]` | متغيرات مقروءة |
| `deltas` | `List[StateDelta]` | التغييرات المرتبة |
| `call_points` | `List[ExternalCallPoint]` | نقاط الاستدعاء الخارجي |
| `state_writes` | `List[str]` | متغيرات مكتوبة (ملخص) |
| `net_effect` | `Dict[str, str]` | التأثير الصافي `{var: expr}` |
| `writes_after_calls` | `bool` | ⚠️ هل يوجد كتابة بعد استدعاء |
| `calls_between_deltas` | `bool` | ⚠️ هل يوجد استدعاء بين تغييرين |
| `reads_before_calls` | `bool` | هل يوجد قراءات قبل استدعاء |

### FunctionEffect

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `function_name` | `str` | اسم الدالة |
| `contract_name` | `str` | اسم العقد |
| `signature` | `str` | مثل `withdraw(uint256)` |
| `parameters` | `List[Dict]` | `[{name, type}]` |
| `msg_value_used` | `bool` | هل تستخدم `msg.value` |
| `msg_sender_used` | `bool` | هل تستخدم `msg.sender` |
| `reads` | `List[str]` | متغيرات حالة مقروءة |
| `reads_from_external` | `List[str]` | قراءات من عقود خارجية |
| `writes` | `List[str]` | متغيرات حالة مكتوبة |
| `net_delta` | `Dict[str, str]` | `{var: change_expr}` |
| `external_calls` | `List[Dict]` | `[{target, type, sends_eth, line}]` |
| `eth_sent` | `bool` | هل ترسل ETH |
| `events_emitted` | `List[str]` | الأحداث المُرسلة |
| `requires_access` | `bool` | هل تحتاج صلاحية |
| `access_roles` | `List[str]` | الأدوار المطلوبة |
| `reentrancy_guarded` | `bool` | هل محمية بـ nonReentrant |
| `conflicts_with` | `List[str]` | دوال تكتب نفس المتغيرات |
| `depends_on` | `List[str]` | دوال تكتب ما نقرأه |

### TemporalEdge

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `edge_id` | `str` | `temporal_1`, `temporal_2`, ... |
| `source_function` | `str` | `Contract.function` المصدر |
| `target_function` | `str` | `Contract.function` الهدف |
| `source_step` | `int` | خطوة التنفيذ المصدر |
| `target_step` | `int` | خطوة التنفيذ الهدف |
| `dependency_type` | `str` | نوع التبعية (انظر الجدول أسفل) |
| `shared_variable` | `str` | المتغير المشترك |
| `description` | `str` | وصف نصي مفصل |
| `is_vulnerability` | `bool` | هل هذا ضلع ثغرة |
| `vulnerability_type` | `str` | نوع الثغرة |
| `vulnerability_severity` | `str` | خطورة الثغرة |

**أنواع `dependency_type`:**

| النوع | المعنى | ثغرة؟ |
|-------|--------|-------|
| `call_then_update` | استدعاء خارجي ← كتابة حالة | ✅ reentrancy |
| `reads_then_calls` | قراءة حالة ← استدعاء خارجي | ❌ (info) |
| `call_between_deltas` | استدعاء بين تغييرين | ✅ partial_state_reentrancy |
| `classic_cei_violation` | كل التغييرات بعد الاستدعاء | ✅ CEI violation |
| `cross_function` | تبعية عبر دالتين | ✅ cross_function_reentrancy |
| `write_write` | دالتان تكتبان نفس المتغير | ⚠️ إذا بدون access control |

### TemporalAnalysis

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `timelines` | `List[ExecutionTimeline]` | كل الخطوط الزمنية |
| `mutations` | `List[StateMutation]` | كل نماذج التحول |
| `effects` | `List[FunctionEffect]` | كل نماذج التأثير |
| `temporal_edges` | `List[TemporalEdge]` | كل الأضلاع الزمنية |
| `total_cei_violations` | `int` | إجمالي انتهاكات CEI |
| `total_reentrancy_risks` | `int` | إجمالي مخاطر reentrancy |
| `total_cross_function_deps` | `int` | إجمالي تبعيات cross-function |
| `total_write_conflicts` | `int` | إجمالي تعارضات الكتابة |
| `vulnerability_candidates` | `List[Dict]` | ثغرات مرتبة بالخطورة |

---

## 9. Pipeline التنفيذ

### الاستخدام الأساسي

```python
from agl_security_tool.state_extraction import StateExtractionEngine

engine = StateExtractionEngine()
result = engine.extract("path/to/contract.sol")

# الوصول للتحليل الزمني
ta = result.graph.temporal_analysis

# CEI violations
for tl in ta.timelines:
    for v in tl.cei_violations:
        print(f"[{v.severity}] {v.violation_type} in {tl.function_name}")

# State mutations
for m in ta.mutations:
    print(f"{m.function_name}: writes_after_calls={m.writes_after_calls}")

# Vulnerability candidates
for vuln in ta.vulnerability_candidates:
    print(f"[{vuln['severity']}] {vuln['type']}: {vuln['description']}")
```

### تعطيل التحليل الزمني

```python
engine = StateExtractionEngine(config={"temporal": False})
# سيعمل فقط Layer 1 بدون Dynamic State Transition Model
```

### المكونات بشكل مستقل

```python
from agl_security_tool.state_extraction import (
    ExecutionSemanticsExtractor,
    StateMutationTracker,
    FunctionEffectModeler,
    TemporalDependencyGraph,
)
from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser

# التحليل خطوة بخطوة
parser = SoliditySemanticParser()
contracts = parser.parse(source_code, "contract.sol")

exec_ext = ExecutionSemanticsExtractor()
timelines = exec_ext.extract(contracts)

mut_tracker = StateMutationTracker()
mutations = mut_tracker.track(contracts)

eff_modeler = FunctionEffectModeler()
effects = eff_modeler.model(contracts, mutations)

tdg = TemporalDependencyGraph()
analysis = tdg.build(timelines, mutations, effects, contracts)
```

### مخرج JSON الكامل

```python
result = engine.extract_source(source_code)
json_output = result.to_json(indent=2)

# JSON يحتوي:
# {
#   "graph": {
#     "temporal_analysis": {
#       "timelines": [...],
#       "mutations": [...],
#       "effects": [...],
#       "temporal_edges": [...],
#       "summary": {
#         "total_cei_violations": 3,
#         "total_reentrancy_risks": 3,
#         ...
#       },
#       "vulnerability_candidates": [...]
#     }
#   }
# }
```

---

## 10. أنواع الثغرات المكتشفة

### 1. Classic Reentrancy (إعادة الدخول الكلاسيكية)

**الخطورة**: Critical  
**النمط**:
```solidity
function withdraw(uint amount) external {
    (bool s,) = msg.sender.call{value: amount}("");  // INTERACTION
    balances[msg.sender] -= amount;                   // EFFECT (too late!)
}
```
**الكشف**: `ExecutionTimeline.cei_violations` + `TemporalEdge(type=call_then_update)`

### 2. Non-ETH Reentrancy (إعادة دخول بدون ETH)

**الخطورة**: High  
**النمط**:
```solidity
function withdraw(uint amount) external {
    token.transfer(msg.sender, amount);  // ERC777 hook!
    balances[msg.sender] -= amount;       // EFFECT after call
}
```
**الكشف**: `CEIViolation(type=non_eth_reentrancy)`

### 3. Cross-Function Reentrancy

**الخطورة**: High  
**النمط**:
```solidity
function withdraw(uint amount) external {
    msg.sender.call{value: amount}("");  // attacker re-enters via getBalance()
    balances[msg.sender] -= amount;       // not updated yet!
}
function getBalance(address u) external view returns (uint) {
    return balances[u];  // reads stale value during reentrancy
}
```
**الكشف**: `TemporalEdge(type=cross_function)` + `ExecutionSemanticsExtractor.find_cross_function_risks()`

### 4. Partial State Reentrancy

**الخطورة**: High  
**النمط**:
```solidity
function complexWithdraw(uint amount) external {
    balances[msg.sender] -= amount;       // delta[0] — updated
    msg.sender.call{value: amount}("");   // call between deltas!
    totalSupply -= amount;                // delta[1] — NOT updated during reentrancy
}
```
**الكشف**: `TemporalEdge(type=call_between_deltas)` + `StateMutation.calls_between_deltas=True`

### 5. Read-Only Reentrancy Surface

**الخطورة**: Medium  
**النمط**: دالة `view` تقرأ حالة يمكن أن تكون stale أثناء reentrancy في دالة أخرى.

### 6. Classic CEI Violation

**الخطورة**: Critical/High  
**النمط**: كل كتابات الحالة تحدث **بعد** الاستدعاء الخارجي (`deltas_before=0, deltas_after>0`).

### 7. Write-Write Conflict

**الخطورة**: Medium  
**النمط**: دالتان public بدون access control تكتبان نفس المتغير.  
**الخطر**: race condition في حالة reentrancy.

### 8. Delegatecall با Storage Collision Risk

**الكشف**: `ExecutionTimeline.delegatecalls_count > 0` + `CEI violation` على delegatecall

---

## 11. أمثلة عملية مع مخرجات حقيقية

### المثال: VulnerableVault (من الاختبار)

**المدخل:**
```solidity
contract VulnerableVault {
    mapping(address => uint256) public balances;
    uint256 public totalDeposits;
    
    function deposit() external payable {
        require(msg.value > 0);
        balances[msg.sender] += msg.value;
        totalDeposits += msg.value;
    }
    
    // مُخترَق
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;
        totalDeposits -= amount;
    }
    
    // آمن
    function safeWithdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        totalDeposits -= amount;
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
    }
    
    function executeStrategy(address strategy, bytes calldata data) external {
        require(balances[msg.sender] > 0);
        (bool success, ) = strategy.delegatecall(data);
        require(success);
        balances[msg.sender] = 0;
    }
}
```

**المخرج الفعلي:**

```
TEMPORAL ANALYSIS RESULTS:

Execution Timelines (5 functions):
  VulnerableVault.withdraw()    → 6 steps, 2 CEI violations (CRITICAL)
  VulnerableVault.safeWithdraw() → 6 steps, 0 CEI violations ✅
  VulnerableVault.executeStrategy() → 4 steps, 1 CEI violation (HIGH)
  VulnerableVault.deposit()     → 4 steps, 0 violations ✅
  VulnerableVault.getBalance()  → 1 step,  0 violations ✅

State Mutations:
  withdraw():      writes_after_calls=True  (deltas_before=0, deltas_after=2)
  safeWithdraw():  writes_after_calls=False (deltas_before=2, deltas_after=0) ✅
  executeStrategy(): writes_after_calls=True (deltas_before=0, deltas_after=1)

Temporal Edges: 15 total
  Vulnerability edges: 6
  Info edges: 9

Vulnerability Candidates (sorted by severity):
  [CRITICAL] reentrancy — withdraw → balances
  [CRITICAL] reentrancy — withdraw → totalDeposits
  [CRITICAL] classic_cei_violation — withdraw → balances
  [CRITICAL] classic_cei_violation — withdraw → totalDeposits
  [HIGH] non_eth_reentrancy — executeStrategy → balances
  [HIGH] classic_cei_violation — executeStrategy → balances

Summary:
  CEI Violations: 3
  Reentrancy Risks: 3
  JSON Output: 50,304 bytes
```

---

## 12. الـ API المتاح

### عبر StateExtractionEngine (الطريقة الموصى بها)

```python
from agl_security_tool.state_extraction import StateExtractionEngine

engine = StateExtractionEngine(config={
    "temporal": True,       # تحليل زمني (default: True)
    "validate": True,       # تحقق تناسق (default: True)
    "flatten": True,        # دمج imports (default: True)
    "project_root": "/path",
})

# ملف واحد
result = engine.extract("contract.sol")

# كود مباشر
result = engine.extract_source(solidity_code, "name.sol")

# مشروع كامل
result = engine.extract_project("project_dir/")

# الوصول
ta = result.graph.temporal_analysis
ta.timelines        # List[ExecutionTimeline]
ta.mutations         # List[StateMutation]
ta.effects           # List[FunctionEffect]
ta.temporal_edges    # List[TemporalEdge]
ta.vulnerability_candidates  # List[Dict]
```

### عبر AGLSecurityAudit (من core.py)

```python
from agl_security_tool.core import AGLSecurityAudit

audit = AGLSecurityAudit()
state_result = audit.extract_state("contract.sol")
json_str = audit.extract_state_json("contract.sol")
```

### المكونات المستقلة

```python
from agl_security_tool.state_extraction import (
    ExecutionSemanticsExtractor,
    StateMutationTracker,
    FunctionEffectModeler,
    TemporalDependencyGraph,
)
```

---

## 13. بنية الملفات

```
agl_security_tool/
└── state_extraction/
    ├── __init__.py                 # تصدير كل الكلاسات (v2.0)
    ├── models.py                   # نماذج البيانات (~1100 سطر)
    │   ├── EntityType, RelationType, ...    (Layer 1)
    │   ├── Entity, Relationship, ...        (Layer 1)
    │   ├── ExecutionStep                    ← جديد v2.0
    │   ├── CEIViolation                     ← جديد v2.0
    │   ├── ExecutionTimeline                ← جديد v2.0
    │   ├── StateDelta                       ← جديد v2.0
    │   ├── ExternalCallPoint                ← جديد v2.0
    │   ├── StateMutation                    ← جديد v2.0
    │   ├── FunctionEffect                   ← جديد v2.0
    │   ├── TemporalEdge                     ← جديد v2.0
    │   ├── TemporalAnalysis                 ← جديد v2.0
    │   ├── GraphNode, GraphEdge, ...        (Layer 1)
    │   └── FinancialGraph                   (Layer 1 + temporal_analysis field)
    │
    ├── entity_extractor.py         # استخراج الكيانات (Layer 1)
    ├── relationship_mapper.py      # رسم العلاقات (Layer 1)
    ├── fund_mapper.py              # خريطة الأموال (Layer 1)
    ├── financial_graph.py          # بناء الرسم البياني (Layer 1)
    ├── validator.py                # التحقق (Layer 1)
    │
    ├── execution_semantics.py      # ← جديد: طبقة دلالات التنفيذ (~400 سطر)
    ├── state_mutation.py           # ← جديد: متتبع تحولات الحالة (~460 سطر)
    ├── function_effects.py         # ← جديد: نموذج تأثير الدالة (~365 سطر)
    ├── temporal_graph.py           # ← جديد: رسم التبعيات الزمنية (~510 سطر)
    │
    ├── engine.py                   # المحرك الرئيسي (v2.0 — يشمل الآن Step 7)
    └── DYNAMIC_STATE_TRANSITION_MODEL.md  # هذا الملف
```

**إجمالي الكود الجديد**: ~1,735 سطر Python + ~384 سطر نماذج بيانات

---

## 14. مخرج JSON الكامل

هيكل JSON الذي يُنتجه `result.to_json()`:

```json
{
  "success": true,
  "summary": {
    "contracts_parsed": 1,
    "entities_found": 1,
    "relationships_found": 5,
    "fund_flows_found": 7,
    "validation_issues": 0
  },
  "graph": {
    "metadata": { "engine_version": "2.0.0", "extraction_time_ms": 45.2 },
    "stats": { "total_nodes": 3, "total_edges": 5 },
    "nodes": [ ... ],
    "edges": [ ... ],
    "entities": [ ... ],
    "relationships": [ ... ],
    "balances": [ ... ],
    "fund_flows": [ ... ],
    "validation": { ... },
    "temporal_analysis": {
      "timelines": [
        {
          "function_name": "withdraw",
          "contract_name": "VulnerableVault",
          "visibility": "external",
          "has_reentrancy_guard": false,
          "total_steps": 6,
          "steps": [
            { "step_index": 0, "op_type": "require", "target": "balances[msg.sender] >= amount" },
            { "step_index": 1, "op_type": "external_call_eth", "target": "msg.sender", "sends_eth": true },
            { "step_index": 2, "op_type": "require", "target": "success" },
            { "step_index": 3, "op_type": "state_write", "target": "balances", "is_state_write": true },
            { "step_index": 4, "op_type": "state_write", "target": "totalDeposits", "is_state_write": true },
            { "step_index": 5, "op_type": "emit", "target": "Withdraw" }
          ],
          "cei_violations": [
            {
              "call_step": 1, "write_step": 3,
              "call_target": "msg.sender", "write_target": "balances",
              "sends_eth": true,
              "violation_type": "classic_reentrancy",
              "severity": "critical"
            }
          ]
        }
      ],
      "mutations": [
        {
          "function_name": "withdraw",
          "preconditions": ["balances[msg.sender] >= amount", "success"],
          "deltas": [
            { "delta_index": 0, "variable": "balances", "operation": "-=", "expression": "amount" },
            { "delta_index": 1, "variable": "totalDeposits", "operation": "-=", "expression": "amount" }
          ],
          "call_points": [
            {
              "target": "msg.sender", "call_type": "call_eth",
              "sends_eth": true, "deltas_before": 0, "deltas_after": 2
            }
          ],
          "net_effect": { "balances": "-amount", "totalDeposits": "-amount" },
          "writes_after_calls": true
        }
      ],
      "effects": [
        {
          "function_name": "withdraw",
          "signature": "withdraw(uint256)",
          "reads": ["balances"],
          "writes": ["balances", "totalDeposits"],
          "net_delta": { "balances": "-amount", "totalDeposits": "-amount" },
          "eth_sent": true,
          "conflicts_with": ["deposit", "safeWithdraw", "executeStrategy"]
        }
      ],
      "temporal_edges": [
        {
          "edge_id": "temporal_1",
          "source_function": "VulnerableVault.withdraw",
          "target_function": "VulnerableVault.withdraw",
          "dependency_type": "call_then_update",
          "shared_variable": "balances",
          "is_vulnerability": true,
          "vulnerability_type": "reentrancy",
          "vulnerability_severity": "critical"
        }
      ],
      "summary": {
        "total_cei_violations": 3,
        "total_reentrancy_risks": 3,
        "total_cross_function_deps": 0,
        "total_write_conflicts": 0
      },
      "vulnerability_candidates": [
        {
          "type": "reentrancy",
          "severity": "critical",
          "source": "VulnerableVault.withdraw",
          "variable": "balances",
          "description": "External call to msg.sender happens BEFORE state update balances..."
        }
      ]
    }
  }
}
```

---

## 15. القيود والتطوير المستقبلي

### القيود الحالية

| القيد | التفاصيل |
|-------|---------|
| Static analysis only | لا يُنفذ الكود فعلياً — يحلل الترتيب بشكل ثابت |
| Single-contract focus | Cross-contract reentrancy (عبر عقود مختلفة) محدود |
| No symbolic execution | لا يحل المعادلات الرياضية — يسجل التعبيرات كنصوص |
| No assembly support | operations داخل `assembly {}` تُسجَّل لكن لا تُحلَّل بعمق |
| Regex-based delta parsing | تحليل نوع العملية يعتمد على regex وقد يخطئ في patterns معقدة |
| No inter-procedural analysis | لا يتتبع الـ state عبر internal_calls بعمق |
| No path sensitivity | لا يميز بين مسارات if/else — يعتبر كل العمليات ممكنة |

### تطوير مستقبلي

1. **Symbolic Execution Layer** — حل المعادلات لتحديد هل الثغرة exploitable فعلاً
2. **Inter-procedural tracking** — تتبع internal calls لبناء call graph كامل
3. **Cross-contract analysis** — تحليل interactions بين عقود مختلفة في مشروع
4. **Path-sensitive analysis** — تمييز الفروع الشرطية لتقليل false positives
5. **Formal verification integration** — ربط مع Z3/SMT solver للإثبات الرياضي
6. **EVM bytecode analysis** — تحليل الـ bytecode المُجَمَّع للدقة القصوى
7. **Historical vulnerability database** — مقارنة الأنماط مع ثغرات معروفة

---

## الملخص

| المقياس | Layer 1 (v1.0) | Layer 1 + DSTM (v2.0) |
|---------|----------------|------------------------|
| يستخرج كيانات وعلاقات | ✅ | ✅ |
| يبني رسم مالي | ✅ | ✅ |
| يفهم ترتيب التنفيذ | ❌ | ✅ |
| يكشف CEI violations | ❌ | ✅ |
| يبني State(t+1) = State(t) + Δ | ❌ | ✅ |
| يبني ΔState = f(inputs) | ❌ | ✅ |
| يكشف cross-function reentrancy | ❌ | ✅ |
| يكشف write-write conflicts | ❌ | ✅ |
| يحلل attack surface | ❌ | ✅ |
| يكشف temporal ordering anomalies | ❌ | ✅ |
| JSON export كامل | ✅ | ✅ (مع temporal_analysis) |

---

*AGL State Extraction Engine v2.0 — Dynamic State Transition Model*  
*آخر تحديث: فبراير 2026*
