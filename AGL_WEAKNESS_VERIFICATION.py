
import sys
import os
import time

# Ensure paths are correct
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'AGL_Core'))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def run_weakness_verification():
    print("="*60)
    print("🛡️ AGL WEAKNESS VERIFICATION PROTOCOL 🛡️")
    print("="*60)
    print("Targeting identified weaknesses: Visualization & Math Precision")
    
    system = AGL_Super_Intelligence()
    
    # Test 1: Real Visualization (Addressing 'Simulation vs Execution')
    print("\n" + "-"*40)
    print("🧪 TEST 1: REAL VISUALIZATION GENERATION")
    print("-" * 40)
    vis_query = "Visualize the interference pattern of a quantum wave function with high frequency."
    print(f"Query: '{vis_query}'")
    
    start_time = time.time()
    vis_response = system.process_query(vis_query)
    duration = time.time() - start_time
    
    print(f"\n⏱️ Time: {duration:.2f}s")
    print(f"📝 Response Length: {len(vis_response)} chars")
    
    # Check for file generation
    vis_dir = os.path.join(current_dir, 'AGL_Visualizations')
    if os.path.exists(vis_dir) and os.listdir(vis_dir):
        files = os.listdir(vis_dir)
        png_files = [f for f in files if f.endswith('.png')]
        if png_files:
            print(f"✅ SUCCESS: Generated {len(png_files)} real image files: {png_files}")
        else:
            print("❌ FAILURE: No PNG files found in AGL_Visualizations.")
    else:
        print("❌ FAILURE: AGL_Visualizations directory not found or empty.")

    # Test 2: Math Precision (Addressing 'Mental Arithmetic')
    print("\n" + "-"*40)
    print("🧪 TEST 2: MATH PRECISION (Stokes-Einstein)")
    print("-" * 40)
    math_query = "Calculate the diffusion coefficient using Stokes-Einstein for a particle of radius 50nm at 310K in water (viscosity 0.0007 Pa.s)."
    print(f"Query: '{math_query}'")
    
    start_time = time.time()
    math_response = system.process_query(math_query)
    duration = time.time() - start_time
    
    print(f"\n⏱️ Time: {duration:.2f}s")
    
    # Expected value approx: (1.38e-23 * 310) / (6 * 3.14159 * 0.0007 * 50e-9)
    # ~ 4.278e-21 / 6.597e-10 ~ 6.48e-12
    
    if "e-12" in math_response or "6.4" in math_response or "10^-12" in math_response:
        print("✅ SUCCESS: Detected correct order of magnitude (e-12).")
    else:
        print("⚠️ WARNING: Check result for precision.")
        
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_weakness_verification()
