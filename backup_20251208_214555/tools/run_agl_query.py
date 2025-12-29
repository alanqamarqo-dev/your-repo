import sys
import json

sys.path.insert(0, r'D:\AGL\repo-copy')

from Self_Improvement.Knowledge_Graph import agl_pipeline


def main():
    q = 'ما هي أعراض الإنفلونزا؟'
    try:
        res = agl_pipeline(q)
        print('\n--- agl_pipeline result ---')
        print(json.dumps(res, ensure_ascii=False, indent=2))
    except Exception as e:
        print('agl_pipeline error:', e)


if __name__ == '__main__':
    main()
