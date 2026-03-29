# 🛡️ AGL Security Audit Report — Alchemix Finance V2

**Date:** 2026-02-17 01:25:34
**Bounty Program:** [Immunefi — Alchemix](https://immunefi.com/bug-bounty/alchemix/) (Max $300,000)
**Scope:** [alchemix-finance/v2-foundry/src](https://github.com/alchemix-finance/v2-foundry/tree/master/src)
**Tool:** AGL Security Tool v1.1.0 (22 detectors, 12 analysis layers)
**Files Scanned:** 32
**Total Findings:** 132

---

## Severity Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | **13** |
| 🟠 HIGH | **79** |
| 🟡 MEDIUM | **4** |
| 🔵 LOW | **36** |
| ℹ️ INFO | **0** |

---
## 🎯 Bounty-Eligible Findings (92)

These findings are potentially eligible for bounty rewards.

### 🔴 Finding #1: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `AlchemistV2.sol` (Line 559)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `deposit` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #2: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `AlchemistV2.sol` (Line 596)
- **Category:** 
- **Confidence:** high

**Description:**
Function `withdraw` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #3: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `AlchemistV2.sol` (Line 615)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `withdrawFrom` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #4: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `AlchemistV2.sol` (Line 746)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `repay` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #5: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `AlchemistV2.sol` (Line 806)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `liquidate` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #6: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `AlchemistV2.sol` (Line 918)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `harvest` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #7: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `TransmuterV2.sol` (Line 210)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `deposit` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #8: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `TransmuterV2.sol` (Line 224)
- **Category:** 
- **Confidence:** high

**Description:**
Function `withdraw` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #9: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `TransmuterBuffer.sol` (Line 345)
- **Category:** 
- **Confidence:** high

**Description:**
Function `withdraw` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #10: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `gALCX.sol` (Line 124)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `unstake` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #11: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `WETHGateway.sol` (Line 56)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `withdrawUnderlying` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #12: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `adapters/yearn/YearnTokenAdapter.sol` (Line 30)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `wrap` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🔴 Finding #13: Unprotected withdrawal function

- **Severity:** CRITICAL
- **File:** `adapters/yearn/YearnTokenAdapter.sol` (Line 39)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `unwrap` transfers value (ETH or tokens) without access control. Any address can call this function to drain funds. Add `onlyOwner` modifier or `require(msg.sender == owner)` check.

---

### 🟠 Finding #14: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 7)
- **Category:** 
- **Confidence:** high

**Description:**
Function `_wrap` has unchecked low-level call (line 7). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #15: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 10)
- **Category:** 
- **Confidence:** high

**Description:**
Function `deposit` has unchecked low-level call (line 10). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #16: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 50)
- **Category:** 
- **Confidence:** high

**Description:**
Function `repay` has unchecked low-level call (line 50). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #17: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 404)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setTokenAdapter` makes external calls without reentrancy protection and shares state variables `_yieldTokens` with public function `setYieldTokenEnabled`. An attacker can re-enter via `setYieldTokenEnabled` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #18: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 470)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setTokenAdapter` makes external calls without reentrancy protection and shares state variables `_yieldTokens` with public function `configureCreditUnlockRate`. An attacker can re-enter via `configureCreditUnlockRate` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #19: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 490)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setTokenAdapter` makes external calls without reentrancy protection and shares state variables `_yieldTokens` with public function `setMaximumExpectedValue`. An attacker can re-enter via `setMaximumExpectedValue` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #20: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 498)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setTokenAdapter` makes external calls without reentrancy protection and shares state variables `_yieldTokens` with public function `setMaximumLoss`. An attacker can re-enter via `setMaximumLoss` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #21: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1044)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `_checkYieldTokenEnabled` reads state variables `_yieldTokens` that are modified by `addYieldToken`, which also makes external calls. During the external call in `addYieldToken`, an attacker can call `_checkYieldTokenEnabled` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #22: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1100)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `_checkLoss` reads state variables `_yieldTokens` that are modified by `addYieldToken`, which also makes external calls. During the external call in `addYieldToken`, an attacker can call `_checkLoss` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #23: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1262)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `_loss` reads state variables `_yieldTokens` that are modified by `addYieldToken`, which also makes external calls. During the external call in `addYieldToken`, an attacker can call `_loss` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #24: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1459)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `_validate` reads state variables `debt` that are modified by `repay`, which also makes external calls. During the external call in `repay`, an attacker can call `_validate` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #25: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1477)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `totalValue` reads state variables `_yieldTokens` that are modified by `addYieldToken`, which also makes external calls. During the external call in `addYieldToken`, an attacker can call `totalValue` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #26: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1540)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `_calculateUnrealizedDebt` reads state variables `_yieldTokens` that are modified by `addYieldToken`, which also makes external calls. During the external call in `addYieldToken`, an attacker can call `_calculateUnrealizedDebt` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #27: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1575)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `_calculateUnrealizedActiveBalance` reads state variables `_yieldTokens` that are modified by `addYieldToken`, which also makes external calls. During the external call in `addYieldToken`, an attacker can call `_calculateUnrealizedActiveBalance` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #28: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1602)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `_calculateUnlockedCredit` reads state variables `_yieldTokens` that are modified by `addYieldToken`, which also makes external calls. During the external call in `addYieldToken`, an attacker can call `_calculateUnlockedCredit` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #29: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1627)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setTokenAdapter` makes external calls without reentrancy protection and shares state variables `_yieldTokens` with public function `convertYieldTokensToShares`. An attacker can re-enter via `convertYieldTokensToShares` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #30: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1640)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `convertSharesToYieldTokens` reads state variables `_yieldTokens` that are modified by `addYieldToken`, which also makes external calls. During the external call in `addYieldToken`, an attacker can call `convertSharesToYieldTokens` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #31: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1665)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `convertYieldTokensToUnderlying` reads state variables `_yieldTokens` that are modified by `addYieldToken`, which also makes external calls. During the external call in `addYieldToken`, an attacker can call `convertYieldTokensToUnderlying` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #32: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 1677)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `convertUnderlyingTokensToYield` reads state variables `_yieldTokens` that are modified by `addYieldToken`, which also makes external calls. During the external call in `addYieldToken`, an attacker can call `convertUnderlyingTokensToYield` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #33: Potential storage collision in proxy pattern

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 51)
- **Category:** storage-collision
- **Confidence:** 0.75

**Description:**
Contract uses delegatecall with 15 state variables but no fixed storage slots (ERC1967). State variables in proxy and implementation may collide in the same storage slots.

---

### 🟠 Finding #34: tx.origin used for authentication

- **Severity:** HIGH
- **File:** `AlchemistV2.sol` (Line 3688)
- **Category:** access-control
- **Confidence:** 0.95

**Description:**
tx.origin is used for authentication. An attacker can deploy a contract that calls this function, where msg.sender != tx.origin, bypassing the intended access control.

---

### 🟠 Finding #35: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `TransmuterV2.sol` (Line 10)
- **Category:** 
- **Confidence:** high

**Description:**
Function `deposit` has unchecked low-level call (line 10). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #36: Reentrancy vulnerability (external call before state update)

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 7)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setAlchemist` makes external call via `TokenUtils.safeApprove` (line 7) before updating `alchemist` (line 12). If the called contract has hooks (ERC777, ERC721 onReceived, etc.), an attacker can re-enter. Update state before external interactions.

---

### 🟠 Finding #37: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 141)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `getAvailableFlow` reads state variables `flowAvailable` that are modified by `withdraw`, which also makes external calls. During the external call in `withdraw`, an attacker can call `getAvailableFlow` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #38: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 160)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `getTotalCredit` reads state variables `alchemist` that are modified by `setAlchemist`, which also makes external calls. During the external call in `setAlchemist`, an attacker can call `getTotalCredit` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #39: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 160)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setAlchemist` makes external calls without reentrancy protection and shares state variables `alchemist` with public function `getTotalCredit`. An attacker can re-enter via `getTotalCredit` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #40: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 179)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setAlchemist` makes external calls without reentrancy protection and shares state variables `alchemist` with public function `setWeights`. An attacker can re-enter via `setWeights` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #41: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 216)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setAlchemist` makes external calls without reentrancy protection and shares state variables `sources` with public function `setSource`. An attacker can re-enter via `setSource` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #42: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 225)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `registerAsset` makes external calls without reentrancy protection and shares state variables `transmuter` with public function `setTransmuter`. An attacker can re-enter via `setTransmuter` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #43: Unbounded loop over storage array (DoS risk)

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 234)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setAlchemist` loops over storage array `registeredUnderlyings` without a maximum iteration limit. As the array grows, the function may exceed the block gas limit, making it permanently uncallable (DoS). Loop also contains external calls, amplifying gas cost. Add a maximum iteration limit or use pagination.

---

### 🟠 Finding #44: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 255)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `_flushToAmo` makes external calls without reentrancy protection and shares state variables `amos` with public function `setAmo`. An attacker can re-enter via `setAmo` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #45: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 305)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `registerAsset` makes external calls without reentrancy protection and shares state variables `transmuter` with public function `onERC20Received`. An attacker can re-enter via `onERC20Received` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #46: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 366)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setAlchemist` makes external calls without reentrancy protection and shares state variables `alchemist` with public function `withdrawFromAlchemist`. An attacker can re-enter via `withdrawFromAlchemist` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #47: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 375)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setAlchemist` makes external calls without reentrancy protection and shares state variables `alchemist` with public function `refreshStrategies`. An attacker can re-enter via `refreshStrategies` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #48: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 404)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `setAlchemist` makes external calls without reentrancy protection and shares state variables `alchemist` with public function `burnCredit`. An attacker can re-enter via `burnCredit` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #49: Read-only reentrancy (view function reads inconsistent state)

