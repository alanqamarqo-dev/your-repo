"""
╔══════════════════════════════════════════════════════════════════════╗
║  AGL RiskCore — Unified Probabilistic Risk Scoring                   ║
║  تقييم المخاطر الموحد — نموذج احتمالي لتسجيل الثغرات                  ║
╚══════════════════════════════════════════════════════════════════════╝

Computes exploit probability for each finding using a logistic model:
    P(exploit) = σ(w_h · h + w_f · f + w_p · p + bias)

Where:
    h = heuristic score (from pattern/detector confidence)
    f = formal verification score (from Z3 proofs)
    p = prior probability (from on-chain / historical data)

Then maps probability → severity label:
    P ≥ 0.85 → CRITICAL
    P ≥ 0.65 → HIGH
    P ≥ 0.40 → MEDIUM
    P < 0.40 → LOW
"""

import math
import logging
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

_logger = logging.getLogger("AGL.risk_core")

# ═══════════════════════════════════════════════════════
#  Weights — learned via logistic regression on labeled data
# ═══════════════════════════════════════════════════════

# Default path for trained weights
_WEIGHTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.pardir,
    "artifacts",
    "risk_core_weights.json",
)

# Default coefficients (calibrated from benchmark data)
DEFAULT_W_HEURISTIC = 2.5  # Weight for heuristic/pattern confidence
DEFAULT_W_FORMAL = 4.0     # Weight for formal Z3 proof
DEFAULT_W_PRIOR = 1.5      # Weight for prior/historical probability
DEFAULT_BIAS = -1.2        # Bias (conservative to reduce false positives)

# Severity thresholds (calibrated to minimize FP while keeping high recall)
SEVERITY_THRESHOLDS = {
    "CRITICAL": 0.85,
    "HIGH": 0.65,
    "MEDIUM": 0.40,
    "LOW": 0.0,
}

# Severity multiplier — applies minor modulation to downstream layers
SEVERITY_MULTIPLIER = {
    "CRITICAL": 1.0,
    "HIGH": 0.95,
    "MEDIUM": 0.80,
    "LOW": 0.60,
}


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    else:
        ez = math.exp(x)
        return ez / (1.0 + ez)


