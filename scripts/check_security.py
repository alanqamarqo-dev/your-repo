# احفظه باسم check_security.py وشغله
import sys
import os

# إضافة المسارات المحتملة
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))
sys.path.append(os.path.join(os.getcwd(), 'repo-copy', 'Safety_Systems'))
sys.path.append(os.path.join(os.getcwd(), 'repo-copy', 'Safety_Control'))

print("--- inspecting Safety ---")

try:
    from Safety_Control import Dialogue_Safety
    print(f"✅ Dialogue_Safety found. Methods: {[x for x in dir(Dialogue_Safety) if not x.startswith('_')]}")
except ImportError as e:
    print(f"❌ Dialogue_Safety NOT found. Error: {e}")

try:
    from Safety_Systems import EmergencyDoctor
    print(f"✅ EmergencyDoctor found.")
    print(f"   Class: EmergencyDoctor.EmergencyDoctor")
    doc_class = EmergencyDoctor.EmergencyDoctor
    methods = [x for x in dir(doc_class) if not x.startswith('_') and callable(getattr(doc_class, x, None))]
    print(f"   Methods: {methods}")
except ImportError as e:
    print(f"❌ EmergencyDoctor NOT found. Error: {e}")
