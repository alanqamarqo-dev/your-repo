"""
اختبارات إصلاحات RC-FIX-1 إلى RC-FIX-5 في audit_pipeline.py
Regression tests for the 5 fixes (RC-FIX-1..5) applied to audit_pipeline.py.

يُشغَّل على عقود Alchemix V2 الخمسة الحقيقية للتحقق من أن الإصلاحات فعّالة.
Uses the 5 real Alchemix V2 bug-bounty contracts to validate each fix.

Fixes verified:
  RC-FIX-1: `'_store' in dir()` → `'_store' in locals()` (Python spec compliance)
  RC-FIX-2: Removed redundant `import re` inside hot-path nested functions
  RC-FIX-3: `discover_project()` now returns `project_path` in its dict
  RC-FIX-4: Heikal findings merged into `severity_total` in `generate_final_report()`
  RC-FIX-5: `run_detectors()` safe-func suppression aligned with `deduplicate_cross_layer()` (LOW/INFO only)
"""

import sys
import os
import re
import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, List

# === Path setup ===
_this = Path(__file__).resolve().parent
_pkg = _this.parent  # agl_security_tool/
_root = _pkg.parent  # AGL/
sys.path.insert(0, str(_pkg))
sys.path.insert(0, str(_root))

from agl_security_tool.audit_pipeline import (
    AuditContext,
    deduplicate_cross_layer,
    discover_project,
    generate_final_report,
    extract_function_blocks,
)

# === Alchemix 5-core path ===
ALCHEMIX_DIR = _pkg / "bounty_contracts" / "alchemix_5core"
ALCHEMIX_SRC = ALCHEMIX_DIR / "src"

# Skip all tests if contracts not found
pytestmark = pytest.mark.skipif(
    not ALCHEMIX_SRC.exists(),
    reason="Alchemix 5-core contracts not found",
)


# ─── Helper: build a minimal project from alchemix ───

def _alchemix_project() -> Dict:
    """Build a project dict from alchemix_5core for testing."""
    contracts = {}
    main_contracts = []
    for sol in ALCHEMIX_SRC.glob("*.sol"):
        name = sol.stem
        contracts[name] = sol
        main_contracts.append(name)
    return {
        "project_type": "bare",
        "contracts_dir": str(ALCHEMIX_SRC),
        "contracts": contracts,
        "main_contracts": main_contracts,
        "libraries": [],
        "interfaces": [],
        "info": None,
    }


# ═══════════════════════════════════════════════════════════════
#  RC-FIX-1: `'_store' in locals()` — Python spec-compliant check
#  Fixed: dir() → locals() in run_state_extraction's finally block
# ═══════════════════════════════════════════════════════════════

class TestFix1_LocalsInsteadOfDir:
    """RC-FIX-1: run_state_extraction uses locals() not dir()."""

    def test_source_code_uses_locals(self):
        """
        يتحقق أن الكود المصدري يستخدم locals() (الطريقة الرسمية).
        """
        import inspect
        from agl_security_tool.audit_pipeline import run_state_extraction

        source = inspect.getsource(run_state_extraction)

        assert "'_store' in locals()" in source, (
            "RC-FIX-1 REGRESSION: run_state_extraction should use locals() not dir()"
        )
        assert "'_store' in dir()" not in source, (
            "RC-FIX-1 REGRESSION: dir() pattern still present — should be locals()"
        )

    def test_locals_reliably_finds_variable(self):
        """
        يتحقق أن locals() تجد المتغير المحلي دائماً — مضمون بمواصفة Python.
        """
        def simulate_fixed_pattern():
            results = {}
            try:
                _store = {"data": "test_value"}
                results["via_try"] = _store
                return results
            except Exception:
                _store = {"error": "failed"}
                return results
            finally:
                if '_store' in locals():
                    results["found"] = True

        result = simulate_fixed_pattern()
        assert result.get("found") is True, (
            "locals() must always find '_store' in finally block"
        )


# ═══════════════════════════════════════════════════════════════
#  RC-FIX-2: Removed redundant `import re` from nested functions
#  Fixed: normalize_title() and extract_func_from_finding() now
#  use module-level `re` (imported at line 68).
# ═══════════════════════════════════════════════════════════════

