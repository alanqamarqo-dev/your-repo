from Integration_Layer.Hybrid_Composer import build_prompt_context
from Core_Engines.Hosted_LLM import chat_llm
import os

story = """كان أحمد يلعب في الحديقة. رأى قطة جميلة تلاحق فراشة.
ثم سمع صوت بكاء طفل صغير. ترك القطة وركض لمساعدة الطفل."""
questions = "1) لماذا ترك أحمد القطة؟\n2) ما هي المشاعر المحتملة لأحمد في كل موقف؟\n3) كيف كان يمكن أن يتصرف بشكل مختلف؟"

messages = build_prompt_context(story, questions)
print('=== MESSAGES TO MODEL ===')
for m in messages:
    print(f"[{m['role']}] {m['content']}\n")

resp = chat_llm(messages, max_new_tokens=512)
print('=== RAW RESP ===')
print(resp)
print('=== TEXT ===')
print(resp.get('text') if isinstance(resp, dict) else str(resp))
