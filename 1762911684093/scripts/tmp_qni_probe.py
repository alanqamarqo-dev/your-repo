import sys
from pathlib import Path
# Ensure repo root is on sys.path so imports like Integration_Layer work when
# running this script directly from scripts/ (fixes ModuleNotFoundError).
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from Integration_Layer.integration_registry import registry
import Core_Engines as CE
CE.bootstrap_register_all_engines(registry, allow_optional=True)
q = registry.get('Quantum_Neural_Core')
prompts = [
    "كلمة 'ضوء' تحمل معاني فيزيائية وفلسفية وفنية. حلل جميع الأبعاد مع الاحتفاظ بتراكبها",
    "كيف يمكن أن يكون المال 'قيمة' و'طاقة' و'علاقة اجتماعية' في نفس الوقت؟",
]
for p in prompts:
    try:
        res = q.process_task({'intent':'eval','text':p}) # type: ignore
    except Exception as e:
        print('process_task raised', e)
        res = {'ok': False, 'error': str(e)}
    print('PROMPT:', p[:60])
    print('RES KEYS:', list(res.keys()))
    print('OK:', res.get('ok'))
    txt = res.get('text') or res.get('reply_text') or ''
    print('TEXT LEN:', len(txt))
    print('SUMMARY:', txt[:500])
    print('---')
