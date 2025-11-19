import sys, os
sys.path.append(os.getcwd())
from Integration_Layer import Domain_Router

cases = [
    "لماذا السماء زرقاء؟",
    "ما هو عاصمة فرنسا؟",
    "احسب 12 * 34",
    "ما هي سرعة الضوء؟",
    "كيف اثبت Python على Windows؟",
]
for c in cases:
    try:
        r = Domain_Router.route(c)
        print('INPUT:', c)
        print('OUTPUT:', r)
        print('-' * 40)
    except Exception as e:
        print('EXCEPTION for', c, e)
