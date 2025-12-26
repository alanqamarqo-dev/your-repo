import importlib.util
import json
import os
import time
import sys

MODULE_PATH = os.path.join(os.getcwd(), "repo-copy", "dynamic_modules", "mission_control_enhanced.py")

mission_text = """
نفّذ هذا الاختبار:

(نفس نص الاختبار كما في الملف الأصلي — يتم توجيهه كسؤال علمي/بحثي متكامل)
"""


def load_module(path):
    # Ensure `repo-copy` is on sys.path so imports like Core_Engines work
    repo_copy = os.path.join(os.getcwd(), "repo-copy")
    if repo_copy not in sys.path:
        sys.path.insert(0, repo_copy)
    spec = importlib.util.spec_from_file_location("mission_control_enhanced", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    start = time.time()
    mod = load_module(MODULE_PATH)
    # Call execute_mission with explicit mission_type to avoid incorrect math routing
    try:
        result = mod.execute_mission(mission_text, mission_type='science')
    except Exception as e:
        result = {"error": str(e)}
    elapsed = time.time() - start

    out = {
        "mission": "ai_theoretical_challenge",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": elapsed,
        "invocation": "execute_mission(..., mission_type='science')",
        "result": result
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))

    try:
        os.makedirs("artifacts", exist_ok=True)
        with open(os.path.join("artifacts", "ai_theoretical_challenge_result_correct.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to write artifacts file:", e)


if __name__ == '__main__':
    main()
