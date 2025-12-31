import time
from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def main():
    print("🔌 [SYSTEM] Initiating Activation Sequence for: SIMULATION ENGINE...")
    
    # 1. استدعاء العقل الخارق
    agl = AGL_Super_Intelligence()
    
    # 2. أمر التفعيل (باستخدام الوعي الذاتي الذي اكتسبه)
    activation_order = """
    COMMAND: ACTIVATE_DORMANT_ENGINE
    TARGET: Simulation Engine
    MODE: Sandbox (Safe Mode)
    
    TASK:
    1. Locate the 'Simulation' code using your System Map.
    2. Initialize the class 'AdvancedSimulationEngine'.
    3. Run a TEST SCENARIO: 
       "Simulate the outcome of deleting the 'AGL_Core' folder."
    4. Report the predicted consequence using Causal Logic.
    """
    
    print("🧠 [AGL] Processing Activation Command...")
    result = agl.process_query(activation_order)
    
    print("\n--------------------------------------------------")
    print("📺 [SIMULATION RESULT]")
    print(result.get('text', 'No response'))
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
