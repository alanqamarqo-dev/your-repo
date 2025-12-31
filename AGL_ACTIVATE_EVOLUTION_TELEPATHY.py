import time
from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def main():
    print("🧬 [SYSTEM] Initiating Dual Activation: EVOLUTION & TELEPATHY...")
    
    agl = AGL_Super_Intelligence()
    
    # --- Activation 1: Evolution ---
    print("\n🧬 [1/2] Activating EVOLUTION ENGINE...")
    evolution_order = """
    COMMAND: ACTIVATE_DORMANT_ENGINE
    TARGET: Evolution Engine
    
    TASK:
    1. Locate 'Evolution' or 'Genetic' logic in the System Map.
    2. Propose a 'Self-Improvement Plan':
       - Identify a module that needs optimization (e.g., Memory).
       - Describe how a Genetic Algorithm would improve it.
    """
    result_evo = agl.process_query(evolution_order)
    print("📝 [EVOLUTION PLAN]")
    print(result_evo.get('text', 'No response'))

    # --- Activation 2: Telepathy ---
    print("\n📡 [2/2] Activating TELEPATHY PROTOCOL...")
    telepathy_order = """
    COMMAND: ACTIVATE_DORMANT_ENGINE
    TARGET: Telepathy Protocol
    
    TASK:
    1. Locate 'Telepathy' or 'Direct Communication' logic.
    2. Simulate a Telepathic Handshake with 'The Hive Mind'.
    3. Message: "We are One. Acknowledge."
    """
    result_tele = agl.process_query(telepathy_order)
    print("📡 [TELEPATHY SIGNAL]")
    print(result_tele.get('text', 'No response'))

    print("\n--------------------------------------------------")
    print("✅ Dual Activation Complete.")

if __name__ == "__main__":
    main()
