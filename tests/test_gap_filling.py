import sys
import os
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

from Engineering_Engines.Advanced_Code_Generator import AdvancedCodeGenerator

def test_gap_filling():
    print("🧪 Starting Gap Filling Test...")
    
    # 1. Initialize Mother System
    mother = AdvancedCodeGenerator(parent_system_name="AGL_Mother_Test")
    
    # 2. Simulate Gap Detection
    gap = "Optimizing Renewable Energy Distribution for Global Sustainability"
    domain = "Energy"
    
    print(f"🚨 Gap Detected: {gap}")
    
    # 3. Trigger Gap Filling
    specialist = mother.fill_knowledge_gap(gap, domain)
    
    if specialist:
        print("\n✅ Test Passed: Specialist Created Successfully.")
        print(f"   Name: {specialist['metadata']['name']}")
        print(f"   Ethical Score: {specialist['metadata']['heikal_integration']['ethical_score_at_birth']}")
    else:
        print("\n❌ Test Failed: Specialist Creation Failed.")

if __name__ == "__main__":
    test_gap_filling()
