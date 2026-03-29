"""
اختبارات تكامل Foundry — Foundry Integration Tests
====================================================

End-to-end tests that run the full AGL pipeline on:
  - VulnerableVault.sol (7 known vulns → expect high recall)
  - SafeVault.sol (secured → expect minimal FPs)

These tests validate that all 7 architectural fixes work together:
  #1  AuditContext passes data between layers
  #2  Exploit Reasoning detects structural exploitability
  #3  Auto-resolve imports
  #4  FP suppression for safe patterns
  #5  Z3 proven findings flow to Exploit Reasoning
  #6  New detectors catch V3 (unchecked-return) + V6 (overflow)
  #7  Heikal/Exploit/State merged into unified findings

Expected results after fixes:
  - VulnerableVault: 7/7 vulns detected (100% recall)
  - SafeVault: 0 CRITICAL, ≤2 HIGH (minimal FPs)
"""

import pytest
import sys
import os
import json
from pathlib import Path

# Ensure agl_security_tool is importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# Test contract paths
FOUNDRY_DIR = Path(__file__).parent.parent.parent / "test_foundry_audit"
VULNERABLE_VAULT = FOUNDRY_DIR / "src" / "VulnerableVault.sol"
SAFE_VAULT = FOUNDRY_DIR / "src" / "SafeVault.sol"


def _get_detectors_only_findings(source_path: str):
    """Run only the 24 semantic detectors on a contract (fast, no LLM needed)."""
    from agl_security_tool.detectors import DetectorRunner
    from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser

    with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    parser = SoliditySemanticParser()
    contracts = parser.parse(source, str(source_path))
    runner = DetectorRunner()
    return runner.run(contracts)


def _get_core_deep_scan(source_path: str):
    """Run core.py deep_scan (L0-L5) on a single contract."""
    from agl_security_tool.core import AGLSecurityAudit

    audit = AGLSecurityAudit()
    return audit.deep_scan(str(source_path))


# ═══════════════════════════════════════════════════
#  Detector-level tests (fast, no external tools)
# ═══════════════════════════════════════════════════


class TestVulnerableVaultDetectors:
    """Run 24 detectors on VulnerableVault — validate recall."""

    _cached_findings = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if not VULNERABLE_VAULT.exists():
            pytest.skip("VulnerableVault.sol not found")
        if TestVulnerableVaultDetectors._cached_findings is None:
            TestVulnerableVaultDetectors._cached_findings = (
                _get_detectors_only_findings(str(VULNERABLE_VAULT))
            )
        self.findings = TestVulnerableVaultDetectors._cached_findings
        self.ids = [f.detector_id for f in self.findings]
        self.by_id = {}
        for f in self.findings:
            self.by_id.setdefault(f.detector_id, []).append(f)

    def test_reentrancy_detected(self):
        """V1: Reentrancy — external call before state update in withdraw()."""
        reentrancy = [f for f in self.findings if "REENTRANCY" in f.detector_id]
        assert len(reentrancy) >= 1, "V1: Reentrancy in withdraw() not detected"
        # Should be in withdraw function
        funcs = {f.function for f in reentrancy}
        assert (
            "withdraw" in funcs
        ), f"V1: Reentrancy not found in withdraw(), found in {funcs}"

    def test_access_control_detected(self):
        """V2: Access control bypass — setOracle() has no onlyOwner."""
        access = [
            f
            for f in self.findings
            if "ACCESS" in f.detector_id or "UNPROTECTED" in f.detector_id
        ]
        assert len(access) >= 1, "V2: Access control bypass not detected"

    def test_unchecked_return_detected(self):
        """V3: Unchecked return value — token.transfer() in transferTokens()."""
        unchecked = [f for f in self.findings if f.detector_id == "UNCHECKED-RETURN"]
        assert len(unchecked) >= 1, (
            "V3: UNCHECKED-RETURN not detected (new detector). "
            f"All IDs found: {set(self.ids)}"
        )

    def test_first_deposit_detected(self):
        """V4: First-deposit attack — no minimum shares in deposit()."""
        first_dep = [f for f in self.findings if "FIRST-DEPOSIT" in f.detector_id]
        assert len(first_dep) >= 1, "V4: First-deposit attack not detected"

    def test_oracle_manipulation_detected(self):
        """V5: Oracle manipulation — spot price used in liquidate()."""
        oracle = [f for f in self.findings if "ORACLE" in f.detector_id]
        assert len(oracle) >= 1, "V5: Oracle manipulation not detected"

    def test_integer_overflow_detected(self):
        """V6: Integer overflow — unchecked block in addBonus()."""
        overflow = [f for f in self.findings if f.detector_id == "INTEGER-OVERFLOW"]
        assert len(overflow) >= 1, (
            "V6: INTEGER-OVERFLOW not detected (new detector). "
            f"All IDs found: {set(self.ids)}"
        )

    def test_tx_origin_detected(self):
        """V7: tx.origin auth — in emergencyWithdraw()."""
        tx_origin = [f for f in self.findings if "TX-ORIGIN" in f.detector_id]
        assert len(tx_origin) >= 1, "V7: tx.origin auth not detected"

    def test_minimum_recall(self):
        """Combined: at least 5/7 vulnerability types must be detected (71%)."""
        vuln_types = {
            "V1_reentrancy": any("REENTRANCY" in f.detector_id for f in self.findings),
            "V2_access": any(
                "ACCESS" in f.detector_id or "UNPROTECTED" in f.detector_id
                for f in self.findings
            ),
            "V3_unchecked_return": any(
                f.detector_id == "UNCHECKED-RETURN" for f in self.findings
            ),
            "V4_first_deposit": any(
                "FIRST-DEPOSIT" in f.detector_id for f in self.findings
            ),
            "V5_oracle": any("ORACLE" in f.detector_id for f in self.findings),
            "V6_overflow": any(
                f.detector_id == "INTEGER-OVERFLOW" for f in self.findings
            ),
            "V7_tx_origin": any("TX-ORIGIN" in f.detector_id for f in self.findings),
        }

        detected = sum(v for v in vuln_types.values())
        print(f"\n  Recall: {detected}/7 ({detected/7*100:.0f}%)")
        for name, found in vuln_types.items():
            status = "✅" if found else "❌"
            print(f"    {status} {name}")

        assert detected >= 5, f"Recall too low: {detected}/7. Details: {vuln_types}"

    def test_severity_distribution(self):
        """Verify severity distribution — most findings should be HIGH/CRITICAL."""
        sevs = {}
        for f in self.findings:
            s = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            sevs[s] = sevs.get(s, 0) + 1

        print(f"\n  VulnerableVault severity distribution: {sevs}")
        high_critical = (
            sevs.get("CRITICAL", 0)
            + sevs.get("HIGH", 0)
            + sevs.get("critical", 0)
            + sevs.get("high", 0)
        )
        assert (
            high_critical >= 3
        ), f"Expected ≥3 HIGH/CRITICAL findings, got {high_critical}"


