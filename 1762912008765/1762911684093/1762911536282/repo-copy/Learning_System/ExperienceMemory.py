"""Learning_System/ExperienceMemory.py

Simple JSONL experience memory for storing run outputs.

API:
 - append_experience(path, obj): append a JSON line to the file (creates dirs)
 - read_experiences(path): generator of parsed JSON objects
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Generator


def _ensure_dir_for(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def append_experience(path: str, obj: Dict[str, Any]) -> None:
    _ensure_dir_for(path)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def read_experiences(path: str) -> Generator[Dict[str, Any], None, None]:
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


class ExperienceMemory:
    """Small class wrapper providing an easy-to-test interface around the
    append_experience/read_experiences helpers.
    """
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.buffer = []
        # load existing if present
        if os.path.exists(self.storage_path):
            self.load()

    def append(self, item: Dict[str, Any]):
        self.buffer.append(item)
        append_experience(self.storage_path, item)

    def load(self):
        self.buffer = list(read_experiences(self.storage_path))

    def clear(self):
        self.buffer = []
        try:
            os.remove(self.storage_path)
        except Exception:
            pass
