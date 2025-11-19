# -- coding: utf-8 --
import json
import os
import sys
sys.path.append(os.getcwd())

from Integration_Layer.Conversation_Manager import auto_route_and_respond, create_session

PROBES = [
    ("probe_1", "ما هو قانون نيوتن؟"),
    ("probe_i18n", "ترجم hello الى ar"),
    ("probe_ci", "أعطني فكرة لميزة مبتكرة"),
    ("probe_vs", "صوّر تخطيط غرفة 3D بسيط"),
]

print("Running probes using Conversation_Manager.auto_route_and_respond()...\n")
for sid, text in PROBES:
    print(f"--- Probe session={sid} text={text}")
    create_session(sid)
    out = auto_route_and_respond(sid, text)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    # print session file
    path = os.path.join('artifacts', 'chat_sessions', f'session_{sid}.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            s = json.load(f)
        print(f"session file ({path}) history last item:")
        if s.get('history'):
            print(json.dumps(s['history'][-1], ensure_ascii=False, indent=2))
        else:
            print("(no history)")
    except Exception as e:
        print(f"Could not read session file: {e}")
    print('\n')

# health check via Domain_Router.get_engine
print('Engine availability check:')
try:
    from Integration_Layer.Domain_Router import get_engine
    keys = ["nlp", "knowledge", "creative", "strategic", "meta", "visual", "social"]
    engines = {}
    for k in keys:
        try:
            eng = get_engine(k)
            engines[k] = 'ok' if eng is not None else 'missing'
        except Exception as e:
            engines[k] = f'missing: {e}'
    print(json.dumps(engines, ensure_ascii=False, indent=2))
except Exception as e:
    print('Domain_Router.get_engine not available:', e)
