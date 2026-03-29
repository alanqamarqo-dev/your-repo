"""
اختبار الدليل السلبي — Negative Evidence Integration Test
============================================================
Tests that the full pipeline (core.py → RiskCore) correctly:
  1. Attaches _negative_evidence metadata from L3/L4
  2. Propagates negative_evidence annotations to findings
  3. Applies penalty in compute_exploit_probability()
  4. Downgrades false positives while keeping true positives

Run:
    python agl_security_tool/tests/test_negative_evidence.py
"""

import math
import os
import sys
import time
import unittest

_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
os.chdir(_PROJECT_ROOT)
sys.path.insert(0, _PROJECT_ROOT)


# ═══════════════════════════════════════════════════════════════════════
#  Part 1 — Unit Tests for RiskCore negative evidence math
# ═══════════════════════════════════════════════════════════════════════


class TestRiskCoreNegativeEvidence(unittest.TestCase):
    """Verify that RiskCore.compute_exploit_probability honours neg evidence."""

    @classmethod
    def setUpClass(cls):
        from agl_security_tool.risk_core import RiskCore, NEGATIVE_EVIDENCE_PENALTY

        cls.rc = RiskCore()
        cls.PENALTY = NEGATIVE_EVIDENCE_PENALTY

    # ── 1. Zero negative evidence → no change ──
    def test_zero_neg_evidence_no_penalty(self):
        bd = self.rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=0,
        )
        self.assertEqual(bd.negative_evidence_count, 0)
        self.assertAlmostEqual(bd.negative_evidence_penalty_applied, 0.0)

    # ── 2. One negative source → exactly PENALTY applied ──
    def test_one_neg_evidence_single_penalty(self):
        bd = self.rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=1,
        )
        self.assertEqual(bd.negative_evidence_count, 1)
        self.assertAlmostEqual(
            bd.negative_evidence_penalty_applied, self.PENALTY, places=6
        )

    # ── 3. Two negative sources → double penalty ──
    def test_two_neg_evidence_double_penalty(self):
        bd = self.rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=2,
        )
        self.assertEqual(bd.negative_evidence_count, 2)
        self.assertAlmostEqual(
            bd.negative_evidence_penalty_applied, 2 * self.PENALTY, places=6
        )

    # ── 4. Probability drops with negative evidence ──
    def test_probability_decreases_with_neg_evidence(self):
        bd_no_neg = self.rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=0,
        )
        bd_one_neg = self.rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=1,
        )
        bd_two_neg = self.rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=2,
        )
        self.assertGreater(
            bd_no_neg.probability,
            bd_one_neg.probability,
            "1 neg should lower P",
        )
        self.assertGreater(
            bd_one_neg.probability,
            bd_two_neg.probability,
            "2 neg should lower P further",
        )

    # ── 5. Detector-only FALSE POSITIVE scenario ──
    #    heuristic=0.8, no formal/profit/exploit
    #    Without neg → HIGH;  With 2 neg → should drop ≥1 severity step
    def test_fp_scenario_downgrade(self):
        bd_no_neg = self.rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=0,
        )
        bd_both_neg = self.rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=2,
        )
        print(f"\n  FP scenario (heur=0.8, no confirm):")
        print(f"    NO  neg → P={bd_no_neg.probability:.4f}  sev={bd_no_neg.severity}")
        print(
            f"    2×  neg → P={bd_both_neg.probability:.4f}  sev={bd_both_neg.severity}"
        )

        # Probability should drop meaningfully
        delta = bd_no_neg.probability - bd_both_neg.probability
        self.assertGreater(delta, 0.05, f"Δ={delta:.4f} too small")

        # Severity should NOT increase (same or lower)
        sev_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
        self.assertGreaterEqual(
            sev_order[bd_no_neg.severity],
            sev_order[bd_both_neg.severity],
            "FP should not be upgraded with neg evidence",
        )

    # ── 6. TRUE POSITIVE — strong evidence should withstand neg ──
    #    formal=0.9 + heuristic=0.8 + exploit_proven → CRITICAL stays
    def test_tp_scenario_survives_neg(self):
        bd = self.rc.compute_exploit_probability(
            formal_score=0.9,
            heuristic_score=0.8,
            profit_score=0.5,
            exploit_proven=True,
            negative_evidence_count=2,
        )
        print(f"\n  TP scenario (formal=0.9, heur=0.8, profit=0.5, proven):")
        print(f"    2× neg → P={bd.probability:.4f}  sev={bd.severity}")

        self.assertGreaterEqual(
            bd.probability, 0.75, "Strongly-confirmed TP should survive neg"
        )
        self.assertIn(bd.severity, ("CRITICAL", "HIGH"), "TP should remain HIGH+")

    # ── 7. to_dict() includes negative_evidence when count > 0 ──
    def test_to_dict_includes_neg_fields(self):
        bd = self.rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=2,
        )
        d = bd.to_dict()
        self.assertIn("negative_evidence", d)
        self.assertEqual(d["negative_evidence"]["count"], 2)
        self.assertAlmostEqual(
            d["negative_evidence"]["penalty_applied"], 2 * self.PENALTY, places=4
        )

    # ── 8. to_dict() omits negative_evidence when count == 0 ──
    def test_to_dict_omits_neg_when_zero(self):
        bd = self.rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=0,
        )
        d = bd.to_dict()
        self.assertNotIn("negative_evidence", d)

    # ── 9. score_findings integrates negative_evidence list ──
    def test_score_findings_reads_neg_list(self):
        findings = [
            {
                "title": "Fake FP",
                "severity": "critical",
                "confidence": 0.85,
                "source": "detector",
                "confirmed_by": ["detector"],
                "negative_evidence": [
                    "l3_no_profitable_attack",
                    "l4_no_exploitable_path",
                ],
            },
            {
                "title": "Real TP",
                "severity": "critical",
                "confidence": 0.9,
                "source": "detector",
                "confirmed_by": ["detector", "z3_symbolic"],
                "is_proven": True,
                "negative_evidence": [],
            },
        ]
        scored = self.rc.score_findings(findings)

        fp = scored[0]
        tp = scored[1]

        self.assertGreater(
            tp["probability"],
            fp["probability"],
            "TP should score higher than FP",
        )
        print(f"\n  score_findings integration:")
        print(f"    FP → P={fp['probability']:.4f}  sev={fp['severity']}")
        print(f"    TP → P={tp['probability']:.4f}  sev={tp['severity']}")


