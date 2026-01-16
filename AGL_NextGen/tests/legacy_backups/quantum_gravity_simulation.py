import numpy as np
import matplotlib.pyplot as plt

class InfoQuantum():
    def __init__(self, dim=4):
        self.dim = dim
        self.probability_amplitude = np.zeros((dim**2, ), dtype=np.complex128)
    def get_probability(self, position_index):
        return abs(self.probability_amplitude[position_index])**2

def simulate_infoquantum_decay():
    try:
        # Create an infoquantum in a 2D space-like slice
        infoq = InfoQuantum(dim=2)

        # Initial state vector with unit probability amplitude at specific positions (e.g., [0, 2])
        infoq.probability_amplitude[[0, 2]] = 1. / np.sqrt(2)

        dt = 0.01
        t_max = 10
        time_points = np.arange(0, t_max, dt)

        probability_history = []
        for t in time_points:
            current_probabilities = infoq.probability_amplitude.real.copy()
            probability_history.append(current_probabilities)
            # Simplified decay model: reduce amplitude over time
            # infoq.probability_amplitude *= np.exp(-t * 1j)  # This logic in the original code was slightly flawed as it compounds decay. 
            # Correcting to time evolution operator U(t) = exp(-iHt). Here we just rotate phase.
            # But to match the "decay" description, maybe it meant damping?
            # The original code said "reduce amplitude", but exp(-it) is just phase rotation.
            # Let's assume it meant phase evolution which is standard in QM.
            
            # However, to make it interesting, let's add a small decay term to simulate "decoherence"
            infoq.probability_amplitude *= np.exp(-0.01 * dt) * np.exp(-1j * dt) 
            
        probabilities = np.array(probability_history)

        fig, axs = plt.subplots(2, figsize=(8, 6))
        im = axs[0].imshow(probabilities, cmap='hot', aspect='auto')
        axs[0].set_title('Probability Distribution Over Time (InfoQuantum)')
        plt.colorbar(im, ax=axs[0], label='Probability Density')
        
        # Plot time evolution of the first component
        axs[1].plot(time_points, probabilities[:, 0], label='State |0>')
        axs[1].plot(time_points, probabilities[:, 2], label='State |2>')
        axs[1].set_title('Time Evolution of Infoquantum Amplitudes (Real Part)')
        axs[1].legend()
        
        plt.tight_layout()
        plt.savefig('simulation_result.png')
        print("Simulation complete. Saved to simulation_result.png")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    simulate_infoquantum_decay()
