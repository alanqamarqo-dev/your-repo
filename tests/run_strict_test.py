import sys
import os

# Setup paths to match AGL_Awakened.py environment
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "repo-copy"))
sys.path.append(os.path.join(current_dir, "AGL_Core"))

# Initialize Path Manager to load libraries
try:
    from AGL_Paths import PathManager
    print("✅ [SETUP] AGL Path Manager Initialized")
except ImportError as e:
    print(f"⚠️ [SETUP] Failed to import AGL_Paths: {e}")

# Import the Awakened Super Intelligence
try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError as e:
    print(f"Failed to import AGL_Super_Intelligence: {e}")
    sys.exit(1)

def run_strict_test():
    print("==================================================")
    print("       🧬 AGL STRICT TEST RUNNER 🧬")
    print("==================================================")
    
    try:
        # Instantiate the system
        print("\n[1] Instantiating AGL_Super_Intelligence...")
        asi = AGL_Super_Intelligence()
        
        # Define the strict query
        query = "Chemistry Medicine Innovation Math Writing New Algorithm Strict Test"
        print(f"\n[2] Processing Query: '{query}'")
        
        # Run the query
        response = asi.process_query(query)
        
        print("\n[3] Test Complete. Response received:")
        print("--------------------------------------------------")
        print(response)
        print("--------------------------------------------------")
        
    except Exception as e:
        print(f"\n❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_strict_test()
