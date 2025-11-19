"""Run a quick probe across registered engines and write artifacts/engine_probe.json.

This is CI-friendly and deterministic when AGL_LLM_PROVIDER=offline.
"""
import json
import os
import time
import sys

# Ensure the repository root is on sys.path so local packages import reliably
sys.path.insert(0, os.path.abspath(os.getcwd()))

from Integration_Layer.integration_registry import registry
from Core_Engines import bootstrap_register_all_engines


def main():
    os.makedirs('artifacts', exist_ok=True)
    # populate registry similarly to the tests
    try:
        bootstrap_register_all_engines(registry, allow_optional=True)
    except Exception:
        # best-effort
        pass

    names = sorted(registry.list_names())
    probe = []
    prompt = "اختبار أداء سريع: اذكر ثلاث نقاط موجزة"  # short Arabic probe

    for name in names:
        start = time.time()
        ok = False
        text_len = 0
        try:
            eng = registry.get(name)
            if eng is None:
                resp = {"ok": False, "error": "missing"}
            else:
                try:
                    resp = eng.process_task({"query": prompt})
                except Exception:
                    try:
                        resp = eng.process_task(prompt)
                    except Exception as e:
                        resp = {"ok": False, "error": str(e)}
            elapsed_ms = int((time.time() - start) * 1000)
            if isinstance(resp, dict):
                ok = bool(resp.get('ok') is True)
                text = resp.get('text') or resp.get('reply_text') or resp.get('summary') or resp.get('answer') or ''
                text_len = len(text or '')
            else:
                ok = False
                text_len = len(str(resp or ''))
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            ok = False
            text_len = 0
            resp = {"ok": False, "error": str(e)}

        probe.append({"name": name, "ok": ok, "elapsed_ms": elapsed_ms, "text_len": text_len})

    out_path = os.path.join('artifacts', 'engine_probe.json')
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(probe, fh, ensure_ascii=False, indent=2)

    print(f"Wrote probe results for {len(probe)} engines to {out_path}")


if __name__ == '__main__':
    main()
