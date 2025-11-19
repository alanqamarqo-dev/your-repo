"""Pytest bootstrap helpers for the repo-copy test runs.

This file ensures the `agl` package directory is loaded as the `agl` module
early during pytest collection. On Windows the top-level `AGL.py` module and
the `agl/` package can conflict (case-insensitive filesystem). Tests expect
`import agl` to resolve to the package; this hook loads the package
explicitly when needed.
"""
from pathlib import Path
import sys
import importlib.util


def _ensure_agl_package():
    try:
        import agl  # type: ignore # noqa: F401
        return
    except Exception:
        # fall through and try to load package from repo-copy/agl
        pass

    root = Path(__file__).resolve().parent
    pkg_dir = root / "agl"
    init_py = pkg_dir / "__init__.py"
    if not init_py.exists():
        return

    try:
        spec = importlib.util.spec_from_file_location("agl", str(init_py))
        module = importlib.util.module_from_spec(spec)
        # mark as package
        module.__package__ = "agl"
        module.__path__ = [str(pkg_dir)]
        # register before executing so relative imports inside the package work
        sys.modules.setdefault("agl", module)
        if spec and spec.loader:
            spec.loader.exec_module(module)
        # also register uppercase alias for compatibility
        sys.modules.setdefault("AGL", module)
    except Exception:
        # best-effort only; do not raise to avoid breaking unrelated test collection
        try:
            # cleanup partial registration if it failed
            if "agl" in sys.modules and getattr(sys.modules["agl"], "__file__", None) is None:
                del sys.modules["agl"]
        except Exception:
            pass


_ensure_agl_package()
import os
import pytest

# Lock essential environment variables for tests so test runs are reproducible
# (these defaults are used only when the variable is not already set).
os.environ.setdefault("AGL_FEATURE_ENABLE_RAG", "1")
# Only set a default LLM model if mock RAG is NOT explicitly enabled. When running with
# mock RAG (AGL_OLLAMA_KB_MOCK or AGL_EXTERNAL_INFO_MOCK), tests should treat the LLM
# as unavailable and rely on deterministic mock responses.
if not (os.environ.get("AGL_OLLAMA_KB_MOCK") or os.environ.get("AGL_EXTERNAL_INFO_MOCK")):
	os.environ.setdefault("AGL_LLM_MODEL", "qwen2.5:3b-instruct")
	os.environ.setdefault("AGL_LLM_BASEURL", "http://127.0.0.1:11434")


# Guard so bootstrap runs only once per pytest process. Some test suites or helpers
# call bootstrap again; this flag prevents duplicate registration attempts which
# previously caused many tests to be marked XFAIL with "registry rejected" reasons.
_bootstrap_done = False


# --- Bootstrap engines once per test session ---------------------------------
# Ensure the Core_Engines bootstrap runs once. We intentionally do NOT clear the
# Integration registry here to preserve previously-registered services; duplicate
# registration is handled idempotently by the registry (see Integration_Layer).
try:
	# import lazily so tests that don't need engines won't pay import cost
	from Core_Engines import __init__ as engines  # type: ignore
	from Integration_Layer.integration_registry import registry as integration_registry
except Exception:
	engines = None
	integration_registry = None


def pytest_configure(config):
	"""Called by pytest before collection. Bootstrap engines if possible."""
	global _bootstrap_done
	# If imports failed (e.g., running linters), skip bootstrap quietly
	if engines is None or integration_registry is None:
		return
	if _bootstrap_done:
		return
	try:
		# allow_optional True so missing heavy deps don't fail the test run
		engines.bootstrap_register_all_engines(integration_registry, allow_optional=True)
		# Add well-known aliases to ease tests that use alternate names
		try:
			if hasattr(integration_registry, 'alias'):
				try:
					integration_registry.alias('CAUSAL_GRAPH', 'Causal_Graph')
				except Exception:
					pass
		except Exception:
			pass
	except Exception:
		# do not raise here; tests will surface missing functionality where required
		pass
	_bootstrap_done = True


@pytest.fixture(scope="session", autouse=True)
def _warm_up_engine_calls():
	"""Warm-up call to exercise a small engine path so infra.engine_monitor
	gets initial data recorded. This makes `/api/system/status` non-empty after
	tests bootstrapped.

	The fixture is forgiving and never fails tests if engines are absent.
	"""
	try:
		from Integration_Layer.integration_registry import registry
		# pick a light-weight engine name that commonly exists; skip if missing
		for candidate in ("Visual_Spatial", "Consistency_Checker", "Causal_Graph"):
			try:
				if candidate in registry:
					eng = registry.get(candidate)
					if hasattr(eng, "process_task"):
						try:
							eng.process_task({"op": "ping"}) # type: ignore
						except Exception:
							# ignore engine runtime errors during warm-up
							pass
					break
			except Exception:
				# ignore errors resolving/calling this candidate and try next
				continue
	except Exception:
		# intentionally silent: warm-up must not fail the test session
		pass

