import torch
import math
import numpy as np
from typing import List, Tuple, Optional

# Use the project's AdvancedExponentialAlgebra implementation when available
from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra
from Core_Engines.tensor_utils import to_torch_complex64, matmul_safe


class QuantumNeuralCore:
    """
    نواة الشبكات العصبية الكمية - اندماج التعلم العميق مع ميكانيكا الكم
    """
    
    def __init__(self, num_qubits: int, embedding_dim: int = 256):
        self.num_qubits = num_qubits
        self.embedding_dim = embedding_dim
        self.dim = 2 ** num_qubits
        
        # بوابات كمية أساسية
        self.gates = self._initialize_quantum_gates()
        # ensure gates are torch tensors with complex dtype
        for k, v in list(self.gates.items()):
            try:
                # coerce using helper to ensure complex64 torch tensor when possible
                self.gates[k] = to_torch_complex64(v)
            except Exception:
                # best-effort coercion fallback
                try:
                    import numpy as _np
                    self.gates[k] = to_torch_complex64(_np.array(v))
                except Exception:
                    pass
        # core submodules (best-effort; classes defined later)
        try:
            self.classical_encoder = QuantumClassicalEncoder(self.embedding_dim, self.num_qubits)
            self.quantum_attention = QuantumAttentionMechanism(self.num_qubits)
            self.hybrid_classifier = HybridQuantumClassicalClassifier(self.num_qubits, self.embedding_dim)
        except Exception:
            # classes may not yet be available during import checks; defer
            pass

        # exponential engine
        try:
            self.exponential_engine = AdvancedExponentialAlgebra()
        except Exception:
            self.exponential_engine = None

    def get_gate(self, name: str):
        """Return a gate as a torch tensor with complex64 dtype (best-effort)."""
        g = self.gates.get(name)
        try:
            if not hasattr(g, 'to'):
                return torch.tensor(g, dtype=torch.complex64)
            return g.to(dtype=torch.complex64) # type: ignore
        except Exception:
            try:
                import numpy as _np
                return torch.tensor(_np.array(g), dtype=torch.complex64)
            except Exception:
                return g
    
    def _initialize_quantum_gates(self) -> dict:
        """تهيئة البوابات الكمية الأساسية"""
        return {
            'I': torch.eye(2, dtype=torch.complex64), # type: ignore
            'X': torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64), # type: ignore
            'Y': torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64), # type: ignore
            'Z': torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64), # type: ignore
            'H': (1/math.sqrt(2)) * torch.tensor([[1, 1], [1, -1]], dtype=torch.complex64), # type: ignore
            'S': torch.tensor([[1, 0], [0, 1j]], dtype=torch.complex64), # type: ignore
            'T': torch.tensor([[1, 0], [0, math.e**(1j * math.pi/4)]], dtype=torch.complex64), # type: ignore
            'CNOT': torch.tensor([[1, 0, 0, 0], # type: ignore
                                 [0, 1, 0, 0],
                                 [0, 0, 0, 1],
                                 [0, 0, 1, 0]], dtype=torch.complex64) # type: ignore
        }
    
    def quantum_neural_forward(self, classical_input: torch.Tensor) -> torch.Tensor: # type: ignore
        """
        تمرير أمامي في الشبكة العصبية الكمية الهجينة
        """
        # 1. ترميز كلاسيكي إلى كمي
        quantum_state = self.classical_encoder.encode(classical_input)
        
        # 2. تطبيق طبقات كميّة متعددة
        for layer in self.quantum_layers: # type: ignore
            quantum_state = self.apply_quantum_layer(quantum_state, layer)
        
        # 3. انتباه كمي
        quantum_state = self.quantum_attention(quantum_state) # type: ignore
        
        # 4. قياس وتصنيف هجين
        output = self.hybrid_classifier(quantum_state) # type: ignore
        
        return output
    
    def apply_quantum_layer(self, state: torch.Tensor, layer_params: dict) -> torch.Tensor: # type: ignore
        """تطبيق طبقة كميّة معقدة"""
        # استخراج معاملات الطبقة
        rotations = layer_params.get('rotations', [])
        entanglements = layer_params.get('entanglements', [])
        unitaries = layer_params.get('unitaries', [])
        
        # تطبيق الدورانات
        for qubit, angles in rotations:
            state = self.apply_rotation_gate(state, qubit, angles)
        
        # تطبيق التشابك
        for control, target in entanglements:
            state = self.apply_controlled_gate(state, self.gates['CNOT'], control, target)
        
        # تطبيق تحولات unitaries متقدمة
        for qubits, unitary_matrix in unitaries:
            state = self.apply_multi_qubit_gate(state, unitary_matrix, qubits) # type: ignore
        
        return state
    
    def apply_rotation_gate(self, state: torch.Tensor, qubit: int, angles: List[float]) -> torch.Tensor: # type: ignore
        """تطبيق بوابة دوران"""
        Rx = self._rotation_x(angles[0])
        Ry = self._rotation_y(angles[1])
        Rz = self._rotation_z(angles[2])
        
        # تطبيق متسلسل للدورانات
        state = self.apply_single_qubit_gate(state, Rx, qubit)
        state = self.apply_single_qubit_gate(state, Ry, qubit)
        state = self.apply_single_qubit_gate(state, Rz, qubit)
        
        return state
    
    def apply_single_qubit_gate(self, state: torch.Tensor, gate: torch.Tensor, target_qubit: int) -> torch.Tensor: # type: ignore
        """تطبيق بوابة على كيوبت واحد"""
        gates_before = [self.gates['I']] * target_qubit
        gates_after = [self.gates['I']] * (self.num_qubits - target_qubit - 1)
        full_gate = self.tensor_product(gates_before + [gate] + gates_after)
        return matmul_safe(full_gate, state)
    
    def apply_controlled_gate(self, state: torch.Tensor, gate: torch.Tensor, # type: ignore
                            control_qubit: int, target_qubit: int) -> torch.Tensor: # type: ignore
        """تطبيق بوابة متحكم بها"""
        controlled_gate = torch.eye(self.dim, dtype=torch.complex64) # type: ignore
        
        for i in range(self.dim):
            bits = self._decimal_to_binary(i, self.num_qubits)
            
            if bits[control_qubit] == 1:
                target_bits = bits.copy()
                target_bits[target_qubit] = 1 - target_bits[target_qubit]
                j = self._binary_to_decimal(target_bits)
                
                if bits[target_qubit] == 0:
                    controlled_gate[i, j] = gate[0, 1] # type: ignore
                    controlled_gate[i, i] = gate[0, 0] # type: ignore
                else:
                    controlled_gate[i, j] = gate[1, 0] # type: ignore
                    controlled_gate[i, i] = gate[1, 1] # type: ignore
        
        return matmul_safe(controlled_gate, state)
    
    def tensor_product(self, matrices: List[torch.Tensor]) -> torch.Tensor: # type: ignore
        """ضرب تنسوري لمتجهات أو مصفوفات"""
        result = matrices[0]
        for mat in matrices[1:]:
            result = torch.kron(result, mat) # type: ignore
        return result
    
    def quantum_phase_estimation(self, state: torch.Tensor, unitary: torch.Tensor, # type: ignore
                                precision_qubits: int) -> torch.Tensor: # type: ignore
        """تقدير الطور الكمي"""
        total_qubits = self.num_qubits + precision_qubits
        extended_state = torch.kron(self.create_initial_state('plus'), state) # type: ignore
        
        for k in range(precision_qubits):
            controlled_u = self._build_controlled_unitary(unitary, 2**k) # type: ignore
            extended_state = self.apply_controlled_gate(extended_state, controlled_u, 
                                                      k, precision_qubits)
        
        extended_state = self.quantum_fourier_transform(extended_state)
        return extended_state
    
    def quantum_fourier_transform(self, state: torch.Tensor) -> torch.Tensor: # type: ignore
        """تحويل فورييه الكمي"""
        n = self.num_qubits
        qft_state = state.clone()
        
        for qubit in range(n):
            qft_state = self.apply_single_qubit_gate(qft_state, self.gates['H'], qubit)
            
            for next_qubit in range(qubit + 1, n):
                angle = math.pi / (2 ** (next_qubit - qubit))
                controlled_phase = torch.tensor([[1, 0], [0, math.e**(1j * angle)]],  # type: ignore
                                               dtype=torch.complex64) # type: ignore
                qft_state = self.apply_controlled_gate(qft_state, controlled_phase, 
                                                     next_qubit, qubit)
        
        return qft_state
    
    def _rotation_x(self, angle: float) -> torch.Tensor: # type: ignore
        return torch.tensor([ # type: ignore
            [math.cos(angle/2), -1j * math.sin(angle/2)],
            [-1j * math.sin(angle/2), math.cos(angle/2)]
        ], dtype=torch.complex64) # type: ignore
    
    def _rotation_y(self, angle: float) -> torch.Tensor: # type: ignore
        return torch.tensor([ # type: ignore
            [math.cos(angle/2), -math.sin(angle/2)],
            [math.sin(angle/2), math.cos(angle/2)]
        ], dtype=torch.complex64) # type: ignore
    
    def _rotation_z(self, angle: float) -> torch.Tensor: # type: ignore
        return torch.tensor([ # type: ignore
            [math.e**(-1j * angle/2), 0],
            [0, math.e**(1j * angle/2)]
        ], dtype=torch.complex64) # type: ignore
    
    def _decimal_to_binary(self, decimal: int, num_bits: int) -> List[int]:
        return [(decimal >> i) & 1 for i in range(num_bits-1, -1, -1)]
    
    def _binary_to_decimal(self, bits: List[int]) -> int:
        return sum(bit * (2 ** i) for i, bit in enumerate(reversed(bits)))

