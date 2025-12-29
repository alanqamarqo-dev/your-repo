"""
اختبار المحركات الثلاثة الجديدة المُصلحة
Test the 3 newly fixed engines for real output generation
"""
import asyncio
import sys
import os

# Add repo to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Scientific_Systems.Hardware_Simulator import HardwareSimulator
from Engineering_Engines.IoT_Protocol_Designer import IoTProtocolDesigner
from Self_Improvement.Self_Monitoring_System import SelfMonitoringSystem

def print_section(title):
    print("\n" + "="*70)
    print(f"🧪 {title}")
    print("="*70)

def test_hardware_simulator():
    """اختبار محاكي العتاد"""
    print_section("اختبار HardwareSimulator - محاكي العتاد")
    
    simulator = HardwareSimulator()
    
    # Test 1: Basic simulation
    print("\n📊 الاختبار 1: محاكاة بسيطة")
    result1 = simulator.simulate(model="sensor_network", steps=10)
    print(f"   النتيجة: {result1}")
    print(f"   ✅ الحالة: {result1.get('status')}")
    print(f"   📈 عدد الخطوات: {result1.get('steps')}")
    print(f"   🔧 النموذج: {result1.get('model')}")
    
    # Test 2: Advanced simulation
    print("\n📊 الاختبار 2: محاكاة متقدمة")
    config = {
        'device_type': 'temperature_sensor',
        'sample_rate': 1000,
        'duration': 60
    }
    result2 = simulator.run_simulation(config)
    print(f"   النتيجة: {result2}")
    print(f"   ✅ اكتمال المحاكاة: {result2.get('simulation_complete')}")
    print(f"   📋 الإعدادات: {result2.get('config')}")
    print(f"   📊 النتائج: {result2.get('results')}")
    
    # Validation
    has_output1 = result1 and len(str(result1)) > 20
    has_output2 = result2 and result2.get('simulation_complete') == True
    
    print(f"\n{'✅' if has_output1 and has_output2 else '❌'} التقييم النهائي:")
    print(f"   - إجابات حقيقية: {'نعم ✅' if has_output1 and has_output2 else 'لا ❌'}")
    print(f"   - طول الإجابة 1: {len(str(result1))} حرف")
    print(f"   - طول الإجابة 2: {len(str(result2))} حرف")
    
    return has_output1 and has_output2

def test_iot_protocol_designer():
    """اختبار مصمم بروتوكولات IoT"""
    print_section("اختبار IoTProtocolDesigner - مصمم بروتوكولات IoT")
    
    designer = IoTProtocolDesigner()
    
    # Test 1: Basic protocol creation
    print("\n📊 الاختبار 1: إنشاء بروتوكول بسيط")
    requirements1 = {
        'device_count': 100,
        'data_rate': 'high',
        'security': 'required'
    }
    result1 = designer.create(requirements1)
    print(f"   النتيجة: {result1}")
    print(f"   🔧 نوع البروتوكول: {result1.get('iot_protocol')}")
    print(f"   📋 المتطلبات: {result1.get('requirements')}")
    print(f"   📌 الإصدار: {result1.get('version')}")
    
    # Test 2: Advanced protocol design
    print("\n📊 الاختبار 2: تصميم بروتوكول متقدم")
    spec = {
        'topology': 'mesh',
        'encryption': 'AES-256',
        'max_devices': 1000,
        'latency': 'low'
    }
    result2 = designer.design_protocol(spec)
    print(f"   النتيجة: {result2}")
    print(f"   ✅ تم التصميم: {result2.get('protocol_designed')}")
    print(f"   📊 المواصفات: {result2.get('spec')}")
    print(f"   🔐 الأمان: {result2.get('security')}")
    print(f"   📚 الطبقات: {result2.get('layers')}")
    
    # Validation
    has_output1 = result1 and result1.get('iot_protocol') is not None
    has_output2 = result2 and result2.get('protocol_designed') == True
    
    print(f"\n{'✅' if has_output1 and has_output2 else '❌'} التقييم النهائي:")
    print(f"   - إجابات حقيقية: {'نعم ✅' if has_output1 and has_output2 else 'لا ❌'}")
    print(f"   - طول الإجابة 1: {len(str(result1))} حرف")
    print(f"   - طول الإجابة 2: {len(str(result2))} حرف")
    print(f"   - عدد الطبقات المصممة: {len(result2.get('layers', []))}")
    
    return has_output1 and has_output2

