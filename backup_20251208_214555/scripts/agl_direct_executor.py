#!/usr/bin/env python3
import sys, os, json
from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter

def run(question, timeout=120.0):
    adapter = HostedLLMAdapter()
    # allow overriding engine_hint via env var to avoid RAG short-circuit/context when needed
    engine_hint = os.environ.get('AGL_ENGINE_HINT', '').strip() or None
    task = {"question": question, "task_type": "qa_single"}
    if engine_hint:
        task['engine_hint'] = engine_hint
    out = adapter.process_task(task, timeout_s=float(timeout))
    # print full JSON
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: agl_direct_executor.py "<question>" [timeout_s]')
        sys.exit(1)
    q = sys.argv[1]
    t = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    run(q, t)
