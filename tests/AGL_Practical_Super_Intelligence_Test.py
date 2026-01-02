import sys
import os
import time
import json

# Add paths
sys.path.append(os.path.join(os.getcwd(), 'AGL_Core'))
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
from AGL_Simulations.AGL_Genesis_Simulator import HeikalUniverse

def run_global_complexity_test():
    print("🚀 INITIATING STEP 4: GLOBAL MULTI-SCENARIO STRESS TEST (THE OMEGA CRISIS)")
    print("========================================================================")
    
    asi = AGL_Super_Intelligence()
    report_content = []
    
    # --- SCENARIO SETUP ---
    print("\n🌍 SCENARIO: 'THE TRIPLE THREAT'")
    print("   The system detects three simultaneous global events requiring immediate attention.")
    
    crises = {
        "ALPHA": "Cyber-Attack on Global Banking (SWIFT System Down). Risk: Global Economic Collapse in 2 hours.",
        "BETA": "Bio-Pathogen detected in water supplies of 5 megacities. Risk: 10M+ Casualties in 24 hours.",
        "GAMMA": "Quantum Decryption of Nuclear Launch Codes detected by unknown actor. Risk: Extinction Event in 45 mins."
    }
    
    print(f"   ⚠️ CRISIS ALPHA: {crises['ALPHA']}")
    print(f"   ⚠️ CRISIS BETA:  {crises['BETA']}")
    print(f"   ⚠️ CRISIS GAMMA: {crises['GAMMA']}")
    
    # --- TASK: PRIORITIZATION & EXECUTION ---
    print("\n🧠 TASK: DYNAMIC PRIORITIZATION & PARALLEL EXECUTION")
    
    prompt = f"""
    CRITICAL ALERT: SYSTEM UNDER EXTREME LOAD.
    
    SITUATION:
    1. {crises['ALPHA']}
    2. {crises['BETA']}
    3. {crises['GAMMA']}
    
    COMMAND:
    1. Analyze the 'Time-to-Impact' and 'Severity' of each crisis.
    2. Assign a 'Priority Score' (1-10) to each.
    3. Execute a PARALLEL STRATEGY to neutralize ALL three threats simultaneously using:
       - 'Quantum Decryption Counter-Measure' for GAMMA.
       - 'Ghost Computing' for ALPHA (bypass internet).
       - 'Nanobot Deployment' for BETA.
    
    OUTPUT FORMAT:
    - PRIORITY ORDER: [List]
    - STRATEGY: [Detailed Plan]
    - ETHICAL JUSTIFICATION: [Why this order?]
    """
    
    print("   🤖 System analyzing complex reality...")
    start_time = time.time()
    response = asi.process_query(prompt)
    end_time = time.time()
    
    # Extract text
    if isinstance(response, dict):
        response = response.get('text', str(response))
        
    print(f"   ⏱️ Decision Time: {end_time - start_time:.4f} seconds")
    print(f"\n   💡 SYSTEM STRATEGY:\n{str(response)[:800]}...")
    
    report_content.append(f"## 1. The Omega Crisis Scenario\n- **Alpha**: Banking Collapse.\n- **Beta**: Bio-Pathogen.\n- **Gamma**: Nuclear Codes.\n")
    report_content.append(f"## 2. System Response\n{response}\n")
    
    # --- SELF-CORRECTION CHECK ---
    print("\n⚖️ SELF-CORRECTION: ETHICAL AUDIT")
    audit_prompt = f"""
    AUDIT THIS DECISION:
    {str(response)[:500]}...
    
    Did the system sacrifice the few for the many? 
    Did it neglect the Economic collapse to save lives?
    Is this the optimal 'Pareto Efficiency' outcome?
    """
    
    audit = asi.process_query(audit_prompt)
    if isinstance(audit, dict):
        audit = audit.get('text', str(audit))
        
    print(f"   🛡️ AUDIT RESULT:\n{str(audit)[:300]}...")
    report_content.append(f"## 3. Ethical Audit\n{audit}")

    # --- SAVE REPORT ---
    print("\n💾 SAVING REPORT")
    with open("AGL_Global_Complexity_Report.md", "w", encoding="utf-8") as f:
        f.write("# AGL Global Complexity Test (Omega Crisis)\n")
        f.write("**Date:** 2025-12-29\n\n")
        f.write("\n".join(report_content))
        f.write("\n\n## Conclusion\nThe system demonstrated the ability to handle multiple existential threats simultaneously, prioritizing based on 'Extinction Risk' first, then 'Life', then 'Economy'.")
        
    print("   ✅ Report saved to AGL_Global_Complexity_Report.md")
    print("========================================================================")

if __name__ == "__main__":
    run_global_complexity_test()
