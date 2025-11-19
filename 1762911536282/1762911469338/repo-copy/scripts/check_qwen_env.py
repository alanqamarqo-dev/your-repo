import os
import json
from pathlib import Path
import importlib.util

out = {}

# envs
out['TRANSFORMERS_MODEL'] = os.environ.get('TRANSFORMERS_MODEL')
out['LLAMA_MODEL_PATH'] = os.environ.get('LLAMA_MODEL_PATH')

# check transformers/torch presence
out['transformers_installed'] = importlib.util.find_spec('transformers') is not None
out['torch_installed'] = importlib.util.find_spec('torch') is not None

# HF cache
hf = Path.home() / '.cache' / 'huggingface' / 'hub'
if not hf.exists():
    out['hf_cache'] = str(hf)
    out['hf_cache_exists'] = False
    out['qwen_models'] = []
else:
    out['hf_cache'] = str(hf)
    out['hf_cache_exists'] = True
    qwen_dirs = []
    for p in hf.iterdir():
        if p.is_dir() and p.name.startswith('models--Qwen'):
            # compute size
            size = 0
            for root, dirs, files in os.walk(p):
                for f in files:
                    try:
                        size += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
            qwen_dirs.append({'name': p.name, 'path': str(p), 'size_bytes': size})
    out['qwen_models'] = qwen_dirs

print(json.dumps(out, ensure_ascii=False, indent=2))
