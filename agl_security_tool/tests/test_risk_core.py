"""
AGL RiskCore Tests — اختبارات نواة المخاطر
=============================================

Tests the unified probabilistic risk equation:
  P(exploit) = σ(w_f·S_f + w_h·S_h + w_p·S_p + w_e·E + β)

Validates: probability math, severity mapping, weight sanity,
negative evidence, batch scoring, serialization.
"""

import math
import pytest
from risk_core import (
    RiskCore,
    RiskBreakdown,
    DEFAULT_WEIGHTS,
    SEVERITY_THRESHOLDS,
    NEGATIVE_EVIDENCE_PENALTY,
    SEVERITY_MULTIPLIER,
)


def sigmoid(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    else:
        z = math.exp(x)
        return z / (1.0 + z)


class TestRiskCoreInit:
    """Test initialization and weight loading."""

    def test_default_weights(self):
        rc = RiskCore(auto_load=False)
        assert rc.weights["w_formal"] == DEFAULT_WEIGHTS["w_formal"]
        assert rc.weights["w_heuristic"] == DEFAULT_WEIGHTS["w_heuristic"]
        assert rc.weights["bias"] == DEFAULT_WEIGHTS["bias"]

    def test_custom_weights(self):
        rc = RiskCore(weights={"w_formal": 5.0, "bias": -1.0}, auto_load=False)
        assert rc.weights["w_formal"] == 5.0
        assert rc.weights["bias"] == -1.0
        # Others should remain default
        assert rc.weights["w_exploit"] == DEFAULT_WEIGHTS["w_exploit"]

    def test_weights_are_sane_valid(self):
        assert RiskCore._weights_are_sane(DEFAULT_WEIGHTS) is True

    def test_weights_are_sane_negative_formal(self):
        bad = dict(DEFAULT_WEIGHTS, w_formal=-1.0)
        assert RiskCore._weights_are_sane(bad) is False

    def test_weights_are_sane_negative_exploit(self):
        bad = dict(DEFAULT_WEIGHTS, w_exploit=-0.5)
        assert RiskCore._weights_are_sane(bad) is False

    def test_weights_are_sane_negative_heuristic(self):
        bad = dict(DEFAULT_WEIGHTS, w_heuristic=-0.1)
        assert RiskCore._weights_are_sane(bad) is False

    def test_weights_are_sane_collapsed(self):
        bad = {"w_formal": 0.01, "w_heuristic": 0.01, "w_profit": 0.01,
               "w_exploit": 0.01, "bias": 0.0}
        assert RiskCore._weights_are_sane(bad) is False


class TestCoreEquation:
    """Test the main probability equation."""

    def test_zero_evidence_low_probability(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.0, 0.0, 0.0, False)
        assert bd.probability < 0.5, "Zero evidence should give P < 0.5"
        assert bd.severity in ("INFO", "LOW")

    def test_full_exploit_proven_high_probability(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.95, 0.9, 0.8, True)
        assert bd.probability > 0.9, f"Full evidence P={bd.probability} should be > 0.9"
        assert bd.severity == "CRITICAL"

    def test_heuristic_only_medium(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.0, 0.7, 0.0, False)
        assert 0.3 < bd.probability < 0.8
        assert bd.severity in ("MEDIUM", "HIGH", "LOW")

    def test_formal_proof_high(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.95, 0.5, 0.0, False)
        assert bd.probability > 0.7

    def test_monotonicity_more_evidence_higher_p(self):
        rc = RiskCore(auto_load=False)
        p1 = rc.compute_exploit_probability(0.0, 0.5, 0.0, False).probability
        p2 = rc.compute_exploit_probability(0.5, 0.5, 0.0, False).probability
        p3 = rc.compute_exploit_probability(0.5, 0.5, 0.5, False).probability
        p4 = rc.compute_exploit_probability(0.5, 0.5, 0.5, True).probability
        assert p1 < p2 < p3 < p4, f"Monotonicity failed: {p1} < {p2} < {p3} < {p4}"

    def test_probability_bounded_0_1(self):
        rc = RiskCore(auto_load=False)
        for f in [0.0, 0.5, 1.0]:
            for h in [0.0, 0.5, 1.0]:
                for p in [0.0, 0.5, 1.0]:
                    for e in [False, True]:
                        bd = rc.compute_exploit_probability(f, h, p, e)
                        assert 0.0 <= bd.probability <= 1.0

    def test_logit_math_matches(self):
        rc = RiskCore(auto_load=False)
        w = rc.weights
        bd = rc.compute_exploit_probability(0.8, 0.6, 0.4, False)
        expected_logit = (
            w["w_formal"] * 0.8
            + w["w_heuristic"] * 0.6
            + w["w_profit"] * 0.4
            + w["w_exploit"] * 0.0
            + math.log(1) * 0.3  # source_bonus for source_count=1
            + w["bias"]
        )
        assert abs(bd.raw_logit - expected_logit) < 1e-6

    def test_input_clamping(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(2.0, -0.5, 1.5, False)
        assert bd.formal_score == 1.0
        assert bd.heuristic_score == 0.0
        assert bd.profit_score == 1.0


class TestSeverityMapping:
    """Test severity derivation from probability."""

    def test_critical_threshold(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(1.0, 1.0, 1.0, True)
        assert bd.severity == "CRITICAL"

    def test_info_threshold(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.0, 0.0, 0.0, False)
        assert bd.severity in ("INFO", "LOW")

    def test_severity_thresholds_order(self):
        # Thresholds must be in descending order
        for i in range(len(SEVERITY_THRESHOLDS) - 1):
            assert SEVERITY_THRESHOLDS[i][0] > SEVERITY_THRESHOLDS[i + 1][0]


class TestNegativeEvidence:
    """Test negative evidence penalty."""

    def test_negative_evidence_reduces_p(self):
        rc = RiskCore(auto_load=False)
        p_no_neg = rc.compute_exploit_probability(0.0, 0.7, 0.0, False,
                                                   negative_evidence_count=0).probability
        p_neg_1 = rc.compute_exploit_probability(0.0, 0.7, 0.0, False,
                                                  negative_evidence_count=1).probability
        p_neg_2 = rc.compute_exploit_probability(0.0, 0.7, 0.0, False,
                                                  negative_evidence_count=2).probability
        assert p_no_neg > p_neg_1 > p_neg_2

    def test_negative_evidence_penalty_applied(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.0, 0.7, 0.0, False,
                                            negative_evidence_count=2)
        expected_penalty = 2 * NEGATIVE_EVIDENCE_PENALTY
        assert abs(bd.negative_evidence_penalty_applied - expected_penalty) < 1e-6

    def test_negative_evidence_in_breakdown(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.0, 0.7, 0.0, False,
                                            negative_evidence_count=1)
        assert bd.negative_evidence_count == 1
        d = bd.to_dict()
        assert "negative_evidence" in d


class TestMultiSourceBonus:
    """Test source_count confirmation bonus."""

    def test_multi_source_increases_p(self):
        rc = RiskCore(auto_load=False)
        p1 = rc.compute_exploit_probability(0.0, 0.5, 0.0, False,
                                            source_count=1).probability
        p3 = rc.compute_exploit_probability(0.0, 0.5, 0.0, False,
                                            source_count=3).probability
        assert p3 > p1

    def test_source_bonus_diminishing(self):
        rc = RiskCore(auto_load=False)
        p2 = rc.compute_exploit_probability(0.0, 0.5, 0.0, False, source_count=2).probability
        p5 = rc.compute_exploit_probability(0.0, 0.5, 0.0, False, source_count=5).probability
        p10 = rc.compute_exploit_probability(0.0, 0.5, 0.0, False, source_count=10).probability
        delta_2_5 = p5 - p2
        delta_5_10 = p10 - p5
        assert delta_5_10 < delta_2_5  # Diminishing returns


class TestInfluencePercentages:
    """Test explainability percentages."""

    def test_influence_sums_to_100(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.5, 0.5, 0.5, True)
        total = (bd.formal_influence_pct + bd.heuristic_influence_pct +
                 bd.profit_influence_pct + bd.exploit_influence_pct)
        assert abs(total - 100.0) < 5.0  # Allow for source_bonus rounding

    def test_formal_dominant_when_proven(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.95, 0.1, 0.0, False)
        assert bd.formal_influence_pct > bd.heuristic_influence_pct


class TestRiskBreakdownSerialization:
    """Test to_dict output."""

    def test_to_dict_keys(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.5, 0.5, 0.0, False)
        d = bd.to_dict()
        assert "probability" in d
        assert "severity" in d
        assert "formal_score" in d
        assert "heuristic_score" in d
        assert "influence" in d
        assert "sources" in d

    def test_to_dict_negative_evidence_omitted_when_zero(self):
        rc = RiskCore(auto_load=False)
        bd = rc.compute_exploit_probability(0.5, 0.5, 0.0, False,
                                            negative_evidence_count=0)
        d = bd.to_dict()
        assert "negative_evidence" not in d


class TestBatchScoring:
    """Test score_findings batch method."""

    def test_score_findings_adds_breakdown(self):
        rc = RiskCore(auto_load=False)
        findings = [
            {"confidence": 0.9, "severity": "high", "confirmed_by": ["detector"],
             "source": "heuristic"},
            {"confidence": 0.5, "severity": "medium", "confirmed_by": ["detector"],
             "source": "heuristic"},
        ]
        scored = rc.score_findings(findings)
        assert len(scored) == 2
        for s in scored:
            assert "risk_breakdown" in s

    def test_score_findings_with_z3_proven(self):
        rc = RiskCore(auto_load=False)
        findings = [
            {"confidence": 0.95, "severity": "high", "confirmed_by": ["z3"],
             "is_proven": True, "source": "z3_symbolic"},
        ]
        scored = rc.score_findings(findings)
        assert len(scored) == 1
        bd = scored[0]["risk_breakdown"]
        assert bd["formal_score"] > 0


class TestSeverityMultiplier:
    """Test severity multiplier constants."""

    def test_critical_highest(self):
        assert SEVERITY_MULTIPLIER["critical"] >= SEVERITY_MULTIPLIER["high"]

    def test_info_lowest(self):
        assert SEVERITY_MULTIPLIER["info"] <= SEVERITY_MULTIPLIER["low"]

    def test_all_positive(self):
        for k, v in SEVERITY_MULTIPLIER.items():
            assert v > 0, f"Multiplier for {k} should be positive"
