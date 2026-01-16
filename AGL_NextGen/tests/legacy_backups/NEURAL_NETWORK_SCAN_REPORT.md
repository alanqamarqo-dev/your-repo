# 🧠 AGL Neural Network Scan Report
Date: 2026-01-01
Status: Completed

## 1. Deep Learning Models (PyTorch `nn.Module`)
These are the actual trainable neural networks found in the codebase.

| Model Class | Location | Type |
|:---|:---|:---|
| **SemanticBridge** | `HERMES_OMNI/HERMES_OMNI_GENESIS.py` | Semantic Processing / Bridge |
| **HybridBridge** | `HERMES_OMNI/AGL_HERMES_HYBRID.py` | Hybrid Architecture Bridge |
| **OmniAttentionMechanism** | `GENESIS_OMEGA/GENESIS_OMEGA_CORE.py` | Attention Mechanism |
| **GENESIS_OMEGA_Entity** | `GENESIS_OMEGA/GENESIS_OMEGA_CORE.py` | Core Entity Model |

## 2. Conceptual Intelligence Cores
These are the logic engines that drive the system's "consciousness" and decision making, often wrapping LLMs or complex logic.

| Core Name | Location | Function |
|:---|:---|:---|
| **QuantumNeuralCore** | `repo-copy/Core_Engines/Quantum_Neural_Core.py` | LLM Interface / Decision Making |
| **AGL_Core_Consciousness** | `AGL_Core_Consciousness.py` | Main Consciousness Loop |
| **Heikal_Quantum_Core** | `AGL_Core/Heikal_Quantum_Core.py` | Quantum Simulation Core |
| **HussamAlKami** | `Hussam_Nervous_System/Hussam_Al_Kami.py` | Nervous System Manager (New) |

## 3. Code Generators
These components generate neural network code but are not networks themselves.

- `Advanced_Code_Generator` (`repo-copy/Engineering_Engines/Advanced_Code_Generator.py`)

## 4. Recommendations
- **Consolidation**: The `HERMES` and `GENESIS_OMEGA` models seem to be the most advanced.
- **Integration**: The new `Hussam_Nervous_System` should likely interface with `QuantumNeuralCore` to route signals effectively.
