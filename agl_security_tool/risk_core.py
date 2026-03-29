"""
╔══════════════════════════════════════════════════════════════════════╗
║          AGL Risk Core — النواة الاحتمالية الموحدة                    ║
║          Unified Probabilistic Risk Engine                           ║
╚══════════════════════════════════════════════════════════════════════╝

Single equation for all risk decisions:

    P(exploit | evidence) = σ( w_f·S_f + w_h·S_h + w_p·S_p + w_e·E + β )

Where:
    S_f = formal verification score (Z3 SAT/UNSAT)
    S_h = heuristic score (tunneling, wave, detectors)
    S_p = profit feasibility score (economic attack simulation)
    E   = exploit_proven indicator (1 if Z3 + invariant violated)
    σ   = sigmoid function
    w   = calibrated weights
    β   = bias term

Severity is derived ONLY from P:
    P > 0.85 → CRITICAL
    P > 0.65 → HIGH
    P > 0.40 → MEDIUM
    P > 0.15 → LOW
    else     → INFO

Every finding carries a transparent breakdown of how P was computed.
"""

from __future__ import annotations

import json
import math
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

_logger = logging.getLogger("AGL.risk_core")

# Default path for learned weights
_WEIGHTS_PATH = os.path.join("artifacts", "risk_weights.json")

# ═══════════════════════════════════════════════════════════════
#  Calibrated Weights (Phase 1 defaults — will be tuned by benchmark)
# ═══════════════════════════════════════════════════════════════
DEFAULT_WEIGHTS = {
    "w_formal": 3.5,  # Z3 proven findings carry highest weight
    "w_heuristic": 1.38,  # Trained: heuristic alone insufficient — needs corroboration (↓ from 1.5)
    "w_profit": 1.2,  # Economic viability signal
    "w_exploit": 4.0,  # Exploit fully proven (Z3 + invariant) — decisive
    "bias": -0.43,  # Trained: mild skepticism (↓ from -0.3, reduces FP severity inflation)
}

# Multiplier applied to heuristic_score based on original detector severity.
# Ensures the model respects detector-assigned severity, not just confidence.
SEVERITY_MULTIPLIER = {
    "critical": 1.0,
    "high": 0.85,
    "medium": 0.6,
    "low": 0.3,
    "info": 0.1,
    "warning": 0.2,
}

# Severity thresholds — smooth mapping from probability
SEVERITY_THRESHOLDS = [
    (0.85, "CRITICAL"),
    (0.65, "HIGH"),
    (0.40, "MEDIUM"),
    (0.15, "LOW"),
    (0.00, "INFO"),
]

# Negative evidence penalty — applied per source of exculpatory evidence.
# When L3 ran but found no profitable attack, or L4 ran but found no
# exploitable path, each subtracts this from the logit.
# -0.6 means: 1 negative source ≈ meaningful demotion;
#              2 negative sources ≈ significant severity reduction.
#              (was -0.3, too weak against w_heuristic bias)
NEGATIVE_EVIDENCE_PENALTY = -0.6


