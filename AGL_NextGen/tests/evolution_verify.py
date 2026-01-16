
import sys
import os

# Add src to path
project_root = r"D:\AGL\AGL_NextGen"
sys.path.insert(0, os.path.join(project_root, "src"))

from agl.engines.recursive_improver import RecursiveImprover

def run_evolution():
    print("🚀 Starting Iron Loop Evolution Test...")
    improver = RecursiveImprover()
    
    target = "agl.engines.evolution_test_engine"
    goal = "Optimize the fib method to use iteration or memoization for efficiency. Ensure type hints are added."
    
    result = improver.analyze_and_improve(target, goal, apply_changes=True)
    
    print("\n" + "="*50)
    print(f"EVOLUTION RESULT: {result.get('status')}")
    print(f"MESSAGE: {result.get('message', 'No message')}")
    print("="*50)

if __name__ == "__main__":
    run_evolution()
