from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter
import traceback
h = HostedLLMAdapter()
try:
    out = h.call_ollama('اختبار صغير', timeout=15)
    print('CALL_OK')
    print(out[:1000])
except Exception as e:
    print('CALL_ERROR')
    traceback.print_exc()
