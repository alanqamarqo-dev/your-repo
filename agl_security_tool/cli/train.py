#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║  AGL Weight Trainer — تدريب الأوزان من بيانات البنشمارك              ║
║  Learn RiskCore weights from labelled benchmark data                 ║
╚══════════════════════════════════════════════════════════════════════╝

Runs a benchmark suite, extracts (X, y) training pairs, trains logistic
regression via gradient descent, and saves optimized weights.

Usage:
    # Train from SWC ground truth
    python train_weights.py --dataset swc --swc-dir path/to/swc_contracts

    # Train from Damn Vulnerable DeFi
    python train_weights.py --dataset dvdefi --dvd-dir path/to/dvd_contracts

    # Train from custom JSON benchmark results
    python train_weights.py --dataset custom --benchmark-json results.json

    # Train from synthetic data (for testing the pipeline)
    python train_weights.py --dataset synthetic

Options:
    --lr           Learning rate (default: 0.1)
    --epochs       Max epochs (default: 1000)
    --l2           L2 regularization (default: 0.01)
    --output       Output weights path (default: artifacts/risk_weights.json)
    --level        'finding' or 'contract' level training (default: finding)
    --verbose      Show training progress
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import random
import sys
import time

# ── Path setup ──────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(
    os.path.dirname(_SCRIPT_DIR)
)  # cli/ → agl_security_tool/ → repo root
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from agl_security_tool.weight_optimizer import (
    WeightOptimizer,
    TrainingConfig,
    TrainingResult,
    FEATURE_NAMES,
)
from agl_security_tool.risk_core import RiskCore


def generate_synthetic_data(
    n_samples: int = 200, seed: int = 42
) -> tuple[list[list[float]], list[int]]:
    """
    Generate synthetic training data with known ground truth.

    The synthetic oracle uses:
        y = 1 if (2.0*Sf + 1.5*Sh + 1.0*Sp + 2.5*E + 0.0) > 0 else 0
    with Gaussian noise.

    The oracle bias (0.0) is calibrated so that a finding with zero
    evidence gets P≈50% — the model must see actual signals to decide.
    This prevents the trained bias from becoming too negative.
    """
    rng = random.Random(seed)
    X, y = [], []

    for _ in range(n_samples):
        sf = rng.random()  # formal [0,1]
        sh = rng.random()  # heuristic [0,1]
        sp = rng.random()  # profit [0,1]
        e = 1.0 if rng.random() > 0.7 else 0.0  # 30% chance exploit proven

        # Ground truth logit (known true weights)
        # bias=0: model learns to be neutral at zero evidence.
        # Positive weights mean: more evidence → more likely exploitable.
        logit = 2.0 * sf + 1.5 * sh + 1.0 * sp + 2.5 * e
        # Shift so that average sample is ~50/50
        logit -= 2.0  # mean(sf+sh+sp)≈1.5, mean(e)≈0.3 → mean(logit)≈2.0+1.5*0.5+1.0*0.5+0.75=3.5-2.0≈1.5
        # Add noise
        logit += rng.gauss(0, 0.5)
        # Sigmoid → probability → binary label
        p = 1.0 / (1.0 + math.exp(-logit))
        label = 1 if rng.random() < p else 0

        X.append([sf, sh, sp, e])
        y.append(label)

    pos = sum(y)
    neg = len(y) - pos
    print(f"  Synthetic data: {len(y)} samples ({pos} positive, {neg} negative)")
    print(f"  True weights: w_f=2.0, w_h=1.5, w_p=1.0, w_e=2.5, bias=-2.0")
    return X, y


def train_from_swc(
    swc_dir: str, level: str = "finding"
) -> tuple[list[list[float]], list[int]]:
    """Run SWC benchmark and extract training data."""
    from agl_security_tool.benchmark_runner import BenchmarkRunner

    print(f"  Running SWC benchmark on: {swc_dir}")
    runner = BenchmarkRunner(scan_mode="deep", skip_llm=True)
    result = runner.run_swc_benchmark(swc_dir)

    data = result.to_dict()
    if level == "contract":
        X, y = WeightOptimizer.extract_training_data_contract_level(data)
    else:
        X, y = WeightOptimizer.extract_training_data(data)

    print(f"  Extracted: {len(X)} training samples ({sum(y)} positive)")
    runner.print_summary(result)
    return X, y


def train_from_dvdefi(
    dvd_dir: str, level: str = "finding"
) -> tuple[list[list[float]], list[int]]:
    """Run DvDeFi benchmark and extract training data."""
    from agl_security_tool.benchmark_runner import BenchmarkRunner

    print(f"  Running DvDeFi benchmark on: {dvd_dir}")
    runner = BenchmarkRunner(scan_mode="deep", skip_llm=True)
    result = runner.run_dvdefi_benchmark(dvd_dir)

    data = result.to_dict()
    if level == "contract":
        X, y = WeightOptimizer.extract_training_data_contract_level(data)
    else:
        X, y = WeightOptimizer.extract_training_data(data)

    print(f"  Extracted: {len(X)} training samples ({sum(y)} positive)")
    runner.print_summary(result)
    return X, y


