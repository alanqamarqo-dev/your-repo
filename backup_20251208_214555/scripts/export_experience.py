#!/usr/bin/env python3
"""
repo-copy/scripts/export_experience.py
Export experiences from LTM (SQLite), events.jsonl, and STM (if available)
into a JSONL dataset and a finetuning-conformant JSON file.

This script is conservative and read-only: it will not modify databases or
models. It attempts to reuse existing project modules when available.
"""
from __future__ import annotations

import json
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


# Ensure repo-copy is on sys.path when run from repo root
HERE = Path(__file__).resolve()
REPO_COPY_ROOT = HERE.parent.parent
if str(REPO_COPY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_COPY_ROOT))


class ExperienceExporter:
    def __init__(self):
        self.experiences: List[Dict[str, Any]] = []

    def export_from_sqlite(self, db_path: str = "memory.sqlite") -> None:
        """Export suitable LTM rows from a SQLite file.

        The SQL/table names are best-effort; adapt if your project uses
        different schema names.
        """
        path = Path(db_path)
        if not path.is_file():
            # try artifacts/memory.sqlite
            alt = Path("artifacts") / path.name
            if alt.is_file():
                path = alt
            else:
                return

        try:
            conn = sqlite3.connect(str(path))
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, content, timestamp, context, embedding, learning_score
                FROM ltm_memory
                WHERE learning_score > 0.5
                ORDER BY timestamp DESC
                LIMIT 1000
                """
            )
        except Exception:
            return

        try:
            for row in cursor.fetchall():
                exp = {
                    "id": f"ltm_{row[0]}",
                    "type": "long_term_memory",
                    "content": row[1],
                    "timestamp": row[2],
                    "context": row[3],
                    "embedding": row[4] if len(row) > 4 else None,
                    "source": "sqlite_ltm",
                }
                self.experiences.append(exp)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def export_from_events(self, events_path: str = None) -> None:
        """Export learning events from a JSONL log file.

        Default path is taken from `AGL_SELF_LEARNING_LOGDIR/events.jsonl` or
        `learning_logs/events.jsonl`.
        """
        if events_path is None:
            base = os.getenv("AGL_SELF_LEARNING_LOGDIR", "") or "learning_logs"
            events_path = str(Path(base) / "events.jsonl")

        p = Path(events_path)
        if not p.is_file():
            return

        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except Exception:
                    continue
                exp = {
                    "id": f"event_{event.get('id', abs(hash(line)))}",
                    "type": "learning_event",
                    "task_type": event.get("payload", {}).get("task_type") or event.get("event"),
                    "input": event.get("payload", {}).get("input") or event.get("input"),
                    "output": event.get("payload", {}).get("output") or event.get("output"),
                    "feedback": event.get("payload", {}).get("feedback") or event.get("payload", {}).get("reward"),
                    "timestamp": event.get("ts") or event.get("timestamp") or datetime.now().isoformat(),
                    "source": "events_jsonl",
                }
                self.experiences.append(exp)

    def export_from_stm(self) -> None:
        """Attempt to read recent STM/LTM events.

        Strategy (best-effort, non-destructive):
        1. Try to read from `Core_Memory` singleton bridge (`get_bridge()`) and
           iterate `stm` and `ltm` structures if present.
        2. Fallback: instantiate `UnifiedAGISystem` and use its `memory` to
           collect recent episodic/working memories.
        3. If neither is available, silently return.
        """
        # 1) Try bridge singleton (preferred)
        try:
            try:
                from Core_Memory.bridge_singleton import get_bridge
                cb = get_bridge()
            except Exception:
                cb = None

            if cb is not None:
                # STM (recent, in-memory)
                stm_items = list(getattr(cb, 'stm', []) or [])
                for i, ev in enumerate(stm_items[-100:]):
                    # events may be dict-like with payload/ts
                    try:
                        payload = ev.get('payload') if isinstance(ev, dict) else (ev.payload if hasattr(ev, 'payload') else ev)
                    except Exception:
                        payload = ev
                    content = None
                    if isinstance(payload, dict):
                        content = payload.get('output') or payload.get('input') or payload.get('text') or str(payload)
                    else:
                        content = str(payload)

                    timestamp = ev.get('ts') if isinstance(ev, dict) else (getattr(ev, 'ts', None) or datetime.now().isoformat())

                    exp = {
                        'id': f'conscious_stm_{i}',
                        'type': 'short_term_memory',
                        'content': content,
                        'timestamp': timestamp,
                        'source': 'conscious_bridge_stm'
                    }
                    self.experiences.append(exp)

                # LTM (persistent)
                ltm_items = list(getattr(cb, 'ltm', []) or [])
                for i, ev in enumerate(ltm_items[-100:]):
                    try:
                        payload = ev.get('payload') if isinstance(ev, dict) else (ev.payload if hasattr(ev, 'payload') else ev)
                    except Exception:
                        payload = ev
                    content = payload.get('output') if isinstance(payload, dict) else str(payload)
                    timestamp = ev.get('ts') if isinstance(ev, dict) else (getattr(ev, 'ts', None) or datetime.now().isoformat())
                    exp = {
                        'id': f'conscious_ltm_{i}',
                        'type': 'long_term_memory',
                        'content': content,
                        'timestamp': timestamp,
                        'source': 'conscious_bridge_ltm'
                    }
                    self.experiences.append(exp)

                # done
                return
        except Exception:
            # swallow and continue to fallback
            pass

        # 2) Fallback: use UnifiedAGISystem.memory.recall or its episodic list
        try:
            from dynamic_modules.unified_agi_system import UnifiedAGISystem

            agi = UnifiedAGISystem(engine_registry={})
            mem = getattr(agi, 'memory', None)
            if mem is not None:
                # episodic_memory entries
                items = getattr(mem, 'episodic_memory', []) or []
                for i, item in enumerate(items[-100:]):
                    try:
                        content = item.content if hasattr(item, 'content') else str(item)
                        timestamp = getattr(item, 'timestamp', datetime.now().isoformat())
                    except Exception:
                        content = str(item)
                        timestamp = datetime.now().isoformat()
                    exp = {
                        'id': f'episodic_{i}',
                        'type': 'short_term_memory',
                        'content': content,
                        'timestamp': timestamp,
                        'source': 'unified_memory_episodic'
                    }
                    self.experiences.append(exp)

                # working memory ids -> try to resolve
                try:
                    working = list(getattr(mem, 'working_memory', []))
                    for i, wid in enumerate(working[-50:]):
                        it = None
                        try:
                            it = mem._get_item_by_id(wid)
                        except Exception:
                            it = None
                        if it:
                            content = getattr(it, 'content', str(it))
                            timestamp = getattr(it, 'timestamp', datetime.now().isoformat())
                            exp = {
                                'id': f'working_{i}',
                                'type': 'short_term_memory',
                                'content': content,
                                'timestamp': timestamp,
                                'source': 'unified_memory_working'
                            }
                            self.experiences.append(exp)
                except Exception:
                    pass

                return
        except Exception:
            # final fallback: nothing else to do
            return

    def save_to_jsonl(self, output_path: str = "artifacts/experience.jsonl") -> None:
        outp = Path(output_path)
        outp.parent.mkdir(parents=True, exist_ok=True)
        with outp.open("w", encoding="utf-8") as f:
            for exp in self.experiences:
                f.write(json.dumps(exp, ensure_ascii=False) + "\n")
        print(f"✅ Exported {len(self.experiences)} experiences to {outp}")

    def convert_to_finetuning_dataset(self) -> Dict[str, Any]:
        dataset: Dict[str, Any] = {
            "version": "1.0",
            "experiences": [],
            "statistics": {"total": len(self.experiences), "by_type": {}, "by_source": {}},
        }

        # Also produce OpenAI-style JSONL file for fine-tuning if examples available
        finetune_jsonl_path = Path("artifacts/finetune_examples.jsonl")
        finetune_examples: List[Dict[str, str]] = []

        def _make_openai_pair(prompt: str, completion: str) -> Dict[str, str]:
            # ensure completion begins with a space (OpenAI fine-tune best-practice)
            comp = completion
            if not comp.startswith(" "):
                comp = " " + comp
            # ensure completion ends with newline
            if not comp.endswith("\n"):
                comp = comp + "\n"
            return {"prompt": prompt, "completion": comp}

        for exp in self.experiences:
            exp_type = exp.get("type", "unknown")
            exp_source = exp.get("source", "unknown")
            dataset["statistics"]["by_type"][exp_type] = dataset["statistics"]["by_type"].get(exp_type, 0) + 1
            dataset["statistics"]["by_source"][exp_source] = dataset["statistics"]["by_source"].get(exp_source, 0) + 1

            # Prefer exact input/output pairs
            inp = exp.get("input")
            out = exp.get("output")
            if inp is not None and out is not None:
                training_example = {
                    "instruction": exp.get("task_type") or "Answer the following",
                    "input": inp,
                    "response": out,
                    "context": exp.get("context", ""),
                    "metadata": {"source": exp.get("source"), "timestamp": exp.get("timestamp"), "feedback": exp.get("feedback", 1.0)},
                }
                dataset["experiences"].append(training_example)

                # create OpenAI-style pair
                prompt = f"{training_example['instruction']}\n\nInput:\n{inp}\n\n###\n"
                finetune_examples.append(_make_openai_pair(prompt, str(out)))
                continue

            # If it's a memory entry (LTM) that contains Q/A style, try to extract
            content = exp.get("content") or ""
            if isinstance(content, str) and ("Q:" in content or "A:" in content or "Question:" in content):
                # crude split: take first Q/A found
                try:
                    # find 'Q:' and 'A:'
                    if 'Q:' in content and 'A:' in content:
                        q = content.split('Q:')[-1].split('A:')[0].strip()
                        a = content.split('A:')[-1].strip()
                    elif 'Question:' in content and 'Answer:' in content:
                        q = content.split('Question:')[-1].split('Answer:')[0].strip()
                        a = content.split('Answer:')[-1].strip()
                    else:
                        q = content[:200]
                        a = content[200:400]
                    training_example = {"instruction": "Answer the question:", "input": q, "response": a, "context": "memory_extract", "metadata": {"source": exp_source}}
                    dataset["experiences"].append(training_example)
                    prompt = f"Answer the question:\n\n{q}\n\n###\n"
                    finetune_examples.append(_make_openai_pair(prompt, a))
                    continue
                except Exception:
                    pass

            # For generic long-form memory content, create summarization example
            if content:
                summary = content.strip().replace('\n', ' ')[:250]
                instruction = "Summarize the following memory concisely for retrieval:"
                training_example = {"instruction": instruction, "input": content, "response": summary, "context": "memory_summarize", "metadata": {"source": exp_source}}
                dataset["experiences"].append(training_example)
                prompt = f"{instruction}\n\nContent:\n{content}\n\n###\n"
                finetune_examples.append(_make_openai_pair(prompt, summary))
                continue

            # If it's a learning_event without explicit input/output, synthesize a short description example
            if exp_type == 'learning_event':
                evt_type = exp.get('task_type') or exp.get('event') or 'learning_event'
                payload = exp.get('payload') or {}
                ts = exp.get('timestamp') or ''
                instr = f"Interpret this learning event and provide a short human-readable summary:"
                inp_text = f"Event: {evt_type}\nPayload: {json.dumps(payload, ensure_ascii=False)}\nTimestamp: {ts}"
                summary = f"Event {evt_type} recorded at {ts}" if not payload else f"{evt_type}: {', '.join([str(v) for v in (payload if isinstance(payload, (list, tuple)) else payload.values())])}"
                training_example = {"instruction": instr, "input": inp_text, "response": summary, "context": "event_summarize", "metadata": {"source": exp_source}}
                dataset["experiences"].append(training_example)
                prompt = f"{instr}\n\n{inp_text}\n\n###\n"
                finetune_examples.append(_make_openai_pair(prompt, summary))
                continue

        # write JSON dataset
        Path("artifacts").mkdir(parents=True, exist_ok=True)
        with open("artifacts/finetuning_dataset.json", "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        # write OpenAI JSONL if examples exist
        if finetune_examples:
            with finetune_jsonl_path.open("w", encoding="utf-8") as f:
                for ex in finetune_examples:
                    f.write(json.dumps(ex, ensure_ascii=False) + "\n")

        print(f"📊 Created finetuning dataset ({len(dataset['experiences'])} examples) and {len(finetune_examples)} openai-jsonl examples")
        # return dataset and path info
        return {"dataset": dataset, "jsonl_path": str(finetune_jsonl_path) if finetune_examples else None}


def main():
    print("🚀 Starting experience export...")
    exporter = ExperienceExporter()

    print("📂 Exporting from SQLite (ltm)...")
    exporter.export_from_sqlite(db_path=os.getenv('AGL_LTM_SQLITE', 'memory.sqlite'))

    print("📝 Exporting from events log...")
    exporter.export_from_events()

    print("🧠 Exporting from STM (best-effort)...")
    exporter.export_from_stm()

    print("💾 Saving experiences...")
    exporter.save_to_jsonl()

    print("🔁 Converting to finetuning dataset...")
    dataset_result = exporter.convert_to_finetuning_dataset()

    # normalize returned structure (backwards-compatible)
    if isinstance(dataset_result, dict) and 'dataset' in dataset_result:
        dataset = dataset_result['dataset']
        jsonl_path = dataset_result.get('jsonl_path')
    else:
        dataset = dataset_result
        jsonl_path = None

    report = {
        "export_timestamp": datetime.now().isoformat(),
        "total_experiences": len(exporter.experiences),
        "dataset_ready": len(dataset.get('experiences', [])) > 0,
        "statistics": dataset.get('statistics', {}),
        "finetune_jsonl": jsonl_path
    }
    Path("artifacts").mkdir(exist_ok=True)
    with open("artifacts/export_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("🎉 Export complete")
    return exporter.experiences


if __name__ == '__main__':
    main()
