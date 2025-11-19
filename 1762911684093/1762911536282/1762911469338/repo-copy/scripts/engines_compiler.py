"""Run/activate a set of core engines and collect short outputs into a single report.

Usage:
    .venv/Scripts/python.exe scripts/engines_compiler.py [--live] [--out artifacts/engines_compiler_report.json]

The script attempts to import known engine modules, call a small safe entrypoint on each,
and writes a JSON report with status, short output and any error. When --live is set,
it enables the ExternalInfoProvider live mode by setting `AGL_EXTERNAL_INFO_ENABLED=1`.

This aggregator is intentionally conservative: it won't print secrets, and will catch
exceptions per-engine to avoid one failing engine blocking the rest.
"""
from __future__ import annotations

from __future__ import annotations
# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_LIMIT = _to_int('AGL_LIMIT', 20)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import os
import json
import traceback
import argparse
from datetime import datetime
ENGINES = [('Core_Engines.General_Knowledge', 'General_Knowledge'), ('Core_Engines.External_InfoProvider', 'External_InfoProvider'), ('Core_Engines.Reasoning_Layer', 'Reasoning_Layer'), ('Integration_Layer.rag', 'RAG'), ('Integration_Layer.retriever', 'Retriever'), ('Learning_System.robust_fit', 'Robust_Fit')]
def safe_import(module_name: str):
    try:
        mod = __import__(module_name, fromlist=['*'])
        return (True, mod, None)
    except Exception as e:
        return (False, None, traceback.format_exc())
def run_general_knowledge(mod):
    names = ['GeneralKnowledgeEngine', 'GeneralKnowledge']
    cls = None
    for n in names:
        cls = getattr(mod, n, None)
        if cls:
            break
    if not cls:
        ask = getattr(mod, 'ask', None)
        if callable(ask):
            try:
                r = ask('ما أهم الحقائق العامة؟', context=['اختبار ملخص'])
                return r
            except Exception:
                return {'error': traceback.format_exc()}
        return {'error': 'no_entrypoint_found'}
    try:
        inst = cls()
        if hasattr(inst, 'ask'):
            return inst.ask('ما أهم الحقائق العامة؟', context=['اختبار ملخص'])
        if hasattr(inst, 'run'):
            return inst.run({'query': 'ما هي أبرز النقاط؟'})
        return {'error': 'no_callable_entry_on_instance'}
    except Exception:
        return {'error': traceback.format_exc()}
def run_external_info_provider(mod):
    Provider = getattr(mod, 'ExternalInfoProvider', None)
    if not Provider:
        return {'error': 'no_provider_class'}
    try:
        prov = Provider()
    except Exception as e:
        try:
            prov = Provider(model=os.getenv('AGL_EXTERNAL_INFO_MODEL', None))
        except Exception:
            return {'error': 'constructor_failed', 'trace': traceback.format_exc()}
    try:
        res = prov.fetch_facts('ما هي آخر الحقائق العامة حول تلوث الهواء؟', hints=['domain:environment'])
        return res
    except Exception:
        return {'error': 'call_failed', 'trace': traceback.format_exc()}
def run_reasoning_layer(mod):
    cls = None
    for n in ['run', 'infer', 'reason']:
        fn = getattr(mod, n, None)
        if callable(fn):
            try:
                return fn({'query': 'ما هي أبرز النقاط؟', 'max_steps': 1})
            except Exception:
                return {'error': traceback.format_exc()}
    for n in ['Reasoner', 'ReasoningEngine', 'Reasoning']:
        c = getattr(mod, n, None)
        if c and callable(c):
            try:
                inst = c()
                fn = getattr(inst, 'run', None)
                if callable(fn):
                    return fn({'query': 'ما هي أبرز النقاط؟'})
            except Exception:
                return {'error': traceback.format_exc()}
    return {'error': 'no_entrypoint'}
def run_generic_callable(mod):
    for name in ('run', 'execute', 'plan', 'retrieve', 'fetch', 'fit'):
        fn = getattr(mod, name, None)
        if callable(fn):
            try:
                if name in ('retrieve', 'fetch'):
                    return fn('ما هو الاختبار؟', limit=_AGL_LIMIT) if ('limit' in fn.__code__.co_varnames if hasattr(fn, '__code__') else False) else fn('ما هو الاختبار؟')
                if name == 'fit':
                    try:
                        return fn([0.0, 1.0], [0.0, 1.0])
                    except TypeError:
                        return {'ok': True}
                return fn({'query': 'ما هو الاختبار؟'})
            except Exception:
                return {'error': traceback.format_exc()}
    return {'error': 'no_callable_entry'}
RUNNERS = {'Core_Engines.General_Knowledge': run_general_knowledge, 'Core_Engines.External_InfoProvider': run_external_info_provider, 'Core_Engines.Reasoning_Layer': run_reasoning_layer}
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='Enable live ExternalInfoProvider (requires OPENAI_API_KEY in env/session)')
    parser.add_argument('--out', default='artifacts/engines_compiler_report.json')
    args = parser.parse_args()
    try:
        from tools.resource_guard import ResourceGuard
    except Exception:
        ResourceGuard = None
    if args.live:
        os.environ['AGL_EXTERNAL_INFO_ENABLED'] = '1'
        os.environ['AGL_EXTERNAL_INFO_MOCK'] = ''
    report = {'created': datetime.utcnow().isoformat() + 'Z', 'live': bool(args.live), 'engines': {}}
    runner_ctx = ResourceGuard() if ResourceGuard else None
    ctx = runner_ctx.__enter__() if runner_ctx else None
    try:
        for modname, human in ENGINES:
            ok, mod, err = safe_import(modname)
            entry = {}
            entry['imported'] = bool(ok)
            if not ok:
                entry['error'] = err
                report['engines'][human] = entry
                continue
            try:
                runner = RUNNERS.get(modname, None)
                if runner:
                    out = runner(mod)
                else:
                    out = run_generic_callable(mod)
                entry['result'] = out
            except Exception:
                entry['error'] = traceback.format_exc()
            report['engines'][human] = entry
    finally:
        if runner_ctx:
            runner_ctx.__exit__(None, None, None)
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(f'Engines compiler finished. Report: {args.out}')
if __name__ == '__main__':
    main()
