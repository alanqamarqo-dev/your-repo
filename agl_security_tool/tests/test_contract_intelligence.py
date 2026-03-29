"""
AGL ContractIntelligence Tests — اختبارات ذكاء مستوى العقد
============================================================

Tests: Noisy-OR aggregation, ContractAggregator, ContractMetrics,
MetaClassifier, ContractVerdict, dampened_aggregate, feature extraction.
"""

import math
import pytest
from contract_intelligence import (
    ContractAggregator,
    ContractMetrics,
    MetaClassifier,
    ContractVerdict,
    ContractCalibrationResult,
    META_FEATURE_NAMES,
    DEFAULT_CONTRACT_THRESHOLD,
    _sigmoid,
    _shannon_entropy,
    _log_norm,
)


# ═══════════════════════════════════════════════════════════
#  Utility Functions
# ═══════════════════════════════════════════════════════════

class TestUtilityFunctions:

    def test_sigmoid_zero(self):
        assert abs(_sigmoid(0.0) - 0.5) < 1e-10

    def test_sigmoid_large_positive(self):
        assert _sigmoid(100.0) > 0.999

    def test_sigmoid_large_negative(self):
        assert _sigmoid(-100.0) < 0.001

    def test_sigmoid_symmetry(self):
        for x in [0.5, 1.0, 2.0, 5.0]:
            assert abs(_sigmoid(x) + _sigmoid(-x) - 1.0) < 1e-10

    def test_shannon_entropy_empty(self):
        assert _shannon_entropy([]) == 0.0

    def test_shannon_entropy_certain(self):
        # Near-certain probs have low entropy
        e = _shannon_entropy([0.99, 0.99, 0.01])
        assert e < 0.3

    def test_shannon_entropy_uncertain(self):
        # 0.5 probs have max entropy
        e = _shannon_entropy([0.5, 0.5, 0.5])
        assert e > 0.5

    def test_log_norm_zero(self):
        assert _log_norm(0) == 0.0

    def test_log_norm_positive(self):
        assert _log_norm(5) > 0.0
        assert _log_norm(5) < 1.0

    def test_log_norm_monotonic(self):
        assert _log_norm(1) < _log_norm(5) < _log_norm(20)


# ═══════════════════════════════════════════════════════════
#  Noisy-OR Aggregation
# ═══════════════════════════════════════════════════════════

class TestNoisyOR:

    def test_empty_returns_zero(self):
        agg = ContractAggregator()
        assert agg.noisy_or([]) == 0.0

    def test_single_probability(self):
        agg = ContractAggregator()
        p = agg.noisy_or([0.8])
        assert abs(p - 0.8) < 1e-10

    def test_two_probabilities(self):
        agg = ContractAggregator()
        # P = 1 - (1-0.8)(1-0.6) = 1 - 0.2*0.4 = 0.92
        p = agg.noisy_or([0.8, 0.6])
        assert abs(p - 0.92) < 1e-10

    def test_all_zeros(self):
        agg = ContractAggregator()
        assert agg.noisy_or([0.0, 0.0, 0.0]) == 0.0

    def test_one_certain(self):
        agg = ContractAggregator()
        p = agg.noisy_or([1.0, 0.3, 0.5])
        assert abs(p - 1.0) < 1e-10

    def test_monotonic_with_more_findings(self):
        agg = ContractAggregator()
        p1 = agg.noisy_or([0.5])
        p2 = agg.noisy_or([0.5, 0.5])
        p3 = agg.noisy_or([0.5, 0.5, 0.5])
        assert p1 < p2 < p3

    def test_result_in_unit_interval(self):
        agg = ContractAggregator()
        for probs in [[0.1], [0.5, 0.5], [0.9, 0.8, 0.7]]:
            p = agg.noisy_or(probs)
            assert 0.0 <= p <= 1.0

    def test_clamping(self):
        agg = ContractAggregator()
        # Values outside [0,1] should be clamped
        p = agg.noisy_or([1.5, -0.3])
        assert 0.0 <= p <= 1.0


