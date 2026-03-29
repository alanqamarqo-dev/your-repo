"""
═══════════════════════════════════════════════════════════════
 Deep Accuracy Audit — Stage 2.5 Shared Parsing
 يقارن مخرجات الـ Parser مع Ground Truth يدوي (تحليل Regex مباشر)
═══════════════════════════════════════════════════════════════
"""
import sys, re, time
from pathlib import Path
from collections import Counter, defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
from agl_security_tool.detectors import OpType

# ═════════════════════════════════════════════════════════════
# GROUND TRUTH — manual regex extraction for comparison
# ═════════════════════════════════════════════════════════════

def ground_truth_extract(source: str):
    """Independent extraction NOT using the AGL parser — pure regex ground truth."""
    gt = {
        "contracts": [],
        "interfaces": [],
        "libraries": [],
        "functions": {},        # name -> {visibility, mutability, in_contract}
        "state_vars": [],
        "external_calls": [],   # (line, text)
        "state_writes": [],     # (line, text)
        "modifiers_decl": [],
        "events_decl": [],
    }

    lines = source.splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Contracts / interfaces / libraries
        m = re.match(r'(contract|interface|library|abstract\s+contract)\s+(\w+)', stripped)
        if m:
            kind = m.group(1).replace("abstract contract", "abstract")
            name = m.group(2)
            if "interface" in kind:
                gt["interfaces"].append(name)
            elif "library" in kind:
                gt["libraries"].append(name)
            else:
                gt["contracts"].append(name)

        # Functions
        fm = re.match(r'function\s+(\w+)\s*\(', stripped)
        if fm:
            fn_name = fm.group(1)
            vis = "internal"
            for v in ("external", "public", "private", "internal"):
                if v in line:
                    vis = v
                    break
            mut = None
            for m_ in ("view", "pure", "payable"):
                if m_ in line:
                    mut = m_
                    break
            # Find parent contract
            parent = "unknown"
            for j in range(i - 1, 0, -1):
                cm = re.match(r'\s*(contract|library|abstract\s+contract)\s+(\w+)', lines[j-1])
                if cm:
                    parent = cm.group(2)
                    break
            gt["functions"][f"{parent}.{fn_name}@L{i}"] = {
                "name": fn_name, "visibility": vis, "mutability": mut, "line": i, "contract": parent
            }

        # Modifier declarations
        if re.match(r'modifier\s+(\w+)', stripped):
            mm = re.match(r'modifier\s+(\w+)', stripped)
            gt["modifiers_decl"].append(mm.group(1))

        # Event declarations
        if re.match(r'event\s+(\w+)', stripped):
            em = re.match(r'event\s+(\w+)', stripped)
            gt["events_decl"].append(em.group(1))

        # External calls (interface casts + low-level calls)
        ext_patterns = [
            r'IERC20\(\w+\)\.\w+\(',
            r'IPriceFeed\(\w+\)\.\w+\(',
            r'\w+\.call\{',
            r'\w+\.delegatecall\(',
            r'\w+\.staticcall\(',
            r'\w+\.transfer\(',
            r'\w+\.send\(',
            r'\w+\.safeTransfer\w*\(',
        ]
        for pat in ext_patterns:
            if re.search(pat, stripped):
                gt["external_calls"].append((i, stripped[:100]))
                break

        # State assignments (excludes comments, local vars common patterns)
        assign = re.match(r'(\w[\w\[\].\s]*)\s*(?:=|\+=|-=|\*=|/=)\s', stripped)
        if assign and not stripped.startswith('//') and not stripped.startswith('/*'):
            var = assign.group(1).strip().split('[')[0].split('.')[0]
            # Heuristic: state vars usually start lowercase and aren't type declarations
            if var not in ('uint', 'int', 'bool', 'address', 'bytes', 'string', 'uint256',
                          'uint104', 'uint64', 'uint40', 'uint8', 'uint128', 'uint16',
                          'int104', 'int256', 'mapping', 'AssetConfig', 'UserBasic',
                          'TotalsBasic', 'TotalsCollateral', 'UserCollateral',
                          'AssetInfo', 'address[]'):
                gt["state_writes"].append((i, var, stripped[:100]))

    return gt


