
#!/bin/bash
# سكربت تهيئة لنظام MedicalAssistant_v1

echo "🚀 بدء تشغيل النظام الابن..."
echo "النطاق: طب"
echo "المحركات: 2"
echo "النظام الأم: FatherAGI"

# إنشاء البيئة
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# تشغيل النظام
python main.py --mode=child --parent=FatherAGI

echo "✅ النظام الابن يعمل بنجاح!"