- **Severity:** HIGH
- **File:** `TransmuterBuffer.sol` (Line 443)
- **Category:** 
- **Confidence:** medium

**Description:**
View function `_getTotalBuffered` reads state variables `alchemist` that are modified by `setAlchemist`, which also makes external calls. During the external call in `setAlchemist`, an attacker can call `_getTotalBuffered` and observe inconsistent state (read-only reentrancy). Use a reentrancy guard on view functions that read sensitive state, or ensure state is updated before external calls.

---

### 🟠 Finding #50: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `StakingPools.sol` (Line 8)
- **Category:** 
- **Confidence:** high

**Description:**
Function `_deposit` has unchecked low-level call (line 8). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #51: Unchecked ERC20 transfer return value

- **Severity:** HIGH
- **File:** `gALCX.sol` (Line 2)
- **Category:** 
- **Confidence:** high

**Description:**
Function `reApprove` calls `alcx.approve()` (line 2) without checking the return value. Some ERC20 tokens (USDT, BNB) return `false` instead of reverting on failure. The token transfer may silently fail. Use OpenZeppelin's `SafeERC20` library: `using SafeERC20 for IERC20; token.safeTransfer(...)`

---

### 🟠 Finding #52: Reentrancy vulnerability (external call before state update)

- **Severity:** HIGH
- **File:** `gALCX.sol` (Line 8)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `migrateSource` makes external call via `alcx.approve` (line 8) before updating `pools` (line 10). If the called contract has hooks (ERC777, ERC721 onReceived, etc.), an attacker can re-enter. Update state before external interactions.

