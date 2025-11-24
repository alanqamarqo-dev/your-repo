import sys, os, json
sys.path.insert(0, r'D:\AGL\repo-copy')
results = {}

# 1) Core_Consciousness imports and instantiate
try:
    from Core_Consciousness import SelfModel, PerceptionLoop, IntentGenerator, StateLogger
    results['consciousness_import'] = 'ok'
    sm = SelfModel()
    try:
        pl = PerceptionLoop(self_model=sm, interval=0.0, sample_scope='stm')
        results['perception_init'] = 'ok'
    except Exception as e:
        results['perception_init'] = f'err: {e}'
except Exception as e:
    results['consciousness_import'] = f'err: {e}'

# 2) run run_once if possible
try:
    if 'pl' in globals():
        r = pl.run_once()
        results['perception_run_once'] = 'ok'
    else:
        results['perception_run_once'] = 'skipped'
except Exception as e:
    results['perception_run_once'] = f'err: {e}'

# 3) C_Layer StateLogger snapshot
try:
    from Core.C_Layer.state_logger import StateLogger as CStateLogger
    cs = CStateLogger()
    p = cs.snapshot({'hello':'world'}, tags={'phase':'test_integration'})
    results['c_layer_state_snapshot'] = ('ok', p)
except Exception as e:
    results['c_layer_state_snapshot'] = f'err: {e}'

# 4) CuriosityEngine detect + register
try:
    from Core_Engines.Self_Reflective import create_curiosity_engine
    ce = create_curiosity_engine()
    triggers = ce.detect_curiosity_triggers([{'type':'question','payload':{'text':'What is X?'}}])
    try:
        ce.register_question({'type':'question','text':'What is X?'})
        reg_stat = 'registered'
    except Exception as e:
        reg_stat = f'register_err: {e}'
    results['curiosity'] = {'detect': triggers, 'register': reg_stat}
except Exception as e:
    results['curiosity'] = f'err: {e}'

# 5) ReflectiveCortex
try:
    from Core_Consciousness.Self_Model import ReflectiveCortex
    rc = ReflectiveCortex(sm)
    summ = rc.reflect_on_performance([{'success':False,'latency_ms':200,'task':'t1'},{'success':False,'latency_ms':250,'task':'t1'}])
    results['reflective'] = summ
except Exception as e:
    results['reflective'] = f'err: {e}'

# 6) bootstrap register all engines
try:
    from Core_Engines import bootstrap_register_all_engines
    reg = {}
    registered = bootstrap_register_all_engines(reg, allow_optional=True)
    results['bootstrap_registered_count'] = len(registered)
    results['bootstrap_sample_keys'] = list(registered.keys())[:10]
except Exception as e:
    results['bootstrap'] = f'err: {e}'

out_dir = os.path.join(r'D:\AGL\repo-copy','artifacts','state')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'integration_check.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('WROTE', out_path)
print(json.dumps(results, ensure_ascii=False, indent=2))
