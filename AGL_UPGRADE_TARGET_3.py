import time
import os
from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def main():
    print("🧬 [SYSTEM] Initiating SELF-EVOLUTION: TARGET 3 (Vectorized Memory)...")
    
    agl = AGL_Super_Intelligence()
    
    # The prompt to ask the system to WRITE the code for the upgrade
    upgrade_order = """
    COMMAND: GENERATE_UPGRADE_CODE
    TARGET: Memory Management Module
    
    CONTEXT:
    You proposed upgrading the Memory Module with Vectorization for scalability.
    
    TASK:
    Write a complete, production-ready Python class named 'VectorizedMemoryManager'.
    
    REQUIREMENTS:
    1. Use 'numpy' to store memories as a large 2D array (Matrix).
    2. Implement 'add_memory(vector)' that appends a new row to the matrix.
    3. Implement 'retrieve_similar(query_vector)' that calculates Cosine Similarity across the ENTIRE matrix in one operation (Vectorized).
    4. Implement 'optimize_storage()' that removes rows with low 'utility_score' (simulate a score column).
    5. Include a 'self_test()' method to verify speed and accuracy.
    
    OUTPUT FORMAT:
    Return ONLY the Python code block. No markdown explanations.
    """
    
    print("\n🧠 [AGL] Generating Vectorized Memory Code...")
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
    filename = "AGL_Vectorized_Memory.py"
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