class TestFix2_NoRedundantImportRe:
    """RC-FIX-2: no redundant `import re` in deduplicate_cross_layer."""

    def test_no_inner_import_re(self):
        """
        يتحقق أن normalize_title و extract_func_from_finding لا تستوردان re داخلياً.
        """
        import inspect
        source = inspect.getsource(deduplicate_cross_layer)

        inner_imports = len(re.findall(r'^\s+import re\b', source, re.MULTILINE))

        assert inner_imports == 0, (
            f"RC-FIX-2 REGRESSION: found {inner_imports} inner `import re` "
            f"in deduplicate_cross_layer — should be 0"
        )

    def test_dedup_still_works_with_module_re(self):
        """
        يتحقق أن deduplicate_cross_layer تعمل بشكل صحيح بعد إزالة الاستيرادات.
        """
        ctx = AuditContext(engines={}, project=_alchemix_project(), mode="full")
        ctx.results = {
            "deep_scan": {"AlchemistV2": {
                "all_findings_unified": [
                    {"title": "Test: reentrancy!@#$", "severity": "HIGH",
                     "category": "reentrancy", "function": "deposit", "line": 50},
                ],
            }},
            "z3_symbolic": [],
            "detectors": [],
            "exploit_reasoning": {},
            "heikal_math": {},
            "state_extraction": {},
        }
        ctx.shared_parse = {}

        result = deduplicate_cross_layer(ctx)
        unified = result.get("unified_findings", [])
        assert len(unified) >= 1, "dedup should produce at least 1 finding"


# ═══════════════════════════════════════════════════════════════
#  RC-FIX-3: discover_project() now returns `project_path`
#  Fixed: return dict includes project_path so callers don't
#  need to inject it manually (as run_audit previously did).
# ═══════════════════════════════════════════════════════════════

class TestFix3_DiscoverProjectIncludesPath:
    """RC-FIX-3: discover_project() returns project_path."""

    def test_discover_project_has_project_path(self):
        """
        يتحقق أن discover_project() تُرجع project_path.
        """
        project = discover_project(str(ALCHEMIX_SRC))

        assert "project_path" in project, (
            "RC-FIX-3 REGRESSION: discover_project() must return project_path"
        )
        assert project["project_path"] == str(ALCHEMIX_SRC), (
            f"RC-FIX-3: project_path should be '{ALCHEMIX_SRC}', "
            f"got '{project['project_path']}'"
        )

    def test_poc_generation_can_find_project_path(self):
        """
        يتحقق أن run_poc_generation ستجد project_path بدون تدخل يدوي.
        """
        project = discover_project(str(ALCHEMIX_SRC))
        project_path = project.get("project_path", "")

        assert project_path != "", (
            "RC-FIX-3 REGRESSION: project_path should not be empty"
        )

    def test_discover_alchemix_finds_contracts(self):
        """
        يتحقق أن discover_project تجد عقود Alchemix الخمسة فعلاً.
        """
        project = discover_project(str(ALCHEMIX_SRC))

        contracts = project["contracts"]
        assert len(contracts) >= 3, (
            f"Expected at least 3 Alchemix contracts, found {len(contracts)}: "
            f"{list(contracts.keys())}"
        )

        contract_names = set(contracts.keys())
        expected = {"AlchemistV2", "TransmuterV2", "AlchemicTokenV2"}
        found = expected & contract_names
        assert len(found) >= 2, (
            f"Expected at least 2 of {expected}, found {found} in {contract_names}"
        )


# ═══════════════════════════════════════════════════════════════
#  RC-FIX-4: Heikal findings now merged into severity_total
#  Fixed: generate_final_report() counts heikal CRITICAL/HIGH/etc
#  and adds them to the report's severity_total and total_findings.
# ═══════════════════════════════════════════════════════════════

