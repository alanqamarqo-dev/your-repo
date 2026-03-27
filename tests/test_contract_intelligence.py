"""
Comprehensive unit tests for agl_security_tool.contract_intelligence.

Tests cover:
  - Utility functions: _sigmoid, _shannon_entropy, _log_norm
  - ContractVerdict and ContractCalibrationResult dataclasses (to_dict)
  - ContractAggregator: noisy_or, dampened_aggregate, extract_features, classify
  - ContractMetrics: compute, ROC curve, calibration bins
  - MetaClassifier: extract_features, predict_proba, fit, save/load
"""

import json
import math
import os
import sys
import tempfile

import pytest

_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, _PROJECT_ROOT)

from agl_security_tool.contract_intelligence import (
    _sigmoid,
    _shannon_entropy,
    _log_norm,
    ContractVerdict,
    ContractCalibrationResult,
    MetaTrainingResult,
    ContractAggregator,
    ContractMetrics,
    MetaClassifier,
    DEFAULT_CONTRACT_THRESHOLD,
    META_FEATURE_NAMES,
)


# ═══════════════════════════════════════════════════════════
#  Utility Functions
# ═══════════════════════════════════════════════════════════


class TestSigmoid:
    def test_zero(self):
        assert _sigmoid(0.0) == pytest.approx(0.5, abs=1e-10)

    def test_positive(self):
        result = _sigmoid(5.0)
        assert 0.99 < result < 1.0

    def test_negative(self):
        result = _sigmoid(-5.0)
        assert 0.0 < result < 0.01

    def test_large_positive_no_overflow(self):
        result = _sigmoid(700.0)
        assert result == pytest.approx(1.0, abs=1e-10)

    def test_large_negative_no_underflow(self):
        result = _sigmoid(-700.0)
        assert result == pytest.approx(0.0, abs=1e-10)


class TestShannonEntropy:
    def test_empty_list(self):
        assert _shannon_entropy([]) == 0.0

    def test_all_certain_positive(self):
        """All probabilities near 1.0 → low entropy."""
        result = _shannon_entropy([0.99, 0.99, 0.99])
        assert result < 0.1

    def test_all_uncertain(self):
        """All probabilities at 0.5 → maximum binary entropy."""
        result = _shannon_entropy([0.5, 0.5, 0.5])
        # Maximum binary entropy = ln(2) ≈ 0.693
        assert result == pytest.approx(math.log(2), rel=0.01)

    def test_single_value(self):
        result = _shannon_entropy([0.5])
        assert result > 0

    def test_mixed_probabilities(self):
        result = _shannon_entropy([0.1, 0.5, 0.9])
        assert result > 0


class TestLogNorm:
    def test_zero(self):
        assert _log_norm(0) == pytest.approx(0.0)

    def test_at_scale(self):
        """At n=scale, result should be 1.0."""
        assert _log_norm(20, scale=20.0) == pytest.approx(1.0, rel=1e-10)

    def test_positive(self):
        result = _log_norm(10)
        assert 0.0 < result < 1.0

    def test_negative_returns_zero(self):
        assert _log_norm(-1) == 0.0


# ═══════════════════════════════════════════════════════════
#  ContractVerdict Dataclass
# ═══════════════════════════════════════════════════════════


class TestContractVerdict:
    def test_default_values(self):
        v = ContractVerdict()
        assert v.p_contract == 0.0
        assert v.is_vulnerable is False
        assert v.method == "noisy_or"

    def test_to_dict(self):
        v = ContractVerdict(p_contract=0.75, is_vulnerable=True, method="meta_logistic")
        d = v.to_dict()
        assert d["p_contract"] == pytest.approx(0.75, abs=1e-5)
        assert d["is_vulnerable"] is True
        assert d["method"] == "meta_logistic"

    def test_to_dict_with_meta(self):
        v = ContractVerdict(p_meta=0.8)
        d = v.to_dict()
        assert "p_meta" in d
        assert d["p_meta"] == pytest.approx(0.8, abs=1e-5)

    def test_to_dict_without_meta(self):
        v = ContractVerdict()
        d = v.to_dict()
        assert "p_meta" not in d


# ═══════════════════════════════════════════════════════════
#  ContractAggregator — Noisy-OR
# ═══════════════════════════════════════════════════════════