def compare_deep(source, file_path):
    """Run parser + ground truth and compare every metric."""
    parser = SoliditySemanticParser()
    
    # Parse with the AGL parser
    t0 = time.perf_counter()
    contracts = parser.parse(source, str(file_path))
    parse_time = time.perf_counter() - t0
    
    # Ground truth
    gt = ground_truth_extract(source)
    
    print(f"\n{'='*80}")
    print(f"  FILE: {file_path.name} ({len(source.splitlines())} lines)")
    print(f"  Parse time: {parse_time:.4f}s")
    print(f"{'='*80}")
    
    # ─── 1. Contract Detection ───────────────────
    parser_contracts = [c.name for c in contracts if c.contract_type != "interface"]
    parser_interfaces = [c.name for c in contracts if c.contract_type == "interface"]
    parser_libraries = [c.name for c in contracts if c.contract_type == "library"]
    
    gt_all = gt["contracts"] + gt["libraries"]
    
    print(f"\n┌─ 1. CONTRACT DETECTION")
    print(f"│  Ground truth: {gt['contracts']} + libs:{gt['libraries']} + ifaces:{gt['interfaces']}")
    print(f"│  Parser found: contracts={parser_contracts}, ifaces={parser_interfaces}, libs={parser_libraries}")
    
    missed_contracts = set(gt_all) - set(parser_contracts) - set(parser_libraries)
    extra_contracts = set(parser_contracts + parser_libraries) - set(gt_all)
    
    if missed_contracts:
        print(f"│  ❌ MISSED: {missed_contracts}")
    if extra_contracts:
        print(f"│  ⚠️  EXTRA: {extra_contracts}")
    if not missed_contracts and not extra_contracts:
        print(f"│  ✅ 100% match")
    print(f"└──────────────────────")
    
    # ─── 2. Function Detection ───────────────────
    parser_funcs = {}
    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            parser_funcs[f"{c.name}.{fn_name}"] = fn
    
    gt_non_iface = {k: v for k, v in gt["functions"].items() 
                    if v["contract"] not in gt["interfaces"]}
    gt_func_names = set(v["name"] for v in gt_non_iface.values())
    parser_func_names = set()
    for c in contracts:
        if c.contract_type == "interface":
            continue
        parser_func_names.update(c.functions.keys())
    
    print(f"\n┌─ 2. FUNCTION DETECTION")
    print(f"│  Ground truth (non-interface): {len(gt_non_iface)} function declarations")
    print(f"│  Parser found: {len(parser_funcs)} functions")
    print(f"│  Unique names GT: {len(gt_func_names)}, Parser: {len(parser_func_names)}")
    
    # Check for duplicates in GT (overloaded functions)
    gt_name_counts = Counter(v["name"] for v in gt_non_iface.values())
    overloaded = {k: v for k, v in gt_name_counts.items() if v > 1}
    if overloaded:
        print(f"│  ⚠️  Overloaded functions in GT: {overloaded}")
        print(f"│  (Parser uses name as dict key → loses overloads)")
    
    missed_funcs = gt_func_names - parser_func_names
    extra_funcs = parser_func_names - gt_func_names
    # Also count constructor/fallback/receive which GT might miss
    special = {'constructor', 'fallback', 'receive'}
    missed_funcs -= special
    
    if missed_funcs:
        print(f"│  ❌ MISSED functions: {sorted(missed_funcs)}")
    if extra_funcs - special:
        print(f"│  ⚠️  EXTRA functions: {sorted(extra_funcs - special)}")
    
    overlap = gt_func_names & parser_func_names
    match_pct = len(overlap) / max(len(gt_func_names), 1) * 100
    print(f"│  Match rate: {match_pct:.1f}% ({len(overlap)}/{len(gt_func_names)})")
    print(f"└──────────────────────")
    
    # ─── 3. Function Visibility Accuracy ───────────────────
    print(f"\n┌─ 3. VISIBILITY ACCURACY")
    vis_correct = 0
    vis_total = 0
    vis_errors = []
    for gt_key, gt_fn in gt_non_iface.items():
        fn_name = gt_fn["name"]
        for c in contracts:
            if c.contract_type == "interface":
                continue
            if fn_name in c.functions:
                pf = c.functions[fn_name]
                vis_total += 1
                if pf.visibility == gt_fn["visibility"]:
                    vis_correct += 1
                else:
                    vis_errors.append(f"{fn_name}: GT={gt_fn['visibility']} vs Parser={pf.visibility}")
                break
    
    if vis_total > 0:
        print(f"│  Checked: {vis_total}, Correct: {vis_correct}, Accuracy: {vis_correct/vis_total*100:.1f}%")
    if vis_errors:
        for e in vis_errors[:5]:
            print(f"│  ❌ {e}")
        if len(vis_errors) > 5:
            print(f"│  ... and {len(vis_errors)-5} more")
    elif vis_total > 0:
        print(f"│  ✅ All visibility matches correct")
    print(f"└──────────────────────")
    
    # ─── 4. External Call Detection ───────────────────
    print(f"\n┌─ 4. EXTERNAL CALL DETECTION (Critical)")
    gt_ext = gt["external_calls"]
    parser_ext = []
    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            for op in fn.operations:
                if op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH, 
                                  OpType.DELEGATECALL, OpType.STATICCALL):
                    parser_ext.append((op.line, fn_name, op.raw_text[:80] if op.raw_text else ""))
    
    print(f"│  Ground truth external calls: {len(gt_ext)}")
    for line, text in gt_ext:
        print(f"│    L{line}: {text[:80]}")
    
    print(f"│  Parser detected external calls: {len(parser_ext)}")
    for line, fn, text in parser_ext:
        print(f"│    L{line} in {fn}(): {text[:80]}")
    
    if len(gt_ext) > 0:
        detection_rate = len(parser_ext) / len(gt_ext) * 100
        print(f"│  Detection rate: {detection_rate:.1f}% ({len(parser_ext)}/{len(gt_ext)})")
    
    missed_calls = []
    for line, text in gt_ext:
        found = any(abs(pe[0] - line) <= 1 for pe in parser_ext)
        if not found:
            missed_calls.append((line, text))
    
    if missed_calls:
        print(f"│  ❌ MISSED external calls ({len(missed_calls)}):")
        for line, text in missed_calls:
            print(f"│    L{line}: {text[:80]}")
            # Diagnose WHY it was missed
            if re.search(r'\w+\(\w+\)\.\w+\(', text):
                print(f"│    → CAUSE: Interface cast pattern (e.g. IERC20(addr).func()) not matched by regex")
            elif '.call{' in text:
                print(f"│    → CAUSE: Low-level call missed")
    else:
        print(f"│  ✅ All external calls detected")
    print(f"└──────────────────────")
    
    # ─── 5. State Write Detection (Inheritance Problem) ───────────────
    print(f"\n┌─ 5. STATE WRITE DETECTION")
    
    # What the parser found
    parser_writes = defaultdict(list)
    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            if fn.state_writes:
                parser_writes[fn_name] = fn.state_writes
                
    parser_write_count = sum(len(v) for v in parser_writes.values())
    
    # State vars per contract
    print(f"│  State variables by contract:")
    all_state_var_names = set()
    for c in contracts:
        if c.contract_type == "interface":
            continue
        var_names = list(c.state_vars.keys())
        all_state_var_names.update(var_names)
        print(f"│    {c.name}: {len(var_names)} vars")
    
    # Inheritance analysis
    inheritance_map = {}
    for c in contracts:
        if c.inherits:
            parents = [p.strip() for p in c.inherits.split(',')]
            inheritance_map[c.name] = parents
    
    if inheritance_map:
        print(f"│  Inheritance chain:")
        for child, parents in inheritance_map.items():
            parent_vars = []
            for p in parents:
                for c in contracts:
                    if c.name == p:
                        parent_vars.extend(c.state_vars.keys())
            print(f"│    {child} → {parents} (inherits {len(parent_vars)} vars)")
            if parent_vars:
                print(f"│    Inherited vars: {parent_vars[:10]}{'...' if len(parent_vars) > 10 else ''}")
    
    # Detect writes to inherited vars that parser missed
    comet_contract = None
    storage_contract = None
    for c in contracts:
        if c.name == "Comet":
            comet_contract = c
        if c.name == "CometStorage":
            storage_contract = c
    
    if comet_contract and storage_contract:
        inherited_vars = set(storage_contract.state_vars.keys())
        comet_own_vars = set(comet_contract.state_vars.keys())
        
        print(f"│  ")
        print(f"│  Comet has {len(comet_own_vars)} own vars, inherits {len(inherited_vars)} from CometStorage")
        print(f"│  Parser only checks {len(comet_own_vars)} own vars for state writes!")
        print(f"│  Missing from analysis: {sorted(inherited_vars)[:10]}...")
        
        # Manual check: how many functions in Comet write to inherited vars?
        writes_to_inherited = 0
        for fn_name, fn in comet_contract.functions.items():
            for op in fn.operations:
                if op.raw_text:
                    for ivar in inherited_vars:
                        if re.search(rf'\b{re.escape(ivar)}\b\s*(?:=|\+=|-=)', op.raw_text):
                            writes_to_inherited += 1
                            break
        
        print(f"│  Operations that write to inherited vars (rough): {writes_to_inherited}")
    
    print(f"│  ")
    print(f"│  Parser detected state writes: {parser_write_count}")
    for fn, writes in parser_writes.items():
        print(f"│    {fn}(): writes={writes}")
    print(f"└──────────────────────")
    
    # ─── 6. Operation Ordering Depth ───────────────────
    print(f"\n┌─ 6. OPERATION ORDERING DEPTH")
    
    total_ops = 0
    op_type_counter = Counter()
    funcs_with_ops = 0
    max_ops = 0
    max_ops_fn = ""
    
    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            n = len(fn.operations)
            total_ops += n
            if n > 0:
                funcs_with_ops += 1
            if n > max_ops:
                max_ops = n
                max_ops_fn = f"{c.name}.{fn_name}"
            for op in fn.operations:
                op_type_counter[op.op_type.value] += 1
    
    print(f"│  Total operations tracked: {total_ops}")
    print(f"│  Functions with operations: {funcs_with_ops}")
    print(f"│  Max operations in one func: {max_ops} ({max_ops_fn})")
    print(f"│  Operation type distribution:")
    for op_type, count in sorted(op_type_counter.items(), key=lambda x: -x[1]):
        bar = '█' * min(count, 40)
        print(f"│    {op_type:25s} {count:4d} {bar}")
    
    # Check: for functions with state_writes AND external_calls — can we detect ordering?
    print(f"│  ")
    print(f"│  CEI-relevant functions (both ext_calls + state_writes):")
    cei_funcs = 0
    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            if fn.external_calls and fn.state_writes:
                cei_funcs += 1
                first_call = None
                last_write = None
                for i, op in enumerate(fn.operations):
                    if op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH) and first_call is None:
                        first_call = i
                    if op.op_type == OpType.STATE_WRITE:
                        last_write = i
                if first_call is not None and last_write is not None:
                    if last_write > first_call:
                        print(f"│    ⚠️  {c.name}.{fn_name}(): CEI VIOLATION (write@{last_write} > call@{first_call})")
                    else:
                        print(f"│    ✅ {c.name}.{fn_name}(): CEI OK")
    
    if cei_funcs == 0:
        print(f"│    (none found — likely due to ext_call detection gap)")
    print(f"└──────────────────────")
    
    # ─── 7. Computed Properties Accuracy ───────────────────
    print(f"\n┌─ 7. COMPUTED SECURITY PROPERTIES")
    
    properties = {
        "has_reentrancy_guard": 0, "has_access_control": 0,
        "sends_eth": 0, "modifies_state": 0,
        "has_loops": 0, "has_delegatecall": 0, "has_selfdestruct": 0
    }
    
    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            if fn.has_reentrancy_guard: properties["has_reentrancy_guard"] += 1
            if fn.has_access_control: properties["has_access_control"] += 1
            if fn.sends_eth: properties["sends_eth"] += 1
            if fn.modifies_state: properties["modifies_state"] += 1
            if fn.has_loops: properties["has_loops"] += 1
            if fn.has_delegatecall: properties["has_delegatecall"] += 1
            if fn.has_selfdestruct: properties["has_selfdestruct"] += 1
    
    for prop, count in properties.items():
        print(f"│  {prop}: {count} functions")
    
    # Verify reentrancy guard specifically
    reent_guarded = []
    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            if fn.has_reentrancy_guard:
                reent_guarded.append(fn_name)
    
    # Ground truth from contract
    gt_nonreentrant = []
    for i, line in enumerate(source.splitlines(), 1):
        if 'nonReentrant' in line and 'function' in line:
            m = re.search(r'function\s+(\w+)', line)
            if m:
                gt_nonreentrant.append(m.group(1))
    
    print(f"│  ")
    print(f"│  nonReentrant guard verification:")
    print(f"│    GT functions with nonReentrant: {gt_nonreentrant}")
    print(f"│    Parser detected guard on: {reent_guarded}")
    if set(reent_guarded) == set(gt_nonreentrant):
        print(f"│    ✅ Perfect match")
    else:
        print(f"│    ❌ Mismatch: missed={set(gt_nonreentrant)-set(reent_guarded)}, extra={set(reent_guarded)-set(gt_nonreentrant)}")
    
    # Access control verification
    gt_access = []
    for i, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if re.search(r'msg\.sender\s*!=\s*governor|msg\.sender\s*==\s*governor|onlyOwner|onlyAdmin|onlyGovernor', stripped):
            if 'function' not in stripped and 'require' in stripped or 'revert' in stripped or 'if' in stripped:
                # Find enclosing function
                for j in range(i-1, max(0, i-50), -1):
                    fm = re.match(r'\s*function\s+(\w+)', source.splitlines()[j-1])
                    if fm:
                        gt_access.append(fm.group(1))
                        break
    
    print(f"│  Access control verification:")
    print(f"│    GT functions with governor check: {gt_access}")
    access_ctrl_funcs = [fn_name for c in contracts if c.contract_type != "interface" 
                         for fn_name, fn in c.functions.items() if fn.has_access_control]
    print(f"│    Parser detected access control: {access_ctrl_funcs}")
    print(f"└──────────────────────")
    
    # ─── 8. Safe Functions Analysis ───────────────────
    print(f"\n┌─ 8. SAFE FUNCTIONS CLASSIFICATION DEPTH")
    safe = set()
    unsafe = set()
    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            if fn.visibility in ("internal", "private") or fn.mutability in ("view", "pure"):
                safe.add(fn_name)
            else:
                unsafe.add(fn_name)
    
    print(f"│  Safe: {len(safe)}, Unsafe: {len(unsafe)}")
    
    # Are there functions classified as "safe" that actually modify state?
    false_safe = []
    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            if fn_name.lower() in {s.lower() for s in safe}:
                if fn.modifies_state or fn.external_calls:
                    false_safe.append(f"{fn_name} (modifies={fn.modifies_state}, ext_calls={len(fn.external_calls)})")
    
    if false_safe:
        print(f"│  ⚠️  'Safe' functions that actually affect state:")
        for fs in false_safe:
            print(f"│    {fs}")
    
    # Key question: internal functions that DO modify state (like supplyInternal)
    # The parser classifies them as "safe" but they're critical
    critical_internals = []
    for c in contracts:
        if c.contract_type == "interface":
            continue
        for fn_name, fn in c.functions.items():
            if fn.visibility == "internal" and fn.mutability not in ("view", "pure"):
                # This is classified "safe" by visibility, but may be state-changing
                if fn_name.lower() in {s.lower() for s in safe}:
                    critical_internals.append(fn_name)
    
    if critical_internals:
        print(f"│  ⚠️  Internal non-view/pure (classified 'safe' by visibility only):")
        for ci in sorted(critical_internals):
            print(f"│    {ci}")
        print(f"│  → These are skipped by downstream finding suppression!")
    
    print(f"└──────────────────────")
    
    return {
        "contracts_accuracy": 100 if not missed_contracts else (1 - len(missed_contracts)/len(gt_all)) * 100,
        "functions_accuracy": match_pct,
        "ext_call_detection": len(parser_ext) / max(len(gt_ext), 1) * 100,
        "parse_time": parse_time,
        "total_ops": total_ops,
    }


