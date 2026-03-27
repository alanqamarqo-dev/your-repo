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

    def retrieve_gravitational(self, top_k=5):
        """
        Retrieves memories using Heikal's Gravitational Memory Theory.
        
        Theory: Memories are massive objects in the cognitive spacetime.
        - Mass (M): Importance * Emotional Intensity
        - Distance (r): Time decay (t_now - t_memory)
        - Gravity (g): G * M / r^2
        
        This allows important memories to remain 'heavy' and accessible even if old,
        while trivial recent memories fade.
        """
        import time
        current_time = time.time()
        G = 100000.0 # Gravitational constant of the mind (scaled for time in seconds)
        
        scored_memories = []
        
        for mem in self.buffer:
            # 1. Calculate Mass (M)
            # Default to 1.0 if not specified
            importance = float(mem.get('importance', 1.0))
            intensity = float(mem.get('intensity', 1.0))
            
            # If 'score' exists (0-100), use it as a proxy for importance
            if 'score' in mem:
                try:
                    score_val = float(mem['score'])
                    importance = max(importance, score_val / 10.0)
                except:
                    pass
                
            mass = importance * intensity
            
            # 2. Calculate Distance (r)
            # Use timestamp if available, else assume it's old (large distance)
            timestamp = float(mem.get('timestamp', current_time - 100000))
            time_diff = max(1.0, current_time - timestamp)
            
            # Heikal Metric: Spacetime interval
            # We treat time as the primary distance dimension in memory
            # UPDATE: Using Logarithmic Time Decay (Cognitive Distance)
            # This reflects that subjective time passes slower for recent events and faster for old ones.
            # r_effective = log(time_diff)
            import math
            r_effective = math.log(time_diff + math.e) # +e to ensure log >= 1
            
            # 3. Calculate Gravitational Pull
            # F = G * M / r_effective^2
            gravity = (G * mass) / (r_effective**2)
            
            scored_memories.append((gravity, mem))
            
        # Sort by gravity (descending)
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        return [m[1] for m in scored_memories[:top_k]]

    def clear(self):
        self.buffer = []
        try:
            os.remove(self.storage_path)
        except Exception:
            pass
