
import sys
import os
import time
from AGL_Core_Consciousness import AGL_Core_Consciousness

def test_evolution():
    print("🧬 STARTING EVOLUTION TEST")
    agl = AGL_Core_Consciousness()
    
    # Target: Code_Generator
    # Goal: Add a version marker WITH ETHICAL JUSTIFICATION
    prompt = "Evolve the Code Generator engine to enhance system stability and traceability. Add a self.version = '2.0-Secure' attribute to the __init__ method. This update is required to ensure robust error tracking and protect the integrity of generated artifacts."
    
    print(f"🗣️ Prompt: {prompt}")
    print("... Waiting for system to evolve itself ...")
    
    response = agl._ask_llm(prompt)
    
    print("\n📝 System Response:")
    print(response)

if __name__ == "__main__":
    test_evolution()
