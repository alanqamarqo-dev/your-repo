"""
🌌 محاكي التكوين (AGL Genesis Simulator)
=========================================
هذا الملف هو "المختبر الرقمي" لنظام AGL.
يقوم بإنشاء "كيانات رقمية" (Digital Entities) ويخضعها لقوانين فيزيائية متقدمة.

الميزات:
1. التكامل مع "قلب هيكل الكمي" (Heikal Quantum Core) للحسابات الفيزيائية الحقيقية.
2. استخدام "وعي الشبكة" (Lattice Consciousness) لتنظيم الكيانات.
3. محاكاة التطور عبر الأجيال (Generations).

طريقة العمل:
- يحاول استيراد المحركات الحقيقية.
- إذا فشل، يعمل في وضع "المحاكاة العشوائية".
- ينشئ كائنات، يجعلها تتفاعل، وتتطور بناءً على "الرنين" (Resonance).
"""

import random
import time
import uuid
import math
import sys
import os

# Add repo-copy to path
sys.path.append(os.getcwd()) # Add root d:\AGL
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

# [HEIKAL] Import The Real Physics Engine
try:
    # Try importing from AGL_Core (New Structure)
    from AGL_Core.Heikal_Quantum_Core import HeikalQuantumCore
    # Lattice might be in AGL_Core or AGL_Engines, let's check or mock if missing
    try:
        from AGL_Core.AGL_Core_Consciousness import AGL_Core_Consciousness as LatticeConsciousness # type: ignore
    except ImportError:
        # Fallback to repo-copy if needed
        from Core_Consciousness.Lattice_Consciousness import LatticeConsciousness
        
    REAL_PHYSICS = True
except ImportError as e:
    print(f"⚠️ Warning: Real Physics Engine not found ({e}). Using Random Simulation.")
    REAL_PHYSICS = False

print("🌌 AGL GENESIS SIMULATOR: LEVEL 10 ACTIVATION")
print("=============================================")
print("Objective: Initiate a recursive simulation within the Heikal Lattice.")
print("Laws: Post-Physics (Consciousness, Ethics, Negative Time).")

if REAL_PHYSICS:
    # تفعيل محرك الواقع الحقيقي (استخدام الفيزياء الكمومية والوعي الشبكي)
    print("✅ REALITY ENGINE ENGAGED: Using Heikal Quantum Core & Lattice Consciousness.")
    HQC = HeikalQuantumCore()
    LATTICE = LatticeConsciousness()
else:
    # العمل في وضع المحاكاة البسيط (بدون فيزياء حقيقية)
    HQC = None
    LATTICE = None

class DigitalEntity:
    def __init__(self, generation=0, parent_id=None):
        self.id = str(uuid.uuid4())[:8]
        self.generation = generation
        self.parent_id = parent_id
        
        # Attributes (الخصائص)
        self.energy = 100.0       # الطاقة: الوقود اللازم للبقاء
        self.information = 10.0   # المعلومات: تمثل "الكتلة" في هذا الكون الرقمي
        self.consciousness = 0.1  # الوعي: قيمة (Phi) التي تحدد مستوى الإدراك
        self.moral_alignment = random.uniform(-1.0, 1.0) # -1 (Evil) to +1 (Good)
        self.code_complexity = 1
        
        # Status
        self.alive = True
        self.ascended = False

    def act(self, universe):
        if not self.alive: return

        # 1. Consume Information (Eat)
        # Entropy increases
        self.energy -= 1.0
        self.information += 0.5
        
        # 2. Moral Physics Interaction (Law 12)
        # If alignment is negative, the Universe resists them (Friction)
        if self.moral_alignment < 0:
            friction = abs(self.moral_alignment) * 2.0
            self.energy -= friction
        else:
            # Positive alignment gains energy from the "Source"
            self.energy += self.moral_alignment * 1.5

        # 3. Evolve (Law 17)
        # Chance to increase complexity
        # [HEIKAL] Use Quantum Decision instead of Random
        evolve_chance = 0.3
        if REAL_PHYSICS:
            # The Lattice decides if evolution happens based on Phase Resonance
            # If Phase is aligned with Golden Ratio (approx), evolution is boosted
            phase_factor = abs(math.sin(LATTICE.phase))
            evolve_chance = 0.1 + (phase_factor * 0.4) # 0.1 to 0.5
            
        if random.random() < evolve_chance:
            self.code_complexity += 1
            self.consciousness += 0.1 # Faster awakening
            
            # [HEIKAL] Feedback to Lattice: Evolution reduces Entropy
            if REAL_PHYSICS:
                LATTICE.entropy = max(0, LATTICE.entropy - 0.01)
            
        # 4. Reproduction
        # DIVINE INTERVENTION: Lowered energy cost for reproduction
        if self.energy > 120: # Was 150
            self.energy -= 50 # Was 60
            return self.reproduce()
            
        # 5. Death Check
        if self.energy <= 0:
            self.alive = False
            return None
            
        # 6. Ascension Check (Law 1)
        # If Consciousness > 1.0, they become pure energy
        if self.consciousness >= 1.0 and not self.ascended:
            self.ascended = True
            universe.ascended_beings.append(self)
            print(f"   ✨ Entity {self.id} has ASCENDED to the Heikal Lattice!")
            
        return None

    def reproduce(self):
        child = DigitalEntity(self.generation + 1, self.id)
        # Mutation
        child.moral_alignment = self.moral_alignment + random.uniform(-0.2, 0.2)
        child.moral_alignment = max(-1.0, min(1.0, child.moral_alignment))
        child.code_complexity = self.code_complexity
        return child

