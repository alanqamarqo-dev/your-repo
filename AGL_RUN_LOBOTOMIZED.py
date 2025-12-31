import subprocess
import sys
import time
import os

def run_test():
    print("🧪 Testing the 'Improved' (Lobotomized) System...")
    
    script_path = os.path.join("AGL_Core", "AGL_Awakened_TEST.py")
    
    # Complex query requiring math, physics, and reasoning
    complex_query = "Calculate the diffusion coefficient of a gold nanoparticle (radius 50nm) in water at 37C using the Stokes-Einstein equation. Then explain the quantum implications."
    
    print(f"📝 Query: {complex_query}")
    print("-" * 50)
    
    # Start the process
    process = subprocess.Popen(
        [sys.executable, script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.getcwd()
    )
    
    try:
        # Send input and get output
        # We send the query, then 'exit' to break the loop
        input_str = f"{complex_query}\nexit\n"
        stdout, stderr = process.communicate(input=input_str, timeout=30)
        
        print("📤 OUTPUT:")
        print(stdout)
        
        if stderr:
            print("⚠️ ERRORS:")
            print(stderr)
            
    except subprocess.TimeoutExpired:
        process.kill()
        print("❌ Process timed out.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_test()
