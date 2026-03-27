import sys
import os
sys.path.append(r"D:\AGL\AGL_NextGen\src")

from agl.engines.advanced_meta_reasoner import AdvancedMetaReasonerEngine

def verify():
    engine = AdvancedMetaReasonerEngine()
    concepts = ["Chaos", "Order", "Gravity", "Time"]
    print(f"Input Concepts: {concepts}")
    
    result = engine.recursive_meta_abstraction(concepts)
    print("\nGenerated Result:")
    print(result)
    
    if result.get("higher_order_principle") == "Universal_Balance":
        print("\n❌ STILL USING PLACEHOLDER")
    else:
        print(f"\n✅ DYNAMIC RESPONSE: {result.get('higher_order_principle')}")

if __name__ == "__main__":
    verify()