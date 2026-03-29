"""
╔══════════════════════════════════════════════════════════════════════╗
║       AGL Tool Backends — Native Subprocess Wrappers                 ║
║       Self-contained Slither / Mythril / Semgrep / Solc              ║
╚══════════════════════════════════════════════════════════════════════╝

Decoupled from AGL_NextGen — no external sys.path dependencies.
Each tool wrapper:
  1. Checks if tool is installed (shutil.which)
  2. Runs subprocess with proper timeout + error capture
  3. Parses JSON output into unified Finding format
  4. Reports tool failures EXPLICITLY (never silent)

Usage:
    from agl_security_tool.tool_backends import SlitherRunner, MythrilRunner, SemgrepRunner
    sr = SlitherRunner()
    findings = sr.analyze("contract.sol")
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

_logger = logging.getLogger("AGL.tool_backends")


# ═══════════════════════════════════════════════════════════════
#  Solc Health Check — cached, runs once
# ═══════════════════════════════════════════════════════════════

_solc_check_done = False
_solc_available = False
_solc_error = ""


def _check_solc_available(timeout: int = 8) -> bool:
    """
    Test if `solc --version` responds within *timeout* seconds.
    On this system solc is a solc-select wrapper that hangs when no
    version is installed and the network is blocked.  A fast probe
    prevents Slither / Mythril from wasting minutes per file.
    Result is cached so it runs at most once per process.
    """
    global _solc_check_done, _solc_available, _solc_error

    if _solc_check_done:
        return _solc_available

    _solc_check_done = True

    solc_path = shutil.which("solc")
    if solc_path is None:
        _solc_error = "solc not found in PATH"
        _solc_available = False
        _logger.warning("solc not found in PATH — Slither/Mythril will be disabled")
        return False

    try:
        proc = subprocess.run(
            ["solc", "--version"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode == 0 and proc.stdout:
            _solc_available = True
            _logger.info("solc available: %s", proc.stdout.strip().split("\\n")[-1])
        else:
            _solc_error = f"solc returned code {proc.returncode}: {(proc.stderr or '')[:200]}"
            _solc_available = False
            _logger.warning("solc check failed: %s", _solc_error)
    except subprocess.TimeoutExpired:
        _solc_error = (
            f"solc --version timed out after {timeout}s — "
            "likely solc-select has no installed version and network is blocked. "
            "Fix: download a solc binary manually and place it in PATH, "
            "or run `solc-select install <version>` when network is available."
        )
        _solc_available = False
        _logger.warning("solc hangs (timeout %ds) — Slither/Mythril disabled", timeout)
    except Exception as e:
        _solc_error = f"solc probe error: {e}"
        _solc_available = False
        _logger.warning("solc probe error: %s", e)

    return _solc_available


# ═══════════════════════════════════════════════════════════════
#  Unified Finding Format
# ═══════════════════════════════════════════════════════════════


@dataclass
class ToolFinding:
    """Standardized finding from any external tool."""

    id: str = ""
    title: str = ""
    severity: str = "MEDIUM"
    category: str = "other"
    description: str = ""
    file_path: str = ""
    line: int = 0
    line_end: int = 0
    code_snippet: str = ""
    source_tool: str = ""
    confidence: float = 0.5
    detector_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "file_path": self.file_path,
            "line": self.line,
            "line_end": self.line_end,
            "code_snippet": self.code_snippet,
            "source": self.source_tool,
            "confidence": self.confidence,
            "detector": self.detector_name,
        }


@dataclass
class ToolResult:
    """Result from a tool run — NEVER silent, always explicit."""

    tool_name: str
    available: bool = False
    success: bool = False
    findings: List[ToolFinding] = field(default_factory=list)
    error: str = ""
    stderr: str = ""
    duration_ms: int = 0
    timed_out: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool_name,
            "available": self.available,
            "success": self.success,
            "findings_count": len(self.findings),
            "error": self.error,
            "timed_out": self.timed_out,
            "duration_ms": self.duration_ms,
        }


# ═══════════════════════════════════════════════════════════════
#  Category Mapping
# ═══════════════════════════════════════════════════════════════


def _classify_category(name: str) -> str:
    """Classify a detector/rule name into a standard category."""
    n = name.lower()
    if "reentrancy" in n or "reentran" in n:
        return "reentrancy"
    if "access" in n or "owner" in n or "auth" in n:
        return "access_control"
    if "overflow" in n or "underflow" in n or "arithmetic" in n:
        return "arithmetic"
    if "delegatecall" in n:
        return "delegatecall"
    if "timestamp" in n or "block.timestamp" in n:
        return "timestamp"
    if "oracle" in n or "price" in n:
        return "oracle_manipulation"
    if "flash" in n:
        return "flash_loan"
    if "unchecked" in n or "low-level" in n:
        return "unchecked_call"
    if "self-destruct" in n or "selfdestruct" in n or "suicide" in n:
        return "selfdestruct"
    if "front" in n or "sandwich" in n or "mev" in n:
        return "frontrunning"
    return "logic"


# ═══════════════════════════════════════════════════════════════
#  Import Resolution Helper — auto-generates remappings for Slither/Mythril
# ═══════════════════════════════════════════════════════════════


def _detect_project_root(file_path: str) -> Optional[str]:
    """Walk up from file_path to find the project root (foundry.toml / package.json / .git)."""
    p = Path(file_path).resolve().parent
    for _ in range(10):
        if any(
            (p / marker).exists()
            for marker in (
                "foundry.toml",
                "package.json",
                "hardhat.config.js",
                "hardhat.config.ts",
                ".git",
            )
        ):
            return str(p)
        parent = p.parent
        if parent == p:
            break
        p = parent
    return None


def _build_remappings(project_root: str) -> List[str]:
    """Build Solidity import remappings from project structure."""
    root = Path(project_root)
    remappings = []
    seen = set()

    # 1. Read existing remappings.txt
    remap_file = root / "remappings.txt"
    if remap_file.exists():
        try:
            for line in remap_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    if line not in seen:
                        remappings.append(line)
                        seen.add(line)
        except Exception:
            pass

    # 2. Parse foundry.toml remappings
    foundry_toml = root / "foundry.toml"
    if foundry_toml.exists():
        try:
            content = foundry_toml.read_text(encoding="utf-8")
            in_remappings = False
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("remappings"):
                    in_remappings = True
                    continue
                if in_remappings:
                    if stripped == "]":
                        break
                    m = re.match(r'["\']([^"\']+)["\']', stripped)
                    if m:
                        remap = m.group(1)
                        if remap not in seen:
                            remappings.append(remap)
                            seen.add(remap)
        except Exception:
            pass

    # 3. Auto-detect from lib/ (Foundry deps)
    lib_dir = root / "lib"
    if lib_dir.is_dir():
        try:
            for entry in sorted(os.listdir(str(lib_dir))):
                full = lib_dir / entry
                if not full.is_dir():
                    continue
                src = full / "src"
                contracts = full / "contracts"
                if src.is_dir():
                    remap = f"{entry}/={str(src)}/"
                    if remap not in seen:
                        remappings.append(remap)
                        seen.add(remap)
                elif contracts.is_dir():
                    remap = f"@{entry}/={str(contracts)}/"
                    if remap not in seen:
                        remappings.append(remap)
                        seen.add(remap)
        except Exception:
            pass

    # 4. Auto-detect from node_modules/
    node_modules = root / "node_modules"
    if node_modules.is_dir():
        common_ns = ["@openzeppelin", "@chainlink", "@uniswap", "@aave"]
        for ns in common_ns:
            ns_dir = node_modules / ns
            if ns_dir.is_dir():
                remap = f"{ns}/={str(ns_dir)}/"
                if remap not in seen:
                    remappings.append(remap)
                    seen.add(remap)

    return remappings


def _ensure_remappings_file(project_root: str) -> Optional[str]:
    """Ensure remappings.txt exists in project root. Returns path if created/exists."""
    root = Path(project_root)
    remap_path = root / "remappings.txt"

    remappings = _build_remappings(project_root)
    if not remappings:
        return None

    # Only write if file doesn't exist or is empty
    if not remap_path.exists() or remap_path.stat().st_size == 0:
        try:
            remap_path.write_text("\n".join(remappings) + "\n", encoding="utf-8")
            _logger.info(
                "Auto-generated remappings.txt with %d entries", len(remappings)
            )
        except Exception as e:
            _logger.debug("Could not write remappings.txt: %s", e)

    return str(remap_path) if remap_path.exists() else None


# ═══════════════════════════════════════════════════════════════
#  Slither Runner
# ═══════════════════════════════════════════════════════════════


class SlitherRunner:
    """
    Native Slither subprocess wrapper.
    No dependency on AGL_NextGen — calls slither CLI directly.
    """

    SEVERITY_MAP = {
        "High": "HIGH",
        "Medium": "MEDIUM",
        "Low": "LOW",
        "Informational": "INFO",
        "Optimization": "INFO",
    }

    def __init__(self, timeout: int = 120, detectors: Optional[List[str]] = None):
        self.timeout = timeout
        self.detectors = detectors
        self.path = shutil.which("slither")
        self.available = self.path is not None
        self._solc_error = ""

        # Slither requires a working solc — fast probe (cached, runs once)
        if self.available and not _check_solc_available():
            self.available = False
            self._solc_error = _solc_error
            _logger.warning(
                "Slither disabled — solc broken: %s", self._solc_error
            )

    def analyze(self, file_path: str) -> ToolResult:
        """Run Slither on a Solidity file. Returns explicit result — never silent."""
        import time

        result = ToolResult(tool_name="slither", available=self.available)

        if not self.available:
            result.error = self._solc_error or "slither not installed (pip install slither-analyzer)"
            _logger.warning("Slither not available: %s", result.error)
            return result

        if not os.path.exists(file_path):
            result.error = f"File not found: {file_path}"
            return result

        # Auto-resolve imports: detect project root and generate remappings
        project_root = _detect_project_root(file_path)
        solc_remaps = []
        cwd = None
        if project_root:
            _ensure_remappings_file(project_root)
            remappings = _build_remappings(project_root)
            if remappings:
                solc_remaps = remappings
            cwd = project_root

        cmd = ["slither", os.path.abspath(file_path), "--json", "-"]
        if self.detectors:
            cmd.extend(["--detect", ",".join(self.detectors)])
        # Pass remappings to Slither so it can resolve imports
        if solc_remaps:
            cmd.extend(["--solc-remaps", ";".join(solc_remaps)])

        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd,
            )
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            result.stderr = proc.stderr[:2000] if proc.stderr else ""

            if proc.stdout:
                try:
                    data = json.loads(proc.stdout)
                    for det in data.get("results", {}).get("detectors", []):
                        finding = self._parse_finding(det, file_path)
                        if finding:
                            result.findings.append(finding)
                    result.success = True
                except json.JSONDecodeError as e:
                    result.error = f"JSON parse error: {e}"
            else:
                result.success = True  # No output = no findings

        except subprocess.TimeoutExpired:
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            result.timed_out = True
            result.error = f"Slither timed out after {self.timeout}s"
            _logger.warning(result.error)
        except FileNotFoundError:
            result.error = "slither binary not found in PATH"
            result.available = False
        except Exception as e:
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            result.error = f"Slither error: {e}"
            _logger.error(result.error)

        _logger.info(
            "Slither: %d findings in %dms (success=%s)",
            len(result.findings),
            result.duration_ms,
            result.success,
        )
        return result

    def _parse_finding(self, det: Dict, file_path: str) -> Optional[ToolFinding]:
        """Parse a single Slither detector result."""
        try:
            check = det.get("check", "unknown")
            severity_raw = det.get("impact", "Low")
            confidence_raw = det.get("confidence", "Medium")

            # Extract location
            elements = det.get("elements", [])
            line = 0
            line_end = 0
            snippet = ""
            if elements:
                src = elements[0].get("source_mapping", {})
                lines = src.get("lines", [])
                if lines:
                    line = min(lines)
                    line_end = max(lines)
                snippet = src.get("content", "")[:500]

            return ToolFinding(
                id=f"SLITHER-{check.upper()}",
                title=det.get("description", check)[:200],
                severity=self.SEVERITY_MAP.get(severity_raw, "MEDIUM"),
                category=_classify_category(check),
                description=det.get("description", ""),
                file_path=file_path,
                line=line,
                line_end=line_end,
                code_snippet=snippet,
                source_tool="slither",
                confidence=(
                    0.85
                    if confidence_raw == "High"
                    else 0.65 if confidence_raw == "Medium" else 0.45
                ),
                detector_name=check,
            )
        except Exception as e:
            _logger.debug("Slither parse error: %s", e)
            return None


# ═══════════════════════════════════════════════════════════════
#  Mythril Runner
# ═══════════════════════════════════════════════════════════════


class MythrilRunner:
    """
    Native Mythril subprocess wrapper.
    Calls `myth analyze` CLI directly.
    """

    SEVERITY_MAP = {
        "High": "HIGH",
        "Medium": "MEDIUM",
        "Low": "LOW",
    }

    SWC_TO_CATEGORY = {
        "SWC-101": "arithmetic",  # Integer Overflow
        "SWC-104": "unchecked_call",  # Unchecked Call Return
        "SWC-106": "selfdestruct",  # Unprotected Selfdestruct
        "SWC-107": "reentrancy",  # Reentrancy
        "SWC-110": "logic",  # Assert Violation
        "SWC-112": "delegatecall",  # Delegatecall to untrusted
        "SWC-113": "logic",  # DoS with failed call
        "SWC-114": "timestamp",  # Timestamp dependency
        "SWC-115": "access_control",  # Authorization via tx.origin
        "SWC-116": "timestamp",  # Block values as proxy
        "SWC-120": "logic",  # Weak sources of randomness
    }

    def __init__(self, timeout: int = 300, max_depth: int = 22):
        self.timeout = timeout
        self.max_depth = max_depth
        self.path = shutil.which("myth")
        self.available = self.path is not None
        self._solc_error = ""

        # Mythril requires a working solc — fast probe (cached, runs once)
        if self.available and not _check_solc_available():
            self.available = False
            self._solc_error = _solc_error
            _logger.warning(
                "Mythril disabled — solc broken: %s", self._solc_error
            )

    def analyze(self, file_path: str) -> ToolResult:
        """Run Mythril on a Solidity file. Returns explicit result."""
        import time

        result = ToolResult(tool_name="mythril", available=self.available)

        if not self.available:
            result.error = self._solc_error or "mythril not installed (pip install mythril)"
            _logger.warning("Mythril not available: %s", result.error)
            return result

        if not os.path.exists(file_path):
            result.error = f"File not found: {file_path}"
            return result

        # Auto-resolve imports
        project_root = _detect_project_root(file_path)
        cwd = None
        solc_remaps = []
        if project_root:
            _ensure_remappings_file(project_root)
            solc_remaps = _build_remappings(project_root)
            cwd = project_root

        cmd = [
            "myth",
            "analyze",
            os.path.abspath(file_path),
            "--execution-timeout",
            str(self.timeout),
            "--max-depth",
            str(self.max_depth),
            "-o",
            "json",
        ]
        # Pass remappings to Mythril via --solc-args
        if solc_remaps:
            remap_str = " ".join(f"--allow-paths {project_root}" for _ in [1])
            cmd.extend(["--solc-args", remap_str])

        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 60,
            )
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            result.stderr = proc.stderr[:2000] if proc.stderr else ""

            if proc.stdout:
                try:
                    data = json.loads(proc.stdout)
                    for issue in data.get("issues", []):
                        finding = self._parse_finding(issue, file_path)
                        if finding:
                            result.findings.append(finding)
                    result.success = True
                except json.JSONDecodeError as e:
                    result.error = f"JSON parse error: {e}"
            else:
                result.success = True

        except subprocess.TimeoutExpired:
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            result.timed_out = True
            result.error = f"Mythril timed out after {self.timeout + 60}s"
            _logger.warning(result.error)
        except FileNotFoundError:
            result.error = "myth binary not found in PATH"
            result.available = False
        except Exception as e:
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            result.error = f"Mythril error: {e}"
            _logger.error(result.error)

        _logger.info(
            "Mythril: %d findings in %dms (success=%s)",
            len(result.findings),
            result.duration_ms,
            result.success,
        )
        return result

    def _parse_finding(self, issue: Dict, file_path: str) -> Optional[ToolFinding]:
        """Parse a single Mythril issue."""
        try:
            swc = issue.get("swc-id", "")
            swc_key = f"SWC-{swc}" if swc else ""
            title = issue.get("title", "Unknown")
            severity_raw = issue.get("severity", "Medium")

            return ToolFinding(
                id=(
                    f"MYTH-{swc_key}"
                    if swc_key
                    else f"MYTH-{title[:20].upper().replace(' ','-')}"
                ),
                title=title,
                severity=self.SEVERITY_MAP.get(severity_raw, "MEDIUM"),
                category=self.SWC_TO_CATEGORY.get(swc_key, _classify_category(title)),
                description=issue.get("description", ""),
                file_path=file_path,
                line=issue.get("lineno", 0),
                line_end=issue.get("lineno", 0),
                code_snippet=issue.get("code", "")[:500],
                source_tool="mythril",
                confidence=0.75,
                detector_name=swc_key or title,
            )
        except Exception as e:
            _logger.debug("Mythril parse error: %s", e)
            return None


# ═══════════════════════════════════════════════════════════════
#  Semgrep Runner
# ═══════════════════════════════════════════════════════════════

# Built-in Solidity security rules (no external rule download needed)
_SEMGREP_SOLIDITY_RULES = """
rules:
  - id: reentrancy-eth-transfer
    pattern: |
      (bool $OK, ) = $ADDR.call{value: $AMT}($DATA);
    message: "External call with ETH transfer — check for reentrancy"
    languages: [solidity]
    severity: ERROR

  - id: unchecked-call-return
    patterns:
      - pattern: |
          (bool $OK,) = $ADDR.call($DATA);
      - pattern-not-inside: |
          require($OK);
    message: "Unchecked return value of low-level call"
    languages: [solidity]
    severity: WARNING

  - id: tx-origin-auth
    pattern: |
      require(tx.origin == $ADDR, ...);
    message: "tx.origin used for authentication — vulnerable to phishing"
    languages: [solidity]
    severity: ERROR

  - id: unsafe-delegatecall
    pattern: |
      $ADDR.delegatecall($DATA);
    message: "Unsafe delegatecall — verify target is trusted"
    languages: [solidity]
    severity: ERROR

  - id: selfdestruct-unprotected
    pattern: |
      selfdestruct($ADDR);
    message: "selfdestruct found — ensure proper access control"
    languages: [solidity]
    severity: ERROR

  - id: block-timestamp-dependency
    pattern: |
      require(block.timestamp >= $VAL, ...);
    message: "Block timestamp in condition — can be manipulated by miners"
    languages: [solidity]
    severity: WARNING

  - id: arbitrary-eth-send
    pattern: |
      $ADDR.transfer($AMT);
    message: "ETH transfer — verify recipient address"
    languages: [solidity]
    severity: WARNING

  - id: state-after-external-call
    pattern: |
      (bool $OK, ) = $EXT.call{value: $V}($D);
      ...
      $STATE = $EXPR;
    message: "State change after external call — verify CEI order"
    languages: [solidity]
    severity: WARNING
