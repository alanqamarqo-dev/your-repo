import sys
import os
import json
from pathlib import Path

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Engineering_Engines.Advanced_Code_Generator import AdvancedCodeGenerator

def main():
    print("🧬 [MOTHER TEST] Initializing Advanced Code Generator (The Mother)...")
    
    mother = AdvancedCodeGenerator(parent_system_name="AGL_Prime_Test")
    
    # Define specs for a child system
    child_specs = {
        "name": "AGL_Medical_Specialist_Alpha",
        "domain": "Medicine",
        "purpose": "Assist in diagnosing rare diseases based on symptoms.",
        "software_requirements": {
            "name": "Medical_Diagnosis_System",
            "language": "python",
            "component_type": "expert_system",
            "component_spec": {
                "inference_engine": "forward_chaining",
                "knowledge_base_format": "json"
            }
        },
        "required_engines": ["Reasoning_Layer", "General_Knowledge"], # Engines to clone
        "fertile": False # This child cannot create other children
    }
    
    print(f"   👶 Requesting Birth of Child System: {child_specs['name']}")
    print(f"   📜 Purpose: {child_specs['purpose']}")
    
    # Attempt to generate child
    # This should succeed because AGL_HUMAN_CONSENT.txt is GRANTED
    child_system = mother.generate_child_agi(child_specs)
    
    if child_system and child_system.get("status") != "blocked":
        print("\n✅ [SUCCESS] Child System Born!")
        print(f"   Name: {child_system['metadata']['name']}")
        print(f"   Domain: {child_system['metadata']['domain']}")
        print(f"   Engines Cloned: {list(child_system['components']['agi_engines'].keys())}")
        
        # Save the child definition to a file
        output_path = Path("AGL_Artifacts") / "born_children"
        output_path.mkdir(parents=True, exist_ok=True)
        child_file = output_path / f"{child_specs['name']}.json"
        
        with open(child_file, "w", encoding="utf-8") as f:
            json.dump(child_system, f, indent=2, ensure_ascii=False)
            
        print(f"   💾 Child DNA saved to: {child_file}")
        
    else:
        print("\n❌ [FAIL] Child Creation Failed or Blocked.")
        if child_system:
            print(f"   Reason: {child_system.get('reason')}")

if __name__ == "__main__":
    main()
