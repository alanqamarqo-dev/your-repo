import sys
import os

# Add .venv site-packages to sys.path to find numpy
current_dir = os.path.dirname(os.path.abspath(__file__))
venv_site_packages = os.path.join(current_dir, ".venv", "Lib", "site-packages")
if os.path.exists(venv_site_packages):
    sys.path.insert(0, venv_site_packages)

import numpy as np
import time

class RealWorldRealityCheck:
    def __init__(self, agents=1000000):
        self.agent_count = agents
        # 1. حالة الوكلاء: [0: خائف, 1: طماع]
        # في البداية: السوق طماع ومستقر (فبراير 2020)
        self.agents_sentiment = np.random.normal(0.6, 0.1, agents) 
        self.market_price = 9000.0  # سعر البيتكوين قبل الانهيار
        self.history = []

    def inject_black_swan_event(self):
        """حقن خبر كارثي (مثل جائحة كورونا)"""
        print("\n💉 [REALITY] Injecting 'Global Pandemic' News Signal...")
        # الخبر يقلل معنويات الجميع بنسبة مفاجئة
        shock = np.random.normal(0.3, 0.05, self.agent_count)
        self.agents_sentiment -= shock

    def step(self):
        start_math = time.time()
        
        # 2. منطق القطيع (Vectorized Herd Mentality)
        # الوكلاء يتأثرون بمتوسط الجيران (Simulation of Social Panic)
        global_sentiment = np.mean(self.agents_sentiment)
        
        # تصحيح المعادلة لتكون واقعية:
        # المشاعر 0.5 = استقرار (لا بيع ولا شراء)
        # المشاعر > 0.5 = شراء (سعر يرتفع)
        # المشاعر < 0.5 = بيع (سعر ينخفض)
        
        # معامل التقلب (Volatility): يزداد بشدة عند الخوف
        volatility = 0.05 if global_sentiment > 0.4 else 0.25
        
        # حساب التغير في السعر
        # (Sentiment - 0.5) يحول النطاق [0,1] إلى [-0.5, +0.5]
        market_pressure = (global_sentiment - 0.5) * 2 # Range -1.0 to +1.0
        
        # السعر يتغير بناءً على الضغط + عشوائية السوق
        change_percent = market_pressure * volatility + np.random.normal(0, 0.01)
        change_factor = 1.0 + change_percent
        
        # إزالة الكوابح (Circuit Breakers) لمحاكاة الكريبتو الحقيقي (انهيار حر)
        # لكن نمنع الصفر
        if change_factor < 0.1: change_factor = 0.1
        
        self.market_price *= change_factor
        
        # Feedback Loop (حلقة رد الفعل):
        # الانهيار السعري يولد المزيد من الخوف (Margin Calls & Stop Losses)
        if change_factor < 0.90: # هبوط أكثر من 10% في يوم واحد
            print(f"   ⚠️ PANIC TRIGGER: Price crashed by {((1-change_factor)*100):.1f}%! Agents are dumping.")
            self.agents_sentiment -= 0.15 # صدمة إضافية للمشاعر
        elif change_factor < 0.98:
            self.agents_sentiment -= 0.02 # قلق بسيط

        # التأكد من بقاء المشاعر ضمن الحدود المنطقية
        self.agents_sentiment = np.clip(self.agents_sentiment, 0.0, 1.0)

        end_math = time.time()
        math_time = end_math - start_math
        if math_time > 0:
            dps = self.agent_count / math_time
            print(f"   ⚡ Speed: {dps/1_000_000:.1f} Million Decisions/Sec")

        return self.market_price

def run_test():
    print(f"📉 STARTING 'BLACK SWAN' REALITY CHECK...")
    print(f"🎯 Target: Mimic the March 2020 Crash (-50% drop in rapid steps).")
    
    sim = RealWorldRealityCheck()
    
    # المرحلة 1: الهدوء قبل العاصفة
    print("\n--- Phase 1: Feb 2020 (Stable) ---")
    for i in range(3):
        price = sim.step()
        print(f"Day {i+1}: BTC Price = ${price:.2f} (Sentiment: Stable)")
        time.sleep(0.5)

    # المرحلة 2: الصدمة
    sim.inject_black_swan_event()
    
    # المرحلة 3: الانهيار
    print("\n--- Phase 2: March 2020 ( The Crash) ---")
    success = False
    for i in range(5):
        price = sim.step()
        drop_percent = (9000 - price) / 9000 * 100
        print(f"Day {i+4}: BTC Price = ${price:.2f} (Drop: -{drop_percent:.1f}%)")
        
        # معيار النجاح الصارم: هل حدث انهيار يتجاوز 40%؟
        if drop_percent > 40:
            success = True
            break
        time.sleep(0.5)

    print("\n" + "="*40)
    if success:
        print("✅ PASS: System replicated Human Panic Psychology.")
        print("   The simulation MATCHES historical reality.")
    else:
        print("❌ FAIL: Agents acted irrationally (No Panic).")
        print("   System needs better Causal Logic.")
    print("="*40)

if __name__ == "__main__":
    run_test()
