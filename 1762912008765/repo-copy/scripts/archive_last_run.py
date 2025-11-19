"""Append the last run report to data/experiences.jsonl using ExperienceMemory helper."""
from __future__ import annotations

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
from Learning_System.ExperienceMemory import append_experience


def main():
    rpath = 'reports/last_run.json'
    with open(rpath, 'r', encoding='utf-8-sig') as f:
        rep = json.load(f)
    append_experience('data/experiences.jsonl', rep)
    print('Appended report to data/experiences.jsonl')


if __name__ == '__main__':
    main()