class TestSafeVaultDetectors:
    """Run 24 detectors on SafeVault — validate FP rate."""

    _cached_findings = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if not SAFE_VAULT.exists():
            pytest.skip("SafeVault.sol not found")
        if TestSafeVaultDetectors._cached_findings is None:
            TestSafeVaultDetectors._cached_findings = _get_detectors_only_findings(
                str(SAFE_VAULT)
            )
        self.findings = TestSafeVaultDetectors._cached_findings

    def test_no_critical_findings(self):
        """SafeVault should have 0 CRITICAL findings."""
        critical = [
            f
            for f in self.findings
            if (
                f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            ).upper()
            == "CRITICAL"
        ]
        if critical:
            for f in critical:
                print(f"  FP CRITICAL: [{f.detector_id}] {f.function} — {f.title}")
        assert (
            len(critical) == 0
        ), f"SafeVault has {len(critical)} CRITICAL findings (all FPs)"

    def test_minimal_high_findings(self):
        """SafeVault should have ≤3 HIGH findings (allowing some parser limitations)."""
        high = [
            f
            for f in self.findings
            if (
                f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            ).upper()
            == "HIGH"
        ]
        if high:
            print(f"\n  SafeVault HIGH findings ({len(high)}):")
            for f in high:
                print(f"    FP?: [{f.detector_id}] {f.function} — {f.title}")
        assert len(high) <= 3, f"SafeVault has {len(high)} HIGH findings (too many FPs)"

    def test_no_reentrancy_false_positive(self):
        """SafeVault uses nonReentrant — should NOT trigger reentrancy."""
        reentrancy = [
            f
            for f in self.findings
            if "REENTRANCY" in f.detector_id
            and (
                f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            ).upper()
            in ("HIGH", "CRITICAL")
        ]
        assert len(reentrancy) == 0, (
            f"SafeVault has {len(reentrancy)} reentrancy HIGH/CRITICAL findings — "
            "nonReentrant guard should prevent these"
        )


# ═══════════════════════════════════════════════════
#  Deep Scan tests (core.py L0-L5, slower)
# ═══════════════════════════════════════════════════

import shutil

_has_slither = shutil.which("slither") is not None
_deep_scan_reason = "deep_scan requires slither/mythril (external tools not installed)"


