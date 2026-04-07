# 🛡️ AGL Full Pipeline Security Audit Report

**Date:** 2026-04-07T15:47:12.761778+00:00
**Pipeline Version:** 1.2.0
**Duration:** 0.5s
**Engines:** deep_scan, 22_detectors, z3_symbolic, exploit_reasoning, risk_core, meta_classifier

## 📊 Summary

| Metric | Value |
|--------|-------|
| Contracts Scanned | 4 |
| Total Findings | 26 |
| 🔴 Critical | 0 |
| 🟠 High | 7 |
| 🟡 Medium | 19 |
| 🔵 Low | 0 |
| ⚪ Info | 0 |

---

## 📄 bounty_contracts/ssv_network_immunefi/SSVClusters.sol

**Total findings:** 10 | **Duration:** 0.1s

### Layer 1 — Deep Scan
- Findings: 3

### Layer 2 — 22 Semantic Detectors (7 findings)

| Severity | Detector | Title | Line | Function |
|----------|----------|-------|------|----------|
| 🟠 high | UNCHECKED-CALL | Unchecked low-level call return value | 2 | deposit |
| 🟠 high | UNCHECKED-ERC20 | Unchecked ERC20 transfer return value | 2 | deposit |
| 🟡 medium | ENCODE-PACKED-COLLISION | Hash collision risk with abi.encodePacked | 122 | registerPublicKey |
| 🟡 medium | ENCODE-PACKED-COLLISION | Hash collision risk with abi.encodePacked | 164 | validateHashedCluster |
| 🟡 medium | ENCODE-PACKED-COLLISION | Hash collision risk with abi.encodePacked | 183 | hashClusterData |
| 🟡 medium | ENCODE-PACKED-COLLISION | Hash collision risk with abi.encodePacked | 187 | validateClusterOnRegistration |
| 🟡 medium | ENCODE-PACKED-COLLISION | Hash collision risk with abi.encodePacked | 288 | removeValidator |

### Layer 3 — Z3 Symbolic (0 findings)

### Layer 4 — Exploit Reasoning (0 exploitable / 0 total)

---

## 📄 bounty_contracts/ssv_network_immunefi/SSVDAO.sol

**Total findings:** 1 | **Duration:** 0.0s

### Layer 1 — Deep Scan
- Findings: 1

### Layer 2 — 22 Semantic Detectors (0 findings)

### Layer 3 — Z3 Symbolic (0 findings)

### Layer 4 — Exploit Reasoning (0 exploitable / 0 total)

---

## 📄 bounty_contracts/ssv_network_immunefi/SSVNetwork.sol

**Total findings:** 11 | **Duration:** 0.0s

### Layer 1 — Deep Scan
- Findings: 6

### Layer 2 — 22 Semantic Detectors (4 findings)

| Severity | Detector | Title | Line | Function |
|----------|----------|-------|------|----------|
| 🟠 high | UNCHECKED-CALL | Unchecked low-level call return value | 2 | deposit |
| 🟠 high | UNCHECKED-ERC20 | Unchecked ERC20 transfer return value | 2 | deposit |
| 🟡 medium | ENCODE-PACKED-COLLISION | Hash collision risk with abi.encodePacked | 226 | validateHashedCluster |
| 🟡 medium | ENCODE-PACKED-COLLISION | Hash collision risk with abi.encodePacked | 252 | hashClusterData |

### Layer 3 — Z3 Symbolic (1 findings)

| Severity | Category | Title | Line | Proven | Confidence |
|----------|----------|-------|------|--------|------------|
| 🟠 high | storage-collision | Potential storage collision in proxy pattern | 106 | ❌ | 0.75 |

### Layer 4 — Exploit Reasoning (0 exploitable / 0 total)

---

## 📄 bounty_contracts/ssv_network_immunefi/SSVOperators.sol

**Total findings:** 4 | **Duration:** 0.0s

### Layer 1 — Deep Scan
- Findings: 3

### Layer 2 — 22 Semantic Detectors (0 findings)

### Layer 3 — Z3 Symbolic (1 findings)

| Severity | Category | Title | Line | Proven | Confidence |
|----------|----------|-------|------|--------|------------|
| 🔵 low | timestamp-dependency | Timestamp dependency in executeOperatorFee() | 209 | ❌ | 0.4 |

### Layer 4 — Exploit Reasoning (0 exploitable / 0 total)

---
