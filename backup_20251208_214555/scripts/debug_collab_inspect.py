#!/usr/bin/env python3
"""Debug helper: run one story QA query and print the raw winner and top proposals.

Usage: python scripts/debug_collab_inspect.py
"""
import sys, os, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
except Exception as e:
    print('Import error:', e)
    raise

AR_STORY = (
    "وجد علي قطة صغيرة خلف بيته. كانت القطة خجولة وجائعة. "
    "أعطى علي القطة بعض الحليب واكتسب ثقتها ببطء. خلال الأيام، أصبحت القطة تلاحق علي في كل مكان، "
    "وصارا صديقين. في يوم من الأيام أنقذت القطة علي من سقوط صغير بصياحها وجلب المساعدة."
)

def main():
    cie = CognitiveIntegrationEngine()
    try:
        cie.connect_engines()
    except Exception:
        pass

    task1 = {
        'title': 'story_qa_debug_signals',
        'signals': [
            {'kind': 'story', 'text': AR_STORY},
            {'kind': 'question', 'text': 'من هو بطل القصة؟'}
        ],
        'lang': 'ar'
    }

    task2 = {
        'title': 'story_qa_debug_flat',
        'story': AR_STORY,
        'question': 'من هو بطل القصة؟',
        'lang': 'ar',
        'mode': 'short_answer',
    }

    print('Calling collaborative_solve with signals payload (analysis,reason,language)')
    res1 = cie.collaborative_solve(task1, domains_needed=("analysis","reason","language"))
    print('\n=== WINNER RAW (signals payload) ===')
    print(json.dumps(res1.get('winner'), ensure_ascii=False, indent=2))
    print('\n=== TOP RAW (signals payload) ===')
    print(json.dumps(res1.get('top'), ensure_ascii=False, indent=2))

    print('\n--- now calling with flat payload keys (story,question) ---')
    res2 = cie.collaborative_solve(task2, domains_needed=("analysis","reason","language"))
    print('\n=== WINNER RAW (flat payload) ===')
    print(json.dumps(res2.get('winner'), ensure_ascii=False, indent=2))
    print('\n=== TOP RAW (flat payload) ===')
    print(json.dumps(res2.get('top'), ensure_ascii=False, indent=2))

    print('\n=== FULL RESULT KEYS for last call ===')
    print(list(res2.keys()))


if __name__ == '__main__':
    main()
