---
description: "Use when writing Solidity test contracts for detector training, creating vulnerable/safe/edge test cases, or working with training_contracts/ directory."
---
# Solidity Training Contract Guidelines

## Purpose
Training contracts provide ground truth for weight optimization. Each contract is labeled as vulnerable (y=1) or safe (y=0).

## Requirements
- Use Solidity ^0.8.20
- Include `// SPDX-License-Identifier: MIT`
- Mark vulnerability location with `// VULNERABILITY: <description>` or safe pattern with `// SAFE: <description>`
- Include minimal interfaces (IERC20, IRouter, etc.) directly in the file for standalone compilation
- Keep contracts focused — one vulnerability pattern per file

## Categories
- `vulnerable/` — Must trigger the target detector
- `safe/` — Similar code but properly protected, must NOT trigger the detector
- `edge/` — Boundary cases testing detector precision

## Naming Convention
`<protocol_style>_<pattern>.sol` — e.g. `uniswap_swap_no_minout.sol`, `eip712_proper_nonce.sol`
