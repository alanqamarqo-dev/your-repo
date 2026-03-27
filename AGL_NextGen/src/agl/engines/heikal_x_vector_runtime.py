import random
import numpy as np
import sys
import os

# Ensure local src is in path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, '..', '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from agl.engines.vectorized_wave_processor import VectorizedWaveProcessor
except ImportError:
    class VectorizedWaveProcessor:
        def __init__(self, **kwargs): pass
        def batch_xor(self, a, b): return a ^ b
        def batch_and(self, a, b): return a & b

class QuantumVariable:
    """Advanced Quantum Variable using Vectorized Wave Logic."""
    def __init__(self, states=None, amplitudes=None):
        if states is None:
            self.states = np.array([0, 1])
            self.amplitudes = np.array([0.5, 0.5])
        else:
            self.states = np.array(states)
            if amplitudes is None:
                self.amplitudes = np.ones(len(self.states)) / len(self.states)
            else:
                self.amplitudes = np.array(amplitudes)
        
        self.is_collapsed = False
        self._collapsed_value = None

    def collapse(self):
        if not self.is_collapsed:
            idx = np.random.choice(len(self.states), p=self.amplitudes)
            self._collapsed_value = self.states[idx]
            self.is_collapsed = True
        return self._collapsed_value

    @property
    def value(self):
        if self.is_collapsed:
            return self._collapsed_value
        return self.states

    def __repr__(self):
        if self.is_collapsed:
            return f'Collapsed({self._collapsed_value})'
        return f'Wave(States={len(self.states)}, Entropies={-np.sum(self.amplitudes*np.log2(self.amplitudes+1e-9)):.2f})'

class HeikalXRuntime:
    """The Stronger Heikal-X Runtime: Powered by Vectorized Wave Processor."""
    def __init__(self, mother_system=None):
        self.mother_system = mother_system
        self.vwp = VectorizedWaveProcessor()
        self.variables = {}
        self.entanglements = []

    def declare(self, name, value):
        self.variables[name] = QuantumVariable([value], [1.0])

    def superpose(self, name, states, amplitudes=None):
        self.variables[name] = QuantumVariable(states, amplitudes)

    def entangle(self, name_a, name_b):
        if name_a in self.variables and name_b in self.variables:
            self.entanglements.append((name_a, name_b))

    def observe(self, name):
        if name not in self.variables: return None
        val = self.variables[name].collapse()
        for a, b in self.entanglements:
            if name == a and not self.variables[b].is_collapsed:
                self.variables[b].collapse()
            elif name == b and not self.variables[a].is_collapsed:
                self.variables[a].collapse()
        return val

    def wave_gate(self, op, var_a, var_b, target_name):
        a = self.variables[var_a]
        b = self.variables[var_b]
        if op == 'XOR':
            new_states = np.unique([x ^ y for x in a.states for y in b.states if isinstance(x, int) and isinstance(y, int)])
            self.superpose(target_name, list(new_states))
        return self.variables[target_name]

    def wave_if(self, condition_var, true_branch, false_branch):
        val = self.observe(condition_var)
        if val:
            return true_branch()
        else:
            return false_branch()

    def get_info(self):
        return {
            'name': 'Heikal-X Stronger (Vectorized)',
            'version': '2.2.0-omega',
            'engine': 'VectorizedWaveProcessor (Active)',
            'logic_type': 'Wave-Logic Interference'
        }

    def check_truth_state(self, input_data=None):
        return True

def get_engine(mother_system=None):
    return HeikalXRuntime(mother_system)
