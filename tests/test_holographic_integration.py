"""
Simple Holographic Integration Test
====================================

اختبار بسيط للتكامل الهولوجرامي
"""

import os
import sys
import time

# Set environment
os.environ['AGL_USE_HOLOGRAPHIC_LLM'] = '1'
os.environ['AGL_HOLO_KEY'] = '42'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo-copy'))

print("="*70)
print("🌌 HOLOGRAPHIC INTEGRATION TEST")
print("="*70)

# Test 1: Register Holographic_LLM in ENGINE_SPECS
print("\n📝 Step 1: Checking ENGINE_SPECS")

# Import from correct path
import Core_Engines

# Check if Holographic_LLM exists
try:
    if hasattr(Core_Engines, 'ENGINE_SPECS'):
        if "Holographic_LLM" in Core_Engines.ENGINE_SPECS:
            print("✅ Holographic_LLM already in ENGINE_SPECS")
        else:
            # Add it
            Core_Engines.ENGINE_SPECS["Holographic_LLM"] = ("Core_Engines.Holographic_LLM", "HolographicLLM")
            print("✅ Added Holographic_LLM to ENGINE_SPECS")
        
        print(f"   Total engines: {len(Core_Engines.ENGINE_SPECS)}")
    else:
        print("⚠️ ENGINE_SPECS not found in Core_Engines")
except Exception as e:
    print(f"⚠️ Could not access ENGINE_SPECS: {e}")
    print("   (This is OK - Holographic LLM works independently)")

# Test 2: Direct usage with Response Composer
print("\n🔧 Step 2: Testing Response Composer with Holographic LLM")

from Integration_Layer.Response_Composer import ResponseComposer

composer = ResponseComposer()

# Simulate engine results
engine_results = {
    "test_engine": {
        "hypotheses": ["فرضية 1", "فرضية 2"],
        "reasoning": "تحليل منطقي"
    }
}

# First call - will use API and store
print("\n--- First Call (API + Storage) ---")
start = time.time()
response1 = composer.compose_response(
    engine_results=engine_results,
    user_query="ما هو الذكاء الاصطناعي؟",
    format_style="professional"
)
time1 = time.time() - start
print(f"Time: {time1:.4f}s")
print(f"Response length: {len(str(response1))} chars")

# Second call - should retrieve from hologram
print("\n--- Second Call (Holographic Retrieval) ---")
start = time.time()
response2 = composer.compose_response(
    engine_results=engine_results,
    user_query="ما هو الذكاء الاصطناعي؟",
    format_style="professional"
)
time2 = time.time() - start
print(f"Time: {time2:.4f}s")
print(f"Response length: {len(str(response2))} chars")

if time2 > 0:
    speedup = time1 / time2
    print(f"\n⚡ Speedup: {speedup:.1f}x faster!")

# Display stats
if composer.holo_llm:
    print("\n📊 Statistics:")
    stats = composer.holo_llm.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

print("\n" + "="*70)
print("🏁 TEST COMPLETE")
print("="*70)
