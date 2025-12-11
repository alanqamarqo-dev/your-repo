````instructions
Short, actionable guidance for AI coding assistants working in this repository.

**Purpose:** help AI coding agents be productive quickly: architecture, key files, run/test workflows, env vars, and code patterns unique to this repo.

**Big picture**: the project is an on-prem AGL orchestration stack (LLM-backed).
- `Core_Engines/` — LLM adapters and knowledge engines (example: `Core_Engines/Hosted_LLM.py`).
- `Integration_Layer/` — prompt composers and routing (example: `Integration_Layer/Hybrid_Composer.py`, `Action_Router.py`).
- `AGL_UI/`, `scripts/` — UI and helper scripts (example: `scripts/quick_llm_ping.py`).

**Key files to consult**
- `Core_Engines/Hosted_LLM.py`: central `chat_llm` entrypoint and provider selection.
- `Core_Engines/__init__.py`: `ENGINE_SPECS` and `bootstrap_register_all_engines` behavior.
- `Integration_Layer/Hybrid_Composer.py`: `build_prompt_context(story, questions)` — preferred prompt builder.
- `conftest.py` (tests): sets default RAG env vars and runs bootstrap before tests.
- `artifacts/bootstrap_report.json`: produced after engine bootstrap — useful for debugging registrations.

**Model selection & environment variables (exact names)**
- `AGL_LLM_PROVIDER`, `AGL_LLM_MODEL`, `AGL_LLM_BASEURL`, `OLLAMA_API_URL` — control provider, model and base HTTP URL.
- Mock and cache flags: `AGL_EXTERNAL_INFO_MOCK`, `AGL_OLLAMA_KB_MOCK`, `AGL_OPENAI_KB_MOCK`, `AGL_OLLAMA_KB_CACHE_ENABLE`.
- HTTP tuning: `AGL_HTTP_RETRIES`, `AGL_HTTP_BACKOFF`, `AGL_LLM_TIMEOUT`.

PowerShell snippet (clear mocks + point to local Ollama):
```powershell
Remove-Item env:AGL_EXTERNAL_INFO_MOCK -ErrorAction SilentlyContinue;
Remove-Item env:AGL_OLLAMA_KB_MOCK -ErrorAction SilentlyContinue;
$env:AGL_LLM_PROVIDER='ollama';
$env:AGL_LLM_MODEL='qwen2.5:7b-instruct';
$env:AGL_LLM_BASEURL='http://localhost:11434';
```

**Prompt & messaging conventions**
- Use `Integration_Layer.Hybrid_Composer.build_prompt_context(story, questions)` — it returns system/user lists.
- Note: `chat_llm` (Hosted_LLM) currently consumes only the *first* `system` and *first* `user` message. If you need multiple messages, merge them into the first user entry.

**Mock detection**
- The mock path prefixes returned by engines are stable: `OllamaKnowledgeEngine._call_model` emits responses starting with `محاكاة:` when `AGL_OLLAMA_KB_MOCK` is enabled. Detect this literal prefix to identify stubbed replies.

**Engine bootstrap & registration**
- `bootstrap_register_all_engines` prefers `create_engine(config)` but will construct classes; it validates `process_task` and writes `artifacts/bootstrap_report.json`.
- `_try_registry_register` accepts multiple registry shapes (dict, `register(...)`, `add_engine`). Use existing patterns when adding engines.

**Common developer workflows**
- Run unit tests: `pytest -q` (see `pytest.ini` / `conftest.py`).
- Quick LLM smoke-check used in CI: `python scripts/quick_llm_ping.py --base $AGL_LLM_BASEURL --model $AGL_LLM_MODEL`.
- Bootstrap + inspect report: run the bootstrap path in `conftest.py` or `scripts/` and examine `artifacts/*.json` for registration and latency reports.

**Common issues & remedies (repo-specific)**
- HTTP 405 from Ollama-like endpoints: ensure `AGL_LLM_BASEURL` includes the correct generate path (e.g. `/api/generate`) and server accepts POST.
- `ollama` CLI not found on Windows: either add `ollama.exe` to PATH or set `AGL_LLM_BASEURL` to an HTTP endpoint.
- JSON decode / streaming chunk errors: older Ollama versions return streaming chunks — upgrade Ollama (>=0.2.8) or use client stream-handling.

**When changing code**
- Run `pytest` and check `artifacts/bootstrap_report.json` for registration regressions.
- Follow existing engine registration patterns in `Core_Engines/__init__.py` when adding engines to avoid registry shape mismatches.

If you want, I can (pick one): generate a compact Arabic-first version, add a CI smoke job snippet that runs `quick_llm_ping.py`, or insert a short example PR template referencing these checks. Tell me which to add.
````
