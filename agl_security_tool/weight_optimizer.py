"""
╔══════════════════════════════════════════════════════════════════════╗
║      AGL Weight Optimizer — Logistic Regression via Gradient Descent ║
║      تعلّم الأوزان تلقائيًا من بيانات البنشمارك                        ║
╚══════════════════════════════════════════════════════════════════════╝

Trains the RiskCore weights  w_f, w_h, w_p, w_e, β  from labelled data
using mini-batch gradient descent on the binary cross-entropy (log-loss).

No external ML libraries required — pure Python + math.

Key equation (same as RiskCore):
    P = σ( w_f·S_f + w_h·S_h + w_p·S_p + w_e·E + β )

Loss:
    L = -(1/N) Σ [ y·log(P) + (1-y)·log(1-P) ]

Gradient:
    ∂L/∂wⱼ = (1/N) Σ (P - y) · xⱼ

Regularization (optional L2):
    L_reg = L + (λ/2N) Σ wⱼ²

Usage:
    from agl_security_tool.weight_optimizer import WeightOptimizer
    opt = WeightOptimizer()
    X = [[0.9, 0.6, 0.3, 1.0], [0.1, 0.2, 0.0, 0.0], ...]
    y = [1, 0, ...]
    result = opt.fit(X, y)
    print(result.weights)  # {'w_formal': ..., ...}
"""

from __future__ import annotations

import json
import math
import logging
import os
import random
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

_logger = logging.getLogger("AGL.weight_optimizer")

# Feature names in order — matches X columns for finding-level training
FEATURE_NAMES = ["w_formal", "w_heuristic", "w_profit", "w_exploit"]

# Extended feature names for contract-level training (8 features)
CONTRACT_FEATURE_NAMES = [
    "w_formal",
    "w_heuristic",
    "w_profit",
    "w_exploit",
    "w_n_findings",
    "w_n_critical",
    "w_cat_diversity",
    "w_avg_formal",
]

# Default artifact path
DEFAULT_WEIGHTS_PATH = os.path.join("artifacts", "risk_weights.json")


@dataclass
class TrainingConfig:
    """Hyperparameters for logistic regression training."""

    learning_rate: float = 0.1
    epochs: int = 1000
    batch_size: int = 32  # 0 = full batch
    l2_lambda: float = 0.5  # L2 regularization toward prior (strong pull keeps calibrated weights stable)
    early_stop_patience: int = 50  # Stop if no improvement for N epochs
    early_stop_min_delta: float = 1e-6
    verbose: bool = True
    seed: int = 42

    # Weight constraints (prevent explosion)
    w_min: float = -10.0
    w_max: float = 10.0
    bias_min: float = -2.0   # Prevent bias from crushing all heuristic findings
    bias_max: float = 1.0


@dataclass
class TrainingResult:
    """Result of weight optimization."""

    weights: Dict[str, float] = field(default_factory=dict)
    bias: float = 0.0
    final_loss: float = 0.0
    final_accuracy: float = 0.0
    final_brier_score: float = 0.0
    epochs_run: int = 0
    converged: bool = False
    loss_history: List[float] = field(default_factory=list)
    training_samples: int = 0
    duration_s: float = 0.0

    # Feature importance (|w| / Σ|w|)
    feature_importance: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": {k: round(v, 6) for k, v in self.weights.items()},
            "bias": round(self.bias, 6),
            "final_loss": round(self.final_loss, 6),
            "final_accuracy": round(self.final_accuracy, 4),
            "final_brier_score": round(self.final_brier_score, 6),
            "epochs_run": self.epochs_run,
            "converged": self.converged,
            "training_samples": self.training_samples,
            "duration_s": round(self.duration_s, 3),
            "feature_importance": {
                k: round(v, 4) for k, v in self.feature_importance.items()
            },
        }


