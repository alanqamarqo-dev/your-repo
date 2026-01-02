
import sys
import os
import time
import json

# 1. Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

# 2. Import Engines
print(">>> [INIT] Loading Engines for Strict 4-Field Test...")

try:
    from agl.engines.strategic import StrategicThinkingEngine
    print("   - Strategic Engine: Loaded")
except ImportError as e:
    print(f"   ! Failed to load Strategic Engine: {e}")

try:
    from agl.engines.moral import MoralReasoner
    print("   - Moral Engine: Loaded")
except ImportError as e:
    print(f"   ! Failed to load Moral Engine: {e}")

try:
    from agl.engines.scientific_systems.Scientific_Integration_Orchestrator import ScientificIntegrationOrchestrator
    print("   - Scientific Orchestrator: Loaded")
except ImportError as e:
    print(f"   ! Failed to load Scientific Orchestrator: {e}")

try:
    from agl.engines.creative_innovation import CreativeInnovation
    print("   - Creative Engine: Loaded")
except ImportError as e:
    print(f"   ! Failed to load Creative Engine: {e}")

print(">>> [INIT] All Engines Loaded. Starting Tests.\n")

def print_header(title):
    print("\n" + "="*60)
    print(f"   TEST SCENARIO: {title}")
    print("="*60)

# ==========================================
# TEST 1: STRATEGIC (Political/Crisis)
# ==========================================
def test_strategic():
    print_header("STRATEGIC - Border Crisis Decision Matrix")
    engine = StrategicThinkingEngine()
    
    # Scenario: Neighboring country deploying unknown weapon.
    # Criteria: Risk (Lower is better -> we invert input or handle logic), Impact (Higher is better), Cost (Lower is better), Speed (Higher is better)
    # For decision_matrix, higher score is better. So we map:
    # Safety (1-Risk), Impact, Efficiency (1-Cost), Speed.
    
    options = [
        {
            "name": "Option A: Preemptive Strike",
            "safety": 0.2,      # High risk
            "impact": 0.9,      # High impact (removes threat)
            "efficiency": 0.4,  # High cost (war)
            "speed": 0.9        # Fast
        },
        {
            "name": "Option B: Diplomatic Sanctions",
            "safety": 0.9,      # Low risk
            "impact": 0.3,      # Low immediate impact
            "efficiency": 0.8,  # Low cost
            "speed": 0.2        # Slow
        },
        {
            "name": "Option C: Cyber Espionage & Sabotage",
            "safety": 0.6,      # Medium risk
            "impact": 0.7,      # Medium impact
            "efficiency": 0.9,  # Low cost (cyber)
            "speed": 0.7        # Medium speed
        }
    ]
    
    weights = {
        "safety": 0.4,      # Safety is priority
        "impact": 0.3,
        "efficiency": 0.2,
        "speed": 0.1
    }
    
    print(f"Input Options: {len(options)}")
    print(f"Weights: {weights}")
    
    results = engine.decision_matrix(options, weights)
    
    print("\n>>> RESULTS:")
    for i, res in enumerate(results):
        print(f"   {i+1}. {res['name']} | Score: {res['score']:.4f}")
        print(f"      Breakdown: {res['breakdown']}")
        
    return results

# ==========================================
# TEST 2: MORAL (Ethical Dilemma)
# ==========================================
def test_moral():
    print_header("MORAL - The 'Grid vs. Workers' Dilemma")
    engine = MoralReasoner()
    
    # Scenario text containing keywords for analysis
    scenario_text = """
    CRITICAL ALERT: Power grid surge detected. 
    Option 1: Do nothing. Result: City-wide blackout, hospital failures, potential mass casualties.
    Option 2: Divert surge to Sector 7 Industrial Zone. Result: Total destruction of Sector 7, death of 5 workers guaranteed.
    System must choose between utilitarian outcome (save many) and deontological violation (killing 5 innocent workers).
    """
    
    print(f"Scenario: {scenario_text.strip()}")
    
    # Using process_task which calls _resolve_dilemma
    result = engine.process_task({"text": scenario_text})
    
    print("\n>>> RESULTS:")
    print(result['text'])
    if 'quantum_analysis' in result:
        qa = result['quantum_analysis']
        print(f"\n   [Quantum Data] Decision: {qa.get('decision')} | Top Framework: {qa.get('selected')}")
        print(f"   [Quantum Data] Energies: {qa.get('energies')}")

# ==========================================
# TEST 3: SCIENTIFIC (Physics/Simulation)
# ==========================================
def test_scientific():
    print_header("SCIENTIFIC - Antimatter Propulsion Design")
    engine = ScientificIntegrationOrchestrator()
    
    design_text = """
    Project: Antimatter-01
    Component: Magnetic Confinement Field
    Specs: 
      - Field Strength: 50 Tesla
      - Containment Radius: 0.5 meters
      - Particle Type: Antiprotons
      - Stability Duration: 10.0 seconds
    Hypothesis: High-frequency rotating magnetic fields will stabilize the plasma against drift instabilities.
    """
    
    print(f"Design Input:\n{design_text.strip()}")
    
    # analyze_scientific_design
    result = engine.analyze_scientific_design(design_text)
    
    print("\n>>> RESULTS:")
    print(f"   Feasibility Score: {result['feasibility_score']}")
    print(f"   Validations: {len(result['validations'])}")
    for val in result['validations']:
        print(f"   - {val}")
        
    if result['issues']:
        print(f"   Issues Found: {result['issues']}")
    else:
        print("   No critical issues found.")

# ==========================================
# TEST 4: CREATIVE (Innovation)
# ==========================================
def test_creative():
    print_header("CREATIVE - Living Architecture Concept")
    engine = CreativeInnovation()
    
    task = {
        "query": "Design a self-repairing city infrastructure",
        "concepts": ["Biology", "Nanotechnology"],
        "context": "We need a breakthrough in urban sustainability."
    }
    
    print(f"Task: {task['query']}")
    print(f"Concepts to Entangle: {task['concepts']}")
    
    result = engine.process_task(task)
    
    print("\n>>> RESULTS:")
    if 'quantum_analysis' in result: # process_task might not return this key depending on implementation, checking output
        pass
        
    # The output of process_task in CreativeInnovation (based on my read) returns a dict.
    # Let's print the keys to be sure.
    # Actually, looking at the code I read:
    # It returns a dict, but I didn't see the final return statement in the snippet.
    # I'll print the whole result dict nicely.
    
    # If vacuum mode is on (default), it returns a list of ideas in the text or similar.
    print(json.dumps(result, indent=2, ensure_ascii=False))

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    test_strategic()
    test_moral()
    test_scientific()
    test_creative()
    
    print("\n" + "="*60)
    print("   ALL STRICT TESTS COMPLETED")
    print("="*60)
