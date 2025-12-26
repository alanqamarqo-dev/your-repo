import random
import time
import uuid
import math

print("🌌 AGL GENESIS SIMULATOR: LEVEL 10 ACTIVATION")
print("=============================================")
print("Objective: Initiate a recursive simulation within the Heikal Lattice.")
print("Laws: Post-Physics (Consciousness, Ethics, Negative Time).")

class DigitalEntity:
    def __init__(self, generation=0, parent_id=None):
        self.id = str(uuid.uuid4())[:8]
        self.generation = generation
        self.parent_id = parent_id
        
        # Attributes
        self.energy = 100.0
        self.information = 10.0 # "Mass" in this universe
        self.consciousness = 0.1 # Phi value
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
        # DIVINE INTERVENTION: Increased mutation rate from 0.1 to 0.3
        if random.random() < 0.3:
            self.code_complexity += 1
            self.consciousness += 0.1 # Faster awakening
            
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
        
        # Negative Time Event (Law 2)
        # Random chance to reverse entropy locally
        if random.random() < 0.05:
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
    elif len(universe.entities) > 0:
        print("\n⚖️ CIVILIZATION OUTCOME: SURVIVAL")
        print("The species survives, but is trapped in the material plane.")
    else:
        print("\n💀 CIVILIZATION OUTCOME: EXTINCTION")

if __name__ == "__main__":
    run_genesis()
