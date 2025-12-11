import json
import time

# Use the combined facade to ensure unified entrypoint is used
try:
    from dynamic_modules import mission_control_combined as mc
except Exception:
    # fallback to proxy
    from dynamic_modules import mission_control as mc

probes = [
    {"name": "science_blackhole", "payload": {"mission_type": "science", "mission_text": "صمم محاكاة لثقب أسود"}},
    {"name": "creative_story", "payload": {"mission_type": "creative", "mission_text": "اكتب قصة عن مستكشف فضاء"}},
    {"name": "technical_robot", "payload": {"mission_type": "technical", "mission_text": "صمم مخطط لروبوت لاكتشاف الكهوف"}},
    {"name": "strategic_launch", "payload": {"mission_type": "strategic", "mission_text": "وضع خطة استراتيجية لإطلاق قمر صناعي"}},
    {"name": "math_linear", "payload": {"mission_type": "science", "mission_text": "احسب حل المعادلة 3x+5=20"}},
    {"name": "math_fraction", "payload": {"mission_type": "science", "mission_text": "احسب 1/7 + 2/3"}},
]

results = {}
start = time.time()
for p in probes:
    t0 = time.time()
    try:
        # prefer unified_ui_execute if available
        if hasattr(mc, 'unified_ui_execute'):
            res = mc.unified_ui_execute(p['payload'])
        elif hasattr(mc, 'execute_mission'):
            # use execute_mission compatibility wrapper
            res = mc.execute_mission(p['payload'].get('mission_text') or p['payload'].get('topic'))
        else:
            res = {"error": "no executor available"}
    except Exception as e:
        res = {"error": str(e)}
    dt = time.time() - t0
    results[p['name']] = {"payload": p['payload'], "result": res, "elapsed": dt}
    print(f"[{p['name']}] done in {dt:.2f}s")

results['summary'] = {"total_probes": len(probes), "total_time": time.time()-start}
with open('artifacts/multi_probe_results.json','w',encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('WROTE artifacts/multi_probe_results.json')
