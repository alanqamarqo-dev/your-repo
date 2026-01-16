import numpy as np
import cmath

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
