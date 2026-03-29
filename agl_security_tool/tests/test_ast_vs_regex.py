"""
Side-by-side comparison: Regex Parser vs AST Parser
Tests on real contracts to verify the AST parser matches or exceeds regex quality.
"""

import sys, time, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))

from detectors.solidity_parser import SoliditySemanticParser
from detectors.solidity_ast_parser import SolidityASTParserFull
from detectors import ParsedContract

CONTRACT_DIR = ROOT / "test_contracts" / "real_world"
VULN_DIR = ROOT / "test_contracts" / "vulnerable"


def load(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def compare_contract(name: str, regex_c: ParsedContract, ast_c: ParsedContract) -> dict:
    """Compare a single contract from both parsers."""
    issues = []

    # State vars
    regex_vars = set(regex_c.state_vars.keys())
    ast_vars = set(ast_c.state_vars.keys())
    missing_vars = regex_vars - ast_vars
    extra_vars = ast_vars - regex_vars
    if missing_vars:
        issues.append(f"AST missing state vars: {sorted(missing_vars)}")
    
    # Functions
    regex_funcs = set(regex_c.functions.keys())
    ast_funcs = set(ast_c.functions.keys())
    missing_funcs = regex_funcs - ast_funcs
    extra_funcs = ast_funcs - regex_funcs
    if missing_funcs:
        issues.append(f"AST missing functions: {sorted(missing_funcs)}")

    # Per-function comparison
    common_funcs = regex_funcs & ast_funcs
    ext_call_diff = 0
    state_write_diff = 0
    state_read_diff = 0
    for fname in common_funcs:
        rf = regex_c.functions[fname]
        af = ast_c.functions[fname]
        if len(af.external_calls) < len(rf.external_calls):
            ext_call_diff += len(rf.external_calls) - len(af.external_calls)
        if len(af.state_writes) < len(rf.state_writes):
            state_write_diff += len(rf.state_writes) - len(af.state_writes)

    return {
        "name": name,
        "regex_vars": len(regex_vars),
        "ast_vars": len(ast_vars),
        "extra_vars": len(extra_vars),
        "regex_funcs": len(regex_funcs),
        "ast_funcs": len(ast_funcs),
        "extra_funcs": len(extra_funcs),
        "missing_funcs": len(missing_funcs),
        "ext_call_regression": ext_call_diff,
        "state_write_regression": state_write_diff,
        "issues": issues,
    }


def test_file(path: Path):
    """Test a single .sol file with both parsers."""
    source = load(path)
    name = path.name

    regex_parser = SoliditySemanticParser()
    ast_parser_full = SolidityASTParserFull()
    
    # Time regex parser
    t0 = time.perf_counter()
    regex_contracts = regex_parser.parse(source, name)
    t_regex = time.perf_counter() - t0

    # Time AST parser
    t0 = time.perf_counter()
    ast_contracts = ast_parser_full.parse(source, name)
    t_ast = time.perf_counter() - t0

    print(f"\n{'─'*60}")
    print(f"  {name}")
    print(f"  Regex: {len(regex_contracts)} contracts in {t_regex*1000:.1f}ms")
    print(f"  AST:   {len(ast_contracts)} contracts in {t_ast*1000:.1f}ms")

    # Compare contract-by-contract
    regex_by_name = {c.name: c for c in regex_contracts}
    ast_by_name = {c.name: c for c in ast_contracts}

    all_names = set(regex_by_name.keys()) | set(ast_by_name.keys())
    results = []

    for cname in sorted(all_names):
        rc = regex_by_name.get(cname)
        ac = ast_by_name.get(cname)
        if rc and ac:
            r = compare_contract(cname, rc, ac)
            results.append(r)
            status = "✅" if not r["issues"] and r["missing_funcs"] == 0 else "⚠️"
            print(f"  {status} {cname}: vars({r['regex_vars']}→{r['ast_vars']}) "
                  f"funcs({r['regex_funcs']}→{r['ast_funcs']}) "
                  f"extra_funcs(+{r['extra_funcs']}) "
                  f"ext_call_regression({r['ext_call_regression']})")
            if r["issues"]:
                for issue in r["issues"]:
                    print(f"     ⚠ {issue}")
        elif rc and not ac:
            print(f"  ❌ {cname}: MISSING in AST parser")
            results.append({"name": cname, "issues": ["contract missing from AST"]})
        elif ac and not rc:
            print(f"  ➕ {cname}: NEW in AST parser (regex missed)")
            results.append({"name": cname, "issues": []})

    return results, t_regex, t_ast


def main():
    print("=" * 60)
    print("  Regex Parser vs AST Parser — Comparison Suite")
    print("=" * 60)

    # Collect test files
    test_files = []
    if CONTRACT_DIR.exists():
        test_files.extend(sorted(CONTRACT_DIR.glob("*.sol")))
    if VULN_DIR.exists():
        # Add a few vuln files
        vuln_files = sorted(VULN_DIR.glob("*.sol"))[:5]
        test_files.extend(vuln_files)

    if not test_files:
        print("No test contracts found!")
        sys.exit(1)

    total_results = []
    total_regex_ms = 0
    total_ast_ms = 0

    for path in test_files:
        try:
            results, t_r, t_a = test_file(path)
            total_results.extend(results)
            total_regex_ms += t_r * 1000
            total_ast_ms += t_a * 1000
        except Exception as e:
            print(f"\n  ❌ ERROR on {path.name}: {e}")
            traceback.print_exc()

    # Summary
    print(f"\n\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    
    contracts_with_issues = sum(1 for r in total_results if r.get("issues"))
    contracts_ok = len(total_results) - contracts_with_issues
    total_missing_funcs = sum(r.get("missing_funcs", 0) for r in total_results)
    total_ext_regression = sum(r.get("ext_call_regression", 0) for r in total_results)

    print(f"  Total contracts compared: {len(total_results)}")
    print(f"  Contracts OK (no regressions): {contracts_ok}")
    print(f"  Contracts with issues: {contracts_with_issues}")
    print(f"  Total missing functions: {total_missing_funcs}")
    print(f"  Total ext_call regressions: {total_ext_regression}")
    print(f"  Performance: Regex {total_regex_ms:.0f}ms vs AST {total_ast_ms:.0f}ms")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
