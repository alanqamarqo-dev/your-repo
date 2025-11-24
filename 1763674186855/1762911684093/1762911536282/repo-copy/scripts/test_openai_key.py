"""
Small helper to check whether OPENAI_API_KEY is configured and to exercise
Core_Engines.OpenAI_KnowledgeEngine.ask() if available.

This script prints only non-secret information: presence/absence of the key,
and the result or the exception message returned by the engine.
"""
import os
import json
import traceback
import sys

# Ensure repo root is on sys.path so imports like Core_Engines.* work when
# running the script from the scripts/ folder or from CI.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

KEY = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY'.upper())
print('OPENAI_API_KEY_PRESENT:', bool(KEY))

if not KEY:
    print('No OPENAI_API_KEY found in environment. To enable real OpenAI KB fallback, set the variable in PowerShell:')
    print("$env:OPENAI_API_KEY = 'sk-...'")
    print('Then re-run this script. (Do NOT paste secrets into chat.)')
    raise SystemExit(0)

# If key present, try to import the optional engine adapter and call .ask()
try:
    from Core_Engines.OpenAI_KnowledgeEngine import OpenAIKnowledgeEngine
except Exception as e:
    print('OpenAIKnowledgeEngine import failed:', str(e))
    traceback.print_exc()
    raise SystemExit(1)

try:
    oa = OpenAIKnowledgeEngine()
    q = 'ما هي سرعة الضوء؟'
    print('Calling OpenAIKnowledgeEngine.ask(...) with a test prompt...')
    resp = oa.ask(q, context=[])  # adapt signature if engine differs
    print('RESPONSE_TYPE:', type(resp))
    try:
        print('RESPONSE_PRETTY:')
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    except Exception:
        print('Raw response:', resp)
except Exception as e:
    print('Call to OpenAIKnowledgeEngine.ask failed with exception:')
    traceback.print_exc()
    raise SystemExit(2)
