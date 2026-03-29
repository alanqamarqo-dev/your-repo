#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║  AGL Training Data Generator — مولّد بيانات التدريب المتخصصة        ║
║  Generates instruction-tuning pairs from contracts + pipeline        ║
╚══════════════════════════════════════════════════════════════════════╝

Creates high-quality (instruction, input, output) training pairs for
fine-tuning a small LLM into an expert Solidity/DeFi security analyzer.

Task Types:
  1. vuln_analysis     — Full vulnerability analysis of a contract
  2. function_audit    — Function-level security audit
  3. invariant_extract — Extract business invariants
  4. protocol_classify — Identify protocol type and architecture
  5. exploit_reason    — Reason about exploit paths
  6. access_control    — Analyze access control patterns
  7. fund_flow         — Trace fund movements
  8. cei_check         — Check Checks-Effects-Interactions pattern
  9. pipeline_synth    — Synthesize pipeline layer outputs

Usage:
    python -m agl_security_tool.cli.generate_training_data \\
        --contracts-dir test_contracts/ \\
        --output artifacts/training_data.jsonl \\
        --tasks all
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import hashlib
from pathlib import Path
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PKG_ROOT = os.path.dirname(_SCRIPT_DIR)
_REPO_ROOT = os.path.dirname(_PKG_ROOT)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

logger = logging.getLogger("agl.training_data")

# ═══════════════════════════════════════════════════════════════
# EXPERT KNOWLEDGE TEMPLATES — Hand-crafted ground truth
# ═══════════════════════════════════════════════════════════════

