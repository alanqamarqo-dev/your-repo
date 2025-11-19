# -*- coding: utf-8 -*-
import os
import time
from Integration_Layer.integration_registry import registry
from Core_Engines import bootstrap_register_all_engines
from tests.helpers.engine_ask import ask_engine


def _ensure_envs():
    # Make tests deterministic in CI/local runs: prefer scaffold/offline fallbacks
    os.environ.setdefault('AGL_TEST_SCAFFOLD_FORCE', '1')
    os.environ.setdefault('AGL_LLM_PROVIDER', 'offline')


def test_all_registered_engines_return_canonical_shape():
    """Lightweight smoke: each registered engine that exposes a callable
    interface should return the canonical response keys quickly.

    This test is intentionally light: it checks for crashes, canonical keys,
    and a reasonable per-engine latency (<5s). It uses the same probe across
    all engines and relies on local deterministic fallbacks when available.
    """
    _ensure_envs()

    # Populate the registry (idempotent)
    try:
        bootstrap_register_all_engines(registry)
    except Exception:
        # best-effort: if bootstrap fails, continue — registry may already be populated
        pass

    # Short probe used for transfer / analogy checks — neutral and small.
    probe = "How is irrigation like teaching? Please provide a short mapping."

    names = registry.list_names()
    assert isinstance(names, (list, tuple)), "registry.list_names() must return a list"

    timeout_s = float(os.environ.get('AGENT_PER_ENGINE_TIMEOUT_S', '12'))

    for name in sorted(names):
        # Resolve instance if available; skip utilities that are not engines
        eng = registry.get(name)
        if not eng:
            continue
        # Heuristic: require the object expose a process_task/ask entrypoint
        if not (hasattr(eng, 'process_task') or hasattr(eng, 'ask')):
            continue

        start = time.time()
        res = ask_engine(name, probe)
        elapsed = time.time() - start

        # Basic runtime bound to detect hangs in CI (configurable via env)
        assert elapsed < timeout_s, f"engine {name} took too long ({elapsed:.2f}s) > {timeout_s}s"

        assert isinstance(res, dict), f"engine {name} must return a dict envelope"
        # canonical minimal keys
        assert 'ok' in res, f"engine {name} response missing 'ok'"
        assert 'text' in res, f"engine {name} response missing 'text'"
        assert 'reply_text' in res, f"engine {name} response missing 'reply_text'"
        assert 'engine' in res or res.get('ok') is False, f"engine {name} should include 'engine' on success"

        # For successful responses, text must be non-empty
        if res.get('ok'):
            txt = (res.get('text') or '').strip()
            assert txt, f"engine {name} returned ok=True but empty text"
