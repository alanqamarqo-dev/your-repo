# artifacts/run_real_dyson_test.py
import sys
import os
import json

# Add repo-copy to path to find modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'repo-copy')))

try:
    from Scientific_Systems.Scientific_Integration_Orchestrator import ScientificIntegrationOrchestrator
    SCIENTIFIC_CHECK_ENABLED = True
except ImportError as e:
    print(f"Import Error: {e}")
    SCIENTIFIC_CHECK_ENABLED = False

def run_dyson_test():
    print("🚀 Running Real Dyson Swarm Test...")
    
    if not SCIENTIFIC_CHECK_ENABLED:
        print("❌ Scientific System not enabled.")
        return

    orchestrator = ScientificIntegrationOrchestrator()

    # محاكاة تصميم تم توليده بواسطة النظام (أو تصميم بشري)
    # يحتوي على معطيات رقمية محددة لاختبار الحسابات
    design_proposal = """
    # Project: Helios Alpha (Realistic Dyson Swarm)
    
    ## Target Star
    - Type: G-type Main Sequence (Sun-like)
    - Mass: 1.989e30 kg
    - Luminosity: 3.828e26 W
    
    ## Swarm Configuration
    - Orbit Radius: 1.0 AU (1.496e11 m)
    - Number of Satellites: 10,000,000
    - Formation: Dense Ring / Swarm
    
    ## Satellite Specifications
    - Material: Graphene-reinforced polymer
    - Density: 2200 kg/m^3
    - Dimensions: 1000m x 1000m (Area: 1,000,000 m^2)
    - Thickness: 0.005 m
    - Efficiency: 35%
    
    ## Energy & Transmission
    - Total Target Output: > 1e20 W
    - Transmission: Phased Array Microwave Beams
    
    ## Stability
    - Active control using solar sails and ion thrusters.
    """

    print("\n📄 Analyzing Design Proposal...")
    analysis = orchestrator.analyze_scientific_design(design_proposal)

    print("\n📊 Analysis Results:")
    print(f"   • Feasibility Score: {analysis['feasibility_score']:.2%}")
    print(f"   • Issues Found: {len(analysis['issues'])}")
    
    if analysis['issues']:
        print("\n   ⚠️ Issues:")
        for issue in analysis['issues']:
            print(f"     - {issue}")
    else:
        print("\n   ✅ No critical physics contradictions found.")

    print("\n🧮 Calculations & Simulation:")
    
    if analysis.get('calculations'):
        for calc in analysis['calculations']:
            for key, val in calc.items():
                print(f"   • {key}: {val}")

    if analysis.get('simulation'):
        sim = analysis['simulation']
        print("\n   ⚗️ Simulation Results:")
        print(f"     - Feasibility: {sim.get('feasibility')}")
        if 'numerical_results' in sim:
            for k, v in sim['numerical_results'].items():
                print(f"     - {k}: {v:.2e}")
        if 'issues' in sim and sim['issues']:
            print("     - Simulation Issues:")
            for i in sim['issues']:
                print(f"       * {i}")

    print("\n✅ Test Complete.")

if __name__ == "__main__":
    run_dyson_test()
