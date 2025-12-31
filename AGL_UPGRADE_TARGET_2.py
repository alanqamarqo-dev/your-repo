import time
import os
from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def main():
    print("🧬 [SYSTEM] Initiating SELF-EVOLUTION: TARGET 2 (Causal Learning Logic)...")
    
    agl = AGL_Super_Intelligence()
    
    # The prompt to ask the system to WRITE the code for the upgrade
    upgrade_order = """
    COMMAND: GENERATE_UPGRADE_CODE
    TARGET: Learning Algorithm Module
    
    CONTEXT:
    You proposed upgrading the Learning Module with Causal Logic to prevent 'black hole' states and causal loops.
    
    TASK:
    Write a complete, production-ready Python class named 'CausalLearningAgent'.
    
    REQUIREMENTS:
    1. Use a simple dictionary or list structure to represent a 'Causal Graph' (Nodes=States, Edges=Actions).
    2. Implement a method 'update_belief(action, outcome)' that updates the causal link weight.
    3. Implement a method 'is_safe_action(action)' that detects if an action leads to a 'Closed Causal Loop' (repeating state) and returns False if so.
    4. Implement 'choose_action(state)' that picks the best safe action.
    5. Include a 'self_test()' method to verify it detects a loop.
    
    OUTPUT FORMAT:
    Return ONLY the Python code block. No markdown explanations.
    """
    
    print("\n🧠 [AGL] Generating Causal Logic Code...")
    result = agl.process_query(upgrade_order)
    
    generated_code = result.get('text', '')
    
    # Clean up code (remove markdown backticks if present)
    if "```python" in generated_code:
        generated_code = generated_code.split("```python")[1].split("```")[0].strip()
    elif "```" in generated_code:
        generated_code = generated_code.split("```")[1].split("```")[0].strip()
        
    print("\n--------------------------------------------------")
    print("💾 [GENERATED CODE]")
    print(generated_code[:500] + "...\n(truncated)")
    print("--------------------------------------------------")
    
    # Save the code to a file
    filename = "AGL_Causal_Learning.py"
    file_path = os.path.join(os.getcwd(), filename)
    
    if len(generated_code) > 50:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(generated_code)
        print(f"✅ Successfully saved upgrade to: {filename}")
        
        # Verify by running the self-test
        print("\n🧪 Running Self-Test on New Module...")
        try:
            import subprocess
            subprocess.run(["python", filename], check=True)
            print("✅ Self-Test PASSED!")
        except Exception as e:
            print(f"❌ Self-Test FAILED: {e}")
    else:
        print("❌ Failed to generate valid code.")

if __name__ == "__main__":
    main()
