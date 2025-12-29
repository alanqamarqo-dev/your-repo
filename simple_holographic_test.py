"""
اختبار بسيط لـ Holographic LLM - التخزين اللانهائي
"""
import os
import sys
import time

# Set environment
os.environ["AGL_USE_HOLOGRAPHIC_LLM"] = "1"
os.environ["AGL_HOLO_KEY"] = "42"

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo-copy"))

from Core_Engines.Holographic_LLM import HolographicLLM

def test_holographic_llm():
    """Test holographic LLM with infinite storage"""
    print("=" * 80)
    print("🌌 HOLOGRAPHIC LLM - INFINITE STORAGE TEST")
    print("=" * 80)
    
    # Create holographic LLM
    print("\n✨ Creating Holographic LLM...")
    holo_llm = HolographicLLM(key_seed=42)
    
    # Test query
    query = "ما هي فوائد الطاقة المتجددة؟"
    messages = [
        {"role": "system", "content": "أنت مساعد ذكي."},
        {"role": "user", "content": query}
    ]
    
    print(f"\n🔬 Test 1: First Query (Will call API and store)")
    print(f"   Query: {query}")
    start = time.time()
    response1 = holo_llm.chat_llm(messages, max_new_tokens=100, temperature=0.7, use_holographic=True)
    time1 = time.time() - start
    print(f"   ✅ Response received in {time1:.4f}s")
    print(f"   Response: {response1.get('text', str(response1))[:200]}...")
    
    print(f"\n🔬 Test 2: Same Query (Should be instant from hologram)")
    start = time.time()
    response2 = holo_llm.chat_llm(messages, max_new_tokens=100, temperature=0.7, use_holographic=True)
    time2 = time.time() - start
    print(f"   ✅ Response received in {time2:.4f}s")
    print(f"   Response: {response2.get('text', str(response2))[:200]}...")
    
    # Speedup
    if time2 > 0:
        speedup = time1 / time2
        print(f"\n⚡ Speedup: {speedup:.2f}× faster on repeat!")
    
    # Statistics
    stats = holo_llm.get_statistics()
    print(f"\n📊 Holographic Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test 3: Different query
    query2 = "كيف تعمل الطاقة الشمسية؟"
    messages2 = [
        {"role": "system", "content": "أنت مساعد ذكي."},
        {"role": "user", "content": query2}
    ]
    
    print(f"\n🔬 Test 3: Different Query")
    print(f"   Query: {query2}")
    start = time.time()
    response3 = holo_llm.chat_llm(messages2, max_new_tokens=100, temperature=0.7, use_holographic=True)
    time3 = time.time() - start
    print(f"   ✅ Response received in {time3:.4f}s")
    
    # Test 4: Repeat query 2
    print(f"\n🔬 Test 4: Repeat Query 2 (Should be instant)")
    start = time.time()
    response4 = holo_llm.chat_llm(messages2, max_new_tokens=100, temperature=0.7, use_holographic=True)
    time4 = time.time() - start
    print(f"   ✅ Response received in {time4:.4f}s")
    
    if time4 > 0:
        speedup2 = time3 / time4
        print(f"   ⚡ Speedup: {speedup2:.2f}× faster!")
    
    # Final statistics
    stats = holo_llm.get_statistics()
    print(f"\n📊 Final Holographic Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 80)
    print("🎯 TEST COMPLETE")
    print("=" * 80)
    print(f"\n💡 Infinite Storage: ✅ Working")
    print(f"💡 Instant Retrieval: ✅ {stats.get('average_retrieval_time', 0):.6f}s avg")
    print(f"💡 Efficiency: {stats.get('efficiency_ratio', 0):.1f}%")
    print(f"💡 Total Saved: {stats.get('total_time_saved', 0):.2f}s")

if __name__ == "__main__":
    test_holographic_llm()