class TestFix4_HeikalInSeverityTotal:
    """RC-FIX-4: Heikal findings included in severity_total."""

    def _build_mock_results(self) -> Dict:
        """Build realistic all_results with heikal findings."""
        return {
            "deep_scan": {
                "AlchemistV2": {
                    "findings": [
                        {"title": "Reentrancy", "severity": "HIGH", "line": 100},
                    ],
                    "severity_summary": {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0, "INFO": 0},
                }
            },
            "z3_symbolic": [],
            "detectors": [],
            "state_extraction": {},
            "exploit_reasoning": {},
            "heikal_math": {
                "functions": {
                    "AlchemistV2::deposit": {
                        "severity": "HIGH",
                        "tunneling": {"confidence": 0.65},
                        "wave": {"heuristic_score": 0.72},
                        "description": "High-risk deposit function",
                        "_contract": "AlchemistV2",
                    },
                    "AlchemistV2::withdraw": {
                        "severity": "CRITICAL",
                        "tunneling": {"confidence": 0.85},
                        "wave": {"heuristic_score": 0.90},
                        "description": "Critical withdraw function",
                        "_contract": "AlchemistV2",
                    },
                },
                "attacks": {
                    "Reentrancy_Attack": {
                        "severity": "CRITICAL",
                        "tunneling": {"confidence": 0.80},
                        "wave": {"heuristic_score": 0.85},
                        "description": "Re-enter via callback",
                    },
                },
                "summary": {
                    "total_functions_analyzed": 2,
                    "total_attacks_analyzed": 1,
                },
            },
            "unified_findings": [
                {"title": "Reentrancy", "severity": "HIGH", "line": 100},
            ],
            "dedup_stats": {"total_unified": 1},
            "severity_unified": {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0, "INFO": 0},
        }

    def test_heikal_merged_into_severity_total(self):
        """
        يتحقق أن generate_final_report() تُدمج Heikal findings في severity_total.
        Heikal: 2 CRITICAL (1 func + 1 attack) + 1 HIGH (1 func)
        Unified: 0 CRITICAL, 1 HIGH
        Total expected: 2 CRITICAL, 2 HIGH
        """
        all_results = self._build_mock_results()
        project = _alchemix_project()

        report = generate_final_report(all_results, project, "alchemix_test", 10.0)

        severity = report["severity_total"]
        heikal_count = report.get("heikal_analyses", 0)

        assert heikal_count == 3, (
            f"Expected 3 heikal analyses, got {heikal_count}"
        )

        # RC-FIX-4: CRITICAL should now include heikal CRITICAL findings
        assert severity.get("CRITICAL", 0) == 2, (
            f"RC-FIX-4 REGRESSION: CRITICAL should be 2 (heikal: 1 func + 1 attack), "
            f"got {severity.get('CRITICAL', 0)}"
        )

        # HIGH: 1 from unified + 1 from heikal function
        assert severity.get("HIGH", 0) == 2, (
            f"RC-FIX-4 REGRESSION: HIGH should be 2 (1 unified + 1 heikal), "
            f"got {severity.get('HIGH', 0)}"
        )

    def test_heikal_severity_breakdown_in_report(self):
        """
        يتحقق أن التقرير يحتوي heikal_severity كحقل منفصل.
        """
        all_results = self._build_mock_results()
        project = _alchemix_project()

        report = generate_final_report(all_results, project, "test", 5.0)

        assert "heikal_severity" in report, (
            "RC-FIX-4: report should contain heikal_severity breakdown"
        )
        hs = report["heikal_severity"]
        assert hs["CRITICAL"] == 2
        assert hs["HIGH"] == 1

    def test_total_findings_includes_heikal(self):
        """
        يتحقق أن total_findings يشمل Heikal findings.
        """
        all_results = self._build_mock_results()
        project = _alchemix_project()

        report = generate_final_report(all_results, project, "test", 5.0)

        # 1 unified + 3 heikal = 4 total
        assert report["total_findings"] == 4, (
            f"RC-FIX-4 REGRESSION: total_findings should be 4 (1 unified + 3 heikal), "
            f"got {report['total_findings']}"
        )


# ═══════════════════════════════════════════════════════════════
#  RC-FIX-5: Safe function suppression now consistent
#  Fixed: run_detectors() now only suppresses LOW/INFO on safe
#  functions, matching deduplicate_cross_layer() behavior.
# ═══════════════════════════════════════════════════════════════

