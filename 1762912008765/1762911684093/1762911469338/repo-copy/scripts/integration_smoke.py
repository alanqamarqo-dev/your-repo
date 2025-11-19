import sys, json
sys.path.append('.')
from Integration_Layer.Domain_Router import get_engine
from Integration_Layer.Action_Router import route
from Integration_Layer.Intent_Recognizer import recognize_intent
from AGL_UI.Language_Interface import parse_entities

keys=['nlp','knowledge','creative','strategic','meta','visual','social']
out={}
for k in keys:
    try:
        e=get_engine(k)
        out[k]={'ok':True,'type':type(e).__name__ if e is not None else None,'has_methods':[m for m in ['respond','ask','ideate','plan','few_shot_learn','describe_or_generate','empathetic_reply'] if hasattr(e,m)]}
    except Exception as ex:
        out[k]={'ok':False,'error':str(ex)}

# sample Arabic question to exercise route()
sample = "ما هي أسباب ازدحام المرور في المدينة وكيف يمكن تخفيفها؟"
try:
    intent = recognize_intent(sample)
    kv = parse_entities(sample)
    routed = route(intent.get('task'), intent.get('law'), kv) # type: ignore
except Exception as e:
    routed = {'error': str(e)}

print(json.dumps({'engines': out, 'route_result': routed}, indent=2, ensure_ascii=False))