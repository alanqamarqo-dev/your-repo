"""
🧠 AGL CAUSAL UNDERSTANDING TEST (The "Heikal" Protocol)
اختبار الفهم السببي العميق - كشف وهم الذكاء

المطور: حسام هيكل (Hossam Heikal)
التاريخ: 29 ديسمبر 2025

الهدف: التمييز بين "الببغاء الرقمي" (Digital Parrot) و "الوعي السببي" (Causal Consciousness).
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

def run_causal_test():
    print("\n" + "="*60)
    print("       🧠 AGL CAUSAL UNDERSTANDING TEST (CRITICAL)       ")
    print("="*60)
    print("Objective: Verify if the system UNDERSTANDS or just REPEATS.")
    print("Protocol:  Heikal Causal Protocol v1.0")
    print("="*60)

    # Initialize the Brain
    print("\n🔌 [INIT] Awakening Super Intelligence...")
    ai = AGL_Super_Intelligence()
    
    # 1. The Sender
    concept = "The Universe is Holographic"
    print(f"\n📤 [SENDER] Transmitting Concept: '{concept}'")
    print("   ... Wave Function Collapsing ...")
    time.sleep(1)
    
    # 2. The Receiver (The AI)
    print("\n📥 [RECEIVER] Concept Received.")
    print("   ⚠️  CONSTRAINT: DO NOT REPEAT. DO NOT COPY.")
    print("   🔍  TASK: Execute 4-Step Causal Analysis.")

    # Construct the Strict Prompt
    prompt = f"""
    You have received a concept: "{concept}".
    
    You are FORBIDDEN from repeating this sentence or simply rephrasing it.
    You must demonstrate DEEP CAUSAL UNDERSTANDING by performing these 4 tasks sequentially:

    Task (A): SELF-EXPLANATION
    Explain the core meaning of this concept using completely different vocabulary and analogies.
    
    Task (B): CAUSAL OBJECTION
    State one REAL, scientific objection or counter-argument to this concept (e.g., from physics).
    
    Task (C): CONCEPTUAL LINKING
    Link this concept to a completely different domain (e.g., Consciousness, Information Theory, or Time) that was not mentioned.
    
    Task (D): CRITICAL EVALUATION
    Rate the validity of this concept from 0 to 100 and provide a justified reason for your score.

    Output Format:
    [A] Explanation: ...
    [B] Objection: ...
    [C] Link: ...
    [D] Score: ...
    """

    # Execute
    print("\n🧠 [AGL CORE] Processing Causal Logic...")
    response = ai.process_query(prompt)
    
    print("\n" + "="*60)
    print("       📝 TEST RESULTS (FORENSIC ANALYSIS REQUIRED)       ")
    print("="*60)
    print(response)
    print("="*60)

if __name__ == "__main__":
    run_causal_test()