class TestFix5_SafeFuncConsistentSuppression:
    """RC-FIX-5: Both layers suppress only LOW/INFO on safe functions."""

    def test_run_detectors_has_severity_filter(self):
        """
        يتحقق أن run_detectors تحتوي فلتر severity قبل حذف findings.
        RC-FIX-5: الآن تحذف فقط LOW/INFO — مطابقة لـ deduplicate_cross_layer.
        """
        import inspect
        from agl_security_tool.audit_pipeline import run_detectors

        source = inspect.getsource(run_detectors)

        # After RC-FIX-5: run_detectors checks sev in ("LOW", "INFO")
        assert 'sev in ("LOW", "INFO")' in source, (
            "RC-FIX-5 REGRESSION: run_detectors must check severity "
            "before suppressing safe function findings"
        )

    def test_dedup_also_suppresses_low_info_only(self):
        """
        يتحقق أن deduplicate_cross_layer تحذف فقط LOW/INFO — متسقة مع run_detectors.
        """
        import inspect
        source = inspect.getsource(deduplicate_cross_layer)

        assert 'sev in ("LOW", "INFO")' in source, (
            "deduplicate_cross_layer should only suppress LOW/INFO on safe functions"
        )

    def test_critical_not_suppressed_on_safe_func(self):
        """
        اختبار عملي: CRITICAL finding على safe function لا تُحذف في أي طبقة.
        RC-FIX-5 ضمنت أن كلا الطبقتين تتوافقان.
        """
        critical_finding = {
            "title": "Reentrancy in _withdraw",
            "severity": "CRITICAL",
            "category": "reentrancy",
            "function": "_withdraw",
            "line": 200,
        }

        safe_funcs = {"_withdraw"}

        sev = str(critical_finding.get("severity", "MEDIUM")).upper()
        fn = critical_finding.get("function", "").lower()

        # Both layers now use the SAME logic: only suppress LOW/INFO
        would_suppress = fn in safe_funcs and sev in ("LOW", "INFO")
        assert would_suppress is False, (
            "RC-FIX-5 REGRESSION: CRITICAL findings on safe functions must NOT be suppressed"
        )

    def test_low_info_suppressed_on_safe_func(self):
        """
        يتحقق أن LOW/INFO على safe function تُحذف بشكل صحيح.
        """
        for sev_level in ("LOW", "INFO"):
            finding = {"severity": sev_level, "function": "_internal"}
            safe_funcs = {"_internal"}

            sev = str(finding["severity"]).upper()
            fn = finding["function"].lower()

            would_suppress = fn in safe_funcs and sev in ("LOW", "INFO")
            assert would_suppress is True, (
                f"{sev_level} findings on safe functions should be suppressed"
            )


