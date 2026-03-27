"""Quantum Simulator Wrapper

Provides a simple, dependency-light simulator for basic ops (H, CNOT, QFT,
phase estimation-ish probe) that can run purely in numpy. This wrapper is
registered as an engine and exposes a process_task API compatible with the
AGL engine contract.

It respects the environment variable AGL_QCORE_NUM_QUBITS and AGL_QUANTUM_MODE
('simulate' to enable). If the underlying Quantum_Neural_Core provides more
advanced APIs they can be integrated later; for now this file is self-contained
and safe to run in CI.
"""
from typing import Dict, Any, List
import os
import math
import json
import subprocess
import shutil
import urllib.request
import urllib.error
import urllib.parse
import numpy as np


def _hadamard_matrix():
    return np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)


def _pauli_x():
    return np.array([[0, 1], [1, 0]], dtype=complex)


def _kron_n(mats: List[np.ndarray]) -> np.ndarray:
    out = mats[0]
    for m in mats[1:]:
        out = np.kron(out, m)
    return out


def apply_gate(state: np.ndarray, gate: np.ndarray, targets: List[int], num_qubits: int) -> np.ndarray:
    # Build full gate via kron for small num_qubits
    mats = []
    for q in range(num_qubits):
        if q in targets:
            mats.append(gate)
        else:
            mats.append(np.eye(2, dtype=complex))
    full = _kron_n(mats)
    return full.dot(state)


def measure_state(state: np.ndarray, shots: int = 1024) -> Dict[str, float]:
    probs = np.abs(state) ** 2
    # labels
    n = int(np.log2(len(probs)))
    labels = [format(i, '0{}b'.format(n)) for i in range(len(probs))]
    counts = dict.fromkeys(labels, 0)
    samples = np.random.choice(len(probs), size=shots, p=probs)
    for s in samples:
        counts[labels[s]] += 1
    return {k: v / shots for k, v in counts.items()}