"""

SEMGREP_SEVERITY_MAP = {
    "ERROR": "HIGH",
    "WARNING": "MEDIUM",
    "INFO": "LOW",
}


class SemgrepRunner:
    """
    Native Semgrep subprocess wrapper with built-in Solidity rules.
    """

    def __init__(self, timeout: int = 60, extra_rules_path: Optional[str] = None):
        self.timeout = timeout
        self.extra_rules_path = extra_rules_path
        self.path = shutil.which("semgrep")
        self.available = self.path is not None
        self._rules_file: Optional[str] = None

    def analyze(self, file_path: str) -> ToolResult:
        """Run Semgrep on a Solidity file. Returns explicit result."""
        import time

        result = ToolResult(tool_name="semgrep", available=self.available)

        if not self.available:
            result.error = "semgrep not installed (pip install semgrep)"
            _logger.warning("Semgrep not available: %s", result.error)
            return result

        if not os.path.exists(file_path):
            result.error = f"File not found: {file_path}"
            return result

        # Create temp rules file
        rules_file = self._get_rules_file()
        if not rules_file:
            result.error = "Failed to create Semgrep rules file"
            return result

        cmd = ["semgrep", "--config", rules_file, "--json", file_path]
        if self.extra_rules_path:
            cmd = [
                "semgrep",
                "--config",
                rules_file,
                "--config",
                self.extra_rules_path,
                "--json",
                file_path,
            ]

        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            result.stderr = proc.stderr[:2000] if proc.stderr else ""

            if proc.stdout:
                try:
                    data = json.loads(proc.stdout)
                    for match in data.get("results", []):
                        finding = self._parse_finding(match, file_path)
                        if finding:
                            result.findings.append(finding)
                    result.success = True
                except json.JSONDecodeError as e:
                    result.error = f"JSON parse error: {e}"
            else:
                result.success = True

        except subprocess.TimeoutExpired:
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            result.timed_out = True
            result.error = f"Semgrep timed out after {self.timeout}s"
        except FileNotFoundError:
            result.error = "semgrep binary not found in PATH"
            result.available = False
        except Exception as e:
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            result.error = f"Semgrep error: {e}"

        _logger.info(
            "Semgrep: %d findings in %dms (success=%s)",
            len(result.findings),
            result.duration_ms,
            result.success,
        )
        return result

    def _parse_finding(self, match: Dict, file_path: str) -> Optional[ToolFinding]:
        """Parse a single Semgrep match."""
        try:
            rule_id = match.get("check_id", "unknown")
            # Clean up semgrep rule path prefix
            rule_short = rule_id.split(".")[-1] if "." in rule_id else rule_id
            severity_raw = match.get("extra", {}).get("severity", "INFO")
            msg = match.get("extra", {}).get("message", "")

            return ToolFinding(
                id=f"SEMGREP-{rule_short.upper()}",
                title=rule_short.replace("-", " ").title(),
                severity=SEMGREP_SEVERITY_MAP.get(severity_raw, "LOW"),
                category=_classify_category(rule_short),
                description=msg,
                file_path=file_path,
                line=match.get("start", {}).get("line", 0),
                line_end=match.get("end", {}).get("line", 0),
                code_snippet=match.get("extra", {}).get("lines", "")[:500],
                source_tool="semgrep",
                confidence=0.8 if severity_raw == "ERROR" else 0.6,
                detector_name=rule_short,
            )
        except Exception as e:
            _logger.debug("Semgrep parse error: %s", e)
            return None

    def _get_rules_file(self) -> Optional[str]:
        """Create a temporary rules file."""
        if self._rules_file and os.path.exists(self._rules_file):
            return self._rules_file
        try:
            fd, path = tempfile.mkstemp(suffix=".yaml", prefix="agl_semgrep_")
            with os.fdopen(fd, "w") as f:
                f.write(_SEMGREP_SOLIDITY_RULES)
            self._rules_file = path
            return path
        except Exception as e:
            _logger.error("Failed to create semgrep rules: %s", e)
            return None

    def __del__(self):
        if self._rules_file and os.path.exists(self._rules_file):
            try:
                os.unlink(self._rules_file)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
#  Parallel Runner — runs all tools and merges results
# ═══════════════════════════════════════════════════════════════


class ToolBackendRunner:
    """
    Runs all available external tools in parallel.
    Results are explicit — tool failures appear in report, never silenced.
    """

    def __init__(
        self,
        enable_slither: bool = True,
        enable_mythril: bool = True,
        enable_semgrep: bool = True,
        slither_timeout: int = 120,
        mythril_timeout: int = 300,
        semgrep_timeout: int = 60,
    ):
        self.slither = (
            SlitherRunner(timeout=slither_timeout) if enable_slither else None
        )
        self.mythril = (
            MythrilRunner(timeout=mythril_timeout) if enable_mythril else None
        )
        self.semgrep = (
            SemgrepRunner(timeout=semgrep_timeout) if enable_semgrep else None
        )

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Run all enabled tools on a file.
        Returns dict with:
            - findings: List[Dict] — all tool findings merged
            - tool_status: Dict — per-tool success/error status
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        all_findings: List[Dict[str, Any]] = []
        tool_status: Dict[str, Dict] = {}
        runners = []

        if self.slither:
            runners.append(("slither", self.slither))
        if self.mythril:
            runners.append(("mythril", self.mythril))
        if self.semgrep:
            runners.append(("semgrep", self.semgrep))

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(runner.analyze, file_path): name
                for name, runner in runners
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result: ToolResult = future.result()
                    tool_status[name] = result.to_dict()
                    for tf in result.findings:
                        all_findings.append(tf.to_dict())
                except Exception as e:
                    tool_status[name] = {
                        "tool": name,
                        "available": False,
                        "success": False,
                        "error": str(e),
                        "findings_count": 0,
                    }

        return {
            "findings": all_findings,
            "tool_status": tool_status,
            "total_findings": len(all_findings),
        }

    def status(self) -> Dict[str, bool]:
        """Check which tools are available."""
        return {
            "slither": self.slither.available if self.slither else False,
            "mythril": self.mythril.available if self.mythril else False,
            "semgrep": self.semgrep.available if self.semgrep else False,
        }
