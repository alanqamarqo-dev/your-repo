from Integration_Layer.integration_registry import registry
import Core_Engines as CE
CE.bootstrap_register_all_engines(registry, allow_optional=True)
q = registry.get("Quantum_Neural_Core")

print('Q core present:', bool(q))

# Test 1: simulate_superposition_measure
task = {
  "op": "simulate_superposition_measure",
  "params": {
    "num_qubits": 1,
    "state": "|0>",
    "gates": [{"type":"H","target":0}],
    "shots": 2000
  }
}
try:
    res = q.process_task(task) # type: ignore
    print('\n-- simulate_superposition_measure ->')
    print(res)
except Exception as e:
    print('simulate_superposition_measure error:', e)

# Test 2: qft and phase_estimation
try:
    print('\n-- qft ->')
    print(q.process_task({"op":"qft","params":{"num_qubits":3}})) # type: ignore
except Exception as e:
    print('qft error:', e)

try:
    print('\n-- phase_estimation ->')
    print(q.process_task({"op":"phase_estimation","params":{"angle":0.314}})) # type: ignore
except Exception as e:
    print('phase_estimation error:', e)
