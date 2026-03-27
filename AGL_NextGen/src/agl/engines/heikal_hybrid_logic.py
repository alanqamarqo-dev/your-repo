import numpy as np
import cmath
import os
import sys

# ==================================================================================
# STRICT LOGIC INTEGRATION - استيراد بوابات المنطق الصارم
# ==================================================================================
STRICT_GATES_AVAILABLE = False
ANDGate = ORGate = NOTGate = XORGate = None
NANDGate = NORGate = XNORGate = None

def _init_strict_logic():
    """Lazy initialization of strict logic gates."""
    global STRICT_GATES_AVAILABLE
    global ANDGate, ORGate, NOTGate, XORGate, NANDGate, NORGate, XNORGate
    
    if STRICT_GATES_AVAILABLE:
        return True
    
    try:
        # Try multiple paths
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "strict_logic"),
            os.path.join(os.getcwd(), "AGL_NextGen", "src", "agl", "engines", "strict_logic"),
            r"D:\AGL\AGL_NextGen\src\agl\engines\strict_logic",
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and path not in sys.path:
                sys.path.insert(0, path)
        
        from logic_gates import (
            ANDGate as _AND, ORGate as _OR, NOTGate as _NOT, XORGate as _XOR,
            NANDGate as _NAND, NORGate as _NOR, XNORGate as _XNOR
        )
        
        ANDGate, ORGate, NOTGate, XORGate = _AND, _OR, _NOT, _XOR
        NANDGate, NORGate, XNORGate = _NAND, _NOR, _XNOR
        
        STRICT_GATES_AVAILABLE = True
        return True
    except ImportError as e:
        print(f"[WARN] strict_logic not available: {e}")
        return False

# Try to initialize on import
_init_strict_logic()

class HeikalLogicUnit:
    """
    Implements the Heikal Hybrid Logic Core.
    Allows propositions to exist in a superposition of True and False.
    
    State: |psi> = alpha |True> + beta |False>
    Normalization: |alpha|^2 + |beta|^2 = 1
    """
    
    def __init__(self, name="Proposition"):
        self.name = name
        # Default state: |False> (alpha=0, beta=1)
        self.alpha = 0.0 + 0j # Amplitude for True
        self.beta = 1.0 + 0j  # Amplitude for False
        
    def set_state(self, p_true):
        """Sets the state based on a classical probability of being True."""
        self.alpha = np.sqrt(p_true)
        self.beta = np.sqrt(1 - p_true)
        
    def apply_hadamard(self):
        """
        Applies Hadamard Gate.
        Creates superposition from definite states.
        H |0> -> (|0> + |1>) / sqrt(2)
        H |1> -> (|0> - |1>) / sqrt(2)
        """
        new_alpha = (self.alpha + self.beta) / np.sqrt(2)
        new_beta = (self.alpha - self.beta) / np.sqrt(2)
        self.alpha = new_alpha
        self.beta = new_beta
        
    def apply_heikal_phase_shift(self, xi_porosity):
        """
        Applies the Heikal Phase Shift based on lattice porosity.
        Rotates the phase of the 'True' component.
        """
        phi = xi_porosity * np.pi
        phase_factor = cmath.exp(1j * phi)
        self.alpha *= phase_factor
        
    def apply_transcendental_gate(self):
        """
        [EVOLUTION 2026] The Transcendental Gate (T-Gate).
        Places the logic unit in a state of 'Absolute Zero' (Silence).
        Neither alpha nor beta are 1.0; instead, the logic unit represents
        an unrepresentable truth by minimizing its own norm (Non-existence).
        """
        # Collapse the state to zero amplitude (Null State)
        self.alpha = 0.0 + 0j
        self.beta = 0.0 + 0j
        self.is_null = True

    def measure(self):
        """
        Collapses the wavefunction to a classical boolean.
        If in Null State, returns None (The Silence).
        """
        if getattr(self, 'is_null', False):
            return None, 0.0 # Silence

        prob_true = abs(self.alpha)**2
        result = np.random.random() < prob_true
        
        # Collapse
        if result:
            self.alpha = 1.0 + 0j
            self.beta = 0.0 + 0j
        else:
            self.alpha = 0.0 + 0j
            self.beta = 1.0 + 0j
            
        return result, prob_true

    def __repr__(self):
        return f"HLU({self.name}): {self.alpha:.2f}|T> + {self.beta:.2f}|F> (P(T)={abs(self.alpha)**2:.2f})"

