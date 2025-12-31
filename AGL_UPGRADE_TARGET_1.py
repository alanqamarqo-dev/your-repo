import time
import os
from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def main():
    print("🧬 [SYSTEM] Initiating SELF-EVOLUTION: TARGET 1 (Quantum Data Analysis)...")
    
    agl = AGL_Super_Intelligence()
    
    # The prompt to ask the system to WRITE the code for the upgrade
    upgrade_order = """
    COMMAND: GENERATE_UPGRADE_CODE
    TARGET: Data Analysis Module
    
    CONTEXT:
    You proposed upgrading the Data Analysis Module with Quantum Algorithms.
    
    TASK:
    Write a complete, production-ready Python class named 'QuantumDataAnalyzer'.
    
    REQUIREMENTS:
    1. Use 'numpy' for vectorization.
    2. Define real physical constants: h_bar = 1.0545718e-34.
    3. Implement a method 'analyze_dataset(data)' that:
       - Converts data points into Wave Functions (psi = exp(i * data / h_bar)).
       - Computes the 'Interference Pattern' (constructive/destructive).
       - Returns a classification based on the wave energy.
    4. Include a 'self_test()' method to verify it works.
    
    OUTPUT FORMAT:
    Return ONLY the Python code block. No markdown explanations.
    """
    
    print("\n🧠 [AGL] Generating Quantum Code...")
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
    filename = "AGL_Quantum_Data_Analysis.py"
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
