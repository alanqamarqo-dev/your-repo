"""
╔══════════════════════════════════════════════════════════════════════╗
║      AGL Benchmark Runner — Statistical Evaluation Framework         ║
║      Precision / Recall / F1 / FPR / FNR                            ║
╚══════════════════════════════════════════════════════════════════════╝

Measures the tool's real performance against known-vulnerable contracts.
Supports:
  - SWC Registry (Smart Contract Weakness Classification)
  - Damn Vulnerable DeFi (DeFi-specific exploits)
  - Custom contract suites

Output:
  - Per-category and aggregate precision, recall, F1
  - False positive / negative rates
  - ROC data points for threshold tuning
  - JSON + CSV export

Usage:
    from agl_security_tool.benchmark_runner import BenchmarkRunner
    runner = BenchmarkRunner()
    results = runner.run_swc_benchmark("path/to/swc_contracts/")
    runner.export_json(results, "benchmark_results.json")
"""

from __future__ import annotations

import json
import math
import time
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

_logger = logging.getLogger("AGL.benchmark")

# Number of bins for calibration reliability diagram
CALIBRATION_BINS = 10

# Default contract-level threshold (may be overridden by ROC optimization)
DEFAULT_CONTRACT_THRESHOLD = 0.5


# ═══════════════════════════════════════════════════════════════
#  Ground Truth Definitions
# ═══════════════════════════════════════════════════════════════

# SWC Registry — expected vulnerabilities per SWC ID
SWC_GROUND_TRUTH: Dict[str, Dict[str, Any]] = {
    "SWC-101": {
        "category": "arithmetic",
        "severity_min": "medium",
        "exploitable": True,
        "description": "Integer Overflow and Underflow",
    },
    "SWC-104": {
        "category": "unchecked_call",
        "severity_min": "medium",
        "exploitable": True,
        "description": "Unchecked Call Return Value",
    },
    "SWC-106": {
        "category": "selfdestruct",
        "severity_min": "high",
        "exploitable": True,
        "description": "Unprotected SELFDESTRUCT",
    },
    "SWC-107": {
        "category": "reentrancy",
        "severity_min": "high",
        "exploitable": True,
        "description": "Reentrancy",
    },
    "SWC-110": {
        "category": "logic",
        "severity_min": "medium",
        "exploitable": False,
        "description": "Assert Violation",
    },
    "SWC-112": {
        "category": "delegatecall",
        "severity_min": "high",
        "exploitable": True,
        "description": "Delegatecall to Untrusted Callee",
    },
    "SWC-113": {
        "category": "logic",
        "severity_min": "medium",
        "exploitable": True,
        "description": "DoS with Failed Call",
    },
    "SWC-114": {
        "category": "timestamp",
        "severity_min": "low",
        "exploitable": False,
        "description": "Timestamp Dependence",
    },
    "SWC-115": {
        "category": "access_control",
        "severity_min": "medium",
        "exploitable": True,
        "description": "Authorization through tx.origin",
    },
    "SWC-116": {
        "category": "timestamp",
        "severity_min": "low",
        "exploitable": False,
        "description": "Block values as proxies for time",
    },
    "SWC-120": {
        "category": "logic",
        "severity_min": "medium",
        "exploitable": True,
        "description": "Weak Sources of Randomness",
    },
    "SWC-124": {
        "category": "logic",
        "severity_min": "medium",
        "exploitable": True,
        "description": "Write to Arbitrary Storage Location",
    },
    "SWC-128": {
        "category": "logic",
        "severity_min": "low",
        "exploitable": False,
        "description": "DoS With Block Gas Limit",
    },
    "SWC-131": {
        "category": "logic",
        "severity_min": "low",
        "exploitable": False,
        "description": "Presence of unused variables",
    },
    "SWC-134": {
        "category": "logic",
        "severity_min": "medium",
        "exploitable": True,
        "description": "Message call with hardcoded gas",
    },
    "SWC-135": {
        "category": "arithmetic",
        "severity_min": "medium",
        "exploitable": True,
        "description": "Code With No Effects",
    },
    "SWC-136": {
        "category": "access_control",
        "severity_min": "high",
        "exploitable": True,
        "description": "Unencrypted Private Data On-Chain",
    },
}

# Damn Vulnerable DeFi — challenge names with expected finding categories
DVDEFI_GROUND_TRUTH: Dict[str, Dict[str, Any]] = {
    "unstoppable": {"categories": ["logic", "flash_loan"], "exploitable": True},
    "naive-receiver": {
        "categories": ["access_control", "flash_loan"],
        "exploitable": True,
    },
    "truster": {"categories": ["access_control", "flash_loan"], "exploitable": True},
    "side-entrance": {"categories": ["reentrancy", "flash_loan"], "exploitable": True},
    "the-rewarder": {"categories": ["flash_loan", "logic"], "exploitable": True},
    "selfie": {"categories": ["flash_loan", "access_control"], "exploitable": True},
    "compromised": {"categories": ["oracle_manipulation"], "exploitable": True},
    "puppet": {"categories": ["oracle_manipulation"], "exploitable": True},
    "puppet-v2": {"categories": ["oracle_manipulation"], "exploitable": True},
    "free-rider": {"categories": ["reentrancy", "logic"], "exploitable": True},
    "backdoor": {"categories": ["access_control", "logic"], "exploitable": True},
    "climber": {"categories": ["access_control", "logic"], "exploitable": True},
}


