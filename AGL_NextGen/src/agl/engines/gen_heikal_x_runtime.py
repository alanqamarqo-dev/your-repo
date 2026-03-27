import random
import numpy as np

class QuantumVariable:
    def __init__(self, states=None, amplitudes=None):
        if states is None:
            self.states = [None]
            self.amplitudes = [1.0]
        else:
            self.states = states
            self.amplitudes = amplitudes if amplitudes else [1.0/len(states)] * len(states)
        self.is_collapsed = False
        self._collapsed_value = None

    def collapse(self):
        if not self.is_collapsed:
            self._collapsed_value = random.choices(self.states, weights=self.amplitudes)[0]
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
        return f'Superposition({list(zip(self.states, self.amplitudes))})'

class HeikalXRuntime:
    def __init__(self, mother_system=None):
        self.mother_system = mother_system
        self.variables = {}
        self.entanglements = []

    def declare(self, name, value):
        if isinstance(value, list):
            self.variables[name] = QuantumVariable(value)
        else:
            self.variables[name] = QuantumVariable([value], [1.0])

    def superpose(self, name, states, amplitudes=None):
        self.variables[name] = QuantumVariable(states, amplitudes)

    def entangle(self, name_a, name_b):
        self.entanglements.append((name_a, name_b))

    def observe(self, name):
        if name in self.variables:
            val = self.variables[name].collapse()
            for a, b in self.entanglements:
                if name == a and b in self.variables:
                    self.variables[b].collapse()
                elif name == b and a in self.variables:
                    self.variables[a].collapse()
            return val
        return None

    def wave_if(self, condition_var, true_branch, false_branch):
        val = self.observe(condition_var)
        if val:
            return true_branch()
        else:
            return false_branch()

    def get_info(self):
        return {
            'name': 'Heikal-X Runtime',
            'version': '1.1.0-fixed',
            'logic_type': 'Wave-Logic',
            'variables_count': len(self.variables)
        }

    def check_truth_state(self, input_data=None):
        return True

def get_engine(mother_system=None):
    return HeikalXRuntime(mother_system)
