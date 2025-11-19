# -*- coding: utf-8 -*-
from __future__ import annotations
import math
import pytest
from Integration_Layer.integration_registry import registry
import Core_Engines as CE


CE.bootstrap_register_all_engines(registry, allow_optional=True)
sim = registry.get('Quantum_Simulator_Wrapper')


def approx_equal(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


def test_qft_uniform_on_zero():
    # QFT on |0> should give uniform distribution over 2^n states
    res = sim.process_task({'op': 'qft', 'params': {'num_qubits': 2, 'basis': '00'}}) # type: ignore
    assert res.get('ok', False)
    q = res.get('qft_probs', {})
    assert isinstance(q, dict) and len(q) == 4
    total = sum(q.values())
    assert abs(total - 1.0) < 1e-6
    # expect near-uniform
    for v in q.values():
        assert abs(v - 0.25) < 1e-6


def test_phase_estimation_returns_angle():
    angle = 0.333
    res = sim.process_task({'op': 'phase_estimation', 'params': {'angle': angle}}) # type: ignore
    assert res.get('ok', False)
    assert pytest.approx(res.get('phase', 0.0), rel=1e-6) == angle


def test_quantum_neural_forward_deterministic():
    a = sim.process_task({'op': 'quantum_neural_forward', 'params': {'input': 'hello'}}) # pyright: ignore[reportOptionalMemberAccess]
    b = sim.process_task({'op': 'quantum_neural_forward', 'params': {'input': 'hello'}}) # pyright: ignore[reportOptionalMemberAccess]
    assert a.get('ok', False) and b.get('ok', False)
    assert a.get('logits') == b.get('logits')


def test_simulate_hadamard_uniform_sampling():
    # With H on both qubits, distribution should approximate uniform for enough shots
    res = sim.process_task({'op': 'simulate_superposition_measure', 'params': {'num_qubits': 2, 'gates': [{'type': 'H', 'target': 0}, {'type': 'H', 'target': 1}], 'shots': 4096}}) # type: ignore
    assert res.get('ok', False)
    probs = res.get('probabilities', {})
    assert isinstance(probs, dict) and len(probs) == 4
    total = sum(probs.values())
    assert abs(total - 1.0) < 0.02
    for v in probs.values():
        assert abs(v - 0.25) < 0.06