class RiskCore:
    """
    Unified probabilistic risk scorer for security findings.

    Consumes per-finding data and outputs calibrated exploit probabilities
    with severity labels based on learned thresholds.
    """

    def __init__(
        self,
        w_heuristic: float = DEFAULT_W_HEURISTIC,
        w_formal: float = DEFAULT_W_FORMAL,
        w_prior: float = DEFAULT_W_PRIOR,
        bias: float = DEFAULT_BIAS,
    ):
        self.w_heuristic = w_heuristic
        self.w_formal = w_formal
        self.w_prior = w_prior
        self.bias = bias

        # Try loading trained weights
        self._load_weights()

    def _load_weights(self):
        """Load trained weights from JSON if available."""
        path = os.path.normpath(_WEIGHTS_PATH)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.w_heuristic = data.get("w_heuristic", self.w_heuristic)
                self.w_formal = data.get("w_formal", self.w_formal)
                self.w_prior = data.get("w_prior", self.w_prior)
                self.bias = data.get("bias", self.bias)
                _logger.info("RiskCore weights loaded from %s", path)
            except Exception as e:
                _logger.warning("Failed to load RiskCore weights: %s", e)

    def save_weights(self, path: Optional[str] = None):
        """Save current weights to JSON."""
        path = path or os.path.normpath(_WEIGHTS_PATH)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        payload = {
            "w_heuristic": self.w_heuristic,
            "w_formal": self.w_formal,
            "w_prior": self.w_prior,
            "bias": self.bias,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        _logger.info("RiskCore weights saved to %s", path)

    def compute_exploit_probability(
        self,
        heuristic_score: float = 0.0,
        formal_score: float = 0.0,
        prior_score: float = 0.0,
    ) -> float:
        """
        Compute P(exploit) from feature scores.

        Args:
            heuristic_score: Confidence from pattern/detector (0–1)
            formal_score: Z3 formal proof score (0 or 1 typically)
            prior_score: Prior probability from historical data (0–1)

        Returns:
            P(exploit) ∈ [0, 1]
        """
        logit = (
            self.w_heuristic * heuristic_score
            + self.w_formal * formal_score
            + self.w_prior * prior_score
            + self.bias
        )
        return _sigmoid(logit)

    def probability_to_severity(self, p: float) -> str:
        """Map probability to severity label."""
        if p >= SEVERITY_THRESHOLDS["CRITICAL"]:
            return "CRITICAL"
        elif p >= SEVERITY_THRESHOLDS["HIGH"]:
            return "HIGH"
        elif p >= SEVERITY_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"

    def _extract_heuristic_score(self, finding: Dict[str, Any]) -> float:
        """Extract heuristic confidence from a finding dict."""
        # Try explicit confidence field
        conf = finding.get("confidence", None)
        if conf is not None:
            if isinstance(conf, (int, float)):
                return max(0.0, min(1.0, float(conf)))
            if isinstance(conf, str):
                return {"high": 0.9, "medium": 0.7, "low": 0.5}.get(
                    conf.lower(), 0.5
                )

        # Fall back to severity-based estimate
        sev = str(finding.get("severity", "medium")).lower()
        return {
            "critical": 0.95,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
            "info": 0.2,
        }.get(sev, 0.5)

    def _extract_formal_score(self, finding: Dict[str, Any]) -> float:
        """Extract formal verification score from a finding dict."""
        # Z3 proven
        if finding.get("is_proven", False):
            return 1.0

        # Exploit proof
        proof = finding.get("exploit_proof", {})
        if isinstance(proof, dict) and proof.get("exploitable", False):
            return 0.9

        return 0.0

    def _extract_prior_score(self, finding: Dict[str, Any]) -> float:
        """Extract prior probability from a finding dict."""
        # Explicit probability field
        p = finding.get("probability", None)
        if p is not None:
            if isinstance(p, (int, float)):
                return max(0.0, min(1.0, float(p)))

        return 0.0

    def score_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single finding with exploit probability.

        Returns the finding dict augmented with risk_breakdown.
        """
        h = self._extract_heuristic_score(finding)
        f = self._extract_formal_score(finding)
        p = self._extract_prior_score(finding)

        prob = self.compute_exploit_probability(h, f, p)
        severity = self.probability_to_severity(prob)

        # Preserve original severity for downstream layers
        original_severity = finding.get("severity", "medium")
        if "original_severity" not in finding:
            finding["original_severity"] = original_severity

        # Add risk breakdown
        finding["risk_breakdown"] = {
            "exploit_probability": round(prob, 4),
            "heuristic_score": round(h, 4),
            "formal_score": round(f, 4),
            "prior_score": round(p, 4),
            "severity": severity,
            "model": "logistic_v1",
        }

        # Update severity based on model
        finding["severity"] = severity.lower()
        finding["probability"] = round(prob, 4)

        return finding

    def score_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score all findings with exploit probabilities.

        Returns the list of findings with risk_breakdown added.
        """
        scored = []
        for f in findings:
            try:
                scored.append(self.score_finding(dict(f)))
            except Exception as e:
                _logger.warning("RiskCore scoring error for finding: %s", e)
                scored.append(f)

        _logger.info(
            "RiskCore scored %d findings (%d CRITICAL, %d HIGH, %d MEDIUM, %d LOW)",
            len(scored),
            sum(1 for f in scored if f.get("severity", "").lower() == "critical"),
            sum(1 for f in scored if f.get("severity", "").lower() == "high"),
            sum(1 for f in scored if f.get("severity", "").lower() == "medium"),
            sum(1 for f in scored if f.get("severity", "").lower() == "low"),
        )
        return scored
