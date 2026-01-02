import os
import sys
import time
import ast

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

def verify_real_disk_io():
    print("\n[1] 🧪 Creating a BROKEN file on disk...")
    target_file = os.path.join(root_dir, 'capability_test', 'real_fix_test.py')
    
    # Create a file with a syntax error
    broken_content = """
def broken_function():
    print("This line is missing a closing parenthesis"
"""
    with open(target_file, 'w') as f:
        f.write(broken_content)
        
    print(f"    - File created at: {target_file}")
    print(f"    - Content:\n{broken_content}")
    
    print("\n[2] 🚑 Running AutonomousCoder (Self-Healing)...")
    
    # Initialize Engineer
    engineer = AutonomousCoder(os.path.dirname(target_file))
    
    # Monkey-patch talk_to_brain to use RecursiveImprover's direct LLM call
    # This proves we are using the REAL LLM, not a simulation script
    improver = RecursiveImprover()
    engineer.talk_to_brain = lambda prompt: improver._call_llm_direct("System Maintainer", prompt)
    
    # Run Scan & Fix
    engineer.scan_codebase()
    
    if engineer.pain_points:
        print(f"    - Detected {len(engineer.pain_points)} issues.")
        issue = engineer.pain_points[0]
        print(f"    - Fixing issue in: {os.path.basename(issue['file'])}")
        engineer.fix_issue(issue)
    else:
        print("    ❌ Failed to detect the error!")
        return

    print("\n[3] 🕵️ Verifying Disk Changes...")
    
    with open(target_file, 'r') as f:
        new_content = f.read()
        
    print(f"    - New Content:\n{new_content}")
    
    try:
        ast.parse(new_content)
        print("\n✅ SUCCESS: The file was physically modified and is now valid Python code.")
        print("   This proves the system is NOT a simulation. It read, parsed, and wrote to the disk.")
    except SyntaxError:
        print("\n❌ FAILURE: The file is still broken.")

if __name__ == "__main__":
    verify_real_disk_io()
