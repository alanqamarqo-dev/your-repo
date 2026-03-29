# ورقة تصميم: بناء 14 كاشفاً جديداً وتدريب أوزانهم
# Design Paper: Building 14 New Detectors & Training Their Weights

**المؤلف:** AGL Security Tool — Detector Engineering  
**التاريخ:** يونيو 2025  
**الحالة:** مسودة تقنية  

---

## جدول المحتويات

1. [ملخص تنفيذي](#1-ملخص-تنفيذي)
2. [البنية الحالية — كيف يعمل الكاشف](#2-البنية-الحالية)
3. [مواصفات الكاشفات الـ 14 الجديدة](#3-مواصفات-الكاشفات)
4. [استراتيجية تدريب الأوزان](#4-تدريب-الأوزان)
5. [بيانات التدريب المطلوبة](#5-بيانات-التدريب)
6. [توسيع البنشمارك](#6-توسيع-البنشمارك)
7. [خطة التنفيذ](#7-خطة-التنفيذ)
8. [الأثر المتوقع على الدقة](#8-الأثر-المتوقع)

---

## 1. ملخص تنفيذي

### الوضع الحالي
- **24 كاشفاً** عاملاً عبر 5 ملفات (common, reentrancy, access_control, defi, token)
- **تغطية 63%** من أنواع الثغرات المعروفة في Bug Bounty
- **دقة استرجاع 92.3%** على 13 ثغرة معروفة (فشل في: slippage/MEV)
- **دقة إيجابية 12.9%** (نسبة إنذارات كاذبة مرتفعة)

### الهدف
بناء **14 كاشفاً جديداً** لرفع التغطية إلى **~95%** مع تحسين الدقة الإيجابية عبر:
1. أنماط كشف دقيقة (semantic, ليس regex سطحي)
2. أنماط حماية شاملة (تقليل الإنذارات الكاذبة)
3. تدريب أوزان جديدة على بيانات موسّعة

---

## 2. البنية الحالية

### 2.1 دورة حياة الكاشف (Detector Lifecycle)

```
SolidityParser ──→ ParsedContract ──→ DetectorRunner.run()
                                          │
                   ┌──────────────────────┤
                   │                      │
            detector.detect()      detector.detect()
            (contract, all)        (contract, all)
                   │                      │
                   └──────┬───────────────┘
                          ▼
                    List[Finding]
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
       RiskCore    ExploitReasoning   Dedup
     (أوزان P)      (Z3 + paths)   (±5 سطور)
           │              │              │
           └──────────────┴──────┬───────┘
                                 ▼
                          Final Report
```

### 2.2 واجهة BaseDetector المطلوبة

كل كاشف جديد **يجب** أن يرث من `BaseDetector` ويحقق:

```python
class NewDetector(BaseDetector):
    # ═══ خصائص إلزامية ═══
    DETECTOR_ID = "UNIQUE-ID"           # معرّف فريد (أحرف كبيرة + شرطات)
    TITLE = "Human-readable title"      # عنوان واضح
    SEVERITY = Severity.HIGH            # CRITICAL | HIGH | MEDIUM | LOW | INFO
    CONFIDENCE = Confidence.MEDIUM      # HIGH | MEDIUM | LOW

    # ═══ الدالة الرئيسية ═══
    def detect(self, contract: ParsedContract, 
               all_contracts: List[ParsedContract]) -> List[Finding]:
        findings = []
        # ... منطق الكشف ...
        # استخدم self._make_finding() لإنشاء النتائج
        return findings
```

### 2.3 البيانات المتاحة في ParsedContract

| الحقل | النوع | الوصف |
|-------|------|-------|
| `name` | str | اسم العقد |
| `functions` | Dict[str, ParsedFunction] | كل الدوال مع تحليلها |
| `state_vars` | Dict[str, StateVar] | متغيرات الحالة |
| `modifiers` | Dict[str, ModifierInfo] | المودفايرز |
| `inherits` | List[str] | العقود الموروثة |
| `is_upgradeable` | bool | هل العقد قابل للترقية |
| `events` | List[str] | الأحداث المعرّفة |
| `using_for` | List[Dict] | المكتبات المستخدمة |

### 2.4 البيانات المتاحة في ParsedFunction

| الحقل | النوع | الاستخدام |
|-------|------|----------|
| `operations` | List[Operation] | **العمود الفقري** — ترتيب العمليات |
| `raw_body` | str | النص الخام للدالة (لـ regex المعقد) |
| `state_reads` / `state_writes` | List[str] | المتغيرات المقروءة/المكتوبة |
| `external_calls` | List[Operation] | النداءات الخارجية |
| `require_checks` | List[str] | شروط require/assert |
| `modifiers` | List[str] | المودفايرز المطبّقة |
| `parameters` | List[Dict] | البارامترات `[{name, type}]` |
| `visibility` | str | public/external/internal/private |
| `mutability` | str | view/pure/payable/"" |
| `has_access_control` | bool | هل هناك تحكم وصول |
| `sends_eth` | bool | هل ترسل ETH |

### 2.5 أنواع العمليات (OpType) — 21 نوعاً

```
STATE_READ, STATE_WRITE, EXTERNAL_CALL, EXTERNAL_CALL_ETH,
DELEGATECALL, STATICCALL, INTERNAL_CALL, REQUIRE, ASSERT,
REVERT, EMIT, SELFDESTRUCT, LOOP_START, LOOP_BODY_OP,
LOOP_END, RETURN, ASSEMBLY, MAPPING_ACCESS, ARRAY_PUSH,
ARRAY_LENGTH, ENCODE_PACKED
```

### 2.6 نمط التسجيل (Registration Pattern)

في `detectors/__init__.py` → `_register_all_detectors()`:
```python
from .new_module import NewDetector1, NewDetector2
# ثم أضف إلى self.detectors list:
self.detectors.append(NewDetector1())
self.detectors.append(NewDetector2())
```

---

## 3. مواصفات الكاشفات الـ 14 الجديدة

### تقسيم الملفات المقترح

| الملف | الكاشفات | السبب |
|-------|---------|-------|
| `detectors/defi_advanced.py` | MISSING-SLIPPAGE, MISSING-DEADLINE, ROUNDING-DIRECTION, DOUBLE-VOTING | ثغرات DeFi متقدمة |
| `detectors/proxy_safety.py` | UNINITIALIZED-PROXY, FORCE-FEED-ETH, FROZEN-FUNDS | أمان العقود القابلة للترقية |
| `detectors/input_validation.py` | UNSAFE-DOWNCAST, MISSING-ZERO-ADDRESS, ARRAY-LENGTH-MISMATCH | التحقق من المدخلات |
| `detectors/crypto_ops.py` | SIGNATURE-REPLAY, PERMIT-FRONT-RUN | عمليات التشفير |
| `detectors/advanced_attacks.py` | RETURN-BOMB, CENTRALIZATION-RISK | هجمات متقدمة |

---

### 3.1 MISSING-SLIPPAGE-PROTECTION (الأولوية: 1 — CRITICAL)

**الوصف:** كشف عمليات swap/trade بدون حد أدنى للمخرجات (`amountOutMin = 0` أو غائب).

**نمط الثغرة:**
```solidity
// ثغرة: لا يوجد حماية من الانزلاق
router.swapExactTokensForTokens(amountIn, 0, path, to, deadline);
//                                       ↑ amountOutMin = 0!

// أو: الدالة لا تأخذ amountOutMin أصلاً
function swap(uint amount, address[] path) external {
    router.swapExactTokensForTokens(amount, 0, path, msg.sender, block.timestamp);
}
```

**خوارزمية الكشف:**
```
1. ابحث في كل دالة عن نداءات swap/exchange/trade
2. تحقق من أن amountOutMin/minAmountOut موجود كبارامتر أو متغير محلي
3. تحقق من أن القيمة ليست 0 أو block.timestamp (حماية وهمية)
4. تحقق من أنماط الحماية (slippage check بعد العملية)
```

**أنماط الكشف (Detection Patterns):**
```python
_SWAP_NAMES = {
    "swap", "swapExactTokensForTokens", "swapTokensForExactTokens",
    "swapExactETHForTokens", "swapExactTokensForETH",
    "exactInput", "exactOutput", "exactInputSingle", "exactOutputSingle",
    "exchange", "exchange_underlying",  # Curve
    "trade", "fillOrder", "swap_exact_amount_in",
}

_ZERO_SLIPPAGE_PATTERNS = [
    re.compile(r'swap\w*\([^)]*,\s*0\s*,', re.IGNORECASE),
    re.compile(r'amountOutMin\w*\s*[:=]\s*0\b'),
    re.compile(r'minAmountOut\s*[:=]\s*0\b'),
    re.compile(r'minReturn\s*[:=]\s*0\b'),
]

_PROTECTION_PATTERNS = [
    re.compile(r'require\s*\([^)]*>=\s*\w*[Mm]in', re.IGNORECASE),
    re.compile(r'slippage|slippageCheck|minOutput', re.IGNORECASE),
    re.compile(r'amountOutMin\s*[>!]', re.IGNORECASE),
]
```

**منطق تقليل الإنذارات الكاذبة:**
- تجاهل الدوال التي في `interface` أو `library`
- تجاهل الدوال `view/pure` (لا تنفذ swap فعلياً)
- تحقق من الدالة المستدعية recursively (قد يكون amountOutMin في wrapper)
- تجاهل إذا كان هناك `require(amountOut >= minAmount)` بعد swap

**Severity:** CRITICAL — يسمح بهجوم sandwich فوري  
**Confidence:** HIGH إذا `0` صريح، MEDIUM إذا بارامتر مفقود

---

### 3.2 MISSING-DEADLINE (الأولوية: 2 — HIGH)

**الوصف:** عمليات DEX بدون deadline أو باستخدام `block.timestamp` (يساوي عدم وجود deadline).

**نمط الثغرة:**
```solidity
// block.timestamp == الآن دائماً → لا حماية فعلية
router.swapExactTokensForTokens(amount, minOut, path, to, block.timestamp);
//                                                       ↑ deadline = now!
```

**خوارزمية الكشف:**
```
1. ابحث عن نداءات Router (Uniswap V2/V3, SushiSwap, PancakeSwap)
2. تحقق من وجود بارامتر deadline
3. إذا كان deadline = block.timestamp → ثغرة
4. إذا كان deadline غائباً تماماً → ثغرة
```

**أنماط الكشف:**
```python
_DEADLINE_FUNCTIONS = {
    "swapExactTokensForTokens", "swapTokensForExactTokens",
    "addLiquidity", "removeLiquidity", "addLiquidityETH",
    "removeLiquidityETH", "removeLiquidityWithPermit",
}

_FAKE_DEADLINE_PATTERNS = [
    re.compile(r'block\.timestamp\s*\)'),           # حرفياً block.timestamp كآخر بارامتر
    re.compile(r'block\.timestamp\s*\+\s*0\b'),     # +0 = لا شيء
    re.compile(r'type\(uint\d*\)\.max'),            # uint.max = لا deadline عملياً
    re.compile(r'deadline\s*[:=]\s*block\.timestamp\b'),
]
```

**Severity:** HIGH  
**Confidence:** HIGH

---

### 3.3 SIGNATURE-REPLAY (الأولوية: 3 — CRITICAL)

**الوصف:** توقيعات EIP-712/EIP-191 بدون حماية nonce أو chainId → إعادة استخدام.

**نمط الثغرة:**
```solidity
function executeWithSig(bytes memory sig, address to, uint amount) external {
    bytes32 hash = keccak256(abi.encodePacked(to, amount));
    // ↑ لا يوجد nonce ولا chainId ولا عنوان العقد!
    address signer = ECDSA.recover(hash, sig);
    require(signer == owner);
    token.transfer(to, amount);
}
```

**خوارزمية الكشف:**
```
1. ابحث عن ecrecover / ECDSA.recover / SignatureChecker
2. تتبع hash المُمرر لها للخلف
3. تحقق من أن hash يتضمن: nonce, chainId أو block.chainid, address(this)
4. تحقق من أن nonce يُزاد بعد الاستخدام
5. إذا غاب أي من {nonce, chainId} → ثغرة
```

**أنماط الكشف:**
```python
_SIGNATURE_VERIFY = [
    re.compile(r'ecrecover\s*\('),
    re.compile(r'ECDSA\.recover\s*\('),
    re.compile(r'SignatureChecker\.isValidSignatureNow\s*\('),
    re.compile(r'isValidSignature\s*\('),
]

_REPLAY_PROTECTION = [
    re.compile(r'nonce[s]?\s*\['),                    # nonces[signer]++
    re.compile(r'_useNonce|_useUnorderedNonce|useNonce'),
    re.compile(r'chain\.?id|block\.chainid'),
    re.compile(r'_DOMAIN_SEPARATOR|DOMAIN_SEPARATOR|domainSeparator'),
    re.compile(r'EIP712|_buildDomainSeparator|_domainSeparatorV4'),
    re.compile(r'_hashTypedDataV4'),
]

_NONCE_INCREMENT = [
    re.compile(r'nonce\w*\s*\+[+=]|nonce\w*\s*=\s*nonce\w*\s*\+\s*1'),
    re.compile(r'_useNonce|_useUnorderedNonce|invalidateNonce'),
]
```

**Severity:** CRITICAL — يسمح بسرقة الأموال عبر إعادة تشغيل التوقيع  
**Confidence:** HIGH إذا غاب nonce, MEDIUM إذا غاب chainId فقط

---

### 3.4 UNINITIALIZED-PROXY (الأولوية: 4 — CRITICAL)

**الوصف:** عقد Implementation قابل للترقية بدون حماية `initialize()`.

**نمط الثغرة:**
```solidity
contract VaultV1 is Initializable, UUPSUpgradeable {
    address public owner;
    
    function initialize(address _owner) public {
        // ↑ لا يوجد initializer modifier!
        owner = _owner;
    }
}
```

**خوارزمية الكشف:**
```
1. هل العقد is_upgradeable أو يرث من Initializable/UUPSUpgradeable/TransparentUpgradeable?
2. ابحث عن دالة initialize/init/setup
3. تحقق من أن الدالة تحمل modifier "initializer" أو "reinitializer"
4. تحقق من أن Constructor يستدعي _disableInitializers()
5. إذا لم يكن هناك حماية → ثغرة
```

**أنماط الكشف:**
```python
_UPGRADEABLE_PARENTS = {
    "Initializable", "UUPSUpgradeable", "TransparentUpgradeableProxy",
    "ERC1967Upgrade", "BeaconProxy", "Proxy", "ERC1967Proxy",
    "OwnableUpgradeable", "AccessControlUpgradeable",
    "PausableUpgradeable", "ReentrancyGuardUpgradeable",
}

_INIT_NAMES = {"initialize", "init", "setup", "__init", "initializer"}

_INIT_PROTECTIONS = [
    re.compile(r'\binitializer\b'),
    re.compile(r'\breinitializer\b'),
    re.compile(r'_disableInitializers\s*\(\s*\)'),
    re.compile(r'initialized\s*==?\s*false|!initialized'),
    re.compile(r'_initialized\s*==?\s*0'),
]
```

**Severity:** CRITICAL — يسمح لأي شخص بأخذ ملكية العقد  
**Confidence:** HIGH

---

### 3.5 UNSAFE-DOWNCAST (الأولوية: 5 — MEDIUM)

**الوصف:** تحويل uint256 إلى نوع أصغر (uint128, uint96, int128...) بدون فحص.

**نمط الثغرة:**
```solidity
function setPrice(uint256 newPrice) external {
    price = uint128(newPrice);  // ← إذا newPrice > 2^128 → شلّ صامت!
}
```

**خوارزمية الكشف:**
```
1. ابحث في raw_body عن أنماط casting: uint128(expr), int64(expr), إلخ
2. تحقق من أن expr هو متغير بنوع أكبر (uint256, int256)
3. تحقق من عدم وجود require/if قبل الـ cast يتحقق من الحدود
4. تجاهل إذا المكتبة SafeCast مستخدمة
5. تجاهل المعاملات الحسابية على ثوابت/literals صغيرة
```

**أنماط الكشف:**
```python
_DOWNCAST_PATTERN = re.compile(
    r'(u?int(?:8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|136|144|152|160|168|176|184|192|200|208|216|224|232|240|248))\s*\(\s*(\w+)',
)

_SAFE_CAST_PATTERNS = [
    re.compile(r'SafeCast\.to(?:Uint|Int)\d+', re.IGNORECASE),
    re.compile(r'\.toUint\d+\(|\.toInt\d+\('),
    re.compile(r'require\s*\(\s*\w+\s*[<>=!]+.*?(?:type\(|MAX_|max\b)', re.IGNORECASE),
]
```

**Severity:** MEDIUM (HIGH إذا كان على قيمة مالية — balance, amount, price)  
**Confidence:** MEDIUM

---

### 3.6 RETURN-BOMB (الأولوية: 6 — HIGH)

**الوصف:** external call يمكن أن يعيد بيانات ضخمة → استنزاف gas المستدعي.

**نمط الثغرة:**
```solidity
// الهجوم: العقد الخارجي يعيد 1MB من البيانات
(bool ok, bytes memory data) = target.call(payload);
//                  ↑ نسخ بيانات غير محدودة إلى الذاكرة!
```

**خوارزمية الكشف:**
```
1. ابحث عن .call() / .staticcall() / .delegatecall() مع bytes memory return
2. تحقق من أن target هو عنوان يتحكم به مستخدم (بارامتر أو state var قابل للتغيير)
3. تحقق من عدم وجود تحديد لحجم returndata
4. تجاهل إذا target هو عنوان ثابت (immutable/constant)
```

**أنماط الكشف:**
```python
_LOW_LEVEL_CALL = re.compile(
    r'(\w+)\s*\.\s*(call|staticcall|delegatecall)\s*[\({]'
)

_RETURN_DATA_COPY = re.compile(
    r'bytes\s+memory\s+\w+\s*\)\s*=\s*\w+\.(call|staticcall|delegatecall)'
)

_PROTECTIONS = [
    re.compile(r'assembly\s*\{[^}]*returndatasize\s*\(\s*\).*?[<>]'),  # حجم محدود في assembly
    re.compile(r'ExcessivelySafeCall|excessivelySafeCall'),
    re.compile(r'returnbomb|RETURN_BOMB', re.IGNORECASE),
]
```

**Severity:** HIGH  
**Confidence:** MEDIUM (يعتمد على ما إذا كان target قابلاً للتحكم)

---

### 3.7 DOUBLE-VOTING (الأولوية: 7 — HIGH)

**الوصف:** نظام تصويت يسمح بـ vote → transfer tokens → vote again.

**نمط الثغرة:**
```solidity
function vote(uint proposalId) external {
    require(balanceOf(msg.sender) > 0);
    // ← يتحقق من الرصيد الحالي فقط!
    votes[proposalId] += balanceOf(msg.sender);
    // بعد التصويت: transfer() → صوّت من حساب آخر
}
```

**خوارزمية الكشف:**
```
1. ابحث عن دوال vote/castVote/submitVote
2. تحقق من أن التصويت يعتمد على balanceOf أو getVotes الآني
3. تحقق من عدم وجود snapshot/checkpoint mechanism
4. تحقق من عدم وجود hasVoted[msg.sender][proposalId] flag
```

**أنماط الكشف:**
```python
_VOTE_NAMES = {"vote", "castVote", "castVoteWithReason", "submitVote", "castVoteBySig"}

_SNAPSHOT_PATTERNS = [
    re.compile(r'getPastVotes|getVotesAtBlock|getPriorVotes'),
    re.compile(r'_checkpoints|_snapshot|snapshotId'),
    re.compile(r'checkpoint\s*\(|_writeCheckpoint'),
    re.compile(r'ERC20Votes|ERC20VotesComp|GovernorVotes'),
]

_ALREADY_VOTED = [
    re.compile(r'hasVoted\s*\['),
    re.compile(r'receipt\.hasVoted|voted\['),
    re.compile(r'require.*!.*voted|require.*!.*hasVoted'),
]
```

**Severity:** HIGH  
**Confidence:** MEDIUM

---

### 3.8 CENTRALIZATION-RISK (الأولوية: 8 — MEDIUM)

**الوصف:** عنوان واحد (owner) يمكنه سحب/إيقاف/ترقية بدون timelock أو multisig.

**نمط الثغرة:**
```solidity
function emergencyWithdraw() external onlyOwner {
    token.transfer(owner, token.balanceOf(address(this)));
    // ← owner واحد يأخذ كل الأموال فوراً!
}
```

**خوارزمية الكشف:**
```
1. ابحث عن دوال بها onlyOwner/onlyAdmin/onlyRole + (transfer/withdraw/pause/upgrade/setFee)
2. تحقق من قيمة TVL المحتملة (هل العقد يحتفظ بأموال)
3. تحقق من عدم وجود timelock/multisig/governance
4. أعطِ medium severity (ليست bug تقنية، لكن risk)
```

**أنماط الكشف:**
```python
_PRIVILEGED_OPS = [
    re.compile(r'transfer\s*\(\s*(owner|admin|msg\.sender)\s*,'),
    re.compile(r'withdraw\w*\s*\('),
    re.compile(r'pause\s*\(\s*\)|unpause\s*\(\s*\)'),
    re.compile(r'upgradeTo\w*\s*\('),
    re.compile(r'set(?:Fee|Rate|Price|Oracle|Admin|Owner)\s*\('),
    re.compile(r'selfdestruct\s*\(|suicide\s*\('),
]

_DECENTRALIZATION_PATTERNS = [
    re.compile(r'TimeLock|timelock|Timelock|TimelockController'),
    re.compile(r'[Mm]ulti[Ss]ig|gnosis|Safe\b'),
    re.compile(r'[Gg]overnor|governance|DAO\b'),
    re.compile(r'renounceOwnership\s*\(\s*\)'),
    re.compile(r'TIMELOCK_ADMIN_ROLE|PROPOSER_ROLE'),
]
```

**Severity:** MEDIUM  
**Confidence:** MEDIUM

---

### 3.9 ROUNDING-DIRECTION (الأولوية: 9 — HIGH)

**الوصف:** عمليات حسابية يكون فيها التقريب لصالح المستخدم وليس البروتوكول.

**نمط الثغرة:**
```solidity
// عند الإيداع: يجب التقريب لأسفل (أقل أسهم للمستخدم)
shares = assets * totalSupply / totalAssets;  // ← يقرّب لأسفل ✓

// عند السحب: يجب التقريب لأعلى (أكثر أصول مطلوبة)
assets = shares * totalAssets / totalSupply;  // ← يقرّب لأسفل ✗ (يجب لأعلى!)
```

**خوارزمية الكشف:**
```
1. حدد دوال withdraw/redeem/burn (عمليات خروج)
2. ابحث عن عمليات القسمة فيها
3. تحقق من أن التقريب يكون لأعلى (mulDivUp, ceil, +1)
4. حدد دوال deposit/mint (عمليات دخول)
5. تحقق من أن التقريب يكون لأسفل (mulDivDown, floor)
6. إذا كان التقريب خاطئاً → ثغرة
```

**أنماط الكشف:**
```python
_WITHDRAW_NAMES = {"withdraw", "redeem", "burn", "removeLiquidity", "unstake", "exit"}
_DEPOSIT_NAMES = {"deposit", "mint", "stake", "addLiquidity", "enter", "supply"}

# التقريب لأعلى (مطلوب في withdraw)
_ROUND_UP = [
    re.compile(r'mulDivUp|mulDiv\w*Up|ceilDiv|divUp'),
    re.compile(r'\+\s*(?:1|totalSupply\s*-\s*1)\s*\)\s*/'),  # (a + b - 1) / b
    re.compile(r'Math\.Rounding\.Ceil|Math\.Rounding\.Up'),
]

# التقريب لأسفل (الافتراضي — خطر في withdraw)
_PLAIN_DIVISION = re.compile(r'\w+\s*\*\s*\w+\s*/\s*\w+')
```

**Severity:** HIGH  
**Confidence:** MEDIUM

---

### 3.10 MISSING-ZERO-ADDRESS (الأولوية: 10 — LOW)

**الوصف:** بارامتر address بدون فحص `!= address(0)`.

**خوارزمية الكشف:**
```
1. ابحث عن دوال تأخذ address كبارامتر
2. تحقق من أن البارامتر يُمرر لـ transfer/approve/setOwner/critical state
3. تحقق من عدم وجود require(addr != address(0))
4. تجاهل view/pure functions
5. تجاهل إذا كانت الدالة internal/private (الفحص في المستدعي)
```

**Severity:** LOW  
**Confidence:** HIGH

---

### 3.11 FORCE-FEED-ETH (الأولوية: 11 — MEDIUM)

**الوصف:** عقد يعتمد على `address(this).balance` يمكن خداعه عبر `selfdestruct(target)`.

**نمط الثغرة:**
```solidity
function isGameOver() public view returns (bool) {
    return address(this).balance >= targetAmount;
    // ← يمكن إجبار الشرط عبر selfdestruct!
}
```

**خوارزمية الكشف:**
```
1. ابحث عن address(this).balance في شروط (require, if, return)
2. تحقق من أن الشرط يُستخدم في منطق حاسم (ليس فقط view)
3. تحقق من عدم وجود accounting داخلي (internalBalance tracking)
```

**أنماط الكشف:**
```python
_BALANCE_CHECK = re.compile(r'address\s*\(\s*this\s*\)\s*\.balance')

_INTERNAL_ACCOUNTING = [
    re.compile(r'totalDeposit|totalBalance|internalBalance|_balance'),
    re.compile(r'deposits\s*\[|balance\s*\['),  # tracking per-user
]
```

**Severity:** MEDIUM  
**Confidence:** MEDIUM

---

### 3.12 FROZEN-FUNDS (الأولوية: 12 — HIGH)

**الوصف:** عقد يستقبل ETH/tokens لكن لا يوجد آلية لسحبها.

**خوارزمية الكشف:**
```
1. هل العقد يستقبل ETH (payable functions, receive, fallback)?
2. هل هناك transfer/send/call{value} يُخرج ETH?
3. هل هناك token.transfer للـ tokens المُستقبلة?
4. إذا يستقبل ولا يُخرج → أموال مجمّدة
```

**أنماط الكشف:**
```python
_RECEIVES_ETH = [
    re.compile(r'\bpayable\b'),
    re.compile(r'receive\s*\(\s*\)\s*external\s+payable'),
    re.compile(r'fallback\s*\(\s*\)\s*external\s+payable'),
]

_SENDS_ETH = [
    re.compile(r'\.transfer\s*\(|\.send\s*\('),
    re.compile(r'\.call\s*\{[^}]*value'),
    re.compile(r'selfdestruct\s*\('),
]
```

**Severity:** HIGH  
**Confidence:** MEDIUM (قد يكون مقصوداً — مثل عقد burn)

---

### 3.13 PERMIT-FRONT-RUN (الأولوية: 13 — MEDIUM)

**الوصف:** استخدام `permit()` ثم `transferFrom()` في نفس المعاملة → قابل لـ front-run.

**نمط الثغرة:**
```solidity
function depositWithPermit(uint amount, uint deadline, uint8 v, bytes32 r, bytes32 s) {
    token.permit(msg.sender, address(this), amount, deadline, v, r, s);
    token.transferFrom(msg.sender, address(this), amount);
    // ← إذا front-runner استدعى permit أولاً، transferFrom تفشل!
}
```

**خوارزمية الكشف:**
```
1. ابحث عن .permit() متبوعاً بـ .transferFrom() في نفس الدالة
2. تحقق من عدم وجود try/catch حول permit
3. تحقق من عدم وجود فحص allowance قبل permit
```

**أنماط الكشف:**
```python
_PERMIT_CALL = re.compile(r'\.permit\s*\(')
_TRANSFER_FROM = re.compile(r'\.transferFrom\s*\(|\.safeTransferFrom\s*\(')

_PROTECTIONS = [
    re.compile(r'try\s+\w+\.permit'),
    re.compile(r'allowance\s*\([^)]*\)\s*>='),
    re.compile(r'if\s*\(\s*\w+\.allowance'),
]
```

**Severity:** MEDIUM  
**Confidence:** HIGH

---

### 3.14 ARRAY-LENGTH-MISMATCH (الأولوية: 14 — HIGH)

**الوصف:** دوال batch تأخذ مصفوفتين+ بدون فحص تطابق الأطوال.

**نمط الثغرة:**
```solidity
function batchTransfer(address[] calldata to, uint[] calldata amounts) external {
    // ← لا يوجد: require(to.length == amounts.length)
    for (uint i = 0; i < to.length; i++) {
        token.transfer(to[i], amounts[i]);  // ← out of bounds إذا amounts أقصر!
    }
}
```

**خوارزمية الكشف:**
```
1. ابحث عن دوال بها 2+ بارامتر من نوع array ([]calldata, []memory)
2. تحقق من وجود require(a.length == b.length) أو ما يعادله
3. تجاهل إذا المصفوفات لا تُستخدم معاً في loop
```

**أنماط الكشف:**
```python
_MULTIPLE_ARRAYS = re.compile(
    r'(\w+)\s*\[\s*\]\s+(?:calldata|memory)\s+(\w+).*?'
    r'(\w+)\s*\[\s*\]\s+(?:calldata|memory)\s+(\w+)',
    re.DOTALL
)

_LENGTH_CHECK = re.compile(
    r'require\s*\([^)]*\.length\s*==\s*\w+\.length'
)
```

**Severity:** HIGH  
**Confidence:** HIGH

---

## 4. تدريب الأوزان

### 4.1 النظام الحالي

```
WeightOptimizer (weight_optimizer.py)
    │
    ├── fit(X, y) → TrainingResult
    │     X = [[S_f, S_h, S_p, E], ...]   (4 أبعاد)
    │     y = [1, 0, ...]                  (هل قابل للاستغلال فعلاً)
    │
    │     P = σ(w_f·S_f + w_h·S_h + w_p·S_p + w_e·E + β)
    │
    │     Loss = BCE + L2
    │     Optimizer = mini-batch SGD
    │
    ├── extract_training_data(benchmark_dict) → (X, y)
    │     يحوّل نتائج البنشمارك إلى بيانات تدريب
    │
    └── save_weights() → artifacts/risk_weights.json

RiskCore (risk_core.py) يقرأ الأوزان:
    DEFAULT_WEIGHTS = {
        w_formal:    3.5    # ← وزن الإثبات الرسمي
        w_heuristic: 1.5    # ← وزن الكشف الاستدلالي
        w_profit:    1.2    # ← وزن الربحية
        w_exploit:   4.0    # ← وزن إثبات الاستغلال
        bias:       -1.5    # ← الانحياز الأولي
    }
```

### 4.2 كيف يؤثر كل كاشف جديد على الأوزان

كل كاشف ينتج `Finding` → يمر بـ RiskCore → يحصل على 4 ميزات:

| الميزة | كيف تتحدد | تأثير الكاشف الجديد |
|--------|----------|-------------------|
| `S_f` (formal_score) | هل Z3 أثبته | معظم الكواشف الجديدة → S_f = 0 (لا Z3) |
| `S_h` (heuristic_score) | عدد الأنماط المتطابقة × الثقة | **هذا يتأثر مباشرة** — confidence الكاشف |
| `S_p` (profit_score) | هل هناك ربح مالي | يعتمد على فئة الثغرة |
| `E` (exploit_proven) | هل ExploitReasoning أثبتها | يعتمد على Z3 + path analysis |

### 4.3 استراتيجية التدريب الموصى بها

#### المرحلة 1: تدريب أولي بأوزان يدوية ← (قبل أي بيانات)

```python
# أوزان مقترحة لكل كاشف جديد حسب طبيعته
DETECTOR_WEIGHT_HINTS = {
    # ═══ الكواشف ذات الأثر المالي المباشر ═══
    "MISSING-SLIPPAGE":   {"heuristic": 0.85, "profit": 0.9, "severity_boost": 1.0},
    "SIGNATURE-REPLAY":   {"heuristic": 0.90, "profit": 0.95, "severity_boost": 1.0},
    "UNINITIALIZED-PROXY":{"heuristic": 0.95, "profit": 0.8, "severity_boost": 1.0},
    "ROUNDING-DIRECTION": {"heuristic": 0.70, "profit": 0.7, "severity_boost": 0.85},
    
    # ═══ الكواشف ذات الأثر المتوسط ═══
    "MISSING-DEADLINE":   {"heuristic": 0.75, "profit": 0.5, "severity_boost": 0.85},
    "RETURN-BOMB":        {"heuristic": 0.65, "profit": 0.3, "severity_boost": 0.85},
    "DOUBLE-VOTING":      {"heuristic": 0.80, "profit": 0.6, "severity_boost": 0.85},
    "FROZEN-FUNDS":       {"heuristic": 0.70, "profit": 0.5, "severity_boost": 0.85},
    "ARRAY-LENGTH-MISMATCH": {"heuristic": 0.80, "profit": 0.4, "severity_boost": 0.85},
    
    # ═══ الكواشف ذات الأثر المنخفض/التحذيري ═══
    "UNSAFE-DOWNCAST":    {"heuristic": 0.55, "profit": 0.3, "severity_boost": 0.6},
    "CENTRALIZATION-RISK":{"heuristic": 0.50, "profit": 0.2, "severity_boost": 0.6},
    "MISSING-ZERO-ADDRESS":{"heuristic": 0.40, "profit": 0.1, "severity_boost": 0.3},
    "FORCE-FEED-ETH":    {"heuristic": 0.60, "profit": 0.3, "severity_boost": 0.6},
    "PERMIT-FRONT-RUN":  {"heuristic": 0.65, "profit": 0.4, "severity_boost": 0.6},
}
```

#### المرحلة 2: جمع بيانات التدريب (Ground Truth)

```
لكل كاشف جديد نحتاج:
├── 10+ عقود فيها الثغرة مؤكدة (y=1)      ← من: Immunefi, Code4rena, Sherlock
├── 10+ عقود آمنة يجب ألا تُكتشف (y=0)    ← من: OpenZeppelin, Uniswap V3
└── 5+ حالات حدية (edge cases)              ← مكتوبة يدوياً
```

**مصادر بيانات التدريب:**

| المصدر | عدد العقود المتوقع | الأنواع |
|--------|-------------------|--------|
| Code4rena Reports (2023-2024) | ~200 عقد | جميع الأنواع |
| Sherlock Audits | ~150 عقد | DeFi خصوصاً |
| Immunefi Bug Reports (العامة) | ~50 عقد | الأنواع الحرجة |
| OpenZeppelin Contracts (آمنة) | ~80 عقد | كل الأنواع (y=0) |
| Damn Vulnerable DeFi | 12 عقد | الأنواع الأساسية |
| test_contracts/ الموجودة | ~10 عقود | الأنواع الحالية |
| **عقود توليدية (يدوية)** | ~70 عقد | حالات حدية |

#### المرحلة 3: التدريب الفعلي

```python
# ── الخطوة A: تشغيل البنشمارك على كل العقود ──
benchmark = BenchmarkRunner()
results = benchmark.run_ground_truth_suite(contracts_dir="training_contracts/")

# ── الخطوة B: استخراج بيانات التدريب ──
optimizer = WeightOptimizer(config=TrainingConfig(
    learning_rate=0.05,      # أقل من الافتراضي — بيانات أكثر
    epochs=2000,
    batch_size=64,
    l2_lambda=0.005,         # تقليل regularization — بيانات كافية
    early_stop_patience=100,
))

X, y = optimizer.extract_training_data(results.to_dict())

# ── الخطوة C: موازنة الفئات (Critical!) ──
# عادة: 70% y=0, 30% y=1 → نحتاج sample_weights
n_pos = sum(y)
n_neg = len(y) - n_pos
ratio = n_neg / max(1, n_pos)
sample_weights = [ratio if yi == 1 else 1.0 for yi in y]

# ── الخطوة D: التدريب مع 5-Fold Cross-Validation ──
# (هذا غير موجود حالياً → يجب إضافته!)
from random import shuffle
fold_results = []
indices = list(range(len(X)))
shuffle(indices)
fold_size = len(indices) // 5

for fold in range(5):
    val_idx = set(indices[fold * fold_size : (fold + 1) * fold_size])
    train_X = [X[i] for i in range(len(X)) if i not in val_idx]
    train_y = [y[i] for i in range(len(y)) if i not in val_idx]
    val_X = [X[i] for i in val_idx]
    val_y = [y[i] for i in val_idx]
    train_sw = [sample_weights[i] for i in range(len(y)) if i not in val_idx]
    
    result = optimizer.fit(train_X, train_y, sample_weights=train_sw)
    val_acc = evaluate(result, val_X, val_y)
    fold_results.append(val_acc)

avg_accuracy = sum(fold_results) / len(fold_results)
# إذا avg_accuracy > 0.75 → الأوزان جاهزة
```

#### المرحلة 4: معايرة الاحتمالات (Calibration)

```python
# ── بعد التدريب: تحقق من المعايرة ──
calibration = benchmark.calibrate_probabilities(results)

# المعايرة المثالية: عندما يقول P=0.8 → 80% فعلاً مستغلة
# ECE (Expected Calibration Error) يجب أن يكون < 0.1

if calibration.ece > 0.15:
    # أعد التدريب مع temperature scaling
    # T = argmin Σ -[y·log(σ(z/T)) + (1-y)·log(1-σ(z/T))]
    pass
```

### 4.4 تأثير bias الانحياز على الكواشف الجديدة

> **مشكلة معروفة:** `bias = -1.0` (risk_core.py:58) يخفض كل شيء.

**الحل المقترح:**

```python
# بدلاً من bias واحد لكل الكواشف، نستخدم bias حسب الفئة:
CATEGORY_BIAS = {
    "slippage":    -0.3,   # ← ثغرات slippage عادة حقيقية
    "replay":      -0.3,   # ← ثغرات replay عادة حقيقية
    "proxy":       -0.5,   # ← بعض false positives
    "rounding":    -0.7,   # ← كثير false positives
    "centralization": -1.2, # ← عادة تحذيرات وليست bugs
    "default":     -0.5,   # ← الافتراضي الجديد
}
```

---

## 5. بيانات التدريب المطلوبة

### 5.1 هيكل عقد التدريب

```
training_contracts/
├── slippage/
│   ├── vulnerable/
│   │   ├── uniswap_swap_no_minout.sol      # y=1
│   │   ├── curve_exchange_zero_min.sol      # y=1
│   │   └── custom_dex_no_slippage.sol       # y=1
│   ├── safe/
│   │   ├── uniswap_v3_proper_swap.sol       # y=0
│   │   ├── 1inch_with_slippage.sol          # y=0
│   │   └── custom_dex_with_check.sol        # y=0
│   └── edge/
│       ├── dynamic_slippage_calc.sol         # y=0 (حماية ديناميكية)
│       └── wrapper_passes_minout.sol         # y=0 (الفحص في wrapper)
├── signature_replay/
│   ├── vulnerable/
│   │   ├── no_nonce_permit.sol
│   │   └── missing_chainid.sol
│   ├── safe/
│   │   ├── eip712_proper.sol
│   │   └── openzeppelin_permit.sol
│   └── edge/
│       └── bitmap_nonces.sol
├── ... (14 مجلد — واحد لكل كاشف)
```

### 5.2 صيغة بيانات التدريب (JSONL)

```jsonl
{"contract": "uniswap_no_minout.sol", "detector": "MISSING-SLIPPAGE", "expected": true, "severity": "critical", "function": "swap", "line": 42, "notes": "amountOutMin=0 in router call"}
{"contract": "uniswap_v3_proper.sol", "detector": "MISSING-SLIPPAGE", "expected": false, "notes": "has amountOutMinimum param properly checked"}
```

### 5.3 عدد العقود المطلوب لكل كاشف

| الكاشف | الحد الأدنى | المُوصى | المصدر الرئيسي |
|--------|-----------|---------|---------------|
| MISSING-SLIPPAGE | 10 | 25 | Code4rena, DeFi protocols |
| MISSING-DEADLINE | 8 | 20 | Uniswap forks |
| SIGNATURE-REPLAY | 8 | 20 | EIP-712 implementations |
| UNINITIALIZED-PROXY | 8 | 15 | Proxy audits |
| UNSAFE-DOWNCAST | 10 | 30 | Solidity codebases (common) |
| RETURN-BOMB | 5 | 12 | Cross-contract calls |
| DOUBLE-VOTING | 5 | 12 | Governance protocols |
| CENTRALIZATION-RISK | 15 | 40 | كل البروتوكولات (شائع جداً) |
| ROUNDING-DIRECTION | 8 | 20 | Vault/AMM protocols |
| MISSING-ZERO-ADDRESS | 15 | 40 | كل البروتوكولات (شائع جداً) |
| FORCE-FEED-ETH | 5 | 10 | CTF challenges |
| FROZEN-FUNDS | 5 | 15 | Multi-sig, lockers |
| PERMIT-FRONT-RUN | 5 | 12 | ERC20Permit implementations |
| ARRAY-LENGTH-MISMATCH | 8 | 20 | Batch operations |
| **المجموع** | **~120** | **~290** | — |

---

## 6. توسيع البنشمارك

### 6.1 إضافات SWC_GROUND_TRUTH المطلوبة

```python
# في benchmark_runner.py — إضافة لـ SWC_GROUND_TRUTH:
EXTENDED_GROUND_TRUTH = {
    # ═══ ثغرات DeFi المتقدمة (غير موجودة في SWC) ═══
    "DEFI-001": {
        "category": "slippage",
        "severity_min": "critical",
        "exploitable": True,
        "description": "Missing slippage protection in DEX swap",
    },
    "DEFI-002": {
        "category": "deadline",
        "severity_min": "high",
        "exploitable": True,
        "description": "Missing or fake deadline in DEX transaction",
    },
    "DEFI-003": {
        "category": "rounding",
        "severity_min": "high",
        "exploitable": True,
        "description": "Incorrect rounding direction in vault/AMM",
    },
    "DEFI-004": {
        "category": "voting",
        "severity_min": "high",
        "exploitable": True,
        "description": "Double voting via token transfer",
    },
    
    # ═══ ثغرات Proxy ═══
    "PROXY-001": {
        "category": "proxy",
        "severity_min": "critical",
        "exploitable": True,
        "description": "Uninitialized upgradeable proxy",
    },
    
    # ═══ ثغرات التشفير ═══
    "CRYPTO-001": {
        "category": "signature",
        "severity_min": "critical",
        "exploitable": True,
        "description": "Signature replay — missing nonce or chainId",
    },
    "CRYPTO-002": {
        "category": "permit",
        "severity_min": "medium",
        "exploitable": True,
        "description": "Permit front-running via permit+transferFrom",
    },
    
    # ═══ ثغرات التحقق ═══
    "VALID-001": {
        "category": "input_validation",
        "severity_min": "high",
        "exploitable": True,
        "description": "Array length mismatch in batch operations",
    },
    "VALID-002": {
        "category": "casting",
        "severity_min": "medium",
        "exploitable": True,
        "description": "Unsafe integer downcast",
    },
    "VALID-003": {
        "category": "input_validation",
        "severity_min": "low",
        "exploitable": False,
        "description": "Missing zero-address validation",
    },
    
    # ═══ هجمات متقدمة ═══
    "ADV-001": {
        "category": "return_bomb",
        "severity_min": "high",
        "exploitable": True,
        "description": "Return data bomb — unbounded returndata copy",
    },
    "ADV-002": {
        "category": "force_feed",
        "severity_min": "medium",
        "exploitable": True,
        "description": "Force-fed ETH via selfdestruct",
    },
    "ADV-003": {
        "category": "frozen_funds",
        "severity_min": "high",
        "exploitable": False,
        "description": "Permanently frozen funds — no withdrawal mechanism",
    },
    "ADV-004": {
        "category": "centralization",
        "severity_min": "medium",
        "exploitable": False,
        "description": "Single-point-of-failure centralization risk",
    },
}
```

### 6.2 خريطة الكاشف → فئة البنشمارك

```python
DETECTOR_TO_GROUND_TRUTH = {
    "MISSING-SLIPPAGE":       "DEFI-001",     # slippage
    "MISSING-DEADLINE":       "DEFI-002",     # deadline
    "ROUNDING-DIRECTION":     "DEFI-003",     # rounding
    "DOUBLE-VOTING":          "DEFI-004",     # voting
    "UNINITIALIZED-PROXY":    "PROXY-001",    # proxy
    "SIGNATURE-REPLAY":       "CRYPTO-001",   # signature
    "PERMIT-FRONT-RUN":       "CRYPTO-002",   # permit
    "ARRAY-LENGTH-MISMATCH":  "VALID-001",    # input_validation
    "UNSAFE-DOWNCAST":        "VALID-002",    # casting
    "MISSING-ZERO-ADDRESS":   "VALID-003",    # input_validation
    "RETURN-BOMB":            "ADV-001",      # return_bomb
    "FORCE-FEED-ETH":         "ADV-002",      # force_feed
    "FROZEN-FUNDS":           "ADV-003",      # frozen_funds
    "CENTRALIZATION-RISK":    "ADV-004",      # centralization
}
```

---

## 7. خطة التنفيذ

### 7.1 ثلاث مراحل

```
═══════════════════════════════════════════════════════════
  المرحلة 1: الكواشف الحرجة (الأسبوع 1)
═══════════════════════════════════════════════════════════
  
   ┌─────────────────────────────────────────┐
   │  1. MISSING-SLIPPAGE     (defi_adv.py)  │ ← الأكثر تأثيراً
   │  2. SIGNATURE-REPLAY     (crypto.py)    │ ← الأخطر
   │  3. UNINITIALIZED-PROXY  (proxy.py)     │ ← الأسهل (بيانات ParsedContract جاهزة)
   │  4. MISSING-DEADLINE     (defi_adv.py)  │ ← مرتبط بـ SLIPPAGE
   │  5. ARRAY-LENGTH-MISMATCH (input.py)    │ ← الأسهل في التنفيذ
   └─────────────────────────────────────────┘
   
   بعد المرحلة 1:
   ├── إنشاء 25+ عقد تدريب (5 لكل كاشف)
   ├── تشغيل بنشمارك أولي
   └── التحقق من عدم regression في الـ 24 كاشف الموجودين

═══════════════════════════════════════════════════════════
  المرحلة 2: الكواشف المتوسطة (الأسبوع 2)
═══════════════════════════════════════════════════════════
  
   ┌─────────────────────────────────────────┐
   │  6. UNSAFE-DOWNCAST      (input.py)     │
   │  7. RETURN-BOMB          (advanced.py)  │
   │  8. DOUBLE-VOTING        (defi_adv.py)  │
   │  9. ROUNDING-DIRECTION   (defi_adv.py)  │
   │ 10. FROZEN-FUNDS         (proxy.py)     │
   └─────────────────────────────────────────┘
   
   بعد المرحلة 2:
   ├── إنشاء 25+ عقد تدريب إضافي
   ├── أول تدريب حقيقي للأوزان (50+ عقد)
   └── قياس الدقة والمعايرة

═══════════════════════════════════════════════════════════
  المرحلة 3: التحذيرات والتحسين (الأسبوع 3)
═══════════════════════════════════════════════════════════
  
   ┌─────────────────────────────────────────┐
   │ 11. CENTRALIZATION-RISK  (advanced.py)  │
   │ 12. MISSING-ZERO-ADDRESS (input.py)     │
   │ 13. FORCE-FEED-ETH      (proxy.py)     │
   │ 14. PERMIT-FRONT-RUN    (crypto.py)     │
   └─────────────────────────────────────────┘
   
   بعد المرحلة 3:
   ├── تدريب نهائي بكل البيانات (~120+ عقد)
   ├── 5-fold cross-validation
   ├── معايرة الاحتمالات (calibration)
   └── بنشمارك شامل: recall, precision, F1
```

### 7.2 ترتيب العمل لكل كاشف (Template)

```
لكل كاشف:
   1. كتابة الـ detector class               (~50-150 سطر)
   2. إضافة import + تسجيل في __init__.py      (~3 أسطر)
   3. كتابة 3 عقود اختبار (vuln, safe, edge)  (~50-100 سطر لكل عقد)
   4. كتابة unit test                          (~30-50 سطر)
   5. تشغيل على البنشمارك الحالي               (تحقق من عدم regression)
   6. تحديث GROUND_TRUTH                        (~5 أسطر)
```

### 7.3 هيكل الملفات الجديدة

```
detectors/
├── __init__.py           ← تحديث: import + تسجيل 14 كاشف
├── common.py             (بدون تغيير)
├── reentrancy.py         (بدون تغيير)
├── access_control.py     (بدون تغيير)
├── defi.py               (بدون تغيير)
├── token.py              (بدون تغيير)
├── defi_advanced.py      ← جديد: 4 كواشف (slippage, deadline, rounding, voting)
├── proxy_safety.py       ← جديد: 3 كواشف (uninitialized, force-feed, frozen)
├── input_validation.py   ← جديد: 3 كواشف (downcast, zero-addr, array-length)
├── crypto_ops.py         ← جديد: 2 كاشف (signature, permit)
└── advanced_attacks.py   ← جديد: 2 كاشف (return-bomb, centralization)

training_contracts/
├── slippage/             ← 5+ عقود
├── signature_replay/     ← 5+ عقود
├── ...                   ← 14 مجلد
└── centralization/       ← 5+ عقود

tests/
└── test_new_detectors.py ← اختبارات وحدة لكل 14 كاشف
```

---

## 8. الأثر المتوقع على الدقة

### 8.1 التحسين المتوقع

| المقياس | الحالي | بعد المرحلة 1 | بعد المرحلة 3 |
|---------|--------|-------------|-------------|
| **عدد الكاشفات** | 24 | 29 | 38 |
| **تغطية الأنواع** | 63% | 76% | ~95% |
| **Recall (استرجاع)** | 92.3% | ~95% | ~97% |
| **Precision (دقة إيجابية)** | 12.9% | ~15% | ~20%+ |
| **F1 Score** | 24.8% | ~26% | ~33%+ |

### 8.2 سبب تحسن الدقة الإيجابية

1. **أنماط حماية شاملة:** كل كاشف جديد يتحقق من 3-5 أنماط حماية (protection patterns) قبل إصدار ثغرة
2. **Confidence دقيق:** كل كاشف يحدد confidence بناءً على قوة النمط المكتشف
3. **أوزان مُدرّبة:** بدلاً من أوزان يدوية، نستخدم أوزان مُحسّنة من بيانات حقيقية
4. **Cross-validation:** يمنع التدريب الزائد (overfitting) على بيانات التدريب

### 8.3 المخاطر

| المخاطر | الاحتمال | التخفيف |
|---------|---------|--------|
| كواشف جديدة تنتج FP كثيرة | متوسط | أنماط حماية شاملة + confidence منخفض |
| Z3 timeout على الأنماط الجديدة | مرتفع | لا نعتمد على Z3 للكواشف الجديدة |
| Regression في الكواشف القديمة | منخفض | بنشمارك بعد كل إضافة |
| بيانات تدريب غير كافية | متوسط | عقود توليدية (synthetic) |

---

## الملحق A: مثال كامل — كاشف MISSING-SLIPPAGE

```python
"""
AGL DeFi Advanced Detectors — كاشفات DeFi المتقدمة
4 detectors:
1. MISSING-SLIPPAGE — swap بدون حد أدنى
2. MISSING-DEADLINE — trade بدون deadline
3. ROUNDING-DIRECTION — تقريب خاطئ في vault
4. DOUBLE-VOTING — تصويت مزدوج
"""

from typing import List, Set
import re
from . import (
    BaseDetector,
    Finding,
    Severity,
    Confidence,
    ParsedContract,
    ParsedFunction,
    OpType,
)


class MissingSlippageProtection(BaseDetector):
    """
    كشف عمليات swap/exchange بدون حماية من الانزلاق السعري.
    
    Pattern:
        router.swapExactTokensForTokens(amountIn, 0, path, to, deadline)
        // amountOutMin = 0 يسمح بهجوم sandwich
    
    Detection:
        1. Find swap/exchange calls in function body
        2. Check if amountOutMin/minReturn is present and non-zero
        3. Verify no post-swap slippage check exists
    
    Real-world: Sandwich attacks on Uniswap, SushiSwap, PancakeSwap
    """

    DETECTOR_ID = "MISSING-SLIPPAGE"
    TITLE = "Missing slippage protection in DEX swap"
    SEVERITY = Severity.CRITICAL
    CONFIDENCE = Confidence.HIGH

    _SWAP_CALL_PATTERNS = [
        # Uniswap V2-style
        re.compile(r'swap(?:Exact)?(?:Tokens?)?(?:For)?(?:Tokens?|ETH|Exact)',
                   re.IGNORECASE),
        # Uniswap V3-style
        re.compile(r'exactInput(?:Single)?|exactOutput(?:Single)?', re.IGNORECASE),
        # Curve-style
        re.compile(r'exchange(?:_underlying)?', re.IGNORECASE),
        # Generic 
        re.compile(r'\.swap\s*\(', re.IGNORECASE),
    ]

    _ZERO_MIN_PATTERNS = [
        re.compile(r',\s*0\s*,'),                    # ..., 0, ... (literal zero)
        re.compile(r'amountOutMin\w*\s*[:=]\s*0\b'),
        re.compile(r'min(?:Amount)?(?:Out)?\w*\s*[:=]\s*0\b', re.IGNORECASE),
    ]

    _SLIPPAGE_PROTECTIONS = [
        re.compile(r'require\s*\([^)]*>=\s*\w*(?:min|Min)', re.IGNORECASE),
        re.compile(r'amountOutMin\w*\s*[>!]', re.IGNORECASE),
        re.compile(r'slippage(?:Check|Tolerance|Protection)', re.IGNORECASE),
        re.compile(r'require\s*\([^)]*amount(?:Out)?\s*>=', re.IGNORECASE),
    ]

    def detect(
        self, contract: ParsedContract, all_contracts: List[ParsedContract]
    ) -> List[Finding]:
        findings = []

        if contract.contract_type in ("interface", "library"):
            return findings

        for fname, func in contract.functions.items():
            if func.mutability in ("view", "pure"):
                continue

            body = func.raw_body or ""
            if not body:
                continue

            # هل هناك نداء swap?
            has_swap = any(p.search(body) for p in self._SWAP_CALL_PATTERNS)
            if not has_swap:
                continue

            # هل amountOutMin = 0?
            has_zero_min = any(p.search(body) for p in self._ZERO_MIN_PATTERNS)
            # أو: هل amountOutMin غائب تماماً من بارامترات الدالة?
            param_names = {p.get("name", "").lower() for p in func.parameters}
            has_min_param = any(
                "min" in pn and ("amount" in pn or "out" in pn or "return" in pn)
                for pn in param_names
            )

            if not has_zero_min and has_min_param:
                continue  # لديه بارامتر min ولا يمرر 0

            # هل هناك فحص slippage بعد الـ swap?
            has_protection = any(p.search(body) for p in self._SLIPPAGE_PROTECTIONS)
            if has_protection:
                continue

            # تحقق عبر الدوال الأخرى (قد يكون wrapper)
            all_source = " ".join(
                f.raw_body or "" for f in contract.functions.values()
            )
            has_global_protection = any(
                p.search(all_source) for p in self._SLIPPAGE_PROTECTIONS
            )

            confidence = Confidence.HIGH if has_zero_min else Confidence.MEDIUM

            findings.append(
                self._make_finding(
                    contract=contract.name,
                    function=fname,
                    line=func.line_start,
                    snippet=self._extract_swap_snippet(body),
                    description=(
                        f"Function `{fname}` performs a DEX swap without "
                        f"slippage protection (amountOutMin = 0 or missing). "
                        f"An attacker can sandwich this transaction to extract "
                        f"value via MEV."
                    ),
                    recommendation=(
                        "Add a `minAmountOut` parameter and pass it to the "
                        "swap call. Never hardcode amountOutMin to 0. "
                        "Consider using a slippage tolerance (e.g., 0.5%)."
                    ),
                    references=[
                        "https://docs.uniswap.org/concepts/protocol/swaps",
                    ],
                    extra={
                        "has_zero_literal": has_zero_min,
                        "has_min_param": has_min_param,
                        "has_global_protection": has_global_protection,
                    },
                    confidence_override=confidence,
                )
            )

        return findings

    @staticmethod
    def _extract_swap_snippet(body: str) -> str:
        """استخرج سطر الـ swap من جسم الدالة."""
        for line in body.split("\n"):
            if re.search(r'swap|exchange', line, re.IGNORECASE):
                return line.strip()[:200]
        return ""
```

---

## الملحق B: تحديث __init__.py

```python
# في _register_all_detectors() أضف:

# DeFi Advanced
from .defi_advanced import (
    MissingSlippageProtection,
    MissingDeadline,
    RoundingDirection,
    DoubleVoting,
)

# Proxy Safety
from .proxy_safety import (
    UninitializedProxy,
    ForceFeedETH,
    FrozenFunds,
)

# Input Validation
from .input_validation import (
    UnsafeDowncast,
    MissingZeroAddress,
    ArrayLengthMismatch,
)

# Crypto Operations
from .crypto_ops import (
    SignatureReplay,
    PermitFrontRun,
)

# Advanced Attacks
from .advanced_attacks import (
    ReturnBomb,
    CentralizationRisk,
)

# ثم في self.detectors أضف:
# ═══ DeFi Advanced (Critical/High) ═══
MissingSlippageProtection(),
MissingDeadline(),
RoundingDirection(),
DoubleVoting(),
# ═══ Proxy Safety (Critical/High) ═══
UninitializedProxy(),
ForceFeedETH(),
FrozenFunds(),
# ═══ Input Validation (Medium/High) ═══
UnsafeDowncast(),
MissingZeroAddress(),
ArrayLengthMismatch(),
# ═══ Crypto Operations (Critical/Medium) ═══
SignatureReplay(),
PermitFrontRun(),
# ═══ Advanced Attacks (High/Medium) ═══
ReturnBomb(),
CentralizationRisk(),
```

---

## الملحق C: مخطط تدفق تدريب الأوزان الكامل

```
           ┌─────────────────────────────┐
           │  training_contracts/ (290+)  │
           │  (vulnerable + safe + edge)  │
           └──────────┬──────────────────┘
                      ▼
           ┌─────────────────────────────┐
           │   BenchmarkRunner.run()      │
           │   (38 كاشف على كل العقود)    │
           └──────────┬──────────────────┘
                      ▼
           ┌─────────────────────────────┐
           │   extract_training_data()    │
           │   X = [[S_f, S_h, S_p, E]]  │
           │   y = [0, 1, 1, 0, ...]     │
           └──────────┬──────────────────┘
                      ▼
           ┌─────────────────────────────┐
           │   class_balance(y)           │
           │   sample_weights = [...]     │
           │   (تعويض عدم التوازن)         │
           └──────────┬──────────────────┘
                      ▼
           ┌─────────────────────────────┐
           │   5-Fold Cross-Validation    │
           │                             │
           │   for fold in 1..5:          │
           │     train_X, val_X = split() │
           │     result = fit(train_X)    │
           │     val_acc = eval(val_X)    │
           └──────────┬──────────────────┘
                      ▼
           ┌─────────────────────────────┐
           │   avg(val_acc) > 0.75?       │
           │                             │
           │   نعم → أعد التدريب على الكل  │
           │   لا  → تشخيص (underfitting?) │
           └──────────┬──────────────────┘
                      ▼
           ┌─────────────────────────────┐
           │   calibrate_probabilities()  │
           │   ECE < 0.10?                │
           │                             │
           │   نعم → حفظ الأوزان          │
           │   لا  → temperature scaling  │
           └──────────┬──────────────────┘
                      ▼
           ┌─────────────────────────────┐
           │   save_weights()             │
           │   → artifacts/risk_weights.json│
           │                             │
           │   {                          │
           │     "w_formal": 3.8,         │
           │     "w_heuristic": 2.1,      │
           │     "w_profit": 1.5,         │
           │     "w_exploit": 3.6,        │
           │     "bias": -0.5             │
           │   }                          │
           └─────────────────────────────┘
```

---

## الملحق D: أمر التشغيل السريع

```bash
# ── بعد بناء كل الكواشف ──

# 1. تشغيل اختبارات الوحدة
cd <project-root>            # root of agl_security_tool checkout
python -m pytest tests/test_new_detectors.py -v

# 2. تشغيل البنشمارك مع الكواشف الجديدة
python -m agl_security_tool._benchmark_dvd

# 3. تدريب الأوزان
python -c "
from agl_security_tool.weight_optimizer import WeightOptimizer, TrainingConfig
from agl_security_tool.benchmark_runner import BenchmarkRunner

runner = BenchmarkRunner()
results = runner.run_ground_truth_suite('training_contracts/')

opt = WeightOptimizer(TrainingConfig(learning_rate=0.05, epochs=2000))
X, y = opt.extract_training_data(results.to_dict())
result = opt.fit(X, y)
opt.save_weights(result)
print(f'Accuracy: {result.final_accuracy:.4f}')
print(f'Weights: {result.weights}')
"

# 4. قياس الأداء النهائي
python tests/test_pipeline_accuracy.py
```

---

**نهاية الورقة التصميمية**

> هذه الورقة هي مرجع حي (living document) — يجب تحديثها بعد كل مرحلة
> بناءً على النتائج الفعلية للبنشمارك وتدريب الأوزان.
