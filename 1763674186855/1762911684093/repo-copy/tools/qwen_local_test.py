prompt = "اشرح باختصار ما هو الذكاء الاصطناعي العام."
"""Small local test to load and run a HF model.

This file used to perform heavy imports at module-import time which causes
pytest collection to fail when transformers/torch aren't installed. To make
the repository testable without heavyweight ML packages, we avoid importing
transformers/torch at import time. The heavyweight work is wrapped in
``main()`` and only executed when run as a script.

Usage: .\\.venv\\Scripts\\python.exe tools\\qwen_local_test.py
"""

import traceback
import sys
import os


def _prevent_repo_shadowing():
    """Guard against repo-local modules shadowing installed packages.

    Keeps sys.path clean so that a local file named `torch.py` or similar
    does not accidentally shadow the real package.
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if sys.path and sys.path[0] and os.path.abspath(sys.path[0]) == script_dir:
            sys.path.pop(0)
    except Exception:
        pass


def _try_load_venv_torch():
    """Attempt to load a torch package directly from the venv site-packages if present.

    This is best-effort; failures are ignored and normal import resolution
    will be used instead.
    """
    try:
        venv_torch_init = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.venv', 'Lib', 'site-packages', 'torch', '__init__.py'))
        if os.path.exists(venv_torch_init):
            import importlib.util
            spec = importlib.util.spec_from_file_location('torch', venv_torch_init)
            torch = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(torch)
            sys.modules['torch'] = torch
    except Exception:
        pass


def main():
    _prevent_repo_shadowing()
    _try_load_venv_torch()

    try:
        # Heavy imports are done here (inside main), not at module import time.
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
    except Exception as e:
        print('Import error:', e)
        print('Make sure you ran: .\\.venv\\Scripts\\python.exe -m pip install transformers accelerate torch sentencepiece protobuf')
        return 1

    model_name = "Qwen/Qwen-7B-Chat"
    print('Model:', model_name)
    print('torch version:', getattr(sys.modules.get('torch'), '__version__', 'unknown'))
    try:
        print('CUDA available:', torch.cuda.is_available())
        print('CUDA device count:', torch.cuda.device_count() if torch.cuda.is_available() else 0)
    except Exception:
        print('CUDA information: unavailable')

    prompt = "اشرح باختصار ما هو الذكاء الاصطناعي العام."

    try:
        print('\nDownloading/Loading tokenizer... (this may take a while)')
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

        print('Loading model (device_map="auto")... this may use CPU or GPU depending on your system')
        model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", trust_remote_code=True)

        print('\nTokenizing prompt and generating...')
        inputs = tokenizer(prompt, return_tensors="pt")
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        outputs = model.generate(**inputs, max_new_tokens=150)
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

        print('\n=== MODEL OUTPUT ===')
        print(decoded)
        print('=== END OUTPUT ===')

    except Exception as e:
        print('\nError while loading or running the model:')
        traceback.print_exc()
        print('\nCommon causes: out-of-memory (no GPU and model too large), missing internet to download model, or incompatible PyTorch build.')
        print('If OOM, try a smaller model or ensure you have a GPU with enough RAM, or use device_map with offload_to_cpu/torch_dtype quantized weights.')
        return 2

    print('\nSuccess (if output printed above)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
