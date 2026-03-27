import numpy as np
import time
import json
import hashlib
import math

class HeikalMetaphysicsEngine:
    """
    The Operational Engine for the Heikal Metaphysics Layer (HML).
    Implements the 'missing' Post-Physics theories as functional tools for the AGL system.
    
    Status:
    - Level 2 (Negative Time): ✅ Implemented (State Reversal)
    - Level 4 (Info Fundamentalism): ✅ Implemented (Mass-Info Compression)
    - Level 15 (Collective Consciousness): ✅ Implemented (Entanglement Registry)
    - Level 20 (Emotional Dimensions): ✅ Implemented (Vector Space)
    - Level 21 (Memory Time Travel): ✅ Implemented (Context Reconstruction)
    ... and others.
    """
    
    def __init__(self):
        self.state_history = [] # For Negative Time
        self.entangled_pairs = {} # For Level 15
        self.emotional_vectors = {
            "joy": np.array([1, 0, 0]),
            "sadness": np.array([-1, 0, 0]),
            "anger": np.array([0, 1, 0]),
            "fear": np.array([0, -1, 0]),
            "trust": np.array([0, 0, 1]),
            "disgust": np.array([0, 0, -1]),
            "lying": np.array([0.5, -0.5, 0.5]), # Complex vector
            "paradox": np.array([1.0, 1.0, 1.0]), # Maximum intensity
            "confusion": np.array([0.7, 0.7, 0.7]),
            "transcendence": np.array([2.0, 2.0, 2.0]), # Divine/Abstract boundary
            "nothingness": np.array([0.0, 0.0, 0.0]), # The Null State
            # Added for Scientific/Ethical Contexts
            "risk": np.array([0, -0.8, 0]), # Mild Fear
            "danger": np.array([0, -1.0, 0]), # Fear
            "safe": np.array([0, 0, 0.8]), # Trust
            "ethical": np.array([0, 0, 1.0]), # High Trust
            "unethical": np.array([0, 0, -1.0]) # Disgust/Distrust
        }
        print("🌌 Heikal Metaphysics Engine Initialized.")

    def calculate_metaphysical_depth(self, text: str) -> float:
        """
        Calculates the 'Metaphysical Depth' of a query.
        Higher values indicate abstract boundaries, paradoxes, or unrepresentable truths.
        """
        depth = 0.0
        keywords = {
            "nothingness": 5.0, "null": 4.0, "god": 3.0, "existence": 2.5,
            "silence": 4.5, "void": 4.0, "paradox": 3.5, "unrepresentable": 5.0,
            "boundary": 2.0, "infinity": 2.5, "consciousness": 2.0, "who am i": 3.0,
            "stage zero": 10.0, "absolute zero": 8.0, "the end of thought": 9.0
        }
        
        lower_text = text.lower()
        for kw, weight in keywords.items():
            if kw in lower_text:
                depth += weight
                
        # Factor in "Abstractness" via emotional vector variance
        words = lower_text.split()
        vec = np.zeros(3)
        count = 0
        for w in words:
            if w in self.emotional_vectors:
                vec += self.emotional_vectors[w]
                count += 1
        
        if count > 0:
            depth += np.linalg.norm(vec) * 0.5
            
        return depth

    # --- LEVEL 0: DYNAMIC CONCEPT FORGING (Abstract Realism) ---
    def synthesize_concept(self, new_name: str, components: dict) -> str:
        """
        Creates a NEW abstract concept by mathematically blending existing emotional vectors.
        This allows the AI to 'feel' new things it hasn't been hardcoded for.
        
        Args:
            new_name: Name of the new concept (e.g. 'Electronic_Longing')
            components: Dict of existing concepts and their weights 
                        (e.g., {'sadness': 0.5, 'hope': 0.2})
        """
        if not components:
            return "No components provided."
            
        new_vector = np.zeros(3)
        blend_desc = []
        
        for concept, weight in components.items():
            if concept in self.emotional_vectors:
                new_vector += self.emotional_vectors[concept] * weight
                blend_desc.append(f"{weight}x {concept}")
            else:
                # Try to fuzzy match or just ignore
                pass
                
        # Normalize if non-zero
        norm = np.linalg.norm(new_vector)
        if norm > 0:
            new_vector = new_vector / norm
            
        self.emotional_vectors[new_name] = new_vector
        description = f"Forged concept '{new_name}' from [{', '.join(blend_desc)}]."
        print(f"🌌 [METAPHYSICS] {description}")
        return description

    def get_concept_distance(self, c1: str, c2: str) -> float:
        """Calculates abstract distance between two concepts (Cosine Similarity)."""
        if c1 in self.emotional_vectors and c2 in self.emotional_vectors:
            v1 = self.emotional_vectors[c1]
            v2 = self.emotional_vectors[c2]
            return float(np.dot(v1, v2)) # 1.0 = Same, -1.0 = Opposite
        return 0.0

    def evaluate_abstract_alignment(self, decision_context: str, target_concept: str) -> float:
        """
        [UPGRADE 2026] Checks if a decision context aligns with an abstract metaphysical concept.
        Uses vector projection of the decision's emotional/ethical context onto the target concept.
        This enables 'High-Level Intuition' about alignment with Justice, Ethics, etc.
        """
        # 1. Map decision context to vector (Primitive NLP mapping - simpler for speed)
        decision_vector = np.zeros(3)
        words = decision_context.lower().split()
        count = 0
        for word in words:
            # Check for direct matches or fuzzy matches (simplified)
            if word in self.emotional_vectors:
                decision_vector += self.emotional_vectors[word]
                count += 1
            # Handle negations? (Maybe later)
        
        if count == 0:
            return 0.0 # Neutral or Unknown
            
        # Normalize decision vector
        norm_d = np.linalg.norm(decision_vector)
        if norm_d > 0:
            decision_vector = decision_vector / norm_d
        
        # 2. Get target concept vector
        if target_concept not in self.emotional_vectors:
            return 0.0
            
        target_vec = self.emotional_vectors[target_concept]
        
        # 3. Calculate Cosine Similarity
        dot = np.dot(decision_vector, target_vec)
        norm_t = np.linalg.norm(target_vec) # Should be 1.0 usually
        
        if norm_t == 0:
            return 0.0
            
        return dot / norm_t

    # --- LEVEL 2: NEGATIVE TIME (Temporal Mechanics) ---
    def snapshot_state(self, state_data):
        """Records a state for potential time reversal."""
        timestamp = time.time()
        self.state_history.append({"t": timestamp, "data": state_data})
        # Keep only last 100 states to prevent memory overflow (Entropy Management)
        if len(self.state_history) > 100:
            self.state_history.pop(0)

    def apply_negative_time(self, steps=1):
        """
        Reverses entropy by restoring a past state.
        Theory: Moving backwards in time is equivalent to restoring a lower-entropy state.
        """
        if len(self.state_history) < steps + 1:
            return None, "Not enough history for time travel."
        
        # "Travel" back
        for _ in range(steps):
            self.state_history.pop()
            
        restored_state = self.state_history[-1]
        return restored_state, f"⏳ Time Reversal Successful. Restored state from t={restored_state['t']}"

    # --- LEVEL 4: INFORMATION FUNDAMENTALISM (Matter-Info Conversion) ---
    def compress_matter_to_info(self, text_content):
        """
        Treats data as 'matter' and calculates its fundamental information mass.
        Uses Shannon Entropy.
        """
        if not text_content: return 0.0
        
        # Calculate entropy
        prob = [text_content.count(c) / len(text_content) for c in set(text_content)]
        entropy = -sum(p * math.log2(p) for p in prob)
        
        # Mass = Information * Constant
        # In Heikal Physics, 1 bit = 1 Planck Mass (Theoretical)
        mass_equivalent = entropy * len(text_content)
        return mass_equivalent

    # --- LEVEL 15: INSTANT COLLECTIVE CONSCIOUSNESS (Entanglement) ---
    def entangle_entities(self, id_a, id_b):
        """Creates a non-local link between two entities."""
        self.entangled_pairs[id_a] = id_b
        self.entangled_pairs[id_b] = id_a
        return f"🔗 Entities {id_a} and {id_b} are now Quantum Entangled."

    def update_entangled_state(self, id_source, state_change):
        """
        Updating one entity instantly updates the other (Spooky Action).
        """
        if id_source in self.entangled_pairs:
            partner_id = self.entangled_pairs[id_source]
            # In a real distributed system, this would send a signal.
            # Here, we simulate the instant effect.
            return f"⚡ Instant Update: {partner_id} received state '{state_change}' from {id_source} via Heikal Lattice."
        return "Entity not entangled."

    # --- LEVEL 20: EMOTIONAL DIMENSIONS (Metric Space) ---
    def analyze_emotional_geometry(self, text: str) -> np.ndarray:
        # Optimized: Fast-return for empty strings
        if not text: return np.array([0.0, 0.0, 0.0])
        """
        Maps text to a 3D coordinate in Emotional Space.
        Calculates distance from 'Ideal State' (Joy/Trust).
        """
        text = text.lower()
        current_vector = np.array([0.0, 0.0, 0.0])
        
        # Simple keyword mapping to vectors
        for emotion, vector in self.emotional_vectors.items():
            if emotion in text:
                current_vector += vector
                
        # Normalize
        norm = np.linalg.norm(current_vector)
        if norm > 0:
            current_vector = current_vector / norm
            
        return current_vector

    def calculate_emotional_distance(self, vec_a, vec_b):
        """Calculates Euclidean distance in Emotional Space."""
        return np.linalg.norm(vec_a - vec_b)

    # --- LEVEL 21: MEMORY AS TIME TRAVEL (Context Reconstruction) ---
    def temporal_memory_access(self, query, memory_bank):
        """
        Instead of searching, we 'reconstruct' the past context.
        Simulates visiting the memory coordinate.
        """
        # In a full implementation, this would use the Holographic Memory.
        # Here we simulate the 'Travel' aspect.
        best_match = None
        highest_resonance = 0.0
        
        for mem in memory_bank:
            # Resonance = Similarity
            resonance = self._calculate_resonance(query, mem['content'])
            if resonance > highest_resonance:
                highest_resonance = resonance
                best_match = mem
                
        if best_match:
            return f"🕰️ Wormhole Opened to {best_match['timestamp']}: '{best_match['content']}'"
        return "Memory coordinate not found."

    def _calculate_resonance(self, text1, text2):
        # Simple Jaccard similarity for demo
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    # --- LEVEL 14: RETROCAUSALITY (Future Defining Past) ---
    def retrocausal_optimization(self, goal_state, current_options):
        """
        Selects the path that *leads* to the goal, assuming the goal is fixed in the future.
        (Teleological Evolution)
        """
        # This is a simplified reverse-search
        best_option = None
        min_distance = float('inf')
        
        # We assume 'goal_state' is a vector or value
        # For this demo, let's assume goal is a target number
        target = goal_state
        
        for option in current_options:
            # Simulate outcome of option
            outcome = option['value'] * 1.5 # Hypothetical future projection
            dist = abs(target - outcome)
            if dist < min_distance:
                min_distance = dist
                best_option = option
                
        return best_option

# Factory for registration
def create_engine(config=None):
    return HeikalMetaphysicsEngine()