@dataclass
class RiskBreakdown:
    """
    Transparent breakdown for a single finding's risk computation.
    Every number is traceable — no hidden scoring.
    """

    # Input scores (all normalized to [0, 1])
    formal_score: float = 0.0  # From Z3/symbolic verification
    heuristic_score: float = 0.0  # From detectors/patterns/tunneling
    profit_score: float = 0.0  # From economic simulation
    exploit_proven: bool = False  # Z3 SAT + invariant violated

    # Source attribution
    formal_sources: List[str] = field(default_factory=list)
    heuristic_sources: List[str] = field(default_factory=list)
    profit_sources: List[str] = field(default_factory=list)

    # Computed outputs
    raw_logit: float = 0.0
    probability: float = 0.0
    severity: str = "INFO"

    # Influence percentages (explainability)
    formal_influence_pct: float = 0.0
    heuristic_influence_pct: float = 0.0
    profit_influence_pct: float = 0.0
    exploit_influence_pct: float = 0.0

    # Multi-source confirmation count
    source_count: int = 1

    # Negative evidence — exculpatory signals from L3/L4 silence
    negative_evidence_count: int = 0
    negative_evidence_penalty_applied: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "probability": round(self.probability, 4),
            "severity": self.severity,
            "formal_score": round(self.formal_score, 4),
            "heuristic_score": round(self.heuristic_score, 4),
            "profit_score": round(self.profit_score, 4),
            "exploit_proven": self.exploit_proven,
            "influence": {
                "formal_pct": round(self.formal_influence_pct, 1),
                "heuristic_pct": round(self.heuristic_influence_pct, 1),
                "profit_pct": round(self.profit_influence_pct, 1),
                "exploit_pct": round(self.exploit_influence_pct, 1),
            },
            "sources": {
                "formal": self.formal_sources,
                "heuristic": self.heuristic_sources,
                "profit": self.profit_sources,
            },
            "source_count": self.source_count,
            "raw_logit": round(self.raw_logit, 4),
        }
        if self.negative_evidence_count > 0:
            d["negative_evidence"] = {
                "count": self.negative_evidence_count,
                "penalty_applied": round(self.negative_evidence_penalty_applied, 4),
            }
        return d


