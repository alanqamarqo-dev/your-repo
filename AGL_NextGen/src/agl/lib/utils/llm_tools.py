import os
from typing import Optional


def build_llm_url(endpoint_type: str = "chat", base: Optional[str] = None) -> str:
    """
    Build a canonical LLM URL.

    - endpoint_type: "chat", "generate", "completions" or a raw path like "/api/generate".
    - base: optional base url override; if omitted uses `AGL_LLM_BASEURL` or `OLLAMA_API_URL`.

    This helper ensures we don't end up with duplicated '/v1/v1' segments and
    normalizes common Ollama/OpenAI endpoint shapes.
    """
    base = (base or os.getenv("AGL_LLM_BASEURL") or os.getenv("OLLAMA_API_URL") or "http://localhost:11434").rstrip('/')

    # Remove a trailing '/v1' to avoid accidental duplication later
    if base.endswith('/v1'):
        base = base[:-3]

    # Normalize common endpoint types
    et = (endpoint_type or "").lower()
    if et == "chat":
        path = "/v1/chat/completions"
    elif et == "generate":
        # Ollama historically exposes /api/generate; keep that as default for generate
        path = "/api/generate"
    elif et == "completions":
        path = "/v1/completions"
    else:
        # If caller provided an explicit path, accept it (ensure leading slash)
        path = endpoint_type if endpoint_type.startswith('/') else f"/{endpoint_type}"

    return f"{base}{path}"
