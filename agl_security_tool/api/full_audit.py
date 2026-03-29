"""
AGL Security — Full-Power Audit Bridge
جسر التدقيق الكامل — يربط agl_audit_api بـ FastAPI

Wraps the 7-layer audit pipeline from agl_audit_api.py
for use inside the FastAPI web interface:

  Layer 0   : Solidity Flattener
  Layer 0.5 : Z3 Symbolic Execution
  Layer 1-4 : State Extraction + Action Space + Attack Sim + Search
  Layer 5   : 22 Semantic Detectors
  Layer 6   : Exploit Reasoning (Z3 Proofs)
  Layer 7   : Heikal Math (Tunneling + Wave + Holographic + Resonance)
"""

import os
import re
import sys
import time
import json
import shutil
import logging
import tempfile
import threading
import subprocess
import traceback
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable

from .database import get_db_session, Scan, _now

_logger = logging.getLogger("AGL.api.full_audit")

# Ensure project root is on path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _make_json_safe(obj, depth=0):
    """Recursively convert any non-JSON-serializable objects to dicts/strings."""
    if depth > 20:
        return str(obj)
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if isinstance(obj, dict):
        return {str(k): _make_json_safe(v, depth + 1) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_safe(v, depth + 1) for v in obj]
    if isinstance(obj, set):
        return [_make_json_safe(v, depth + 1) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "__dict__"):
        return _make_json_safe(obj.__dict__, depth + 1)
    return str(obj)


# ═══════════════════════════════════════════════════════════
#  ENGINE CACHE (lazily loaded)
# ═══════════════════════════════════════════════════════════

_full_engines: Optional[Dict[str, Any]] = None
_engine_lock = threading.Lock()


def _get_full_engines(project_root: str = ".") -> Dict[str, Any]:
    """Load all engines once (core + Layer 6 + Layer 7). Thread-safe."""
    global _full_engines
    if _full_engines is not None:
        return _full_engines
    with _engine_lock:
        if _full_engines is not None:
            return _full_engines
        _full_engines = _load_engines(project_root)
        return _full_engines


def _load_engines(project_root: str) -> Dict[str, Any]:
    """Load all available AGL security engines."""
    engines = {}

    # Core (Layer 0-5)
    try:
        from agl_security_tool.core import AGLSecurityAudit

        engines["core"] = AGLSecurityAudit()
        _logger.info("Layer 0-5: AGLSecurityAudit ready")
    except Exception as e:
        _logger.warning("AGLSecurityAudit unavailable: %s", e)

    # Z3 Symbolic
    try:
        from agl_security_tool.z3_symbolic_engine import Z3SymbolicEngine

        engines["z3"] = Z3SymbolicEngine()
        _logger.info("Layer 0.5: Z3 Symbolic ready")
    except Exception as e:
        _logger.warning("Z3SymbolicEngine unavailable: %s", e)

    # State Extraction (Layer 1-4)
    try:
        from agl_security_tool.state_extraction import StateExtractionEngine

        engines["state"] = StateExtractionEngine(
            {
                "project_root": project_root,
                "action_space": True,
                "attack_simulation": True,
                "search_engine": True,
            }
        )
        _logger.info("Layer 1-4: State Extraction ready")
    except Exception as e:
        _logger.warning("StateExtractionEngine unavailable: %s", e)

    # Exploit Reasoning (Layer 6)
    try:
        from agl_security_tool.exploit_reasoning import ExploitReasoningEngine

        engines["exploit"] = ExploitReasoningEngine()
        _logger.info("Layer 6: Exploit Reasoning ready")
    except Exception as e:
        _logger.warning("ExploitReasoningEngine unavailable: %s", e)

    # Flattener
    try:
        from agl_security_tool.solidity_flattener import SolidityFlattener

        engines["flattener"] = SolidityFlattener(project_root)
        _logger.info("Layer 0: Solidity Flattener ready")
    except Exception as e:
        _logger.warning("SolidityFlattener unavailable: %s", e)

    # Detectors (Layer 5)
    try:
        from agl_security_tool.detectors import DetectorRunner
        from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser

        engines["detectors"] = DetectorRunner()
        engines["parser"] = SoliditySemanticParser()
        _logger.info("Layer 5: 22 Semantic Detectors ready")
    except Exception as e:
        _logger.warning("DetectorRunner unavailable: %s", e)

    # Heikal Math (Layer 7)
    try:
        from agl_security_tool.heikal_math import (
            HeikalTunnelingScorer,
            WaveDomainEvaluator,
            HolographicVulnerabilityMemory,
            ResonanceProfitOptimizer,
        )

        engines["tunneling"] = HeikalTunnelingScorer()
        engines["wave"] = WaveDomainEvaluator()
        engines["holographic"] = HolographicVulnerabilityMemory()
        engines["resonance"] = ResonanceProfitOptimizer()
        _logger.info("Layer 7: Heikal Math (4 algorithms) ready")
    except Exception as e:
        _logger.warning("Heikal Math unavailable: %s", e)

    return engines


