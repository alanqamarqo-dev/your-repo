"""Download and register a local HF text-generation model for AGL.

Usage:
  .\.venv\Scripts\python.exe scripts/install_register_model.py --model distilgpt2

What it does:
  - Installs (downloads) the model weights via `transformers.pipeline('text-generation', model=...)`
  - Writes `artifacts/agl_model_config.json` containing the chosen model name so
    the project's LLM adapter will prefer the registered model when env vars
    are not set.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path


def main(model_name: str):
    try:
        from transformers import pipeline
    except Exception as e:
        print('transformers not installed or import failed:', e)
        print('Please install with: pip install transformers[sentencepiece]')
        return

    print('Attempting to instantiate model pipeline for', model_name)
    try:
        pipe = pipeline('text-generation', model=model_name)
        # run a tiny generation to ensure files are downloaded
        out = pipe('Test', max_new_tokens=5, do_sample=False)
        print('Model pipeline created, sample output:', out)
    except Exception as e:
        print('Failed to create pipeline:', e)
        return

    cfg = {'TRANSFORMERS_MODEL': model_name, 'model': model_name}
    out_path = Path('artifacts') / 'agl_model_config.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print('Wrote registration to', out_path)
    print('You can now run runners without setting TRANSFORMERS_MODEL; the adapter will prefer the registered model.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--model', '-m', required=True, help='HF model name (e.g. distilgpt2, gpt2)')
    args = p.parse_args()
    main(args.model)