@dataclass
class CalibrationBin:
    """One bin in the reliability diagram."""

    bin_start: float = 0.0
    bin_end: float = 0.0
    bin_midpoint: float = 0.0
    count: int = 0
    avg_predicted: float = 0.0  # Mean predicted P in this bin
    avg_actual: float = 0.0  # Fraction actually exploitable
    gap: float = 0.0  # |avg_predicted - avg_actual|

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bin": f"{self.bin_start:.1f}-{self.bin_end:.1f}",
            "count": self.count,
            "avg_predicted_P": round(self.avg_predicted, 4),
            "actual_exploit_rate": round(self.avg_actual, 4),
            "gap": round(self.gap, 4),
        }


@dataclass
class CalibrationResult:
    """
    Probability calibration metrics.

    Answers: "When the model says P=0.8, is it really ~80% correct?"

    Key metrics:
      - Brier Score: Mean squared error of probabilities (lower = better)
        BS = (1/N) * Σ (P_i - y_i)²   where y_i ∈ {0, 1}
        Perfect = 0.0, worst = 1.0

      - Expected Calibration Error (ECE): Weighted average gap across bins
        ECE = Σ (n_b/N) * |avg_P_b - actual_rate_b|
        Perfect = 0.0

      - Reliability bins: Per-bucket predicted vs actual rates

      - Overconfidence flag: True if model predicts high P but low actual rate
    """

    brier_score: float = 0.0
    ece: float = 0.0
    max_calibration_error: float = 0.0
    bins: List[CalibrationBin] = field(default_factory=list)
    total_predictions: int = 0

    # Diagnosis
    is_overconfident: bool = False
    is_underconfident: bool = False
    overconfident_bins: List[str] = field(default_factory=list)
    underconfident_bins: List[str] = field(default_factory=list)
    diagnosis: str = ""

    # Raw data for re-analysis
    raw_predictions: List[Tuple[float, int]] = field(default_factory=list)
    # (predicted_P, ground_truth_0_or_1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brier_score": round(self.brier_score, 6),
            "ece": round(self.ece, 6),
            "max_calibration_error": round(self.max_calibration_error, 6),
            "total_predictions": self.total_predictions,
            "is_overconfident": self.is_overconfident,
            "is_underconfident": self.is_underconfident,
            "overconfident_bins": self.overconfident_bins,
            "underconfident_bins": self.underconfident_bins,
            "diagnosis": self.diagnosis,
            "bins": [b.to_dict() for b in self.bins],
        }


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""

    # Per-contract results
    contract_results: List[Dict[str, Any]] = field(default_factory=list)

    # Aggregate metrics
    total_contracts: int = 0
    contracts_with_findings: int = 0

    # Confusion matrix
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0

    # Computed metrics
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    accuracy: float = 0.0

    # Per-category breakdown
    per_category: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # ROC data points (threshold → TPR, FPR)
    roc_data: List[Tuple[float, float, float]] = field(default_factory=list)

    # ── Calibration ──
    calibration: Optional[CalibrationResult] = None

    # ── Contract-level intelligence (Phase 2) ──
    contract_calibration: Optional[Any] = None  # ContractCalibrationResult
    contract_verdicts: List[Dict[str, Any]] = field(default_factory=list)
    contract_threshold: float = 0.5

    # Timing
    total_duration_s: float = 0.0
    avg_duration_s: float = 0.0

    def compute_metrics(self):
        """Compute precision, recall, F1     from confusion matrix."""
        tp, fp, tn, fn = (
            self.true_positives,
            self.false_positives,
            self.true_negatives,
            self.false_negatives,
        )
        total = tp + fp + tn + fn

        self.precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        self.recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        self.f1 = (
            2 * self.precision * self.recall / (self.precision + self.recall)
            if (self.precision + self.recall) > 0
            else 0.0
        )
        self.false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        self.false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        self.accuracy = (tp + tn) / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "total_contracts": self.total_contracts,
            "contracts_with_findings": self.contracts_with_findings,
            "confusion_matrix": {
                "TP": self.true_positives,
                "FP": self.false_positives,
                "TN": self.true_negatives,
                "FN": self.false_negatives,
            },
            "metrics": {
                "precision": round(self.precision, 4),
                "recall": round(self.recall, 4),
                "f1": round(self.f1, 4),
                "accuracy": round(self.accuracy, 4),
                "false_positive_rate": round(self.false_positive_rate, 4),
                "false_negative_rate": round(self.false_negative_rate, 4),
            },
            "per_category": self.per_category,
            "timing": {
                "total_s": round(self.total_duration_s, 2),
                "avg_s": round(self.avg_duration_s, 2),
            },
            "roc_data": [
                {"threshold": round(t, 2), "tpr": round(tpr, 4), "fpr": round(fpr, 4)}
                for t, tpr, fpr in self.roc_data
            ],
            "contract_results": self.contract_results,
        }
        if self.calibration:
            d["calibration"] = self.calibration.to_dict()
        if self.contract_calibration:
            d["contract_calibration"] = (
                self.contract_calibration.to_dict()
                if hasattr(self.contract_calibration, "to_dict")
                else self.contract_calibration
            )
        if self.contract_verdicts:
            d["contract_verdicts"] = self.contract_verdicts
        return d


