"""Download a Qwen model from Hugging Face into the local HF cache.

Usage (PowerShell):

# set project env and run (this will download tens/hundreds of MBs+)
$env:PYTHONPATH='D:\AGL'
$env:TRANSFORMERS_MODEL='Qwen/Qwen1.5-1.8B-Chat'
.\.venv\Scripts\python.exe scripts/download_qwen.py --model Qwen/Qwen1.5-1.8B-Chat

Note: This script will download the model to your Hugging Face cache
(e.g. C:\Users\<you>\.cache\huggingface\hub). Only run if you have
sufficient disk space and bandwidth.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception as e:
    print('Could not import transformers:', e)
    print('Please install required packages: pip install transformers torch safetensors')
    raise


def download_model(model_name: str, trust_remote_code: bool = True, device_map: str | dict | None = 'auto'):
    print(f"🔽 Starting download for model: {model_name}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=trust_remote_code)
        print('Tokenizer loaded OK')
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map=device_map,
            trust_remote_code=trust_remote_code,
            low_cpu_mem_usage=True,
        )
        print('Model downloaded/loaded into device_map=', device_map)
    except Exception as e:
        print('Error while downloading/loading model:')
        traceback.print_exc()
        raise

    # quick test generation (small)
    try:
        prompt = 'اشرح لي مفهوم الذكاء الاصطناعي بلغة بسيطة.'
        inputs = tokenizer(prompt, return_tensors='pt')
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        outputs = model.generate(**inputs, max_new_tokens=80)
        text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print('\n=== Sample generation ===\n')
        print(text)
        print('\n=== End sample ===\n')
    except Exception as e:
        print('Model loaded but quick generation failed (this may be OK on CPU-only or due to memory):', e)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--model', '-m', default=os.environ.get('TRANSFORMERS_MODEL', 'Qwen/Qwen1.5-1.8B-Chat'), help='Hugging Face model name')
    p.add_argument('--device-map', '-d', default=os.environ.get('HF_DEVICE_MAP', 'auto'), help='device_map passed to from_pretrained ("auto" or "cpu")')
    p.add_argument('--yes', action='store_true', help='Confirm download without prompting')
    args = p.parse_args()

    model_name = args.model
    device_map = args.device_map
    if device_map.lower() == 'cpu':
        device_map = {'': 'cpu'}

    print('Model to download:', model_name)
    print('Device map:', device_map)

    if not args.yes:
        resp = input('This will download model files from Hugging Face (may be large). Proceed? [y/N]: ').strip().lower()
        if resp not in ('y', 'yes'):
            print('Aborted by user.')
            sys.exit(1)

    download_model(model_name, trust_remote_code=True, device_map=device_map)
