import sys, importlib, pathlib
print("PYTHONPATH head:", sys.path[0])
print("Root exists:", pathlib.Path(r"D:\\AGL").exists())
for m in ["AGL", "AGL.reasoning", "scripts", "scripts.live_training", "AGL.memory"]:
    try:
        importlib.import_module(m)
        print(m, "OK")
    except Exception as e:
        print(m, "ERR:", e)
import sys, traceback
sys.path.append('.')
try:
    import Integration_Layer.Intent_Recognizer as ir
    print('Imported Intent_Recognizer OK. Has attributes:')
    print([a for a in dir(ir) if not a.startswith('_')])
except Exception:
    traceback.print_exc()

try:
    from Integration_Layer.Domain_Router import get_engine
    print('\nImported Domain_Router.get_engine OK')
except Exception:
    traceback.print_exc()

try:
    from Integration_Layer.Intent_Recognizer import route as route_fn # type: ignore
    print('\nRoute function imported OK')
except Exception:
    traceback.print_exc()
