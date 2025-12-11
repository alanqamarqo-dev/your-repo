import sys
import json
import traceback

sys.path.insert(0, r'D:\AGL\repo-copy')

from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine


def main():
    cie = CognitiveIntegrationEngine()
    cie.connect_engines()
    prob = {'title': 'ما هي أعراض الإنفلونزا؟', 'question': 'ما هي أعراض الإنفلونزا؟'}
    print('ADAPTERS:', [a.name for a in cie.adapters])
    for a in cie.adapters:
        try:
            r = a.infer(prob, context=[], timeout_s=3.0)
            print('\n--', a.name, '->', r.get('score'), r.get('content'))
        except Exception as e:
            print('ERR', a.name, e)
            traceback.print_exc()


if __name__ == '__main__':
    main()
