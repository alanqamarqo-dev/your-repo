import inspect
# استيراد ملفاتك الحالية
from Core_Engines import Perception_Context, Causal_Graph, AdvancedMetaReasoner
from Core_Memory import Conscious_Bridge


def print_methods(module, name):
    print(f"\n--- فحص ملف: {name} ---")
    # نحاول العثور على الكلاسات داخل الملف
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if inspect.isclass(attribute):
            print(f"Class Found: {attribute_name}")
            # فحص الدوال داخل الكلاس
            for method_name in dir(attribute):
                if not method_name.startswith("__"): # تجاهل الدوال الداخلية
                    print(f"   -> Method: {method_name}()")

# تشغيل الفحص
try:
    print_methods(Perception_Context, "Perception_Context")
    print_methods(Conscious_Bridge, "Conscious_Bridge")
    print_methods(Causal_Graph, "Causal_Graph")
    print_methods(AdvancedMetaReasoner, "AdvancedMetaReasoner")
except Exception as e:
    print(f"Error inspecting: {e}")