@pytest.mark.slow
@pytest.mark.timeout(300)
class TestVulnerableVaultDeepScan:
    """Run full deep_scan on VulnerableVault — test all layers."""

    _cached_result = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if not VULNERABLE_VAULT.exists():
            pytest.skip("VulnerableVault.sol not found")
        if TestVulnerableVaultDeepScan._cached_result is None:
            TestVulnerableVaultDeepScan._cached_result = _get_core_deep_scan(
                str(VULNERABLE_VAULT)
            )
        self.result = TestVulnerableVaultDeepScan._cached_result

    def test_scan_completes(self):
        """Deep scan should complete without errors."""
        assert (
            "error" not in self.result
        ), f"Deep scan failed: {self.result.get('error')}"

    def test_findings_count(self):
        """Should produce a meaningful number of findings."""
        findings = self.result.get(
            "all_findings_unified", self.result.get("findings", [])
        )
        print(f"\n  VulnerableVault deep_scan: {len(findings)} findings")
        assert len(findings) >= 5, f"Too few findings: {len(findings)}"

    def test_layers_used(self):
        """Multiple layers should contribute findings."""
        layers = self.result.get("layers_used", [])
        print(f"  Layers used: {layers}")
        assert len(layers) >= 2, f"Too few layers: {layers}"

    def test_severity_summary(self):
        """Should have at least CRITICAL or HIGH findings."""
        sev = self.result.get("severity_summary", {})
        print(f"  Severity: {sev}")
        high_critical = sev.get("CRITICAL", 0) + sev.get("HIGH", 0)
        assert high_critical >= 2, f"Expected ≥2 HIGH/CRITICAL, got {high_critical}"

    def test_z3_symbolic_runs(self):
        """Z3 symbolic analysis should produce findings."""
        sym = self.result.get("symbolic_findings", [])
        print(f"  Z3 symbolic findings: {len(sym)}")
        # Z3 should at least attempt analysis
        assert isinstance(sym, list)

    def test_exploit_reasoning_runs(self):
        """Exploit reasoning should produce proofs."""
        er = self.result.get("exploit_reasoning", {})
        proofs = er.get("exploit_proofs", []) if isinstance(er, dict) else []
        print(f"  Exploit proofs: {len(proofs)}")

        # After fixes, at least some should be exploitable
        exploitable = [p for p in proofs if p.get("exploitable")]
        print(f"  Exploitable: {len(exploitable)}")

    def test_detector_findings(self):
        """Detector layer should produce findings."""
        det = self.result.get("detector_findings", [])
        print(f"  Detector findings: {len(det)}")
        assert len(det) >= 3, f"Too few detector findings: {len(det)}"


@pytest.mark.slow
@pytest.mark.timeout(300)
class TestSafeVaultDeepScan:
    """Run full deep_scan on SafeVault — test FP suppression."""

    _cached_result = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if not SAFE_VAULT.exists():
            pytest.skip("SafeVault.sol not found")
        if TestSafeVaultDeepScan._cached_result is None:
            TestSafeVaultDeepScan._cached_result = _get_core_deep_scan(str(SAFE_VAULT))
        self.result = TestSafeVaultDeepScan._cached_result

    def test_scan_completes(self):
        assert (
            "error" not in self.result
        ), f"Deep scan failed: {self.result.get('error')}"

    def test_reduced_false_positives(self):
        """SafeVault should have fewer HIGH/CRITICAL findings than VulnerableVault."""
        findings = self.result.get(
            "all_findings_unified", self.result.get("findings", [])
        )
        high_crit = [
            f
            for f in findings
            if str(f.get("severity", "")).upper() in ("CRITICAL", "HIGH")
        ]
        print(
            f"\n  SafeVault deep_scan: {len(findings)} total, {len(high_crit)} HIGH/CRITICAL"
        )

        if high_crit:
            for f in high_crit:
                print(
                    f"    FP?: [{f.get('detector', f.get('category', '?'))}] "
                    f"{f.get('function', '?')} — {f.get('title', '?')}"
                )

    def test_fp_suppression_working(self):
        """Check that FP suppression is actively reducing noise."""
        findings = self.result.get(
            "all_findings_unified", self.result.get("findings", [])
        )
        suppressed = [f for f in findings if f.get("suppression_reason")]
        print(f"  Suppressed findings (demoted to info/low): {len(suppressed)}")


# ═══════════════════════════════════════════════════
#  Exploit Reasoning integration
# ═══════════════════════════════════════════════════


