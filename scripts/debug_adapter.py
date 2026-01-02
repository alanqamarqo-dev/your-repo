import os
import sys

# ensure repo root and repo-copy are importable
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter


def debug_deep_silence():
    print(">> Initializing Adapter...")
    adapter = HostedLLMAdapter()
    
    # the prompt that caused silence
    quantum_prompt = """
    ROLE: You are a Quantum Creativity Engine.
    GOAL: Generate 3 distinct hypotheses.
    FORMAT: RETURN ONLY A RAW JSON ARRAY.
    """
    
    task = {
        "question": quantum_prompt,
        "deep_mode": True,   # back to deep-mode for this probe
        "temperature": 0.8
    }
    
    print(f">> Sending Task (Deep Mode = {task['deep_mode']})...")
    
    # print everything that comes back
    try:
        resp = adapter.process_task(task, timeout_s=60)
        print("\n[RESULT RAW TYPE]:", type(resp))
        print("[RESULT CONTENT]:", resp)
        
        if isinstance(resp, dict):
            content = resp.get('content', {}) or {}
            print("\n--- Breakdown ---")
            print(f"Answer length: {len(content.get('answer') or '')}")
            print(f"Reasoning length: {len(content.get('reasoning') or '')}")
            print(f"Improved_answer present: {('improved_answer' in content and content.get('improved_answer') is not None)}")
            if 'verified' in content:
                print(f"verified keys: {list(content.get('verified').keys()) if isinstance(content.get('verified'), dict) else type(content.get('verified'))}")
    except Exception as e:
        print(f"\n[CRITICAL ERROR]: {e}")


if __name__ == "__main__":
    debug_deep_silence()
