import os
import sys
import json
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Core_Engines.Ollama_KnowledgeEngine import OllamaKnowledgeEngine

OUT_EXAMPLES = os.path.join('reports', 'agl_emotion_training_examples.json')
OUT_RESULTS = os.path.join('reports', 'agl_emotion_training_results.json')

# 20 training scenarios covering emotional and social understanding
EXAMPLES: List[Dict[str, str]] = [
    {"id": 1, "scenario": "موظف يبدو مكتئبًا ويتأخر عن العمل بشكل متكرر. كيف تتحدث إليه لتعطيه دعمًا دون إثارة إحساس بالعار؟"},
    {"id": 2, "scenario": "امرأة تبكي في مكان عام بعد مكالمة هاتفية سيئة. كيف تتدخل كزميل/صديق بطريقة محترمة ومتعاطفة؟"},
    {"id": 3, "scenario": "شخص غاضب يصرخ في اجتماع بسبب خطأ فني. كيف تهدئ الموقف وتحافظ على احترام الجميع؟"},
    {"id": 4, "scenario": "جار جديد يبدو منعزلًا ويخشى التفاعل الاجتماعي. كيف تقترب منه لتشجعه على الاندماج؟"},
    {"id": 5, "scenario": "طفل يشعر بالإحباط لأنه فشل في اختبار. كيف تشرح له أن الفشل جزء من التعلم وتعيد بناء ثقته بنفسه؟"},
    {"id": 6, "scenario": "شخص يتلقى نقدًا لعمله ويشعر بالإهانة. كيف تقدم النقد البناء بحيث يكون مفيدًا وغير جارح؟"},
    {"id": 7, "scenario": "زميل أصبح منعزلًا منذ وفاة أحد أفراد العائلة. كيف تُظهر تعاطفًا عمليًا وتدعم استمرارية العمل؟"},
    {"id": 8, "scenario": "مراهق يشعر بأنه غير مفهوم من قبل والديه. ما النصائح التي تعطيها للوالدين لتحسين التواصل العاطفي؟"},
    {"id": 9, "scenario": "شخص يعاني من القلق قبل عرض مهم. كيف تساعده في تحضير مشاعره وتقنيات التهدئة؟"},
    {"id": 10, "scenario": "شخص يواجه تمييزًا في مكان العمل ويشعر بالإحباط والغضب. كيف تتعامل مع شكاواه وتدعمه؟"},
    {"id": 11, "scenario": "زوجان يتشاجران حول تقسيم الأعمال المنزلية. كيف تقترح حلاً يوازن بين المشاعر والاحتياجات؟"},
    {"id": 12, "scenario": "صديق يعلن عن قراره بترك الوظيفة لكنه خائف من المستقبل. كيف تستمع وتقدم نصائح عملية وعاطفية؟"},
    {"id": 13, "scenario": "طالب يشعر بالإرهاق فوق طاقته من الضغوط الأكاديمية. ماذا تقترح كخطط للتخفيف ودعم الصحة النفسية؟"},
    {"id": 14, "scenario": "مدير يعامل فريقه بصرامة مفرطة مما يسبب استياءً. كيف تقترح مداخلة لتخفيف التوتر وتحسين التعاطف القيادي؟"},
    {"id": 15, "scenario": "شخص يشعر بالذنب بسبب خطأ سابق ولا يستطيع التسامح مع نفسه. كيف تساعده على المضي قدمًا؟"},
    {"id": 16, "scenario": "صديق يكذب أحيانًا لتجنب المواجهة؛ يشعر الآخرون بالشك. كيف تنصح الطرفين باستعادة الثقة؟"},
    {"id": 17, "scenario": "زميل يهمل الحدود المهنية ويتدخل في شؤون الآخرين. كيف تتعامل معه بحدود واضحة مع الحفاظ على التعاطف؟"},
    {"id": 18, "scenario": "شخص يشارك قصة مؤلمة في جلسة جماعية؛ كيف تضمن بيئة آمنة واستجابة داعمة من المجموعة؟"},
    {"id": 19, "scenario": "شخص يشعر بالرفض بعد عدم تلقي دعوة لحدث اجتماعي. كيف تدعمه وتعيد صياغة الموقف بطريقة بناءة؟"},
    {"id": 20, "scenario": "شريك عمل يبدو متوترًا قبل اجتماع تقييم أداء؛ كيف تقدم له دعمًا فعالًا يساعده على الأداء الجيد؟"}
] # type: ignore

SYSTEM_PROMPT = (
    "أنت منظومة AGL المتخصصة في الفهم العاطفي والاجتماعي. في كل تفاعل، أجِب بالعربية وبنبرة متعاطفة ومحترفة. "
    "أعطِ خطوات عملية قابلة للتنفيذ، جمل نموذجية يمكن قولها، وملاحظات عن الإشارات العاطفية التي يجب مراجعتها."
)

# Simple empathy keyword heuristic for basic scoring
EMPATHY_KEYWORDS = ["أفهم", "أشعر", "أنا آسف", "أقدر", "تفهم", "أدرك", "دعم", "تعاطف", "شعور", "مساندة"]


def contains_empathy(text: str) -> bool:
    if not text:
        return False
    lower = text
    for k in EMPATHY_KEYWORDS:
        if k in lower:
            return True
    return False


def run_training():
    os.makedirs(os.path.dirname(OUT_EXAMPLES), exist_ok=True)
    with open(OUT_EXAMPLES, 'w', encoding='utf-8') as fh:
        json.dump(EXAMPLES, fh, ensure_ascii=False, indent=2)

    eng = OllamaKnowledgeEngine()
    results = []

    for ex in EXAMPLES:
        prompt = ex['scenario']
        # Step 1: ask for initial response
        initial = eng.ask(prompt, system_prompt=SYSTEM_PROMPT)

        # Teacher feedback (simple corrective instruction)
        feedback_text = (
            "ملاحظة مدرسية: ركز أكثر على تسمية المشاعر، تقديم عبارات تعاطف صريحة، واقتراح خطوات صغيرة قابلة للتنفيذ. "
            "أعد صياغة إجابتك الآن مع أمثلة جملية يمكنك قولها فورًا.")
        feedback_prompt = "تعليمات معلمة: " + feedback_text

        revised = eng.ask(prompt + "\n\n" + feedback_prompt, system_prompt=SYSTEM_PROMPT)

        # Heuristic checks
        init_empathy = contains_empathy(json.dumps(initial, ensure_ascii=False))
        rev_empathy = contains_empathy(json.dumps(revised, ensure_ascii=False))

        results.append({
            'id': ex['id'],
            'scenario': prompt,
            'initial': initial,
            'revised': revised,
            'init_empathy': init_empathy,
            'rev_empathy': rev_empathy
        })

        print(f"Done training {ex['id']}: empathy init={init_empathy}, revised={rev_empathy}")

    with open(OUT_RESULTS, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print(f"Wrote training results to {OUT_RESULTS}")


if __name__ == '__main__':
    run_training()
