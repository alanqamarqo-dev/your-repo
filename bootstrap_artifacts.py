import os
import json
import time

# إعداد المسارات (يفترض التشغيل من D:\AGL)
BASE_DIR = os.getcwd()
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
NIGHT_CYCLES_DIR = os.path.join(ARTIFACTS_DIR, "night_cycles")
LOGS_DIR = os.path.join(BASE_DIR, "logs")


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"📁 Created directory: {path}")


def create_if_missing(filename, content, folder=ARTIFACTS_DIR):
    filepath = os.path.join(folder, filename)
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=4, ensure_ascii=False)
        print(f"✅ Created: {filename}")
    else:
        print(f"⏩ Exists: {filename}")


def main():
    print(f"🚀 Bootstrapping AGL Artifacts in: {BASE_DIR}")
    print("-" * 40)

    ensure_dir(ARTIFACTS_DIR)
    ensure_dir(NIGHT_CYCLES_DIR)
    ensure_dir(LOGS_DIR)

    create_if_missing("engine_logs.json", {
        "entries": [],
        "last_update": "Genesis"
    })

    create_if_missing("safety_log.json", {
        "incidents": [],
        "rollbacks": 0
    })

    create_if_missing("harvest_stats.json", {
        "total_facts": 0,
        "last_run": None
    })

    facts_path = os.path.join(ARTIFACTS_DIR, "harvested_facts.jsonl")
    if not os.path.exists(facts_path):
        with open(facts_path, 'w', encoding='utf-8') as f:
            f.write("")
        print("✅ Created: harvested_facts.jsonl")
    else:
        print("⏩ Exists: harvested_facts.jsonl")

    create_if_missing("evolution_plan.json", {
        "cycle_id": "Genesis_Bootstrap_v1",
        "intent": "Initial System Boot",
        "tasks": []
    })

    dummy_report_name = "night_report_genesis.json"
    dummy_report_path = os.path.join(NIGHT_CYCLES_DIR, dummy_report_name)
    if not os.path.exists(dummy_report_path):
        with open(dummy_report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "cycle_id": "Genesis_Alpha",
                "insights": ["System initialized successfully"],
                "tasks": []
            }, f, indent=4, ensure_ascii=False)
        print(f"✅ Created: {dummy_report_name}")
    else:
        print(f"⏩ Exists: {dummy_report_name}")

    print("-" * 40)
    print("🎉 Bootstrap Complete. You are ready to launch Consciousness.")


if __name__ == "__main__":
    main()
