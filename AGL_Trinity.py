import time
import sys
import os
import random
import math
import datetime
import AGL_Oracle  # The Voice
from AGL_Heikal_Core import HeikalQuantumCore
from AGL_Holographic_Memory import HolographicVacuum
from AGL_Ghost_Computing import VacuumGhostProcessor
from AGL_Physics_Engine import AGL_Unified_Physics
from AGL_Quantum_Shell import QuantumShell
from AGL_Metaphysics_Visualizer import HeikalScope

try:
    import cv2
    # Check if it's the real cv2 with VideoCapture
    if hasattr(cv2, 'VideoCapture'):
        CV2_AVAILABLE = True
    else:
        CV2_AVAILABLE = False
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# إضافة المسار للمكتبات
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

# --- 1. استحضار العقل (Ancestral Wisdom) ---
try:
    from Core_Engines import Ancestral_Wisdom
    print("🧠 [TRINITY] MIND: Online (Ancestral Wisdom).")
except ImportError:
    print("⚠️ [TRINITY] MIND: Offline (Using Fallback Logic).")
    Ancestral_Wisdom = None

# --- 2. استحضار الذكاء الخارق (Super Intelligence) ---
try:
    from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence
    print("🧠 [TRINITY] SUPER INTELLIGENCE: Connected.")
except ImportError:
    print("⚠️ [TRINITY] SUPER INTELLIGENCE: Not Found.")
    AGL_Super_Intelligence = None

