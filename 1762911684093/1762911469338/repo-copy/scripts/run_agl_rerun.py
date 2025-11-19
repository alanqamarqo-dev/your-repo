import os
import sys
import json

# Ensure project root on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core_Engines.Ollama_KnowledgeEngine import OllamaKnowledgeEngine

INPUT_PATH = os.path.join('reports', 'agl_test_input.txt')
OUTPUT_PATH = os.path.join('reports', 'agl_response_rerun.json')

# Read the test prompt
with open(INPUT_PATH, 'r', encoding='utf-8') as fh:
    test_prompt = fh.read()

# System-level instruction asking the engine to behave as an integrated AGL system
system_instruction = (
    "أنت الآن منظومة AGL المتكاملة — تتصرف كوحدة واحدة تتألف من مكونات: التخطيط، التنفيذ، التعلم، التحقق، والتقييم. "
    "كُن واضحًا جدًا: أجب بالعربية فقط. لا تستخدم لغات أخرى.\n"
    "لِكل جزء (1 إلى 5) قدم: ملخصًا واضحًا، خطوات عملية قابلة للتنفيذ، أمثلة رقمية/تقديرات حيث ينطبق، ومخاطر/افتراضات.\n"
    "بعد إجابات الأجزاء، قِم بتقييم ذاتي رقمي لكل معيار من المعايير التالية: \n"
    "- الفهم المتكامل (25%)\n- العمق والتفاصيل (25%)\n- الإبداع والمرونة (20%)\n- التخطيط المنطقي (20%)\n- الفهم العاطفي والاجتماعي (10%)\n"
    "أعطِ لكل معيار درجة من 0 إلى 100 مع شرح موجز للأسباب، ثم احسب النتيجة النهائية الموزونة (0-100).\n"
    "أجب بصيغة تقرير واضح ومهيكل، ولا تدرج أي نص بلغة أخرى. النهاية." 
)

# Create engine
eng = OllamaKnowledgeEngine()

# Split the input into parts to avoid very long single-prompt generation timeouts.
chunks = test_prompt.split('\n\nالجزء ')
# The first chunk may contain the title; subsequent chunks begin with e.g. '١: ...'
parts = []
if len(chunks) > 1:
    for c in chunks[1:6]:
        parts.append('الجزء ' + c.strip())
else:
    # Fallback: treat entire test as single part
    parts = [test_prompt]

results = {"parts": [], "evaluation": None}
for i, p in enumerate(parts, start=1):
    print(f"Asking part {i} (length {len(p)} chars)")
    r = eng.ask(p, system_prompt=system_instruction)
    results["parts"].append({"part": i, "prompt": p, "response": r})

# After collecting parts, ask the engine to evaluate the combined responses and score itself
evaluation_prompt = (
    "الآن لديك الإجابات للأجزاء 1-5. قدم تقييمًا ذاتيًا رقميًا لكل معيار (الفهم المتكامل، العمق، الإبداع، التخطيط، الفهم العاطفي)، "
    "مع شرح موجز لكل درجة وحساب النتيجة النهائية الموزونة (0-100). اجب بالعربية فقط."
)
combined_context = '\n\n'.join([json.dumps(p["response"], ensure_ascii=False) for p in results["parts"]])
eval_resp = eng.ask(evaluation_prompt + "\n\nسياق: \n" + combined_context, system_prompt=system_instruction)
results["evaluation"] = eval_resp

# Save response
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, 'w', encoding='utf-8') as fh:
    json.dump(results, fh, ensure_ascii=False, indent=2)

print(f"Wrote rerun response to {OUTPUT_PATH}")
