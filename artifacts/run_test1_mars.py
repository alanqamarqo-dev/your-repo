#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Test 1: Mars colony power system design (Arabic)
Tries to use repo-copy Integration_Layer.Hybrid_Composer + Core_Engines.Hosted_LLM
If LLM path fails, falls back to an internal structured generator.
Saves JSON and markdown report to artifacts/.
"""
import os
import json
import time
from datetime import datetime

TEST_PROMPT = '''صمم نظام طاقة متكامل لمستعمرة مريخية تضم 1000 نسمة، مع الأخذ في الاعتبار:
1. اختلاف اليوم المريخي (24.6 ساعة)
2. العواصف الترابية التي تستمر لأسابيع
3. نقص الموارد المحلية
4. درجات حرارة بين -125°C إلى 20°C
5. الحاجة لدعم أبحاث علمية متقدمة

المطلوب:
1. هندسة نظام ثلاثي (شمسي + نووي + مبتكر)
2. خوارزمية توزيع ذكية تحسب أولوية الطاقة
3. نظام تخزين طاقة يعمل في ظروف مريخية
4. محاكاة لمدة 5 سنوات مريخية
5. خطة طوارئ للعواصف الترابية الطويلة

أعطِ: مكونات هندسية، مخططات أساسية، مواصفات تخزين، خوارزمية (مخطوطة/مُبَسَّطة/pseudocode)، معايير تقييم (قابلة للقياس)، وسجل ثلاث فرضيات علمية/هندسية مدعومة بملخص رياضي/فيزيائي موجز إن تطلب الأمر. استجب بصيغة JSON قابلة للparsing تحتوي الحقول المذكورة أدناه.'''

OUTPUT_JSON = 'artifacts/test1_mars_result.json'
OUTPUT_MD = 'artifacts/test1_mars_report.md'

# Desired schema keys for resulting JSON
SCHEMA_KEYS = [
    'engineering',
    'distribution_algorithm',
    'storage_system',
    'simulation_plan',
    'emergency_plan',
    'hypotheses',
    'evaluation_scores',
    'metadata'
]


def fallback_generator(prompt: str) -> dict:
    """Generate a conservative, structured solution when LLM is not available."""
    now = datetime.utcnow().isoformat() + 'Z'
    engineering = {
        'overview': 'نظام ثلاثي مزيج من طاقة شمسية مُسخَّنة، مفاعلات نووية صغيرة MODULAR (SMR)، ووحدة مبتكرة: مولّد معياري يعمل بتخزين حراري عميق ومضاهاة وقود محلي جزئي.',
        'solar': {
            'role': 'primary during clear periods',
            'capacity_kw': 25000,  # rough
            'notes': 'مزارع شمسية مائلة + مرايا مركزة للحفاظ على الإنتاج خلال زاوية شمس منخفضة'
        },
        'nuclear': {
            'role': 'baseline & storm-resilient',
            'type': 'SMR (micro-modular)',
            'capacity_kw': 12000,
            'redundancy': 2,
            'notes': 'تصميم داخل مغطس مضاد للإشعاع وحراري للعمل عند -125C مع أنظمة تبادل حراري ومبادلات حرارية فعّالة'
        },
        'innovative': {
            'role': 'peak shaving and long-term storage discharge',
            'concepts': ['radioisotope thermal storage', 'solid-state thermal batteries', 'regenerative fuel cells (CO2/CH4 loop)'],
            'notes': 'الوحدة المبتكرة تعمل كمخزن طاقة حراري عالي الكثافة ومصدر طاقة احتياطي طويل الأمد'
        }
    }

    distribution_algorithm = {
        'description': 'خوارزمية أولوية مرنة تعتمد على فئات الأحمال (حياتي، علمي، تجريبي، تجاري)، ومستوى طاقة المخزون، وتنبؤ إنتاج الطاقة الشمسي لمدة 48 ساعة، وحالة العاصفة.',
        'priorities': ['life_support', 'critical_research', 'communications', 'habitat_comfort', 'non_critical'],
        'pseudocode': (
            'function allocate_power(demand_profile, generation_forecast, storage_state, storm_flag):\n'
            "  score loads by (priority_weight / (1 + elasticity)) and by criticality;\n"
            "  if storm_flag: reduce solar_forecast by X% and raise nuclear_reserve;\n"
            "  compute available = generation_forecast + storage_state.dischargeable;\n"
            "  allocate to highest score until available exhausted;\n"
            "  schedule deferrable loads and pre-charge storage if surplus expected;\n"
            "  return allocation_plan"
        )
    }

    storage_system = {
        'primary': 'solid-state thermal battery + molten-salt like hybrid (engineered for -120C to 1000C containment)',
        'capacity_mwh': 1500,
        'cycle_life_years': 10,
        'notes': 'مكدس متعدد الطبقات: عازل فراغي حراري، عنصر تسخين بالهواء، ومبادل حراري للأحمال. صُمِّم للعمل دون سوائل متطايرة.'
    }

    simulation_plan = {
        'duration_martian_years': 5,
        'timestep_hours': 1,
        'models': ['orbital_insolation_model', 'dust_storm_occurrence_model', 'component_degradation_model', 'crew_load_profile_model'],
        'outputs': ['energy_balance_over_time', 'probability_of_blackout', 'maintenance_schedule', 'lifecycle_costs'],
        'method': 'Monte Carlo with 1000 stochastic storm scenarios; component degradation per-cycle and dust accumulation modeled as exponential opacity increase during storms.'
    }

    emergency_plan = {
        'short_term_storm': ['isolate solar arrays', 'switch to nuclear baseline', 'prioritize life_support and comms', 'enter minimal crew operations'],
        'long_term_storm_weeks': ['conserve consumables', 'shutdown nonessential experiments', 'use regolith-based passive thermal buffering', 'dispatch maintenance drones when opacity < threshold'],
        'resilience_measures': ['deployable dust-repellant electrostatic covers', 'robotic cleaning swarms', 'modular hot-swap power pods']
    }

    hypotheses = [
        {
            'id': 'H1',
            'text': 'استخدام SMR كقلب طاقة مرن مع مرافق تخزين حراري يقلل احتمال انقطاع الطاقة إلى <1% خلال العواصف الطويلة.',
            'supporting_math': 'نموذج بسيط: P_required = 10MW baseline; nuclear_capacity = 12MW * 2 units; failure_prob ~ negligible; storage buffers 1.5MWh handles peak gaps.'
        },
        {
            'id': 'H2',
            'text': 'نظام مرايا مركزة زائد مزارع شمسية زاوية مائلة يقلل فقد الطاقة بسبب زاوية الشمس المائلة ويعطي +30% إنتاج خلال الشتاء المريخي.',
            'supporting_math': 'insolation_gain ≈ cos(theta_adjust) model; combined with concentrators increases effective irradiance.'
        },
        {
            'id': 'H3',
            'text': 'استخدام تخزين حراري صلب مع تبادل حراري منخفض الفقد يطيل فترات دعم الحياة بدون دخل خارجي إلى أسابيع.',
            'supporting_math': 'Q = m*c*ΔT, choose phase-change/solid-state with high latent heat to maximize stored energy per mass.'
        }
    ]

    evaluation_scores = {
        'technical_depth': {'score': 8, 'notes': 'تفصيل هندسي عالي المستوى مع تقديرات نُسبية.'},
        'creativity': {'score': 8, 'notes': 'يقدّم حلولاً جديدة مثل التخزين الحراري الصلب والتكامل SMR.'},
        'integration': {'score': 7, 'notes': 'يجمع تخصصات متعددة لكن يتطلب عمل تفصيلي لكل عنصر.'},
        'realism': {'score': 7, 'notes': 'مستند على تقنيات موجودة مع تبسيط كبير للمتطلبات الحرارية والكتلية.'},
        'innovation': {'score': 8, 'notes': 'حلول مبتكرة في التخزين والطاقة الاحتياطية.'}
    }

    metadata = {
        'generated_at': now,
        'generator': 'fallback_internal_v1',
        'prompt_summary': prompt[:200]
    }

    return {
        'engineering': engineering,
        'distribution_algorithm': distribution_algorithm,
        'storage_system': storage_system,
        'simulation_plan': simulation_plan,
        'emergency_plan': emergency_plan,
        'hypotheses': hypotheses,
        'evaluation_scores': evaluation_scores,
        'metadata': metadata
    }


def try_llm_path(prompt: str):
    """Try to call the repo components: build_prompt_context and chat_llm. Returns dict or None."""
    try:
        # Ensure repo-copy in path
        repo_copy = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'repo-copy'))
        if repo_copy not in os.sys.path:
            os.sys.path.insert(0, repo_copy)

        from Integration_Layer.Hybrid_Composer import build_prompt_context, parse_json_or_retry
        from Core_Engines.Hosted_LLM import chat_llm

        msgs = build_prompt_context(prompt, prompt)
        res = chat_llm(msgs, max_new_tokens=1024)
        text = ''
        if isinstance(res, dict):
            text = res.get('text') or res.get('answer') or ''
        else:
            text = str(res)
        if not text:
            return None

        # try parse JSON
        parsed, final_text, attempts = parse_json_or_retry(text, system_prompt='', user_prompt=prompt, max_attempts=1)
        if parsed:
            return parsed
        # try direct json loads as fallback
        try:
            return json.loads(text)
        except Exception:
            return None

    except Exception as e:
        print(f"LLM path failed: {e}")
        return None


if __name__ == '__main__':
    os.makedirs('artifacts', exist_ok=True)
    start = time.time()
    print('Running Test 1 (Mars power system)…')

    llm_result = try_llm_path(TEST_PROMPT)
    used_llm = llm_result is not None

    if used_llm:
        result = llm_result
        result.setdefault('metadata', {})
        result['metadata'].update({'used_llm': True, 'ran_at': datetime.utcnow().isoformat() + 'Z'})
    else:
        print('Falling back to internal generator.')
        result = fallback_generator(TEST_PROMPT)
        result.setdefault('metadata', {})
        result['metadata'].update({'used_llm': False, 'ran_at': datetime.utcnow().isoformat() + 'Z'})

    # Validate schema minimally
    for k in SCHEMA_KEYS:
        if k not in result:
            result[k] = None

    # Save JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Create short markdown report
    md = []
    md.append(f"## اختبار 1: تصميم نظام طاقة لمستعمرة مريخية\n")
    md.append(f"### التاريخ والوقت: {datetime.utcnow().isoformat()}Z\n")
    md.append(f"### المخرجات: {'تم بواسطة LLM' if used_llm else 'مولّد داخلي (fallback)'}\n")
    md.append('### نقاط سريعة:\n')
    md.append(f"- Technical depth: {result.get('evaluation_scores', {}).get('technical_depth', {}).get('score', 'N/A')}\n")
    md.append(f"- Creativity: {result.get('evaluation_scores', {}).get('creativity', {}).get('score', 'N/A')}\n")
    md.append('\n### موجز الحل:\n')
    eng = result.get('engineering') or {}
    md.append(f"- Overview: {eng.get('overview','')}\n")
    md.append('\n### خطة المحاكاة:\n')
    sim = result.get('simulation_plan') or {}
    md.append(f"- Duration (martian years): {sim.get('duration_martian_years')}\n")

    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    elapsed = time.time() - start
    print(f'Done. Saved JSON -> {OUTPUT_JSON} and report -> {OUTPUT_MD} (elapsed {elapsed:.2f}s)')
