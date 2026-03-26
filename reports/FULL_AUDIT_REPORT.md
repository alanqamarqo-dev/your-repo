# 🛡️ AGL Full Pipeline Security Audit Report

**Date:** 2026-03-26T16:01:48.569553+00:00
**Pipeline Version:** 1.1.0
**Duration:** 0.5s
**Engines:** deep_scan, 22_detectors, z3_symbolic, exploit_reasoning

## 📊 Summary

| Metric | Value |
|--------|-------|
| Contracts Scanned | 6 |
| Total Findings | 58 |
| 🔴 Critical | 15 |
| 🟠 High | 21 |
| 🟡 Medium | 5 |
| 🔵 Low | 17 |
| ⚪ Info | 0 |

---

## 📄 vulnerable.sol

**Total findings:** 13 | **Duration:** 0.1s

### Layer 1 — Deep Scan
- Findings: 6

### Layer 2 — 22 Semantic Detectors (4 findings)

| Severity | Detector | Title | Line | Function |
|----------|----------|-------|------|----------|
| 🔴 critical | REENTRANCY-ETH | Reentrancy vulnerability (ETH transfer before state update) | 5 | withdraw |
| 🔴 critical | UNPROTECTED-WITHDRAW | Unprotected withdrawal function | 14 | withdraw |
| 🟠 high | TX-ORIGIN-AUTH | Authentication via tx.origin | 2 | transferTo |
| 🟠 high | UNCHECKED-CALL | Unchecked low-level call return value | 2 | ping |

### Layer 3 — Z3 Symbolic (3 findings)

| Severity | Category | Title | Line | Proven | Confidence |
|----------|----------|-------|------|--------|------------|
| 🔴 critical | reentrancy | Reentrancy in withdraw() — state write after external call | 14 | ✅ | 0.95 |
| 🟡 medium | access-control | Missing access control on withdraw() | 14 | ❌ | 0.6 |
| 🟠 high | access-control | tx.origin used for authentication | 26 | ✅ | 0.95 |

### Layer 4 — Exploit Reasoning (0 exploitable / 0 total)

---

## 📄 test_project/src/Vault.sol

**Total findings:** 20 | **Duration:** 0.0s

### Layer 1 — Deep Scan
- Findings: 3

### Layer 2 — 22 Semantic Detectors (12 findings)

| Severity | Detector | Title | Line | Function |
|----------|----------|-------|------|----------|
| 🔴 critical | REENTRANCY-ETH | Reentrancy vulnerability (ETH transfer before state update) | 5 | withdraw |
| 🔴 critical | UNPROTECTED-WITHDRAW | Unprotected withdrawal function | 59 | withdraw |
| 🔴 critical | UNPROTECTED-WITHDRAW | Unprotected withdrawal function | 74 | safeWithdraw |
| 🔴 critical | UNPROTECTED-WITHDRAW | Unprotected withdrawal function | 113 | emergencyWithdraw |
| 🟠 high | TX-ORIGIN-AUTH | Authentication via tx.origin | 2 | emergencyWithdraw |
| 🟠 high | REENTRANCY-NO-ETH | Reentrancy vulnerability (external call before state update) | 3 | deposit |
| 🟠 high | UNCHECKED-CALL | Unchecked low-level call return value | 3 | deposit |
| 🟠 high | UNCHECKED-ERC20 | Unchecked ERC20 transfer return value | 3 | deposit |
| 🟠 high | REENTRANCY-READ-ONLY | Read-only reentrancy (view function reads inconsistent state) | 87 | calculateReward |
| 🟠 high | REENTRANCY-CROSS-FUNCTION | Cross-function reentrancy | 87 | calculateReward |
| 🟠 high | REENTRANCY-CROSS-FUNCTION | Cross-function reentrancy | 95 | claimReward |
| 🔵 low | MISSING-EVENT | State change without event emission | 106 | setRewardRate |

### Layer 3 — Z3 Symbolic (5 findings)

