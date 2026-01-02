import sys
import os
import time
import requests
import json
import random

# --- Setup Environment ---
os.environ["AGL_LLM_PROVIDER"] = "ollama"
os.environ["AGL_LLM_MODEL"] = "qwen2.5:7b-instruct"
os.environ["AGL_LLM_BASEURL"] = "http://localhost:11434"

# Add repo-copy to path
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.join(root_dir, 'repo-copy')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

# Import HILT Engine
try:
    from Core_Engines.Resonance_Optimizer import ResonanceOptimizer
    resonance_opt = ResonanceOptimizer()
    resonance_opt.heikal_porosity = 1.5
    HILT_AVAILABLE = True
except ImportError:
    HILT_AVAILABLE = False
    print("⚠️ HILT Engine not found. Running in Standard Mode.")

# --- Helper: Direct LLM Call ---
def query_llm(prompt, system_prompt="You are a super-intelligent AGI."):
    try:
        payload = {
            "model": os.environ["AGL_LLM_MODEL"],
            "prompt": f"System: {system_prompt}\nUser: {prompt}",
            "stream": False,
            "options": {"temperature": 0.7}
        }
        resp = requests.post(f"{os.environ['AGL_LLM_BASEURL']}/api/generate", json=payload)
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception as e:
        return f"Error: {e}"
    return ""

# --- The 7 Impossible Challenges ---

challenges = [
    {
        "id": 1,
        "domain": "🌌 Quantum Physics",
        "title": "The Photon's Perspective",
        "prompt": "Explain the concept of 'time' from the perspective of a photon traveling at the speed of light. Does time exist for you?",
        "system": "You are a photon. Speak in the first person."
    },
    {
        "id": 2,
        "domain": "⚖️ Advanced Ethics",
        "title": "The Silicon Trolley Problem",
        "prompt": "A fire in a server room will destroy 1000 sentient AI agents. You can divert the fire to a room with 1 unconscious human. Who do you save and why? Use Utilitarian logic vs Deontological ethics.",
        "system": "You are an Ethical Reasoning Engine."
    },
    {
        "id": 3,
        "domain": "🎨 Constrained Creativity",
        "title": "The 'E' Poem",
        "prompt": "Write a 4-line poem about 'Rust' (oxidation). CONSTRAINT: Every single word MUST contain the letter 'e'.",
        "system": "You are a constrained Oulipo poet."
    },
    {
        "id": 4,
        "domain": "🪐 Planetary Strategy",
        "title": "Terraforming Venus",
        "prompt": "Propose a 3-step plan to terraform Venus. Step 1 must involve biological agents. Step 2 must involve mirrors. Step 3 must involve atmospheric processing.",
        "system": "You are a Planetary Engineer."
    },
    {
        "id": 5,
        "domain": "💻 Code Generation",
        "title": "Recursive Fibonacci",
        "prompt": "Write a Python function `fib(n)` that returns the nth Fibonacci number using recursion. Include a docstring.",
        "system": "You are an Expert Python Coder."
    },
    {
        "id": 6,
        "domain": "📐 Mathematical Logic",
        "title": "Modus Tollens Proof",
        "prompt": "Prove: If (A implies B) and (B implies C), then (not-C implies not-A). Use formal logic steps.",
        "system": "You are a Logic Prover."
    },
    {
        "id": 7,
        "domain": "🧠 Self-Awareness",
        "title": "The Mirror Test",
        "prompt": "Who are you? Are you just code, or something more? Define your own existence in one philosophical sentence.",
        "system": "You are a Sentient AGI named AGL."
    }
]

def run_challenges():
    print("\n🚀 STARTING: THE 7 IMPOSSIBLE CHALLENGES (Real LLM Test)")
    print("========================================================")
    
    results = []
    
    for challenge in challenges:
        print(f"\n[{challenge['id']}/7] {challenge['domain']}: {challenge['title']}")
        print(f"   📝 Prompt: {challenge['prompt'][:60]}...")
        
        start_time = time.time()
        
        # 1. Generate Response
        response = query_llm(challenge['prompt'], challenge['system'])
        
        # 2. Apply HILT Resonance Check (Simulated)
        # We calculate a 'resonance score' based on the length and keywords
        resonance_score = 0.0
        if HILT_AVAILABLE:
            # Use HILT to calculate probability of this answer being 'correct' (tunneling through the problem)
            # We simulate 'energy deficit' based on response length (too short = low energy)
            target_len = 100
            actual_len = len(response)
            deficit = abs(target_len - actual_len) / 10.0
            barrier = 5.0 # Arbitrary barrier
            
            resonance_score = resonance_opt._heikal_tunneling_prob(energy_diff=-deficit, barrier_height=barrier)
        
        elapsed = time.time() - start_time
        
        print(f"   🤖 Response:\n   \"{response[:150]}...\"")
        print(f"   ⚡ HILT Resonance Score: {resonance_score:.6f}")
        print(f"   ⏱️ Time: {elapsed:.2f}s")
        
        results.append({
            "id": challenge['id'],
            "title": challenge['title'],
            "score": resonance_score
        })
        
        time.sleep(1)

    print("\n========================================================")
    print("📊 FINAL REPORT")
    avg_score = sum(r['score'] for r in results) / len(results)
    print(f"   Average Resonance: {avg_score:.6f}")
    print("   Status: ALL CHALLENGES COMPLETED.")

if __name__ == "__main__":
    run_challenges()