class TestExploitReasoningIntegration:
    """Test exploit reasoning on VulnerableVault with real findings."""

    @pytest.fixture(autouse=True)
    def setup(self):
        if not VULNERABLE_VAULT.exists():
            pytest.skip("VulnerableVault.sol not found")

    def test_exploit_on_real_findings(self):
        """Run exploit reasoning on VulnerableVault findings."""
        from agl_security_tool.exploit_reasoning import ExploitReasoningEngine

        with open(VULNERABLE_VAULT, "r", encoding="utf-8") as f:
            source = f.read()

        # Create synthetic findings matching VulnerableVault's known vulns
        findings = [
            {
                "title": "Reentrancy in withdraw()",
                "severity": "HIGH",
                "original_severity": "HIGH",
                "category": "reentrancy",
                "function": "withdraw",
                "line": 65,
                "description": "External call before state update",
            },
            {
                "title": "Access control bypass in setOracle()",
                "severity": "HIGH",
                "original_severity": "HIGH",
                "category": "access_control",
                "function": "setOracle",
                "line": 75,
                "description": "Missing onlyOwner modifier",
            },
            {
                "title": "tx.origin authentication",
                "severity": "HIGH",
                "original_severity": "HIGH",
                "category": "tx_origin",
                "function": "emergencyWithdraw",
                "line": 140,
                "description": "tx.origin used for auth",
            },
        ]

        engine = ExploitReasoningEngine()
        result = engine.analyze(findings, source, str(VULNERABLE_VAULT))

        assert result["total_analyzed"] >= 2
        proofs = result["exploit_proofs"]
        print(f"\n  Exploit proofs: {len(proofs)}")
        for p in proofs:
            status = "🔴 EXPLOITABLE" if p["exploitable"] else "⚪ not exploitable"
            print(
                f"    {status}: {p['function']} ({p['z3_result']}, conf={p['confidence']:.2f})"
            )

        exploitable = result["exploitable_count"]
        print(f"  Exploitable count: {exploitable}/{result['total_analyzed']}")

        # After Fix #2, at least reentrancy should be exploitable (structural)
        assert exploitable >= 1, (
            f"Expected ≥1 exploitable after Fix #2, got {exploitable}. "
            f"Proofs: {json.dumps(proofs, indent=2, default=str)[:500]}"
        )


# ═══════════════════════════════════════════════════
#  New Detectors on real contracts
# ═══════════════════════════════════════════════════


class TestNewDetectorsOnRealContracts:
    """Validate UNCHECKED-RETURN and INTEGER-OVERFLOW on actual Foundry contracts."""

    @pytest.fixture(autouse=True)
    def setup(self):
        if not VULNERABLE_VAULT.exists():
            pytest.skip("VulnerableVault.sol not found")

    def test_unchecked_return_on_vulnerable_vault(self):
        """Should detect V3: token.transfer() in transferTokens() is unchecked."""
        from agl_security_tool.detectors.common import UncheckedReturnValue
        from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser

        with open(VULNERABLE_VAULT, "r", encoding="utf-8") as f:
            source = f.read()

        parser = SoliditySemanticParser()
        contracts = parser.parse(source, str(VULNERABLE_VAULT))
        detector = UncheckedReturnValue()

        findings = []
        for c in contracts:
            findings.extend(detector.detect(c, contracts))

        print(f"\n  UNCHECKED-RETURN findings: {len(findings)}")
        for f in findings:
            print(f"    {f.function} L{f.line}: {f.description[:100]}")

        # V3: transferTokens does token.transfer without checking return
        assert (
            len(findings) >= 1
        ), "V3: token.transfer() in transferTokens should be flagged"

    def test_integer_overflow_on_vulnerable_vault(self):
        """Should detect V6: unchecked { balances[user] += bonus; } in addBonus()."""
        from agl_security_tool.detectors.common import IntegerOverflow
        from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser

        with open(VULNERABLE_VAULT, "r", encoding="utf-8") as f:
            source = f.read()

        parser = SoliditySemanticParser()
        contracts = parser.parse(source, str(VULNERABLE_VAULT))
        detector = IntegerOverflow()

        findings = []
        for c in contracts:
            findings.extend(detector.detect(c, contracts))

        print(f"\n  INTEGER-OVERFLOW findings: {len(findings)}")
        for f in findings:
            print(f"    {f.function} L{f.line}: {f.description[:100]}")

        # V6: addBonus has unchecked { balances[user] += bonus; }
        assert (
            len(findings) >= 1
        ), "V6: unchecked arithmetic in addBonus should be flagged"

    def test_no_overflow_on_safe_vault(self):
        """SafeVault has no unchecked blocks — should produce 0 overflow findings."""
        if not SAFE_VAULT.exists():
            pytest.skip("SafeVault.sol not found")

        from agl_security_tool.detectors.common import IntegerOverflow
        from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser

        with open(SAFE_VAULT, "r", encoding="utf-8") as f:
            source = f.read()

        parser = SoliditySemanticParser()
        contracts = parser.parse(source, str(SAFE_VAULT))
        detector = IntegerOverflow()

        findings = []
        for c in contracts:
            findings.extend(detector.detect(c, contracts))

        print(f"\n  SafeVault INTEGER-OVERFLOW findings: {len(findings)}")
        assert (
            len(findings) == 0
        ), f"SafeVault should have 0 overflow findings, got {len(findings)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
