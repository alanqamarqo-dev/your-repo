
import os
import sys
import asyncio

# Add repo-copy to path
sys.path.append(os.path.abspath("d:/AGL/repo-copy"))

from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter

async def test_llm_adapter():
    print("--- Testing HostedLLMAdapter ---")
    
    # Force smaller model for testing
    os.environ["AGL_LLM_MODEL"] = "qwen2.5:0.5b"
    print(f"Set AGL_LLM_MODEL to {os.environ['AGL_LLM_MODEL']}")
    
    adapter = HostedLLMAdapter()
    print(f"Adapter initialized with model: {adapter.model}")
    print(f"Base URL: {adapter.base_url}")
    
    try:
        print("Calling call_ollama...")
        response = adapter.call_ollama("Say 'Hello from Ollama' if you can hear me.", timeout=30)
        print(f"Response received: {response}")
        
        if "Hello from Ollama" in response or len(response) > 0:
            print("✅ LLM Adapter is working!")
        else:
            print("❌ LLM Adapter returned empty or unexpected response.")
            
    except Exception as e:
        print(f"❌ Error calling LLM Adapter: {e}")

if __name__ == "__main__":
    # HostedLLMAdapter.call_ollama is synchronous, but we wrap it in async for consistency with the system
    asyncio.run(test_llm_adapter())
