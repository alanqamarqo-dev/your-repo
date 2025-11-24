"""Adapter that exposes a fetch_facts(question, hints=...) API backed by OpenAIKnowledgeEngine.

This adapter is intentionally small and best-effort: it calls the OpenAIKnowledgeEngine.ask()
and transforms the returned text into a 'facts' list with simple metadata so it matches the
ExternalInfoProvider shape expected by callers.

Enable by setting environment variable:
  AGL_EXTERNAL_INFO_IMPL=openai_engine

"""
import os
import json
from typing import List, Dict, Any, Optional, cast

from .OpenAI_KnowledgeEngine import OpenAIKnowledgeEngine


class OpenAIAdapter:
    def __init__(self, model: Optional[str] = None, cache_dir: Optional[str] = None):
        # Respect model env override or passed model
        self.model = model or os.getenv('AGL_EXTERNAL_INFO_MODEL')
        # Create the engine; let it raise if OPENAI_API_KEY missing
        self.engine = OpenAIKnowledgeEngine(model=self.model, cache_dir=cache_dir)

    def fetch_facts(self, question: str, hints: List[str] | None = None) -> Dict[str, Any]:
        # Build a light context from hints
        ctx = hints or []
        try:
            resp = cast(Any, self.engine).ask(question, context=ctx)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        # resp expected shape: {ok: bool, text: str, sources: []}
        if not resp or not isinstance(resp, dict):
            return {"ok": False, "error": "invalid_engine_response"}

        ok = bool(resp.get('ok', True))
        answer = resp.get('text') or resp.get('answer') or ''
        sources = resp.get('sources') or []

        # Create one fact entry with the answer and sources if present
        facts = []
        if answer:
            facts.append({
                'text': answer,
                'source': ','.join(sources) if isinstance(sources, list) else (sources or ''),
                'confidence': 0.8
            })

        return {"ok": ok, "answer": answer, "facts": facts}