class QuantumSimulatorWrapper:
    name = "Quantum_Simulator_Wrapper"

    def __init__(self):
        try:
            self.num_qubits = int(os.getenv('AGL_QCORE_NUM_QUBITS', '4'))
        except Exception:
            self.num_qubits = 4
        self.mode = os.getenv('AGL_QUANTUM_MODE', '')

    def _init_state(self, num_qubits: int, basis_state: str = None) -> np.ndarray: # type: ignore
        dim = 2 ** num_qubits
        state = np.zeros((dim,), dtype=complex)
        if basis_state is None:
            state[0] = 1.0
        else:
            # accept '0'|'1' for single qubit or bitstring
            if isinstance(basis_state, str) and set(basis_state) <= {'0', '1'}:
                idx = int(basis_state, 2)
                state[idx] = 1.0
            else:
                state[0] = 1.0
        return state

    def _call_ollama_for_task(self, op: str, params: Dict[str, Any]) -> str:
        """Call a local Ollama-like HTTP endpoint or fall back to the ollama CLI.

        Returns the text response from the model (best-effort). Raises on fatal errors.
        """
        base = os.getenv('AGL_LLM_BASEURL') or os.getenv('OLLAMA_API_URL')
        model = os.getenv('AGL_LLM_MODEL', '')
        prompt = json.dumps({'op': op, 'params': params}, ensure_ascii=False)

        if base:
            endpoint = base.rstrip('/') + '/api/generate'
            payload = {'model': model, 'prompt': prompt}
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(endpoint, data=data, headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    body = resp.read().decode('utf-8')
                    try:
                        j = json.loads(body)
                    except Exception:
                        return body
                    # common fields
                    for k in ('response', 'text', 'completion', 'output', 'generated_text'):
                        if k in j:
                            return j[k]
                    if 'choices' in j and isinstance(j['choices'], list) and j['choices']:
                        c = j['choices'][0]
                        if isinstance(c, dict):
                            for k in ('text', 'message', 'content'):
                                if k in c:
                                    return c[k]
                        return str(c)
                    return json.dumps(j)
            except urllib.error.URLError as e:
                # fall through to CLI fallback
                http_err = e
        else:
            http_err = None

        # Fallback: try the ollama CLI if available
        if shutil.which('ollama'):
            try:
                args = ['ollama', 'run']
                if model:
                    args.append(model)
                # pass prompt on stdin
                p = subprocess.run(args, input=prompt.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                out = p.stdout.decode('utf-8')
                if out:
                    return out
                err = p.stderr.decode('utf-8')
                if err:
                    raise RuntimeError('ollama cli error: ' + err)
            except Exception as e:
                raise RuntimeError('ollama cli failed: ' + str(e))

        # If both methods failed, raise informative error
        if http_err is not None:
            raise RuntimeError(f'Ollama HTTP call failed: {http_err}')
        raise RuntimeError('No Ollama endpoint configured and ollama CLI not found')

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        op = (task.get('op') or '').lower()
        params = task.get('params') or {}
        num_qubits = int(params.get('num_qubits', self.num_qubits))
        shots = int(params.get('shots', 1024))

        # Only operate in simulate mode (env) unless op explicitly specified
        # If not in simulate mode, try to call a configured Ollama HTTP endpoint
        # or fall back to the `ollama` CLI. This makes engines call a live
        # Ollama model automatically when tests are run with live provider.
        if self.mode != 'simulate':
            try:
                llm_text = self._call_ollama_for_task(op, params)
                return {"ok": True, "engine": self.name, "mode": 'live', "llm_response": llm_text}
            except Exception as e:
                # If live call fails, fall back to echo/capabilities so tests don't crash
                return {"ok": False, "engine": self.name, "mode": self.mode, "error": str(e)}

        # simulate_superposition_measure: apply list of gates then measure
        if op == 'simulate_superposition_measure':
            state = self._init_state(num_qubits, params.get('state')) # type: ignore
            gates = params.get('gates', [])
            for g in gates:
                gtype = (g.get('type') or '').upper()
                tgt = g.get('target')
                if gtype == 'H':
                    H = _hadamard_matrix()
                    state = apply_gate(state, H, [tgt], num_qubits)
                elif gtype == 'X':
                    X = _pauli_x()
                    state = apply_gate(state, X, [tgt], num_qubits)
                # extend with RX/RY/RZ if needed
            probs = measure_state(state, shots=shots)
            return {"ok": True, "engine": self.name, "mode": 'simulate', "probabilities": probs, "shots": shots}

        if op == 'qft':
            # simple check: return a marker that QFT would be applied; implement small n
            n = int(params.get('num_qubits', num_qubits))
            # For demonstration produce deterministic transform on computational basis
            basis = params.get('basis', '0')
            state = self._init_state(n, basis_state=basis)
            # naive QFT via matrix (small n only)
            dim = 2 ** n
            omega = np.exp(2j * np.pi / dim)
            Q = np.array([[omega ** (i * j) for j in range(dim)] for i in range(dim)], dtype=complex) / math.sqrt(dim)
            out = Q.dot(state)
            probs = np.abs(out) ** 2
            labels = [format(i, '0{}b'.format(n)) for i in range(len(probs))]
            return {"ok": True, "engine": self.name, "mode": 'simulate', "qft_probs": dict(zip(labels, probs.tolist()))}

        if op == 'phase_estimation':
            # lightweight simulated phase estimation: return supplied angle
            angle = params.get('angle', None)
            if angle is None:
                angle = 0.0
            return {"ok": True, "engine": self.name, "mode": 'simulate', "phase": float(angle)}

        if op == 'quantum_neural_forward':
            # stub: return logits shaped to two classes using random or deterministic mapping
            inp = params.get('input')
            # deterministic pseudo-random from input
            s = str(inp) if inp is not None else '0'
            seed = sum(ord(c) for c in s) % 1000
            rng = np.random.RandomState(seed)
            logits = rng.rand(2).tolist()
            return {"ok": True, "engine": self.name, "mode": 'simulate', "logits": logits}

        # default: echo capabilities
        return {"ok": True, "engine": self.name, "num_qubits": self.num_qubits, "mode": self.mode}


def factory():
    return QuantumSimulatorWrapper()


    
