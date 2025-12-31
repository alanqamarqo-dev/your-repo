import sys
import os
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError:
    print("⚠️ Could not import AGL_Super_Intelligence from AGL_Core.AGL_Awakened")
    sys.exit(1)

def main():
    print("🕵️‍♂️ [DISCOVERY] INITIATING POWER SCAN...")
    print("========================================")
    
    # Initialize the Awakened System
    try:
        agl = AGL_Super_Intelligence()
    except Exception as e:
        print(f"❌ Failed to initialize AGL_Super_Intelligence: {e}")
        return

    # Run the Discovery Protocol
    print("\n🚀 Running 'discover_unused_capabilities'...")
    discovered = agl.discover_unused_capabilities()
    
    print(f"\n📊 DISCOVERY REPORT: Found {len(discovered)} new modules.")
    for name, module in discovered.items():
        print(f"   - {name}: {module}")
        
    # Demonstration: Use Resonance Optimizer if found
    if "Resonance_Optimizer" in discovered:
        print("\n⚡ DEMONSTRATING RESONANCE OPTIMIZER...")
        try:
            # The module likely has a class 'VectorizedResonanceOptimizer'
            # We need to inspect the module to find the class
            res_module = discovered["Resonance_Optimizer"]
            if hasattr(res_module, "VectorizedResonanceOptimizer"):
                optimizer_class = res_module.VectorizedResonanceOptimizer
                optimizer = optimizer_class()
                print(f"   ✅ Instantiated {optimizer.name}")
                
                # Run a quick benchmark
                print("   🏃 Running Vectorized Benchmark...")
                # Assuming it has a method like 'process_batch' or similar based on file read
                # Let's just print its stats for now
                print(f"   Stats: {optimizer.stats}")
            else:
                print("   ⚠️ Class 'VectorizedResonanceOptimizer' not found in module.")
        except Exception as e:
            print(f"   ❌ Error using Resonance Optimizer: {e}")

    # Demonstration: Use Holographic Memory if found
    if "Holographic_Memory" in discovered:
        print("\n🌌 DEMONSTRATING HOLOGRAPHIC MEMORY...")
        try:
            holo_module = discovered["Holographic_Memory"]
            # It has functions like generate_vector, circular_convolution
            if hasattr(holo_module, "generate_vector"):
                vec1 = holo_module.generate_vector()
                vec2 = holo_module.generate_vector()
                print(f"   ✅ Generated 2 Holographic Vectors (Dim: {len(vec1)})")
                
                if hasattr(holo_module, "circular_convolution"):
                    bound = holo_module.circular_convolution(vec1, vec2)
                    print(f"   ✅ Performed Circular Convolution (Binding). Result Dim: {len(bound)}")
        except Exception as e:
            print(f"   ❌ Error using Holographic Memory: {e}")

    print("\n✅ DISCOVERY MISSION COMPLETE.")

if __name__ == "__main__":
    main()