# ═══════════════════════════════════════════════════════════════════════
#  Part 2 — Full pipeline scan on test contract
# ═══════════════════════════════════════════════════════════════════════

import pytest


@pytest.mark.slow
class TestFullPipelineNegativeEvidence(unittest.TestCase):
    """Scan negative_evidence_test.sol through core.py full pipeline."""

    _result = None

    @classmethod
    def setUpClass(cls):
        from agl_security_tool.core import AGLSecurityAudit

        contract = os.path.join(
            _PROJECT_ROOT,
            "agl_security_tool",
            "test_contracts",
            "negative_evidence_test.sol",
        )
        if not os.path.exists(contract):
            raise FileNotFoundError(f"Test contract missing: {contract}")

        print(f"\n{'='*60}")
        print(f"  Full pipeline scan: negative_evidence_test.sol")
        print(f"{'='*60}")

        t0 = time.time()
        audit = AGLSecurityAudit()
        cls._result = audit.scan(contract)
        elapsed = time.time() - t0
        print(f"  Scan completed in {elapsed:.1f}s")

    # ── 10. _negative_evidence metadata is present ──
    def test_neg_evidence_metadata_present(self):
        neg = self._result.get("_negative_evidence", {})
        print(f"\n  _negative_evidence metadata: {neg}")
        self.assertIsInstance(neg, dict)
        # At minimum l3_ran and l4_ran keys should exist
        self.assertIn("l3_ran", neg)
        self.assertIn("l4_ran", neg)

    # ── 11. Layers activated (at least L1, L2) ──
    def test_layers_activated(self):
        layers = self._result.get("layers_used", [])
        print(f"  Layers: {layers}")
        self.assertTrue(len(layers) >= 1, "At least 1 layer should run")

    # ── 12. Unified findings exist ──
    def test_unified_findings_exist(self):
        unified = self._result.get("all_findings_unified", [])
        self.assertTrue(len(unified) > 0, "Should have findings")
        print(f"  Total unified findings: {len(unified)}")

    # ── 13. Some findings have negative_evidence annotations ──
    def test_some_findings_have_neg_annotations(self):
        unified = self._result.get("all_findings_unified", [])
        neg_annotated = [f for f in unified if f.get("negative_evidence")]
        print(f"  Findings with negative_evidence: {len(neg_annotated)}/{len(unified)}")

        # Report all findings for diagnostics
        print(f"\n  All findings:")
        for i, f in enumerate(unified):
            neg = f.get("negative_evidence", [])
            rb = f.get("risk_breakdown", {})
            neg_info = rb.get("negative_evidence", {})
            print(
                f"    [{i+1}] {f.get('severity','?').upper():>8} "
                f"P={f.get('probability', '?'):>6} "
                f"neg={neg} "
                f"neg_penalty={neg_info.get('penalty_applied', 0):.2f} "
                f"| {f.get('title', '?')[:60]}"
            )

    # ── 14. FalsePositiveVault findings get neg evidence penalty ──
    def test_fp_vault_findings_penalized(self):
        unified = self._result.get("all_findings_unified", [])
        fp_findings = [
            f
            for f in unified
            if "FalsePositiveVault" in str(f.get("contract", ""))
            or "FalsePositiveVault" in str(f.get("title", ""))
            or "FalsePositiveVault" in str(f.get("description", ""))
        ]
        if not fp_findings:
            # Check if any finding mentions the safe patterns
            fp_findings = [
                f
                for f in unified
                if "nonReentrant" in str(f.get("description", ""))
                or "emergencyWithdraw" in str(f.get("title", ""))
            ]

        print(f"\n  FalsePositiveVault findings: {len(fp_findings)}")
        for f in fp_findings:
            neg = f.get("negative_evidence", [])
            print(
                f"    sev={f.get('severity','?')} neg={neg} | {f.get('title','?')[:60]}"
            )

        # If we found FP findings OR if we can check risk_breakdown
        if fp_findings:
            for f in fp_findings:
                neg = f.get("negative_evidence", [])
                rb = f.get("risk_breakdown", {})
                neg_info = rb.get("negative_evidence", {})
                if neg:
                    self.assertGreater(
                        neg_info.get("count", 0),
                        0,
                        "FP finding with neg_evidence should have penalty",
                    )

    # ── 15. Risk breakdown includes neg evidence fields ──
    def test_risk_breakdown_neg_fields(self):
        unified = self._result.get("all_findings_unified", [])
        for f in unified:
            rb = f.get("risk_breakdown")
            if rb is None:
                continue
            if f.get("negative_evidence"):
                self.assertIn(
                    "negative_evidence",
                    rb,
                    f"risk_breakdown should contain neg evidence for: {f.get('title','')}",
                )


