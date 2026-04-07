# SSV Network — Bug Bounty Security Audit

## Program Details
- **Platform**: Immunefi
- **Program**: SSV Network
- **Bounty**: Up to $1,000,000
- **URL**: https://immunefi.com/bounty/ssvnetwork/
- **Source**: https://github.com/ssvlabs/ssv-network

## Contracts in Scope
| File | Description | Lines |
|------|-------------|-------|
| `SSVNetwork.sol` | Main entry point — UUPS proxy with delegatecall router | ~350 |
| `SSVClusters.sol` | Cluster management — validators, liquidation, deposits, withdrawals | ~350 |
| `SSVOperators.sol` | Operator registration, fee management, earnings withdrawal | ~280 |
| `SSVDAO.sol` | DAO governance — network fee, protocol params | ~130 |

## Protocol Overview
SSV Network is a decentralized staking infrastructure protocol. It splits an Ethereum validator key
among multiple non-trusting operators, enabling distributed validator technology (DVT).

Key security-sensitive areas:
- **Cluster balance accounting** (deposit/withdraw/liquidation)
- **Operator fee management** (declare/execute/cancel)
- **UUPS proxy upgradability** (storage collision, unauthorized upgrades)
- **Delegatecall routing** (fallback-based module dispatch)
- **Diamond storage pattern** (custom storage slots)

## Audit Date
$(date -u +"%Y-%m-%d %H:%M UTC")
