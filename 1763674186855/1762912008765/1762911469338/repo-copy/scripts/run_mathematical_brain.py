import sys
sys.path.insert(0, r'D:\AGL\repo-copy')

from tests.helpers.engine_ask import ask_engine
import json

question = '''طبق مفهوم الإنتروبيا من الفيزياء على المجالات التالية مع شرح رياضي دقيق:

1) علم النفس: كيف يمكن قياس اضطراب النظام النفسي باستخدام الإنتروبيا؟
2) اللغات: كيف تطورت تعقيدات اللغة من منظور إنتروبي؟
3) المدن الذكية: كيف نحسب كفاءة توزيع الموارد في المدينة باستخدام الإنتروبيا؟

قدم معادلات رياضية ومقاييس قابلة للقياس وتطبيقات عملية.'''

result = ask_engine('Mathematical_Brain', question)
print('=== نتيجة Mathematical_Brain (الأقوى علمياً) ===')
# print structured if available
try:
    print(json.dumps(result, ensure_ascii=False, indent=2))
except Exception:
    print(result)
