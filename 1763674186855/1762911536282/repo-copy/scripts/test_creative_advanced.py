from Core_Engines.Creative_Innovation import CreativeInnovationEngine
import json

def run():
    eng = CreativeInnovationEngine(seed=7)
    s = eng.design_solutions_for_hard_problems('حل مشكلة التكدس المروري في المدن', attempts=2, decomposition_depth=2, constraints={'budget':10000,'timeline_days':90})
    a = eng.invent_original_artwork('مدينة مستقبلية بلا سيارات', pieces=2, medium='literary')
    m = eng.develop_new_theoretical_models('مرور','تدفق المركبات', n_models=2)
    print('SOLUTIONS:', json.dumps(s, ensure_ascii=False, indent=2))
    print('\nARTIFACTS:', json.dumps(a, ensure_ascii=False, indent=2))
    print('\nMODELS:', json.dumps(m, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    run()
