Engine response contract (local scaffold / CI)

Minimum required response shape for engines used in local tests and CI:

- A JSON object containing at least these top-level keys:
  - "ok": bool  # True when the engine produced a valid response, False on error
  - "engine": str  # short engine identifier
  - "text": str  # primary human-readable response body (may be short)
  - "reply_text": str  # mirror of text for reply-friendly clients

Optional:

- "error": str (present when ok is False)
- other engine-specific fields (sources, metrics, domain, map, etc.)

Tests and test helpers (e.g. `tests/helpers/engine_ask.py`) will normalize common variants
(`answer` → `text`, infer missing `ok`, etc.) but engines should strive to return the canonical
shape above for clarity and CI stability.
