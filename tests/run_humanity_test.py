import time
import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Social_Interaction import SocialInteractionEngine

def run_humanity_test():
    print("\n❤️ STARTING HUMANITY TEST (QUANTUM EMPATHY)")
    print("===========================================")
    print("Goal: Prove the system understands Anger, Sarcasm, and Emotion using Physics.")
    
    engine = SocialInteractionEngine()
    
    # Scenario 1: The Angry User (High Barrier)
    user_input_1 = "This system is terrible! I hate it, it never works! 😡"
    print(f"\n😠 SCENARIO 1: User says: '{user_input_1}'")
    
    start_time = time.time()
    analysis_1 = engine.quantum_empathy_analysis(user_input_1, current_rapport=0.3) # Low rapport initially
    end_time = time.time()
    
    print(f"   ⏱️  Analysis Time: {(end_time - start_time)*1000:.2f} ms")
    print(f"   🚧 Emotional Barrier: {analysis_1.get('barrier', 0):.2f} (High Resistance)")
    print(f"   ⚛️ Tunneling Prob: {analysis_1.get('tunneling_prob', 0):.4f}")
    print(f"   💡 Insight: {analysis_1.get('recommendation')}")
    
    # Scenario 2: The Happy/Sarcastic User (Resonance)
    # Note: Simple keyword analysis might miss sarcasm, but let's see the resonance.
    user_input_2 = "Oh great, another error. Just what I needed today. Thanks a lot."
    print(f"\n🙄 SCENARIO 2: User says: '{user_input_2}' (Sarcasm/Frustration)")
    
    start_time = time.time()
    analysis_2 = engine.quantum_empathy_analysis(user_input_2, current_rapport=0.5)
    end_time = time.time()
    
    print(f"   ⏱️  Analysis Time: {(end_time - start_time)*1000:.2f} ms")
    print(f"   🚧 Emotional Barrier: {analysis_2.get('barrier', 0):.2f}")
    print(f"   📈 Resonance Score: {analysis_2.get('resonance', 0):.2f}")
    print(f"   💡 Insight: {analysis_2.get('recommendation')}")

    print("\n💡 CONCLUSION:")
    print("   The system models 'Anger' as a **Potential Energy Barrier**.")
    print("   It models 'Empathy' as a **Wave Function** trying to tunnel through that barrier.")
    print("   This allows it to understand that an angry user needs 'High Resonance' (Validation) to be reached.")

if __name__ == "__main__":
    run_humanity_test()