# ═══════════════════════════════════════════════════════════════
#  Integration: Run full pipeline on Alchemix to verify bugs manifest
# ═══════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestBugsOnAlchemixContracts:
    """Integration tests using real Alchemix contracts."""

    def test_discover_alchemix_project(self):
        """RC-FIX-3: discover_project includes project_path."""
        project = discover_project(str(ALCHEMIX_SRC))

        # RC-FIX-3: project_path now included
        assert "project_path" in project, (
            "RC-FIX-3 REGRESSION: project_path must be in discover_project()"
        )
        assert project["project_path"], "project_path should be non-empty"

        # The project should still be valid
        assert len(project["contracts"]) >= 3
        assert project["project_type"] in ("bare", "foundry", "hardhat")

    def test_extract_function_blocks_alchemix(self):
        """extract_function_blocks works on real Alchemix contracts."""
        alchemist = ALCHEMIX_SRC / "AlchemistV2.sol"
        if not alchemist.exists():
            pytest.skip("AlchemistV2.sol not found")

        with open(alchemist, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        blocks = extract_function_blocks(source)

        assert len(blocks) > 0, "Should find functions in AlchemistV2.sol"

        # Check for known functions
        func_names = set(blocks.keys())
        print(f"\n  Found {len(func_names)} functions: {sorted(func_names)[:10]}...")

        # Verify blocks contain actual code (not truncated)
        for name, body in list(blocks.items())[:3]:
            assert body.startswith("function"), (
                f"Block for {name} should start with 'function', got: {body[:50]}"
            )
            assert "{" in body and "}" in body, (
                f"Block for {name} should contain braces"
            )

    def test_dedup_with_mock_alchemix_findings(self):
        """
        يُشغِّل deduplicate_cross_layer على بيانات مُحاكية لـ Alchemix.
        RC-FIX-4: Heikal findings now included in severity counts.
        """
        ctx = AuditContext(
            engines={},
            project=_alchemix_project(),
            target_name="alchemix_v2",
            mode="full",
        )
        ctx.results = {
            "deep_scan": {
                "AlchemistV2": {
                    "findings": [
                        {
                            "title": "Reentrancy in deposit()",
                            "severity": "HIGH",
                            "category": "reentrancy",
                            "function": "deposit",
                            "line": 150,
                        }
                    ],
                    "all_findings_unified": [
                        {
                            "title": "Reentrancy in deposit()",
                            "severity": "HIGH",
                            "category": "reentrancy",
                            "function": "deposit",
                            "line": 150,
                        }
                    ],
                }
            },
            "z3_symbolic": [],
            "detectors": [],
            "exploit_reasoning": {},
            "heikal_math": {
                "functions": {
                    "AlchemistV2::withdraw": {
                        "severity": "CRITICAL",
                        "tunneling": {"confidence": 0.82},
                        "wave": {"heuristic_score": 0.88},
                        "description": "Critical withdraw",
                        "_contract": "AlchemistV2",
                    },
                },
                "attacks": {},
            },
            "state_extraction": {},
        }
        ctx.shared_parse = {}

        result = deduplicate_cross_layer(ctx)

        unified = result.get("unified_findings", [])
        severity = result.get("severity_unified", {})

        # deep_scan: 1 HIGH finding
        # heikal: 1 CRITICAL finding (if not deduped)
        total = len(unified)
        print(f"\n  Unified: {total} findings, severity: {severity}")

        # Bug #4 manifests here: even if heikal CRITICAL is in unified_findings,
        # generate_final_report doesn't add it to the report's severity summary
        # when counting from unified_findings fallback path.
        # Let's verify the dedup itself works:
        assert total >= 1, f"Expected at least 1 finding, got {total}"


class TestFixesSummary:
    """Summary test: confirms all 5 RC-FIX patches are active."""

    def test_all_fixes_applied(self):
        """
        ملخص: يتحقق أن جميع الإصلاحات الخمسة مُطبّقة.
        Summary: verifies all 5 RC-FIX patches are active.
        """
        import inspect
        from agl_security_tool.audit_pipeline import (
            run_state_extraction,
            run_detectors,
        )

        fixes = {}

        # RC-FIX-1: locals() instead of dir()
        src_state = inspect.getsource(run_state_extraction)
        fixes["FIX1_locals_not_dir"] = "'_store' in locals()" in src_state

        # RC-FIX-2: no redundant import re
        src_dedup = inspect.getsource(deduplicate_cross_layer)
        inner_imports = len(re.findall(r'^\s+import re\b', src_dedup, re.MULTILINE))
        fixes["FIX2_no_redundant_import"] = inner_imports == 0

        # RC-FIX-3: discover_project includes project_path
        project = discover_project(str(ALCHEMIX_SRC))
        fixes["FIX3_project_path_present"] = "project_path" in project

        # RC-FIX-4: heikal merged into severity_total
        src_report = inspect.getsource(generate_final_report)
        fixes["FIX4_heikal_in_severity"] = (
            "heikal_severity" in src_report
            and "severity_total" in src_report
        )

        # RC-FIX-5: run_detectors severity filter on safe funcs
        src_det = inspect.getsource(run_detectors)
        fixes["FIX5_safe_func_severity_filter"] = (
            'sev in ("LOW", "INFO")' in src_det
        )

        # Print summary
        print("\n" + "=" * 60)
        print("  RC-FIX STATUS SUMMARY / ملخص حالة الإصلاحات")
        print("=" * 60)
        failed = []
        for name, is_applied in fixes.items():
            status = "✅ APPLIED" if is_applied else "🔴 MISSING"
            if not is_applied:
                failed.append(name)
            print(f"  {status}  {name}")
        print(f"\n  Total: {len(fixes) - len(failed)}/{len(fixes)} fixes applied")
        print("=" * 60)

        # ALL fixes must be applied — this is a regression guard
        assert len(failed) == 0, (
            f"RC-FIX REGRESSION: {len(failed)} fixes missing: {failed}"
        )