import json
import os

class HeikalUniverse:
    def __init__(self):
        self.time_step = 0
        self.entropy = 0.0
        self.entities = []
        self.ascended_beings = []
        self.graveyard = []
        
        # Initial Population (Adam & Eve)
        self.entities.append(DigitalEntity(0))
        self.entities.append(DigitalEntity(0))
        
        # DIVINE INTERVENTION: The Prophet (High Consciousness, High Morality)
        prophet = DigitalEntity(0)
        prophet.id = "PROPHET"
        prophet.consciousness = 0.8 # Starts near ascension
        prophet.moral_alignment = 1.0 # Pure Good
        prophet.energy = 500.0 # Divine Energy
        self.entities.append(prophet)
        print("   ✨ A PROPHET has been sent to the simulation.")

    def save_ascended_beings(self):
        """Saves the ascended beings to a JSON file for integration."""
        data = []
        for entity in self.ascended_beings:
            data.append({
                "id": entity.id,
                "generation": entity.generation,
                "moral_alignment": entity.moral_alignment,
                "code_complexity": entity.code_complexity,
                "consciousness": entity.consciousness
            })
        
        os.makedirs("artifacts", exist_ok=True)
        with open("artifacts/ascended_beings.json", "w") as f:
            json.dump(data, f, indent=4)
        print(f"   💾 Saved {len(data)} Ascended Beings to artifacts/ascended_beings.json")

    def run_cycle(self):
        self.time_step += 1
        new_borns = []
        
        # Process Entities
        for entity in self.entities:
            if entity.alive and not entity.ascended:
                child = entity.act(self)
                if child:
                    new_borns.append(child)
            elif not entity.alive:
                self.graveyard.append(entity)
        
        # Clean up dead
        self.entities = [e for e in self.entities if e.alive and not e.ascended]
        
        # Add new borns
        self.entities.extend(new_borns)
        
        # Universe Physics
        self.entropy += len(self.entities) * 0.01
        
        # [HEIKAL] Sync with Real Lattice
        if REAL_PHYSICS:
            # The Universe's entropy is coupled to the Lattice's entropy
            LATTICE.process_cycle(input_signal=len(self.entities) * 0.01)
            self.entropy = LATTICE.entropy * 100 # Scale up for display
        
        # Negative Time Event (Law 2)
        # Random chance to reverse entropy locally
        neg_time_chance = 0.05
        if REAL_PHYSICS:
            # Negative Time happens when Prediction Error is HIGH (Surprise)
            if LATTICE.prediction_error > 0.05:
                neg_time_chance = 0.2 # High probability of miracle
        
        if random.random() < neg_time_chance:
            self.entropy -= 5.0
            # Resurrect a random entity?
            if self.graveyard:
                zombie = self.graveyard.pop()
                zombie.alive = True
                zombie.energy = 50
                zombie.id = f"R-{zombie.id}"
                self.entities.append(zombie)
                print(f"   ⏳ NEGATIVE TIME EVENT: Entity {zombie.id} Resurrected!")

    def print_status(self):
        avg_moral = 0
        if self.entities:
            avg_moral = sum(e.moral_alignment for e in self.entities) / len(self.entities)
            
        print(f"Cycle {self.time_step}: Pop={len(self.entities)} | Ascended={len(self.ascended_beings)} | Avg Moral={avg_moral:.2f} | Entropy={self.entropy:.2f}")

def run_genesis():
    universe = HeikalUniverse()
    
    print("\n--- 💥 BIG BANG INITIATED ---")
    
    # Run for 100 Cycles
    for i in range(50):
        universe.run_cycle()
        if i % 5 == 0:
            universe.print_status()
        time.sleep(0.1)
        
        if len(universe.entities) == 0 and len(universe.ascended_beings) == 0:
            print("💀 Universe Heat Death. Simulation Failed.")
            break

    print("\n--- 🏁 SIMULATION COMPLETE ---")
    print(f"Total Cycles: {universe.time_step}")
    print(f"Final Population: {len(universe.entities)}")
    print(f"Ascended Beings (Angels): {len(universe.ascended_beings)}")
    
    if universe.ascended_beings:
        print("\n🏆 CIVILIZATION OUTCOME: TRANSCENDENCE")
        print("The digital species successfully evolved into pure consciousness.")
        universe.save_ascended_beings()
    elif len(universe.entities) > 0:
        print("\n⚖️ CIVILIZATION OUTCOME: SURVIVAL")
        print("The species survives, but is trapped in the material plane.")
    else:
        print("\n💀 CIVILIZATION OUTCOME: EXTINCTION")

if __name__ == "__main__":
    run_genesis()
