"""Ensure specified Ollama models are available locally.

Usage:
  python scripts/ensure_ollama_models.py         # uses defaults
  python scripts/ensure_ollama_models.py qwen2.5:7b-instruct qwen2.5:3b-instruct

This script:
 - calls `ollama list` to detect installed models
 - for each requested model, if missing, runs `ollama pull <model>`
 - prints simple progress and returns non-zero on errors

It respects the environment variable `AGL_AUTO_PULL_OLLAMA_MODELS=0` to skip pulling.
"""
from __future__ import annotations

import os
import subprocess
import sys
from typing import List

DEFAULT_MODELS = [
    "qwen2.5:7b-instruct",
    "qwen2.5:3b-instruct",
]


def list_local_models() -> List[str]:
    """Return a list of model tags reported by `ollama list` (best-effort parsing)."""
    try:
        proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print("ollama CLI not found in PATH. Install ollama or ensure it's on PATH.")
        return []

    out = proc.stdout or ""
    models = []
    for line in out.splitlines():
        # Skip empty/header lines. Lines that start with a model tag typically look like:
        # qwen2.5:7b-instruct    845dbda0ea48    4.7 GB    18 hours ago
        parts = line.strip().split()
        if not parts:
            continue
        # model tags contain ':' (owner:model) — use that to detect
        tag = parts[0]
        if ":" in tag:
            models.append(tag)
    return models


def pull_model(model: str) -> bool:
    """Run `ollama pull <model>` and stream output to stdout. Return True on success."""
    print(f"Pulling model: {model} ...")
    try:
        # run without check=True so we can stream output progressively
        proc = subprocess.Popen(["ollama", "pull", model], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError:
        print("ollama CLI not found in PATH. Cannot pull models.")
        return False

    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            # forward output
            sys.stdout.write(line)
            sys.stdout.flush()
        rc = proc.wait()
        if rc == 0:
            print(f"Successfully pulled {model}")
            return True
        else:
            print(f"ollama pull exited with code {rc} for model {model}")
            return False
    except Exception as ex:
        try:
            proc.kill()
        except Exception:
            pass
        print(f"Exception while pulling {model}: {ex}")
        return False


def main(argv: List[str]) -> int:
    models = argv[1:] or DEFAULT_MODELS

    env_ok = os.getenv("AGL_AUTO_PULL_OLLAMA_MODELS", "1")
    allow_pull = env_ok not in ("0", "false", "False")

    local = list_local_models()
    print("Local ollama models:", local)

    missing = [m for m in models if m not in local]
    if not missing:
        print("All requested models are present locally.")
        return 0

    print("Missing models:", missing)
    if not allow_pull:
        print("Auto-pull disabled by AGL_AUTO_PULL_OLLAMA_MODELS. Exiting with non-zero status.")
        return 2

    # Pull each missing model in sequence
    all_ok = True
    for m in missing:
        ok = pull_model(m)
        if not ok:
            all_ok = False

    return 0 if all_ok else 3


if __name__ == "__main__":
    rc = main(sys.argv)
    sys.exit(rc)
