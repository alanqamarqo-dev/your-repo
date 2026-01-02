import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

# Import the module directly to access the standalone function
import Core_Engines.Hosted_LLM as llm_module

# Force a missing model to trigger the 404 and auto-switch
os.environ['AGL_LLM_MODEL'] = 'ghost-model:99b'
os.environ['AGL_LLM_BASEURL'] = 'http://localhost:11434'

print(f"🧪 Testing Auto-Switching with missing model: {os.environ['AGL_LLM_MODEL']}")

messages = [{"role": "user", "content": "Hello, identify yourself."}]

# Call the function
result = llm_module.chat_llm(messages)

print("\n--- Result ---")
print(result)