---

### 🟠 Finding #53: Unchecked ERC20 transfer return value

- **Severity:** HIGH
- **File:** `gALCX.sol` (Line 8)
- **Category:** 
- **Confidence:** high

**Description:**
Function `migrateSource` calls `alcx.approve()` (line 8) without checking the return value. Some ERC20 tokens (USDT, BNB) return `false` instead of reverting on failure. The token transfer may silently fail. Use OpenZeppelin's `SafeERC20` library: `using SafeERC20 for IERC20; token.safeTransfer(...)`

---

### 🟠 Finding #54: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `gALCX.sol` (Line 90)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `migrateSource` makes external calls without reentrancy protection and shares state variables `poolId, alcx, pools` with public function `bumpExchangeRate`. An attacker can re-enter via `bumpExchangeRate` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #55: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `EthAssetManager.sol` (Line 2)
- **Category:** 
- **Confidence:** high

**Description:**
Function `sweepToken` has unchecked low-level call (line 2). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #56: Potential storage collision in proxy pattern

- **Severity:** HIGH
- **File:** `EthAssetManager.sol` (Line 456)
- **Category:** storage-collision
- **Confidence:** 0.75

**Description:**
Contract uses delegatecall with 7 state variables but no fixed storage slots (ERC1967). State variables in proxy and implementation may collide in the same storage slots.

