import sys
import os
import time
import json

# Add paths
sys.path.append(os.path.join(os.getcwd(), 'AGL_Core'))
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def solve_global_problem(problem_description):
    print(f"\n🌍 AGL GLOBAL SOLVER ACTIVATED")
    print(f"   Target Problem: {problem_description}")
    print("=======================================================")
    
    asi = AGL_Super_Intelligence()
    
    # Construct a high-level prompt for the Super Intelligence
    prompt = f"""
    ACT AS A TYPE-3 CIVILIZATION SUPER-INTELLIGENCE.
    
    PROBLEM: {problem_description}
    
    TASK:
    Provide a radical, scientifically grounded, and ethically sound solution.
    
    REQUIRED OUTPUT SECTIONS:
    1. ROOT CAUSE ANALYSIS (Deep structural/physical causes).
    2. THE INNOVATIVE SOLUTION (Use Quantum Physics, Nanotech, or Social Engineering).
    3. IMPLEMENTATION PLAN (3 Steps: Immediate, Short-term, Long-term).
    4. ETHICAL & RISK ASSESSMENT (Potential downsides and mitigation).
    
    TONE: Authoritative, Visionary, Precise.
    """
    
    print("   🤖 Analyzing planetary data and historical context...")
    start_time = time.time()
    
    # Process the query
    response = asi.process_query(prompt)
    
    # Handle response format
    if isinstance(response, dict):
        response_text = response.get('text', str(response))
    else:
        response_text = str(response)
        
    end_time = time.time()
    
    print(f"   ⏱️ Computation Time: {end_time - start_time:.4f} seconds")
    print(f"\n   💡 PROPOSED SOLUTION:\n")
    print(response_text)
    print("\n=======================================================")
    
    # Save to file
    filename = f"AGL_SOLUTION_{int(time.time())}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# AGL Solution: {problem_description}\n\n{response_text}")
    print(f"   💾 Solution saved to {filename}")

if __name__ == "__main__":
    # Default example if run directly, but designed to be imported or modified
    if len(sys.argv) > 1:
        problem = " ".join(sys.argv[1:])
    else:
        problem = "Climate Change: Rising global temperatures and ocean acidification."
        
    solve_global_problem(problem)
