import sys
import os

# Add repo-copy to path so we can import Core_Engines
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

try:
    from Core_Engines.Causal_Graph import CausalGraphEngine
    
    print("1. Initialization Check:")
    engine = CausalGraphEngine()
    print("   - Engine initialized successfully.")

    print("\n2. Processing Check (English):")
    text_en = "High temperature causes evaporation. Rain leads to wet ground."
    result_en = engine.process_task({"text": text_en})
    print(f"   - Input: '{text_en}'")
    print(f"   - Extracted Edges: {result_en.get('edges')}")

    print("\n3. Processing Check (Arabic):")
    text_ar = "ارتفاع الحرارة يسبب التبخر. المطر يؤدي إلى بلل الأرض."
    result_ar = engine.process_task({"text": text_ar})
    print(f"   - Input: '{text_ar}'")
    print(f"   - Extracted Edges: {result_ar.get('edges')}")

    if result_en.get('edges') or result_ar.get('edges'):
        print("\nResult: The Causal Graph Engine is WORKING.")
    else:
        print("\nResult: The Causal Graph Engine is NOT extracting edges correctly.")

except Exception as e:
    print(f"\nResult: Failed with error: {e}")