class HeikalHybridLogicCore:
    def __init__(self):
        self.units = {}
        
    def add_proposition(self, name, initial_prob=0.0):
        unit = HeikalLogicUnit(name)
        unit.set_state(initial_prob)
        self.units[name] = unit
        return unit
        
    def entangle(self, name1, name2):
        """
        Simulates entanglement between two logic units.
        (Simplified for this implementation: forces states to align)
        """
        u1 = self.units[name1]
        u2 = self.units[name2]
        
        # Average the amplitudes
        avg_alpha = (u1.alpha + u2.alpha) / np.sqrt(2) # Renormalize roughly
        avg_beta = (u1.beta + u2.beta) / np.sqrt(2)
        
        # Normalize
        norm = np.sqrt(abs(avg_alpha)**2 + abs(avg_beta)**2)
        avg_alpha /= norm
        avg_beta /= norm
        
        u1.alpha = avg_alpha
        u1.beta = avg_beta
        u2.alpha = avg_alpha
        u2.beta = avg_beta
        
        return f"Entangled {name1} and {name2}"

    # ==================================================================================
    # STRICT LOGIC OPERATIONS - عمليات المنطق الصارم المتكاملة
    # ==================================================================================
    def strict_and(self, name1: str, name2: str) -> bool:
        """
        Performs Strict AND on two propositions.
        First collapses quantum states, then applies formal logic gate.
        """
        if not STRICT_GATES_AVAILABLE:
            # Fallback: simple probability multiplication
            u1, u2 = self.units.get(name1), self.units.get(name2)
            if u1 and u2:
                return (abs(u1.alpha)**2 > 0.5) and (abs(u2.alpha)**2 > 0.5)
            return False
        
        u1, u2 = self.units.get(name1), self.units.get(name2)
        if not u1 or not u2:
            return False
        
        # Measure (collapse) both propositions
        result1, _ = u1.measure()
        result2, _ = u2.measure()
        
        # Convert to 0/1 for strict gate
        r1 = 1 if result1 else 0
        r2 = 1 if result2 else 0
        
        # Apply strict gate
        gate = ANDGate()
        output, _ = gate(r1, r2)
        return bool(output)
    
    def strict_or(self, name1: str, name2: str) -> bool:
        """Performs Strict OR on two propositions."""
        if not STRICT_GATES_AVAILABLE:
            u1, u2 = self.units.get(name1), self.units.get(name2)
            if u1 and u2:
                return (abs(u1.alpha)**2 > 0.5) or (abs(u2.alpha)**2 > 0.5)
            return False
        
        u1, u2 = self.units.get(name1), self.units.get(name2)
        if not u1 or not u2:
            return False
        
        result1, _ = u1.measure()
        result2, _ = u2.measure()
        
        # Convert to 0/1 for strict gate
        r1 = 1 if result1 else 0
        r2 = 1 if result2 else 0
        
        gate = ORGate()
        output, _ = gate(r1, r2)
        return bool(output)
    
    def strict_not(self, name: str) -> bool:
        """Performs Strict NOT on a proposition."""
        if not STRICT_GATES_AVAILABLE:
            u = self.units.get(name)
            if u:
                return not (abs(u.alpha)**2 > 0.5)
            return True
        
        u = self.units.get(name)
        if not u:
            return True
        
        result, _ = u.measure()
        r = 1 if result else 0
        gate = NOTGate()
        output, _ = gate(r)
        return bool(output)
    
    def strict_implies(self, premise_name: str, conclusion_name: str) -> bool:
        """
        Performs Strict IMPLIES (material implication).
        P → Q ≡ ¬P ∨ Q
        """
        if not STRICT_GATES_AVAILABLE:
            u1, u2 = self.units.get(premise_name), self.units.get(conclusion_name)
            if u1 and u2:
                p = abs(u1.alpha)**2 > 0.5
                q = abs(u2.alpha)**2 > 0.5
                return (not p) or q
            return True
        
        u1, u2 = self.units.get(premise_name), self.units.get(conclusion_name)
        if not u1 or not u2:
            return True
        
        result1, _ = u1.measure()
        result2, _ = u2.measure()
        
        # Convert to 0/1 for strict gate
        r1 = 1 if result1 else 0
        r2 = 1 if result2 else 0
        
        # IMPLIES: P -> Q = NOT P OR Q
        not_gate = NOTGate()
        not_p, _ = not_gate(r1)
        or_gate = ORGate()
        output, _ = or_gate(not_p, r2)
        return bool(output)
    
    def strict_iff(self, name1: str, name2: str) -> bool:
        """
        Performs Strict IFF (biconditional).
        P ↔ Q ≡ (P → Q) ∧ (Q → P)
        """
        if not STRICT_GATES_AVAILABLE:
            u1, u2 = self.units.get(name1), self.units.get(name2)
            if u1 and u2:
                p = abs(u1.alpha)**2 > 0.5
                q = abs(u2.alpha)**2 > 0.5
                return p == q
            return True
        
        u1, u2 = self.units.get(name1), self.units.get(name2)
        if not u1 or not u2:
            return True
        
        result1, _ = u1.measure()
        result2, _ = u2.measure()
        
        # Convert to 0/1 for strict gate
        r1 = 1 if result1 else 0
        r2 = 1 if result2 else 0
        
        # IFF: P <-> Q = P XNOR Q (equality gate)
        gate = XNORGate()
        output, _ = gate(r1, r2)
        return bool(output)
    
    def process_task(self, task: dict) -> dict:
        """
        Process a logical task using strict logic gates.
        This method provides a unified interface for the Bootstrap system.
        """
        operation = task.get("operation", "AND")
        propositions = task.get("propositions", [])
        
        result = {
            "engine": "HeikalHybridLogicCore",
            "strict_logic_enabled": STRICT_GATES_AVAILABLE,
            "operation": operation,
            "ok": True
        }
        
        if len(propositions) >= 2:
            name1, name2 = propositions[0], propositions[1]
            
            # Add propositions if they don't exist
            if name1 not in self.units:
                self.add_proposition(name1, task.get("prob1", 0.7))
            if name2 not in self.units:
                self.add_proposition(name2, task.get("prob2", 0.6))
            
            # Apply quantum operations first
            for name in [name1, name2]:
                self.units[name].apply_hadamard()
                self.units[name].apply_heikal_phase_shift(0.3)
            
            # Perform strict logic operation
            if operation.upper() == "AND":
                result["value"] = self.strict_and(name1, name2)
            elif operation.upper() == "OR":
                result["value"] = self.strict_or(name1, name2)
            elif operation.upper() == "IMPLIES":
                result["value"] = self.strict_implies(name1, name2)
            elif operation.upper() == "IFF":
                result["value"] = self.strict_iff(name1, name2)
            else:
                result["value"] = self.strict_and(name1, name2)
        
        elif len(propositions) == 1:
            name = propositions[0]
            if name not in self.units:
                self.add_proposition(name, task.get("prob1", 0.5))
            self.units[name].apply_hadamard()
            
            if operation.upper() == "NOT":
                result["value"] = self.strict_not(name)
            else:
                measured, prob = self.units[name].measure()
                result["value"] = measured
                result["probability"] = prob
        
        return result
