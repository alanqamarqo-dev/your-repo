import sys
from pathlib import Path
# ensure repo root is on sys.path so top-level modules (AGL_Omega) import correctly
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from AGL_Omega import MetaReasoner
import json

def main():
    meta = MetaReasoner(memory_path='artifacts/memory/long_term.jsonl')
    thinking_patterns = meta.analyze_reasoning_patterns()
    plan = meta.generate_self_improvement_plan()
    print('THINKING PATTERNS:')
    print(json.dumps(thinking_patterns, ensure_ascii=False, indent=2))
    print('\nIMPROVEMENT PLAN:')
    print(json.dumps(plan, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
