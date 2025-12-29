import os, json, sys
# ensure repo root is importable when running this script directly
sys.path.insert(0, os.getcwd())
from Learning_System.Self_Engineer import SelfEngineer
from Core_Engines.AdvancedMetaReasoner import analyze_thinking_quality, generate_self_improvement_plan

os.makedirs('artifacts', exist_ok=True)
se = SelfEngineer()
# run a small meta cycle which will emit traces via the instrumented SelfEngineer
out = se.meta_improvement_cycle(test_reports=[{'type':'pytest','payload':{'failures':[]}}], max_candidates=2)
open('artifacts/meta_improvement_cycle_out.json','w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=2))
# analyze traces
q = analyze_thinking_quality()
plan = generate_self_improvement_plan()
report = {'quality': q, 'plan': plan}
open('artifacts/advanced_meta_report.json','w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2))
print('WROTE artifacts/advanced_meta_report.json')
