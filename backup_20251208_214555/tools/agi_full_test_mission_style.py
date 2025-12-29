#!/usr/bin/env python3
"""Run or reformat the Arabic AGI full test into mission-style JSON outputs.

Usage:
  python tools/agi_full_test_mission_style.py [--re-run] [--base-url http://127.0.0.1:8000/chat] [--token TOKEN]

This script will:
- If `--re-run` is provided, call the existing `tools/agi_full_test.run_test` to (re)execute the 17-question test.
- Load the consolidated results from `artifacts/agi_full_test/agi_full_test_results.json` (created by the harness) and
  convert each item into a mission-style JSON structure saved under
  `artifacts/agi_full_test_mission_style/`.

The mission-style output is a compact, structured JSON that mirrors the sample mission format the user provided.
"""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools"
ART_IN = ROOT / "artifacts" / "agi_full_test"
ART_OUT = ROOT / "artifacts" / "agi_full_test_mission_style"
ART_OUT.mkdir(parents=True, exist_ok=True)


def load_results() -> Dict[str, Any] | None:
    p = ART_IN / "agi_full_test_results.json"
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_mission(qitem: Dict[str, Any], session_id: str):
    qid = qitem.get("id") or qitem.get("qid") or "unknown"
    title = qitem.get("title") or ""
    prompt = qitem.get("prompt") or ""
    raw = qitem.get("raw_response") or qitem.get("raw") or qitem.get("raw_response", {})
    answer = qitem.get("answer_text") or qitem.get("answer") or None

    # Try to extract focused output or llm summary if present in raw
    focused = None
    if isinstance(raw, dict):
        focused = raw.get("focused_output") or raw.get("llm_summary") or raw.get("focused")

    mission_doc = {
        "mission_id": qid,
        "session_id": session_id,
        "mission_type": "AGI_Test",
        "title": title,
        "user_input": prompt,
        "answer_plain": answer,
        "focused_output": focused,
        "engines": qitem.get("meta") or (raw.get("meta") if isinstance(raw, dict) else None) or {},
        "raw_response": raw,
    }

    outp = ART_OUT / f"{qid}.mission.json"
    with outp.open("w", encoding="utf-8") as f:
        json.dump(mission_doc, f, ensure_ascii=False, indent=2)

    return mission_doc


def build_consolidated(results: Dict[str, Any]):
    session_id = results.get("session_id") or "unknown_session"
    items = results.get("items", [])
    consolidated = {"session_id": session_id, "count": len(items), "missions": []}
    for it in items:
        md = save_mission(it, session_id)
        consolidated["missions"].append({"mission_id": md["mission_id"], "title": md["title"], "file": f"{md["mission_id"]}.mission.json"})

    outp = ART_OUT / "agi_full_test_mission_results.json"
    with outp.open("w", encoding="utf-8") as f:
        json.dump(consolidated, f, ensure_ascii=False, indent=2)

    # also write a short human-readable report
    rpt = ART_OUT / "agi_full_test_mission_report.txt"
    with rpt.open("w", encoding="utf-8") as f:
        f.write(f"AGI Full Test - Mission Style Report\nSession: {session_id}\nTotal Missions: {len(items)}\n\n")
        for m in consolidated["missions"]:
            f.write(f"- {m['mission_id']}: {m['title']} -> {m['file']}\n")

    return consolidated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--re-run", action="store_true", help="Re-run the AGI test harness before formatting results")
    parser.add_argument("--base-url", default=os.getenv("AGI_TEST_BASE_URL","http://127.0.0.1:8000/chat"))
    parser.add_argument("--token", default=os.getenv("GENESIS_ALPHA_TOKEN"))
    args = parser.parse_args()

    if args.re_run:
        # import and run the existing harness
        try:
            from tools.agi_full_test import run_test
        except Exception as e:
            print("Could not import run_test from tools.agi_full_test:", e)
            return

        print("Re-running AGI full test (this may take a while)...")
        results = run_test(args.base_url, token=args.token, delay=0.5, session_id=None, stop_on_error=False)
    else:
        results = load_results()
        if results is None:
            print("No existing results found. Use --re-run to execute the test first.")
            return

    consolidated = build_consolidated(results)
    print("Mission-style outputs written to:", ART_OUT)
    print("Consolidated file:", ART_OUT / "agi_full_test_mission_results.json")


if __name__ == '__main__':
    main()
