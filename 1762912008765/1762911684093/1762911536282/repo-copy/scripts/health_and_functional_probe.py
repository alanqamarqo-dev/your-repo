import sys, json, traceback
sys.path.append('.')
from Integration_Layer.Domain_Router import get_engine
out = {"engines":{}}
keys=['nlp','knowledge','creative','strategic','meta','visual','social']
health_candidates = ['healthcheck','health_check','health','ping','status','is_ready','isReady']
for k in keys:
    try:
        e = get_engine(k)
        if e is None:
            out['engines'][k] = {'ok':False,'error':'instance_is_None'}
            continue
        methods = [m for m in dir(e) if not m.startswith('_')]
        health_result = None
        for c in health_candidates:
            if hasattr(e, c):
                try:
                    fn = getattr(e, c)
                    r = fn()
                    health_result = {'method':c, 'result': r}
                except Exception as ex:
                    health_result = {'method':c, 'error': str(ex)}
                break
        out['engines'][k] = {'ok':True, 'type': type(e).__name__, 'methods_preview': methods[:60], 'health_probe': health_result}
    except Exception as ex:
        out['engines'][k] = {'ok':False, 'error': str(ex), 'trace': traceback.format_exc()}

# Functional probes
func = {'nlp': None, 'knowledge': None}
try:
    nlp = get_engine('nlp')
    if nlp is None:
        func['nlp'] = {'ok':False,'error':'nlp_instance_none'} # type: ignore
    else:
        # try common reply methods
        tried = {}
        for m in ('respond','helpful','reply','generate_reply','multi_turn_chat'):
            if hasattr(nlp, m):
                try:
                    if m == 'multi_turn_chat':
                        r = getattr(nlp,m)(history=[], user_text='سلام')
                    else:
                        r = getattr(nlp,m)('سلام')
                    tried[m] = {'ok':True, 'result': r}
                except Exception as e:
                    tried[m] = {'ok':False, 'error': str(e)}
        func['nlp'] = {'ok':True, 'tried': tried} # type: ignore
except Exception as e:
    func['nlp'] = {'ok':False, 'error': str(e), 'trace': traceback.format_exc()} # type: ignore

try:
    gk = get_engine('knowledge')
    if gk is None:
        func['knowledge'] = {'ok':False,'error':'knowledge_instance_none'} # type: ignore
    else:
        try:
            # call ask with a benign query; may call external provider
            ans = None
            try:
                ans = gk.ask('ما هي أسباب ازدحام المرور؟', context=['probe'])
            except TypeError:
                # maybe signature is ask(question)
                ans = gk.ask('ما هي أسباب ازدحام المرور؟')
            func['knowledge'] = {'ok':True, 'answer_preview': ans} # type: ignore
        except Exception as e:
            func['knowledge'] = {'ok':False, 'error': str(e), 'trace': traceback.format_exc()} # type: ignore
except Exception as e:
    func['knowledge'] = {'ok':False, 'error': str(e), 'trace': traceback.format_exc()} # type: ignore

out['functional'] = func
# write to artifacts
import os
os.makedirs('artifacts', exist_ok=True)
with open('artifacts/health_functional_probe.json','w',encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print('Wrote artifacts/health_functional_probe.json')
print(json.dumps({'status':'done','engines': list(out['engines'].keys())}, ensure_ascii=False))
