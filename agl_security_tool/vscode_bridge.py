#!/usr/bin/env python3
"""
AGL Security — جسر VS Code
Python bridge for VS Code extension — uses full ProjectScanner + AGLSecurityAudit API.

This script is called by the VS Code extension with JSON commands on stdin,
and returns JSON results on stdout. All engine output goes to stderr.

Protocol:
    {"action": "scan_file", "target": "path.sol", "mode": "deep"}
    {"action": "scan_project", "target": "path/", "mode": "deep", "config": {...}}
    {"action": "discover", "target": "path/"}
    {"action": "stats", "target": "path/"}
    {"action": "graph", "target": "path/"}
    {"action": "check"}
"""

import sys
import os
import json
import time
import io

# Redirect all print/logging to stderr so stdout stays clean JSON
_real_stdout = sys.stdout
sys.stdout = sys.stderr


def main():
    # Read command from stdin
    raw = sys.stdin.buffer.read().decode('utf-8').strip()
    if not raw:
        send_result({"error": "No input", "status": "ERROR"})
        return

    try:
        cmd = json.loads(raw)
    except json.JSONDecodeError as e:
        send_result({"error": f"Invalid JSON: {e}", "status": "ERROR"})
        return

    action = cmd.get("action", "")
    target = cmd.get("target", "")
    mode = cmd.get("mode", "scan")
    config = cmd.get("config", {})

    # ═══ Setup paths ═══
    tool_dir = os.path.dirname(os.path.abspath(__file__))
    agl_root = os.path.dirname(tool_dir)
    engines_src = os.path.join(agl_root, "AGL_NextGen", "src")
    for p in [agl_root, engines_src]:
        if p not in sys.path:
            sys.path.insert(0, p)

    try:
        if action == "check":
            from agl_security_tool import __version__
            send_result({
                "status": "OK",
                "version": __version__,
                "python": sys.version,
                "engines": detect_engines()
            })

        elif action == "scan_file":
            result = scan_file(target, mode, config)
            send_result(result)

        elif action == "scan_project":
            result = scan_project(target, mode, config)
            send_result(result)

        elif action == "discover":
            result = discover_project(target, config)
            send_result(result)

        elif action == "stats":
            result = project_stats(target, config)
            send_result(result)

        elif action == "graph":
            result = dependency_graph(target, config)
            send_result(result)

        else:
            send_result({"error": f"Unknown action: {action}", "status": "ERROR"})

    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        send_result({"error": str(e), "status": "ERROR", "traceback": traceback.format_exc()})


def send_result(data: dict):
    """Write JSON result to real stdout."""
    out = json.dumps(data, ensure_ascii=False, default=str)
    _real_stdout.write(out)
    _real_stdout.flush()


def detect_engines() -> dict:
    """Check which engines are available."""
    engines = {}
    try:
        from agl.engines.smart_contract_analyzer import SmartContractAnalyzer
        engines["smart_contract_analyzer"] = True
    except Exception:
        engines["smart_contract_analyzer"] = False
    try:
        from agl.engines.agl_security import AGLSecuritySuite
        engines["agl_security_suite"] = True
    except Exception:
        engines["agl_security_suite"] = False
    try:
        from agl.engines.offensive_security import OffensiveSecurityEngine
        engines["offensive_security"] = True
    except Exception:
        engines["offensive_security"] = False
    try:
        from agl.engines.formal_verifier import FormalVerificationEngine
        engines["formal_verifier"] = True
    except Exception:
        engines["formal_verifier"] = False
    try:
        from agl_security_tool.detectors import DetectorRunner
        dr = DetectorRunner()
        engines["detectors"] = len(dr.detectors)
    except Exception:
        engines["detectors"] = 0
    return engines


# ═══════════════════════════════════════════════════
# Actions
# ═══════════════════════════════════════════════════

