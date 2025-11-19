#!/usr/bin/env python3
"""Wrapper around Learning_System.self_learning_cli that checks data file existence
and logs a helpful message instead of crashing when the CSV is missing.

Usage: python scripts/safe_self_learning.py --base ohm --data data/training/B_ohm_B.csv --out artifacts/models/ohm_B
"""
import argparse
import os
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--base', required=True)
parser.add_argument('--data', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--extra', nargs=argparse.REMAINDER)
args = parser.parse_args()

if not os.path.exists(args.data):
    print(f"SafeSelfLearning: data file not found, skipping training: {args.data}")
    sys.exit(0)

cmd = [sys.executable, '-m', 'Learning_System.self_learning_cli', '--base', args.base, '--data', args.data, '--out', args.out]
if args.extra:
    cmd.extend(args.extra)

print('SafeSelfLearning: running:', ' '.join(cmd))
proc = subprocess.run(cmd)
sys.exit(proc.returncode)