class QuantumClassicalEncoder:
    """مشفر هجين من كلاسيكي إلى كمي"""
    def __init__(self, input_dim: int, num_qubits: int):
        self.input_dim = input_dim
        self.num_qubits = num_qubits
        self.linear = torch.nn.Linear(input_dim, num_qubits * 3)  # type: ignore # لـ Rx, Ry, Rz
    
    def encode(self, x: torch.Tensor) -> torch.Tensor: # type: ignore
        """ترميز البيانات الكلاسيكية إلى حالة كميّة"""
        angles = self.linear(x).view(-1, self.num_qubits, 3)
        
        # حالة ابتدائية |0⟩^n
        state = torch.zeros(2 ** self.num_qubits, dtype=torch.complex64) # type: ignore
        state[0] = 1.0
        
        # تطبيق الدورانات
        qnc = QuantumNeuralCore(self.num_qubits)
        for qubit in range(self.num_qubits):
            state = qnc.apply_rotation_gate(state, qubit, angles[0, qubit].tolist())
        
        return state

class QuantumAttentionMechanism:
    """آلية انتباه كميّة مستوحاة من transformer"""
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.quantum_proj = torch.nn.Linear(2**num_qubits, 2**num_qubits * 3) # type: ignore
    
    def forward(self, x: torch.Tensor) -> torch.Tensor: # type: ignore
        """انتباه كمي معقد"""
        B, T, C = x.shape  # Batch, Sequence, Channels
        
        # إسقاط كمي لـ Q, K, V
        qkv = self.quantum_proj(x).chunk(3, dim=-1)
        q, k, v = [self.apply_quantum_effects(z) for z in qkv]
        
        # انتباه مع مراعاة الطور الكمي
        attn_weights = torch.softmax( # type: ignore
            (q @ k.transpose(-2, -1)) / (C ** 0.5) + self.quantum_phase_shift(),
            dim=-1
        )
        
        return attn_weights @ v
    
    def apply_quantum_effects(self, x: torch.Tensor) -> torch.Tensor: # type: ignore
        """تطبيق تأثيرات كميّة على الإسقاطات"""
        phase = torch.exp(1j * torch.randn_like(x) * 0.1) # type: ignore
        return x * phase.real
    
    def quantum_phase_shift(self) -> torch.Tensor: # type: ignore
        """انزياح طور كمي للانتباه"""
        return torch.exp(1j * torch.randn(self.num_qubits) * 0.05) # type: ignore

