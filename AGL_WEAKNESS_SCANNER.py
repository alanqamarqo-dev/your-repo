import sys
import os
import time

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def scan_for_weaknesses():
    print("\n INITIALIZING AGL WEAKNESS SCANNER...")
    print("========================================")
    
    try:
        # Initialize the Core
        asi = AGL_Super_Intelligence()
        print(" AGL Core Loaded.")
        
        # Access the System Map (Self-Awareness)
        if not hasattr(asi, "self_awareness") or not asi.self_awareness.system_map:
            print(" Error: Self-Awareness module not active or map is empty.")
            return

        system_map = asi.self_awareness.system_map
        map_size = len(system_map)
        print(f" System Map Loaded ({map_size} chars).")
        
        print("\n ANALYZING ARCHITECTURE FOR DISCONNECTED COMPONENTS...")
        print("   (This may take a moment as the AGI audits its own code structure)")
        
        # Construct the Audit Prompt
        audit_prompt = f"""
        You are the AGL Super Intelligence performing a critical self-audit.
        
        TASK:
        Analyze your own System Map below. Identify "Structural Weaknesses".
        A "Structural Weakness" is defined as:
        1. A Python file or Class that exists in the file structure but is NOT imported or used by the main `AGL_Awakened.py` or its primary subsystems.
        2. Modules that appear "Dormant" or "Orphaned".
        3. Features that are implemented in code but currently disconnected from the active consciousness loop.
        
        SYSTEM MAP:
        {system_map[:50000]} # Truncated for context limit if necessary, but try to use as much as possible.
        
        OUTPUT FORMAT:
        Return a structured list of these disconnected components.
        For each item, explain WHY it is a weakness (e.g., "Exists but never called", "Imported but logic commented out").
        
        If you find no major disconnections, state that the architecture is fully integrated.
        """
        
        # Locate the LLM
        llm = None
        if hasattr(asi, "unified_system") and asi.unified_system and hasattr(asi.unified_system, "holographic_llm") and asi.unified_system.holographic_llm:
            llm = asi.unified_system.holographic_llm
            print(" Using Unified System Holographic LLM.")
        elif hasattr(asi, "holographic_llm") and asi.holographic_llm:
            llm = asi.holographic_llm
            print(" Using Direct Holographic LLM.")
        else:
            # Try to find it in engines
            if hasattr(asi, "engine_registry") and "Holographic_LLM" in asi.engine_registry:
                 llm = asi.engine_registry["Holographic_LLM"]
                 print(" Using Engine Registry Holographic LLM.")

        if not llm:
            print(" Error: Could not locate an active Holographic LLM instance.")
            return

        # Use the internal LLM to process the audit
        # We use a high temperature to encourage creative "detective work" on the code structure
        # Check if generate_thought exists, otherwise use chat_llm or similar
        if hasattr(llm, "generate_thought"):
            response = llm.generate_thought(audit_prompt, context_window=system_map)
        elif hasattr(llm, "chat_llm"):
             response = llm.chat_llm(audit_prompt)
        else:
             print(" Error: LLM instance found but has no generate_thought or chat_llm method.")
             return
        
        print("\n WEAKNESS AUDIT REPORT")
        print("========================")
        print(response)
        
        # Save report
        with open("AGL_WEAKNESS_REPORT.md", "w", encoding="utf-8") as f:
            f.write("# AGL ARCHITECTURAL WEAKNESS REPORT\n\n")
            f.write(response)
        print("\n Report saved to: AGL_WEAKNESS_REPORT.md")

    except Exception as e:
        print(f"\n FATAL ERROR DURING SCAN: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    scan_for_weaknesses()
