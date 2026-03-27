from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


_HOLO_SINGLETON = None


def _truthy_env(name: str, default: str = "1") -> bool:
    return os.getenv(name, default) in ("1", "true", "True", "yes", "YES")


def get_holographic_llm():
    """Best-effort singleton for HolographicLLM.

    This keeps all LLM calls routing through one cache on disk (when enabled),
    while still allowing the system to run in offline/CI environments.
    """
    global _HOLO_SINGLETON

    if _HOLO_SINGLETON is not None:
        return _HOLO_SINGLETON

    if not _truthy_env("AGL_HOLO_ENABLE", "1"):
        return None

    try:
        from agl.engines.holographic_llm import HolographicLLM
    except Exception:
        return None

    try:
        key_seed = int(os.getenv("AGL_HOLO_KEY", "42"))
    except Exception:
        key_seed = 42

    cache_dir = os.getenv("AGL_HOLO_CACHE", "artifacts/holographic_llm")

    try:
        _HOLO_SINGLETON = HolographicLLM(key_seed=key_seed, cache_dir=cache_dir)
        return _HOLO_SINGLETON
    except Exception:
        _HOLO_SINGLETON = None
        return None


def chat_llm(
    messages: List[Dict[str, str]],
    max_new_tokens: int | None = None,
    temperature: float = 0.2,
    top_p: float = 0.9,
) -> Dict[str, Any]:
    """Unified LLM entrypoint for NextGen.

    Returns a dict with at least: ok, text.
    Prefers holographic cache when available, otherwise falls back to hosted_llm.
    """
    if not messages:
        return {"ok": False, "error": "no_messages"}

    holo = get_holographic_llm()
    if holo is not None:
        try:
            text = holo.chat_llm(
                messages,
                max_new_tokens=max_new_tokens or 500,
                temperature=float(temperature),
                use_holographic=True,
            )
            return {
                "ok": bool(str(text).strip()),
                "engine": "holographic_llm:gateway",
                "text": str(text),
            }
        except Exception:
            # Fall back to hosted shim below.
            pass

    try:
        from agl.lib.llm import hosted_llm

        return hosted_llm.chat_llm(
            messages,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )
    except Exception:
        return {"ok": False, "error": "no_llm_backend"}
