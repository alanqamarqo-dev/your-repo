import sys
import os

# Add repo-copy to path
repo_copy = os.path.abspath(os.path.join(os.getcwd(), 'repo-copy'))
sys.path.insert(0, repo_copy)

print(f"Checking imports from: {repo_copy}")

try:
    from Scientific_Systems.Automated_Theorem_Prover import AutomatedTheoremProver
    print("✅ AutomatedTheoremProver imported successfully")
except ImportError as e:
    print(f"❌ Failed to import AutomatedTheoremProver: {e}")

try:
    from Scientific_Systems.Scientific_Research_Assistant import ScientificResearchAssistant
    print("✅ ScientificResearchAssistant imported successfully")
except ImportError as e:
    print(f"❌ Failed to import ScientificResearchAssistant: {e}")

try:
    from Scientific_Systems.Hardware_Simulator import HardwareSimulator
    print("✅ HardwareSimulator imported successfully")
except ImportError as e:
    print(f"❌ Failed to import HardwareSimulator: {e}")

try:
    from Scientific_Systems.Integrated_Simulation_Engine import IntegratedSimulationEngine
    print("✅ IntegratedSimulationEngine imported successfully")
except ImportError as e:
    print(f"❌ Failed to import IntegratedSimulationEngine: {e}")
