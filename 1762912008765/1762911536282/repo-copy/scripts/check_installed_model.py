"""Check whether a local HF/llama model is installed or registered for AGL.

Outputs a short JSON-like summary to stdout.
"""
import os
import json
from pathlib import Path

def exists_in_paths(paths):
    for p in paths:
        if Path(p).exists():
            return True, str(Path(p).resolve())
    return False, None

out = {}
out['env'] = {
    'TRANSFORMERS_MODEL': os.environ.get('TRANSFORMERS_MODEL'),
    'LLAMA_MODEL_PATH': os.environ.get('LLAMA_MODEL_PATH') or os.environ.get('LLAMA_MODEL'),
    'OPENAI_API_KEY': bool(os.environ.get('OPENAI_API_KEY')),
}

# common registration/config files
candidates = [
    'artifacts/models',
    'models',
    'config/agl_model.json',
    'artifacts/registered_model.json',
    'artifacts/agl_model_registration.json',
]
found = []
for c in candidates:
    p = Path(c)
    if p.exists():
        found.append(str(p.resolve()))

out['found_paths'] = found

# Try to inspect the adapter
try:
    from Core_Engines.LLM_OpenAI import LLMOpenAIEngine
    engine = LLMOpenAIEngine()
    out['engine'] = {
        'name': getattr(engine, 'name', None),
        'local_kind': getattr(engine, 'local_kind', None),
        'last_backend_used': getattr(engine, 'last_backend_used', None),
        'has_client': bool(getattr(engine, 'client', None)),
    }
except Exception as e:
    out['engine_error'] = repr(e)

# Check HF cache locations
home = Path.home()
hf_cache = [
    home / '.cache' / 'huggingface' / 'transformers',
    home / '.cache' / 'huggingface' / 'hub',
    Path(os.environ.get('HF_HOME','')) if os.environ.get('HF_HOME') else None,
]
hf_found = []
for p in hf_cache:
    if p and p.exists():
        hf_found.append(str(p))
out['hf_cache_paths'] = hf_found

print(json.dumps(out, ensure_ascii=False, indent=2))
