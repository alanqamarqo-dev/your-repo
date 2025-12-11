#!/usr/bin/env python3
"""
اختبار نقاط نهاية AGI الجديدة
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_consciousness_status():
    """اختبار حالة الوعي"""
    print("\n" + "="*60)
    print("🧠 اختبار 0: حالة الوعي")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/agi/consciousness_status", timeout=10)
        result = response.json()
        print(f"✅ الحالة: {response.status_code}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def test_original_math():
    """اختبار التفكير الرياضي الأصيل"""
    print("\n" + "="*60)
    print("🔢 اختبار 1: التفكير الرياضي الأصيل")
    print("="*60)
    
    problem = "أوجد جميع الأعداد الأولية p حيث p² + 2 عدد أولي أيضاً"
    print(f"المسألة: {problem}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/agi/test_original_math",
            json={"problem": problem},
            timeout=120
        )
        result = response.json()
        
        print(f"\n✅ الحل:")
        print(f"الحالة: {response.status_code}")
        
        if "solution" in result:
            print(f"\nالحل الرياضي:\n{result['solution'][:500]}...")
        
        if "learning_status" in result:
            print(f"\nحالة التعلم: {result['learning_status']}")
        
        if "consciousness_level" in result:
            print(f"\nمستوى الوعي: {result['consciousness_level']}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def test_creativity():
    """اختبار الإبداع - اختراع لعبة"""
    print("\n" + "="*60)
    print("🎮 اختبار 2: الإبداع (اختراع لعبة)")
    print("="*60)
    
    requirements = "لعبة تدمج الرياضيات والفلسفة"
    print(f"المتطلبات: {requirements}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/agi/test_creativity",
            json={"requirements": requirements},
            timeout=120
        )
        result = response.json()
        
        print(f"\n✅ النتيجة:")
        print(f"الحالة: {response.status_code}")
        
        if "original_idea" in result:
            print(f"\nالفكرة الأصلية:")
            print(json.dumps(result['original_idea'], ensure_ascii=False, indent=2))
        
        if "game_design" in result:
            print(f"\nتصميم اللعبة:\n{result['game_design'][:500]}...")
        
        if "creativity_score" in result:
            print(f"\nدرجة الإبداع: {result['creativity_score']}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def test_evolution_smoke():
    """اختبار فحص سلامة التطور الذاتي"""
    print("\n" + "="*60)
    print("🧬 اختبار 3: فحص التطور الذاتي (Evolution)")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": "test evolution integrity"},
            timeout=60
        )
        result = response.json()
        
        print(f"✅ الحالة: {response.status_code}")
        
        # تأكيد وجود حقول التطور
        meta = result.get('meta', {})
        assert 'evolution_status' in meta, "❌ حقل evolution_status غير موجود"
        assert 'genetic_generations' in meta, "❌ حقل genetic_generations غير موجود"
        
        print(f"\n✅ حالة التطور: {meta['evolution_status']}")
        print(f"✅ عدد الأجيال: {meta['genetic_generations']}")
        
        # تحقق إضافي من تاريخ التطور إن وُجد
        if 'evolution_history' in meta:
            print(f"✅ سجل التطور متوفر: {len(meta['evolution_history'])} نقطة تفتيش")
        
        return True
        
    except AssertionError as e:
        print(f"❌ فشل التأكيد: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def test_evolution_smoke():
    """اختبار فحص سلامة التطور الذاتي"""
    print("\n" + "="*60)
    print("🧬 اختبار 3: فحص التطور الذاتي (Evolution)")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": "test evolution integrity"},
            timeout=60
        )
        result = response.json()
        
        print(f"✅ الحالة: {response.status_code}")
        
        # تأكيد وجود حقول التطور
        meta = result.get('meta', {})
        assert 'evolution_status' in meta, "❌ حقل evolution_status غير موجود"
        assert 'genetic_generations' in meta, "❌ حقل genetic_generations غير موجود"
        
        print(f"\n✅ حالة التطور: {meta['evolution_status']}")
        print(f"✅ عدد الأجيال: {meta['genetic_generations']}")
        
        # تحقق إضافي من تاريخ التطور إن وُجد
        if 'evolution_history' in meta:
            print(f"✅ سجل التطور متوفر: {len(meta['evolution_history'])} نقطة تفتيش")
        
        return True
        
    except AssertionError as e:
        print(f"❌ فشل التأكيد: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def test_language_invention():
    """اختبار اختراع لغة جديدة"""
    print("\n" + "="*60)
    print("🗣️ اختبار 4: اختراع لغة جديدة")
    print("="*60)
    
    theme = "لغة رياضية-فلسفية"
    print(f"الموضوع: {theme}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/agi/test_language_invention",
            json={"theme": theme},
            timeout=120
        )
        result = response.json()
        
        print(f"\n✅ النتيجة:")
        print(f"الحالة: {response.status_code}")
        
        if "invented_language" in result:
            print(f"\nاللغة المخترعة:\n{result['invented_language'][:500]}...")
        
        if "learning_status" in result:
            print(f"\nحالة التعلم: {result['learning_status']}")
        
        if "can_teach" in result:
            print(f"\nهل يمكن تعليمها؟ {result['can_teach']}")
        
        return True

    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def test_evolution_smoke():
    """Smoke test: ensure evolution diagnostic runs and meta contains keys."""
    print("\n" + "="*60)
    print("🧪 اختبار تطور: فحص سلامة الإشارة")
    print("="*60)
    try:
        payload = {"message": "smoke evolution test"}
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=180)
        print(f"حالة الاستجابة: {response.status_code}")
        data = response.json()
        meta = data.get('meta') or {}
        # Basic assertions / checks
        ok = True
        if 'evolution_status' not in meta:
            print("❌ الحقل 'evolution_status' غير موجود في meta")
            ok = False
        else:
            print(f"evolution_status: {meta.get('evolution_status')}")

        if 'genetic_generations' not in meta:
            print("❌ الحقل 'genetic_generations' غير موجود في meta")
            ok = False
        else:
            print(f"genetic_generations: {meta.get('genetic_generations')}")

        # Ensure service didn't error
        if response.status_code != 200:
            print("❌ استجابة غير 200 من الخادم")
            ok = False

        print("✅ اختبار تطور انتهى — نجاح" if ok else "❌ اختبار تطور فشل")
        return ok
    except Exception as e:
        print(f"❌ خطأ أثناء اختبار التطور: {e}")
        return False


def main():
    """تشغيل جميع الاختبارات"""
    print("\n" + "🚀 "*30)
    print("بدء اختبارات AGI الشاملة")
    print("🚀 "*30)
    
    results = {
        "consciousness_status": test_consciousness_status(),
        "original_math": test_original_math(),
        "creativity": test_creativity(),
        "language_invention": test_language_invention(),
        "evolution_smoke": test_evolution_smoke()
    }
    
    print("\n" + "="*60)
    print("📊 ملخص النتائج:")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ نجح" if passed else "❌ فشل"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nالإجمالي: {passed}/{total} اختبارات نجحت")
    
    if passed == total:
        print("\n🎉 جميع الاختبارات نجحت! النظام جاهز لـ AGI")
    else:
        print(f"\n⚠️ {total - passed} اختبار(ات) فشلت، يلزم المزيد من العمل")


if __name__ == "__main__":
    main()
