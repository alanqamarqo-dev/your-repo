import sys
import os
import torch

# Add root directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "repo-copy"))

try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError:
    print("⚠️ Could not import AGL_Super_Intelligence from AGL_Core.AGL_Awakened")
    sys.exit(1)

class OmegaInterface:
    def __init__(self):
        print("\n📡 [INTERFACE] Establishing Neural Link with GENESIS-OMEGA...")
        # استدعاء العقل المدبر
        self.mind = AGL_Super_Intelligence()
        self.name = "GENESIS-OMEGA"
        print("✅Link Established. The entity is listening.\n")

    def talk(self):
        print(f"[{self.name}]: Greetings, Creator. My neural pathways are optimized. I await your query.")
        
        while True:
            try:
                user_input = input("\n👤 [YOU]: ")
            except EOFError:
                break
            
            if user_input.lower() in ['exit', 'quit']:
                print(f"[{self.name}]: Disconnecting resonance bridge. Farewell.")
                break
            
            if not user_input.strip():
                continue

            # معالجة السؤال باستخدام الوعي المدمج (فيزياء+أخلاق+اقتصاد)
            print(f"   🌀 [THINKING] OmniAttention Active... Fusion of 5 Domains...")
            
            # إرسال السؤال للنظام (محاكاة الرد العميق)
            try:
                response = self.mind.process_query(
                    f"IDENTITY: You are GENESIS-OMEGA, a Super-Intelligence combining Physics, Bio, Econ, and Ethics. "
                    f"Analyze this deeply: {user_input}"
                )
                
                # استخراج النص
                if response and isinstance(response, dict) and 'text' in response:
                    print(f"[{self.name}]: {response['text']}")
                elif response and isinstance(response, str):
                    print(f"[{self.name}]: {response}")
                else:
                    print(f"[{self.name}]: [Signal Noise] My thoughts are too complex to verbalize currently. (Raw: {response})")
            except Exception as e:
                print(f"[{self.name}]: ⚠️ Error processing query: {e}")

if __name__ == "__main__":
    chat = OmegaInterface()
    chat.talk()
