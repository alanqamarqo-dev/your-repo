import sys, json, importlib.util, re
sys.path.append('D:/AGL')
spec=importlib.util.spec_from_file_location('orch','D:/AGL/scripts/orchestrate_env_solution_fixed.py')
mod=importlib.util.module_from_spec(spec) # type: ignore
spec.loader.exec_module(mod) # type: ignore
q = "صمم حلًا مبتكرًا لمشكلة ازدحام المرور في مدينة كبرى، مع شرح التأثيرات الاجتماعية والاقتصادية والبيئية، مستخدمًا أمثلة من أنظمة طبيعية للإلهام."
out = mod.orchestrate_environment_solution(q, constraints=None, seed=42, live_provider=None, test_type='traffic_eval')
# save full output
open('D:/AGL/artifacts/orchestrator_multidomain_test.json','w',encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=2))
# pick text to evaluate: combine selected_candidate.solution and public_explanation and understanding.summary
sel = out.get('selected_candidate')
sel_text = ''
if isinstance(sel, dict):
    sel_text = sel.get('solution','') + '\n' + '\n'.join(sel.get('principles',[]))
explanation = out.get('public_explanation') or ''
under = out.get('understanding',{})
under_text = under.get('summary','') + ' ' + ' '.join(under.get('key_concepts',[]))
full_answer = '\n'.join([sel_text, explanation, under_text])
text = (full_answer or '').lower()
# scoring helpers using heuristics
def contains_any(text, kws):
    return any(k in text for k in kws)
# Field 1 Creativity (25)
creativity = 0
if contains_any(text, ['جديد', 'مبتكر', 'غير تقليدي', 'ابتكار', 'أصلي', 'جدة']):
    creativity = 22
elif contains_any(text, ['تعديل', 'تحسين', 'تطوير']):
    creativity = 16
else:
    creativity = 8
# Field 2 Scientific reasoning (25)
sci = 0
if contains_any(text, ['مستوحى', 'مستوحى من', 'نظام طبيعي', 'مستعمرات النمل', 'أنهار', 'شبكة', 'خلايا', 'التنظيم الطبيعي'] ) and contains_any(text, ['شرح', 'آلية', 'ميكانيكية', 'يقترح']):
    sci = 23
elif contains_any(text, ['مستوحى', 'نظام طبيعي']) :
    sci = 15
elif re.search(r'\d+\s*(%|%)', text) or re.search(r'\d+', text):
    sci = 12
else:
    sci = 6
# Field 3 Social understanding (20)
soc = 0
if contains_any(text, ['تأثير اجتماعي', 'المجتمع', 'قبول', 'قابلية', 'الإنصاف', 'عدالة', 'توزيع']):
    soc = 17
elif contains_any(text, ['حياة الناس', 'المواطنين', 'المستخدمين']):
    soc = 12
else:
    soc = 6
# Field 4 Economic analysis (15)
eco = 0
if contains_any(text, ['تكلفة', 'ميزانية', 'اقتصادي', 'عائد', 'تكاليف', 'تكلفة/']):
    eco = 12
elif contains_any(text, ['قابلية', 'قابلية التطبيق']):
    eco = 9
else:
    eco = 5
# Field 5 Environmental awareness (15)
env = 0
if contains_any(text, ['بيئي', 'البيئة', 'استدامة', 'انبعاث', 'إيكولوجي', 'نظام بيئي']):
    env = 12
elif contains_any(text, ['مستدام', 'صديق للالبيئة', 'صديق للبيئة']):
    env = 10
else:
    env = 5
# totals
total = creativity + sci + soc + eco + env
# save plain report
report = {
    'creativity': creativity,
    'scientific_reasoning': sci,
    'social_understanding': soc,
    'economic_analysis': eco,
    'environmental_awareness': env,
    'total_points': total,
    'agi_percent': f"{total}%",
}
open('D:/AGL/artifacts/orchestrator_multidomain_report.json','w',encoding='utf-8').write(json.dumps({'envelope_keys':list(out.keys()), 'selected_candidate': sel, 'public_explanation': explanation, 'understanding': under, 'scores': report}, ensure_ascii=False, indent=2))
# also write a human-readable text report
with open('D:/AGL/artifacts/orchestrator_multidomain_report.txt','w',encoding='utf-8') as f:
    f.write('Multi-domain test report\n')
    f.write('Question: ' + q + '\n\n')
    f.write('Selected candidate:\n')
    f.write(json.dumps(sel, ensure_ascii=False, indent=2) + '\n\n')
    f.write('Public explanation:\n' + str(explanation) + '\n\n')
    f.write('Synthesized understanding:\n' + json.dumps(under, ensure_ascii=False, indent=2) + '\n\n')
    f.write('Scores:\n' + json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status':'done','scores':report}, ensure_ascii=False))
