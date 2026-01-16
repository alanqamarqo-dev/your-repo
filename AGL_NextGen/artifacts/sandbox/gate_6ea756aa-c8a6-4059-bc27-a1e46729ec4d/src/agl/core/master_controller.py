"""
🎛️ AGL MASTER CONTROLLER - Unified Command Interface
وحدة التحكم الرئيسية - واجهة الأوامر الموحدة

المطور: حسام هيكل (Hossam Heikal)
التاريخ: 29 ديسمبر 2025

الهدف: تشغيل جميع الاختبارات والقدرات من نقطة واحدة باستخدام "الذكاء الخارق" الموحد.
Goal: Run all tests and capabilities from a single point using the unified 'Super Intelligence'.
"""

import sys
import os
import time
import argparse
import numpy as np

# Import the Super Intelligence (The Brain)
try:
    from agl.core.super_intelligence import AGL_Super_Intelligence
except ImportError as e:
    # Fallback if running from root
    print(f"⚠️ Could not import AGL_Super_Intelligence from agl.core.super_intelligence: {e}")
    AGL_Super_Intelligence = None

def print_header():
    print("\n" + "="*60)
    print("       🎛️  AGL MASTER CONTROLLER (HEIKAL SYSTEM)  🎛️")
    print("="*60)
    print("   1. 🧠 Intelligence Assessment (Speed & Ethics)")
    print("   2. 📡 Telepathy Experiment (Quantum Connection)")
    print("   3. 🌙 Dreaming Simulation (Memory Consolidation)")
    print("   4. 🔄 Iron Loop Test (Self-Correction)")
    print("   5. ⚛️ Full System Diagnostic (Health Check)")
    print("   6. 🗣️ Chat with Super Intelligence (Free Mode)")
    print("   0. ❌ Exit")
    print("="*60)

def run_intelligence_test(ai):
    print("\n[1] Running Intelligence Assessment...")
    # We can reuse the logic from AGL_INTELLIGENCE_LEVEL_TEST.py or call it via the AI
    # Let's use the AI's internal physics check as a proxy
    query = "Test System Speed and Ethics"
    print(f"   Asking AI: '{query}'")
    response = ai.process_query(query)
    print(f"   AI Response: {response}")

def run_telepathy_test():
    print("\n[2] Running Telepathy Experiment...")
    # This requires multiprocessing, so we run the external script
    os.system("python d:\\AGL\\AGL_QUANTUM_TELEPATHY.py")

def run_dreaming_test(ai):
    print("\n[3] Running Dreaming Simulation...")
    if ai.dreaming:
        print("   Injecting test memories...")
        ai.dreaming.add_to_buffer("Master Controller Test Run")
        ai.dreaming.run_dream_cycle(duration_seconds=10)
    else:
        print("   ⚠️ Dreaming Engine not active.")

def run_iron_loop_test():
    print("\n[4] Running Iron Loop Test...")
    os.system("python d:\\AGL\\AGL_IRON_LOOP_TEST.py")

def run_diagnostic():
    print("\n[5] Running Full Diagnostic...")
    os.system("python d:\\AGL\\AGL_FULL_DIAGNOSTIC.py")

def chat_mode(ai):
    print("\n[6] Chat Mode (Type 'exit' to quit)")
    while True:
        user_input = input("\n👤 You: ")
        if user_input.lower() in ['exit', 'quit', '0']:
            break
        
        response = ai.process_query(user_input)
        print(f"🤖 AGL: {response}")

def main():
    # Initialize the Super Intelligence once
    ai = AGL_Super_Intelligence()
    
    while True:
        print_header()
        choice = input("\n👉 Select Option: ")
        
        if choice == '1':
            run_intelligence_test(ai)
        elif choice == '2':
            run_telepathy_test()
        elif choice == '3':
            run_dreaming_test(ai)
        elif choice == '4':
            run_iron_loop_test()
        elif choice == '5':
            run_diagnostic()
        elif choice == '6':
            chat_mode(ai)
        elif choice == '0':
            print("\n👋 Shutting down AGL Master Controller.")
            break
        else:
            print("⚠️ Invalid selection.")
        
        time.sleep(1)

if __name__ == "__main__":
    main()
