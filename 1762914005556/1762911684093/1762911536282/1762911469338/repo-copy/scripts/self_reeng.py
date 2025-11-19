#!/usr/bin/env python3
"""CLI wrapper for the Self-Engineering orchestrator (dry-run by default)."""
import argparse
from Learning_System.Self_Engineer import SelfEngineer


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--task', default='predict_y')
    p.add_argument('--budget', type=int, default=3)
    p.add_argument('--no-dry-run', dest='dry', action='store_false')
    args = p.parse_args()

    se = SelfEngineer()
    out = se.run_cycle(task=args.task, models_report={}, data_profile={}, budget=args.budget, dry_run=args.dry)
    print('Result:', out)


if __name__ == '__main__':
    main()