def test_self_monitoring_system():
    """اختبار نظام المراقبة الذاتية"""
    print_section("اختبار SelfMonitoringSystem - نظام المراقبة الذاتية")
    
    monitor = SelfMonitoringSystem()
    
    # Test 1: Heartbeat check
    print("\n📊 الاختبار 1: فحص نبض النظام")
    result1 = monitor.heartbeat()
    print(f"   النتيجة: {result1}")
    print(f"   💓 النبض: {'نشط ✅' if result1 else 'متوقف ❌'}")
    
    # Test 2: System monitoring
    print("\n📊 الاختبار 2: مراقبة النظام")
    result2 = monitor.monitor()
    print(f"   النتيجة: {result2}")
    print(f"   ✅ الحالة: {result2.get('status')}")
    print(f"   ⏱️ وقت التشغيل: {result2.get('uptime')}")
    print(f"   📊 المقاييس: {result2.get('metrics')}")
    print(f"   ⚠️ التنبيهات: {result2.get('alerts')}")
    
    # Test 3: Health check
    print("\n📊 الاختبار 3: فحص الصحة")
    result3 = monitor.check_health()
    print(f"   النتيجة: {result3}")
    print(f"   💚 صحة النظام: {'جيد ✅' if result3.get('healthy') else 'سيء ❌'}")
    print(f"   🖥️ المكونات: {result3.get('components')}")
    
    # Validation
    has_output1 = result1 == True
    has_output2 = result2 and result2.get('status') == 'healthy'
    has_output3 = result3 and result3.get('healthy') == True
    
    print(f"\n{'✅' if all([has_output1, has_output2, has_output3]) else '❌'} التقييم النهائي:")
    print(f"   - إجابات حقيقية: {'نعم ✅' if all([has_output1, has_output2, has_output3]) else 'لا ❌'}")
    print(f"   - نبض النظام: {'✅' if has_output1 else '❌'}")
    print(f"   - حالة المراقبة: {'✅' if has_output2 else '❌'}")
    print(f"   - فحص الصحة: {'✅' if has_output3 else '❌'}")
    print(f"   - عدد المكونات المراقبة: {len(result3.get('components', {}))}")
    
    return all([has_output1, has_output2, has_output3])

def main():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*70)
    print("🚀 اختبار المحركات الثلاثة المُصلحة - توليد الإجابات الحقيقية")
    print("="*70)
    
    results = {}
    
    # Test each engine
    try:
        results['hardware_simulator'] = test_hardware_simulator()
    except Exception as e:
        print(f"\n❌ خطأ في HardwareSimulator: {e}")
        results['hardware_simulator'] = False
    
    try:
        results['iot_designer'] = test_iot_protocol_designer()
    except Exception as e:
        print(f"\n❌ خطأ في IoTProtocolDesigner: {e}")
        results['iot_designer'] = False
    
    try:
        results['monitoring'] = test_self_monitoring_system()
    except Exception as e:
        print(f"\n❌ خطأ في SelfMonitoringSystem: {e}")
        results['monitoring'] = False
    
    # Final summary
    print("\n" + "="*70)
    print("📊 الملخص النهائي - تقييم توليد الإجابات")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n{'✅' if results.get('hardware_simulator') else '❌'} HardwareSimulator: "
          f"{'يولد إجابات حقيقية' if results.get('hardware_simulator') else 'لا يولد إجابات'}")
    print(f"{'✅' if results.get('iot_designer') else '❌'} IoTProtocolDesigner: "
          f"{'يولد إجابات حقيقية' if results.get('iot_designer') else 'لا يولد إجابات'}")
    print(f"{'✅' if results.get('monitoring') else '❌'} SelfMonitoringSystem: "
          f"{'يولد إجابات حقيقية' if results.get('monitoring') else 'لا يولد إجابات'}")
    
    print(f"\n📈 معدل النجاح: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ممتاز! جميع المحركات تولد إجابات حقيقية وليست فارغة!")
    elif passed > 0:
        print(f"\n⚠️ تحذير: {total - passed} محرك لا يولد إجابات حقيقية")
    else:
        print("\n❌ خطأ: لا يوجد أي محرك يولد إجابات حقيقية!")
    
    print("="*70)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
