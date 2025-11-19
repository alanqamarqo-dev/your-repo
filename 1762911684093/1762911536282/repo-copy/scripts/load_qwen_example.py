"""
Minimal example to load a model/tokenizer with `transformers` and run a short generation.
Save as `scripts/load_qwen_example.py` and run with `py -3 scripts\load_qwen_example.py` after installing dependencies.
Note: Adjust `model_id` and installation (torch wheels, bitsandbytes, GPTQ loaders) for your system/GPU.
"""
"""Example runner that attempts to load a model from Hugging Face.

This script accepts --model and --token so you can pass a gated HF token on the CLI
without exporting environment variables.

Usage:
  py -3 scripts\load_qwen_example.py --model Qwen2.5-Omni-3B-GPTQ --token <HF_TOKEN>
"""
import argparse
import os
import traceback
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', default='Qwen2.5-Omni-3B-GPTQ')
    p.add_argument('--token', default=None, help='Hugging Face token (optional)')
    args = p.parse_args()

    model_id = args.model
    token = args.token or os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_HUB_TOKEN')

    print(f"Model id: {model_id}")
    if token:
        print("Using HF token from --token or HF_TOKEN env var (not shown)")

    try:
        print('Loading tokenizer...')
        tok = AutoTokenizer.from_pretrained(model_id, use_fast=True, use_auth_token=token)
        print('Tokenizer loaded.')

        print('Loading model (this may download files and require HF access)...')
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map='auto',
            torch_dtype=torch.float16,
            load_in_4bit=True,
            llm_int8_enable_fp32_cpu_offload=True,
            max_memory={"cuda:0": "3.7GiB", "cpu": "12GiB"},
            trust_remote_code=True,
            use_auth_token=token,
        )
        print('Model loaded.')

        prompt = "فسّر قانون بقاء الطاقة باختصار."
        inputs = tok(prompt, return_tensors='pt').to(model.device)
        out = model.generate(**inputs, max_new_tokens=200)
        print('\n=== Generated ===\n')
        print(tok.decode(out[0], skip_special_tokens=True))
    except Exception as e:
        print('ERROR: failed to load/run model:')
        traceback.print_exc()
        print('\nHints:')
        print(' - If the repo is gated/private you need a valid HF token (use --token or set HF_TOKEN).')
        print(' - Ensure you have enough disk space and a compatible transformers/auto-gptq/bitsandbytes setup.')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
