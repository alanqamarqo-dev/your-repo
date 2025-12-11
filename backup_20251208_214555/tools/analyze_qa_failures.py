import json
import os
import time
from collections import Counter
from typing import Dict, Any


HERE = os.path.dirname(__file__)
ARTIFACTS_DIR = os.path.join(os.path.dirname(HERE), "artifacts")

DEFAULT_MEMORY_PATH = os.path.join(ARTIFACTS_DIR, "collective_memory.jsonl")
DEFAULT_PATCHES_PATH = os.path.join(
    os.path.dirname(HERE), "Self_Improvement", "prompt_patches.json"
)

# Note: resolve paths at runtime (so tests can monkeypatch env vars)
MEMORY_PATH = None
PATCHES_PATH = None


def load_memory(path: str) -> list:
    rows = []
    if not os.path.exists(path):
        print(f"[WARN] collective_memory not found at {path}")
        return rows

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def build_prompt_patches(rows: list, score_threshold: float = 0.8, top_n: int = 8) -> Dict[str, Any]:
    """
    نركّز على الأسئلة التي سكورها أقل من العتبة، ونجمع الكلمات المفقودة الأكثر تكرارًا.
    """
    missing_counter = Counter()

    for row in rows:
        score = float(row.get("score", 0.0))
        if score >= score_threshold:
            continue
        for kw in row.get("missing", []):
            if isinstance(kw, str) and kw.strip():
                missing_counter[kw.strip()] += 1

    if not missing_counter:
        print("[INFO] no significant missing keywords; nothing to patch.")
        return {}

    top_missing = [kw for kw, _ in missing_counter.most_common(top_n)]

    extra_instruction = (
        "عند الإجابة عن الأسئلة الطبية أو الصحية، حاول أن تذكر — إذا كان ذلك مناسبًا للسؤال — "
        "العناصر أو الجوانب التالية متى انطبقت: "
        + "، ".join(top_missing)
        + "."
    )

    patches = {
        "medical_qa_v1": {
            "extra_instruction": extra_instruction,
            "generated_at": time.time(),
            "top_missing": top_missing,
        }
    }
    return patches


def save_patches(patches: Dict[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(patches, f, ensure_ascii=False, indent=2)
    print(f"[INFO] saved prompt patches to {path}")


def main() -> Dict[str, Any]:
    memory_path = os.getenv("AGL_COLLECTIVE_MEMORY_PATH", DEFAULT_MEMORY_PATH)
    patches_path = os.getenv("AGL_PROMPT_PATCHES_PATH", DEFAULT_PATCHES_PATH)

    print(f"[INFO] loading memory from {memory_path}")
    rows = load_memory(memory_path)

    print(f"[INFO] loaded {len(rows)} rows from collective memory.")
    patches = build_prompt_patches(rows)

    if not patches:
        print("[INFO] no patches generated.")
        return {}

    save_patches(patches, patches_path)
    return patches


if __name__ == "__main__":
    main()
