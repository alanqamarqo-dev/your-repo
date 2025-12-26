---
Short, actionable guidance for AI coding assistants working in this repository.

Purpose: help an AI agent be productive quickly — architecture, key files, run/test workflows, env vars, and repo-specific patterns.

Big picture (3 layers):
- `repo-copy/Core_Engines/` — LLM adapters, knowledge engines and engine registry (`Hosted_LLM.py`, `Ollama_KnowledgeEngine.py`, `__init__.py`).
- `repo-copy/Integration_Layer/` — prompt composition and routing (`Hybrid_Composer.py`, `Action_Router.py`, `rag_wrapper.py`).
- UI / scripts / tools — smoke checks and helpers (`scripts/quick_llm_ping.py`, `scripts/*`, `AGL_UI/`).

Key files to consult (relative to repo root):
- `repo-copy/Core_Engines/Hosted_LLM.py` — `chat_llm(messages, max_new_tokens, temperature)` (provider selection and HTTP/CLI fallbacks).
- `repo-copy/Core_Engines/__init__.py` — `ENGINE_SPECS` + `bootstrap_register_all_engines()` (registration patterns).
- `repo-copy/Integration_Layer/Hybrid_Composer.py` — `build_prompt_context(story, questions)` (returns system+user messages).
- `repo-copy/Integration_Layer/rag_wrapper.py` — RAG orchestration entrypoint.
- `repo-copy/AGENT.md` — concise Arabic-first quickstart for devs/agents.

Model selection & env vars (exact names — keep these literal):
- `AGL_LLM_PROVIDER`, `AGL_LLM_MODEL`, `AGL_LLM_BASEURL`, `OLLAMA_API_URL`
- Mocks/caching: `AGL_EXTERNAL_INFO_MOCK`, `AGL_OLLAMA_KB_MOCK`, `AGL_OPENAI_KB_MOCK`, `AGL_OLLAMA_KB_CACHE_ENABLE`
- HTTP tuning/timeouts: `AGL_HTTP_RETRIES`, `AGL_HTTP_BACKOFF`, `AGL_LLM_TIMEOUT`

Prompt & messaging conventions:
- Use `repo-copy/Integration_Layer/Hybrid_Composer.build_prompt_context(story, questions)` to produce system/user messages.
- Important: `chat_llm` currently consumes only the first `system` and first `user` message — merge additional content into the first user entry if needed.

Mock detection:
- When `AGL_OLLAMA_KB_MOCK` is enabled, `OllamaKnowledgeEngine._call_model` returns responses prefixed with `محاكاة:` — detect that exact prefix to identify mocked replies.

Engine bootstrap & artifacts:
- `bootstrap_register_all_engines(registry, allow_optional, max_seconds)` prefers `create_engine(config)` factories, validates `process_task`, handles multiple registry shapes, and writes `artifacts/bootstrap_report.json` with registered/skipped engines and latencies.