---

### 🟠 Finding #57: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `ThreePoolAssetManager.sol` (Line 2)
- **Category:** 
- **Confidence:** high

**Description:**
Function `sweep` has unchecked low-level call (line 2). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #58: Potential storage collision in proxy pattern

- **Severity:** HIGH
- **File:** `ThreePoolAssetManager.sol` (Line 492)
- **Category:** storage-collision
- **Confidence:** 0.75

**Description:**
Contract uses delegatecall with 8 state variables but no fixed storage slots (ERC1967). State variables in proxy and implementation may collide in the same storage slots.

---

### 🟠 Finding #59: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `TwoPoolAssetManager.sol` (Line 2)
- **Category:** 
- **Confidence:** high

**Description:**
Function `sweep` has unchecked low-level call (line 2). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #60: Potential storage collision in proxy pattern

- **Severity:** HIGH
- **File:** `TwoPoolAssetManager.sol` (Line 399)
- **Category:** storage-collision
- **Confidence:** 0.75

**Description:**
Contract uses delegatecall with 9 state variables but no fixed storage slots (ERC1967). State variables in proxy and implementation may collide in the same storage slots.

---

### 🟠 Finding #61: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `PoolAssetManager.sol` (Line 2)
- **Category:** 
- **Confidence:** high

**Description:**
Function `sweep` has unchecked low-level call (line 2). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #62: Potential storage collision in proxy pattern

- **Severity:** HIGH
- **File:** `PoolAssetManager.sol` (Line 341)
- **Category:** storage-collision
- **Confidence:** 0.75

**Description:**
Contract uses delegatecall with 7 state variables but no fixed storage slots (ERC1967). State variables in proxy and implementation may collide in the same storage slots.

---

### 🟠 Finding #63: Unchecked ERC20 transfer return value

- **Severity:** HIGH
- **File:** `WETHGateway.sol` (Line 2)
- **Category:** 
- **Confidence:** high

**Description:**
Function `refreshAllowance` calls `WETH.approve()` (line 2) without checking the return value. Some ERC20 tokens (USDT, BNB) return `false` instead of reverting on failure. The token transfer may silently fail. Use OpenZeppelin's `SafeERC20` library: `using SafeERC20 for IERC20; token.safeTransfer(...)`

---

### 🟠 Finding #64: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `WETHGateway.sol` (Line 14)
- **Category:** 
- **Confidence:** high

**Description:**
Function `withdrawUnderlying` has unchecked low-level call (line 14). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #65: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `WETHGateway.sol` (Line 22)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `withdrawUnderlying` makes external calls without reentrancy protection and shares state variables `WETH` with public function `constructor`. An attacker can re-enter via `constructor` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #66: tx.origin used for authentication

- **Severity:** HIGH
- **File:** `WETHGateway.sol` (Line 1499)
- **Category:** access-control
- **Confidence:** 0.95

**Description:**
tx.origin is used for authentication. An attacker can deploy a contract that calls this function, where msg.sender != tx.origin, bypassing the intended access control.

---

### 🟠 Finding #67: Authentication via tx.origin

- **Severity:** HIGH
- **File:** `AutoleverageBase.sol` (Line 3)
- **Category:** 
- **Confidence:** high

