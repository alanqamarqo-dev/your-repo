# -*- coding: utf-8 -*-
"""Integration cohesion check script
Runs a series of lightweight checks across AGL modules and reports a cohesion score.
"""
import os
import json
import math
import traceback
import sys
from pathlib import Path

# Ensure repo root is on sys.path so top-level modules (AGL, Integration_Layer, Core_Engines) import
sys.path.insert(0, str(Path(__file__).parent.parent))

report = {
    'checks': [],
    'score': 0.0,
    'max_score': 0.0,
}

# set simulate mode for quantum simulator to avoid external calls
os.environ['AGL_QUANTUM_MODE'] = os.getenv('AGL_QUANTUM_MODE', 'simulate')

# helper to record check
def record(name, ok, weight, details=None):
    report['checks'].append({'name': name, 'ok': bool(ok), 'weight': weight, 'details': details})
    if ok:
        report['score'] += weight
    report['max_score'] += weight

# 1) import AGL
try:
    import AGL
    # instantiate an AGL instance so its _initialize_integration_layer runs and
    # (when env requests) DKN components are created and registered
    try:
        # The repo contains both a module `AGL.py` and a package `AGL/` which
        # can complicate imports. Attempt to load the top-level file `AGL.py`
        # directly to access the helper `create_agl_instance` if present.
        try:
            import importlib.util
            agl_path = Path(__file__).parent.parent / 'AGL.py'
            if agl_path.exists():
                spec = importlib.util.spec_from_file_location('agl_module', str(agl_path))
                agl_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(agl_module)  # type: ignore
                try:
                    agl = getattr(agl_module, 'create_agl_instance')()
                except Exception:
                    try:
                        agl = getattr(agl_module, 'AGL')()
                    except Exception:
                        agl = None
            else:
                # fallback: try typical module-level constructor if available
                try:
                    agl = getattr(AGL, 'create_agl_instance')()
                except Exception:
                    try:
                        agl = getattr(AGL, 'AGL')()
                    except Exception:
                        agl = None
        except Exception:
            agl = None
    except Exception:
        agl = None
    record('import_agl', True, 10, 'AGL imported')
except Exception as e:
    record('import_agl', False, 10, f'Import failed: {e}\n{traceback.format_exc()}')

# 2) bootstrap core engines into registry
try:
    from Integration_Layer.integration_registry import registry
    import Core_Engines as CE
    CE.bootstrap_register_all_engines(registry, allow_optional=True)
    keys = []
    try:
        keys = list(registry.keys())
    except Exception:
        try:
            # fallback if registry lacks keys()
            keys = [k for k in registry.__dict__.keys() if not k.startswith('_')]
        except Exception:
            keys = []
    ok = 'Quantum_Simulator_Wrapper' in keys or registry.get('Quantum_Simulator_Wrapper') is not None
    record('bootstrap_register', ok, 15, f'registry_keys_count={len(keys)}')
except Exception as e:
    record('bootstrap_register', False, 15, f'bootstrap failed: {e}\n{traceback.format_exc()}')

# 3) quantum simulator QFT
try:
    sim = registry.get('Quantum_Simulator_Wrapper')
    if sim is None:
        raise RuntimeError('Quantum_Simulator_Wrapper not found in registry')
    res = sim.process_task({'op': 'qft', 'params': {'num_qubits': 2, 'basis': '00'}})
    ok = bool(res.get('ok')) and isinstance(res.get('qft_probs'), dict) and len(res.get('qft_probs')) == 4
    record('quantum_qft', ok, 20, {'res': res})
except Exception as e:
    record('quantum_qft', False, 20, f'exception: {e}\n{traceback.format_exc()}')

# 4) simulate_superposition_measure
try:
    res2 = sim.process_task({'op': 'simulate_superposition_measure', 'params': {'num_qubits': 2, 'gates': [{'type': 'H', 'target': 0}, {'type': 'H', 'target': 1}], 'shots': 1024}})
    probs = res2.get('probabilities') if isinstance(res2, dict) else None
    total = sum(probs.values()) if isinstance(probs, dict) else 0.0
    ok = bool(res2.get('ok')) and isinstance(probs, dict) and len(probs) == 4 and math.isclose(total, 1.0, rel_tol=1e-2, abs_tol=1e-2)
    record('simulate_superposition_measure', ok, 20, {'res': res2})
