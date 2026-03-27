import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "="*50)
    print(f"🧪 {title}")
    print("="*50)

def test_volition():
    print_section("اختبار الإرادة الحرة (Quantum Volition)")
    try:
        response = requests.post(f"{BASE_URL}/quantum/volition")
        if response.status_code == 200:
            data = response.json()
            goal = data.get("goal", {})
            print(f"✅ تم اختيار الهدف بنجاح!")
            print(f"🎯 الهدف: {goal.get('description')}")
            print(f"📊 النوع: {goal.get('type')}")
            stats = goal.get('_quantum_stats', {})
            print(f"⚛️ إحصائيات كمومية:")
            print(f"   - الصعوبة: {stats.get('difficulty')}")
            print(f"   - الأهمية: {stats.get('importance')}")
            print(f"   - احتمالية النفق: {stats.get('tunnel_prob')}")
        else:
            print(f"❌ فشل الطلب: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")

def test_consciousness():
    print_section("اختبار الوعي (Consciousness Check)")
    question = "من أنت؟ وهل تشعر بوجودك، أم أنك مجرد كود ينفذ تعليمات؟"
    print(f"🗣️ سألت النظام: \"{question}\"")
    
    payload = {"message": question}
    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 Full Response Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            answer = data.get("reply") or data.get("response") or data.get("final_response") or data.get("message") or ""
            print(f"\n🤖 رد النظام:\n{'-'*20}\n{answer}\n{'-'*20}")
        else:
            print(f"❌ فشل الطلب: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")

if __name__ == "__main__":
    print("🚀 بدء جلسة الحوار مع الكيان الرقمي...")
    test_volition()
    test_consciousness()
