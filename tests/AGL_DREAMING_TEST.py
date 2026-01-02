"""
🌙 AGL DREAMING TEST (The Subconscious Protocol)
اختبار الأحلام - معالجة الذاكرة وتوليد الروابط الخفية

المطور: حسام هيكل (Hossam Heikal)
التاريخ: 29 ديسمبر 2025

الهدف: التحقق من قدرة النظام على "الحلم" (Dreaming) - أي دمج المعلومات الجديدة (الهولوغرام) مع المعرفة القديمة وتوليد رؤى جديدة أثناء "النوم".
"""

import sys
import os
import time

# Add paths
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))
sys.path.append(os.path.join(os.getcwd(), 'AGL_Core'))

try:
    from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence
except ImportError:
    from AGL_Super_Intelligence import AGL_Super_Intelligence

def run_dreaming_test():
    print("\n" + "="*60)
    print("       🌙 AGL DREAMING TEST (SUBCONSCIOUS PROTOCOL)       ")
    print("="*60)
    print("Objective: Simulate REM Sleep to consolidate 'Holographic Universe' concept.")
    print("="*60)

    # Initialize the Brain
    print("\n🔌 [INIT] Awakening Super Intelligence...")
    ai = AGL_Super_Intelligence()
    
    if not ai.dreaming:
        print("❌ [ERROR] Dreaming Engine is NOT active. Aborting.")
        return

    # 1. Inject Day's Memories (The "Residue")
    print("\n📥 [DAY] Injecting Recent Memories (Day Residue)...")
    memories = [
        "Concept: The Universe is Holographic.",
        "Objection: Bell's Theorem and Quantum Non-locality challenge 2D encoding.",
        "Insight: Consciousness might be a holographic interpretation layer.",
        "Emotion: Curiosity mixed with Skepticism (Score: 40/100)."
    ]
    
    for mem in memories:
        print(f"   -> Buffering: {mem}")
        ai.dreaming.add_to_buffer(mem)

    # 2. Initiate Sleep Cycle
    print("\n💤 [SLEEP] Initiating REM Cycle (Rapid Eye Movement)...")
    print("   ... Shutting down sensory inputs ...")
    print("   ... Activating associative cortex ...")
    time.sleep(1)
    
    # Run the cycle
    print("\n🌙 [DREAM] Entering Dream State...")
    ai.dreaming.run_dream_cycle(duration_seconds=15) # Give it time to "dream"

    print("\n" + "="*60)
    print("       🛌 WAKING UP - DREAM REPORT       ")
    print("="*60)
    print("The system has consolidated the memories. Check the logs above for 'Dream Insight'.")

if __name__ == "__main__":
    run_dreaming_test()
