import json, os

FACTS_FILE = os.path.join(os.path.dirname(__file__), "law_facts.json")

def save_law_fact(key: str, payload: dict):
    os.makedirs(os.path.dirname(FACTS_FILE), exist_ok=True)
    data = {}
    if os.path.exists(FACTS_FILE):
        try:
            with open(FACTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[key] = payload
    with open(FACTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
