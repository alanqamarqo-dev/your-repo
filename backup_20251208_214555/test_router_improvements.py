"""
اختبار التحسينات الجديدة على intelligent_engine_router
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(test_name, message, expected_engine=None):
    """اختبار endpoint واحد"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")
    print(f"📝 السؤال: {message[:80]}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message},
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            engine = data.get('engine', 'unknown')
            status = data.get('status', 'unknown')
            reply = data.get('reply', '')
            error = data.get('error')
            
            print(f"\n✅ الحالة: {response.status_code}")
            print(f"🔧 المحرك: {engine}")
            print(f"📊 الحالة: {status}")
            
            if error:
                print(f"❌ خطأ: {error}")
                return False
            
            if reply:
                print(f"\n💬 الرد:")
                print(reply[:300])
                if len(reply) > 300:
                    print(f"... ({len(reply)} حرف إجمالي)")
            
            if expected_engine and engine != expected_engine:
                print(f"\n⚠️  تحذير: المحرك المتوقع {expected_engine} لكن حصلنا على {engine}")
                return False
            
            return True
        else:
            print(f"❌ خطأ: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ استثناء: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 اختبار التحسينات على intelligent_engine_router")
    print("="*60)
    
    time.sleep(2)  # انتظار استعداد السيرفر
    
    tests = [
        {
            "name": "الاختبار 1: معادلة رياضية بسيطة",
            "message": "solve: 3x + 7 = 22",
            "expected": None  # MathematicalBrain أو mission_control
        },
        {
            "name": "الاختبار 2: مسألة تحسين معقدة",
            "message": "لديك مزرعة مساحتها 1000 متر مربع وميزانية 5000 دولار. تريد زراعة 3 محاصيل مختلفة لتحقيق أقصى ربح. ما هو التوزيع الأمثل؟",
            "expected": "mission_control"  # يجب توجيهه للتحسين
        },
        {
            "name": "الاختبار 3: سؤال إبداعي",
            "message": "اخترع طريقة مبتكرة لتنقية المياه في القرى الفقيرة باستخدام مواد محلية رخيصة",
            "expected": "mission_control"  # يجب توجيهه للإبداع
        },
        {
            "name": "الاختبار 4: قصة إبداعية",
            "message": "اكتب قصة قصيرة عن ذكاء اصطناعي يتعلم المشاعر الإنسانية",
            "expected": "mission_control"
        }
    ]
    
    results = []
    for test in tests:
        success = test_endpoint(
            test["name"],
            test["message"],
            test.get("expected")
        )
        results.append({
            "name": test["name"],
            "success": success
        })
        time.sleep(2)  # فترة راحة بين الاختبارات
    
    # ملخص النتائج
    print(f"\n\n{'='*60}")
    print("📊 ملخص النتائج")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for r in results:
        status = "✅ نجح" if r["success"] else "❌ فشل"
        print(f"{status} - {r['name']}")
    
    print(f"\n🎯 النتيجة النهائية: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 جميع الاختبارات نجحت!")
    elif passed >= total * 0.5:
        print(f"\n⚠️  {total - passed} اختبار(ات) فشل(ت)")
    else:
        print(f"\n❌ معظم الاختبارات فشلت ({total - passed}/{total})")

if __name__ == "__main__":
    main()
