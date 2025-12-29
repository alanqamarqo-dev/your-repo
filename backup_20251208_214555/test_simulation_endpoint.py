import requests
import json
import time

class SimulationEndpointTester:
    def __init__(self, base_url="http://127.0.0.1:8000", token="GENESIS_ALPHA_TOKEN"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_basic_simulation(self):
        """اختبار محاكاة أساسية"""
        print("🧪 اختبار محاكاة أساسية...")
        
        payload = {
            "hypothesis": "الإنتروبيا العكسية محلياً تخلق حلقات زمنية مغلقة عبر مترية معدلة",
            "simulation_type": "metric_tensor",
            "steps": 200,
            "dt": 0.02,
            "parameters": {
                "alpha": 1.5,
                "spatial_resolution": 50,
                "calculate_curvature": True
            },
            "metadata": {
                "researcher": "نظام Genesis Alpha",
                "priority": "high"
            }
        }
        
        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/api/simulate",
            json=payload,
            headers=self.headers,
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ نجح الاختبار ({elapsed:.2f} ثانية)")
            print(f"   معرف المحاكاة: {results.get('simulation_id')}")
            print(f"   درجة الثقة: {results.get('metrics', {}).get('confidence_score', 0):.3f}")
            print(f"   وقت الحساب: {results.get('metrics', {}).get('computation_time', 0)} ثانية")
            return results
        else:
            print(f"❌ فشل الاختبار: {response.status_code}")
            print(f"   الرسالة: {response.text}")
            return None
    
    def test_quantum_simulation(self):
        """اختبار محاكاة كمومية-ديناميكية"""
        print("\n⚛️ اختبار محاكاة كمومية-ديناميكية...")
        
        payload = {
            "hypothesis": "استغلال التقلبات الكمومية لخلق إنتروبيا عكسية مؤقتة",
            "simulation_type": "quantum_thermodynamic",
            "steps": 500,
            "dt": 0.01,
            "parameters": {
                "alpha": 0.8,
                "quantum_states": 2,
                "temperature": 0.001,
                "coherence_time": 10.0
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/simulate",
            json=payload,
            headers=self.headers,
            timeout=45
        )
        
        return self._process_response(response)
    
    def test_entropy_reversal(self):
        """اختبار محاكاة انعكاس الانتروبيا"""
        print("\n🔄 اختبار محاكاة انعكاس الانتروبيا...")
        
        payload = {
            "hypothesis": "يمكن عكس الانتروبيا محلياً عبر حقول كمومية متشابكة",
            "simulation_type": "entropy_reversal",
            "steps": 300,
            "dt": 0.05,
            "parameters": {
                "reversal_strength": 0.7,
                "localization_radius": 2.0,
                "quantum_entanglement": True
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/simulate",
            json=payload,
            headers=self.headers,
            timeout=30
        )
        
        return self._process_response(response)
    
    def test_invalid_token(self):
        """اختبار توكن غير صالح"""
        print("\n🔒 اختبار مصادقة فاشلة (توكن خاطئ)...")
        
        wrong_headers = self.headers.copy()
        wrong_headers["Authorization"] = "Bearer WRONG_TOKEN"
        
        response = requests.post(
            f"{self.base_url}/api/simulate",
            json={"hypothesis": "اختبار"},
            headers=wrong_headers,
            timeout=10
        )
        
        if response.status_code == 403:
            print("✅ فشل المصادقة كما هو متوقع (رمز 403)")
            return True
        else:
            print(f"❌ كان يجب أن يفشل لكنه نجح: {response.status_code}")
            return False
    
    def test_rate_limiting(self):
        """اختبار عدة طلبات متتالية"""
        print("\n⚡ اختبار عدة طلبات سريعة...")
        
        payload = {
            "hypothesis": "اختبار الأداء",
            "simulation_type": "metric_tensor",
            "steps": 50,
            "dt": 0.1
        }
        
        times = []
        for i in range(3):
            start = time.time()
            response = requests.post(
                f"{self.base_url}/api/simulate",
                json=payload,
                headers=self.headers,
                timeout=20
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                times.append(elapsed)
                print(f"   الطلب {i+1}: {elapsed:.2f} ثانية")
            else:
                print(f"   الطلب {i+1} فشل: {response.status_code}")
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"   ⏱️ متوسط الزمن: {avg_time:.2f} ثانية")
    
    def _process_response(self, response):
        """معالجة الاستجابة"""
        if response.status_code == 200:
            data = response.json()
            sim_id = data.get('simulation_id', 'غير معروف')
            confidence = data.get('metrics', {}).get('confidence_score', 0)
            print(f"✅ نجح: {sim_id} (ثقة: {confidence:.3f})")
            
            # حفظ النتائج
            filename = f"artifacts/test_{sim_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"   💾 محفوظ في: {filename}")
            
            return data
        else:
            print(f"❌ فشل: {response.status_code}")
            print(f"   التفاصيل: {response.text[:200]}")
            return None
    
    def run_comprehensive_test(self):
        """تشغيل جميع الاختبارات"""
        print("=" * 60)
        print("🧪 بدء الاختبار الشامل لـ /api/simulate")
        print("=" * 60)
        
        results = {}
        
        # 1. اختبار المصادقة أولاً
        if not self.test_invalid_token():
            print("\n⚠️ تحذير: نظام المصادقة لا يعمل كما يجب")
        
        # 2. اختبارات المحاكاة
        results['basic'] = self.test_basic_simulation()
        results['quantum'] = self.test_quantum_simulation()
        results['entropy'] = self.test_entropy_reversal()
        
        # 3. اختبار الأداء
        self.test_rate_limiting()
        
        # 4. تحليل النتائج
        self._analyze_results(results)
        
        return results
    
    def _analyze_results(self, results):
        """تحليل نتائج الاختبار"""
        print("\n" + "=" * 60)
        print("📊 تحليل نتائج الاختبار")
        print("=" * 60)
        
        successful = sum(1 for r in results.values() if r is not None)
        total = len(results)
        
        print(f"الاختبارات الناجحة: {successful}/{total}")
        
        if successful > 0:
            confidences = []
            times = []
            
            for key, data in results.items():
                if data:
                    conf = data.get('metrics', {}).get('confidence_score', 0)
                    comp_time = data.get('metrics', {}).get('computation_time', 0)
                    confidences.append(conf)
                    times.append(comp_time)
                    
                    print(f"\n{key.upper()}:")
                    print(f"  الثقة: {conf:.3f}")
                    print(f"  وقت الحساب: {comp_time:.2f} ثانية")
                    print(f"  الخطوات: {data.get('parameters_used', {}).get('steps', 'N/A')}")
            
            if confidences:
                avg_conf = sum(confidences) / len(confidences)
                avg_time = sum(times) / len(times)
                print(f"\n📈 المتوسطات:")
                print(f"  متوسط الثقة: {avg_conf:.3f}")
                print(f"  متوسط زمن المحاكاة: {avg_time:.2f} ثانية")

if __name__ == "__main__":
    tester = SimulationEndpointTester()
    results = tester.run_comprehensive_test()
    
    # حفظ تقرير الاختبار
    with open("artifacts/endpoint_test_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "test_timestamp": time.time(),
            "results_summary": {
                key: "success" if data else "failed" 
                for key, data in results.items()
            },
            "details": results
        }, f, indent=2, ensure_ascii=False)
    
    print("\n📁 تقرير الاختبار محفوظ في: artifacts/endpoint_test_report.json")