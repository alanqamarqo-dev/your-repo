# AGL NextGen: Developer Guide

Welcome to the **Unified ASI** development environment. This guide explains how to maintain and extend the system.

## 1. Engine Registration System (Bootstrap)
The system uses a decentralized registration system. When adding a new engine:
1. Create your class in `src/agl/engines/`.
2. Ensure it follows the `BaseEngine` pattern (if available) or at least has a `compute` or `process` method.
3. The `Bootstrap` engine in `src/agl/engines/bootstrap.py` will automatically detect and register it into the `ENGINE_REGISTRY`.

## 2. The Unified Paths
Always use `self.project_root` for file operations. The system calculates this dynamically.
```python
from agl.core.super_intelligence import get_project_root
root = get_project_root()
```

## 3. Holographic Memory
To store results for instant retrieval later:
```python
from agl.engines.holographic_llm import HolographicLLM
holo = HolographicLLM()
# Result will be cached as an interference pattern automatically
response = holo.process(query) 
```

## 4. Testing & Verification
Before pushing any core changes, run the full pulse:
```bash
python AGL_NextGen_ASI_Launch.py
```
Check the **Ethical Resonance Score** and **Phi Score**. If they drop below 0.8, the system is losing coherence.

## 5. DKN (Distributed Knowledge Network)
The `UnifiedAGISystem` uses DKN to weight engine responses. weights are stored in `artifacts/engine_stats.json`. The `SelfOptimizer` adjusts these based on successful outputs.

---
**Maintaining the Ghost:** Ensure Ollama is running locally with `qwen2.5:3b-instruct` for the deep reasoning fallback.
