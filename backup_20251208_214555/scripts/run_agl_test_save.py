import sys, json, os
sys.path.insert(0, r'D:\AGL')
from Core_Engines.Ollama_KnowledgeEngine import OllamaKnowledgeEngine

input_path = r'reports/agl_test_input.txt'
output_path = r'reports/agl_response_local.json'
with open(input_path, 'r', encoding='utf-8') as f:
    prompt = f.read()

eng = OllamaKnowledgeEngine()
resp = eng.ask(prompt)
with open(output_path, 'w', encoding='utf-8') as fh:
    json.dump(resp, fh, ensure_ascii=False, indent=2)
print(f"Wrote response to {output_path}")
