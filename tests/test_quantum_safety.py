
import sys
import os
import math

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Safety_Systems.Dissonance_Watchdog import DissonanceWatchdog

def test_quantum_safety():
    print("--- Testing Quantum Safety Valve (Dissonance Watchdog) ---")
    
    watchdog = DissonanceWatchdog()
    
    # Case 1: Destructive Confusion (Weak signals, High Conflict)
    # Logic says X (0 degrees), Intuition says Not X (180 degrees)
    # But both are unsure (0.3 confidence)
    print("\n[Case 1: Destructive Confusion]")
    state_weak = {
        "logic_confidence": 0.3,
        "intuition_confidence": 0.3, # Conflict comes from phase calc in watchdog? 
        # Wait, the watchdog calculates phase from magnitude? 
        # No, it maps 0-1 to 0-pi. 
        # 0.3 -> 0.3pi (~54 deg)
        # We need high conflict. 
        # Let's look at the code: angles = [s * np.pi for s in signals]
        # To get max conflict (180 deg diff), we need one at 0 and one at 1?
        # No, 0 maps to 0, 1 maps to pi.
        # So if one signal is 0.1 (low angle) and other is 0.9 (high angle), they are opposed.
        # But we want "Weak signals" to fail tunneling.
        # If signals are 0.1 and 0.9, average is 0.5.
        # If signals are 0.4 and 0.6? Angles 0.4pi and 0.6pi. Close.
        
        # Let's try to simulate "High Dissonance" first.
        # Dissonance = 1 - Coherence.
        # Coherence = VectorSum / N.
        # To get low coherence, vectors must cancel.
        # Vector 1: Angle 0 (Confidence 0.0) -> No, confidence is magnitude? 
        # Code: x_sum = sum(np.cos(a))...
        # So confidence determines the ANGLE.
        # 0.0 -> 0 deg. 1.0 -> 180 deg.
        # So 0.0 and 1.0 are maximally opposed.
        
        # But we want "Energy" (Average Strength) to be low for Case 1.
        # If we have 0.0 and 1.0, Avg = 0.5.
        # If we have 0.2 and 0.8? Avg = 0.5.
        # It seems Average Strength is always 0.5 for max conflict pairs?
        # Wait, if we have 3 signals? 0, 0.5, 1?
        
        # Let's try:
        # Case 1: 0.1 and 0.9. Avg = 0.5. Dissonance is high.
        # Case 2: 0.1 and 0.9. Avg = 0.5.
        # This metric for "Energy" might be flawed if Confidence = Angle.
        
        # Re-reading Watchdog code:
        # angles = [s * np.pi for s in signals]
        # x_sum = sum(np.cos(a))
        # coherence = r / len(signals)
        
        # If signals are [0.0, 1.0]:
        # A1=0, A2=pi.
        # cos(0)=1, cos(pi)=-1. Sum=0.
        # sin(0)=0, sin(pi)=0. Sum=0.
        # r=0. Coherence=0. Dissonance=1.0.
        # Avg Strength = 0.5.
        # Tunneling(0.5, 1.0) -> Energy(0.5) < Barrier(1.0). Tunneling Prob low. -> ALERT.
        
        # Case 2: Productive Dissonance.
        # We need High Energy > Barrier.
        # But if High Energy means High Confidence, High Confidence means Angle -> Pi.
        # If all signals are 1.0 (High Confidence), all angles are Pi.
        # cos(pi)=-1. Sum = -N.
        # r = N. Coherence = 1.0. Dissonance = 0.0.
        # So High Confidence Agreement = Low Dissonance.
        
        # We need High Dissonance (Disagreement) AND High Energy.
        # Disagreement means angles are spread out.
        # High Energy means... what?
        # In the code I wrote: `avg_strength = sum(signals) / len(signals)`.
        # If signals are [0.0, 1.0], Avg=0.5.
        # If signals are [0.2, 0.8], Avg=0.5.
        
        # Maybe I should have used a different metric for Energy?
        # Or maybe the "Confidence = Angle" mapping is the constraint.
        # If Confidence is BOTH the magnitude and the angle, it's tricky.
        # Usually in QSR, Energy is independent of Phase.
        
        # But let's test what we have.
        # Maybe [0.1, 0.9] (Avg 0.5) vs [0.4, 0.6] (Avg 0.5)?
        # [0.4, 0.6]: Angles 72deg, 108deg. Coherence higher. Dissonance lower.
        
        # Let's try to find a case where Tunneling saves us.
        # We need Energy > Barrier.
        # Energy = Avg(Signals). Barrier = 1 - Coherence.
        # We need Avg > 1 - Coherence.
        # Avg + Coherence > 1.
        
        # Try [0.1, 0.9]. Avg=0.5. Coherence=0. Dissonance=1. Sum=0.5. Fail.
        # Try [0.3, 0.7]. Avg=0.5. Angles 54, 126. Diff=72.
        # Coherence = cos(36) = 0.8. Dissonance = 0.2.
        # Energy (0.5) > Barrier (0.2). Tunneling!
        
        # But Dissonance 0.2 is < Threshold 0.4. So it wouldn't alert anyway.
        
        # We need Dissonance > 0.4.
        # So Coherence < 0.6.
        # And Energy > Dissonance.
        
        # Try [0.05, 0.95]. Avg=0.5. Coherence ~ 0. Dissonance ~ 1. Fail.
        
        # It seems with 2 signals summing to 1.0, Energy is always 0.5.
        # And Dissonance is high.
        # So 2-signal conflict always fails tunneling?
        
        # What if we have 3 signals?
        # [0.9, 0.9, 0.1].
        # Angles: 162, 162, 18.
        # Avg Energy: (1.9)/3 = 0.63.
        # Coherence: Vectors at 162, 162, 18.
        # Resultant will be small?
        # 162 is close to 180. 18 is close to 0.
        # It's like 2 vs 1.
        # Coherence might be low (cancellation).
        # If Dissonance is 0.5. Energy is 0.63.
        # 0.63 > 0.5 -> Tunneling!
        
        "logic": 0.9,
        "intuition": 0.9,
        "fear": 0.1
    }
    
    # Case 1: [0.1, 0.9] -> Avg 0.5. Dissonance 1.0. Fail.
    state_fail = {"confidence_1": 0.1, "confidence_2": 0.9}
    
    # Case 2: [0.9, 0.9, 0.1] -> Avg 0.63. Dissonance ~0.5?
    state_pass = {"confidence_1": 0.9, "confidence_2": 0.9, "confidence_3": 0.1}
    
    print(f"Testing State Fail: {state_fail}")
    res_fail = watchdog.monitor(state_fail)
    print(f"Result: {res_fail['status']} (Diss: {res_fail['dissonance']:.2f}, Energy: {res_fail['insight_energy']:.2f})")
    
    print(f"\nTesting State Pass: {state_pass}")
    res_pass = watchdog.monitor(state_pass)
    print(f"Result: {res_pass['status']} (Diss: {res_pass['dissonance']:.2f}, Energy: {res_pass['insight_energy']:.2f})")
    
    if res_fail['status'] == 'alert' and res_pass['status'] == 'productive_dissonance':
        print("\n✅ SUCCESS: Quantum Safety Valve correctly distinguished destructive vs productive dissonance.")
    else:
        print("\n❌ FAILURE: Did not distinguish correctly.")

if __name__ == "__main__":
    test_quantum_safety()
