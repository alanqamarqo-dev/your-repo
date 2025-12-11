"""
اختبار سريع لمحرك التفكير الكمومي بعد الإصلاح
"""
import asyncio
import sys
import os

# إضافة المسارات
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo-copy"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo-copy", "dynamic_modules"))

try:
    from mission_control_enhanced import process_with_unified_agi
except ImportError:
    # Fallback: try to load the module file directly from repo-copy
    import importlib.util
    module_path = os.path.join(os.path.dirname(__file__), "repo-copy", "mission_control_enhanced.py")
    if os.path.isfile(module_path):
        spec = importlib.util.spec_from_file_location("mission_control_enhanced", module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            process_with_unified_agi = getattr(module, "process_with_unified_agi")
        else:
            raise ImportError(f"Cannot load spec for {module_path}")
    else:
        raise

async def test_quantum_fix():
    """اختبار السؤال الذي فشل سابقاً"""
    
    print("=" * 80)
    print("🔬 اختبار إصلاح محرك التفكير الكمومي")
    print("=" * 80)
    
    question = "كيف تؤثر الاحتمالات المتعددة على قراراتنا؟"
    print(f"\n❓ السؤال: {question}\n")
    
    try:
        result = await process_with_unified_agi(question)
        
        print(f"\n📊 النتائج:")
        print(f"   ⚛️ Quantum Applied: {result.get('quantum_applied', False)}")
        print(f"   🧠 Reasoning Type: {result.get('reasoning_type', 'unknown')}")
        print(f"   📝 Response Length: {len(result.get('final_response', ''))} chars")
        
        if result.get('quantum_applied'):
            print(f"   ✅ التفكير الكمومي نشط!")
            if result.get('quantum_result'):
                qr = result['quantum_result']
                print(f"   🌌 Quantum Engine: {qr.get('engine', 'N/A')}")
                print(f"   📊 Genesis Phase: {qr.get('genesis_phase', 'N/A')}")
        else:
            print(f"   ⚠️ التفكير الكمومي لم يُفعّل")
            
        # عرض جزء من الإجابة
        response = result.get('final_response', '')
        if response:
            preview = response[:300] + "..." if len(response) > 300 else response
            print(f"\n💬 معاينة الإجابة:\n{preview}")
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ اكتمل الاختبار")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_quantum_fix())