Quick developer workflows:
- Run tests: `pytest -q` or `pytest -m smoke` (`repo-copy/tests/conftest.py` bootstraps engines once per test session).
- LLM smoke-check (PowerShell):
```powershell
Remove-Item env:AGL_EXTERNAL_INFO_MOCK -ErrorAction SilentlyContinue;
Remove-Item env:AGL_OLLAMA_KB_MOCK -ErrorAction SilentlyContinue;
$env:AGL_LLM_PROVIDER='ollama';
$env:AGL_LLM_MODEL='qwen2.5:7b-instruct';
$env:AGL_LLM_BASEURL='http://localhost:11434';
python repo-copy/scripts/quick_llm_ping.py --base $env:AGL_LLM_BASEURL --model $env:AGL_LLM_MODEL
Short, actionable guidance for AI coding assistants working in this repository.

Purpose: help an AI agent be productive quickly — architecture, key files, run/test workflows, env vars, and repo-specific patterns.

Common issues & quick fixes:
- 405 Method Not Allowed: ensure `AGL_LLM_BASEURL` targets an endpoint that accepts POST (e.g. `/api/generate`).
- `ollama` CLI not found on Windows: add `ollama.exe` to PATH or use HTTP by setting `AGL_LLM_BASEURL`.
- JSON decode / streaming chunk errors: older Ollama returns chunked streams — upgrade to Ollama >= 0.2.8 or handle streaming in client.

Adding or changing engines:
- Update `repo-copy/Core_Engines/__init__.py`'s `ENGINE_SPECS` with `"EngineName": ("module.path", "ClassName")`.
- Prefer a `create_engine(config)` factory in the new engine module and implement `process_task(payload)`.
- Run `pytest -m smoke` and inspect `artifacts/bootstrap_report.json` for registration results.

If you want a fully Arabic-first variant, additional CI smoke-hook, or a short PR template that runs `quick_llm_ping.py`, tell me which and I'll add it.

---
Short, actionable guidance for AI coding assistants working in this repository.

**Purpose:** help AI coding agents be productive quickly: architecture, key files, run/test workflows, env vars, and code patterns unique to this repo.

**Big picture**: the project is an on-prem AGL (Autonomous General Learning) orchestration stack — an advanced autonomous agent with proto-AGI capabilities (Level 3), featuring volition, self-evolution, self-healing, and multi-domain competence.

**Directory structure** (dual layout: root + repo-copy):
- `repo-copy/Core_Engines/` — Cognitive modules ("Brain"): LLM adapters (Hosted_LLM, Ollama_KnowledgeEngine), knowledge engines (General_Knowledge, GK_graph), reasoning layers, and 40+ specialized engines. Engine registration via `ENGINE_SPECS` dict.
- `repo-copy/Integration_Layer/` — Orchestration logic ("Prefrontal Cortex"): prompt composers (Hybrid_Composer), routing (Action_Router), RAG wrapper, task orchestrator, and integration registry.
- `repo-copy/Learning_System/` — Self-improvement: experience memory, meta-cognition, generalization matrix, self-engineering, model zoo.
- `repo-copy/Safety_Systems/` — Safety rails: Emergency_Protection_Layer, Core_Values_Lock (immutable ethics), rollback mechanisms.
- `scripts/`, `tests/`, `artifacts/` — Helper scripts, test suites, and generated reports (bootstrap_report.json, logs).

**Key files to consult** (all paths relative to `repo-copy/`):
- `Core_Engines/Hosted_LLM.py`: central `chat_llm(messages, max_new_tokens, temperature)` entrypoint and provider selection (Ollama HTTP → CLI → OpenAI fallback).
- `Core_Engines/__init__.py`: `ENGINE_SPECS` dict (40+ engines), `bootstrap_register_all_engines(registry, allow_optional, max_seconds)` — initializes and registers all engines.
- `Core_Engines/Ollama_KnowledgeEngine.py`: `LocalKnowledgeEngine.process_task()` — mock detection: returns `"محاكاة: ..."` prefix when `AGL_OLLAMA_KB_MOCK=1`.
- `Integration_Layer/Hybrid_Composer.py`: `build_prompt_context(story, questions)` — returns `[{"role":"system","content":...}, {"role":"user","content":...}]` messages list. Preferred prompt builder for Arabic-first tasks.
- `Integration_Layer/rag_wrapper.py`: `rag_answer(query, context)` — RAG orchestration, calls Hybrid_Composer → chat_llm.
- `Integration_Layer/Action_Router.py`: `route(task, law, kv, session_id)` — domain-specific routing (e.g., solve_ohm).
- `conftest.py` (in repo-copy/tests/): sets default RAG env vars (`AGL_FEATURE_ENABLE_RAG=1`, `AGL_LLM_MODEL`), runs `bootstrap_register_all_engines` once per pytest session, guards against duplicate registrations.
- `artifacts/bootstrap_report.json`: produced after engine bootstrap — lists registered/skipped engines, latency metrics. Essential for debugging registration issues.

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

**Engine bootstrap & registration** (Core_Engines/__init__.py patterns):
- `bootstrap_register_all_engines(registry, allow_optional, max_seconds)` iterates through `ENGINE_SPECS` dict (40+ engines), attempting imports and registration.
- Prefers `create_engine(config)` factory pattern, falls back to direct class instantiation.
- Validates each engine has a `process_task` method before registering.
- Respects `max_seconds` timeout (default: 60s in conftest) to avoid slow collection with heavy optional engines.
- Writes results to `artifacts/bootstrap_report.json` including: registered engines, skipped engines (with reasons like "import failed", "no create_engine", "timeout"), and init latency per engine.
- `_try_registry_register` helper accepts multiple registry shapes: dict (`registry[name] = engine`), Registry object with `register(name, engine)`, or `add_engine(name, engine)`. Use existing patterns when adding new engines.

**Common developer workflows** (from project root `d:\AGL\`):
- Run unit tests: `pytest -q` or `pytest -m smoke` (see `pytest.ini` for markers: `smoke`, `integration`).
  - `conftest.py` auto-bootstraps engines once per session (with 60s timeout to avoid slow collection).
  - Bootstrap result written to `artifacts/bootstrap_report.json` — check for skipped engines if tests fail.
- Quick LLM smoke-check (example, adapt paths): 
  ```powershell
  $env:AGL_LLM_PROVIDER='ollama'; $env:AGL_LLM_MODEL='qwen2.5:7b-instruct'; $env:AGL_LLM_BASEURL='http://localhost:11434';
  python repo-copy/quick_llm_ping.py --base $env:AGL_LLM_BASEURL --model $env:AGL_LLM_MODEL
  ```
- Bootstrap + inspect engines: after running tests, examine `artifacts/bootstrap_report.json` for registered engines, skipped engines (with reasons), and init latencies.

**Common issues & remedies (repo-specific)**
- HTTP 405 from Ollama-like endpoints: ensure `AGL_LLM_BASEURL` includes the correct generate path (e.g. `/api/generate`) and server accepts POST.
- `ollama` CLI not found on Windows: either add `ollama.exe` to PATH or set `AGL_LLM_BASEURL` to an HTTP endpoint.
- JSON decode / streaming chunk errors: older Ollama versions return streaming chunks — upgrade Ollama (>=0.2.8) or use client stream-handling.

**When changing code** (validation checklist):
- Run `pytest` and verify exit code 0 (all tests pass).
- Check `artifacts/bootstrap_report.json` for registration regressions (new skipped engines, increased init latency).
- Follow existing engine registration patterns in `Core_Engines/__init__.py` when adding engines:
  - Add entry to `ENGINE_SPECS` dict: `"EngineName": ("module.path", "ClassName")`.
  - Implement `create_engine(config)` factory and `process_task(payload)` method.
  - Test bootstrap with `pytest -m smoke` to verify registration.

If you want, I can (pick one): generate a compact Arabic-first version, add a CI smoke job snippet that runs `quick_llm_ping.py`, or insert a short example PR template referencing these checks. Tell me which to add.