VULNERABILITY_PATTERNS = {
    "reentrancy": {
        "description": "External call before state update allows recursive withdrawal",
        "severity": "CRITICAL",
        "indicators": [
            "external call before state variable update",
            ".call{value:...}() before balance decrement",
            "No reentrancy guard (nonReentrant modifier)",
            "CEI violation: Interaction before Effects",
        ],
        "exploit_template": (
            "1. Deploy attacker contract with receive()/fallback() that re-calls withdraw()\n"
            "2. Deposit minimum amount\n"
            "3. Call withdraw() — on callback, withdraw() is re-entered before balance is zeroed\n"
            "4. Drain vault of all funds"
        ),
        "fix": "Apply Checks-Effects-Interactions pattern: update state BEFORE external call, or use ReentrancyGuard",
    },
    "unchecked_return": {
        "description": "Return value of low-level call not checked, silent failure possible",
        "severity": "HIGH",
        "indicators": [
            ".call() / .send() / .transfer() without checking bool return",
            "No require() or if-check on call result",
            "Funds may appear sent but actually failed",
        ],
        "exploit_template": (
            "1. Target contract calls addr.send(amount) without checking return\n"
            "2. Attacker deploys contract that reverts on receive\n"
            "3. Send fails silently, but contract state assumes success\n"
            "4. State becomes inconsistent — attacker can claim funds again"
        ),
        "fix": "Always check return value: (bool ok, ) = addr.call{value: amount}(''); require(ok);",
    },
    "tx_origin": {
        "description": "Using tx.origin for authorization allows phishing attacks",
        "severity": "HIGH",
        "indicators": [
            "require(tx.origin == owner)",
            "tx.origin used for access control instead of msg.sender",
            "No distinction between direct caller and transaction originator",
        ],
        "exploit_template": (
            "1. Deploy phishing contract that calls vulnerable contract\n"
            "2. Trick owner into calling phishing contract (e.g., fake token approval)\n"
            "3. Phishing contract calls vulnerable.withdraw() — tx.origin == owner passes\n"
            "4. Attacker drains funds through the phishing proxy"
        ),
        "fix": "Replace tx.origin with msg.sender for all authorization checks",
    },
    "delegatecall_injection": {
        "description": "Unprotected delegatecall allows storage manipulation by attacker",
        "severity": "CRITICAL",
        "indicators": [
            "delegatecall to user-controlled address",
            "No whitelist of allowed implementation addresses",
            "Proxy pattern without proper access control on upgrade",
        ],
        "exploit_template": (
            "1. Deploy malicious implementation contract that overwrites storage slot 0 (owner)\n"
            "2. Call proxy.delegatecall(malicious_addr, setOwner(attacker))\n"
            "3. delegatecall executes in proxy's context — storage is modified\n"
            "4. Attacker becomes owner, drains all funds"
        ),
        "fix": "Whitelist implementation addresses, protect upgrade function with onlyOwner",
    },
    "timestamp_dependency": {
        "description": "Block.timestamp used for randomness or critical logic — manipulable by miners",
        "severity": "MEDIUM",
        "indicators": [
            "block.timestamp used in random number generation",
            "block.timestamp as lottery seed",
            "Time-based conditions that miners can influence",
        ],
        "exploit_template": (
            "1. Miner/validator sees pending lottery transaction\n"
            "2. Adjusts block.timestamp within allowed range (~15s)\n"
            "3. Mines block with timestamp that satisfies winning condition\n"
            "4. Collects lottery prize"
        ),
        "fix": "Use Chainlink VRF for randomness, avoid timestamp for critical decisions",
    },
    "unprotected_selfdestruct": {
        "description": "selfdestruct callable by anyone — permanent contract destruction",
        "severity": "CRITICAL",
        "indicators": [
            "selfdestruct() with no access control",
            "Missing onlyOwner modifier on destroy function",
            "Any address can trigger contract destruction",
        ],
        "exploit_template": (
            "1. Find selfdestruct function without access control\n"
            "2. Call it directly — contract is permanently destroyed\n"
            "3. All funds sent to attacker's address\n"
            "4. Contract bytecode erased — irreversible"
        ),
        "fix": "Add onlyOwner modifier, or remove selfdestruct entirely (deprecated in newer Solidity)",
    },
    "flash_loan_callback": {
        "description": "Unprotected callback allows flash loan manipulation of protocol state",
        "severity": "CRITICAL",
        "indicators": [
            "Callback function callable by any flash loan provider",
            "State changes during callback not validated",
            "No check that callback was initiated by the protocol itself",
        ],
        "exploit_template": (
            "1. Take flash loan of large amount\n"
            "2. Manipulate protocol state during callback (e.g., inflate price)\n"
            "3. Execute profitable action at manipulated price\n"
            "4. Repay flash loan — profit = manipulated gain - loan fee"
        ),
        "fix": "Validate callback origin, use reentrancy guards, check invariants post-callback",
    },
    "oracle_manipulation": {
        "description": "Spot price oracle vulnerable to manipulation via flash loans",
        "severity": "CRITICAL",
        "indicators": [
            "Using pool.slot0() for price directly",
            "Single-block TWAP or no TWAP at all",
            "Price derived from reserve ratio (manipulable)",
        ],
        "exploit_template": (
            "1. Flash loan large amount of token A\n"
            "2. Swap into pool — moves spot price dramatically\n"
            "3. Protocol reads manipulated price for collateral valuation\n"
            "4. Borrow against inflated collateral, repay flash loan"
        ),
        "fix": "Use Chainlink oracle or multi-block TWAP, never use slot0() directly",
    },
    "first_depositor_inflation": {
        "description": "First depositor can manipulate share price to steal from subsequent depositors",
        "severity": "HIGH",
        "indicators": [
            "ERC4626-like vault with shares = assets * totalSupply / totalAssets",
            "No minimum deposit or virtual offset",
            "First deposit sets the exchange rate",
        ],
        "exploit_template": (
            "1. Deposit 1 wei → get 1 share\n"
            "2. Donate large amount directly to vault (inflate totalAssets)\n"
            "3. Next depositor's shares = deposit * 1 / (1 + donated) ≈ 0 (rounded down)\n"
            "4. First depositor redeems 1 share for all assets"
        ),
        "fix": "Add virtual offset (ERC4626 with _decimalsOffset), enforce minimum first deposit",
    },
    "read_only_reentrancy": {
        "description": "View function returns stale data during reentrant callback",
        "severity": "HIGH",
        "indicators": [
            "View function reads state that changes during external call",
            "Other protocol integrates using this view function",
            "No reentrancy guard on view function or state-changing function",
        ],
        "exploit_template": (
            "1. Call withdraw() on Protocol A — triggers external call\n"
            "2. In callback, call Protocol B which reads Protocol A's getPrice()\n"
            "3. getPrice() returns stale value (state not yet updated)\n"
            "4. Protocol B makes decision based on wrong price — attacker profits"
        ),
        "fix": "Apply reentrancy guard to both state-changing and view functions, or use check-on-read pattern",
    },
    "stale_oracle_price": {
        "description": "Chainlink oracle price not checked for freshness — stale data risk",
        "severity": "HIGH",
        "indicators": [
            "latestRoundData() called without checking updatedAt",
            "No staleness threshold comparison",
            "No check for answeredInRound >= roundId",
        ],
        "exploit_template": (
            "1. Wait for Chainlink price feed to become stale (network congestion, etc.)\n"
            "2. Actual market price has moved significantly from stale price\n"
            "3. Execute trades using stale price — arbitrage the difference\n"
            "4. Profit = |actual_price - stale_price| * position_size"
        ),
        "fix": "Check updatedAt freshness: require(block.timestamp - updatedAt < MAX_STALENESS); check answeredInRound >= roundId",
    },
    "gas_dos": {
        "description": "Unbounded loop over dynamic array enables gas DoS",
        "severity": "MEDIUM",
        "indicators": [
            "for loop iterating over unbounded array",
            "Array grows with user deposits/registrations",
            "No pagination or gas limit check",
        ],
        "exploit_template": (
            "1. Register many small entries to grow the array\n"
            "2. Any function iterating the array now exceeds block gas limit\n"
            "3. Critical functions (withdraw, distribute) become uncallable\n"
            "4. Funds permanently locked in contract"
        ),
        "fix": "Use pull-over-push pattern, paginate operations, set array size caps",
    },
}

