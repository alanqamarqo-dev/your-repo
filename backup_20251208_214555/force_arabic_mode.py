import os

target_file = "dynamic_modules/mission_control_enhanced.py"
print("🔧 جاري تثبيت 'مود اللغة العربية الصارم' في غرفة التحكم...")

try:
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    # سنقوم بالبحث عن مكان بناء البرومبت (Prompt Construction) وتعديله
    # نبحث عن السطر الذي يرسل الطلب للـ LLM
    
    # 1. تعريف التعليمات الصارمة
    arabic_instruction = ' \n"IMPORTANT: You must respond ONLY in ARABIC language. Do not summarize; generate the full content creatively." '

    # نقوم بحقن هذه التعليمات في دالة quick_start_enhanced أو run_enhanced_mission
    # سنبحث عن المتغير الذي يحمل الـ prompt ونضيف عليه التعليمات
    
    if 'prompt=prompt' in content:
        # هذا تعديل ذكي يستبدل تمرير البرومبت بتمرير البرومبت + التعليمات
        new_content = content.replace(
            'prompt=prompt', 
            f'prompt=prompt + {arabic_instruction}'
        )
        
        # حماية من التكرار (في حال شغلت السكربت مرتين)
        if arabic_instruction not in content:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("✅ تم حقن كود اللغة العربية بنجاح!")
            print("الآن سيفهم النظام أنك تريد قصة كاملة وبالعربية.")
        else:
            print("ℹ️ النظام معدل مسبقاً للغة العربية.")
            
    else:
        print("⚠️ لم أتمكن من تحديد مكان الحقن بدقة، يرجى التحقق من الكود يدوياً.")

except FileNotFoundError:
    print(f"❌ الملف {target_file} غير موجود!")