except Exception as e:
    record('simulate_superposition_measure', False, 20, f'exception: {e}\n{traceback.format_exc()}')

# 5) quantum_neural_forward deterministic
try:
    a = sim.process_task({'op': 'quantum_neural_forward', 'params': {'input': 'hello'}})
    b = sim.process_task({'op': 'quantum_neural_forward', 'params': {'input': 'hello'}})
    ok = bool(a.get('ok')) and bool(b.get('ok')) and a.get('logits') == b.get('logits')
    record('quantum_neural_forward_deterministic', ok, 10, {'a': a, 'b': b})
except Exception as e:
    record('quantum_neural_forward_deterministic', False, 10, f'exception: {e}\n{traceback.format_exc()}')

# 6) registry core services presence
try:
    keys = list(registry.keys())
    needed = ['hybrid_composer', 'task_orchestrator', 'communication_bus', 'rag']
    found = []
    for k in needed:
        try:
            has_k = (k in keys)
        except Exception:
            has_k = False
        if hasattr(registry, 'has'):
            try:
                has_k = has_k or bool(registry.has(k))
            except Exception:
                pass
        try:
            if not has_k:
                # try resolve/get as last resort
                try:
                    v = registry.get(k)
                    has_k = v is not None
                except Exception:
                    try:
                        v = registry.resolve(k)
                        has_k = v is not None
                    except Exception:
                        has_k = has_k
        except Exception:
            pass
        if has_k:
            found.append(k)
    ok = len(found) >= 2
    record('registry_core_services', ok, 10, {'found': found, 'all_keys_len': len(keys)})
except Exception as e:
    record('registry_core_services', False, 10, f'exception: {e}\n{traceback.format_exc()}')

# 7) DKN components presence
try:
    dkn_present = all((registry.has('dkn_bus') if hasattr(registry, 'has') else ('dkn_bus' in list(registry.keys())),
                       registry.has('knowledge_graph') if hasattr(registry, 'has') else ('knowledge_graph' in list(registry.keys())),
                       registry.has('meta_orchestrator') if hasattr(registry, 'has') else ('meta_orchestrator' in list(registry.keys()))))
    record('dkn_components', dkn_present, 10, {'dkn_present': dkn_present})
except Exception as e:
    record('dkn_components', False, 10, f'exception: {e}\n{traceback.format_exc()}')

# 8) meta_orchestrator available & callable
try:
    mo = None
    try:
        mo = registry.get('meta_orchestrator')
    except Exception:
        try:
            mo = registry.resolve('meta_orchestrator')
        except Exception:
            mo = None
    ok = (mo is not None and hasattr(mo, 'consensus_and_emit') and callable(getattr(mo, 'consensus_and_emit')))
    details = {'meta_orchestrator_type': type(mo).__name__ if mo is not None else None}
    # attempt to call it but guard against side-effects
    if ok:
        try:
            mo.consensus_and_emit()
            details['consensus_called'] = True
        except Exception as e:
            details['consensus_called'] = False
            details['consensus_error'] = str(e)
    record('meta_orchestrator_callable', ok, 5, details)
except Exception as e:
    record('meta_orchestrator_callable', False, 5, f'exception: {e}\n{traceback.format_exc()}')

# compute percentage
percent = 0.0
if report['max_score'] > 0:
    percent = (report['score'] / report['max_score']) * 100.0
report['cohesion_percent'] = round(percent, 2)

# print human-friendly summary + JSON
print('\nINTEGRATION COHESION REPORT\n')
print(f"Score: {report['score']}/{report['max_score']} ({report['cohesion_percent']}%)\n")
for c in report['checks']:
    print(f"- {c['name']}: {'PASS' if c['ok'] else 'FAIL'} (weight={c['weight']}) - {c.get('details')}")

print('\nFull JSON report:')
print(json.dumps(report, ensure_ascii=False, indent=2))

# exit with non-zero if critical failures (e.g., quantum ops failed)
critical_fail = any(not c['ok'] for c in report['checks'] if c['name'] in ('quantum_qft', 'simulate_superposition_measure'))
if critical_fail:
    raise SystemExit(1)
else:
    raise SystemExit(0)
