import sys, json, os
sys.path.insert(0, r'D:\AGL')
# Disable any ollama kb cache if the engine respects this env
os.environ['AGL_OLLAMA_KB_CACHE_ENABLE'] = '0'
from Core_Engines.Ollama_KnowledgeEngine import OllamaKnowledgeEngine

input_path = r'reports/agl_test_input.txt'
with open(input_path, 'r', encoding='utf-8') as f:
    prompt = f.read()

eng = OllamaKnowledgeEngine()
resp = eng.ask(prompt)
# Try to pretty-print JSON-like responses, else print raw
try:
    print(json.dumps(resp, ensure_ascii=False, indent=2))
except Exception:
    print(resp)