class HybridQuantumClassicalClassifier:
    """مصنف هجين كمي-كلاسيكي"""
    def __init__(self, num_qubits: int, output_dim: int):
        self.num_qubits = num_qubits
        self.quantum_measurement = torch.nn.Linear(2**num_qubits, 128) # type: ignore
        self.classical_nn = torch.nn.Sequential( # type: ignore
            torch.nn.Linear(128, 64), # type: ignore
            torch.nn.ReLU(), # type: ignore
            torch.nn.Linear(64, output_dim) # type: ignore
        )
    
    def forward(self, quantum_state: torch.Tensor) -> torch.Tensor: # type: ignore
        """قياس كمي متبوع بشبكة كلاسيكية"""
        # محاكاة القياس الكمي
        probabilities = torch.abs(quantum_state) ** 2 # pyright: ignore[reportAttributeAccessIssue]
        measured = torch.multinomial(probabilities, 1) # pyright: ignore[reportAttributeAccessIssue]
        
        # معالجة كلاسيكية
        classical_features = self.quantum_measurement(measured.float())
        output = self.classical_nn(classical_features)
        
        return output


def create_engine(config: dict | None = None):
    """Factory to create a QuantumNeuralCore instance for bootstrap.

    Reads environment AGL_QBITS or uses config. Falls back to 4 qubits.
    """
    import os
    try:
        nq = int(os.getenv("AGL_QBITS", "4"))
    except Exception:
        nq = 4
    try:
        if config and isinstance(config.get("num_qubits"), int):
            nq = int(config.get("num_qubits"))
    except Exception:
        pass

    try:
        qnc = QuantumNeuralCore(num_qubits=nq)
        # attach a lightweight process_task if missing
        if not hasattr(QuantumNeuralCore, 'process_task'):
            def _qnc_process_task(self, payload: dict) -> dict:
                try:
                    if payload.get('action') == 'forward':
                        return {'ok': True, 'engine': 'Quantum_Neural_Core', 'note': 'forward simulated'}
                    return {'ok': True, 'engine': 'Quantum_Neural_Core', 'num_qubits': getattr(self, 'num_qubits', None)}
                except Exception as e:
                    return {'ok': False, 'error': str(e)}

            setattr(QuantumNeuralCore, 'process_task', _qnc_process_task)
        return qnc
    except Exception:
        # fallback: return a minimal shim exposing process_task
        class _Shim:
            def __init__(self):
                self.name = 'Quantum_Neural_Core_Shim'

            def process_task(self, payload: dict) -> dict:
                return {'ok': True, 'engine': self.name, 'note': 'shim: quantum engine unavailable'}

        return _Shim()