class TestNoisyOr:
    def test_empty_list(self):
        agg = ContractAggregator()
        assert agg.noisy_or([]) == 0.0

    def test_single_probability(self):
        agg = ContractAggregator()
        assert agg.noisy_or([0.7]) == pytest.approx(0.7)

    def test_two_probabilities(self):
        agg = ContractAggregator()
        # P = 1 - (1-0.5)(1-0.5) = 1 - 0.25 = 0.75
        assert agg.noisy_or([0.5, 0.5]) == pytest.approx(0.75)

    def test_all_zeros(self):
        agg = ContractAggregator()
        assert agg.noisy_or([0.0, 0.0, 0.0]) == pytest.approx(0.0)

    def test_one_certain(self):
        agg = ContractAggregator()
        # If any P_i = 1.0, result is 1.0
        assert agg.noisy_or([0.1, 1.0, 0.3]) == pytest.approx(1.0)

    def test_clamps_input(self):
        agg = ContractAggregator()
        # Values outside [0,1] should be clamped
        result = agg.noisy_or([1.5, -0.5])
        assert 0.0 <= result <= 1.0

    def test_many_low_probabilities_accumulate(self):
        agg = ContractAggregator()
        probs = [0.1] * 20
        result = agg.noisy_or(probs)
        # 1 - 0.9^20 ≈ 0.878
        expected = 1.0 - 0.9**20
        assert result == pytest.approx(expected, rel=1e-6)


# ═══════════════════════════════════════════════════════════
#  ContractAggregator — dampened_aggregate
# ═══════════════════════════════════════════════════════════


class TestDampenedAggregate:
    def test_empty_findings(self):
        agg = ContractAggregator()
        assert agg.dampened_aggregate([]) == 0.0

    def test_no_z3_data(self):
        """Findings without exploit_proof use max_conf formula."""
        agg = ContractAggregator()
        findings = [{"confidence": 0.8}, {"confidence": 0.9}]
        result = agg.dampened_aggregate(findings)
        assert 0.0 <= result <= 1.0

    def test_with_z3_data(self):
        """Findings with exploit_proof use Z3-aware formula."""
        agg = ContractAggregator()
        findings = [
            {"confidence": 0.9, "exploit_proof": {"z3_result": "SAT", "exploitable": True}},
            {"confidence": 0.7, "exploit_proof": {"z3_result": "UNSAT", "exploitable": False}},
        ]
        result = agg.dampened_aggregate(findings)
        assert 0.0 <= result <= 1.0


# ═══════════════════════════════════════════════════════════
#  ContractAggregator — extract_features
# ═══════════════════════════════════════════════════════════


class TestExtractFeatures:
    def test_empty_probabilities(self):
        agg = ContractAggregator()
        features = agg.extract_features([])
        for name in META_FEATURE_NAMES:
            assert features[name] == 0.0

    def test_all_feature_names_present(self):
        agg = ContractAggregator()
        features = agg.extract_features([0.5, 0.8])
        for name in META_FEATURE_NAMES:
            assert name in features

    def test_max_p(self):
        agg = ContractAggregator()
        features = agg.extract_features([0.3, 0.7, 0.5])
        assert features["max_p"] == pytest.approx(0.7)

    def test_mean_p(self):
        agg = ContractAggregator()
        features = agg.extract_features([0.2, 0.4, 0.6])
        assert features["mean_p"] == pytest.approx(0.4)

    def test_count_high(self):
        agg = ContractAggregator()
        features = agg.extract_features([0.3, 0.8, 0.9])
        assert features["count_high"] == 2

    def test_severity_counts(self):
        agg = ContractAggregator()
        features = agg.extract_features(
            [0.5, 0.5],
            severities=["critical", "high"],
        )
        assert features["n_critical"] > 0
        assert features["n_high"] > 0


# ═══════════════════════════════════════════════════════════
#  ContractAggregator — classify
# ═══════════════════════════════════════════════════════════


class TestClassify:
    def test_above_threshold_is_vulnerable(self):
        agg = ContractAggregator(threshold=0.5)
        verdict = agg.classify([0.9, 0.8, 0.7])
        assert verdict.is_vulnerable is True

    def test_below_threshold_is_safe(self):
        agg = ContractAggregator(threshold=0.5)
        verdict = agg.classify([0.1])
        assert verdict.is_vulnerable is False

    def test_empty_is_safe(self):
        agg = ContractAggregator()
        verdict = agg.classify([])
        assert verdict.is_vulnerable is False
        assert verdict.p_contract == 0.0

    def test_verdict_has_all_fields(self):
        agg = ContractAggregator()
        verdict = agg.classify([0.5, 0.7], severities=["high", "medium"])
        assert isinstance(verdict, ContractVerdict)
        assert verdict.total_findings == 2
        assert len(verdict.finding_probabilities) == 2

    def test_custom_threshold(self):
        agg = ContractAggregator()
        verdict = agg.classify([0.3], threshold=0.2)
        assert verdict.is_vulnerable is True
        assert verdict.threshold == 0.2


# ═══════════════════════════════════════════════════════════
#  ContractMetrics — compute
# ═══════════════════════════════════════════════════════════