**Description:**
Function `autoleverage` uses `tx.origin` for authentication (line 3). This is vulnerable to phishing attacks: an attacker can trick the owner into calling a malicious contract, which then calls your contract with the owner's `tx.origin`. Use `msg.sender` instead.

---

### 🟠 Finding #68: Flash loan callback without sender validation

- **Severity:** HIGH
- **File:** `AutoleverageBase.sol` (Line 131)
- **Category:** 
- **Confidence:** medium

**Description:**
Flash loan callback `executeOperation` does not validate `msg.sender` (should be the lending pool) or `initiator` (should be this contract). An attacker can call this function directly, bypassing the flash loan mechanism to execute arbitrary operations. Add: `require(msg.sender == address(POOL))` and `require(initiator == address(this))`.

---

### 🟠 Finding #69: tx.origin used for authentication

- **Severity:** HIGH
- **File:** `AutoleverageBase.sol` (Line 1504)
- **Category:** access-control
- **Confidence:** 0.95

**Description:**
tx.origin is used for authentication. An attacker can deploy a contract that calls this function, where msg.sender != tx.origin, bypassing the intended access control.

---

### 🟠 Finding #70: tx.origin used for authentication

- **Severity:** HIGH
- **File:** `AutoleverageCurveFactoryethpool.sol` (Line 1551)
- **Category:** access-control
- **Confidence:** 0.95

**Description:**
tx.origin is used for authentication. An attacker can deploy a contract that calls this function, where msg.sender != tx.origin, bypassing the intended access control.

---

### 🟠 Finding #71: tx.origin used for authentication

- **Severity:** HIGH
- **File:** `AutoleverageCurveMetapool.sol` (Line 1528)
- **Category:** access-control
- **Confidence:** 0.95

**Description:**
tx.origin is used for authentication. An attacker can deploy a contract that calls this function, where msg.sender != tx.origin, bypassing the intended access control.

---

### 🟠 Finding #72: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `migration/MigrationTool.sol` (Line 52)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `migrateVaults` makes external calls without reentrancy protection and shares state variables `alchemicToken, alchemist` with public function `constructor`. An attacker can re-enter via `constructor` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #73: Potential storage collision in proxy pattern

- **Severity:** HIGH
- **File:** `migration/MigrationTool.sol` (Line 60)
- **Category:** storage-collision
- **Confidence:** 0.75

**Description:**
Contract uses delegatecall with 4 state variables but no fixed storage slots (ERC1967). State variables in proxy and implementation may collide in the same storage slots.

---

### 🟠 Finding #74: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `adapters/yearn/YearnTokenAdapter.sol` (Line 2)
- **Category:** 
- **Confidence:** high

**Description:**
Function `wrap` has unchecked low-level call (line 2). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #75: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `adapters/lido/WstETHAdapter.sol` (Line 3)
- **Category:** 
- **Confidence:** high

**Description:**
Function `wrap` has unchecked low-level call (line 3). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #76: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `adapters/rocket/RETHAdapterV1.sol` (Line 3)
- **Category:** 
- **Confidence:** high

**Description:**
Function `unwrap` has unchecked low-level call (line 3). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #77: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `adapters/aave/AAVETokenAdapter.sol` (Line 2)
- **Category:** 
- **Confidence:** high

**Description:**
Function `wrap` has unchecked low-level call (line 2). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #78: Reentrancy vulnerability (external call before state update)

- **Severity:** HIGH
- **File:** `adapters/aave/AAVETokenAdapter.sol` (Line 5)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `constructor` makes external call via `TokenUtils.safeApprove` (line 5) before updating `tokenDecimals` (line 6). If the called contract has hooks (ERC777, ERC721 onReceived, etc.), an attacker can re-enter. Update state before external interactions.

---

### 🟠 Finding #79: Reentrancy vulnerability (external call before state update)

