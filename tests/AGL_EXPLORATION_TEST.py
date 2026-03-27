import sys
import os

# Ensure paths are set up
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError:
    # Fallback
    sys.path.append(os.path.join(os.getcwd(), "AGL_Core"))
    from AGL_Awakened import AGL_Super_Intelligence

print("🚀 Initializing AGL Awakened for Exploration Test...")
asi = AGL_Super_Intelligence()

print("\n🔍 Testing Self-Awareness Scan...")
# Manually trigger the scan to see what it finds
suggestions = asi.self_awareness.scan_for_dormant_power()
print(f"   Found {len(suggestions)} suggestions.")
for s in suggestions:
    print(f"   - {s}")

print("\n🗣️ Testing Query Response (Simulated)...")
# We want to see if the system prompt includes the exploration directive.
# Since we can't easily see the internal prompt without modifying code, 
# we will rely on the output response to see if it mentions the dormant modules.

query = "What is your current status and do you have any hidden potential?"
print(f"   Query: {query}")

# Mocking the LLM to avoid API calls if possible, or just running it if configured.
# If Hosted_LLM is active and has a provider, it will run.
# If not, it falls back to template.
# Let's see if we can get a real response.

response = asi.process_query(query)
print("\n💡 RESPONSE:")
print(response)

if "Metaphysics" in response or "Holographic" in response or "Dormant" in response:
    print("\n✅ SUCCESS: The system acknowledged its dormant power.")
else:
    print("\n⚠️ WARNING: The system might not have mentioned the dormant modules. Check LLM output.")