class RiskCore:
    """
    Unified probabilistic risk engine.

    Single equation computes P(exploit | evidence) for every finding.
    Severity derives ONLY from P — no separate classification logic.

    Usage:
        rc = RiskCore()
        breakdown = rc.compute(formal=0.95, heuristic=0.6, profit=0.3, proven=True)
        print(breakdown.probability)  # 0.97
        print(breakdown.severity)     # CRITICAL
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        auto_load: bool = True,
    ):
        self.weights = dict(DEFAULT_WEIGHTS)

        # Priority: explicit > saved file > defaults
        if weights:
            self.weights.update(weights)
        elif auto_load:
            saved = self._try_load_saved_weights()
            if saved and self._weights_are_sane(saved):
                self.weights.update(saved)
                _logger.info("RiskCore loaded learned weights from %s", _WEIGHTS_PATH)
            elif saved:
                _logger.warning(
                    "RiskCore REJECTED saved weights from %s — failed sanity check "
                    "(w_formal=%s, w_exploit=%s). Using calibrated defaults.",
                    _WEIGHTS_PATH,
                    saved.get("w_formal"),
                    saved.get("w_exploit"),
                )

    @staticmethod
    def _weights_are_sane(w: Dict[str, float]) -> bool:
        """التحقق من صحة الأوزان — رفض الأوزان المعكوسة أو المنهارة.

        Reject weights that invert the model's semantics:
        - w_formal < 0 means Z3 proofs REDUCE severity (catastrophic)
        - w_exploit < 0 means proven exploits REDUCE severity (catastrophic)
        - All weights near zero means the model learned nothing useful

        These conditions indicate a failed or degenerate training run.
        """
        # Rule 1: Z3 formal proofs must INCREASE probability, never decrease
        if w.get("w_formal", 0) < 0:
            _logger.warning(
                "Sanity FAIL: w_formal=%s (negative — Z3 proofs would reduce severity)",
                w.get("w_formal"),
            )
            return False

        # Rule 2: Proven exploits must INCREASE probability
        if w.get("w_exploit", 0) < 0:
            _logger.warning(
                "Sanity FAIL: w_exploit=%s (negative — exploits would reduce severity)",
                w.get("w_exploit"),
            )
            return False

        # Rule 2b: Heuristic detectors must not REDUCE probability
        if w.get("w_heuristic", 0) < 0:
            _logger.warning(
                "Sanity FAIL: w_heuristic=%s (negative — detector findings would reduce severity)",
                w.get("w_heuristic"),
            )
            return False

        # Rule 3: Total positive signal must be meaningful
        total_signal = sum(abs(v) for k, v in w.items() if k != "bias")
        if total_signal < 0.5:
            _logger.warning(
                "Sanity FAIL: total signal %.3f (model learned nothing useful)",
                total_signal,
            )
            return False

        return True

    @staticmethod
    def _try_load_saved_weights() -> Optional[Dict[str, float]]:
        """Attempt to load weights from artifacts/risk_weights.json."""
        try:
            from agl_security_tool.weight_optimizer import WeightOptimizer

            return WeightOptimizer.load_weights(_WEIGHTS_PATH)
        except Exception:
            # Fallback: read JSON directly
            if os.path.isfile(_WEIGHTS_PATH):
                try:
                    with open(_WEIGHTS_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    return data.get("weights", None)
                except Exception:
                    pass
            return None

    # ─── Core Equation ─────────────────────────────────────────
    def compute_exploit_probability(
        self,
        formal_score: float,
        heuristic_score: float,
        profit_score: float,
        exploit_proven: bool,
        source_count: int = 1,
        formal_sources: Optional[List[str]] = None,
        heuristic_sources: Optional[List[str]] = None,
        profit_sources: Optional[List[str]] = None,
        negative_evidence_count: int = 0,
    ) -> RiskBreakdown:
        """
        Compute unified exploit probability from all evidence channels.

        Args:
            formal_score:    Z3/symbolic proof strength [0, 1]
            heuristic_score: Detector/pattern/tunneling score [0, 1]
            profit_score:    Economic viability [0, 1]
            exploit_proven:  True if Z3 SAT + invariant violated
            source_count:    Number of independent sources confirming
            formal_sources:  Names of formal verification sources
            heuristic_sources: Names of heuristic sources
            profit_sources:  Names of profit estimation sources
            negative_evidence_count: Number of L3/L4 sources that ran
                but found NO profitable attack / exploitable path.
                Each piece subtracts NEGATIVE_EVIDENCE_PENALTY from logit.

        Returns:
            RiskBreakdown with probability, severity, and full transparency
        """
        # Clamp inputs to [0, 1]
        f = max(0.0, min(1.0, formal_score))
        h = max(0.0, min(1.0, heuristic_score))
        p = max(0.0, min(1.0, profit_score))
        e = 1.0 if exploit_proven else 0.0

        # Multi-source confirmation bonus (logarithmic, diminishing returns)
        source_bonus = math.log(max(1, source_count)) * 0.3

        # Negative evidence penalty — L3/L4 ran but could not confirm
        neg_count = max(0, int(negative_evidence_count))
        neg_penalty = neg_count * NEGATIVE_EVIDENCE_PENALTY  # negative value

        # Raw logit computation
        w = self.weights
        logit = (
            w["w_formal"] * f
            + w["w_heuristic"] * h
            + w["w_profit"] * p
            + w["w_exploit"] * e
            + source_bonus
            + neg_penalty
            + w["bias"]
        )

        # Sigmoid → P ∈ [0, 1]
        probability = self._sigmoid(logit)

        # Derive severity ONLY from probability
        severity = self._severity_from_probability(probability)

        # Compute influence percentages
        total_positive = (
            abs(w["w_formal"] * f)
            + abs(w["w_heuristic"] * h)
            + abs(w["w_profit"] * p)
            + abs(w["w_exploit"] * e)
            + abs(source_bonus)
        )
        if total_positive > 0:
            f_pct = (abs(w["w_formal"] * f) / total_positive) * 100
            h_pct = (abs(w["w_heuristic"] * h) / total_positive) * 100
            p_pct = (abs(w["w_profit"] * p) / total_positive) * 100
            e_pct = (abs(w["w_exploit"] * e) / total_positive) * 100
        else:
            f_pct = h_pct = p_pct = e_pct = 0.0

        return RiskBreakdown(
            formal_score=f,
            heuristic_score=h,
            profit_score=p,
            exploit_proven=exploit_proven,
            formal_sources=formal_sources or [],
            heuristic_sources=heuristic_sources or [],
            profit_sources=profit_sources or [],
            raw_logit=logit,
            probability=probability,
            severity=severity,
            formal_influence_pct=f_pct,
            heuristic_influence_pct=h_pct,
            profit_influence_pct=p_pct,
            exploit_influence_pct=e_pct,
            source_count=source_count,
            negative_evidence_count=neg_count,
            negative_evidence_penalty_applied=neg_penalty,
        )

    # ─── Batch Processing ──────────────────────────────────────
    def score_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score a batch of findings, adding risk_breakdown to each.

        Each finding dict should have:
            - confidence (float or str): existing confidence
            - severity (str): existing severity (will be OVERRIDDEN)
            - confirmed_by (list): source list
            - exploit_proof (dict, optional): if present, exploit_proven=True
            - is_proven (bool, optional): from Z3
            - profit_estimate (float, optional): estimated profit

        Returns the same list with 'risk_breakdown' and 'severity' updated.
        """
        scored = []
        for f in findings:
            # Extract formal score
            formal = 0.0
            formal_sources = []
            if f.get("is_proven"):
                formal = float(f.get("confidence", 0.9))
                formal_sources.append("z3_proven")
            elif f.get("source", "") in ("z3_symbolic", "z3"):
                formal = float(f.get("confidence", 0.5)) * 0.7
                formal_sources.append("z3_heuristic")

            # Extract heuristic score
            heuristic = 0.0
            heuristic_sources = []
            conf_val = self._normalize_confidence(f.get("confidence", 0.5))
            sources = f.get("confirmed_by", [f.get("source", "unknown")])
            if not isinstance(sources, list):
                sources = [str(sources)]

            for src in sources:
                s = str(src).lower()
                if "z3" in s or "formal" in s or "symbolic" in s:
                    formal = max(formal, conf_val)
                    if s not in formal_sources:
                        formal_sources.append(s)
                else:
                    heuristic = max(heuristic, conf_val)
                    if s not in heuristic_sources:
                        heuristic_sources.append(s)

            # Modulate heuristic by original detector severity so that a
            # high-confidence LOW finding stays low and a medium-confidence
            # HIGH finding is promoted appropriately.
            orig_sev = f.get("severity", "medium").lower()
            sev_mult = SEVERITY_MULTIPLIER.get(orig_sev, 0.5)
            heuristic = heuristic * sev_mult

            # Extract profit score
            profit = 0.0
            profit_sources = []
            if "profit_estimate" in f:
                profit_raw = float(f["profit_estimate"])
                # Sigmoid normalize: 10K → ~0.5, 100K → ~0.88, 1M → ~0.99
                profit = self._sigmoid((math.log10(max(1, profit_raw)) - 4) * 2)
                profit_sources.append("economic_simulation")
            elif f.get("source", "") in ("attack_simulation", "search_engine"):
                profit = conf_val * 0.6
                profit_sources.append(f.get("source", ""))

            # Exploit proven?
            proven = bool(f.get("exploit_proof", {}).get("exploitable", False))

            # Read negative evidence (set by core.py dedup layer)
            neg_ev = f.get("negative_evidence", [])
            neg_count = len(neg_ev) if isinstance(neg_ev, list) else 0

            # Compute unified probability
            breakdown = self.compute_exploit_probability(
                formal_score=formal,
                heuristic_score=heuristic,
                profit_score=profit,
                exploit_proven=proven,
                source_count=len(sources),
                formal_sources=formal_sources,
                heuristic_sources=heuristic_sources,
                profit_sources=profit_sources,
                negative_evidence_count=neg_count,
            )

            # Update finding — preserve original detector severity for
            # downstream layers (exploit reasoning) that need pre-scoring info.
            if "original_severity" not in f:
                f["original_severity"] = f.get("severity", "MEDIUM").upper()
            f["risk_breakdown"] = breakdown.to_dict()
            f["probability"] = breakdown.probability
            f["severity"] = breakdown.severity.upper()
            f["confidence"] = breakdown.probability  # Unify: confidence = probability
            scored.append(f)

        return scored

    # ─── Utility Methods ───────────────────────────────────────
    @staticmethod
    def _sigmoid(x: float) -> float:
        """Numerically stable sigmoid."""
        if x >= 0:
            z = math.exp(-x)
            return 1.0 / (1.0 + z)
        else:
            z = math.exp(x)
            return z / (1.0 + z)

    @staticmethod
    def _severity_from_probability(p: float) -> str:
        """Map probability to severity — single source of truth."""
        for threshold, label in SEVERITY_THRESHOLDS:
            if p >= threshold:
                return label
        return "INFO"

    @staticmethod
    def _normalize_confidence(val) -> float:
        """Normalize confidence to float (detectors use 'high'/'medium'/'low')."""
        if isinstance(val, (int, float)):
            return max(0.0, min(1.0, float(val)))
        return {"high": 0.9, "medium": 0.7, "low": 0.5}.get(str(val).lower(), 0.5)

    # ─── Sensitivity Analysis ─────────────────────────────────
    def partial_derivatives(
        self, formal: float, heuristic: float, profit: float, proven: bool
    ) -> Dict[str, float]:
        """
        Compute ∂P/∂x for each input — measure how each variable affects output.
        Useful for debugging and calibration.
        """
        base = self.compute_exploit_probability(formal, heuristic, profit, proven)
        p0 = base.probability
        delta = 0.01

        derivs = {}
        for name, val in [
            ("formal", formal),
            ("heuristic", heuristic),
            ("profit", profit),
        ]:
            args = {
                "formal_score": formal,
                "heuristic_score": heuristic,
                "profit_score": profit,
                "exploit_proven": proven,
            }
            args[f"{name}_score"] = min(1.0, val + delta)
            p1 = self.compute_exploit_probability(**args).probability
            derivs[f"dP_d{name}"] = (p1 - p0) / delta

        # Exploit toggle
        if not proven:
            p_proven = self.compute_exploit_probability(
                formal, heuristic, profit, True
            ).probability
            derivs["dP_dexploit"] = p_proven - p0
        else:
            derivs["dP_dexploit"] = 0.0

        return derivs

    # ─── Weight Learning Interface ─────────────────────────────
    def fit_weights(
        self,
        training_data: Tuple[List[List[float]], List[int]],
        save_path: str = _WEIGHTS_PATH,
        config: Optional[Any] = None,
    ) -> Dict[str, float]:
        """
        Learn optimal weights from labelled training data via logistic regression.

        This replaces the old grid-search calibrate_from_benchmark() with
        proper gradient-descent optimization.

        Args:
            training_data: Tuple of (X, y) where
                           X = [[S_f, S_h, S_p, E], ...]
                           y = [0 or 1, ...]
            save_path: Where to save learned weights JSON
            config: Optional TrainingConfig override

        Returns:
            Updated weights dict (also sets self.weights and saves to disk)
        """
        from agl_security_tool.weight_optimizer import (
            WeightOptimizer,
            TrainingConfig,
            TrainingResult,
        )

        X, y = training_data
        if not X:
            _logger.warning("Empty training data — keeping current weights")
            return self.weights

        # Configure optimizer
        cfg = config if config else TrainingConfig()
        optimizer = WeightOptimizer(config=cfg)

        # Use current weights as initialization
        result = optimizer.fit(X, y, initial_weights=dict(self.weights))

        # Apply learned weights
        self.weights.update(result.weights)
        _logger.info("Learned weights: %s", self.weights)
        _logger.info(
            "  Loss=%.6f  Acc=%.4f  Brier=%.6f",
            result.final_loss,
            result.final_accuracy,
            result.final_brier_score,
        )

        # Save to disk
        WeightOptimizer.save_weights(result, save_path)

        # Print summary
        optimizer.print_training_summary(result)

        return self.weights

    def calibrate_from_benchmark(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Deprecated: use fit_weights() with proper training data instead.

        This shim extracts feature vectors from benchmark results and
        routes to fit_weights() for proper gradient-descent optimization.
        """
        _logger.warning(
            "calibrate_from_benchmark() is deprecated — use fit_weights() instead"
        )
        from agl_security_tool.weight_optimizer import WeightOptimizer

        # Convert old-style results to (X, y) training data
        X, y = [], []
        for r in results:
            sf = r.get("formal_score", 0.0)
            sh = r.get("heuristic_score", 0.0)
            sp = r.get("profit_score", 0.0)
            e = 1.0 if r.get("exploit_proven", False) else 0.0
            label = 1 if r.get("expected_exploitable", False) else 0
            X.append([sf, sh, sp, e])
            y.append(label)

        if not X:
            return self.weights

        return self.fit_weights((X, y))