def main():
    print("═" * 80)
    print("  DEEP ACCURACY AUDIT — Stage 2.5 Shared Parsing")
    print("  Testing on ALL available real-world contracts")
    print("═" * 80)
    
    real_world_dir = PROJECT_ROOT / "test_contracts" / "real_world"
    vuln_dir = PROJECT_ROOT / "test_contracts" / "vulnerable"
    
    results = {}
    
    # Test all real_world contracts  
    if real_world_dir.exists():
        for sol in sorted(real_world_dir.glob("*.sol")):
            source = sol.read_text(encoding="utf-8", errors="replace")
            if len(source.strip()) < 50:
                continue
            try:
                r = compare_deep(source, sol)
                results[sol.name] = r
            except Exception as e:
                print(f"\n❌ CRASH on {sol.name}: {e}")
                import traceback
                traceback.print_exc()
                results[sol.name] = {"crash": str(e)}
    
    # Test 3 vulnerable contracts
    if vuln_dir.exists():
        for sol in sorted(vuln_dir.glob("*.sol"))[:3]:
            source = sol.read_text(encoding="utf-8", errors="replace")
            if len(source.strip()) < 50:
                continue
            try:
                r = compare_deep(source, sol)
                results[sol.name] = r
            except Exception as e:
                print(f"\n❌ CRASH on {sol.name}: {e}")
                results[sol.name] = {"crash": str(e)}
    
    # ═══ FINAL SUMMARY ═══
    print(f"\n{'═'*80}")
    print(f"  AGGREGATE ACCURACY SUMMARY")
    print(f"{'═'*80}")
    
    success = {k: v for k, v in results.items() if "crash" not in v}
    crashes = {k: v for k, v in results.items() if "crash" in v}
    
    if success:
        avg_contract = sum(v["contracts_accuracy"] for v in success.values()) / len(success)
        avg_func = sum(v["functions_accuracy"] for v in success.values()) / len(success)
        avg_ext = sum(v["ext_call_detection"] for v in success.values()) / len(success)
        avg_time = sum(v["parse_time"] for v in success.values()) / len(success)
        total_ops_sum = sum(v["total_ops"] for v in success.values())
        
        print(f"\n  Files tested: {len(results)} ({len(success)} OK, {len(crashes)} crashed)")
        print(f"\n  ┌────────────────────────────────────────────────┐")
        print(f"  │  METRIC                        AVG ACCURACY    │")
        print(f"  ├────────────────────────────────────────────────┤")
        print(f"  │  Contract detection:           {avg_contract:6.1f}%          │")
        print(f"  │  Function detection:           {avg_func:6.1f}%          │")
        print(f"  │  External call detection:      {avg_ext:6.1f}%          │")
        print(f"  │  Avg parse time:               {avg_time:.4f}s          │")
        print(f"  │  Total operations tracked:     {total_ops_sum:6d}           │")
        print(f"  └────────────────────────────────────────────────┘")
    
    if crashes:
        print(f"\n  CRASHES:")
        for name, v in crashes.items():
            print(f"    {name}: {v['crash'][:100]}")


if __name__ == "__main__":
    main()