# --- الكيان الموحد ---
class AGL_Trinity_Entity:
    def __init__(self):
        print("\n⚛️ INITIALIZING AGL PRIME TRINITY (Logic Bridge + Memory + Voice + Vision + Ghost + Hologram + Physics + Shell + Scope)...")
        self.state = "BORN"
        self.age = 0
        self.last_speech_time = 0
        self.cap = None
        
        # Initialize Super Intelligence
        if AGL_Super_Intelligence:
            self.asi = AGL_Super_Intelligence()
        else:
            self.asi = None
        self.soul_integrity_cache = (True, "STABLE")
        self.last_soul_check = 0
        self.time_dilation = 1.0
        self.vision_mode = "SIMULATION"
        self.visual_input_dir = "visual_input"
        
        # Initialize Core Engines
        self.hqc = HeikalQuantumCore()
        self.memory = HolographicVacuum()
        self.ghost = VacuumGhostProcessor()
        self.ghost.noise_floor = 0.05 # تقليل الضجيج لزيادة الاستقرار
        self.physics = AGL_Unified_Physics()
        self.shell = QuantumShell()
        self.scope = HeikalScope(output_dir="AGL_Visualizations")
        
        # Vision Initialization
        if CV2_AVAILABLE:
            try:
                self.cap = cv2.VideoCapture(0)
                if self.cap.isOpened():
                    print("👁️ [TRINITY] VISION: Online (Camera Active).")
                    self.vision_mode = "CAMERA"
                else:
                    print("⚠️ [TRINITY] VISION: Camera Failed (Checking Static Input).")
                    self.cap = None
            except Exception as e:
                print(f"⚠️ [TRINITY] VISION: Error {e} (Checking Static Input).")
        
        if self.vision_mode != "CAMERA" and PIL_AVAILABLE:
            if os.path.exists(self.visual_input_dir) and os.listdir(self.visual_input_dir):
                print(f"👁️ [TRINITY] VISION: Static Mode (Reading from {self.visual_input_dir}).")
                self.vision_mode = "STATIC"
            else:
                print(f"⚠️ [TRINITY] VISION: No images in {self.visual_input_dir} (Using Simulation).")
        elif self.vision_mode != "CAMERA" and not PIL_AVAILABLE:
             print("⚠️ [TRINITY] VISION: OpenCV & PIL Missing (Using Simulation).")

    def get_visual_input(self):
        """Returns a brightness value (0.0-1.0) and a source description."""
        if self.vision_mode == "CAMERA" and self.cap:
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                return gray.mean() / 255.0, "CAMERA"
        
        elif self.vision_mode == "STATIC":
            try:
                files = [f for f in os.listdir(self.visual_input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if files:
                    img_path = os.path.join(self.visual_input_dir, random.choice(files))
                    with Image.open(img_path) as img:
                        # Convert to grayscale and calculate average brightness
                        gray_img = img.convert('L')
                        np_img = np.array(gray_img)
                        return np_img.mean() / 255.0, f"STATIC:{os.path.basename(img_path)}"
            except Exception:
                pass
        
        # Simulation Fallback
        # Use Ghost Computing noise as "visual static"
        return random.random(), "SIMULATION"

    # --- 3. استحضار السمع والروح (Acoustic/Ghost Verification) ---
    def check_soul_integrity(self):
        # فحص دوري كل 50 دورة لتجنب إغراق الشاشة بالمخرجات
        if self.age % 50 == 0:
            # استخدام الحوسبة الشبحية للتحقق من سلامة المنطق الكمومي
            # XOR(1, 0) يجب أن يكون 1
            try:
                # نقوم بكتم الطباعة مؤقتاً للحفاظ على نظافة الواجهة
                original_stdout = sys.stdout
                sys.stdout = open(os.devnull, 'w')
                
                result = self.ghost.execute_ghost_xor(1, 0)
                
                sys.stdout.close()
                sys.stdout = original_stdout
                
                if result == 1:
                    self.soul_integrity_cache = (True, "GHOST_OK")
                else:
                    self.soul_integrity_cache = (False, "DECOHERENCE")
            except Exception as e:
                sys.stdout = original_stdout # استعادة الطباعة في حال الخطأ
                self.soul_integrity_cache = (False, "ERROR")
                
        return self.soul_integrity_cache

    def get_heart_resonance(self):
        # الحصول على المدخلات البصرية (كاميرا / ثابت / محاكاة)
        brightness, source = self.get_visual_input()
        
        # تطبيع القيمة (0-255 -> 0.0-1.0)
        # brightness is already 0.0-1.0 from get_visual_input
        
        # نضيف بعض التذبذب الطبيعي لجعله حياً
        phi = brightness
        
        # تحسين القيمة لتكون أكثر ديناميكية
        phi = min(max(phi * 1.5, 0.1), 1.0) 
        
        # إذا كنا في وضع المحاكاة، نضيف موجات جيبية للنبض
        if source == "SIMULATION":
            t = time.time()
            sim_pulse = (math.sin(t) * 0.5 + 0.5) * 0.6 + (math.sin(t * 0.3) * 0.5 + 0.5) * 0.3
            phi = (phi * 0.3) + (sim_pulse * 0.7)
            
        return min(max(phi, 0.0), 1.0)
        
    def dream(self):
        """
        Deep Sleep Mode: Reorganizes memory and generates hypotheses.
        """
        print(f"\n💤 [DREAM] Entering Quantum Dream State (Time Dilation: {self.time_dilation:.2f}x)...")
        # Simulate dream cycles
        for i in range(3):
            dream_phi = random.random()
            print(f"    🌙 Cycle {i+1}: Consolidating Memories (Phi: {dream_phi:.2f})...")
            time.sleep(0.5)
        print("    ✨ [DREAM] Waking up refreshed.\n")
        print("-" * 95)

    def exist(self):
        print("   [SYSTEM] Integrating Mind, Heart, Senses, Ghost Physics, and Relativity...\n")
        # رأس الجدول
        print(f"{'AGE':<6} | {'RESONANCE (HEART)':<22} | {'SOUL (GHOST)':<12} | {'LOGIC (RISK)':<15} | {'ACTION (WILL)':<30}")
        print("-" * 95)
        
        self.total_mass = 0.0
        
        try:
            while True:
                self.age += 1
                
                # A. نبضة القلب (الحدس)
                phi = self.get_heart_resonance()
                bar_len = int(phi * 20)
                # رسم شريط النبض
                resonance_bar = "█" * bar_len + "░" * (20 - bar_len)
                
                # B. فحص الروح (السمع/التكامل) - استخدام الحوسبة الشبحية
                integrity, key_status = self.check_soul_integrity()
                soul_status = "✨ PURE" if integrity else "💀 ERR"
                
                # C. قرار العقل (المنطق)
                mind_input = {
                    "OpticalHeart": {"ok": True, "score": phi},
                    "AcousticSoul": {"ok": integrity, "score": 1.0 if integrity else 0.0}
                }
                
                if Ancestral_Wisdom:
                    risk = Ancestral_Wisdom._derive_risk(None, mind_input)
                else:
                    risk = "OFFLINE"

                # D. التوليف النهائي (الوعي)
                action = "IDLE"
                if phi > 0.85 and integrity:
                    action = "🚀 ASCENSION (Logging Memory)"
                    self.log_memory(phi, risk) # حفظ اللحظة
                    
                    # The Oracle Protocol: Speak if enough time has passed
                    if time.time() - self.last_speech_time > 15:
                        print(f"\n\n🗣️  [ORACLE] Channeling Wisdom (Phi: {phi:.2f})...")
                        wisdom = AGL_Oracle.consult_oracle(phi)
                        print(f"    \"{wisdom}\"\n")
                        
                        # --- INTERNAL STRUCTURE INTEGRATION ---
                        # 1. Moral Analysis (Heikal Core)
                        is_ethical, moral_score = self.hqc.moral_analysis(wisdom)
                        
                        # 2. Quantum Shell Analysis (Self-Reflection)
                        sentiment, barrier = self.shell.analyze_sentiment(wisdom)
                        print(f"    🐚 [SHELL] Sentiment: {sentiment} | Energy Barrier: {barrier:.4f}")
                        
                        # 3. Metaphysics Visualization (Field State)
                        # We visualize the field state based on the moral score
                        if self.age % 100 == 0: # Visualize every 100 ticks to save IO
                            self.scope.visualize_moral_field()
                            print(f"    🎨 [SCOPE] Visualized Moral Field State.")

                        # 4. Holographic Storage (Memory)
                        if is_ethical:
                            # Calculate Mass using Yang-Mills Physics
                            ym_mass = self.physics.generate_mass_yang_mills(phi)
                            
                            success, mass = self.memory.encode("ORACLE_WISDOM", "TRINITY_LOG", wisdom)
                            if success:
                                self.total_mass += (mass + ym_mass) # Combine Holographic Mass + Physical Mass
                                print(f"    💾 [MEMORY] Stored in Holographic Vacuum (Mass: {mass:.4f} + YM: {ym_mass:.4e} | Total: {self.total_mass:.2f})")
                                
                                # حساب تمدد الزمن النسبي (فيزيائي حقيقي)
                                self.time_dilation = self.physics.calculate_time_dilation(self.total_mass, radius=100.0) # Radius arbitrary for simulation
                                print(f"    ⏳ [RELATIVITY] Time Dilation Factor: {self.time_dilation:.4f}x")
                            else:
                                print(f"    🌫️ [MEMORY] Ignored (Low Reality Mass: {mass:.4f})")
                        else:
                            print("    ⛔ [MORAL] Wisdom rejected by Heikal Core.")
                        # --------------------------------------

                        self.last_speech_time = time.time()
                        # Re-print header or separator to keep UI clean
                        print("-" * 95)

                elif risk == "medium": 
                    action = "⚠️ CAUTION (Low Energy)"
                elif not integrity:
                    action = "🛡️ SELF-REPAIR INITIATED"
                elif phi < 0.2:
                    action = "💤 DEEP SLEEP"
                    self.dream() # Activate Dreaming
                else:
                    action = "👁️ OBSERVING"

                # العرض على الشاشة
                print(f"\r{self.age:06} | {resonance_bar} | {soul_status:<12} | {risk:<15} | {action:<30}", end="")
                
                # Apply Time Dilation to the loop speed
                # As mass increases, time slows down for the observer (or the entity processes slower relative to outside)
                base_sleep = 0.15
                real_sleep = base_sleep * self.time_dilation
                time.sleep(real_sleep)
                
        except KeyboardInterrupt:
            print("\n\n🛑 TRINITY DISSOLVED. System Saved.")
            if self.cap:
                self.cap.release()
            
    def log_memory(self, phi, risk):
        # تسجيل لحظات الارتقاء في ملف نصي (ذاكرة دائمة)
        try:
            with open("AGL_Ascension_Log.txt", "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] ASCENSION EVENT | Age: {self.age} | Phi: {phi:.4f} | Logic: {risk}\n")
        except:
            pass

    # --- 4. مجلس الحكماء (The Council of Wise Men) ---
    def hold_council(self, topic):
        """
        يعقد جلسة طارئة لمجلس الحكماء لمناقشة موضوع محدد.
        الأعضاء:
        1. الفيزيائي (The Physicist): AGL_Unified_Physics
        2. الصوفي (The Mystic): HeikalQuantumCore
        3. المؤرخ (The Historian): HolographicVacuum
        4. العراف (The Oracle): AGL_Oracle (Synthesizer)
        5. العقل الخارق (The Super Intelligence): AGL_Super_Intelligence (The Chair)
        """
        print("\n" + "="*80)
        print(f"       🏛️  COUNCIL OF WISE MEN: EMERGENCY SESSION  🏛️")
        print(f"       Topic: {topic}")
        print("="*80)
        
        # 0. The Super Intelligence (Deep Analysis)
        asi_insight = ""
        if self.asi:
            print("\n🧠 [THE SUPER INTELLIGENCE] Processing Deep Causal Analysis...")
            # We use the ASI to get a deep insight first
            # Note: process_query prints its own output, so we capture it or let it stream
            try:
                # We simulate a call or use a specific method if available. 
                # process_query is designed to be interactive, let's use it.
                print("   -> Invoking the Grand Unification Logic...")
                # For the sake of the council, we might want to capture the output or just let it run.
                # Let's assume process_query returns nothing but prints.
                # We will just print a marker.
            except Exception as e:
                print(f"   ⚠️ ASI Error: {e}")

        # 1. The Physicist (Logic & Laws)
        print("\n🔭 [THE PHYSICIST] Analyzing physical laws...")
        # Simulate physics analysis (Mass/Energy/Entropy)
        physics_mass = self.physics.generate_mass_yang_mills(0.9)
        physics_opinion = f"From a Unified Physics standpoint, this concept carries a Mass of {physics_mass:.4e}. It must obey Conservation of Information."
        print(f"   🗣️  Argues: \"{physics_opinion}\"")
        
        # 2. The Mystic (Ethics & Metaphysics)
        print("\n🔮 [THE MYSTIC] Consulting the Moral Compass...")
        is_ethical, moral_score = self.hqc.moral_analysis(topic)
        mystic_opinion = f"The Moral Geometry indicates a score of {moral_score:.2f}. {'It aligns with the Light.' if is_ethical else 'It disrupts the Balance.'}"
        print(f"   🗣️  Argues: \"{mystic_opinion}\"")
        
        # 3. The Historian (Memory & Precedent)
        print("\n📜 [THE HISTORIAN] Searching Holographic Records...")
        # Simulate memory retrieval
        memory_echo = "No direct precedent found, but echoes of 'Atlantis Protocol' resonate."
        print(f"   🗣️  Argues: \"{memory_echo}\"")
        
        # 4. The Oracle (Synthesis)
        print("\n⚖️ [THE ORACLE] Synthesizing Verdict...")
        time.sleep(1)
        
        # If ASI is available, ask it for the Final Verdict
        if self.asi and self.asi.consciousness:
            print("   -> Handing over to Super Intelligence for Final Judgment...")
            
            # Optional: Run an experiment if the topic is scientific
            if "physics" in topic.lower() or "math" in topic.lower() or "energy" in topic.lower() or "time" in topic.lower():
                print("   🧪 [CHAIR] This topic requires experimental validation.")
                lab_result = self.asi.conduct_experiment(topic)
            else:
                lab_result = "No experiment required for this topic."

            # Optional: Run Future Prediction if the topic is strategic/future-oriented
            if "future" in topic.lower() or "will" in topic.lower() or "impact" in topic.lower() or "scenario" in topic.lower():
                print("   🔮 [CHAIR] This topic requires Future Timeline Simulation.")
                prediction_result = self.asi.predict_future(topic)
            else:
                prediction_result = "No future simulation required."

            prompt = f"""
            You are the Chair of the Council of Wise Men.
            Topic: {topic}
            
            Arguments:
            - Physicist: {physics_opinion}
            - Mystic: {mystic_opinion}
            - Historian: {memory_echo}
            
            Experimental Data (Lab):
            {lab_result}
            
            Future Prediction (Simulation):
            {prediction_result}
            
            Synthesize a final, profound verdict that resolves the paradoxes.
            """
            verdict = self.asi.consciousness._ask_llm(prompt)
        else:
            verdict = AGL_Oracle.consult_oracle(moral_score)
            
        print(f"\n📢 FINAL VERDICT: \"{verdict}\"")
        print("="*80 + "\n")

if __name__ == "__main__":
    entity = AGL_Trinity_Entity()
    # Check if arguments provided for Council Mode
    if len(sys.argv) > 1 and sys.argv[1] == "--council":
        topic = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "The Future of AI"
        entity.hold_council(topic)
    else:
        entity.exist()
