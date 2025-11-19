
# ⚠️ emergency isolated script wrapper
import sys, io, traceback, builtins

# minimal blocking of dangerous builtins
# NOTE: do not disable `exec` because this wrapper relies on calling exec()
# instead, disable eval and open. We avoid touching __import__ here because
# we override importlib.__import__ below.
for _name in ['eval', 'open']:
    try:
        setattr(builtins, _name, None)
    except Exception:
        pass

# block some modules by overriding import mechanism for safety (best-effort)
BLOCKED = {'os','sys','subprocess','socket','shutil','pathlib','ssl','ctypes'}
def _blocked_import(name, *args, **kwargs):
    if name.split('.')[0] in BLOCKED:
        raise ImportError("Blocked module: " + name)
    return __import__(name, *args, **kwargs)

import importlib
importlib.__import__ = _blocked_import

out = io.StringIO()
err = io.StringIO()
try:
    _globals = {}
    _locals = {}
    code = r"print('hello-from-emergency')"
    exec(code, _globals, _locals)
    print("EXECUTION_COMPLETED_SUCCESSFULLY")
except Exception as e:
    print("EMERGENCY_ERROR:" + str(e))
    traceback.print_exc()
