import sys
import os

# ensure repo root on path
sys.path.insert(0, os.path.abspath(os.getcwd()))

from Core_Memory.bridge_singleton import get_bridge

def teach_system():
    print("🚀 جاري تلقين النظام المعلومات الطبية...")

    # اقرأ الملف الطبي إن وجد
    src_path = os.path.join(os.getcwd(), 'medical_source.txt')
    if os.path.exists(src_path):
        with open(src_path, 'r', encoding='utf-8') as f:
            knowledge = f.read().strip()
    else:
        knowledge = (
            "الإنفلونزا (Influenza) عدوى فيروسية. أعراضها: حمى شديدة مفاجئة، آلام عضلات، "
            "سعال جاف، صداع، إرهاق. تختلف عن الزكام بحدة الأعراض."
        )

    bridge = get_bridge()
    if bridge is None:
        print("❌ لم أستطع الحصول على جسر الذاكرة (ConsciousBridge). تأكد من وجود Core_Memory.")
        return

    # خزن كحقل نصي في LTM باستخدام API المتاح (put)
    try:
        ev_id = bridge.put('medical_fact', {'text': knowledge, 'source': 'manual_entry'}, to='ltm')
        print(f"✅ تم إدخال المعلومة في الذاكرة (id={ev_id})")
    except Exception as e:
        print("❌ فشل التخزين في LTM:", e)
        return

    # صدّر لقاعدة البيانات الافتراضية التي يستخدمها bootstrap (data/memory.sqlite)
    try:
        db_path = os.path.join(os.getcwd(), 'data', 'memory.sqlite')
        written = bridge.export_ltm_to_db(db_path=db_path)
        print(f"✅ تم تصدير LTM إلى {db_path} ({written} صفوف)")
    except Exception as e:
        print("⚠️ تحذير: لم أتمكن من تصدير LTM إلى بيانات القرص:", e)

if __name__ == '__main__':
    teach_system()
