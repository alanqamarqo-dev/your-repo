"""Small smoke probe that bootstraps Core_Engines into the Integration registry
and probes each registered engine with a lightweight payload.

Writes a JSON report to artifacts/engine_probe_report.json and prints a brief
summary to stdout. Designed to be safe: uses minimal probe payloads and
continues on exceptions.
"""
import time
import json
import os
from typing import Any, Dict

from Core_Engines import bootstrap_register_all_engines
from Core_Engines import Orchestrator
from Integration_Layer.integration_registry import registry


REPORT_PATH = os.path.join("artifacts", "engine_probe_report.json")


def safe_call_engine(name: str, eng: Any) -> Dict[str, Any]:
    start = time.monotonic()
    out: Dict[str, Any] = {"engine": name, "ok": False, "duration_s": None, "error": None, "snippet": None}
    try:
        payload = {"text": "probe test", "probe": True}
        # prefer lightweight key names used by many engines
        if hasattr(eng, "process_task"):
            resp = eng.process_task(payload)
        elif hasattr(eng, "process"):
            resp = eng.process(payload)
        else:
            out["error"] = "no-callable-method"
            return out
        dur = time.monotonic() - start
        out["duration_s"] = dur
        out["ok"] = True
        try:
            # capture small snippet for inspection
            if isinstance(resp, dict):
                txt = resp.get("text") or resp.get("answer") or resp.get("result")
                out["snippet"] = (txt[:320] if isinstance(txt, str) else str(type(txt)))
            else:
                out["snippet"] = str(resp)[:320]
        except Exception as e:
            out["snippet"] = f"snippet-failed: {e}"
        return out
    except Exception as e:
        dur = time.monotonic() - start
        out["duration_s"] = dur
        out["error"] = str(e)
        return out


def main():
    os.makedirs("artifacts", exist_ok=True)
    # Bootstrap engines into the Integration registry (idempotent)
    registered = bootstrap_register_all_engines(registry, allow_optional=True, verbose=False)

    # Build a list of engine names currently resolvable from the registry
    try:
        reg_names = list(registry.list_names())
    except Exception:
        try:
            reg_names = list(registry.keys())
        except Exception:
            reg_names = []

    # Probe each registered engine
    probes = []
    for name in reg_names:
        try:
            eng = registry.get(name)
        except Exception:
            eng = None
        if eng is None:
            probes.append({"engine": name, "ok": False, "error": "not_resolvable"})
            continue
        probes.append(safe_call_engine(name, eng))

    # Orchestrator smoke: instantiate with the engines that are available
    engines_map = {}
    for name in reg_names:
        try:
            e = registry.get(name)
            if e is not None:
                engines_map[name] = e
        except Exception:
            continue

    orchestrator_result = None
    try:
        orch = Orchestrator(engines=engines_map)
        orchestrator_result = orch.run_task("probe", {"text": "probe test"})
    except Exception as e:
        orchestrator_result = {"error": str(e)}

    report = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "registered_count": len(registered) if isinstance(registered, dict) else None,
        "registry_names_count": len(reg_names),
        "registry_names": reg_names,
        "probes": probes,
        "orchestrator": orchestrator_result,
    }

    try:
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to write report:", e)

    # Print short summary
    ok = sum(1 for p in probes if p.get("ok"))
    fail = len(probes) - ok
    print(f"Engine probe finished: {ok} OK, {fail} failed. Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
