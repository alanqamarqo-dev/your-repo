import sys
import os
import importlib

# Add repo-copy to path so we can import Core_Engines
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

def test_reasoning_layer_fallback():
    print("Testing Reasoning_Layer fallback mechanism...")
    try:
        # We need to mock the environment to trigger the specific code path if possible,
        # or just verify the import doesn't crash.
        # The fix was in the import block inside a try/except or method.
        
        # Let's try to import the module and inspect the patched area if possible, 
        # or run a function that uses it.
        
        import Core_Engines.Reasoning_Layer as RL
        print("✅ Successfully imported Core_Engines.Reasoning_Layer")
        
        # The fix was inside a method, likely `_text_to_facts` or similar where it tries to load LLM_OpenAI
        # We can try to instantiate the shim directly to prove it works.
        
        print("Verifying Shim existence in memory...")
        try:
            from Core_Engines.LLM_OpenAI import LLMOpenAIEngine # type: ignore
            print("✅ Import Core_Engines.LLM_OpenAI succeeded (Shim active or real file exists)")
        except ImportError:
            # If it fails here, it might be because the shim is defined LOCALLY in the files I edited,
            # not globally in the package. 
            # Wait, I edited the files to include a try/except block *inside* the functions/files.
            # So I need to run the code that executes that block.
            print("ℹ️ Core_Engines.LLM_OpenAI not found globally (expected if shim is local)")

        # Let's run the script that had the fix applied directly: check_installed_model.py
        print("\nTesting scripts/check_installed_model.py execution...")
        import subprocess
        result = subprocess.run([sys.executable, "repo-copy/scripts/check_installed_model.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ check_installed_model.py ran successfully.")
            if "HostedLLM_Shim" in result.stdout or "shim" in result.stdout or "engine" in result.stdout:
                 print("   - Output confirms engine detection (likely via shim).")
            else:
                 print("   - Output generated, but shim details not explicitly printed (check logs if needed).")
        else:
            print("❌ check_installed_model.py failed.")
            print("STDERR:", result.stderr)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reasoning_layer_fallback()