def train_from_json(
    json_path: str, level: str = "finding"
) -> tuple[list[list[float]], list[int]]:
    """Load benchmark results from JSON and extract training data."""
    print(f"  Loading benchmark results from: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if level == "contract":
        X, y = WeightOptimizer.extract_training_data_contract_level(data)
    else:
        X, y = WeightOptimizer.extract_training_data(data)

    print(f"  Extracted: {len(X)} training samples ({sum(y)} positive)")
    return X, y


def main():
    parser = argparse.ArgumentParser(
        description="AGL Weight Trainer — Learn RiskCore weights from benchmark data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python train_weights.py --dataset synthetic
  python train_weights.py --dataset swc --swc-dir path/to/SWC
  python train_weights.py --dataset dvdefi --dvd-dir path/to/DvDeFi
  python train_weights.py --dataset custom --benchmark-json results.json
        """,
    )

    parser.add_argument(
        "--dataset",
        choices=["swc", "dvdefi", "custom", "synthetic"],
        default="synthetic",
        help="Training data source (default: synthetic)",
    )
    parser.add_argument("--swc-dir", type=str, help="Path to SWC test contracts")
    parser.add_argument("--dvd-dir", type=str, help="Path to DvDeFi contracts")
    parser.add_argument(
        "--benchmark-json", type=str, help="Path to exported benchmark JSON"
    )
    parser.add_argument("--lr", type=float, default=0.1, help="Learning rate")
    parser.add_argument("--epochs", type=int, default=1000, help="Max training epochs")
    parser.add_argument("--l2", type=float, default=0.01, help="L2 regularization")
    parser.add_argument(
        "--batch-size", type=int, default=32, help="Batch size (0=full)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/risk_weights.json",
        help="Output weights path",
    )
    parser.add_argument(
        "--level",
        choices=["finding", "contract"],
        default="finding",
        help="Training granularity",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Verbose training output"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    print("\n" + "═" * 65)
    print("  AGL Weight Trainer")
    print("  " + "─" * 61)
    print(f"  Dataset:         {args.dataset}")
    print(f"  Level:           {args.level}")
    print(f"  Learning rate:   {args.lr}")
    print(f"  Epochs:          {args.epochs}")
    print(f"  L2 lambda:       {args.l2}")
    print(f"  Batch size:      {args.batch_size}")
    print(f"  Output:          {args.output}")
    print("═" * 65)
    print()

    # ── Get training data ──
    if args.dataset == "synthetic":
        X, y = generate_synthetic_data(n_samples=200, seed=args.seed)
    elif args.dataset == "swc":
        if not args.swc_dir:
            parser.error("--swc-dir required when --dataset=swc")
        X, y = train_from_swc(args.swc_dir, args.level)
    elif args.dataset == "dvdefi":
        if not args.dvd_dir:
            parser.error("--dvd-dir required when --dataset=dvdefi")
        X, y = train_from_dvdefi(args.dvd_dir, args.level)
    elif args.dataset == "custom":
        if not args.benchmark_json:
            parser.error("--benchmark-json required when --dataset=custom")
        X, y = train_from_json(args.benchmark_json, args.level)
    else:
        parser.error(f"Unknown dataset: {args.dataset}")

    if not X:
        print("\n❌ No training data extracted — aborting")
        sys.exit(1)

    # ── Class balance check ──
    pos = sum(y)
    neg = len(y) - pos
    print(
        f"\n  Class balance: {pos} positive ({pos / len(y):.1%}), "
        f"{neg} negative ({neg / len(y):.1%})"
    )
    if pos == 0:
        print(
            "  ⚠️  WARNING: No positive samples — model cannot learn to detect exploits"
        )
    if neg == 0:
        print(
            "  ⚠️  WARNING: No negative samples — model cannot learn to avoid false positives"
        )

    # ── Train ──
    print("\n  Training logistic regression...")
    config = TrainingConfig(
        learning_rate=args.lr,
        epochs=args.epochs,
        batch_size=args.batch_size,
        l2_lambda=args.l2,
        verbose=args.verbose,
        seed=args.seed,
    )

    rc = RiskCore(auto_load=False)  # Start from defaults, not saved
    new_weights = rc.fit_weights((X, y), save_path=args.output, config=config)

    # ── Verify ──
    print(f"\n  ✅ Weights saved to: {args.output}")
    print(
        f"  Final weights: {json.dumps({k: round(v, 4) for k, v in new_weights.items()})}"
    )

    # ── Verify loading works ──
    rc2 = RiskCore(auto_load=True)
    print(
        f"\n  Verification — RiskCore auto-loaded weights: "
        f"{json.dumps({k: round(v, 4) for k, v in rc2.weights.items()})}"
    )

    # ── Quick sanity check ──
    print("\n  Sanity check (sample predictions with learned weights):")
    test_cases = [
        ("High formal + exploit proven", [0.95, 0.5, 0.3, 1.0]),
        ("Low heuristic only", [0.0, 0.2, 0.0, 0.0]),
        ("Medium all signals", [0.5, 0.5, 0.5, 0.0]),
        ("Zero evidence", [0.0, 0.0, 0.0, 0.0]),
    ]
    for desc, features in test_cases:
        bd = rc.compute_exploit_probability(
            formal_score=features[0],
            heuristic_score=features[1],
            profit_score=features[2],
            exploit_proven=features[3] > 0.5,
        )
        print(f"    {desc:35s} → P={bd.probability:.4f}  {bd.severity}")

    print("\n  Done.\n")


if __name__ == "__main__":
    main()
