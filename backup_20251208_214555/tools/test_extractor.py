import importlib.util
import sys
from pathlib import Path

mod_path = Path.cwd() / 'server.py'
spec = importlib.util.spec_from_file_location('server_mod', str(mod_path))
server_mod = importlib.util.module_from_spec(spec)
sys.modules['server_mod'] = server_mod
spec.loader.exec_module(server_mod)

extract_final_answer = server_mod.extract_final_answer

s = '{"ok": true, "text": "هذا نص منسق", "sources": []}'
print('INPUT:', s)
print('OUTPUT:', extract_final_answer(s))

# also test escaped form
s2 = '\\"{\\"ok\\": true, \\"text\\": \\"هذا نص منسق\\", \\"sources\\": []}\\"'
print('INPUT2:', s2)
print('OUTPUT2:', extract_final_answer(s2))