- **Severity:** HIGH
- **File:** `utils/RewardRouter.sol` (Line 13)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `distributeRewards` makes external call via `TokenUtils.safeTransfer` (line 13) before updating `rewards` (line 14). If the called contract has hooks (ERC777, ERC721 onReceived, etc.), an attacker can re-enter. Update state before external interactions.

---

### 🟠 Finding #80: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `utils/RewardRouter.sol` (Line 71)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `distributeRewards` makes external calls without reentrancy protection and shares state variables `rewards` with public function `addVault`. An attacker can re-enter via `addVault` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #81: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `utils/RewardRouter.sol` (Line 81)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `distributeRewards` makes external calls without reentrancy protection and shares state variables `rewards` with public function `setRewardCollectorAddress`. An attacker can re-enter via `setRewardCollectorAddress` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #82: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `utils/RewardRouter.sol` (Line 86)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `distributeRewards` makes external calls without reentrancy protection and shares state variables `rewards` with public function `setRewardAmount`. An attacker can re-enter via `setRewardAmount` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #83: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `utils/RewardRouter.sol` (Line 91)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `distributeRewards` makes external calls without reentrancy protection and shares state variables `rewards` with public function `setRewardTimeframe`. An attacker can re-enter via `setRewardTimeframe` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #84: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `utils/RewardRouter.sol` (Line 106)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `distributeRewards` makes external calls without reentrancy protection and shares state variables `rewards` with public function `getRewardCollector`. An attacker can re-enter via `getRewardCollector` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #85: Reentrancy vulnerability (external call before state update)

- **Severity:** HIGH
- **File:** `utils/collectors/OptimismRewardCollector.sol` (Line 14)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `claimAndDonateRewards` makes external call via `TokenUtils.safeApprove` (line 14) before updating `debtToken` (line 16). If the called contract has hooks (ERC777, ERC721 onReceived, etc.), an attacker can re-enter. Update state before external interactions.

---

### 🟠 Finding #86: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `utils/collectors/OptimismRewardCollector.sol` (Line 45)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `claimAndDonateRewards` makes external calls without reentrancy protection and shares state variables `alchemist, debtToken` with public function `constructor`. An attacker can re-enter via `constructor` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #87: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `utils/collectors/OptimismRewardCollector.sol` (Line 91)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `claimAndDonateRewards` makes external calls without reentrancy protection and shares state variables `debtToken` with public function `getExpectedExchange`. An attacker can re-enter via `getExpectedExchange` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #88: Reentrancy vulnerability (external call before state update)

- **Severity:** HIGH
- **File:** `utils/collectors/ArbitrumRewardCollector.sol` (Line 10)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `claimAndDonateRewards` makes external call via `TokenUtils.safeApprove` (line 10) before updating `debtToken` (line 23). If the called contract has hooks (ERC777, ERC721 onReceived, etc.), an attacker can re-enter. Update state before external interactions.

---

### 🟠 Finding #89: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `utils/collectors/ArbitrumRewardCollector.sol` (Line 52)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `claimAndDonateRewards` makes external calls without reentrancy protection and shares state variables `alchemist, debtToken` with public function `constructor`. An attacker can re-enter via `constructor` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #90: Cross-function reentrancy

- **Severity:** HIGH
- **File:** `utils/collectors/ArbitrumRewardCollector.sol` (Line 112)
- **Category:** 
- **Confidence:** medium

**Description:**
Function `claimAndDonateRewards` makes external calls without reentrancy protection and shares state variables `ALUSD, ALETH, debtToken` with public function `getExpectedExchange`. An attacker can re-enter via `getExpectedExchange` during the external call and manipulate shared state. Apply nonReentrant modifier to both functions.

---

### 🟠 Finding #91: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `libraries/TokenUtils.sol` (Line 2)
- **Category:** 
- **Confidence:** high

**Description:**
Function `safeTransfer` has unchecked low-level call (line 2). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---

### 🟠 Finding #92: Unchecked low-level call return value

- **Severity:** HIGH
- **File:** `libraries/SafeERC20.sol` (Line 2)
- **Category:** 
- **Confidence:** high