class WeightOptimizer:
    """
    Logistic regression optimizer for RiskCore weights.

    Implements gradient descent on binary cross-entropy loss
    with optional L2 regularization. No external dependencies.
    """

    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()

    # ═══════════════════════════════════════════════════════════
    #  Core Training
    # ═══════════════════════════════════════════════════════════

    def fit(
        self,
        X: List[List[float]],
        y: List[int],
        initial_weights: Optional[Dict[str, float]] = None,
        feature_names: Optional[List[str]] = None,
        sample_weights: Optional[List[float]] = None,
    ) -> TrainingResult:
        """
        Train logistic regression on feature matrix X and labels y.

        Args:
            X: Feature matrix — each row is [S_f, S_h, S_p, E] (4 features)
               or enriched contract-level features (8 features).
            y: Ground truth labels — 1 = truly exploitable, 0 = not
            initial_weights: Starting weights (default: zeros + small random)
            feature_names: Feature names matching X columns. If None,
               auto-selects based on feature count (4→FEATURE_NAMES,
               8→CONTRACT_FEATURE_NAMES).
            sample_weights: Per-sample importance weights for class-balanced
               training. If None, all samples weighted equally (1.0).
               Typical usage: give minority-class samples higher weight
               to counteract class imbalance.

        Returns:
            TrainingResult with optimized weights and diagnostics
        """
        cfg = self.config
        rng = random.Random(cfg.seed)
        t0 = time.monotonic()

        N = len(X)
        if N == 0:
            _logger.error("Empty training set — cannot fit")
            return TrainingResult()

        n_features = len(X[0])
        assert all(
            len(row) == n_features for row in X
        ), f"All rows must have {n_features} features"
        assert len(y) == N, "X and y must have same length"
        assert all(yi in (0, 1) for yi in y), "y must be binary (0 or 1)"

        # Select feature names
        if feature_names is None:
            if n_features == len(CONTRACT_FEATURE_NAMES):
                feature_names = CONTRACT_FEATURE_NAMES
            elif n_features == len(FEATURE_NAMES):
                feature_names = FEATURE_NAMES
            else:
                feature_names = [f"w_{i}" for i in range(n_features)]
        assert (
            len(feature_names) == n_features
        ), f"feature_names length {len(feature_names)} != n_features {n_features}"

        # Sample weights for class-balanced training
        # Auto-balance classes when no explicit weights given
        if sample_weights is None:
            pos_count = sum(y)
            neg_count = N - pos_count
            if pos_count > 0 and neg_count > 0:
                # Inverse-frequency weighting: minority class gets higher weight
                w_pos = N / (2.0 * pos_count)
                w_neg = N / (2.0 * neg_count)
                sw = [w_pos if yi == 1 else w_neg for yi in y]
            else:
                sw = [1.0] * N
        else:
            assert (
                len(sample_weights) == N
            ), f"sample_weights length {len(sample_weights)} != N {N}"
            sw = list(sample_weights)
        # Normalize so mean(sw) = 1 (preserves effective learning rate)
        sw_mean = sum(sw) / N
        if sw_mean > 0:
            sw = [w / sw_mean for w in sw]

        # ── Initialize weights ──
        if initial_weights:
            w = [
                initial_weights.get(feature_names[i], rng.gauss(0, 0.1))
                for i in range(n_features)
            ]
            b = initial_weights.get("bias", 0.0)
        else:
            # Xavier-like initialization
            scale = math.sqrt(2.0 / (n_features + 1))
            w = [rng.gauss(0, scale) for _ in range(n_features)]
            b = 0.0

        # Prior-centered L2: regularize toward initial weights, not zero.
        # This keeps trained weights near calibrated defaults unless data
        # provides strong evidence to deviate.
        w_prior = list(w)  # snapshot of initialization
        b_prior = b

        lr = cfg.learning_rate
        best_loss = float("inf")
        patience_counter = 0
        loss_history = []

        batch_size = cfg.batch_size if cfg.batch_size > 0 else N
        indices = list(range(N))

        if cfg.verbose:
            _logger.info(
                "Training: %d samples, %d features, lr=%.4f, "
                "epochs=%d, batch=%d, L2=%.4f",
                N,
                n_features,
                lr,
                cfg.epochs,
                batch_size,
                cfg.l2_lambda,
            )

        # ── Gradient Descent Loop ──
        for epoch in range(cfg.epochs):
            rng.shuffle(indices)

            epoch_loss = 0.0
            n_batches = 0

            for batch_start in range(0, N, batch_size):
                batch_idx = indices[batch_start : batch_start + batch_size]
                B = len(batch_idx)

                # Compute gradients for this batch
                grad_w = [0.0] * n_features
                grad_b = 0.0
                batch_loss = 0.0

                for i in batch_idx:
                    xi = X[i]
                    yi = y[i]
                    wi = sw[i]  # sample weight for class balance

                    # Forward: logit = w·x + b
                    logit = sum(w[j] * xi[j] for j in range(n_features)) + b
                    pi = _sigmoid(logit)

                    # Loss: -wi·[y·log(p) + (1-y)·log(1-p)]
                    # Clamp to avoid log(0)
                    pi_c = max(1e-15, min(1 - 1e-15, pi))
                    batch_loss += wi * (
                        -(yi * math.log(pi_c) + (1 - yi) * math.log(1 - pi_c))
                    )

                    # Gradient: wi·(p - y) · x
                    err = wi * (pi - yi)
                    for j in range(n_features):
                        grad_w[j] += err * xi[j]
                    grad_b += err

                # Average over batch
                for j in range(n_features):
                    grad_w[j] /= B
                    # Prior-centered L2: pull toward initial weights, not zero
                    grad_w[j] += cfg.l2_lambda * (w[j] - w_prior[j])

                grad_b /= B
                # Prior-centered L2 on bias too
                grad_b += cfg.l2_lambda * (b - b_prior)
                batch_loss /= B

                # L2 penalty on loss (for tracking)
                l2_penalty = (cfg.l2_lambda / 2) * (
                    sum((w[j] - w_prior[j])**2 for j in range(n_features))
                    + (b - b_prior)**2
                )
                batch_loss += l2_penalty

                # Update weights
                for j in range(n_features):
                    w[j] -= lr * grad_w[j]
                    w[j] = max(cfg.w_min, min(cfg.w_max, w[j]))
                b -= lr * grad_b
                b = max(cfg.bias_min, min(cfg.bias_max, b))

                epoch_loss += batch_loss
                n_batches += 1

            avg_loss = epoch_loss / max(1, n_batches)
            loss_history.append(avg_loss)

            # Early stopping
            if avg_loss < best_loss - cfg.early_stop_min_delta:
                best_loss = avg_loss
                patience_counter = 0
            else:
                patience_counter += 1

            if patience_counter >= cfg.early_stop_patience:
                if cfg.verbose:
                    _logger.info(
                        "Early stop at epoch %d — loss %.6f", epoch + 1, avg_loss
                    )
                break

            # Periodic logging
            if cfg.verbose and (epoch + 1) % 100 == 0:
                acc = self._compute_accuracy(X, y, w, b)
                _logger.info(
                    "  Epoch %4d — loss=%.6f  acc=%.4f  w=%s  b=%.4f",
                    epoch + 1,
                    avg_loss,
                    acc,
                    [round(wj, 3) for wj in w],
                    b,
                )

        # ── Final Metrics ──
        duration = time.monotonic() - t0
        acc = self._compute_accuracy(X, y, w, b)
        brier = self._compute_brier(X, y, w, b)
        converged = patience_counter >= cfg.early_stop_patience

        # Feature importance
        total_abs = sum(abs(wj) for wj in w) + 1e-15
        importance = {
            feature_names[j]: abs(w[j]) / total_abs for j in range(n_features)
        }

        weights_dict = {feature_names[j]: w[j] for j in range(n_features)}
        weights_dict["bias"] = b

        result = TrainingResult(
            weights=weights_dict,
            bias=b,
            final_loss=loss_history[-1] if loss_history else 0.0,
            final_accuracy=acc,
            final_brier_score=brier,
            epochs_run=len(loss_history),
            converged=converged,
            loss_history=loss_history,
            training_samples=N,
            duration_s=duration,
            feature_importance=importance,
        )

        if cfg.verbose:
            _logger.info(
                "Training complete: %d epochs, loss=%.6f, acc=%.4f, "
                "brier=%.6f, time=%.2fs",
                result.epochs_run,
                result.final_loss,
                result.final_accuracy,
                result.final_brier_score,
                duration,
            )
            _logger.info("  Weights: %s", weights_dict)
            _logger.info("  Importance: %s", importance)

        return result

    # ═══════════════════════════════════════════════════════════
    #  Save / Load Weights
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def save_weights(
        result: TrainingResult,
        path: str = DEFAULT_WEIGHTS_PATH,
    ) -> str:
        """
        Save optimized weights to JSON.

        File format:
            {
                "weights": {"w_formal": ..., "w_heuristic": ..., ...},
                "metadata": { ... training info ... }
            }
        """
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        payload = {
            "weights": result.weights,
            "metadata": {
                "final_loss": round(result.final_loss, 6),
                "final_accuracy": round(result.final_accuracy, 4),
                "final_brier_score": round(result.final_brier_score, 6),
                "epochs_run": result.epochs_run,
                "training_samples": result.training_samples,
                "feature_importance": {
                    k: round(v, 4) for k, v in result.feature_importance.items()
                },
                "converged": result.converged,
                "duration_s": round(result.duration_s, 3),
            },
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        _logger.info("Weights saved to: %s", path)
        return path

    @staticmethod
    def load_weights(path: str = DEFAULT_WEIGHTS_PATH) -> Optional[Dict[str, float]]:
        """
        Load weights from JSON file.

        Returns weight dict or None if file doesn't exist.
        """
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            weights = data.get("weights", {})
            if weights:
                _logger.info("Loaded saved weights from %s: %s", path, weights)
            return weights if weights else None
        except Exception as e:
            _logger.warning("Failed to load weights from %s: %s", path, e)
            return None

    # ═══════════════════════════════════════════════════════════
    #  Training Data Extraction from Benchmark Results
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def extract_training_data(
        benchmark_result_dict: Dict[str, Any],
    ) -> Tuple[List[List[float]], List[int]]:
        """
        Extract (X, y) training pairs from a BenchmarkResult.to_dict().

        Labels are assigned at the CONTRACT level: every finding in a
        vulnerable contract is y=1, every finding in a safe contract is y=0.
        This trains the model to recognise what "truly risky" feature
        distributions look like vs. false-positive noise.

        Returns:
            X: [[S_f, S_h, S_p, E], ...]
            y: [0 or 1, ...]
        """
        X, y_labels = [], []

        for cr in benchmark_result_dict.get("contract_results", []):
            expected = cr.get("expected_exploitable", False)
            label = 1 if expected else 0
            findings = cr.get("findings", [])

            if not findings:
                X.append([0.0, 0.0, 0.0, 0.0])
                y_labels.append(label)
                continue

            for f in findings:
                rb = f.get("risk_breakdown", {})
                if rb:
                    sf = rb.get("formal_score", 0.0)
                    sh = rb.get("heuristic_score", 0.0)
                    sp = rb.get("profit_score", 0.0)
                    e = 1.0 if rb.get("exploit_proven", False) else 0.0
                else:
                    prob = f.get("probability", 0.5)
                    if isinstance(prob, str):
                        prob = {"high": 0.9, "medium": 0.7, "low": 0.5}.get(
                            prob.lower(), 0.5
                        )
                    prob = float(prob)
                    sev = f.get("severity", "").lower()
                    sf = prob * 0.3 if sev in ("critical", "high") else 0.0
                    sh = prob
                    sp = prob * 0.5 if sev in ("critical", "high") else prob * 0.2
                    e = 0.0

                X.append([sf, sh, sp, e])
                y_labels.append(label)

        return X, y_labels

    @staticmethod
    def extract_training_data_contract_level(
        benchmark_result_dict: Dict[str, Any],
    ) -> Tuple[List[List[float]], List[int]]:
        """
        Extract (X, y) at contract level (one row per contract).

        Enriched feature set for better discrimination with small samples:
          [max_sf, max_sh, max_sp, has_exploit, n_findings_norm,
           n_critical_norm, category_diversity, avg_formal]

        n_findings_norm / n_critical_norm are log-scaled: log(1+n)/log(1+20).
        category_diversity = unique_categories / total_findings.

        Returns:
            X: [[...8 features...], ...]
            y: [0 or 1, ...]
        """
        X, y_labels = [], []

        for cr in benchmark_result_dict.get("contract_results", []):
            expected = cr.get("expected_exploitable", False)
            findings = cr.get("findings", [])

            max_sf = max_sh = max_sp = max_e = 0.0
            sum_sf = 0.0
            n_critical = 0
            categories = set()

            for f in findings:
                cat = f.get("category", "").lower()
                if cat:
                    categories.add(cat)
                sev = f.get("severity", "").lower()
                if sev in ("critical",):
                    n_critical += 1

                rb = f.get("risk_breakdown", {})
                if rb:
                    sf = rb.get("formal_score", 0.0)
                    sh = rb.get("heuristic_score", 0.0)
                    sp = rb.get("profit_score", 0.0)
                    max_sf = max(max_sf, sf)
                    max_sh = max(max_sh, sh)
                    max_sp = max(max_sp, sp)
                    sum_sf += sf
                    if rb.get("exploit_proven", False):
                        max_e = 1.0
                else:
                    prob = f.get("probability", 0.5)
                    if isinstance(prob, str):
                        prob = {"high": 0.9, "medium": 0.7, "low": 0.5}.get(
                            prob.lower(), 0.5
                        )
                    prob = float(prob)
                    max_sh = max(max_sh, prob)
                    max_sp = max(max_sp, prob * 0.3)

            n = len(findings)
            _log_norm = math.log(21)  # normalise: log(1+20)
            n_findings_norm = math.log(1 + n) / _log_norm if n else 0.0
            n_critical_norm = (
                math.log(1 + n_critical) / _log_norm if n_critical else 0.0
            )
            cat_diversity = len(categories) / n if n else 0.0
            avg_formal = sum_sf / n if n else 0.0

            X.append(
                [
                    max_sf,
                    max_sh,
                    max_sp,
                    max_e,
                    n_findings_norm,
                    n_critical_norm,
                    cat_diversity,
                    avg_formal,
                ]
            )
            y_labels.append(1 if expected else 0)

        return X, y_labels

    # ═══════════════════════════════════════════════════════════
    #  Helper Methods
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _compute_accuracy(
        X: List[List[float]], y: List[int], w: List[float], b: float
    ) -> float:
        """Compute classification accuracy at threshold 0.5."""
        correct = 0
        for i in range(len(X)):
            logit = sum(w[j] * X[i][j] for j in range(len(w))) + b
            pred = 1 if _sigmoid(logit) >= 0.5 else 0
            if pred == y[i]:
                correct += 1
        return correct / len(X) if X else 0.0

    @staticmethod
    def _compute_brier(
        X: List[List[float]], y: List[int], w: List[float], b: float
    ) -> float:
        """Compute Brier score: (1/N) Σ (P - y)²."""
        total = 0.0
        for i in range(len(X)):
            logit = sum(w[j] * X[i][j] for j in range(len(w))) + b
            p = _sigmoid(logit)
            total += (p - y[i]) ** 2
        return total / len(X) if X else 0.0

    def print_training_summary(self, result: TrainingResult):
        """Pretty-print training results."""
        print("\n" + "=" * 65)
        print("  AGL Weight Optimizer — Training Summary")
        print("  " + "─" * 61)
        print(f"  Training samples:   {result.training_samples}")
        print(f"  Epochs run:         {result.epochs_run}")
        print(
            f"  Converged:          {'✅ Yes' if result.converged else '⬜ No (max epochs)'}"
        )
        print(f"  Duration:           {result.duration_s:.2f}s")
        print()
        print(f"  Final Loss:         {result.final_loss:.6f}")
        print(f"  Final Accuracy:     {result.final_accuracy:.4f}", end="  ")
        if result.final_accuracy >= 0.9:
            print("✅")
        elif result.final_accuracy >= 0.75:
            print("🟡")
        else:
            print("🔴")
        print(f"  Final Brier Score:  {result.final_brier_score:.6f}")
        print()

        print("  Optimized Weights:")
        print(f"  {'Feature':>15} {'Weight':>10} {'Importance':>12}")
        print("  " + "─" * 40)
        for name in FEATURE_NAMES:
            w = result.weights.get(name, 0.0)
            imp = result.feature_importance.get(name, 0.0)
            bar = "█" * int(imp * 20)
            print(f"  {name:>15} {w:>10.4f} {imp:>10.1%}  {bar}")
        print(f"  {'bias':>15} {result.bias:>10.4f}")
        print()

        # Show RiskCore severity mapping with new weights
        print("  Severity thresholds with learned weights:")
        for label, desc in [
            ("CRITICAL", "P > 0.85"),
            ("HIGH", "P > 0.65"),
            ("MEDIUM", "P > 0.40"),
            ("LOW", "P > 0.15"),
            ("INFO", "P ≤ 0.15"),
        ]:
            print(f"    {label:<10} {desc}")
        print("=" * 65)


# ── Module-level sigmoid (avoids method overhead in tight loops) ──
def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)
