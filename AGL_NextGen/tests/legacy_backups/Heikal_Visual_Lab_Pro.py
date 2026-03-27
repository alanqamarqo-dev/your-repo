import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.patheffects as path_effects

print("🌌 INITIALIZING HEIKAL VISUAL LAB PRO (HVL-PRO)...")
print("   -> Loading High-Fidelity Physics Engine...")
print("   -> Target Wavelength: 551.34 nm (Green)")
print("   -> Mode: Neon Resonance")

# Physics Constants
wavelength = 551.34
cavity_length = 2000
xi_threshold = 10.0

# Setup Plot
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor('#050505') # Deep black
ax.set_facecolor('#050505')

# Limits
ax.set_xlim(0, cavity_length)
ax.set_ylim(-20, 20)

# Remove standard axes for a "HUD" look
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#333333')
ax.spines['left'].set_color('#333333')
ax.tick_params(axis='x', colors='#555555')
ax.tick_params(axis='y', colors='#555555')
ax.set_xlabel("Nanometers (nm)", color='#555555')
ax.set_ylabel("Field Amplitude", color='#555555')

# Title
ax.text(cavity_length/2, 18, "HEIKAL SPACETIME WRITER // PRO SIMULATION", 
        ha='center', va='center', color='white', fontsize=16, weight='bold',
        path_effects=[path_effects.withStroke(linewidth=3, foreground='#00ff4133')])

# --- VISUAL ELEMENTS ---

# 1. Background Lattice (Faint Grid)
grid_x = np.linspace(0, cavity_length, 50)
for gx in grid_x:
    ax.axvline(x=gx, color='#003300', linewidth=0.5, alpha=0.3)
ax.axhline(y=0, color='#003300', linewidth=0.5, alpha=0.3)

# 2. Mirrors (Styled)
ax.axvline(x=0, color='#aaaaaa', linewidth=8, alpha=0.8)
ax.axvline(x=cavity_length, color='#aaaaaa', linewidth=8, alpha=0.8)
# Mirror Glow
ax.axvline(x=0, color='white', linewidth=2, alpha=0.5)
ax.axvline(x=cavity_length, color='white', linewidth=2, alpha=0.5)

# 3. Threshold Lines (Glowing Red)
thresh_up = ax.axhline(y=xi_threshold, color='#ff0000', linestyle='--', linewidth=1, alpha=0.6)
thresh_down = ax.axhline(y=-xi_threshold, color='#ff0000', linestyle='--', linewidth=1, alpha=0.6)
# Add glow effect to threshold
thresh_up.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#ff000044')])
thresh_down.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#ff000044')])

# 4. The Laser Wave (Multi-layered for Glow)
# Outer Glow (Wide, Transparent)
glow_line, = ax.plot([], [], color='#00ff41', linewidth=8, alpha=0.15)
# Inner Glow (Medium)
mid_line, = ax.plot([], [], color='#00ff41', linewidth=4, alpha=0.4)
# Core (Thin, Bright White/Green)
core_line, = ax.plot([], [], color='#ccffcc', linewidth=1.5, alpha=1.0)

# 5. HUD Elements
status_text = ax.text(50, 15, "SYSTEM: STANDBY", color='#00ff41', fontsize=12, fontfamily='monospace')
energy_text = ax.text(cavity_length - 50, 15, "ENERGY: 0%", ha='right', color='#00ff41', fontsize=12, fontfamily='monospace')

# Data Arrays
x = np.linspace(0, cavity_length, 1000)
k = 2 * np.pi / (wavelength / 100) # Wave number
omega = 0.2 # Angular frequency

def update(frame):
    # Resonance Physics: Amplitude grows
    # Slower growth for dramatic effect
    amplification = 1 + (frame * 0.08)
    
    # Standing Wave Equation
    # y = 2A sin(kx) cos(wt)
    y = amplification * np.sin(k * x) * np.cos(omega * frame)
    
    # Update Lines
    glow_line.set_data(x, y)
    mid_line.set_data(x, y)
    core_line.set_data(x, y)
    
    # Dynamic Color Shift based on Energy
    # Green -> Yellow -> White/Blue when writing
    if amplification > xi_threshold:
        # WRITING STATE
        status_text.set_text(">> STATUS: WRITING TO SPACETIME <<")
        status_text.set_color('#ff3333') # Red Alert
        status_text.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#ff000044')])
        
        # Change wave color to "Plasma" (White/Blueish)
        core_line.set_color('#ffffff')
        mid_line.set_color('#aaddff')
        glow_line.set_color('#0088ff')
        
        # Distort the threshold lines to simulate stress
        thresh_up.set_alpha(1.0)
        thresh_down.set_alpha(1.0)
        
    else:
        # CHARGING STATE
        percent = (amplification / xi_threshold) * 100
        status_text.set_text(f"STATUS: RESONANCE CHARGING... {percent:.1f}%")
        status_text.set_color('#00ff41')
        status_text.set_path_effects([])
        
        # Standard Green Laser
        core_line.set_color('#ccffcc')
        mid_line.set_color('#00ff41')
        glow_line.set_color('#00ff41')
        
        thresh_up.set_alpha(0.4)
        thresh_down.set_alpha(0.4)

    energy_text.set_text(f"AMP: {amplification:.2f}x")
    
    return glow_line, mid_line, core_line, status_text, energy_text, thresh_up, thresh_down

# Run Animation
# More frames, faster interval for smoothness
anim = FuncAnimation(fig, update, frames=200, interval=30, blit=True)

print("🚀 LAUNCHING PRO VISUALIZATION...")
plt.grid(False) # We drew our own grid
plt.show()