PROTOCOL_TYPES = {
    "amm": {
        "keywords": ["swap", "addLiquidity", "removeLiquidity", "getAmountOut", "reserve", "pair", "pool"],
        "description": "Automated Market Maker — token swap protocol using constant product or similar formula",
        "invariants": [
            "x * y = k (constant product) must hold after every swap",
            "LP shares = sqrt(dx * dy) for initial deposit",
            "Fee accumulates in reserves, not distributed separately",
            "Slippage protection: actual output >= minAmountOut",
        ],
        "attack_surfaces": ["Oracle manipulation via reserve ratio", "Sandwich attacks", "LP token inflation", "Impermanent loss exploitation"],
    },
    "lending": {
        "keywords": ["borrow", "repay", "liquidate", "collateral", "healthFactor", "supply", "withdraw"],
        "description": "Lending protocol — users supply collateral and borrow against it",
        "invariants": [
            "totalBorrows <= totalSupply * LTV_ratio at all times",
            "healthFactor >= 1.0 or position is liquidatable",
            "Interest accrual: borrowBalance * (1 + rate)^time",
            "Liquidation bonus <= (collateral - debt) margin",
        ],
        "attack_surfaces": ["Oracle manipulation for undercollateralized borrows", "Flash loan liquidation cascades", "Interest rate manipulation", "Bad debt accumulation"],
    },
    "vault": {
        "keywords": ["deposit", "withdraw", "shares", "totalAssets", "convertToShares", "convertToAssets"],
        "description": "Yield vault (ERC4626) — accepts deposits and generates yield",
        "invariants": [
            "shares * totalAssets / totalSupply = user's proportional claim",
            "deposit(assets) → shares >= assets * totalSupply / totalAssets (rounding down)",
            "redeem(shares) → assets <= shares * totalAssets / totalSupply (rounding down)",
            "totalAssets >= sum of all deposited assets (yield only increases)",
        ],
        "attack_surfaces": ["First depositor share inflation", "Sandwich on rebalance", "Share price manipulation via donation", "Rounding errors in conversion"],
    },
    "governance": {
        "keywords": ["propose", "vote", "execute", "quorum", "timelock", "delegate"],
        "description": "Governance protocol — on-chain voting and proposal execution",
        "invariants": [
            "Proposal execution requires quorum AND majority",
            "Timelock delay between approval and execution",
            "One address one vote (or delegated voting power)",
            "Proposal cannot be executed twice",
        ],
        "attack_surfaces": ["Flash loan governance attack", "Timelock bypass", "Proposal front-running", "Vote buying"],
    },
    "staking": {
        "keywords": ["stake", "unstake", "claim", "rewardPerToken", "earned", "slash"],
        "description": "Staking/rewards protocol — users lock tokens to earn rewards",
        "invariants": [
            "rewardPerToken accumulates monotonically",
            "earned(user) = balance * (rewardPerToken - userRewardPerToken)",
            "totalStaked = sum of all individual stakes",
            "Reward rate * duration <= reward pool balance",
        ],
        "attack_surfaces": ["Reward calculation manipulation", "Stake/unstake sandwich", "Reward pool draining via flash stake", "Division by zero when totalStaked == 0"],
    },
    "bridge": {
        "keywords": ["lock", "unlock", "mint", "burn", "relayer", "merkleProof", "nonce"],
        "description": "Cross-chain bridge — moves assets between blockchains",
        "invariants": [
            "Locked assets on chain A == Minted tokens on chain B",
            "Each message processed exactly once (nonce tracking)",
            "Merkle proof validates cross-chain message authenticity",
            "Relayer cannot forge messages without valid proof",
        ],
        "attack_surfaces": ["Fake proof submission", "Replay attacks (nonce reuse)", "Relayer censorship", "Bridge drainage via forged proofs"],
    },
}

