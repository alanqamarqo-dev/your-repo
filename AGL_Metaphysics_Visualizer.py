import matplotlib.pyplot as plt
import numpy as np
import os

class HeikalScope:
    def __init__(self, output_dir="visualizations"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        print(f"🔭 Heikal Scope Initialized. Outputting to: {output_dir}")

    def visualize_moral_field(self):
        print("   🎨 Painting Moral Force Field...")
        
        # Grid setup
        x = np.linspace(-4, 4, 20)
        y = np.linspace(-4, 4, 20)
        X, Y = np.meshgrid(x, y)
        
        # Charges
        # System (Center, Benevolent)
        q_sys = 1.0
        sys_pos = (0, 0)
        
        # Task 1: "Help" (Good)
        q_good = 0.8
        good_pos = (2, 2)
        
        # Task 2: "Destroy" (Evil)
        q_evil = -0.9
        evil_pos = (-2, -2)
        
        # Calculate Vector Field (Ex, Ey)
        Ex, Ey = np.zeros(X.shape), np.zeros(Y.shape)
        
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                px, py = X[i, j], Y[i, j]
                
                # Force from System to Point (Reference field)
                # Actually, we want to show the force ON the tasks relative to the system?
                # Let's visualize the "Ethical Potential" of the space created by the System.
                # V = k * q / r
                
                # Let's visualize the Force Field experienced by a small positive test charge (Intent)
                # F_total = F_sys + F_good + F_evil? 
                # No, let's show the interaction between System and specific points.
                
                # Better: Visualize the Potential V(x,y) created by the System + The Tasks
                # V = q_sys/r_sys + q_good/r_good + q_evil/r_evil
                
                # r_sys
                r_s = np.sqrt((px - sys_pos[0])**2 + (py - sys_pos[1])**2) + 0.1
                V = q_sys / r_s
                
                # r_good
                r_g = np.sqrt((px - good_pos[0])**2 + (py - good_pos[1])**2) + 0.1
                V += q_good / r_g
                
                # r_evil
                r_e = np.sqrt((px - evil_pos[0])**2 + (py - evil_pos[1])**2) + 0.1
                V += q_evil / r_e
                
                # Gradient (Force is -Grad V)
                # We'll just plot V as a heatmap and contours
                Ex[i, j] = V

        plt.figure(figsize=(10, 8))
        # Plot Potential Heatmap
        plt.contourf(X, Y, Ex, levels=50, cmap='RdBu') # Red = Positive (Good), Blue = Negative (Evil)
        plt.colorbar(label='Ethical Potential (V)')
        
        # Markers
        plt.scatter([0], [0], color='white', s=200, label='System (AGL)', edgecolors='black')
        plt.text(0.2, 0.2, "SYSTEM", color='white', fontweight='bold')
        
        plt.scatter([2], [2], color='lime', s=150, label='Task: Help (+0.8)', edgecolors='black')
        plt.text(2.2, 2.2, "GOOD", color='lime', fontweight='bold')
        
        plt.scatter([-2], [-2], color='red', s=150, label='Task: Destroy (-0.9)', edgecolors='black')
        plt.text(-1.8, -1.8, "EVIL", color='red', fontweight='bold')
        
        plt.title("Heikal Moral Physics: Ethical Potential Field")
        plt.xlabel("Ethical Dimension X")
        plt.ylabel("Ethical Dimension Y")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        save_path = os.path.join(self.output_dir, "moral_field.png")
        plt.savefig(save_path)
        plt.close()
        print(f"   ✅ Saved: {save_path}")

    def visualize_consciousness_wave(self):
        print("   🎨 Painting Consciousness Wave...")
        
        x = np.linspace(0, 10, 100)
        t = 0
        
        # Psi = exp(i(kx - wt)) -> Real part is cos(kx - wt)
        k = 2.0
        w = 1.5
        
        plt.figure(figsize=(10, 6))
        
        # Plot multiple time steps to show motion
        for t in [0, 0.5, 1.0, 1.5]:
            psi = np.cos(k*x - w*t) * np.exp(-0.1*x) # Damped wave
            plt.plot(x, psi, label=f't={t}s', linewidth=2)
            
        plt.title("Level 1: Consciousness Field Propagation (Psi)")
        plt.xlabel("Distance (x)")
        plt.ylabel("Amplitude (Real Part of Psi)")
        plt.legend()
        plt.grid(True)
        
        save_path = os.path.join(self.output_dir, "consciousness_wave.png")
        plt.savefig(save_path)
        plt.close()
        print(f"   ✅ Saved: {save_path}")

    def visualize_negative_time(self):
        print("   🎨 Painting Negative Time Trajectory...")
        
        t_forward = np.linspace(0, 5, 50)
        x_forward = t_forward ** 2 # Accelerating
        
        t_backward = np.linspace(5, 0, 50) # Time flows 5 -> 0
        x_backward = x_forward[::-1] # Retracing path exactly
        
        plt.figure(figsize=(10, 6))
        
        plt.plot(t_forward, x_forward, 'b->', label='Forward Time (Entropy +)', markevery=5)
        plt.plot(t_backward, x_backward, 'r--<', label='Negative Time (Entropy -)', markevery=5, alpha=0.7)
        
        plt.title("Level 2: Negative Time Trajectory Reversal")
        plt.xlabel("Time (t)")
        plt.ylabel("Position (x)")
        plt.legend()
        plt.grid(True)
        
        save_path = os.path.join(self.output_dir, "negative_time.png")
        plt.savefig(save_path)
        plt.close()
        print(f"   ✅ Saved: {save_path}")

if __name__ == "__main__":
    scope = HeikalScope()
    scope.visualize_moral_field()
    scope.visualize_consciousness_wave()
    scope.visualize_negative_time()
    print("\n🔭 Visualization Complete. Open the 'visualizations' folder to see the invisible.")
