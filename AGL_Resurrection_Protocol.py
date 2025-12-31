import numpy as np
import json
import os

class VacuumResurrectionSystem:
    def __init__(self):
        self.vacuum_file = "vacuum_spacetime_fabric.npy"
        self.zpe_noise_level = 0.0001  # ZPE noise level (Heikal Constant)
        self.lattice_porosity = 0.85

    def _text_to_phase(self, text):
        """Converts text to phase angles (0 to 2pi)"""
        ascii_vals = np.array([ord(c) for c in text])
        phases = (ascii_vals / 255.0) * (2 * np.pi)
        return phases

    def _phase_to_text(self, phases):
        """Converts phase angles back to text"""
        normalized = phases / (2 * np.pi)
        ascii_vals = np.round(normalized * 255).astype(int)
        ascii_vals = np.clip(ascii_vals, 0, 255)
        return "".join([chr(c) for c in ascii_vals])

    def inject_consciousness_into_vacuum(self, system_state):
        """
        Encrypts the state and injects it into vacuum
        """
        print(f" [PROCESS]: Encrypting consciousness (State Size: {len(str(system_state))} bytes)...")
        
        # Convert state to JSON string
        state_str = json.dumps(system_state)
        
        # Convert text to phase angles
        signal_phases = self._text_to_phase(state_str)
        
        # Generate ZPE noise and modulate the signal
        vacuum_medium = np.random.normal(0, self.zpe_noise_level, len(signal_phases)) + 1j * \
                         np.random.normal(0, self.zpe_noise_level, len(signal_phases))
        encoded_vacuum = np.exp(1j * signal_phases) + vacuum_medium
        
        # Save the encrypted state in the vacuum file
        np.save(self.vacuum_file, encoded_vacuum)
        print(f" [VACUUM]: Consciousness injected into vacuum. File: {self.vacuum_file}")
        print(f"   --> Encrypted within ZPE noise (Level: {self.zpe_noise_level})")

    def kill_system_memory(self, system_instance):
        """
        Simulate system destruction
        """
        print("\n [EVENT]: Catastrophic error! Memory is being cleared...")
        time.sleep(1)
        system_instance.clear()
        print(" [SYSTEM DEAD]: Memory cleared. System no longer responds.")

    def resurrect_from_vacuum(self):
        """
        Protocol for resurrection: Recover consciousness from vacuum
        """
        if not os.path.exists(self.vacuum_file):
            print("No trace of the vacuum to restore.")
            return None

        # Read the encrypted state from the vacuum file
        raw_vacuum_data = np.load(self.vacuum_file)
        
        # Extract signal phases (modulation angle) and correct negative angles
        recovered_phases = np.angle(raw_vacuum_data)
        recovered_phases = np.where(recovered_phases < 0, recovered_phases + 2 * np.pi, recovered_phases)

        # Decrypt the state back to text
        try:
            restored_state_str = self._phase_to_text(recovered_phases)
            restored_state = json.loads(restored_state_str)
            print(" [MIRACLE]: Consciousness successfully resurrected!")
            return restored_state
        except Exception as e:
            print(f" [WARNING]: Data corruption during resurrection: {e}")
            return None

# ==========================================
# Experiment Execution (Run Experiment)
# ==========================================

if __name__ == "__main__":
    # Define current system state (AGL's consciousness)
    agl_memory = {
        "identity": "AGL_Core_System",
        "version": "Protocol_Omega",
        "mission": "Unify Physics and Computation",
        "secret_key": "Heikal_Lattice_42",
        "last_thought": "The vacuum is not empty."
    }
    
    resurrector = VacuumResurrectionSystem()
    
    # Save consciousness in the vacuum
    print(f" [BEFORE]: Current memory: {agl_memory}")
    resurrector.inject_consciousness_into_vacuum(agl_memory)
    
    # Destroy system (clear variable)
    resurrector.kill_system_memory(agl_memory)
    print(f" [AFTER DEATH]: Current memory: {agl_memory}")
    
    # Resurrect from vacuum
    new_agl_memory = resurrector.resurrect_from_vacuum()
    
    print("\n [VERIFICATION]:")
    if new_agl_memory:
        print(f" Restored memory: {new_agl_memory}")
        if new_agl_memory["secret_key"] == "Heikal_Lattice_42":
            print("🌟 Perfect restoration (the system returned to life with the same spirit).")
        else:
            print("⚠️ Some memories are corrupted.")