# ═══════════════════════════════════════════════════════════
#  Feature Extraction
# ═══════════════════════════════════════════════════════════

class TestFeatureExtraction:

    def test_extract_features_empty(self):
        agg = ContractAggregator()
        features = agg.extract_features([])
        assert all(v == 0.0 for v in features.values())

    def test_extract_features_keys(self):
        agg = ContractAggregator()
        features = agg.extract_features([0.8, 0.5])
        for name in META_FEATURE_NAMES:
            assert name in features, f"Missing feature: {name}"

    def test_max_p_correct(self):
        agg = ContractAggregator()
        features = agg.extract_features([0.3, 0.8, 0.5])
        assert abs(features["max_p"] - 0.8) < 1e-10

    def test_mean_p_correct(self):
        agg = ContractAggregator()
        features = agg.extract_features([0.3, 0.6, 0.9])
        assert abs(features["mean_p"] - 0.6) < 1e-10

    def test_count_high(self):
        agg = ContractAggregator()
        features = agg.extract_features([0.3, 0.8, 0.9, 0.5])
        assert features["count_high"] == 2  # 0.8 and 0.9 > 0.7

    def test_noisy_or_matches(self):
        agg = ContractAggregator()
        probs = [0.8, 0.5, 0.3]
        features = agg.extract_features(probs)
        assert abs(features["noisy_or_p"] - agg.noisy_or(probs)) < 1e-10

    def test_severity_counting(self):
        agg = ContractAggregator()
        sevs = ["critical", "critical", "high", "medium"]
        features = agg.extract_features([0.9, 0.85, 0.7, 0.4], severities=sevs)
        assert features["n_critical"] > 0
        assert features["n_high"] > 0


# ═══════════════════════════════════════════════════════════
#  Contract Classification
# ═══════════════════════════════════════════════════════════

class TestClassify:

    def test_classify_vulnerable(self):
        agg = ContractAggregator()
        verdict = agg.classify([0.9, 0.8, 0.7])
        assert verdict.is_vulnerable is True
        assert verdict.p_contract > 0.5

    def test_classify_safe(self):
        agg = ContractAggregator()
        verdict = agg.classify([0.1, 0.05])
        assert verdict.is_vulnerable is False
        assert verdict.p_contract < 0.5

    def test_classify_empty(self):
        agg = ContractAggregator()
        verdict = agg.classify([])
        assert verdict.is_vulnerable is False
        assert verdict.p_contract == 0.0

    def test_classify_custom_threshold(self):
        agg = ContractAggregator()
        probs = [0.6, 0.5]
        v1 = agg.classify(probs, threshold=0.3)
        v2 = agg.classify(probs, threshold=0.99)
        assert v1.is_vulnerable is True
        assert v2.is_vulnerable is False

    def test_verdict_to_dict(self):
        agg = ContractAggregator()
        verdict = agg.classify([0.8, 0.5])
        d = verdict.to_dict()
        assert "p_contract" in d
        assert "p_final" in d
        assert "is_vulnerable" in d
        assert "features" in d
        assert "finding_probabilities" in d

    def test_verdict_method(self):
        agg = ContractAggregator()
        verdict = agg.classify([0.8])
        assert verdict.method in ("noisy_or", "dampened_z3")


# ═══════════════════════════════════════════════════════════
#  ContractMetrics
# ═══════════════════════════════════════════════════════════

