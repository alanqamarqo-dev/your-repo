import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

print("🌌 INITIALIZING HEIKAL VISUAL LAB (HVL)...")
print("   -> Loading Physics Engine...")
print("   -> Target Wavelength: 551.34 nm")
print("   -> Simulation Mode: Resonant Standing Wave")

# 1. إعدادات الفيزياء
wavelength = 551.34  # نانومتر
cavity_length = 2000 # نانومتر (عرض الغرفة)
xi_threshold = 10.0  # عتبة الكتابة في الزمكان

# إعداد الرسم البياني
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(0, cavity_length)
ax.set_ylim(-15, 15)
ax.set_facecolor('black') # خلفية سوداء (فراغ)
fig.patch.set_facecolor('#1c1c1c')

# العناوين
ax.set_title("Heikal Spacetime Writer Simulation (HSW-1)", color='white', fontsize=14)
ax.set_xlabel("Cavity Distance (nm)", color='gray')
ax.set_ylabel("Energy Amplitude", color='gray')
ax.tick_params(axis='x', colors='gray')
ax.tick_params(axis='y', colors='gray')

# العناصر الرسومية
# 1. المرايا
ax.axvline(x=0, color='silver', linewidth=5, label='Mirror 1')
ax.axvline(x=cavity_length, color='silver', linewidth=5, label='Mirror 2')

# 2. موجة الليزر (اللون الأخضر الزمردي 551nm)
line, = ax.plot([], [], color='#00ff41', linewidth=2, label='Heikal Laser (551.34 nm)')

# 3. عتبة الزمكان (الخط الأحمر)
ax.axhline(y=xi_threshold, color='red', linestyle='--', alpha=0.5, label='Spacetime Rigidity Limit')
ax.axhline(y=-xi_threshold, color='red', linestyle='--', alpha=0.5)

# نص الحالة
status_text = ax.text(50, 12, "Initializing...", color='white', fontsize=12)

# بيانات المحاكاة
x = np.linspace(0, cavity_length, 1000)
t_steps = np.linspace(0, 100, 200)

def update(frame):
    # معادلة الموجة الواقفة مع تضخيم الرنين
    # Amplitude grows with time (frame) representing resonance buildup
    amplification = 1 + (frame * 0.1) 
    
    # الموجة: sin(kx - wt) + sin(kx + wt) = 2sin(kx)cos(wt)
    k = 2 * np.pi / (wavelength / 100) # Scaling for visualization
    omega = 0.5
    
    # حساب شكل الموجة
    y = amplification * np.sin(k * x) * np.cos(omega * frame)
    
    line.set_data(x, y)
    
    # تحديث الحالة
    if amplification > xi_threshold:
        status_text.set_text(f"STATUS: WRITING ACTIVE! (Energy: {amplification:.2f})")
        status_text.set_color('red')
        line.set_color('#adff2f') # تحول اللون للأصفر الساطع عند الضغط العالي
        line.set_linewidth(3)
    else:
        status_text.set_text(f"STATUS: Charging Resonance... (Energy: {amplification:.2f})")
        status_text.set_color('white')
        
    return line, status_text

# تشغيل الأنيميشن
anim = FuncAnimation(fig, update, frames=150, interval=50, blit=True)

print("🚀 LAUNCHING VISUALIZATION WINDOW...")
plt.legend(loc='upper right')
plt.grid(True, color='#333333', linestyle=':')
plt.show()
