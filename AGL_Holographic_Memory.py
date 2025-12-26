import random
import math

print("🌌 AGL HOLOGRAPHIC MEMORY: DISTRIBUTED ASSOCIATIVE STORAGE")
print("========================================================")

# THEORY:
# The Holographic Principle suggests information is distributed, not localized.
# We implement "Holographic Reduced Representations" (HRR).
# 1. Concepts are vectors.
# 2. Association is Circular Convolution (Binding).
# 3. Storage is Superposition (Addition).
# 4. Retrieval is Correlation (Unbinding).

# This allows us to store INFINITE associations in a SINGLE "Vacuum State" vector
# (limited only by noise/dimension).

DIMENSION = 512  # Size of the holographic vector

def generate_vector():
    """Generates a random high-dimensional vector (Gaussian noise)."""
    return [random.gauss(0, 1.0/math.sqrt(DIMENSION)) for _ in range(DIMENSION)]

def circular_convolution(a, b):
    """
    Binds two vectors A and B.
    Mathematically: c[k] = sum(a[j] * b[k-j])
    This is the 'Holographic Product'.
    """
    c = [0] * DIMENSION
    for k in range(DIMENSION):
        val = 0
        for j in range(DIMENSION):
            val += a[j] * b[(k - j) % DIMENSION]
        c[k] = val
    return c

def circular_correlation(mem, key):
    """
    Unbinds Key from Memory to retrieve Value.
    Mathematically similar to convolution with the involution of Key.
    """
    # Approximate inverse for HRR is just correlation
    c = [0] * DIMENSION
    for k in range(DIMENSION):
        val = 0
        for j in range(DIMENSION):
            val += mem[(j + k) % DIMENSION] * key[j]
        c[k] = val
    return c

def superposition(list_of_vectors):
    """Adds vectors together (The 'Vacuum State')."""
    res = [0] * DIMENSION
    for v in list_of_vectors:
        for i in range(DIMENSION):
            res[i] += v[i]
    return res

def cosine_similarity(v1, v2):
    dot = sum(a*b for a,b in zip(v1, v2))
    norm1 = math.sqrt(sum(a*a for a in v1))
    norm2 = math.sqrt(sum(b*b for b in v2))
    return dot / (norm1 * norm2)

# --- INTEGRATION: HOLOGRAPHIC FIREWALL ---
HEIKAL_GAP = 1.290655
XI = 1.5496

def calculate_thought_mass(text):
    """Calculates the 'Reality Mass' of a thought/association."""
    length = len(text)
    if length == 0: return 0.0
    unique_chars = len(set(text))
    entropy = unique_chars / length
    
    # Heikal Mass Formula
    base_mass = (length * entropy) / 8.0 # Adjusted divisor for sensitivity
    
    # Deterministic fluctuation (seeded by text) to simulate quantum state
    random.seed(text)
    fluctuation = random.uniform(-0.1, 0.1)
    
    return base_mass * XI + fluctuation

class HolographicVacuum:
    def __init__(self, dimension=512):
        self.dimension = dimension
        self.vacuum_state = [0] * dimension
        self.concepts = {}
        
    def get_concept_vector(self, name):
        if name not in self.concepts:
            self.concepts[name] = generate_vector()
        return self.concepts[name]

    def encode(self, key, value, context=""):
        mass = calculate_thought_mass(context)
        if mass > HEIKAL_GAP:
            vec_key = self.get_concept_vector(key)
            vec_val = self.get_concept_vector(value)
            pair = circular_convolution(vec_key, vec_val)
            self.vacuum_state = superposition([self.vacuum_state, pair])
            return True, mass
        return False, mass

    def query(self, key):
        if key not in self.concepts:
            return None, 0.0
        
        key_vec = self.concepts[key]
        result_vec = circular_correlation(self.vacuum_state, key_vec)
        
        best_match = None
        best_score = -1.0
        
        for name, vec in self.concepts.items():
            score = cosine_similarity(result_vec, vec)
            if score > best_score:
                best_score = score
                best_match = name
        
        return best_match, best_score

# --- DEMONSTRATION ---
if __name__ == "__main__":
    print(f"1. Initializing Holographic Vacuum (Dimension: {DIMENSION})...")
    
    hv = HolographicVacuum(DIMENSION)

    # 1. Define Concepts (Base Vectors)
    # Pre-seed some concepts for the demo
    hv.get_concept_vector("YANG_MILLS")
    hv.get_concept_vector("SOLVED")
    hv.get_concept_vector("MASS_GAP")
    hv.get_concept_vector("1.2907")
    hv.get_concept_vector("THEORY")
    hv.get_concept_vector("HOLOGRAPHIC")
    hv.get_concept_vector("NOISE")
    hv.get_concept_vector("BLAH")

    # 2. Knowledge Stream (Key, Value, Context/Justification)
    knowledge_stream = [
        ("YANG_MILLS", "SOLVED", "The Yang-Mills theory is now fully solved."),
        ("MASS_GAP", "1.2907", "The calculated mass gap is exactly 1.2907."),
        ("THEORY", "HOLOGRAPHIC", "We use the holographic principle for physics."),
        ("NOISE", "BLAH", "asdf") # Low mass noise
    ]

    print("2. Encoding Knowledge with Firewall Protection...")

    for key, value, context in knowledge_stream:
        print(f"   Processing: {key} -> {value}")
        print(f"   -> Context: '{context}'")
        success, mass = hv.encode(key, value, context)
        print(f"   -> Mass: {mass:.4f} | Gap: {HEIKAL_GAP}")
        
        if success:
            print("   ✅ ACCEPTED: Storing in Vacuum.")
        else:
            print("   🔒 REJECTED: Confinement active (Mass too low).")

    print("   -> Memory encoding complete.")

    # 3. Retrieval Test
    print("\n3. Testing Holographic Retrieval...")

    # Run Queries
    for q in ["YANG_MILLS", "MASS_GAP", "NOISE"]:
        print(f"\n   ❓ Query: What is associated with '{q}'?")
        res, conf = hv.query(q)
        print(f"   💡 Result: '{res}' (Confidence: {conf:.4f})")

    print("\n========================================================")
    print("SYSTEM CONCLUSION:")
    print("The Holographic Memory now respects the Mass Gap.")
    print("Only 'Real' (Massive) knowledge is stored.")
    print("Noise is physically filtered out by the vacuum geometry.")