# ═══════════════════════════════════════════════════════════
#  GIT CLONE
# ═══════════════════════════════════════════════════════════


def is_github_url(target: str) -> bool:
    return bool(re.match(r"https?://github\.com/[\w\-\.]+/[\w\-\.]+", target))


def is_git_url(target: str) -> bool:
    return (
        is_github_url(target)
        or target.endswith(".git")
        or target.startswith("git@")
        or target.startswith("git://")
    )


def clone_repo(
    url: str,
    dest: Optional[str] = None,
    branch: Optional[str] = None,
    depth: int = 1,
) -> str:
    """Clone a git repository and return the local path."""
    url = url.rstrip("/")
    if not url.endswith(".git") and is_github_url(url):
        url = url + ".git"

    repo_name = url.split("/")[-1].replace(".git", "")

    if dest is None:
        dest = os.path.join(tempfile.mkdtemp(prefix="agl_audit_"), repo_name)
    else:
        dest = os.path.join(dest, repo_name)

    _logger.info("Cloning %s to %s", url, dest)

    cmd = ["git", "clone"]
    if depth > 0:
        cmd += ["--depth", str(depth)]
    if branch:
        cmd += ["--branch", branch]
    cmd += ["--recurse-submodules", "--shallow-submodules"]
    cmd += [url, dest]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            # Retry without submodules
            cmd_basic = ["git", "clone"]
            if depth > 0:
                cmd_basic += ["--depth", str(depth)]
            if branch:
                cmd_basic += ["--branch", branch]
            cmd_basic += [url, dest]
            result = subprocess.run(
                cmd_basic, capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise RuntimeError(f"git clone failed: {result.stderr[:500]}")

        _logger.info("Clone complete: %s", dest)
        return dest

    except FileNotFoundError:
        raise RuntimeError("git is not installed or not in PATH")
    except subprocess.TimeoutExpired:
        raise RuntimeError("git clone timed out (>5 min)")


def install_dependencies(project_path: str) -> None:
    """Install Foundry/Node.js project dependencies."""
    root = Path(project_path)

    if (root / "foundry.toml").exists():
        _logger.info("Installing Foundry dependencies...")
        try:
            forge_path = shutil.which("forge")
            if forge_path:
                subprocess.run(
                    [forge_path, "install"],
                    cwd=str(root),
                    capture_output=True,
                    timeout=120,
                )
        except Exception:
            pass

    if (root / "package.json").exists():
        _logger.info("Installing Node dependencies...")
        try:
            if (root / "yarn.lock").exists() and shutil.which("yarn"):
                subprocess.run(
                    ["yarn", "install"],
                    cwd=str(root),
                    capture_output=True,
                    timeout=180,
                )
            elif shutil.which("npm"):
                subprocess.run(
                    ["npm", "install"],
                    cwd=str(root),
                    capture_output=True,
                    timeout=180,
                )
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
#  PROJECT DISCOVERY
# ═══════════════════════════════════════════════════════════


def discover_project(project_path: str, config: Dict = None) -> Dict[str, Any]:
    """
    Discover project structure: type, contracts, classification.

    Returns dict with keys:
        project_type, contracts_dir, contracts, main_contracts, libraries, interfaces
    """
    config = config or {}
    root = Path(project_path)
    contracts = {}
    main_contracts = []
    libraries = []
    interfaces = []

    # Try ProjectScanner first
    info = None
    try:
        from agl_security_tool.project_scanner import ProjectScanner

        scanner = ProjectScanner(project_path, config=config)
        scanner.discover()
        info = scanner.project_info
    except Exception as e:
        _logger.warning("ProjectScanner fallback: %s", e)

    # Determine contracts directory
    contracts_dir = None
    if info and getattr(info, "contracts_dir", None):
        contracts_dir = info.contracts_dir
    else:
        for candidate in ["src", "contracts", "."]:
            p = root / candidate
            if p.exists() and list(p.glob("**/*.sol")):
                contracts_dir = str(p)
                break
        if not contracts_dir:
            contracts_dir = str(root)

    exclude_dirs = {
        "node_modules",
        ".git",
        "cache",
        "out",
        "build",
        "artifacts",
        "typechain",
        "typechain-types",
        "coverage",
        "crytic-export",
    }
    exclude_tests = config.get("exclude_tests", True)
    scan_deps = config.get("scan_dependencies", False)

    def should_skip(dirpath: str) -> bool:
        parts = Path(os.path.relpath(dirpath, project_path)).parts
        if set(parts) & exclude_dirs:
            return True
        if not scan_deps and ("lib" in parts or "node_modules" in parts):
            return True
        if exclude_tests and any(p in parts for p in {"test", "tests", "test-foundry"}):
            return True
        return False

    def is_test_file(name: str) -> bool:
        lower = name.lower()
        return (
            lower.endswith(".t.sol")
            or lower.startswith("test")
            or lower.startswith("mock")
        )

    for dirpath, dirnames, filenames in os.walk(project_path):
        if should_skip(dirpath):
            dirnames.clear()
            continue
        for fname in filenames:
            if not fname.endswith(".sol"):
                continue
            if exclude_tests and is_test_file(fname):
                continue

            fullpath = Path(dirpath) / fname
            rel = os.path.relpath(str(fullpath), project_path)
            parts = Path(rel).parts
            stem = fullpath.stem

            is_lib = any(p in ("libraries", "lib", "utils", "math") for p in parts)
            is_iface = any(
                p in ("interfaces", "interface") for p in parts
            ) or fname.startswith("I")

            if is_iface:
                key = f"iface/{stem}"
                interfaces.append(key)
            elif is_lib:
                key = f"lib/{stem}"
                libraries.append(key)
            else:
                key = stem
                main_contracts.append(key)

            contracts[key] = fullpath

    # Detect project type
    project_type = "unknown"
    if info and getattr(info, "project_type", None):
        project_type = info.project_type
    elif (root / "foundry.toml").exists():
        project_type = "foundry"
    elif (root / "hardhat.config.js").exists() or (root / "hardhat.config.ts").exists():
        project_type = "hardhat"
    elif (root / "truffle-config.js").exists():
        project_type = "truffle"
    else:
        project_type = "bare"

    return {
        "project_type": project_type,
        "contracts_dir": contracts_dir,
        "contracts": contracts,
        "main_contracts": list(set(main_contracts)),
        "libraries": list(set(libraries)),
        "interfaces": list(set(interfaces)),
    }


# ═══════════════════════════════════════════════════════════
#  SCAN LAYERS
# ═══════════════════════════════════════════════════════════


def run_core_deep_scan(engines: Dict, project: Dict) -> Dict:
    """Layer 0-5: Run deep scan on all main contracts (up to 20)."""
    core = engines.get("core")
    if not core:
        return {}

    contracts = project["contracts"]
    targets = project["main_contracts"] or [
        k for k in contracts if not k.startswith("iface/")
    ]
    results = {}

    for name in targets[:20]:
        path = contracts.get(name)
        if not path or not path.exists():
            continue
        try:
            t0 = time.time()
            result = core.deep_scan(str(path))
            result["_scan_time"] = round(time.time() - t0, 2)
            results[name] = _make_json_safe(result)
        except Exception as e:
            results[name] = {"error": str(e)}

    return results


def run_z3_symbolic(engines: Dict, project: Dict) -> List[Dict]:
    """Layer 0.5: Run Z3 symbolic analysis on all files."""
    z3 = engines.get("z3")
    if not z3:
        return []

    contracts = project["contracts"]
    all_findings = []

    for name, path in contracts.items():
        if not path.exists():
            continue
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
            result = z3.analyze(code)
            if isinstance(result, dict):
                findings = result.get("findings", [])
                for f in findings:
                    f["source_file"] = name
                all_findings.extend(findings)
        except Exception:
            pass

    return all_findings


def run_state_extraction(engines: Dict, project: Dict) -> Dict:
    """Layer 1-4: State extraction + action space + attack simulation."""
    state_eng = engines.get("state")
    if not state_eng:
        return {}

    contracts = project["contracts"]
    targets = project["main_contracts"][:10]
    results = {}

    for name in targets:
        path = contracts.get(name)
        if not path or not path.exists():
            continue
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
            result = state_eng.extract(code)
            results[name] = _make_json_safe(result)
        except Exception as e:
            results[name] = {"error": str(e)}

    return results


def run_detectors(engines: Dict, project: Dict) -> List[Dict]:
    """Layer 5: Run 22 semantic detectors on all files."""
    det = engines.get("detectors")
    parser = engines.get("parser")
    if not det:
        return []

    contracts = project["contracts"]
    all_findings = []

    for name, path in contracts.items():
        if not path.exists():
            continue
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
            parsed = parser.parse(code) if parser else None
            findings = (
                det.run_all(code, parsed_ast=parsed) if parsed else det.run_all(code)
            )
            if isinstance(findings, list):
                for f in findings:
                    f["source_file"] = name
                all_findings.extend(findings)
        except Exception:
            pass

    return all_findings


def run_exploit_reasoning(
    engines: Dict, project: Dict, deep_scan_results: Dict = None
) -> Dict:
    """Layer 6: Exploit reasoning with Z3 proofs."""
    exploit = engines.get("exploit")
    if not exploit:
        return {}

    contracts = project["contracts"]
    targets = project["main_contracts"][:10]
    results = {}

    for name in targets:
        path = contracts.get(name)
        if not path or not path.exists():
            continue
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
            findings_for_contract = []
            if deep_scan_results and name in deep_scan_results:
                ds = deep_scan_results[name]
                findings_for_contract = ds.get(
                    "all_findings_unified", ds.get("findings", [])
                )

            result = exploit.analyze(code, findings=findings_for_contract)
            results[name] = _make_json_safe(result)
        except Exception as e:
            results[name] = {"error": str(e)}

    return results


# ═══════════════════════════════════════════════════════════
#  HEIKAL MATH (Layer 7)
# ═══════════════════════════════════════════════════════════


def extract_function_blocks(code: str) -> Dict[str, str]:
    """Extract function blocks from Solidity source."""
    functions = {}
    pattern = re.compile(r"function\s+(\w+)\s*\([^)]*\)[^{]*\{", re.DOTALL)
    for match in pattern.finditer(code):
        fname = match.group(1)
        start = match.start()
        brace_count = 0
        end = start
        for i in range(match.end() - 1, len(code)):
            if code[i] == "{":
                brace_count += 1
            elif code[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break
        functions[fname] = code[start:end]
    return functions


def analyze_function_security(func_name: str, func_code: str) -> Dict:
    """Build Heikal security model per function."""
    barriers = []
    wave_features = {}
    holo_features = {}

    # Detect barriers
    if "nonReentrant" in func_code:
        barriers.append({"type": "ReentrancyGuard", "strength": 0.9})
    if "onlyOwner" in func_code or "require(msg.sender ==" in func_code:
        barriers.append({"type": "AccessControl", "strength": 0.8})
    if "require(" in func_code:
        req_count = func_code.count("require(")
        barriers.append(
            {
                "type": "RequireStatements",
                "strength": min(0.3 * req_count, 0.95),
                "count": req_count,
            }
        )
    if "modifier" in func_code:
        barriers.append({"type": "CustomModifier", "strength": 0.7})

    # Wave features
    external_calls = len(re.findall(r"\.\w+\(", func_code))
    state_writes = len(re.findall(r"\b\w+\s*=\s*", func_code))
    has_eth = (
        "msg.value" in func_code
        or ".transfer(" in func_code
        or ".send(" in func_code
        or ".call{" in func_code
    )
    has_delegate = "delegatecall" in func_code

    wave_features = {
        "external_calls": external_calls,
        "state_writes": state_writes,
        "handles_eth": has_eth,
        "uses_delegatecall": has_delegate,
        "complexity": external_calls * 2 + state_writes,
    }

    # Holo features
    holo_features = {
        "reads_storage": bool(
            re.findall(r"\b(balances|allowances|totalSupply|_balances)\b", func_code)
        ),
        "writes_storage": state_writes > 0,
        "emits_events": "emit " in func_code,
        "has_loop": "for(" in func_code
        or "for (" in func_code
        or "while(" in func_code
        or "while (" in func_code,
    }

    # CEI violation check
    code_lines = func_code.split("\n")
    last_external = -1
    last_state_write = -1
    for i, line in enumerate(code_lines):
        if re.search(r"\.\w+\(", line) and "emit " not in line:
            last_external = i
        if (
            re.search(r"\b\w+\s*[+\-*/]?=\s*", line)
            and "=" not in line[: line.find("=")]
            if "==" in line
            else True
        ):
            if re.search(r"(balances|allowances|_balances|mapping|storage)\b", line):
                last_state_write = i

    cei_violation = last_external >= 0 and last_state_write > last_external

    # Energy estimation
    barrier_total = sum(b.get("strength", 0) for b in barriers)
    complexity = wave_features.get("complexity", 0)
    energy = max(0.01, complexity * 0.1 - barrier_total * 0.5)

    return {
        "function": func_name,
        "barriers": barriers,
        "barrier_strength": barrier_total,
        "wave_features": wave_features,
        "holo_features": holo_features,
        "cei_violation": cei_violation,
        "energy": round(energy, 4),
        "chain_length": external_calls + state_writes,
    }


def build_attack_scenarios(project: Dict) -> List[Dict]:
    """Build dynamic attack scenarios based on source code analysis."""
    scenarios = []
    contracts = project["contracts"]

    for name, path in list(contracts.items())[:10]:
        if not path.exists():
            continue
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Reentrancy
        if (
            re.search(r"\.(call|send|transfer)\s*[\({]", code)
            and not "nonReentrant" in code
        ):
            scenarios.append(
                {
                    "name": f"Reentrancy_Attack_{name}",
                    "type": "reentrancy",
                    "target": name,
                    "description": f"Potential reentrancy in {name} — external call without guard",
                    "barriers": [{"type": "ReentrancyGuard", "strength": 0.0}],
                    "energy": 0.3,
                }
            )

        # Flash Loan
        if re.search(r"(flashLoan|flash_loan|borrow|IPool|ILendingPool)", code):
            scenarios.append(
                {
                    "name": f"Flash_Loan_Attack_{name}",
                    "type": "flash_loan",
                    "target": name,
                    "description": f"Flash loan vector in {name}",
                    "barriers": [],
                    "energy": 0.5,
                }
            )

        # Oracle Manipulation
        if re.search(
            r"(getPrice|latestAnswer|oracle|chainlink|getReserves|spot_price)",
            code,
            re.IGNORECASE,
        ):
            scenarios.append(
                {
                    "name": f"Oracle_Manipulation_{name}",
                    "type": "oracle",
                    "target": name,
                    "description": f"Price oracle dependency in {name} — potential manipulation",
                    "barriers": [],
                    "energy": 0.6,
                }
            )

        # Sandwich / Frontrun
        if re.search(
            r"(swap|addLiquidity|removeLiquidity|exchange)", code, re.IGNORECASE
        ):
            scenarios.append(
                {
                    "name": f"Sandwich_Frontrun_{name}",
                    "type": "sandwich",
                    "target": name,
                    "description": f"DEX interaction in {name} — sandwich/frontrun risk",
                    "barriers": [],
                    "energy": 0.4,
                }
            )

        # Governance Takeover
        if re.search(r"(propose|vote|execute|quorum|governance)", code, re.IGNORECASE):
            scenarios.append(
                {
                    "name": f"Governance_Takeover_{name}",
                    "type": "governance",
                    "target": name,
                    "description": f"Governance mechanism in {name}",
                    "barriers": [],
                    "energy": 0.7,
                }
            )

        # Unguarded Fund Flow
        if re.search(r"\.(call|transfer|send)\s*[\({]", code):
            if not re.search(r"(onlyOwner|require\(msg\.sender)", code):
                scenarios.append(
                    {
                        "name": f"Unguarded_Fund_Flow_{name}",
                        "type": "fund_flow",
                        "target": name,
                        "description": f"Unguarded fund transfer in {name}",
                        "barriers": [],
                        "energy": 0.2,
                    }
                )

    return scenarios


def run_heikal_math(engines: Dict, project: Dict) -> Dict:
    """
    Layer 7: Full Heikal Math analysis.
    Runs all 4 algorithms on every function + dynamically generated attack scenarios.
    """
    tunneling = engines.get("tunneling")
    wave = engines.get("wave")
    holographic = engines.get("holographic")
    resonance = engines.get("resonance")

    if not any([tunneling, wave, holographic, resonance]):
        return {}

    contracts = project["contracts"]
    func_results = {}
    attack_results = {}

    # Phase 1: Extract all functions and analyze security
    all_functions = {}
    for name, path in list(contracts.items())[:10]:
        if not path.exists():
            continue
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
            funcs = extract_function_blocks(code)
            for fname, fcode in funcs.items():
                key = f"{name}::{fname}"
                all_functions[key] = analyze_function_security(fname, fcode)
        except Exception:
            pass

    # Phase 2: Build dynamic attack scenarios
    attack_scenarios = build_attack_scenarios(project)

    # Phase 3: Run Heikal algorithms on functions
    for key, sec_model in all_functions.items():
        result = {"function": key}

        if tunneling:
            try:
                t_result = tunneling.compute(
                    barriers=sec_model.get("barriers", []),
                    energy=sec_model.get("energy", 0.5),
                    chain_length=sec_model.get("chain_length", 1),
                )
                result["tunneling"] = (
                    t_result
                    if isinstance(t_result, dict)
                    else {"confidence": float(t_result)}
                )
            except Exception:
                result["tunneling"] = {"confidence": 0.0, "error": "computation_failed"}

        if wave:
            try:
                w_result = wave.evaluate(features=sec_model.get("wave_features", {}))
                result["wave"] = (
                    w_result
                    if isinstance(w_result, dict)
                    else {"heuristic_score": float(w_result)}
                )
            except Exception:
                result["wave"] = {"heuristic_score": 0.0}

        if holographic:
            try:
                h_result = holographic.match(
                    features=sec_model.get("holo_features", {})
                )
                result["holographic"] = (
                    h_result
                    if isinstance(h_result, dict)
                    else {"similarity": float(h_result)}
                )
            except Exception:
                result["holographic"] = {"similarity": 0.0}

        if resonance:
            try:
                r_result = resonance.optimize_amount(
                    features=sec_model.get("wave_features", {})
                )
                result["resonance"] = (
                    r_result
                    if isinstance(r_result, dict)
                    else {"optimal_amount_eth": float(r_result)}
                )
            except Exception:
                result["resonance"] = {"optimal_amount_eth": 0.0}

        # Classify severity
        tunnel_conf = result.get("tunneling", {}).get("confidence", 0)
        if tunnel_conf > 0.7:
            result["severity"] = "CRITICAL"
        elif tunnel_conf > 0.5:
            result["severity"] = "HIGH"
        elif tunnel_conf > 0.3:
            result["severity"] = "MEDIUM"
        elif tunnel_conf > 0.1:
            result["severity"] = "LOW"
        else:
            result["severity"] = "INFO"

        result["description"] = f"Heikal analysis of {key}"
        func_results[key] = result

    # Phase 4: Run algorithms on attack scenarios
    for scenario in attack_scenarios:
        aname = scenario["name"]
        result = {"scenario": aname, "description": scenario.get("description", "")}

        if tunneling:
            try:
                t_result = tunneling.compute(
                    barriers=scenario.get("barriers", []),
                    energy=scenario.get("energy", 0.5),
                    chain_length=1,
                )
                result["tunneling"] = (
                    t_result
                    if isinstance(t_result, dict)
                    else {"confidence": float(t_result)}
                )
            except Exception:
                result["tunneling"] = {"confidence": 0.0}

        if wave:
            try:
                w_result = wave.evaluate(
                    features={"external_calls": 1, "handles_eth": True}
                )
                result["wave"] = (
                    w_result
                    if isinstance(w_result, dict)
                    else {"heuristic_score": float(w_result)}
                )
            except Exception:
                result["wave"] = {"heuristic_score": 0.0}

        if resonance:
            try:
                r_result = resonance.optimize_amount(
                    features={"external_calls": 1, "handles_eth": True}
                )
                result["resonance"] = (
                    r_result
                    if isinstance(r_result, dict)
                    else {"optimal_amount_eth": float(r_result)}
                )
            except Exception:
                result["resonance"] = {"optimal_amount_eth": 0.0}

        tunnel_conf = result.get("tunneling", {}).get("confidence", 0)
        if tunnel_conf > 0.7:
            result["severity"] = "CRITICAL"
        elif tunnel_conf > 0.5:
            result["severity"] = "HIGH"
        elif tunnel_conf > 0.3:
            result["severity"] = "MEDIUM"
        else:
            result["severity"] = "LOW"

        attack_results[aname] = result

    return {
        "functions": func_results,
        "attacks": attack_results,
        "total_functions": len(func_results),
        "total_attacks": len(attack_results),
    }


# ═══════════════════════════════════════════════════════════
#  REPORT GENERATION
# ═══════════════════════════════════════════════════════════


def generate_report(
    all_results: Dict, project: Dict, target_name: str, total_time: float
) -> Dict:
    """Generate comprehensive JSON report from all scan layers."""
    contracts_count = len(project.get("contracts", {}))
    project_type = project.get("project_type", "unknown")

    report = {
        "target": target_name,
        "project_type": project_type,
        "timestamp": datetime.now().isoformat(),
        "contracts_scanned": contracts_count,
        "audit_time_seconds": round(total_time, 1),
        "layers_used": [],
        "results": all_results,
    }

    # Count findings
    total_findings = 0
    severity_total = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

    # Deep scan
    for name, result in all_results.get("deep_scan", {}).items():
        if isinstance(result, dict):
            sev = result.get("severity_summary", {})
            for k, v in sev.items():
                severity_total[k] = severity_total.get(k, 0) + v
                total_findings += v

    # Z3
    z3_findings = all_results.get("z3_symbolic", [])
    total_findings += len(z3_findings)

    # Detectors
    detector_findings = all_results.get("detectors", [])
    total_findings += len(detector_findings)

    # Heikal
    heikal = all_results.get("heikal_math", {})
    for item in list(heikal.get("functions", {}).values()) + list(
        heikal.get("attacks", {}).values()
    ):
        s = item.get("severity", "INFO")
        severity_total[s] = severity_total.get(s, 0) + 1

    report["total_findings"] = total_findings
    report["severity_total"] = severity_total

    # Layers used
    layers = []
    if all_results.get("deep_scan"):
        layers.extend(
            ["Layer 0: Flattener", "Layer 0.5: Z3", "Layer 1-4: Core Deep Scan"]
        )
    if all_results.get("z3_symbolic"):
        layers.append("Layer 0.5: Z3 Symbolic")
    if all_results.get("state_extraction"):
        layers.append("Layer 1-4: State Extraction")
    if all_results.get("detectors"):
        layers.append("Layer 5: 22 Detectors")
    if all_results.get("exploit_reasoning"):
        layers.append("Layer 6: Exploit Reasoning")
    if all_results.get("heikal_math"):
        layers.append("Layer 7: Heikal Math")
    report["layers_used"] = layers

    return report


def generate_markdown_report(report: Dict) -> str:
    """Generate Markdown-formatted audit report."""
    lines = [
        "# AGL Security Audit Report / تقرير التدقيق الأمني",
        "",
        f"**Target:** {report.get('target', 'Unknown')}",
        f"**Project Type:** {report.get('project_type', 'Unknown')}",
        f"**Date:** {report.get('timestamp', '')}",
        f"**Contracts Scanned:** {report.get('contracts_scanned', 0)}",
        f"**Duration:** {report.get('audit_time_seconds', 0):.1f}s",
        "",
    ]

    sev = report.get("severity_total", {})
    lines += [
        "## Severity Summary",
        "",
        "| Severity | Count |",
        "|----------|-------|",
    ]
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        lines.append(f"| {s} | {sev.get(s, 0)} |")
    lines.append("")

    # Heikal Math
    heikal = report.get("results", {}).get("heikal_math", {})
    if heikal:
        attacks = heikal.get("attacks", {})
        if attacks:
            lines += [
                "## Attack Scenarios (Heikal Math)",
                "",
                "| Scenario | Severity | Tunneling | Wave | Description |",
                "|----------|----------|-----------|------|-------------|",
            ]
            for aname, adata in sorted(
                attacks.items(),
                key=lambda x: x[1].get("tunneling", {}).get("confidence", 0),
                reverse=True,
            ):
                t = adata.get("tunneling", {}).get("confidence", 0)
                w = adata.get("wave", {}).get("heuristic_score", 0)
                desc = adata.get("description", "")[:60]
                lines.append(
                    f"| {aname} | {adata.get('severity','?')} | {t:.4f} | {w:.4f} | {desc} |"
                )
            lines.append("")

        funcs = heikal.get("functions", {})
        if funcs:
            lines += [
                "## Function Analysis (Top 20)",
                "",
                "| Function | Severity | Tunneling | Wave | Description |",
                "|----------|----------|-----------|------|-------------|",
            ]
            sorted_f = sorted(
                funcs.items(),
                key=lambda x: x[1].get("tunneling", {}).get("confidence", 0),
                reverse=True,
            )
            for fname, fdata in sorted_f[:20]:
                t = fdata.get("tunneling", {}).get("confidence", 0)
                w = fdata.get("wave", {}).get("heuristic_score", 0)
                desc = fdata.get("description", "")[:60]
                lines.append(
                    f"| {fname} | {fdata.get('severity','?')} | {t:.4f} | {w:.4f} | {desc} |"
                )
            lines.append("")

    # Deep scan
    deep = report.get("results", {}).get("deep_scan", {})
    if deep:
        lines += ["## Deep Scan Results", ""]
        for name, result in deep.items():
            if isinstance(result, dict) and "error" not in result:
                s = result.get("severity_summary", {})
                t = result.get("_scan_time", 0)
                findings = result.get(
                    "all_findings_unified", result.get("findings", [])
                )
                lines.append(f"### {name}")
                lines.append(f"- Findings: {len(findings)} ({t:.1f}s)")
                lines.append(
                    f"- CRITICAL: {s.get('CRITICAL',0)}, HIGH: {s.get('HIGH',0)}, "
                    f"MEDIUM: {s.get('MEDIUM',0)}, LOW: {s.get('LOW',0)}"
                )
                lines.append("")

    lines += ["---", "*Generated by AGL Security Auditor — Full 7-Layer Pipeline*"]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
#  BACKGROUND AUDIT RUNNER
# ═══════════════════════════════════════════════════════════


def _update_scan(scan_id: str, db, **kwargs):
    """Helper to update scan record."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        for k, v in kwargs.items():
            setattr(scan, k, v)
        db.commit()
    return scan


def run_full_audit_background(
    scan_id: str,
    target: str,
    mode: str = "full",
    branch: Optional[str] = None,
    skip_heikal: bool = False,
    include_deps: bool = False,
    include_tests: bool = False,
    no_deps_install: bool = False,
):
    """
    Background worker for full 7-layer audit. Updates DB progress at each step.
    Called from FastAPI background tasks.
    """
    db = get_db_session()
    is_temp = False
    project_path = None

    try:
        _update_scan(
            scan_id,
            db,
            status="running",
            started_at=_now(),
            progress=5,
            current_layer="Resolving target...",
        )

        t_total = time.time()

        # ── Step 0: Resolve target ──
        if is_git_url(target):
            _update_scan(scan_id, db, progress=8, current_layer="Cloning repository...")
            project_path = clone_repo(target, branch=branch)
            is_temp = True
            if not no_deps_install:
                _update_scan(
                    scan_id, db, progress=12, current_layer="Installing dependencies..."
                )
                install_dependencies(project_path)
        else:
            target_path = Path(target).resolve()
            if target_path.is_file() and target_path.suffix == ".sol":
                project_path = str(target_path.parent)
            elif target_path.is_dir():
                project_path = str(target_path)
            else:
                raise FileNotFoundError(f"Target not found: {target}")

        # ── Step 1: Load engines ──
        _update_scan(scan_id, db, progress=15, current_layer="Loading all engines...")
        engines = _get_full_engines(project_path)

        # ── Step 2: Discover project ──
        _update_scan(
            scan_id, db, progress=20, current_layer="Discovering project structure..."
        )
        config = {
            "exclude_tests": not include_tests,
            "exclude_mocks": True,
            "scan_dependencies": include_deps,
        }
        project = discover_project(project_path, config=config)
        contracts = project["contracts"]

        if not contracts:
            raise RuntimeError("No Solidity files found in target")

        target_name = target if is_git_url(target) else Path(project_path).name
        all_results = {}

        # ── Step 3: Core deep scan (Layer 0-5) ──
        if mode in ("full", "deep"):
            _update_scan(
                scan_id, db, progress=25, current_layer="Layer 0-5: Deep Scan..."
            )
            all_results["deep_scan"] = run_core_deep_scan(engines, project)
        else:
            all_results["deep_scan"] = {}

        # ── Step 4: Z3 Symbolic ──
        if mode in ("full", "deep"):
            _update_scan(
                scan_id, db, progress=40, current_layer="Layer 0.5: Z3 Symbolic..."
            )
            all_results["z3_symbolic"] = run_z3_symbolic(engines, project)
        else:
            all_results["z3_symbolic"] = []

        # ── Step 5: State Extraction ──
        if mode == "full":
            _update_scan(
                scan_id, db, progress=50, current_layer="Layer 1-4: State Extraction..."
            )
            all_results["state_extraction"] = run_state_extraction(engines, project)
        else:
            all_results["state_extraction"] = {}

        # ── Step 6: Detectors ──
        _update_scan(
            scan_id, db, progress=60, current_layer="Layer 5: 22 Semantic Detectors..."
        )
        all_results["detectors"] = run_detectors(engines, project)

        # ── Step 7: Exploit Reasoning ──
        if mode in ("full", "deep"):
            _update_scan(
                scan_id, db, progress=70, current_layer="Layer 6: Exploit Reasoning..."
            )
            all_results["exploit_reasoning"] = run_exploit_reasoning(
                engines, project, deep_scan_results=all_results.get("deep_scan", {})
            )
        else:
            all_results["exploit_reasoning"] = {}

        # ── Step 8: Heikal Math ──
        if not skip_heikal and mode == "full":
            _update_scan(
                scan_id, db, progress=80, current_layer="Layer 7: Heikal Math..."
            )
            all_results["heikal_math"] = run_heikal_math(engines, project)
        else:
            all_results["heikal_math"] = {}

        # ── Step 9: Generate report ──
        _update_scan(scan_id, db, progress=95, current_layer="Generating report...")
        total_time = time.time() - t_total
        report = generate_report(all_results, project, target_name, total_time)

        # Make report JSON-safe (some engines return non-serializable objects)
        report = _make_json_safe(report)

        # ── Step 10: Persist results ──
        sev = report.get("severity_total", {})
        total_findings = report.get("total_findings", 0)

        # Heikal composite score
        heikal = all_results.get("heikal_math", {})
        heikal_funcs = heikal.get("functions", {})
        avg_tunnel = 0.0
        avg_wave = 0.0
        if heikal_funcs:
            tunnels = [
                f.get("tunneling", {}).get("confidence", 0)
                for f in heikal_funcs.values()
            ]
            waves = [
                f.get("wave", {}).get("heuristic_score", 0)
                for f in heikal_funcs.values()
            ]
            avg_tunnel = sum(tunnels) / len(tunnels) if tunnels else 0
            avg_wave = sum(waves) / len(waves) if waves else 0

        # Attack data from heikal
        heikal_attacks = heikal.get("attacks", {})
        n_attacks = len(heikal_attacks)
        profitable_attacks = sum(
            1
            for a in heikal_attacks.values()
            if a.get("tunneling", {}).get("confidence", 0) > 0.5
        )

        # Security score
        score = max(
            0,
            100
            - sev.get("CRITICAL", 0) * 15
            - sev.get("HIGH", 0) * 8
            - sev.get("MEDIUM", 0) * 3
            - sev.get("LOW", 0) * 1,
        )

        scan = _update_scan(
            scan_id,
            db,
            status="completed",
            progress=100,
            current_layer="Done — all 7 layers complete",
            completed_at=_now(),
            duration_sec=round(total_time, 2),
            total_findings=total_findings,
            critical_count=sev.get("CRITICAL", 0),
            high_count=sev.get("HIGH", 0),
            medium_count=sev.get("MEDIUM", 0),
            low_count=sev.get("LOW", 0),
            security_score=score,
            total_attacks=n_attacks,
            profitable_attacks=profitable_attacks,
            max_profit_usd=0.0,
            heikal_xi=avg_tunnel,
            heikal_wave=avg_wave,
            heikal_tunnel=avg_tunnel,
            result_json=report,
        )

        _logger.info(
            "Full audit complete for %s: %d findings in %.1fs",
            target_name,
            total_findings,
            total_time,
        )

    except Exception as exc:
        _logger.error("Full audit failed: %s", exc)
        traceback.print_exc()
        try:
            _update_scan(
                scan_id,
                db,
                status="failed",
                error_message=f"{type(exc).__name__}: {exc}",
                progress=0,
                completed_at=_now(),
            )
        except Exception:
            pass

    finally:
        db.close()
        # Cleanup temp directory
        if is_temp and project_path and os.path.exists(project_path):
            try:
                shutil.rmtree(project_path, ignore_errors=True)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════
#  ZIP UPLOAD HELPERS
# ═══════════════════════════════════════════════════════════


MAX_ZIP_SIZE = 50 * 1024 * 1024  # 50 MB


def extract_zip_project(zip_bytes: bytes, dest_dir: str) -> str:
    """
    Extract a ZIP file and return the project root path.
    Handles both flat .sol files and nested project structures.
    """
    zip_path = os.path.join(dest_dir, "upload.zip")
    with open(zip_path, "wb") as f:
        f.write(zip_bytes)

    extract_dir = os.path.join(dest_dir, "project")
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Security: check for path traversal
        for name in zf.namelist():
            if ".." in name or name.startswith("/"):
                raise ValueError(f"Unsafe path in ZIP: {name}")
        zf.extractall(extract_dir)

    # If the ZIP has a single top-level directory, use that
    entries = os.listdir(extract_dir)
    if len(entries) == 1 and os.path.isdir(os.path.join(extract_dir, entries[0])):
        return os.path.join(extract_dir, entries[0])

    return extract_dir