class BenchmarkRunner:
    """
    Statistical evaluation framework for AGL Security Tool.

    Measures precision/recall/F1 against ground-truth contract suites.
    """

    def __init__(
        self,
        scan_mode: str = "deep",
        skip_llm: bool = True,
        contract_threshold: Optional[float] = None,
    ):
        """
        Args:
            scan_mode: 'quick' or 'deep' scan mode
            skip_llm: Skip LLM enrichment during benchmark (faster)
            contract_threshold: Override Noisy-OR threshold (None = use default/ROC)
        """
        self.scan_mode = scan_mode
        self.skip_llm = skip_llm
        self._audit = None
        self._contract_threshold = contract_threshold

        # Calibration data collector — (predicted_P, ground_truth_0_or_1)
        self._calibration_data: List[Tuple[float, int]] = []

    def _get_audit(self):
        """Lazy-load the audit engine."""
        if self._audit is None:
            from agl_security_tool.core import AGLSecurityAudit

            self._audit = AGLSecurityAudit()
        return self._audit

    # ─── SWC Registry Benchmark ─────────────────────────────
    def run_swc_benchmark(self, swc_dir: str) -> BenchmarkResult:
        """
        Run benchmark against SWC registry test contracts.

        Expected directory structure:
            swc_dir/
              SWC-101/
                SWC-101.sol (or any .sol file)
              SWC-107/
                ...
              safe/
                safe_contract.sol (known-safe contracts)
        """
        result = BenchmarkResult()
        swc_path = Path(swc_dir)

        if not swc_path.exists():
            _logger.error("SWC directory not found: %s", swc_dir)
            return result

        self._calibration_data = []  # Reset for this benchmark run
        t0 = time.monotonic()

        # Process vulnerable contracts
        for swc_id, truth in SWC_GROUND_TRUTH.items():
            swc_folder = swc_path / swc_id
            if not swc_folder.exists():
                continue

            sol_files = list(swc_folder.glob("*.sol"))
            for sol_file in sol_files:
                cr = self._scan_and_evaluate(
                    str(sol_file),
                    expected_categories=[truth["category"]],
                    expected_exploitable=truth["exploitable"],
                    label=swc_id,
                )
                result.contract_results.append(cr)
                result.total_contracts += 1

                if cr["detected"]:
                    result.true_positives += 1
                    result.contracts_with_findings += 1
                else:
                    result.false_negatives += 1

                # Per-category
                cat = truth["category"]
                if cat not in result.per_category:
                    result.per_category[cat] = {"tp": 0, "fp": 0, "fn": 0}
                if cr["detected"]:
                    result.per_category[cat]["tp"] += 1
                else:
                    result.per_category[cat]["fn"] += 1

        # Process safe contracts — use Noisy-OR for classification
        from agl_security_tool.contract_intelligence import ContractAggregator

        swc_agg = ContractAggregator()
        safe_dir = swc_path / "safe"
        if safe_dir.exists():
            for sol_file in safe_dir.glob("*.sol"):
                cr = self._scan_and_evaluate(
                    str(sol_file),
                    expected_categories=[],
                    expected_exploitable=False,
                    label="safe",
                )
                result.contract_results.append(cr)
                result.total_contracts += 1

                finding_probs = [
                    f.get("probability", 0.0) for f in cr.get("findings", [])
                ]
                verdict = swc_agg.classify(
                    finding_probs,
                    threshold=self._contract_threshold or DEFAULT_CONTRACT_THRESHOLD,
                )
                cr["contract_verdict"] = verdict.to_dict()

                if verdict.is_vulnerable:
                    result.false_positives += 1
                    result.contracts_with_findings += 1
                else:
                    result.true_negatives += 1

        result.total_duration_s = time.monotonic() - t0
        if result.total_contracts > 0:
            result.avg_duration_s = result.total_duration_s / result.total_contracts

        # Compute ROC curve
        result.roc_data = self._compute_roc(result.contract_results)

        # Compute per-category F1
        for cat, counts in result.per_category.items():
            tp, fp, fn = counts.get("tp", 0), counts.get("fp", 0), counts.get("fn", 0)
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0
            counts["precision"] = round(prec, 4)
            counts["recall"] = round(rec, 4)
            counts["f1"] = round(
                2 * prec * rec / (prec + rec) if prec + rec > 0 else 0, 4
            )

        result.compute_metrics()
        self.compute_calibration_and_attach(result)
        return result

    # ─── Damn Vulnerable DeFi Benchmark ────────────────────
    def run_dvdefi_benchmark(self, dvd_dir: str) -> BenchmarkResult:
        """
        Run benchmark against Damn Vulnerable DeFi contracts.

        Expected directory structure:
            dvd_dir/
              contracts/
                unstoppable/
                  *.sol
                naive-receiver/
                  *.sol
                ...
        """
        result = BenchmarkResult()
        dvd_path = Path(dvd_dir) / "contracts"

        if not dvd_path.exists():
            dvd_path = Path(dvd_dir)

        self._calibration_data = []  # Reset for this benchmark run
        t0 = time.monotonic()

        for challenge, truth in DVDEFI_GROUND_TRUTH.items():
            challenge_dir = dvd_path / challenge
            if not challenge_dir.exists():
                continue

            sol_files = list(challenge_dir.rglob("*.sol"))
            for sol_file in sol_files:
                cr = self._scan_and_evaluate(
                    str(sol_file),
                    expected_categories=truth["categories"],
                    expected_exploitable=truth["exploitable"],
                    label=f"dvd-{challenge}",
                )
                result.contract_results.append(cr)
                result.total_contracts += 1

                if cr["detected"]:
                    result.true_positives += 1
                    result.contracts_with_findings += 1
                else:
                    result.false_negatives += 1

                for cat in truth["categories"]:
                    if cat not in result.per_category:
                        result.per_category[cat] = {"tp": 0, "fp": 0, "fn": 0}
                    if cr["detected"]:
                        result.per_category[cat]["tp"] += 1
                    else:
                        result.per_category[cat]["fn"] += 1

        result.total_duration_s = time.monotonic() - t0
        if result.total_contracts > 0:
            result.avg_duration_s = result.total_duration_s / result.total_contracts

        result.roc_data = self._compute_roc(result.contract_results)
        result.compute_metrics()
        self.compute_calibration_and_attach(result)
        return result

    # ─── Custom Contract Suite ─────────────────────────────
    def run_custom_benchmark(
        self,
        contracts: List[Dict[str, Any]],
    ) -> BenchmarkResult:
        """
        Run benchmark against a custom contract list.

        Each entry in contracts:
            {
                "path": "path/to/contract.sol",
                "expected_categories": ["reentrancy", "access_control"],
                "expected_exploitable": True,
                "label": "my-contract-1"
            }
        """
        result = BenchmarkResult()
        self._calibration_data = []  # Reset for this benchmark run
        t0 = time.monotonic()

        # Lazy import to avoid circular dependency
        from agl_security_tool.contract_intelligence import (
            ContractAggregator,
            ContractMetrics,
            extract_contract_predictions,
        )

        agg = ContractAggregator()

        for entry in contracts:
            cr = self._scan_and_evaluate(
                entry["path"],
                expected_categories=entry.get("expected_categories", []),
                expected_exploitable=entry.get("expected_exploitable", True),
                label=entry.get("label", Path(entry["path"]).stem),
            )
            result.contract_results.append(cr)
            result.total_contracts += 1

            # ── Contract-level classification via dampened Z3-aware aggregate ──
            finding_probs = [f.get("probability", 0.0) for f in cr.get("findings", [])]
            finding_sevs = [f.get("severity", "") for f in cr.get("findings", [])]
            verdict = agg.classify(
                finding_probs,
                finding_sevs,
                threshold=self._contract_threshold or DEFAULT_CONTRACT_THRESHOLD,
                findings=cr.get("findings"),
            )
            cr["contract_verdict"] = verdict.to_dict()

            if entry.get("expected_exploitable", True):
                # Vulnerable contract: use category detection for TP/FN
                if cr["detected"]:
                    result.true_positives += 1
                else:
                    result.false_negatives += 1
            else:
                # Safe contract: use Noisy-OR verdict instead of severity check
                if verdict.is_vulnerable:
                    result.false_positives += 1
                else:
                    result.true_negatives += 1

            if cr.get("findings"):
                result.contracts_with_findings += 1

        result.total_duration_s = time.monotonic() - t0
        if result.total_contracts > 0:
            result.avg_duration_s = result.total_duration_s / result.total_contracts

        result.roc_data = self._compute_roc(result.contract_results)
        result.compute_metrics()
        self.compute_calibration_and_attach(result)

        # ── Contract-level calibration (Phase 2) ──
        result_dict = result.to_dict()
        contract_preds = extract_contract_predictions(result_dict)
        threshold = self._contract_threshold or DEFAULT_CONTRACT_THRESHOLD
        contract_cal = ContractMetrics.compute(contract_preds, threshold=threshold)
        contract_cal.method = "dampened_z3"
        result.contract_calibration = contract_cal
        result.contract_threshold = threshold

        # Store verdicts for debugging
        result.contract_verdicts = [
            cr.get("contract_verdict", {}) for cr in result.contract_results
        ]

        return result

    # ─── Internal scan helper ──────────────────────────────
    def _scan_and_evaluate(
        self,
        file_path: str,
        expected_categories: List[str],
        expected_exploitable: bool,
        label: str,
    ) -> Dict[str, Any]:
        """Scan a contract and evaluate against ground truth."""
        audit = self._get_audit()

        t0 = time.monotonic()
        try:
            if self.scan_mode == "deep":
                scan_result = audit.deep_scan(file_path)
            else:
                scan_result = audit.quick_scan(file_path)
        except Exception as e:
            _logger.error("Scan failed for %s: %s", file_path, e)
            return {
                "file": file_path,
                "label": label,
                "error": str(e),
                "detected": False,
                "findings": [],
                "max_probability": 0.0,
                "duration_s": time.monotonic() - t0,
            }

        duration = time.monotonic() - t0

        # Extract findings
        findings = scan_result.get("all_findings_unified", [])

        # Check if expected categories were detected
        found_categories = set()
        for f in findings:
            cat = f.get("category", "").lower()
            for key in expected_categories:
                if key in cat:
                    found_categories.add(key)

        detected = len(found_categories) > 0 if expected_categories else False

        # Max probability across findings
        max_prob = 0.0
        per_finding_probs = []
        for f in findings:
            p = f.get("probability", f.get("confidence", 0))
            if isinstance(p, str):
                p = {"high": 0.9, "medium": 0.7, "low": 0.5}.get(p.lower(), 0.5)
            p = float(p)
            max_prob = max(max_prob, p)
            per_finding_probs.append(p)

        # ── Collect calibration data (per-finding level) ──
        # Ground truth: every finding in a vulnerable contract is "truly
        # dangerous" (label=1), every finding in a safe contract is "noise"
        # (label=0).  This aligns with the contract-level evaluation that
        # determines TP/FP/TN/FN and with the training-data labelling.
        for f_idx, f in enumerate(findings):
            f_prob = per_finding_probs[f_idx] if f_idx < len(per_finding_probs) else 0.0
            ground_truth = 1 if expected_exploitable else 0
            self._calibration_data.append((f_prob, ground_truth))

        # If contract is exploitable but we found nothing → record a missed prediction
        if expected_exploitable and not findings:
            # The model implicitly predicted P≈0 for a truly exploitable contract
            self._calibration_data.append((0.0, 1))

        # If contract is safe and we found high-severity → record false alarm
        if not expected_exploitable and findings:
            for f_idx, f in enumerate(findings):
                sev = f.get("severity", "").lower()
                if sev in ("critical", "high"):
                    f_prob = (
                        per_finding_probs[f_idx]
                        if f_idx < len(per_finding_probs)
                        else 0.5
                    )
                    self._calibration_data.append((f_prob, 0))

        # Compute contract-level aggregate at scan time
        from agl_security_tool.contract_intelligence import ContractAggregator

        _scan_agg = ContractAggregator()
        noisy_or_p = _scan_agg.noisy_or(per_finding_probs)

        # Build finding dicts with Z3/proof data for dampened aggregate
        finding_dicts = [
            {
                "title": f.get("title", ""),
                "severity": f.get("severity", ""),
                "category": f.get("category", ""),
                "confidence": f.get("confidence", f.get("probability", 0.5)),
                "probability": (
                    per_finding_probs[i] if i < len(per_finding_probs) else 0.0
                ),
                "risk_breakdown": f.get("risk_breakdown", {}),
                "exploit_proof": f.get("exploit_proof", {}),
                "confirmed_by": f.get("confirmed_by", []),
                "ground_truth": None,  # filled during calibration
            }
            for i, f in enumerate(findings[:20])
        ]
        dampened_p = _scan_agg.dampened_aggregate(finding_dicts)

        return {
            "file": file_path,
            "label": label,
            "expected_categories": expected_categories,
            "expected_exploitable": expected_exploitable,
            "detected": detected,
            "found_categories": list(found_categories),
            "findings_count": len(findings),
            "findings": finding_dicts,
            "max_probability": max_prob,
            "noisy_or_probability": noisy_or_p,
            "dampened_probability": dampened_p,
            "duration_s": round(duration, 2),
        }

    # ─── ROC Curve Computation ─────────────────────────────
    def _compute_roc(
        self, contract_results: List[Dict]
    ) -> List[Tuple[float, float, float]]:
        """Compute ROC data points using dampened Z3-aware aggregate."""
        from agl_security_tool.contract_intelligence import ContractAggregator

        roc_agg = ContractAggregator()

        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        roc = []

        for threshold in thresholds:
            tp = fp = tn = fn = 0
            for cr in contract_results:
                findings = cr.get("findings", [])
                p_contract = roc_agg.dampened_aggregate(findings)
                predicted_positive = p_contract >= threshold
                actual_positive = cr.get("expected_exploitable", False)

                if predicted_positive and actual_positive:
                    tp += 1
                elif predicted_positive and not actual_positive:
                    fp += 1
                elif not predicted_positive and actual_positive:
                    fn += 1
                else:
                    tn += 1

            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0  # True positive rate
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0  # False positive rate
            roc.append((threshold, tpr, fpr))

        return roc

    # ═══════════════════════════════════════════════════════════════
    #  Calibration — Brier Score + ECE + Reliability Diagram
    # ═══════════════════════════════════════════════════════════════

    def compute_calibration(
        self,
        predictions: Optional[List[Tuple[float, int]]] = None,
        num_bins: int = CALIBRATION_BINS,
    ) -> CalibrationResult:
        """
        Compute probability calibration metrics.

        Uses the (predicted_P, ground_truth) pairs collected during benchmark,
        or accepts external predictions list.

        Args:
            predictions: Optional list of (predicted_probability, actual_label)
                         where actual_label ∈ {0, 1}
            num_bins: Number of bins for reliability diagram (default 10)

        Returns:
            CalibrationResult with Brier Score, ECE, reliability bins, diagnosis
        """
        data = predictions or self._calibration_data
        cal = CalibrationResult()
        cal.total_predictions = len(data)
        cal.raw_predictions = list(data)

        if not data:
            cal.diagnosis = "No calibration data — run a benchmark first"
            return cal

        # ── Brier Score ──
        # BS = (1/N) × Σ (P_i - y_i)²
        brier_sum = 0.0
        for p, y in data:
            brier_sum += (p - y) ** 2
        cal.brier_score = brier_sum / len(data)

        # ── Reliability Bins + ECE ──
        bin_width = 1.0 / num_bins
        bins: List[CalibrationBin] = []

        for b in range(num_bins):
            b_start = b * bin_width
            b_end = (b + 1) * bin_width
            b_mid = (b_start + b_end) / 2.0

            # Collect predictions falling in this bin
            bin_preds = [(p, y) for p, y in data if b_start <= p < b_end]
            # Last bin includes 1.0
            if b == num_bins - 1:
                bin_preds = [(p, y) for p, y in data if b_start <= p <= b_end]

            cb = CalibrationBin(
                bin_start=b_start,
                bin_end=b_end,
                bin_midpoint=b_mid,
                count=len(bin_preds),
            )

            if bin_preds:
                cb.avg_predicted = sum(p for p, _ in bin_preds) / len(bin_preds)
                cb.avg_actual = sum(y for _, y in bin_preds) / len(bin_preds)
                cb.gap = abs(cb.avg_predicted - cb.avg_actual)
            bins.append(cb)

        cal.bins = bins

        # ECE = Σ (n_b / N) × |avg_P_b - actual_rate_b|
        N = len(data)
        ece = 0.0
        max_ce = 0.0
        for cb in bins:
            if cb.count > 0:
                weight = cb.count / N
                ece += weight * cb.gap
                max_ce = max(max_ce, cb.gap)
        cal.ece = ece
        cal.max_calibration_error = max_ce

        # ── Overconfidence / Underconfidence Detection ──
        overconf_bins = []
        underconf_bins = []
        for cb in bins:
            if cb.count < 3:  # Skip bins with too few samples
                continue
            # Overconfident: predicted >> actual (model says high P but few real exploits)
            if cb.avg_predicted > cb.avg_actual + 0.15:
                overconf_bins.append(
                    f"{cb.bin_start:.1f}-{cb.bin_end:.1f} "
                    f"(predicted={cb.avg_predicted:.2f}, actual={cb.avg_actual:.2f})"
                )
            # Underconfident: predicted << actual (model says low P but many real exploits)
            if cb.avg_actual > cb.avg_predicted + 0.15:
                underconf_bins.append(
                    f"{cb.bin_start:.1f}-{cb.bin_end:.1f} "
                    f"(predicted={cb.avg_predicted:.2f}, actual={cb.avg_actual:.2f})"
                )

        cal.overconfident_bins = overconf_bins
        cal.underconfident_bins = underconf_bins
        cal.is_overconfident = len(overconf_bins) > 0
        cal.is_underconfident = len(underconf_bins) > 0

        # ── Diagnosis ──
        if cal.brier_score < 0.05:
            quality = "ممتاز (Excellent)"
        elif cal.brier_score < 0.15:
            quality = "جيد (Good)"
        elif cal.brier_score < 0.25:
            quality = "متوسط (Fair)"
        else:
            quality = "ضعيف (Poor)"

        diag_parts = [f"Brier Score: {cal.brier_score:.4f} — {quality}"]
        if cal.ece < 0.05:
            diag_parts.append(f"ECE: {cal.ece:.4f} — well-calibrated")
        elif cal.ece < 0.10:
            diag_parts.append(f"ECE: {cal.ece:.4f} — reasonably calibrated")
        else:
            diag_parts.append(f"ECE: {cal.ece:.4f} — NEEDS RECALIBRATION")

        if cal.is_overconfident:
            diag_parts.append(
                f"⚠ OVERCONFIDENT in {len(overconf_bins)} bin(s): "
                "model predicts higher P than reality"
            )
        if cal.is_underconfident:
            diag_parts.append(
                f"⚠ UNDERCONFIDENT in {len(underconf_bins)} bin(s): "
                "model under-predicts actual exploit rate"
            )

        cal.diagnosis = " | ".join(diag_parts)
        return cal

    def compute_calibration_and_attach(
        self, result: BenchmarkResult
    ) -> BenchmarkResult:
        """
        Compute calibration from collected data and attach to BenchmarkResult.
        Call this after a benchmark run.
        """
        result.calibration = self.compute_calibration()
        return result

    # ── Standalone Calibration from External Data ──
    @staticmethod
    def calibrate_from_findings(
        findings: List[Dict[str, Any]],
        ground_truth_map: Dict[str, bool],
    ) -> CalibrationResult:
        """
        Compute calibration from a list of scored findings + ground truth.

        Args:
            findings: List of finding dicts with 'probability' and 'category'
            ground_truth_map: {category: True/False} — is this category a real exploit?

        Returns:
            CalibrationResult
        """
        data = []
        for f in findings:
            p = f.get("probability", f.get("confidence", 0.5))
            if isinstance(p, str):
                p = {"high": 0.9, "medium": 0.7, "low": 0.5}.get(p.lower(), 0.5)
            cat = f.get("category", "").lower()
            # Check if any ground truth key matches
            is_real = False
            for gt_key, gt_val in ground_truth_map.items():
                if gt_key in cat:
                    is_real = gt_val
                    break
            data.append((float(p), 1 if is_real else 0))

        runner = BenchmarkRunner.__new__(BenchmarkRunner)
        runner._calibration_data = []
        return runner.compute_calibration(predictions=data)

    # ── Calibration Summary Print ──
    @staticmethod
    def print_calibration_summary(cal: CalibrationResult):
        """
        Print calibration results — reliability diagram + diagnosis.

        This is the key output that demonstrates whether:
        'When I say P=0.8, am I really correct ~80% of the time?'
        """
        print("\n" + "=" * 70)
        print("  AGL Probability Calibration Report")
        print("  " + "─" * 66)
        print(f"  Total predictions:       {cal.total_predictions}")
        print(f"  Brier Score:             {cal.brier_score:.6f}  ", end="")
        if cal.brier_score < 0.05:
            print("✅ Excellent")
        elif cal.brier_score < 0.15:
            print("🟡 Good")
        elif cal.brier_score < 0.25:
            print("🟠 Fair")
        else:
            print("🔴 Poor")
        print(f"  ECE:                     {cal.ece:.6f}  ", end="")
        if cal.ece < 0.05:
            print("✅ Well-calibrated")
        elif cal.ece < 0.10:
            print("🟡 Reasonable")
        else:
            print("🔴 Needs recalibration")
        print(f"  Max Calibration Error:   {cal.max_calibration_error:.6f}")
        print()

        # ── Reliability Diagram (text) ──
        print("  Reliability Diagram (Predicted P vs Actual Exploit Rate):")
        print(
            f"  {'Bin':>11} {'Count':>6} {'Avg P':>8} {'Actual':>8} {'Gap':>8} {'Status':>12}"
        )
        print("  " + "─" * 60)
        for cb in cal.bins:
            if cb.count == 0:
                status = "   (empty)"
            elif cb.gap < 0.05:
                status = "  ✅ aligned"
            elif cb.avg_predicted > cb.avg_actual:
                status = "  ⬆ overconf"
            else:
                status = "  ⬇ underconf"
            label = f"{cb.bin_start:.1f}-{cb.bin_end:.1f}"
            print(
                f"  {label:>11} {cb.count:>6} "
                f"{cb.avg_predicted:>8.4f} {cb.avg_actual:>8.4f} "
                f"{cb.gap:>8.4f} {status}"
            )

        # ── Bar chart (ASCII) ──
        print()
        print("  Calibration Curve (ideal = diagonal):")
        print("  1.0 ┬" + "─" * 42)
        for row_val in [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]:
            row_str = f"  {row_val:.1f} │"
            for cb in cal.bins:
                if cb.count == 0:
                    row_str += " ·  "
                elif abs(cb.avg_actual - row_val) < 0.05:
                    row_str += " ■  "
                elif abs(cb.bin_midpoint - row_val) < 0.05:
                    row_str += " ◇  "
                else:
                    row_str += "    "
            print(row_str)
        print("      └" + "────" * CALIBRATION_BINS)
        labels = "".join(f" {cb.bin_midpoint:.1f}" for cb in cal.bins)
        print(f"       {labels}")
        print("       ■ = actual rate, ◇ = ideal (diagonal)")

        # ── Warnings ──
        if cal.is_overconfident:
            print()
            print("  ⚠️  WARNING: Model is OVERCONFIDENT in these bins:")
            for msg in cal.overconfident_bins:
                print(f"       → {msg}")
            print("       The model predicts high exploit probability")
            print("       but actual exploit rate is lower.")
            print("       → Consider: lower w_heuristic, raise bias in RiskCore")

        if cal.is_underconfident:
            print()
            print("  ⚠️  WARNING: Model is UNDERCONFIDENT in these bins:")
            for msg in cal.underconfident_bins:
                print(f"       → {msg}")
            print("       The model predicts low probability")
            print("       but many findings are actually exploitable.")
            print("       → Consider: raise w_formal, lower bias in RiskCore")

        print("\n  Diagnosis: " + cal.diagnosis)
        print("=" * 70)

    @staticmethod
    def export_calibration_json(cal: CalibrationResult, path: str):
        """Export calibration results to standalone JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cal.to_dict(), f, indent=2, ensure_ascii=False)
        _logger.info("Calibration exported to: %s", path)

    # ─── Export Methods ────────────────────────────────────
    @staticmethod
    def export_json(result: BenchmarkResult, path: str):
        """Export benchmark results to JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        _logger.info("Benchmark results exported to: %s", path)

    @staticmethod
    def export_csv(result: BenchmarkResult, path: str):
        """Export per-contract results to CSV."""
        import csv

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "file",
                    "label",
                    "expected_exploitable",
                    "detected",
                    "findings_count",
                    "max_probability",
                    "duration_s",
                ],
            )
            writer.writeheader()
            for cr in result.contract_results:
                writer.writerow(
                    {
                        "file": cr.get("file", ""),
                        "label": cr.get("label", ""),
                        "expected_exploitable": cr.get("expected_exploitable", ""),
                        "detected": cr.get("detected", ""),
                        "findings_count": cr.get("findings_count", 0),
                        "max_probability": cr.get("max_probability", 0),
                        "duration_s": cr.get("duration_s", 0),
                    }
                )
        _logger.info("Benchmark CSV exported to: %s", path)

    # ─── Pretty Print ─────────────────────────────────────
    @staticmethod
    def print_summary(result: BenchmarkResult):
        """Print benchmark summary to console."""
        print("\n" + "=" * 65)
        print("  AGL Security Tool — Benchmark Results")
        print("=" * 65)
        print(f"  Contracts tested:  {result.total_contracts}")
        print(f"  With findings:     {result.contracts_with_findings}")
        print(f"  Total time:        {result.total_duration_s:.1f}s")
        print(f"  Avg per contract:  {result.avg_duration_s:.1f}s")
        print()
        print("  ┌─────────────────────────────────────┐")
        print(f"  │ Precision:  {result.precision:.1%}                    │")
        print(f"  │ Recall:     {result.recall:.1%}                    │")
        print(f"  │ F1 Score:   {result.f1:.1%}                    │")
        print(f"  │ Accuracy:   {result.accuracy:.1%}                    │")
        print(f"  │ FP Rate:    {result.false_positive_rate:.1%}                    │")
        print(f"  │ FN Rate:    {result.false_negative_rate:.1%}                    │")
        print("  └─────────────────────────────────────┘")
        print()

        if result.per_category:
            print("  Per-Category Breakdown:")
            print(f"  {'Category':<25} {'Prec':>6} {'Recall':>7} {'F1':>6}")
            print("  " + "-" * 50)
            for cat, metrics in sorted(result.per_category.items()):
                print(
                    f"  {cat:<25} {metrics.get('precision',0):>5.1%}"
                    f" {metrics.get('recall',0):>6.1%}"
                    f" {metrics.get('f1',0):>5.1%}"
                )

        if result.roc_data:
            print()
            print("  ROC Curve Data:")
            print(f"  {'Threshold':>10} {'TPR':>8} {'FPR':>8}")
            print("  " + "-" * 30)
            for t, tpr, fpr in result.roc_data:
                print(f"  {t:>10.2f} {tpr:>8.3f} {fpr:>8.3f}")

        # ── Print calibration if available ──
        if result.calibration and result.calibration.total_predictions > 0:
            BenchmarkRunner.print_calibration_summary(result.calibration)
        else:
            print("\n  (No calibration data — run with ground truth contracts)")

        # ── Print contract-level metrics (Phase 2) ──
        if result.contract_calibration:
            try:
                from agl_security_tool.contract_intelligence import (
                    print_contract_metrics,
                )

                print_contract_metrics(result.contract_calibration)
            except Exception:
                pass  # Graceful degradation if not available

        print("=" * 65)
