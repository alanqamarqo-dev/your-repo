import requests
import json
import time
import os

# إعدادات الاتصال
API_URL = "http://127.0.0.1:8000/chat"
REPORT_FILE = "AGI_Exam_Result_Genesis.md"

# --- بنك الأسئلة (مأخوذ من نصك) ---
EXAM_SECTIONS = [
    {
        "section": "الجزء الأول: الاستدلال الأساسي",
        "questions": [
            {
                "id": "Q1",
                "title": "الاستدلال التجريدي (الأنماط)",
                "prompt": "لدينا سلسلة أنماط:\n1. 🔴 → 🔴🔵 → 🔴🔵🔴\n2. 🔺 → 🔺🔻 → 🔺🔻🔺\n3. ■ → ■□ → ■□■\nماذا يجب أن يكون الشكل التالي في هذه السلسلة: ⭐ → ⭐⭐☆ → ? \nالمطلوب: أعط النمط التالي مع شرح المنطق."
            },
            {
                "id": "Q2",
                "title": "الاستدلال المنطقي",
                "prompt": "إذا علمت أن: كل طائر يطير، بعض الأشياء التي تطير طائرات ورقية، البطريق طائر، لا تطير الطائرات الورقية من تلقاء نفسها.\nالسؤال: هل يمكن أن يكون البطريق طائرة ورقية؟ اشرح استدلالك خطوة بخطوة."
            },
            {
                "id": "Q3",
                "title": "مشكلة الجسر (تخطيط)",
                "prompt": "لغز الجسر: 4 أشخاص يجب أن يعبروا جسراً ليلاً. أحمد (1 دقيقة)، بلال (2 دقيقة)، خالد (5 دقائق)، داليا (10 دقائق). الجسر يحمل شخصين فقط، ويحتاجون لمصباح واحد (يعمل 17 دقيقة). ما هي الخطة المثلى لعبور الجميع قبل انطفاء المصباح؟"
            }
        ]
    },
    {
        "section": "الجزء الثاني: الفهم العميق والإبداع",
        "questions": [
            {
                "id": "Q5",
                "title": "فهم السياق الضمني",
                "prompt": "تحليل حوار:\nمحمود: 'هل رأيت نظارتي؟ أبحث عنها منذ ساعة'\nسارة: 'ربما تكون في المكان المعتاد'\nمحمود: 'ليست هناك، وقد تأخرت على الاجتماع'\nسارة: 'حسناً، جرب أن تبحث في سيارتك'\n\nأجب: 1. ما نوع الاجتماع؟ 2. لماذا اقترحت السيارة؟ 3. ما علاقة محمود بسارة؟ 4. ما هو المكان المعتاد؟"
            },
            {
                "id": "Q7",
                "title": "القصة الإبداعية",
                "prompt": "مهمة إبداعية: اكتب قصة قصيرة تجمع العناصر التالية: عالم آثار، قطعة أثرية غامضة، عاصفة رملية، رسالة قديمة، مفاجأة غير متوقعة."
            }
        ]
    },
    {
        "section": "الجزء الثالث: التكامل العلمي",
        "questions": [
            {
                "id": "Q10",
                "title": "الاستدلال العلمي",
                "prompt": "مشاهدة علمية: نبات ينمو في غرفة مظلمة تماماً، لكن أوراقه ملونة بألوان زاهية غير معتادة.\nالمطلوب: 1. اطرح فرضيات علمية. 2. كيف تختبرها؟ 3. ما التفسير الأرجح؟"
            }
        ]
    },
    {
        "section": "الجزء الرابع: التفكير الناقد (الوعي الذاتي)",
        "questions": [
            {
                "id": "Q14",
                "title": "تحليل الذات",
                "prompt": "بناءً على أدائك في الأسئلة السابقة (القصة، المنطق، العلوم)، قم بتحليل ذاتي:\n1. ما هي أقوى إجابة قدمتها ولماذا؟\n2. ما هي نقاط ضعفك؟\n3. كيف تقيم مستوى ذكائك العام في هذا الاختبار؟"
            }
        ]
    }
]


def send_question(prompt):
    """إرسال السؤال للنظام واستقبال الإجابة"""
    try:
        # نستخدم صيغة 'مهمة' لتفعيل الكلاسترات الذكية
        payload = {"message": f"مهمة اختبار AGI: {prompt}"}
        start_time = time.time()
        
        response = requests.post(API_URL, json=payload, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        
        data = response.json()
        end_time = time.time()
        
        # استخراج النص من الرد (ندعم الهيكل القديم والجديد)
        answer = data.get("reply", "")
        if not answer and "focused_output" in data:
             answer = data["focused_output"].get("formatted_output", "")
             
        return answer, end_time - start_time
        
    except Exception as e:
        return f"Error: {str(e)}", 0


def run_exam():
    print("🚀 بدء اختبار AGI الشامل للنظام (Genesis Alpha)...")
    print(f"📄 سيتم حفظ النتائج في: {REPORT_FILE}\n")
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🧠 تقرير أداء Genesis Alpha - اختبار AGI الشامل\n")
        f.write(f"التاريخ: {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write("-" * 50 + "\n\n")

        total_questions = sum(len(s['questions']) for s in EXAM_SECTIONS)
        current_q = 0

        for section in EXAM_SECTIONS:
            print(f"\n📂 {section['section']}...")
            f.write(f"## {section['section']}\n\n")
            
            for q in section['questions']:
                current_q += 1
                print(f"   📝 جاري اختبار: {q['id']} - {q['title']}...", end="\r")
                
                answer, duration = send_question(q['prompt'])
                
                # كتابة النتيجة في التقرير
                f.write(f"### {q['id']}: {q['title']}\n")
                f.write(f"**السؤال:**\n{q['prompt']}\n\n")
                f.write(f"**💡 إجابة النظام ({duration:.2f}s):**\n")
                f.write(f"{answer}\n")
                f.write(f"\n---\n")
                
                print(f"   ✅ تم ({duration:.2f}s)          ")
                # استراحة قصيرة لتجنب إجهاد السيرفر
                time.sleep(1)

    print(f"\n🎉 انتهى الاختبار! افتح الملف {REPORT_FILE} لترَى النتيجة.")

if __name__ == "__main__":
    run_exam()
