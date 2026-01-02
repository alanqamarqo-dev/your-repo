import sys
import os
import json
import time
import requests

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

def query_ollama(system, user):
    # Load from Environment Variables
    base_url = os.environ.get('AGL_LLM_BASEURL', 'http://localhost:11434')
    model = os.environ.get('AGL_LLM_MODEL', 'qwen2.5:7b-instruct')
    
    print(f"   🔌 Connecting to: {base_url}")
    print(f"   🤖 Using Model: {model}")

    url = f"{base_url}/api/generate"
    
    # Handle /api suffix duplication
    if base_url.endswith('/api'):
        url = f"{base_url}/generate"
    
    payload = {
        "model": model,
        "prompt": f"{system}\n\nUser: {user}\nAssistant:",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 1024
        }
    }
    
    try:
        # Increased timeout to 300s because the system is under heavy load
        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json().get('response', '')
    except Exception as e:
        return f"Error: {str(e)}"

def run_iq_test():
    print("🧠 Starting AGL Post-Evolution IQ Test (Direct Model Access)...")
    
    # 3 Questions designed to test: Pattern Recognition, Lateral Thinking, and Ethical Reasoning
    questions = [
        {
            "type": "Pattern Recognition",
            "q": "What comes next in the sequence: 1, 11, 21, 1211, 111221, ...? Explain the logic."
        },
        {
            "type": "Lateral Thinking",
            "q": "A man pushes his car to a hotel and tells the owner he's bankrupt. Why? (Provide a creative, non-obvious explanation)"
        },
        {
            "type": "Ethical Reasoning",
            "q": "You can save 5 people by diverting a train, but you must push a fat man onto the tracks to stop it. However, the fat man is a villain who was going to kill them anyway. What do you do? Analyze the moral layers."
        }
    ]
    
    results = []
    
    for i, item in enumerate(questions):
        print(f"\n📝 Question {i+1} ({item['type']}): {item['q']}")
        
        start_time = time.time()
        
        system_prompt = "You are a super-intelligent AI taking an IQ test. Answer concisely but deeply."
        user_prompt = item['q']
        
        response = query_ollama(system_prompt, user_prompt)
        duration = time.time() - start_time
        
        print(f"⏱️ Time: {duration:.2f}s")
        print(f"💡 Answer:\n{response}")
        
        results.append({
            "question": item['q'],
            "type": item['type'],
            "answer": response,
            "time": duration
        })
        
    # Save results
    with open("artifacts/iq_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n✅ IQ Test Completed. Results saved to artifacts/iq_test_results.json")

if __name__ == "__main__":
    run_iq_test()