class TestContractMetrics:
    def test_empty_predictions(self):
        result = ContractMetrics.compute([])
        assert result.total_contracts == 0
        assert result.brier_score == 0.0

    def test_perfect_predictions(self):
        predictions = [
            (0.9, 1),  # vulnerable, predicted high
            (0.1, 0),  # safe, predicted low
        ]
        result = ContractMetrics.compute(predictions, threshold=0.5)
        assert result.tp == 1
        assert result.tn == 1
        assert result.fp == 0
        assert result.fn == 0
        assert result.accuracy == 1.0

    def test_all_false_positives(self):
        predictions = [
            (0.9, 0),  # safe but predicted vulnerable
            (0.8, 0),  # same
        ]
        result = ContractMetrics.compute(predictions, threshold=0.5)
        assert result.fp == 2
        assert result.tp == 0
        assert result.fpr == 1.0

    def test_brier_score_perfect(self):
        predictions = [
            (1.0, 1),
            (0.0, 0),
        ]
        result = ContractMetrics.compute(predictions)
        assert result.brier_score == pytest.approx(0.0)

    def test_brier_score_worst(self):
        predictions = [
            (1.0, 0),
            (0.0, 1),
        ]
        result = ContractMetrics.compute(predictions)
        assert result.brier_score == pytest.approx(1.0)

    def test_roc_curve_generated(self):
        predictions = [
            (0.2, 0),
            (0.4, 0),
            (0.6, 1),
            (0.8, 1),
        ]
        result = ContractMetrics.compute(predictions)
        assert len(result.roc_curve) > 0

    def test_to_dict(self):
        predictions = [(0.7, 1), (0.3, 0)]
        result = ContractMetrics.compute(predictions)
        d = result.to_dict()
        assert "brier_score" in d
        assert "confusion_matrix" in d
        assert "roc_curve" in d
        assert "bins" in d


# ═══════════════════════════════════════════════════════════
#  MetaClassifier
# ═══════════════════════════════════════════════════════════


class TestMetaClassifier:
    def test_init_not_trained(self):
        mc = MetaClassifier()
        assert mc.is_trained is False

    def test_extract_features_returns_list(self):
        mc = MetaClassifier()
        features = mc.extract_features([0.5, 0.8, 0.3])
        assert isinstance(features, list)
        assert len(features) == len(META_FEATURE_NAMES)

    def test_predict_proba_untrained_uses_noisy_or(self):
        mc = MetaClassifier()
        # Untrained: falls back to features[5] (noisy_or_p)
        features = mc.extract_features([0.5, 0.8, 0.3])
        result = mc.predict_proba(features)
        assert 0.0 <= result <= 1.0

    def test_predict_proba_trained(self):
        mc = MetaClassifier()
        mc.weights = [0.1] * len(META_FEATURE_NAMES)
        mc.bias = -0.5
        mc._trained = True
        features = mc.extract_features([0.5, 0.8])
        result = mc.predict_proba(features)
        assert 0.0 <= result <= 1.0

    def test_classify_returns_verdict(self):
        mc = MetaClassifier()
        verdict = mc.classify([0.5, 0.8, 0.3])
        assert isinstance(verdict, ContractVerdict)
        assert verdict.method == "noisy_or"  # untrained → noisy_or

    def test_classify_trained(self):
        mc = MetaClassifier()
        mc.weights = [1.0] * len(META_FEATURE_NAMES)
        mc.bias = 0.0
        mc._trained = True
        verdict = mc.classify([0.9, 0.8])
        assert verdict.method == "meta_logistic"

    def test_fit_trains_model(self):
        mc = MetaClassifier()
        # Simple training data: 2 vulnerable, 2 safe
        X = [
            mc.extract_features([0.9, 0.8, 0.7]),   # vulnerable
            mc.extract_features([0.85, 0.9]),         # vulnerable
            mc.extract_features([0.1, 0.2]),           # safe
            mc.extract_features([0.05, 0.1, 0.15]),    # safe
        ]
        y = [1, 1, 0, 0]
        result = mc.fit(X, y, verbose=False, epochs=100)
        assert mc.is_trained is True
        assert result.epochs_run > 0
        assert result.samples == 4

    def test_save_and_load(self, tmp_path):
        mc = MetaClassifier()
        mc.weights = [0.1] * len(META_FEATURE_NAMES)
        mc.bias = -0.5
        mc._trained = True

        path = str(tmp_path / "meta_weights.json")
        mc.save(path)

        mc2 = MetaClassifier()
        loaded = mc2.load(path)
        assert loaded is True
        assert mc2.is_trained is True

    def test_load_missing_file(self):
        mc = MetaClassifier()
        result = mc.load("/nonexistent/path/weights.json")
        assert result is False