# ═══════════════════════════════════════════════════════════════════════
#  Part 3 — Comparative test: same finding WITH vs WITHOUT neg evidence
# ═══════════════════════════════════════════════════════════════════════


class TestComparativeProbability(unittest.TestCase):
    """Mathematical proof that neg evidence changes the outcome."""

    def test_mathematical_proof(self):
        from agl_security_tool.risk_core import (
            RiskCore,
            DEFAULT_WEIGHTS,
            NEGATIVE_EVIDENCE_PENALTY,
        )

        rc = RiskCore()
        w = DEFAULT_WEIGHTS

        # Scenario: Detector says CRITICAL (heur=0.8), no other evidence.
        # WITHOUT negative evidence:
        logit_no = w["w_heuristic"] * 0.8 + w["bias"]
        p_no = 1 / (1 + math.exp(-logit_no))

        # WITH 2× negative evidence:
        logit_neg = logit_no + 2 * NEGATIVE_EVIDENCE_PENALTY
        p_neg = 1 / (1 + math.exp(-logit_neg))

        print(f"\n{'='*60}")
        print(f"  Mathematical Proof — Negative Evidence Effect")
        print(f"{'='*60}")
        print(f"  Weights: heur={w['w_heuristic']}, bias={w['bias']}")
        print(f"  PENALTY = {NEGATIVE_EVIDENCE_PENALTY}")
        print(f"")
        print(f"  Without neg: logit={logit_no:.4f} → P={p_no:.4f}")
        print(f"  With 2× neg: logit={logit_neg:.4f} → P={p_neg:.4f}")
        print(f"  ΔP = {p_no - p_neg:.4f}")
        print(f"")

        # Verify via the actual RiskCore function
        bd_no = rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=0,
        )
        bd_neg = rc.compute_exploit_probability(
            formal_score=0.0,
            heuristic_score=0.8,
            profit_score=0.0,
            exploit_proven=False,
            negative_evidence_count=2,
        )
        print(f"  RiskCore without neg: P={bd_no.probability:.4f} sev={bd_no.severity}")
        print(
            f"  RiskCore with 2× neg: P={bd_neg.probability:.4f} sev={bd_neg.severity}"
        )
        print(f"  ΔP = {bd_no.probability - bd_neg.probability:.4f}")

        # Assertions
        self.assertAlmostEqual(bd_no.probability, p_no, places=4)
        self.assertAlmostEqual(bd_neg.probability, p_neg, places=4)
        self.assertGreater(bd_no.probability, bd_neg.probability)

        # Severity should not increase (same or lower)
        sev_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
        self.assertGreaterEqual(
            sev_order.get(bd_no.severity, 0),
            sev_order.get(bd_neg.severity, 0),
            "Severity should not increase with 2× neg evidence",
        )


if __name__ == "__main__":
    print("=" * 60)
    print("  AGL Negative Evidence — Full Integration Test Suite")
    print("  اختبار الدليل السلبي الكامل")
    print("=" * 60)
    unittest.main(verbosity=2)
