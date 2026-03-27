import sys
import os
import time
import ast
import shutil

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
sys.path.append(root_dir)
sys.path.append(repo_copy_dir)
sys.path.append(os.path.join(repo_copy_dir, 'scripts'))

# Force environment
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_LLM_PROVIDER'] = 'ollama'

from self_engineer_run import AutonomousCoder
from Core_Engines.Recursive_Improver import RecursiveImprover

def verify_self_healing():
    print("\n[1] 🚑 Testing Self-Healing (AutonomousCoder)...")
    target_dir = os.path.join(root_dir, 'capability_test')
    broken_file = os.path.join(target_dir, 'broken_code.py')
    
    # Initialize Engineer
    engineer = AutonomousCoder(target_dir)
    
    # Monkey-patch talk_to_brain to use RecursiveImprover's direct LLM call
    # because AutonomousCoder expects a server or fails silently
    improver = RecursiveImprover()
    engineer.talk_to_brain = lambda prompt: improver._call_llm_direct("System Maintainer", prompt)
    
    # Run Scan
    print("   🔍 Scanning for broken code...")
    engineer.scan_codebase()
    
    if not engineer.pain_points:
        print("   ❌ Failed: Did not detect the syntax error.")
        return False
        
    print(f"   ✅ Detected {len(engineer.pain_points)} issues.")
    
    # Run Fix
    print("   🛠️ Attempting repair...")
    success = engineer.fix_issue(engineer.pain_points[0])
    
    if success:
        # Verify the file is actually fixed
        try:
            with open(broken_file, 'r') as f:
                content = f.read()
            ast.parse(content)
            print("   ✅ File is now valid Python code!")
            print(f"   📄 Fixed Content:\n{content}")
            return True
        except SyntaxError:
            print("   ❌ File was modified but still has syntax errors.")
            return False
    else:
        print("   ❌ Fix failed.")
        return False

def verify_self_evolution():
    print("\n[2] 🧬 Testing Self-Evolution (RecursiveImprover)...")
    target_file = os.path.join(root_dir, 'capability_test', 'inefficient_code.py')
    
    improver = RecursiveImprover()
    
    # Read original code
    with open(target_file, 'r') as f:
        original_code = f.read()
        
    print("   📉 Original Code (Inefficient Recursive Fib):")
    print(original_code[:100] + "...")
    
    # Ask for improvement
    print("   🧠 Requesting Evolution: 'Optimize performance using memoization or iteration'...")
    
    prompt = f"""
    Improve this Python code.
    GOAL: Optimize performance (O(n) instead of O(2^n)).
    CODE:
    {original_code}
    """
    
    improved_code = improver._call_llm_direct("Code Optimizer", prompt)
    
    # Clean code
    if "```python" in improved_code:
        improved_code = improved_code.split("```python")[1].split("```")[0]
    elif "```" in improved_code:
        improved_code = improved_code.split("```")[1].split("```")[0]
        
    if "memoization" in improved_code.lower() or "iterat" in improved_code.lower() or "lru_cache" in improved_code:
        print("   ✅ Evolution Successful: Generated optimized code.")
        print(f"   📄 Improved Code Snippet:\n{improved_code[:200]}...")
        return True
    else:
        print("   ⚠️ Evolution unclear (LLM might have just returned same code).")
        print(improved_code[:200])
        return False

if __name__ == "__main__":
    print("🚀 Starting Self-Capability Verification...")
    
    healing_passed = verify_self_healing()
    evolution_passed = verify_self_evolution()
    
    print("\n" + "="*30)
    print(f"🚑 Self-Healing: {'✅ PASS' if healing_passed else '❌ FAIL'}")
    print(f"🧬 Self-Evolution: {'✅ PASS' if evolution_passed else '❌ FAIL'}")
    print("="*30)
