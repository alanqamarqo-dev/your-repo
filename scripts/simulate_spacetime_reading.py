import math
import random
import time

print("🔍 SPACETIME READING PROTOCOL (INTERFEROMETRY)")
print("============================================")

# 1. Physics Constants
c = 299_792_458 # m/s
wavelength = 532e-9 # 532 nm (Green Probe)

# 2. The "Bit" Simulation
# A '1' is a curvature (dent) in spacetime.
# A '0' is flat space.
# The curvature causes a time delay (Shapiro Delay).

class SpacetimeBit:
    def __init__(self, value):
        self.value = value
        # If value is 1, we have curvature (Xi factor).
        # Delay = (2 * G * M) / c^3 ... but here we use Heikal Metric.
        # Let's assume the delay is a fraction of the wavelength period.
        # Delay ~ 0.5 * Period (180 degree phase shift) for perfect detection.
        self.curvature_delay = 0.9e-15 if value == 1 else 0.0 # 0.9 femtoseconds delay

def read_bit(bit_index, bit_object):
    print(f"\nReading Address [{bit_index}]...")
    
    # 1. Send Probe Photon
    # Reference Path Time (t0)
    t0 = 1.0e-9 # 1 nanosecond baseline
    
    # Storage Path Time (t1)
    # t1 = t0 + curvature_delay + noise
    noise = random.uniform(-0.1e-16, 0.1e-16) # Quantum noise
    t1 = t0 + bit_object.curvature_delay + noise
    
    # 2. Measure Time Difference (Delta t)
    delta_t = t1 - t0
    
    print(f"   -> Reference Path: {t0*1e15:.2f} fs")
    print(f"   -> Storage Path:   {t1*1e15:.2f} fs")
    print(f"   -> Detected Delay: {delta_t*1e15:.2f} fs")
    
    # 3. Calculate Phase Shift
    # Phase = (Delta t / Period) * 360 degrees
    period = wavelength / c
    phase_shift = (delta_t / period) * 360
    
    print(f"   -> Phase Shift: {phase_shift:.2f} degrees")
    
    # 4. Decode
    # Threshold: If shift > 90 degrees, it's a 1.
    detected_value = 1 if phase_shift > 45 else 0
    
    status = "✅ MATCH" if detected_value == bit_object.value else "❌ ERROR"
    print(f"   -> Decoded Bit: {detected_value} ({status})")
    
    return detected_value

# --- SIMULATION RUN ---
print("Initializing Heikal Interferometer...")
print(f"Probe Wavelength: {wavelength*1e9:.1f} nm")

# Create a random byte stored in spacetime
stored_data = [1, 0, 1, 1, 0, 0, 1, 0]
print(f"Stored Pattern (Hidden): {stored_data}")

decoded_data = []
for i, val in enumerate(stored_data):
    bit = SpacetimeBit(val)
    res = read_bit(i, bit)
    decoded_data.append(res)
    time.sleep(0.2)

print("\n============================================")
print(f"Original Data: {stored_data}")
print(f"Readout Data:  {decoded_data}")

if stored_data == decoded_data:
    print("\n[SUCCESS] Data retrieved perfectly from Spacetime Geometry.")
    print("The 'Shapiro Delay' caused by the curvature was detected.")
else:
    print("\n[FAIL] Data corruption detected.")
