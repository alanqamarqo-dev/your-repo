import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate

# Add repo-copy to path (The Correct Path)
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

# Try to import QuantumSimulatorWrapper if available, else use internal simulation
try:
    from Core_Engines.quantum_simulator_wrapper import QuantumSimulatorWrapper
except ImportError:
    QuantumSimulatorWrapper = None

class VacuumProcessorWrapper:
    def __init__(self):
        self.n_modes = 1000
        self.time_steps = 1000
        self.simulator = QuantumSimulatorWrapper() if QuantumSimulatorWrapper else None
        
    def attempt_vacuum_storage(self, data_signal_strength=2.0):
        """
        Simulates storing information in the Quantum Vacuum (Zero-Point Energy fluctuations).
        """
        print("🌌 Initializing Quantum Vacuum Field Simulation...")
        
        # 1. Generate Vacuum Noise (ZPE)
        # Zero-Point Energy: E0 = 0.5 * hbar * omega
        print("   - Generating Zero-Point Fluctuations...")
        vacuum_noise = np.random.normal(0, 1, self.time_steps)
        
        # 2. Inject Signal (The Data)
        # Signal is a modulated displacement of the vacuum
        t = np.linspace(0, 10, self.time_steps)
        signal = data_signal_strength * np.sin(2 * np.pi * 1.0 * t) * np.exp(-0.1 * t)
        
        print("   - Injecting Signal into Vacuum (Modulating Field)...")
        field = vacuum_noise + signal
        
        # 3. Evolve (Storage Duration)
        print("   - Evolving System (Vacuum Channel Transmission)...")
        decay = 0.95 # Slight decoherence
        evolved_field = field * decay
        
        # 4. Retrieve
        print("   - Retrieving Signal...")
        retrieved_signal = evolved_field
        
        # 5. Calculate Fidelity
        signal_power = np.var(signal)
        noise_power = np.var(vacuum_noise)
        snr = 10 * np.log10(signal_power / noise_power)
        
        fidelity = np.corrcoef(signal, retrieved_signal)[0, 1]
        
        print(f"   - Signal Power: {signal_power:.4f}")
        print(f"   - Vacuum Noise Power (ZPE): {noise_power:.4f}")
        print(f"   - SNR: {snr:.2f} dB")
        print(f"   - Fidelity: {fidelity:.4f}")
        
        # Plotting
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 1, 1)
        plt.plot(t, vacuum_noise, color='gray', alpha=0.5, label='Vacuum Fluctuations (ZPE)')
        plt.plot(t, signal, color='blue', linewidth=2, label='Input Signal')
        plt.title("Vacuum Field Encoding")
        plt.legend()
        
        plt.subplot(2, 1, 2)
        plt.plot(t, retrieved_signal, color='green', label='Retrieved Signal (Noisy)')
        plt.plot(t, signal * decay, color='red', linestyle='--', label='Expected Signal (Decayed)')
        plt.title(f"Retrieval (Fidelity: {fidelity:.2f})")
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('vacuum_simulation_results.png')
        print("   - Plot saved to vacuum_simulation_results.png")
        
        return {
            "snr": snr,
            "fidelity": fidelity,
            "status": "SUCCESS" if fidelity > 0.5 else "FAILURE"
        }

    def attempt_vacuum_processing(self, input_bit=1):
        """
        Simulates PROCESSING information using Vacuum Fluctuations (Stochastic Resonance).
        We use the Zero-Point Energy noise to amplify a weak logic signal.
        """
        print("\n🌌 Initializing Vacuum Processing (Stochastic Resonance)...")
        
        # 1. Weak Logic Signal (Sub-threshold)
        # A signal too weak to be detected without vacuum noise
        threshold = 0.5
        signal_strength = 0.45 # Optimized for Resonance (Just below threshold)
        t = np.linspace(0, 10, self.time_steps)
        # Square wave representing a bit
        signal = np.where(np.sin(t) > 0, signal_strength, -signal_strength) * input_bit
        
        print(f"   - Input Signal Strength: {signal_strength} (Threshold: {threshold})")
        
        # 2. Add Vacuum Noise (ZPE)
        # We tune the noise intensity to the optimal resonance point
        noise_intensity = 0.25 # Fine-tuned ZPE Noise
        vacuum_noise = np.random.normal(0, noise_intensity, self.time_steps)
        
        print(f"   - Adding Zero-Point Energy (Noise Intensity: {noise_intensity})...")
        combined_field = signal + vacuum_noise
        
        # 3. Process (Thresholding/Non-linear Operation)
        # The vacuum fluctuations push the weak signal over the threshold
        print("   - Processing: Non-linear Thresholding via Vacuum Interaction...")
        processed_output = np.where(combined_field > threshold, 1.0, 0.0)
        processed_output = np.where(combined_field < -threshold, -1.0, processed_output)
        
        # 4. Verify Output
        # Check if the output correlates with the original weak signal
        # Ideally, the output should be a restored square wave
        ideal_output = np.where(signal > 0, 1.0, -1.0)
        correlation = np.corrcoef(processed_output, ideal_output)[0, 1]
        
        print(f"   - Processing Fidelity (Correlation): {correlation:.4f}")
        
        if correlation > 0.6:
            print("   ✅ VACUUM PROCESSING SUCCESS: ZPE amplified the weak signal.")
        else:
            print("   ❌ VACUUM PROCESSING FAILED.")
            
        return {
            "type": "Stochastic Resonance",
            "fidelity": correlation,
            "status": "SUCCESS" if correlation > 0.6 else "FAILURE"
        }

def run_simulation():
    print("\n🧪 Starting Vacuum Processing Simulation (Integrated Mode)")
    print("=======================================================")
    
    processor = VacuumProcessorWrapper()
    result = processor.attempt_vacuum_storage()
    
    print("\n✅ Simulation Complete.")
    print(f"Result: {result}")

if __name__ == "__main__":
    run_simulation()
