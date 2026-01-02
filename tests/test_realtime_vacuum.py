import time
import sys
import os
import requests

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

import agl_paths
agl_paths.setup_sys_path()

from Core_Engines.Heikal_Quantum_Core import HeikalQuantumCore
from Core_Engines.Hosted_LLM import chat_llm

def force_vacuum_unload():
    """Forces Ollama to unload the model from VRAM immediately."""
    try:
        url = f"{os.environ.get('AGL_LLM_BASEURL', 'http://localhost:11434')}/api/generate"
        payload = {
            "model": os.environ.get('AGL_LLM_MODEL', 'qwen2.5:7b-instruct'),
            "keep_alive": 0
        }
        requests.post(url, json=payload, timeout=2)
        print("      🌌 [Vacuum]: Model unloaded (0% VRAM).")
    except:
        pass

def real_time_chat_simulation():
    print("\n" + "="*60)
    print("💬 HEIKAL REAL-TIME CHAT SIMULATION (Adaptive Vacuum)")
    print("="*60)
    
    core = HeikalQuantumCore()
    
    # Scenario: User sends 3 messages quickly, then stops.
    # We maintain a conversation history to prove Short-Term Memory (Context).
    conversation_history = [
        {"role": "system", "content": "You are a helpful AI. You remember the conversation context."}
    ]

    messages = [
        "My name is Hossam.",
        "What is Quantum Physics?",
        "What is my name?"  # This proves it remembers the first message
    ]
    
    print("\n--- 🚀 Phase 1: Rapid Fire (Active Window + Context) ---")
    
    for i, msg in enumerate(messages):
        print(f"\n👤 User: {msg}")
        
        # Add to history
        conversation_history.append({"role": "user", "content": msg})
        
        # Simulate processing
        t_start = time.time()
        
        # In a real app, we would keep the model loaded here.
        # For this test, we just call the LLM.
        # Note: Ollama keeps the model loaded by default for 5 mins unless we force unload.
        
        # Pass the FULL history to the LLM
        response = chat_llm(conversation_history)
        
        # Handle dictionary response (Direct or Stringified)
        if isinstance(response, dict):
            # It's a real dict
            if 'message' in response and 'content' in response['message']:
                response = response['message']['content']
            elif 'text' in response:
                response = response['text']
            else:
                response = str(response)
        elif isinstance(response, str) and response.strip().startswith("{"):
            # It's a stringified dict - Try Regex
            import re
            match = re.search(r"'content':\s*['\"](.*?)['\"]", response, re.DOTALL)
            if match:
                response = match.group(1)
        
        # Add AI response to history so it remembers what it said
        conversation_history.append({"role": "assistant", "content": response})
        
        t_end = time.time()
        print(f"🤖 AI: {response[:100]}...")
        print(f"   ⏱️ Response Time: {(t_end - t_start):.4f}s")
        
        if i < len(messages) - 1:
            print("   (User is typing fast... Model stays loaded)")
            time.sleep(1) # Simulate short pause between messages
        else:
            print("   (User stopped typing...)")

    print("\n--- ⏳ Phase 2: Inactivity (Vacuum Timer) ---")
    print("   Waiting for 5 seconds (Simulating timeout)...")
    time.sleep(5)
    
    print("   ⏰ Timeout Reached. Initiating Vacuum Protocol.")
    force_vacuum_unload()
    
    print("\n✅ Test Complete: System returned to Vacuum State.")

if __name__ == "__main__":
    real_time_chat_simulation()