def scan_file(target: str, mode: str, config: dict) -> dict:
    """Scan a single file using AGLSecurityAudit."""
    from agl_security_tool import AGLSecurityAudit
    audit = AGLSecurityAudit(config or None)

    if mode == "deep":
        return audit.deep_scan(target)
    elif mode == "quick":
        return audit.quick_scan(target)
    else:
        return audit.scan(target)


def scan_project(target: str, mode: str, config: dict) -> dict:
    """
    Full project scan using ProjectScanner API.
    This is the REAL power — discover + scan + cross-contract analysis.
    """
    from agl_security_tool import ProjectScanner

    scanner = ProjectScanner(target, config=config)
    scanner.discover()

    # Get project info first
    info = scanner.project_info
    stats = scanner.get_project_stats()

    print(f"📁 Project: {info.project_type} | {info.total_sol_files} files | {info.total_contracts} contracts", file=sys.stderr)

    # Run scan based on mode
    if mode == "deep":
        report = scanner.deep_scan(output_format="dict")
    elif mode == "quick":
        report = scanner.quick_scan(output_format="dict")
    else:
        report = scanner.full_scan(output_format="dict")

    # Enrich with full project context
    report["project_info"] = {
        "project_type": info.project_type,
        "root_dir": info.root_dir,
        "contracts_dir": info.contracts_dir,
        "test_dir": info.test_dir,
        "compiler_version": info.compiler_version,
        "total_sol_files": info.total_sol_files,
        "total_contracts": info.total_contracts,
        "remappings": info.remappings,
    }
    report["project_stats"] = stats
    report["dependency_graph"] = scanner.get_dependency_graph()

    # Per-file details with inheritance + imports
    report["files_detail"] = {}
    for rel_path, sf in scanner.files.items():
        report["files_detail"][rel_path] = {
            "contracts": sf.contracts,
            "interfaces": sf.interfaces,
            "libraries": sf.libraries,
            "inherits": sf.inherits,
            "imports": sf.imports,
            "loc": sf.loc,
            "functions_count": sf.functions_count,
            "external_calls": sf.external_calls,
            "state_vars": sf.state_vars,
            "pragma": sf.pragma,
            "license": sf.license,
        }

    return report


def discover_project(target: str, config: dict) -> dict:
    """Discover project structure without scanning."""
    from agl_security_tool import ProjectScanner

    scanner = ProjectScanner(target, config=config)
    info = scanner.discover()

    return {
        "status": "OK",
        "project_info": {
            "project_type": info.project_type,
            "root_dir": info.root_dir,
            "contracts_dir": info.contracts_dir,
            "test_dir": info.test_dir,
            "compiler_version": info.compiler_version,
            "total_sol_files": info.total_sol_files,
            "total_contracts": info.total_contracts,
            "remappings": info.remappings,
            "lib_dirs": info.lib_dirs,
        },
        "files": {
            rel: {
                "contracts": sf.contracts,
                "interfaces": sf.interfaces,
                "libraries": sf.libraries,
                "inherits": sf.inherits,
                "imports": sf.imports,
                "loc": sf.loc,
                "functions_count": sf.functions_count,
                "external_calls": sf.external_calls,
                "state_vars": sf.state_vars,
            }
            for rel, sf in scanner.files.items()
        },
        "dependency_graph": scanner.get_dependency_graph(),
        "stats": scanner.get_project_stats(),
    }


def project_stats(target: str, config: dict) -> dict:
    """Get project statistics."""
    from agl_security_tool import ProjectScanner
    scanner = ProjectScanner(target, config=config)
    scanner.discover()
    stats = scanner.get_project_stats()
    stats["status"] = "OK"
    return stats


def dependency_graph(target: str, config: dict) -> dict:
    """Get dependency graph."""
    from agl_security_tool import ProjectScanner
    scanner = ProjectScanner(target, config=config)
    scanner.discover()
    graph = scanner.get_dependency_graph()
    graph["status"] = "OK"
    return graph


if __name__ == "__main__":
    main()
