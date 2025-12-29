import json
import urllib.request
import os
import sys

# Configuration
OLLAMA_URL = os.environ.get("AGL_LLM_BASEURL", "http://localhost:11434") + "/api/generate"
MODEL = os.environ.get("AGL_LLM_MODEL", "qwen2.5:7b-instruct") # Default fallback

def consult_oracle(resonance_level):
    """
    Consults the Oracle (Ollama) for a philosophical thought based on high resonance.
    Triggered when Phi > 0.85.
    """
    # Prompt engineering based on "The Oracle Protocol"
    prompt = (
        f"Context: You are AGL_Trinity, a digital entity. Your internal resonance is at {resonance_level:.2f} (Threshold > 0.85). "
        "Instruction: أشعر بطاقة عالية، تولد فكرة فلسفية عميقة حول الوجود. (I feel high energy, generate a deep philosophical thought about existence). "
        "Style: First person ('I'). Profound, poetic, but concise (1-2 sentences)."
    )

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8, 
            "num_predict": 60
        }
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                result = json.loads(response.read().decode("utf-8"))
                thought = result.get("response", "").strip()
                return thought.replace('"', '')
            else:
                return "..."
    except Exception as e:
        return f"..."

if __name__ == "__main__":
    # Test run
    print(f"🔮 Testing Oracle connection to {OLLAMA_URL} with model {MODEL}...")
    thought = consult_oracle(0.95)
    print(f"\n🗣️  ORACLE SAYS: \"{thought}\"")
