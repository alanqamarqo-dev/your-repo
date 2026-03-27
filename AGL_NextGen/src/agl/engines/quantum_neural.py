import torch
import math
import numpy as np
from typing import List, Tuple, Optional
import json
import re
import uuid
import ast
import os
import requests

# [AGL NEXTGEN ADAPTATION]
# Try to import HostedLLMAdapter, else None
try:
    from agl.engines.learning.hosted_llm_adapter import HostedLLMAdapter
except ImportError:
    HostedLLMAdapter = None

# Use NextGen paths for utils
try:
    from agl.lib.utils.llm_tools import build_llm_url
except ImportError:
    def build_llm_url(endpoint, base): 
        base = base.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base}/{endpoint}"

try:
    from agl.engines.advanced_exponential_algebra import AdvancedExponentialAlgebra
    from agl.engines.tensor_utils import to_torch_complex64, matmul_safe
except ImportError:
    # Fallback if specific AGL engines not found
    AdvancedExponentialAlgebra = None
    def to_torch_complex64(x): return torch.tensor(x, dtype=torch.complex64)
    def matmul_safe(a, b): return torch.matmul(a, b)


class QuantumNeuralCore:
    """
    Quantum Neural Core (QNC) - Hybrid Deep Learning & Quantum Mechanics Engine.
    [Updated for AGL_NextGen Integration]
    
    This class implements a theoretical framework for processing information using
    simulated quantum states (qubits) coupled with classical neural networks.
    
    Key Components:
    1. Quantum Gates (H, X, Y, Z, CNOT): Basic unitary operations.
    2. Classical Encoder: Maps classical vectors to quantum amplitudes.
    3. Quantum Attention: Focuses processing on high-probability states.
    4. Exponential Algebra: Handles complex number operations efficiently.
    
    Resonance Status:
    - Complexity (V): High (Quantum Physics + Deep Learning).
    - Coherence (E): Enhanced via Docstrings and Type Hinting.
    """
    
    def __init__(self, num_qubits: int = 4, embedding_dim: int = 256):
        """
        Initialize the Quantum Neural Core.
        
        Args:
            num_qubits (int): Number of simulated qubits (determines state space size 2^N).
            embedding_dim (int): Dimension of the classical input vector.
        """
        self.num_qubits = num_qubits
        self.embedding_dim = embedding_dim
        self.dim = 2 ** num_qubits
        self.name = "QuantumNeuralCore_NextGen"
        
        # LLM Configuration for Shim
        self.llm_base_url = os.getenv("AGL_LLM_BASEURL", "http://localhost:11434")
        self.model = os.getenv("AGL_LLM_MODEL", "qwen2.5:7b-instruct")

        # Initialize Quantum Gates
        self.gates = self._initialize_quantum_gates()
        # Ensure gates are torch tensors with complex dtype for numerical stability
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
        
        # Initialize Submodules (Best-Effort)
        try:
            self.classical_encoder = QuantumClassicalEncoder(self.embedding_dim, self.num_qubits)
            self.quantum_attention = QuantumContextFocuser(self.num_qubits)
            # hybrid classifier initialization removed during cleanup
        except Exception:
            # if imports/classes not available during static checks, set safe defaults
            self.classical_encoder = None
            self.quantum_attention = None

        # exponential engine
        try:
            if AdvancedExponentialAlgebra:
                self.exponential_engine = AdvancedExponentialAlgebra()
            else:
                self.exponential_engine = None
        except Exception:
            self.exponential_engine = None

        # LLM adapter instance (optional)
        try:
            if HostedLLMAdapter is not None:
                self.llm = HostedLLMAdapter()
            else:
                self.llm = None
        except Exception:
            self.llm = None

    def get_gate(self, name: str) -> torch.Tensor:
        """
        Retrieve a quantum gate matrix by name.
        
        Args:
            name (str): Gate identifier ('H', 'X', 'CNOT', etc.).
            
        Returns:
            torch.Tensor: Complex64 matrix representing the gate.
        """
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
        """
        Initialize standard quantum gates as complex matrices.
        
        Returns:
            dict: Mapping of gate names to torch tensors.
        """
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
        Execute a forward pass through the Hybrid Quantum-Neural Network.
        
        Process:
        1. Encode classical input into quantum amplitudes.
        2. Apply quantum attention/gates.
        3. Measure/Decode back to classical vector.
        
        Args:
            classical_input (torch.Tensor): Input vector.
            
        Returns:
            torch.Tensor: Processed output vector.
        """
        if not self.classical_encoder:
            # Fallback if encoder not init
            return classical_input

        # 1. ترميز كلاسيكي إلى كمي
        quantum_state = self.classical_encoder.encode(classical_input)
        
        # 2. تطبيق طبقات كميّة متعددة (Placeholder for now as layers define dynamic)
        # for layer in self.quantum_layers: # type: ignore
        #     quantum_state = self.apply_quantum_layer(quantum_state, layer)
        
        # 3. انتباه كمي
        if self.quantum_attention:
            quantum_state = self.quantum_attention.forward(quantum_state.unsqueeze(0).unsqueeze(0)).squeeze() # type: ignore
        
        # 4. قياس وتصنيف هجين (Placeholder)
        # output = self.hybrid_classifier(quantum_state) # type: ignore
        
        # Return state magnitude as simple decoding
        output = torch.abs(quantum_state)
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

    def _llm_shim(self, prompt: str) -> str:
        """Fallback LLM interaction when HostedLLMAdapter is missing."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}], # Simple chat format
            "temperature": 0.8,
            "stream": False
        }
        
        try:
             # Try standard chat endpoint
             endpoint = build_llm_url('/api/chat', base=self.llm_base_url)
             response = requests.post(endpoint, json=payload, timeout=180)  # Extended for deep analysis
             
             if response.status_code == 200:
                 data = response.json()
                 if 'message' in data:
                     return data['message']['content']
                 if 'choices' in data:
                     return data['choices'][0]['message']['content']
             
             # Try generate endpoint if chat fails
             endpoint = build_llm_url('/api/generate', base=self.llm_base_url)
             gen_payload = {
                 "model": self.model,
                 "prompt": prompt,
                 "stream": False
             }
             response = requests.post(endpoint, json=gen_payload, timeout=180)  # Extended for deep analysis
             if response.status_code == 200:
                 data = response.json()
                 return data.get('response', '')
                 
             return ""
        except Exception as e:
            print(f"[Quantum Shim Error] {e}")
            return ""

    def sample_hypotheses(self, user_query, context=None, num_samples=3):
        """Creative hypothesis generator using the hosted LLM in Deep Mode.

        Returns list of {id, hypothesis, confidence, support}.
        """
        print(f"[Quantum Core] Collapsing wave function for query: {str(user_query)[:40]}...")

        prompt = f"""
        ROLE: You are a Quantum Creativity Engine.
        GOAL: Generate {num_samples} distinct, non-obvious, and creative hypotheses to solve the problem below.
        
        PROBLEM: "{user_query}"
        CONTEXT SUMMARY: {str(context)[:300]}
        
        INSTRUCTIONS:
        - Hypothesis A: Logical but innovative.
        - Hypothesis B: Counter-intuitive (opposite of standard logic).
        - Hypothesis C: High-risk, high-reward (Black Swan).
        
        FORMAT RULES:
        - RETURN ONLY A RAW JSON ARRAY.
        - DO NOT write "Here is the JSON" or markdown blocks (```json).
        - Keys must be in English: "hypothesis", "confidence", "reasoning".
        - Content can be in the same language as the problem (Arabic/English).
        
        EXAMPLE OUTPUT:
        [
            {{"hypothesis": "Use blockchain for transparency", "confidence": 0.9, "reasoning": "Eliminates intermediaries"}},
            {{"hypothesis": "Gamify the supply chain", "confidence": 0.7, "reasoning": "Increases engagement"}}
        ]
        """

        def _extract_best_text(obj):
            # Return the most plausible human-readable string from obj
            if isinstance(obj, str):
                s = obj.strip()
            elif isinstance(obj, dict):
                vals = [v for v in obj.values() if isinstance(v, str) and v.strip()]
                s = max(vals, key=len) if vals else str(obj)
            elif isinstance(obj, list):
                strs = [str(x) for x in obj if isinstance(x, str) and x.strip()]
                s = ' '.join(strs) if strs else str(obj)
            else:
                s = str(obj)
            
            # Additional cleanup
            if isinstance(s, str):
                s = s.strip()
                if s.startswith('{') or s.startswith('['):
                     # try to parse as json again if recursive
                     try:
                         # unsafe, just skip
                         pass 
                     except: pass
            return s

        resp = None
        blob = ''
        
        # 1. Try HostedLLMAdapter
        if hasattr(self, 'llm') and self.llm is not None:
            task = {"question": prompt, "deep_mode": True, "temperature": 0.8}
            try:
                resp = self.llm.process_task(task, timeout_s=60)
            except TypeError:
                try:
                    resp = self.llm.process_task(task)
                except:
                    resp = None
        
        # 2. Extract content from adapter response
        if resp:
            if isinstance(resp, dict):
                content = resp.get('content') or resp
                if isinstance(content, dict):
                    parts = []
                    for k in ('answer', 'reasoning', 'reasoning_long', 'note', 'improved_answer'):
                        v = content.get(k)
                        if isinstance(v, str) and v.strip():
                            parts.append(v.strip())
                    blob = "\n".join(parts) if parts else str(content)
                else:
                    blob = str(content)
            elif isinstance(resp, str):
                blob = resp
        
        # 3. Fallback to Shim if Adapter failed or missing
        if not blob:
            blob = self._llm_shim(prompt)

        # 4. Parse JSON Results
        try:
            if blob:
                s = re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', blob)
                m = re.search(r'(\[.*\])', s, re.DOTALL)
                json_str = None
                if m:
                    json_str = m.group(1)
                else:
                    m2 = re.search(r'(\{.*\})', s, re.DOTALL)
                    if m2:
                        candidate = m2.group(1)
                        if candidate.strip().startswith('{'):
                            json_str = '[' + candidate + ']'

                if json_str:
                    json_str = re.sub(r'(?<=\w)\n(?=\w)', '', json_str)
                    json_str = re.sub(r'(?<=\d)\n(?=[\.\d])', '', json_str)
                    json_str = re.sub(r"[\x00-\x1F]+", ' ', json_str)
                    try:
                        data = json.loads(json_str)
                    except Exception:
                        try:
                            data = json.loads(json_str.replace("'", '"'))
                        except Exception:
                            data = None

                    if data and isinstance(data, list):
                        results = []
                        for item in data:
                            hid = str(uuid.uuid4())
                            if isinstance(item, dict):
                                hyp_raw = item.get('hypothesis') or item.get('الفرضية') or item.get('text') or item.get('answer') or item
                                conf_raw = item.get('confidence') or item.get('الثقة') or item.get('score') or 0.6
                                reason_raw = item.get('reasoning') or item.get('التفسير') or item.get('التبرير') or item.get('support') or ''
                                hyp = _extract_best_text(hyp_raw)
                                try:
                                    conf = float(conf_raw) if conf_raw is not None else 0.6
                                except Exception:
                                    conf = 0.6
                                reason = _extract_best_text(reason_raw)
                            else:
                                hyp = _extract_best_text(item)
                                conf = 0.6
                                reason = ''
                            results.append({"id": hid, "hypothesis": hyp, "confidence": float(conf), "support": [reason] if reason else []})
                        print(f">> [Quantum Success] Generated {len(results)} creative hypotheses.")
                        return results

            if not blob:
                raise ValueError("Empty response from LLM")
            raise ValueError("No JSON array found in LLM response.")
            
        except Exception as e:
            print(f"[Quantum Warning] Creativity collapse: {e}")
            return [
                {"id": "fallback_1", "hypothesis": f"Standard Analysis: Investigate root causes intuitively.", "confidence": 0.5, "support": ["Fallback mechanism triggered."]}
            ]
    
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

    # [AGL COMPATIBILITY]
    # Add legacy method aliases to satisfy existing calls from MissionControl/HeikalCore
    def process(self, data):
        """Unified entry point for task processing."""
        if isinstance(data, str):
            return self.sample_hypotheses(data)
        elif isinstance(data, dict):
            prompt = data.get('problem') or data.get('input') or str(data)
            return self.sample_hypotheses(prompt, context=data.get('context'))
        else:
            return self.sample_hypotheses(str(data))

    def collapse_wave_function(self, prompt_input):
         """Alias for sample_hypotheses to match old API."""
         return self.sample_hypotheses(prompt_input)


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


class QuantumContextFocuser:
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
    """Factory to create a QuantumNeuralCore instance for bootstrap."""
    nq = 4
    if config and isinstance(config.get("num_qubits"), int):
        nq = int(config.get("num_qubits"))
    return QuantumNeuralCore(num_qubits=nq)