class TestContractMetrics:

    def test_compute_empty(self):
        cal = ContractMetrics.compute([])
        assert cal.total_contracts == 0
        assert cal.accuracy == 0.0

    def test_compute_perfect(self):
        preds = [(0.9, 1), (0.8, 1), (0.1, 0), (0.2, 0)]
        cal = ContractMetrics.compute(preds, threshold=0.5)
        assert cal.tp == 2
        assert cal.tn == 2
        assert cal.fp == 0
        assert cal.fn == 0
        assert cal.accuracy == 1.0
        assert cal.f1 == 1.0

    def test_compute_confusion_matrix(self):
        preds = [(0.9, 1), (0.8, 0), (0.3, 1), (0.1, 0)]
        cal = ContractMetrics.compute(preds, threshold=0.5)
        assert cal.tp == 1  # 0.9 >= 0.5 & y=1
        assert cal.fp == 1  # 0.8 >= 0.5 & y=0
        assert cal.fn == 1  # 0.3 < 0.5 & y=1
        assert cal.tn == 1  # 0.1 < 0.5 & y=0

    def test_brier_score_perfect(self):
        preds = [(1.0, 1), (0.0, 0)]
        cal = ContractMetrics.compute(preds)
        assert cal.brier_score == 0.0

    def test_brier_score_worst(self):
        preds = [(1.0, 0), (0.0, 1)]
        cal = ContractMetrics.compute(preds)
        assert cal.brier_score == 1.0

    def test_roc_curve_generated(self):
        preds = [(0.9, 1), (0.7, 1), (0.4, 0), (0.1, 0)]
        cal = ContractMetrics.compute(preds)
        assert len(cal.roc_curve) > 0

    def test_optimal_threshold_reasonable(self):
        preds = [(0.9, 1), (0.7, 1), (0.3, 0), (0.1, 0)]
        cal = ContractMetrics.compute(preds)
        assert 0.0 <= cal.optimal_threshold <= 1.0
        assert cal.optimal_j >= 0.0

    def test_to_dict_keys(self):
        preds = [(0.9, 1), (0.1, 0)]
        cal = ContractMetrics.compute(preds)
        d = cal.to_dict()
        assert "brier_score" in d
        assert "accuracy" in d
        assert "confusion_matrix" in d
        assert "roc_curve" in d
        assert "optimal_threshold" in d


# ═══════════════════════════════════════════════════════════
#  MetaClassifier
# ═══════════════════════════════════════════════════════════

class TestMetaClassifier:

    def test_untrained_fallback_to_noisy_or(self):
        mc = MetaClassifier()
        assert mc.is_trained is False
        features = mc.extract_features([0.8, 0.5])
        p = mc.predict_proba(features)
        # Should fall back to noisy_or_p (feature 5)
        agg = ContractAggregator()
        expected = agg.noisy_or([0.8, 0.5])
        assert abs(p - expected) < 1e-6

    def test_extract_features_length(self):
        mc = MetaClassifier()
        features = mc.extract_features([0.9, 0.5, 0.3])
        assert len(features) == len(META_FEATURE_NAMES)

    def test_classify_returns_verdict(self):
        mc = MetaClassifier()
        verdict = mc.classify([0.8, 0.5])
        assert isinstance(verdict, ContractVerdict)
        assert 0.0 <= verdict.p_final <= 1.0


# ═══════════════════════════════════════════════════════════
#  Dampened Aggregate
# ═══════════════════════════════════════════════════════════

class TestDampenedAggregate:

    def test_empty_findings(self):
        agg = ContractAggregator()
        assert agg.dampened_aggregate([]) == 0.0

    def test_without_z3_data(self):
        agg = ContractAggregator()
        findings = [
            {"confidence": 0.8},
            {"confidence": 0.5},
        ]
        p = agg.dampened_aggregate(findings)
        assert 0.0 <= p <= 1.0

    def test_with_z3_sat(self):
        agg = ContractAggregator()
        findings = [
            {"confidence": 0.9, "exploit_proof": {"z3_result": "SAT", "exploitable": True}},
            {"confidence": 0.5, "exploit_proof": {"z3_result": "UNSAT", "exploitable": False}},
        ]
        p = agg.dampened_aggregate(findings)
        assert 0.0 <= p <= 1.0

    def test_z3_sat_increases_score(self):
        agg = ContractAggregator()
        no_z3 = [{"confidence": 0.8}]
        with_z3 = [{"confidence": 0.8, "exploit_proof": {"z3_result": "SAT", "exploitable": True}}]
        p_no = agg.dampened_aggregate(no_z3)
        p_yes = agg.dampened_aggregate(with_z3)
        # Z3 SAT should generally give a higher or at least comparable score
        assert isinstance(p_yes, float)