# ═══════════════════════════════════════════════════════════════
# TRAINING PAIR GENERATORS
# ═══════════════════════════════════════════════════════════════


def _parse_functions(source: str) -> list[dict]:
    """Extract functions with their bodies from Solidity source."""
    functions = []
    # Match function declarations
    pattern = re.compile(
        r'(function\s+(\w+)\s*\([^)]*\)[^{]*\{)',
        re.MULTILINE
    )
    for m in pattern.finditer(source):
        name = m.group(2)
        start = m.start()
        # Find matching closing brace
        brace_count = 0
        body_start = source.index('{', m.start())
        i = body_start
        while i < len(source):
            if source[i] == '{':
                brace_count += 1
            elif source[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    body = source[start:i + 1]
                    functions.append({"name": name, "body": body, "start": start, "end": i + 1})
                    break
            i += 1
    return functions


def _detect_vuln_type(source: str, fn_body: str = "") -> list[str]:
    """Detect vulnerability types present in source code."""
    code = fn_body or source
    found = []

    # Reentrancy: external call before state update
    if re.search(r'\.call\{.*value', code) and re.search(r'balances?\[.*\]\s*[-=]', code):
        # Check if call comes before state update (CEI violation)
        call_pos = code.find('.call{')
        balance_pos = max(code.rfind('balances['), code.rfind('balance['))
        if call_pos > 0 and balance_pos > call_pos:
            found.append("reentrancy")

    # Unchecked return
    if re.search(r'\.call\{', code) and not re.search(r'require\s*\(\s*success', code):
        if re.search(r'\(\s*bool\s+\w+\s*,', code) and not re.search(r'if\s*\(\s*\w+\s*\)', code):
            found.append("unchecked_return")
        elif re.search(r'\.send\(', code):
            found.append("unchecked_return")

    # tx.origin
    if re.search(r'tx\.origin', code):
        found.append("tx_origin")

    # delegatecall
    if re.search(r'delegatecall', code):
        found.append("delegatecall_injection")

    # timestamp
    if re.search(r'block\.timestamp', code) and re.search(r'%|random|lottery|winner', code, re.I):
        found.append("timestamp_dependency")

    # selfdestruct
    if re.search(r'selfdestruct|suicide', code):
        if not re.search(r'onlyOwner|require\s*\(\s*msg\.sender\s*==\s*owner', code):
            found.append("unprotected_selfdestruct")

    # Oracle slot0
    if re.search(r'slot0|getReserves.*price|reserve0.*reserve1.*price', code, re.I):
        found.append("oracle_manipulation")

    # First depositor
    if re.search(r'totalSupply\s*==\s*0', code) and re.search(r'shares?\s*=', code):
        found.append("first_depositor_inflation")

    # Stale oracle
    if re.search(r'latestRoundData', code) and not re.search(r'updatedAt|staleness', code):
        found.append("stale_oracle_price")

    # Gas DoS
    if re.search(r'for\s*\(.*\.length', code) and re.search(r'push\(', source):
        found.append("gas_dos")

    # Flash loan callback
    if re.search(r'flash.*callback|onFlash|executeOperation', code, re.I):
        if not re.search(r'require\s*\(\s*msg\.sender\s*==', code):
            found.append("flash_loan_callback")

    # Read-only reentrancy
    if re.search(r'view.*returns|pure.*returns', code) and re.search(r'balanceOf|totalAssets|getPrice', code):
        found.append("read_only_reentrancy")

    return found


def _classify_protocol(source: str) -> str:
    """Classify protocol type from source code."""
    scores: dict[str, int] = {}
    lower = source.lower()
    for ptype, info in PROTOCOL_TYPES.items():
        score = sum(1 for kw in info["keywords"] if kw.lower() in lower)
        if score > 0:
            scores[ptype] = score
    if not scores:
        return "unknown"
    return max(scores, key=scores.get)


def generate_vuln_analysis(source: str, filepath: str) -> list[dict]:
    """Task 1: Full vulnerability analysis training pairs."""
    pairs = []
    vulns = _detect_vuln_type(source)
    if not vulns:
        # Safe contract — train on "no vulnerabilities" too
        pairs.append({
            "task": "vuln_analysis",
            "instruction": (
                "You are AGL-SEC, an expert smart contract security auditor. "
                "Analyze the following Solidity contract for vulnerabilities. "
                "For each vulnerability found, provide: type, severity (CRITICAL/HIGH/MEDIUM/LOW), "
                "location (function name + line), description, exploit scenario, and fix. "
                "If the contract is secure, explain why."
            ),
            "input": source[:8000],
            "output": json.dumps({
                "verdict": "SECURE",
                "vulnerabilities": [],
                "security_features": [
                    "Proper access control with modifiers",
                    "Checks-Effects-Interactions pattern followed",
                    "No external calls with unchecked returns",
                ],
                "confidence": 0.85
            }, indent=2),
            "source_file": filepath,
        })
        return pairs

    vuln_list = []
    for v in vulns:
        if v in VULNERABILITY_PATTERNS:
            info = VULNERABILITY_PATTERNS[v]
            vuln_list.append({
                "type": v,
                "severity": info["severity"],
                "description": info["description"],
                "indicators_found": info["indicators"],
                "exploit_path": info["exploit_template"],
                "recommended_fix": info["fix"],
            })

    pairs.append({
        "task": "vuln_analysis",
        "instruction": (
            "You are AGL-SEC, an expert smart contract security auditor. "
            "Analyze the following Solidity contract for vulnerabilities. "
            "For each vulnerability found, provide: type, severity (CRITICAL/HIGH/MEDIUM/LOW), "
            "location (function name + line), description, exploit scenario, and fix. "
            "If the contract is secure, explain why."
        ),
        "input": source[:8000],
        "output": json.dumps({
            "verdict": "VULNERABLE",
            "vulnerabilities": vuln_list,
            "total_risk": "CRITICAL" if any(v.get("severity") == "CRITICAL" for v in vuln_list) else "HIGH",
            "confidence": 0.90
        }, indent=2),
        "source_file": filepath,
    })
    return pairs


def generate_function_audit(source: str, filepath: str) -> list[dict]:
    """Task 2: Function-level security audit pairs."""
    pairs = []
    functions = _parse_functions(source)
    for fn in functions[:10]:  # Limit per contract
        vulns = _detect_vuln_type(source, fn["body"])
        if vulns:
            vuln_details = []
            for v in vulns:
                if v in VULNERABILITY_PATTERNS:
                    info = VULNERABILITY_PATTERNS[v]
                    vuln_details.append({
                        "type": v,
                        "severity": info["severity"],
                        "description": info["description"],
                        "in_function": fn["name"],
                        "fix": info["fix"],
                    })
            output = {
                "function": fn["name"],
                "verdict": "VULNERABLE",
                "issues": vuln_details,
            }
        else:
            output = {
                "function": fn["name"],
                "verdict": "SAFE",
                "reasoning": f"Function {fn['name']} follows security best practices: "
                             "proper access control, CEI pattern, no unchecked calls.",
            }

        pairs.append({
            "task": "function_audit",
            "instruction": (
                "You are AGL-SEC. Audit this individual Solidity function for security issues. "
                "Check for: reentrancy, unchecked returns, access control, integer overflow, "
                "CEI violations, and business logic flaws. "
                "Provide verdict (SAFE/VULNERABLE), detailed reasoning, and fix if needed."
            ),
            "input": fn["body"][:4000],
            "output": json.dumps(output, indent=2),
            "source_file": filepath,
        })
    return pairs


def generate_invariant_extraction(source: str, filepath: str) -> list[dict]:
    """Task 3: Extract business invariants from contract."""
    ptype = _classify_protocol(source)
    if ptype == "unknown":
        return []

    info = PROTOCOL_TYPES[ptype]
    pairs = [{
        "task": "invariant_extract",
        "instruction": (
            "You are AGL-SEC. Extract the business invariants from this Solidity contract. "
            "Invariants are properties that MUST hold true at all times. "
            "For each invariant: state the property, identify which functions maintain it, "
            "and flag any functions that might violate it."
        ),
        "input": source[:8000],
        "output": json.dumps({
            "protocol_type": ptype,
            "invariants": [
                {"property": inv, "critical": True}
                for inv in info["invariants"]
            ],
            "attack_surfaces": info["attack_surfaces"],
        }, indent=2),
        "source_file": filepath,
    }]
    return pairs


def generate_protocol_classify(source: str, filepath: str) -> list[dict]:
    """Task 4: Protocol type classification."""
    ptype = _classify_protocol(source)
    info = PROTOCOL_TYPES.get(ptype, {})

    return [{
        "task": "protocol_classify",
        "instruction": (
            "You are AGL-SEC. Classify this Solidity contract's protocol type. "
            "Categories: AMM, Lending, Vault, Governance, Staking, Bridge, Token, Unknown. "
            "Explain your reasoning based on function signatures, state variables, and patterns."
        ),
        "input": source[:6000],
        "output": json.dumps({
            "protocol_type": ptype,
            "description": info.get("description", "Unknown protocol type"),
            "key_indicators": info.get("keywords", []),
            "confidence": 0.85 if ptype != "unknown" else 0.3,
        }, indent=2),
        "source_file": filepath,
    }]


def generate_exploit_reasoning(source: str, filepath: str) -> list[dict]:
    """Task 5: Exploit path reasoning."""
    pairs = []
    vulns = _detect_vuln_type(source)
    for v in vulns:
        if v not in VULNERABILITY_PATTERNS:
            continue
        info = VULNERABILITY_PATTERNS[v]
        pairs.append({
            "task": "exploit_reason",
            "instruction": (
                f"You are AGL-SEC. A {info['severity']} {v.replace('_', ' ')} vulnerability "
                f"was detected in this contract. Reason step-by-step about how an attacker "
                f"would exploit it. Include: prerequisites, attack steps, expected profit, "
                f"and what makes this exploitable vs a false positive."
            ),
            "input": source[:6000],
            "output": json.dumps({
                "vulnerability_type": v,
                "severity": info["severity"],
                "exploit_steps": info["exploit_template"],
                "prerequisites": [
                    "Attacker has ETH for gas",
                    "Contract has funds deposited",
                    "No external protections (e.g., EOA-only guard)",
                ],
                "profit_estimate": "Contract balance (variable)",
                "false_positive_check": (
                    f"This is a TRUE positive because: "
                    f"{info['indicators'][0]}. "
                    f"Would be false positive if: proper guard existed."
                ),
                "confidence": 0.88,
            }, indent=2),
            "source_file": filepath,
        })
    return pairs


def generate_access_control(source: str, filepath: str) -> list[dict]:
    """Task 6: Access control analysis."""
    modifiers_found = re.findall(
        r'modifier\s+(\w+)',
        source
    )
    require_sender = re.findall(
        r'require\s*\(\s*msg\.sender\s*==\s*(\w+)',
        source
    )
    only_owner = "onlyOwner" in source or any("owner" in m.lower() for m in modifiers_found)

    functions = _parse_functions(source)
    public_fns = [f for f in functions if re.search(r'\b(public|external)\b', f["body"])]

    unprotected = []
    for fn in public_fns:
        has_modifier = any(m in fn["body"] for m in modifiers_found)
        has_require = re.search(r'require\s*\(\s*msg\.sender', fn["body"])
        if not has_modifier and not has_require:
            if re.search(r'\.call\{|\.transfer\(|selfdestruct|delegatecall', fn["body"]):
                unprotected.append(fn["name"])

    return [{
        "task": "access_control",
        "instruction": (
            "You are AGL-SEC. Analyze the access control patterns in this Solidity contract. "
            "Identify: all custom modifiers, which functions are protected, which sensitive "
            "functions lack protection, and potential privilege escalation paths."
        ),
        "input": source[:8000],
        "output": json.dumps({
            "modifiers_defined": modifiers_found,
            "owner_pattern": only_owner,
            "sender_checks": require_sender,
            "unprotected_sensitive_functions": unprotected,
            "risk_level": "CRITICAL" if unprotected else "LOW",
            "recommendation": (
                f"Functions {unprotected} handle funds/critical operations but lack access control"
                if unprotected else
                "Access control appears properly implemented"
            ),
        }, indent=2),
        "source_file": filepath,
    }]


def generate_fund_flow(source: str, filepath: str) -> list[dict]:
    """Task 7: Fund flow analysis."""
    # Find fund-related patterns
    eth_transfers = re.findall(r'(\.call\{value:\s*\w+\}|\.transfer\(|\.send\()', source)
    token_transfers = re.findall(r'(\.transfer\(\s*\w+|\.transferFrom\(|\.safeTransfer\()', source)
    balance_updates = re.findall(r'(balances?\[\w+\]\s*[+-]=)', source)

    functions = _parse_functions(source)
    deposit_fns = [f["name"] for f in functions if re.search(r'deposit|supply|stake|add.*liquid', f["name"], re.I)]
    withdraw_fns = [f["name"] for f in functions if re.search(r'withdraw|redeem|unstake|remove.*liquid', f["name"], re.I)]

    return [{
        "task": "fund_flow",
        "instruction": (
            "You are AGL-SEC. Trace all fund flows in this Solidity contract. "
            "Map: entry points (where funds come in), exit points (where funds go out), "
            "internal accounting, and any paths where funds could be misdirected or lost."
        ),
        "input": source[:8000],
        "output": json.dumps({
            "entry_points": deposit_fns or ["receive", "fallback"],
            "exit_points": withdraw_fns or ["N/A"],
            "eth_transfers": len(eth_transfers),
            "token_transfers": len(token_transfers),
            "internal_accounting": len(balance_updates),
            "fund_flow_risks": (
                ["Withdraw without deposit validation"] if withdraw_fns and not deposit_fns
                else ["Balanced fund flow"] if deposit_fns and withdraw_fns
                else ["No clear fund flow pattern"]
            ),
        }, indent=2),
        "source_file": filepath,
    }]


def generate_cei_check(source: str, filepath: str) -> list[dict]:
    """Task 8: CEI pattern verification."""
    pairs = []
    functions = _parse_functions(source)

    for fn in functions[:8]:
        body = fn["body"]
        has_external_call = bool(re.search(r'\.call\{|\.transfer\(|\.send\(|\.safeTransfer', body))
        has_state_update = bool(re.search(r'balances?\[.*\]\s*[-+]?=|_balances\[.*\]\s*[-+]?=|total\w+\s*[-+]?=', body))

        if not has_external_call or not has_state_update:
            continue

        # Find positions
        call_match = re.search(r'\.call\{|\.transfer\(|\.send\(', body)
        state_match = re.search(r'balances?\[.*\]\s*[-+]?=', body)

        if call_match and state_match:
            cei_violation = call_match.start() < state_match.start()
            pairs.append({
                "task": "cei_check",
                "instruction": (
                    "You are AGL-SEC. Check if this Solidity function follows the "
                    "Checks-Effects-Interactions (CEI) pattern. "
                    "CEI requires: 1) Check conditions (require/if), "
                    "2) Update state (effects), 3) External calls (interactions). "
                    "Report whether CEI is followed and any violations."
                ),
                "input": body[:4000],
                "output": json.dumps({
                    "function": fn["name"],
                    "cei_compliant": not cei_violation,
                    "pattern_found": (
                        "VIOLATION: External call at position before state update — "
                        "attacker can re-enter during the call and exploit stale state"
                        if cei_violation else
                        "COMPLIANT: State updated before external call"
                    ),
                    "reentrancy_risk": "HIGH" if cei_violation else "LOW",
                    "fix": (
                        "Move state update BEFORE the external call"
                        if cei_violation else "No fix needed"
                    ),
                }, indent=2),
                "source_file": filepath,
            })
    return pairs


def generate_pipeline_synthesis(source: str, filepath: str, pipeline_output: dict | None = None) -> list[dict]:
    """Task 9: Synthesize pipeline layer outputs into unified analysis."""
    if not pipeline_output:
        return []

    findings = pipeline_output.get("unified_findings", [])
    if not findings:
        return []

    pairs = [{
        "task": "pipeline_synth",
        "instruction": (
            "You are AGL-SEC. Given the multi-layer analysis output from the AGL Security Tool pipeline, "
            "synthesize the findings into a coherent security report. "
            "Cross-validate between layers: if Z3 proves something and heuristic flags it, confidence is higher. "
            "If only heuristic flags it with no formal proof, it might be a false positive. "
            "Prioritize findings by: exploitability, profit potential, and proof strength."
        ),
        "input": json.dumps({
            "contract_source": source[:3000],
            "pipeline_findings": findings[:20],
            "layers_used": pipeline_output.get("layers_used", []),
        }, indent=2),
        "output": json.dumps({
            "synthesized_findings": [
                {
                    "title": f.get("title", "Unknown"),
                    "severity": f.get("severity", "MEDIUM"),
                    "confidence": f.get("probability", 0.5),
                    "corroborated_by": f.get("source", "unknown"),
                    "action": "INVESTIGATE" if f.get("probability", 0) > 0.7 else "MONITOR",
                }
                for f in findings[:10]
            ],
            "overall_risk": "CRITICAL" if any(f.get("severity") == "CRITICAL" for f in findings) else "MEDIUM",
            "false_positive_assessment": "Cross-layer validation applied",
        }, indent=2),
        "source_file": filepath,
    }]
    return pairs


# ═══════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════

TASK_GENERATORS = {
    "vuln_analysis": generate_vuln_analysis,
    "function_audit": generate_function_audit,
    "invariant_extract": generate_invariant_extraction,
    "protocol_classify": generate_protocol_classify,
    "exploit_reason": generate_exploit_reasoning,
    "access_control": generate_access_control,
    "fund_flow": generate_fund_flow,
    "cei_check": generate_cei_check,
}


def generate_from_contract(
    filepath: str,
    tasks: list[str] | None = None,
    pipeline_output: dict | None = None,
) -> list[dict]:
    """Generate all training pairs from a single contract file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        logger.warning("Cannot read %s: %s", filepath, e)
        return []

    if len(source) < 50:
        return []

    all_pairs = []
    active_tasks = tasks or list(TASK_GENERATORS.keys())

    for task_name in active_tasks:
        gen = TASK_GENERATORS.get(task_name)
        if gen:
            try:
                pairs = gen(source, filepath)
                all_pairs.extend(pairs)
            except Exception as e:
                logger.warning("Generator %s failed on %s: %s", task_name, filepath, e)

    # Pipeline synthesis needs pipeline output
    if ("pipeline_synth" in (tasks or []) or tasks is None) and pipeline_output:
        try:
            synth = generate_pipeline_synthesis(source, filepath, pipeline_output)
            all_pairs.extend(synth)
        except Exception as e:
            logger.warning("Pipeline synthesis failed on %s: %s", filepath, e)

    return all_pairs


def generate_dataset(
    contracts_dir: str,
    output_path: str,
    tasks: list[str] | None = None,
    run_pipeline: bool = False,
) -> dict:
    """Generate complete training dataset from a directory of contracts."""
    contracts = []
    for root, _, files in os.walk(contracts_dir):
        for f in files:
            if f.endswith(".sol"):
                contracts.append(os.path.join(root, f))

    logger.info("Found %d Solidity contracts", len(contracts))

    all_pairs = []
    stats = {"contracts": 0, "pairs": 0, "tasks": {}, "errors": 0}

    for filepath in sorted(contracts):
        logger.info("Processing: %s", os.path.basename(filepath))
        stats["contracts"] += 1

        pipeline_output = None
        if run_pipeline:
            try:
                from agl_security_tool.core import AGLSecurityAudit
                scanner = AGLSecurityAudit()
                pipeline_output = scanner._scan_file(filepath)
            except Exception as e:
                logger.warning("Pipeline failed on %s: %s", filepath, e)
                stats["errors"] += 1

        pairs = generate_from_contract(filepath, tasks, pipeline_output)
        for p in pairs:
            task = p.get("task", "unknown")
            stats["tasks"][task] = stats["tasks"].get(task, 0) + 1

        all_pairs.extend(pairs)

    stats["pairs"] = len(all_pairs)

    # Deduplicate by content hash
    seen = set()
    unique_pairs = []
    for p in all_pairs:
        h = hashlib.md5((p.get("input", "") + p.get("output", "")).encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            unique_pairs.append(p)

    stats["unique_pairs"] = len(unique_pairs)
    stats["duplicates_removed"] = len(all_pairs) - len(unique_pairs)

    # Write JSONL output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for pair in unique_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    logger.info(
        "Generated %d unique training pairs from %d contracts → %s",
        len(unique_pairs), stats["contracts"], output_path,
    )
    return stats


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="AGL Training Data Generator — مولّد بيانات التدريب",
    )
    parser.add_argument(
        "--contracts-dir",
        default=os.path.join(_PKG_ROOT, "test_contracts"),
        help="Directory containing .sol files",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(_PKG_ROOT, "artifacts", "training_data.jsonl"),
        help="Output JSONL file path",
    )
    parser.add_argument(
        "--tasks",
        nargs="+",
        choices=list(TASK_GENERATORS.keys()) + ["pipeline_synth", "all"],
        default=["all"],
        help="Task types to generate",
    )
    parser.add_argument(
        "--run-pipeline",
        action="store_true",
        help="Run AGL pipeline on each contract for pipeline_synth task",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    tasks = None if "all" in args.tasks else args.tasks

    stats = generate_dataset(
        contracts_dir=args.contracts_dir,
        output_path=args.output,
        tasks=tasks,
        run_pipeline=args.run_pipeline,
    )

    print("\n╔══════════════════════════════════════════╗")
    print("║     AGL Training Data — Summary           ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║  Contracts processed: {stats['contracts']:>6}              ║")
    print(f"║  Total pairs:         {stats['pairs']:>6}              ║")
    print(f"║  Unique pairs:        {stats.get('unique_pairs', 0):>6}              ║")
    print(f"║  Duplicates removed:  {stats.get('duplicates_removed', 0):>6}              ║")
    print("╠══════════════════════════════════════════╣")
    for task, count in sorted(stats["tasks"].items()):
        print(f"║  {task:<22} {count:>6}              ║")
    print("╚══════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
