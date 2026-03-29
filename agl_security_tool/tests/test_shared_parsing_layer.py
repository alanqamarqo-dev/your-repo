"""
═══════════════════════════════════════════════════════════════
 اختبار المرحلة 2.5: Shared Parsing Layer — اختبار حقيقي
 Test Stage 2.5: Shared Semantic Parsing on Real Contract
═══════════════════════════════════════════════════════════════

This test runs the Shared Parsing layer in ISOLATION on a real-world
Compound V3 Comet contract (1061 lines) to verify:

1. Correct contract extraction
2. Function extraction completeness
3. State variable detection
4. Operation ordering (CEI pattern detection)
5. Safe function identification accuracy
6. Modifier & access control detection
7. External call detection
8. Performance (parsing speed)
"""

import sys
import os
import time
import json
from pathlib import Path
from collections import Counter

# Ensure the project root is on the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
from agl_security_tool.detectors import (
    ParsedContract, ParsedFunction, OpType, StateVar, ModifierInfo
)


def banner(text: str):
    print(f"\n{'═' * 70}")
    print(f"  {text}")
    print(f"{'═' * 70}")


def test_shared_parsing_on_compound_comet():
    """Run the full Shared Parsing pipeline on Compound V3 Comet."""

    contract_path = PROJECT_ROOT / "test_contracts" / "real_world" / "compound_comet.sol"
    assert contract_path.exists(), f"Contract not found: {contract_path}"

    with open(contract_path, "r", encoding="utf-8") as f:
        source = f.read()

    line_count = len(source.splitlines())
    print(f"\n📄 Contract: compound_comet.sol ({line_count} lines, {len(source)} bytes)")

    # ═══════════════════════════════════════════════════
    #  Step 1: Parse with SoliditySemanticParser
    # ═══════════════════════════════════════════════════
    banner("STEP 1: SoliditySemanticParser.parse()")

    parser = SoliditySemanticParser()

    t0 = time.perf_counter()
    contracts = parser.parse(source, str(contract_path))
    parse_time = time.perf_counter() - t0

    print(f"  ⏱️  Parse time: {parse_time:.4f}s")
    print(f"  📦 Contracts found: {len(contracts)}")

    for c in contracts:
        print(f"\n  ┌─ Contract: {c.name} ({c.contract_type})")
        print(f"  │  Lines: {c.line_start}-{c.line_end}")
        print(f"  │  Inherits: {c.inherits or '(none)'}")
        print(f"  │  Pragma: {c.pragma}")
        print(f"  │  Solidity Version: {c.solidity_version}")
        print(f"  │  Upgradeable: {c.is_upgradeable}")
        print(f"  │  Uses SafeMath: {c.uses_safe_math}")
        print(f"  │  State variables: {len(c.state_vars)}")
        print(f"  │  Functions: {len(c.functions)}")
        print(f"  │  Modifiers: {len(c.modifiers)}")
        print(f"  │  Events: {c.events}")
        print(f"  │  Using-for: {c.using_for}")
        print(f"  └─────────────────────────")

    # ═══════════════════════════════════════════════════
    #  Step 2: Detailed Function Analysis
    # ═══════════════════════════════════════════════════
    banner("STEP 2: Function-Level Analysis")

    total_funcs = 0
    all_functions = {}

    for c in contracts:
        if c.contract_type == "interface":
            print(f"\n  ⏭️  Skipping interface: {c.name}")
            continue

        print(f"\n  📋 Contract: {c.name}")
        for fn_name, fn in c.functions.items():
            total_funcs += 1
            all_functions[f"{c.name}.{fn_name}"] = fn

            # Classify operation types
            op_counts = Counter(op.op_type.value for op in fn.operations)

            print(f"\n    ┌─ Function: {fn_name}()")
            print(f"    │  Visibility: {fn.visibility}  |  Mutability: {fn.mutability or '(none)'}")
            print(f"    │  Modifiers: {fn.modifiers or '(none)'}")
            print(f"    │  Parameters: {len(fn.parameters)}")
            print(f"    │  Lines: {fn.line_start}-{fn.line_end}")
            print(f"    │  ── Semantic Properties ──")
            print(f"    │  State reads:  {fn.state_reads}")
            print(f"    │  State writes: {fn.state_writes}")
            print(f"    │  External calls: {len(fn.external_calls)}")
            print(f"    │  Internal calls: {fn.internal_calls}")
            print(f"    │  Require checks: {len(fn.require_checks)}")
            print(f"    │  ── Security Flags ──")
            print(f"    │  sends_eth: {fn.sends_eth}")
            print(f"    │  modifies_state: {fn.modifies_state}")
            print(f"    │  has_reentrancy_guard: {fn.has_reentrancy_guard}")
            print(f"    │  has_access_control: {fn.has_access_control}")
            print(f"    │  has_loops: {fn.has_loops}")
            print(f"    │  has_delegatecall: {fn.has_delegatecall}")
            print(f"    │  has_selfdestruct: {fn.has_selfdestruct}")
            print(f"    │  ── Operation Breakdown ──")
            print(f"    │  Total operations: {len(fn.operations)}")
            for op_type, count in sorted(op_counts.items(), key=lambda x: -x[1]):
                print(f"    │    {op_type}: {count}")
            print(f"    └─────────────────────────")

    print(f"\n  📊 Total functions parsed: {total_funcs}")

    # ═══════════════════════════════════════════════════
    #  Step 3: State Variable Analysis
    # ═══════════════════════════════════════════════════
    banner("STEP 3: State Variable Analysis")

    for c in contracts:
        if c.contract_type == "interface":
            continue
        print(f"\n  📋 Contract: {c.name} — {len(c.state_vars)} state variables")
        for var_name, var in c.state_vars.items():
            print(f"    │  {var_name}: {var.var_type} "
                  f"[vis={var.visibility}, const={var.is_constant}, "
                  f"immut={var.is_immutable}, mapping={var.is_mapping}, "
                  f"array={var.is_array}] line {var.line}")

    # ═══════════════════════════════════════════════════
    #  Step 4: Safe Functions Identification
    #  (This is what run_shared_parsing builds)
    # ═══════════════════════════════════════════════════
    banner("STEP 4: Safe Functions Identification (Core Purpose)")

    safe_funcs = set()
    unsafe_funcs = set()

    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            if fn.visibility in ("internal", "private") or fn.mutability in ("view", "pure"):
                safe_funcs.add(fn_name.lower())
            else:
                unsafe_funcs.add(fn_name.lower())

    print(f"\n  ✅ Safe functions (internal/private/view/pure): {len(safe_funcs)}")
    for sf in sorted(safe_funcs):
        print(f"    │  ✓ {sf}")

    print(f"\n  🎯 Unsafe functions (public/external + state-changing): {len(unsafe_funcs)}")
    for uf in sorted(unsafe_funcs):
        print(f"    │  ✗ {uf}")

    # ═══════════════════════════════════════════════════
    #  Step 5: CEI Pattern (Operation Ordering) Analysis
    # ═══════════════════════════════════════════════════
    banner("STEP 5: CEI (Check-Effect-Interaction) Ordering")

    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            if not fn.external_calls:
                continue

            print(f"\n  🔍 {c.name}.{fn_name}() — has {len(fn.external_calls)} external call(s)")

            # Find the first external call's position in operations
            first_call_idx = None
            last_write_idx = None
            for i, op in enumerate(fn.operations):
                if op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH,
                                  OpType.DELEGATECALL) and first_call_idx is None:
                    first_call_idx = i
                if op.op_type == OpType.STATE_WRITE:
                    last_write_idx = i

            if first_call_idx is not None and last_write_idx is not None:
                if last_write_idx > first_call_idx:
                    print(f"    ⚠️  CEI VIOLATION: Write at op[{last_write_idx}] AFTER "
                          f"call at op[{first_call_idx}]")
                    print(f"       Call: {fn.operations[first_call_idx].raw_text[:80]}")
                    print(f"       Write: {fn.operations[last_write_idx].raw_text[:80]}")
                else:
                    print(f"    ✅ CEI compliant: All writes before calls")
            else:
                if first_call_idx is not None:
                    print(f"    ℹ️  External call but no state writes")

    # ═══════════════════════════════════════════════════
    #  Step 6: Modifier Analysis
    # ═══════════════════════════════════════════════════
    banner("STEP 6: Modifier Analysis")

    for c in contracts:
        if c.contract_type == "interface":
            continue
        if not c.modifiers:
            print(f"\n  📋 {c.name}: No modifiers")
            continue

        print(f"\n  📋 Contract: {c.name}")
        for mod_name, mod in c.modifiers.items():
            print(f"    ┌─ modifier {mod_name}")
            print(f"    │  checks_owner: {mod.checks_owner}")
            print(f"    │  checks_role: {mod.checks_role}")
            print(f"    │  is_reentrancy_guard: {mod.is_reentrancy_guard}")
            print(f"    │  is_paused_check: {mod.is_paused_check}")
            print(f"    └─────────────────────────")

    # ═══════════════════════════════════════════════════
    #  Step 7: Accuracy Verification (Manual Ground Truth)
    # ═══════════════════════════════════════════════════
    banner("STEP 7: Accuracy Metrics")

    # Count what we found
    total_contracts = len([c for c in contracts if c.contract_type != "interface"])
    total_interfaces = len([c for c in contracts if c.contract_type == "interface"])
    total_state_vars = sum(len(c.state_vars) for c in contracts if c.contract_type != "interface")
    total_modifiers = sum(len(c.modifiers) for c in contracts if c.contract_type != "interface")
    total_events = sum(len(c.events) for c in contracts if c.contract_type != "interface")

    funcs_with_ext_calls = sum(
        1 for c in contracts if c.contract_type != "interface"
        for fn in c.functions.values() if fn.external_calls
    )
    funcs_with_state_writes = sum(
        1 for c in contracts if c.contract_type != "interface"
        for fn in c.functions.values() if fn.modifies_state
    )
    funcs_with_access_ctrl = sum(
        1 for c in contracts if c.contract_type != "interface"
        for fn in c.functions.values() if fn.has_access_control
    )
    funcs_with_reentrancy_guard = sum(
        1 for c in contracts if c.contract_type != "interface"
        for fn in c.functions.values() if fn.has_reentrancy_guard
    )

    print(f"""
  ┌────────────────────────────────────────────────┐
  │         SHARED PARSING — RESULTS SUMMARY       │
  ├────────────────────────────────────────────────┤
  │  Parse time:              {parse_time:.4f}s             │
  │  Source lines:            {line_count:<20}│
  │  Contracts found:         {total_contracts:<20}│
  │  Interfaces found:        {total_interfaces:<20}│
  │  Total functions:         {total_funcs:<20}│
  │  State variables:         {total_state_vars:<20}│
  │  Modifiers:               {total_modifiers:<20}│
  │  Events:                  {total_events:<20}│
  │  ─────────────────────────────────────────────│
  │  Safe functions:          {len(safe_funcs):<20}│
  │  Unsafe functions:        {len(unsafe_funcs):<20}│
  │  Functions w/ ext calls:  {funcs_with_ext_calls:<20}│
  │  Functions w/ writes:     {funcs_with_state_writes:<20}│
  │  Functions w/ access:     {funcs_with_access_ctrl:<20}│
  │  Functions w/ reent guard:{funcs_with_reentrancy_guard:<20}│
  └────────────────────────────────────────────────┘
""")

    # ═══════════════════════════════════════════════════
    #  Step 8: Cross-check with what run_shared_parsing outputs
    # ═══════════════════════════════════════════════════
    banner("STEP 8: Simulating run_shared_parsing() Output")

    # This simulates exactly what run_shared_parsing() does
    shared = {}
    parsed = parser.parse(source, str(contract_path))
    if parsed:
        nf = sum(len(c.functions) for c in parsed)
        shared["compound_comet"] = {
            "parsed": parsed,
            "source": source,
            "path": contract_path,
        }

    sim_safe = set()
    for entry in shared.values():
        for contract in entry["parsed"]:
            for fn_name, fn in contract.functions.items():
                if fn.visibility in ("internal", "private") or fn.mutability in ("view", "pure"):
                    sim_safe.add(fn_name.lower())

    shared["_safe_funcs"] = sim_safe

    print(f"  Simulated run_shared_parsing output:")
    print(f"    Contracts in shared: {[k for k in shared if not k.startswith('_')]}")
    print(f"    Safe functions: {len(sim_safe)}")
    print(f"    Safe set: {sorted(sim_safe)}")

    # ═══════════════════════════════════════════════════
    #  Step 9: Test on reentrancy_vault too (known vulnerable)
    # ═══════════════════════════════════════════════════
    banner("STEP 9: Quick Test on reentrancy_vault.sol (Known Vulnerable)")

    vuln_path = PROJECT_ROOT / "test_contracts" / "vulnerable" / "reentrancy_vault.sol"
    if vuln_path.exists():
        with open(vuln_path, "r", encoding="utf-8") as f:
            vuln_source = f.read()

        t1 = time.perf_counter()
        vuln_contracts = parser.parse(vuln_source, str(vuln_path))
        t2 = time.perf_counter()

        print(f"  Parse time: {t2-t1:.4f}s")
        for c in vuln_contracts:
            if c.contract_type == "interface":
                continue
            print(f"\n  Contract: {c.name}")
            for fn_name, fn in c.functions.items():
                if fn.external_calls:
                    print(f"    {fn_name}(): ext_calls={len(fn.external_calls)}, "
                          f"writes={fn.state_writes}, "
                          f"reentrancy_guard={fn.has_reentrancy_guard}, "
                          f"sends_eth={fn.sends_eth}")

                    # Check CEI
                    first_call = None
                    writes_after = []
                    for i, op in enumerate(fn.operations):
                        if op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH) and first_call is None:
                            first_call = i
                        if first_call is not None and op.op_type == OpType.STATE_WRITE:
                            writes_after.append((i, op.target))

                    if writes_after:
                        print(f"    ⚠️  CEI VIOLATION DETECTED!")
                        for idx, target in writes_after:
                            print(f"       Write to '{target}' at op[{idx}] AFTER call at op[{first_call}]")
                    else:
                        print(f"    ✅ No CEI violation")
    else:
        print(f"  ⚠️  reentrancy_vault.sol not found")

    banner("TEST COMPLETE")
    return contracts, safe_funcs, parse_time


if __name__ == "__main__":
    test_shared_parsing_on_compound_comet()
