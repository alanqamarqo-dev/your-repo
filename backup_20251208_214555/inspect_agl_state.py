import json
from pathlib import Path

ARTIFACTS_DIR = Path("artifacts")
LONG_TERM_PATH = ARTIFACTS_DIR / "long_term_projects.jsonl"
LEARNED_FACTS_PATH = ARTIFACTS_DIR / "learned_facts.jsonl"


def read_jsonl(path: Path, max_lines=None):
    items = []
    if not path.exists():
        return items
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if max_lines is not None and i + 1 >= max_lines:
                break
    return items


def show_projects():
    print("=== Long-Term Projects ===")
    projects = read_jsonl(LONG_TERM_PATH)
    if not projects:
        print("(no long-term projects found)")
        return
    for p in projects:
        pid = p.get("project_id")
        goal = p.get("goal")
        ticks = p.get("total_ticks", 0)
        last_ts = p.get("last_tick_ts")
        print(f"- id: {pid}")
        print(f"  goal: {goal}")
        print(f"  total_ticks: {ticks}")
        print(f"  last_tick_ts: {last_ts}")
        print()


def show_learned_facts(max_items=10):
    print("=== Learned Facts (last up to", max_items, ") ===")
    facts = read_jsonl(LEARNED_FACTS_PATH, max_lines=None)
    if not facts:
        print("(no learned facts yet)")
        return
    # show last items
    facts = facts[-max_items:]
    for i, fct in enumerate(facts, 1):
        q = fct.get("question") or fct.get("problem") or ""
        ans = fct.get("answer", "")
        score = fct.get("score", None)
        src = fct.get("source", "")
        print(f"{i}. source={src}, score={score}")
        print(f"   Q: {q}")
        print(f"   A: {ans[:120]}{'...' if len(ans) > 120 else ''}")
        print()


def main():
    show_projects()
    print()
    show_learned_facts(max_items=10)


if __name__ == "__main__":
    main()
