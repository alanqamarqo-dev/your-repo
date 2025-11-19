"""Adapter that exposes a fetch_facts(question, hints=...) API backed by OllamaKnowledgeEngine.

Enable by setting environment variable:
  AGL_EXTERNAL_INFO_IMPL=ollama_engine

This adapter mirrors the OpenAIAdapter shape so it can be plugged into workers/harvester.
"""
import os
import json
from typing import List, Dict, Any, Optional, cast

from .Ollama_KnowledgeEngine import OllamaKnowledgeEngine


class OllamaAdapter:
    def __init__(self, model: Optional[str] = None, cache_dir: Optional[str] = None):
        self.model = model or os.getenv('AGL_EXTERNAL_INFO_MODEL')
        self.engine = OllamaKnowledgeEngine(model=self.model, cache_dir=cache_dir)

    def fetch_facts(self, question: str, hints: List[str] | None = None, system_prompt: Optional[str] = None, cache: bool = True) -> Dict[str, Any]:
        """Fetch facts from the Ollama engine.

        Parameters:
        - question: the user question
        - hints: optional context hints
        - system_prompt: optional system prompt to pass to the engine (overrides env)
        - cache: whether to allow engine-level caching for this call
        """
        ctx = hints or []
        try:
            # If caller didn't provide a system_prompt, fall back to env var (legacy behavior)
            final_system_prompt = system_prompt if system_prompt is not None else os.getenv('AGL_EXTERNAL_SYSTEM_PROMPT')

            # call engine; allow disabling cache per-call
            resp = cast(Any, self.engine).ask(question, context=ctx, system_prompt=final_system_prompt, cache=cache)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        if not resp or not isinstance(resp, dict):
            return {"ok": False, "error": "invalid_engine_response"}

        ok = bool(resp.get('ok', True))
        answer = resp.get('text') or resp.get('answer') or ''
        sources = resp.get('sources') or []

        facts = []
        if answer:
            facts.append({
                'text': answer,
                'source': ','.join(sources) if isinstance(sources, list) else (sources or ''),
                'confidence': 0.8
            })

        # try to compute a short prompt hash for traceability
        try:
            import hashlib
            ph = (final_system_prompt or '') + '\n' + question
            prompt_hash = hashlib.sha256(ph.encode('utf-8')).hexdigest()[:12]
        except Exception:
            prompt_hash = None

        return {"ok": ok, "answer": answer, "facts": facts, "used_system_prompt": bool(final_system_prompt), "prompt_hash": prompt_hash}