**Description:**
Function `safeTransfer` has unchecked low-level call (line 2). The return value of `.call` / `.send` is not verified. If the call fails, execution continues silently. Capture and check: `(bool success,) = addr.call{...}(...); require(success);`

---


## 🟡 Medium Findings (4)

| # | Title | File | Line | Category |
|---|-------|------|------|----------|
| 1 | Unbounded loop over storage array (DoS risk) | TransmuterBuffer.sol | 166 | ? |
| 2 | Unbounded loop over storage array (DoS risk) | TransmuterBuffer.sol | 267 | ? |
| 3 | Unbounded loop over storage array (DoS risk) | TransmuterBuffer.sol | 375 | ? |
| 4 | Missing price freshness check (stale oracle data) | adapters/lido/WstETHAdapter.sol | 86 | ? |

## 🔵 Low / Info Findings (36)

| # | Title | File | Line |
|---|-------|------|------|
| 1 | Local variable shadows state variable | AlchemistV2.sol | 527 |
| 2 | Local variable shadows state variable | AlchemistV2.sol | 703 |
| 3 | Local variable shadows state variable | AlchemistV2.sol | 746 |
| 4 | Local variable shadows state variable | AlchemistV2.sol | 1459 |
| 5 | Local variable shadows state variable | AlchemistV2.sol | 1540 |
| 6 | Possible division by zero in configure() | AlchemistV2.sol | 1929 |
| 7 | Local variable shadows state variable | TransmuterV2.sol | 210 |
| 8 | Local variable shadows state variable | TransmuterV2.sol | 353 |
| 9 | Local variable shadows state variable | TransmuterV2.sol | 373 |
| 10 | Local variable shadows state variable | TransmuterV2.sol | 377 |
| 11 | Local variable shadows state variable | TransmuterV2.sol | 557 |
| 12 | State change without event emission | gALCX.sol | 65 |
| 13 | State change without event emission | AlchemicTokenV2.sol | 127 |
| 14 | State change without event emission | AlchemicTokenV2Base.sol | 148 |
| 15 | Local variable shadows state variable | AutoleverageBase.sol | 75 |
| 16 | Local variable shadows state variable | keepers/AlchemixHarvester.sol | 30 |
| 17 | State change without event emission | keepers/AlchemixHarvester.sol | 30 |
| 18 | State change without event emission | keepers/AlchemixHarvester.sol | 34 |
| 19 | Timestamp dependency in checker() | keepers/AlchemixHarvester.sol | 1616 |
| 20 | Timestamp dependency in checker() | keepers/HarvestResolver.sol | 1572 |
| 21 | State change without event emission | utils/RewardRouter.sol | 38 |
| 22 | State change without event emission | utils/RewardRouter.sol | 71 |
| 23 | State change without event emission | utils/RewardRouter.sol | 81 |
| 24 | State change without event emission | utils/RewardRouter.sol | 86 |
| 25 | State change without event emission | utils/RewardRouter.sol | 91 |
| 26 | State change without event emission | utils/RewardRouter.sol | 96 |
| 27 | State change without event emission | utils/RewardRouter.sol | 101 |
| 28 | Possible division by zero in distributeRewards() | utils/RewardRouter.sol | 1210 |
| 29 | State change without event emission | utils/collectors/OptimismRewardCollector.sol | 53 |
| 30 | State change without event emission | utils/collectors/OptimismRewardCollector.sol | 57 |
| 31 | State change without event emission | utils/collectors/ArbitrumRewardCollector.sol | 60 |
| 32 | State change without event emission | utils/collectors/ArbitrumRewardCollector.sol | 64 |
| 33 | Local variable shadows state variable | libraries/Limiters.sol | 33 |
| 34 | Local variable shadows state variable | libraries/Limiters.sol | 56 |
| 35 | Possible division by zero in configure() | libraries/Limiters.sol | 69 |
| 36 | Local variable shadows state variable | libraries/FixedPointMath.sol | 56 |

---
*Generated by AGL Security Tool v1.1.0 — 2026-02-17 01:25:34*