| Severity | Category | Title | Line | Proven | Confidence |
|----------|----------|-------|------|--------|------------|
| 🔴 critical | reentrancy | Reentrancy in withdraw() — state write after external call | 60 | ✅ | 0.95 |
| 🟡 medium | access-control | Missing access control on withdraw() | 60 | ❌ | 0.6 |
| 🟡 medium | access-control | Missing access control on emergencyWithdraw() | 114 | ❌ | 0.6 |
| 🟠 high | access-control | tx.origin used for authentication | 112 | ✅ | 0.95 |
| 🟠 high | access-control | tx.origin used for authentication | 115 | ✅ | 0.95 |

### Layer 4 — Exploit Reasoning (0 exploitable / 0 total)

---

## 📄 test_project/src/VaultToken.sol

**Total findings:** 10 | **Duration:** 0.0s

### Layer 1 — Deep Scan
- Findings: 6

### Layer 2 — 22 Semantic Detectors (3 findings)

| Severity | Detector | Title | Line | Function |
|----------|----------|-------|------|----------|
| 🟠 high | TX-ORIGIN-AUTH | Authentication via tx.origin | 2 | emergencyTransfer |
| 🔵 low | MISSING-EVENT | State change without event emission | 74 | pause |
| 🔵 low | MISSING-EVENT | State change without event emission | 78 | unpause |

### Layer 3 — Z3 Symbolic (1 findings)

| Severity | Category | Title | Line | Proven | Confidence |
|----------|----------|-------|------|--------|------------|
| 🟠 high | access-control | tx.origin used for authentication | 60 | ✅ | 0.95 |

### Layer 4 — Exploit Reasoning (0 exploitable / 0 total)

---

## 📄 test_project/src/RewardDistributor.sol

**Total findings:** 8 | **Duration:** 0.0s

### Layer 1 — Deep Scan
- Findings: 3

### Layer 2 — 22 Semantic Detectors (5 findings)

| Severity | Detector | Title | Line | Function |
|----------|----------|-------|------|----------|
| 🔴 critical | REENTRANCY-ETH | Reentrancy vulnerability (ETH transfer before state update) | 6 | claim |
| 🔴 critical | UNPROTECTED-WITHDRAW | Unprotected withdrawal function | 49 | claim |
| 🟠 high | REENTRANCY-CROSS-FUNCTION | Cross-function reentrancy | 37 | distributeRewards |
| 🟡 medium | UNBOUNDED-LOOP | Unbounded loop over storage array (DoS risk) | 37 | distributeRewards |
| 🟡 medium | ENCODE-PACKED-COLLISION | Hash collision risk with abi.encodePacked | 66 | getRandomBonus |

### Layer 3 — Z3 Symbolic (0 findings)

### Layer 4 — Exploit Reasoning (0 exploitable / 0 total)

---

## 📄 test_project/src/VaultFactory.sol

**Total findings:** 6 | **Duration:** 0.0s

### Layer 1 — Deep Scan
- Findings: 3

### Layer 2 — 22 Semantic Detectors (2 findings)

| Severity | Detector | Title | Line | Function |
|----------|----------|-------|------|----------|
| 🔴 critical | DANGEROUS-DELEGATECALL | Delegatecall to user-controlled address | 3 | execute |
| 🟠 high | UNCHECKED-CALL | Unchecked low-level call return value | 3 | collectFees |

### Layer 3 — Z3 Symbolic (1 findings)

| Severity | Category | Title | Line | Proven | Confidence |
|----------|----------|-------|------|--------|------------|
| 🟠 high | storage-collision | Potential storage collision in proxy pattern | 12 | ❌ | 0.75 |

### Layer 4 — Exploit Reasoning (0 exploitable / 0 total)

---

## 📄 test_project/src/interfaces/IVault.sol

**Total findings:** 1 | **Duration:** 0.0s

### Layer 1 — Deep Scan
- Findings: 1

### Layer 2 — 22 Semantic Detectors (0 findings)

### Layer 3 — Z3 Symbolic (0 findings)

### Layer 4 — Exploit Reasoning (0 exploitable / 0 total)

---
