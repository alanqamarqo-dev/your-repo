"""Simple check script to verify openai is importable and env vars are present."""
import os

try:
    import openai
    print("openai ok:", getattr(openai, '__version__', 'unknown'))
except Exception as e:
    print("ERR importing openai:", repr(e))

print('AGL_EXTERNAL_INFO_ENABLED =', os.getenv('AGL_EXTERNAL_INFO_ENABLED'))
print('OPENAI_API_KEY present =', bool(os.getenv('OPENAI_API_KEY')))
