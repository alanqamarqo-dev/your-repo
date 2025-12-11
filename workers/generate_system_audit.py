import glob
import json
import os
from datetime import datetime

# ==========================================
# ⚙️ Path configuration
# ==========================================
BASE_DIR = "D:\\AGL"
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
OUTPUT_FILE = os.path.join(ARTIFACTS_DIR, "system_audit.json")
NIGHT_CYCLES_DIR = os.path.join(ARTIFACTS_DIR, "night_cycles")
HIGHLIGHTS_COUNT = 3


def load_json_safe(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        print(f"⚠️ Error reading {path}: {exc}")
        return {}


def load_jsonl_entries(path):
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as fh:
        for idx, raw_line in enumerate(fh, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                entries.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                print(f"⚠️ Failed parsing line {idx} of {path}: {exc}")
    return entries


def get_latest_night_report():
    candidates = glob.glob(os.path.join(NIGHT_CYCLES_DIR, "night_report_*.json"))
    if not candidates:
        return {"status": "No night cycles recorded yet"}
    latest = max(candidates, key=os.path.getctime)
    return load_json_safe(latest)


def analyze_engine_performance():
    engine_log_path = os.path.join(ARTIFACTS_DIR, "engine_logs.json")
    data = load_json_safe(engine_log_path)
    entries = data.get("entries")
    if isinstance(entries, dict):
        entries = list(entries.values())
    elif entries is None and isinstance(data, list):
        entries = data
    entries = entries or []

    creative_sparks = 0
    engines_used = set()
    for entry in entries:
        engine_name = entry.get("engine") if isinstance(entry, dict) else None
        if engine_name:
            engines_used.add(engine_name)
        if engine_name == "Creative_Innovation":
            creative_sparks += 1

    return {
        "total_activations": len(entries),
        "engines_used": sorted(engines_used),
        "creative_sparks": creative_sparks,
    }


def get_safety_summary():
    safety_log_path = os.path.join(ARTIFACTS_DIR, "safety_log.json")
    logs = load_json_safe(safety_log_path)
    if isinstance(logs, list):
        incident_count = len(logs)
        last_incident = logs[-1] if logs else None
        rollback_events = 0
    elif isinstance(logs, dict):
        incident_count = len(logs.get("incidents", [])) if logs.get("incidents") else len(logs)
        last_incident = logs.get("incidents", [])[-1] if logs.get("incidents") else None
        rollback_events = logs.get("rollbacks", 0)
    else:
        incident_count = 0
        last_incident = None
        rollback_events = 0

    return {
        "incident_count": incident_count,
        "last_incident": last_incident,
        "rollback_events": rollback_events,
    }


def get_current_weights():
    return load_json_safe(os.path.join(CONFIGS_DIR, "fusion_weights.json"))


def get_harvest_summary():
    entries = load_jsonl_entries(os.path.join(ARTIFACTS_DIR, "harvested_facts.jsonl"))
    summary = {
        "fact_count": len(entries),
        "recent_facts": [],
    }
    for entry in entries[-HIGHLIGHTS_COUNT:]:
        if isinstance(entry, dict) and entry.get("summary"):
            summary_value = entry.get("summary")
        elif isinstance(entry, dict):
            summary_value = {k: entry[k] for k in ("id", "title") if k in entry}
        else:
            summary_value = entry
        summary["recent_facts"].append(summary_value)
    return summary


def ensure_output_path():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)


def generate_audit_report():
    print("-> [Audit] 🕵️ Starting System Audit & Consciousness Consolidation...")

    harvest_summary = get_harvest_summary()
    brain_state = get_current_weights()
    engine_stats = analyze_engine_performance()
    last_dream = get_latest_night_report()
    safety_status = get_safety_summary()

    audit_report = {
        "timestamp": datetime.now().isoformat(),
        "consciousness_level": last_dream.get("consciousness_level_end", 0.15),
        "manifesto": "System is evolving based on harvested knowledge and self-reflection.",
        "cognitive_state": {
            "current_iq_weights": brain_state,
            "evolution_stage": last_dream.get("cycle_id", "Genesis"),
        },
        "operational_metrics": {
            "engines_active": engine_stats,
            "safety_health": "Critical" if safety_status["incident_count"] > 10 else "Stable",
        },
        "memory_integration": {
            "harvest_overview": harvest_summary,
            "last_night_insight": last_dream.get("insights", []),
            "pending_improvements": last_dream.get("tasks", []),
        },
        "safety": safety_status,
    }

    ensure_output_path()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(audit_report, fh, indent=4, ensure_ascii=False)

    print(f"-> [Audit] ✅ System Audit Generated: {OUTPUT_FILE}")
    print("-> [Audit] 🧠 This file is now the 'Conscious State' for the next run.")


if __name__ == "__main__":
    generate_audit_report()
