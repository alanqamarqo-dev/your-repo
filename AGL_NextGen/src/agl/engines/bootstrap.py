"""
AGL Engine Bootstrap
-------------------
Registers available engines into a central registry.
Adapted for AGL_NextGen structure.
"""

import importlib
import logging
import time
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Map: Engine Name -> (Module Path, Class Name)
ENGINE_SPECS = {
    # --- Migrated Engines (AGL_NextGen) ---
    "Heikal_Quantum_Core":       ("agl.engines.quantum_core",         "HeikalQuantumCore"),
    "Dreaming_Cycle":            ("agl.engines.dreaming",             "DreamingEngine"),
    "Moral_Reasoner":            ("agl.engines.moral",                "MoralReasoner"),
    "Strategic_Thinking":        ("agl.engines.strategic",            "StrategicThinkingEngine"),
    "Self_Learning":             ("agl.engines.learning",             "SelfLearning"),
    "Mission_Control":           ("agl.engines.mission_control",      "SmartFocusController"),
    "Recursive_Improver":        ("agl.engines.recursive_improver",   "RecursiveImprover"),
    "Quantum_Neural_Core":       ("agl.engines.quantum_neural",       "QuantumNeuralCore"),
    "Heikal_Holographic_Memory": ("agl.engines.holographic_memory",   "HeikalHolographicMemory"),
    "Holographic_LLM":           ("agl.engines.holographic_llm",      "HolographicLLM"),
    "Heikal_Metaphysics_Engine": ("agl.engines.metaphysics",          "HeikalMetaphysicsEngine"),
    "Self_Reflective":           ("agl.engines.self_reflective",      "SelfReflectiveEngine"),
    "Reasoning_Planner":         ("agl.engines.reasoning_planner",    "ReasoningPlanner"),
    "Hypothesis_Generator":      ("agl.engines.hypothesis_generator", "HypothesisGeneratorEngine"),
    "Counterfactual_Explorer":   ("agl.engines.counterfactual_explorer", "CounterfactualExplorer"),
    "Meta_Learning":             ("agl.engines.meta_learning",        "MetaLearningEngine"),
    "Creative_Innovation":       ("agl.engines.creative_innovation",  "CreativeInnovation"),
    "Reasoning_Layer":           ("agl.engines.reasoning_layer",      "ReasoningLayer"),
    "Causal_Graph":              ("agl.engines.causal_graph",         "CausalGraphEngine"),
    "Unified_Lib":               ("agl.lib.unified_lib",              "UnifiedLib"),
    "Unified_AGI_System":        ("agl.core.unified_system",          "UnifiedAGISystem"),
    "Dormant_Powers":            ("agl.engines.dormant_powers",       None), # Module only

    # --- Migrated Legacy Engines ---
    "Advanced_Exponential_Algebra": ("agl.engines.advanced_exponential_algebra", "AdvancedExponentialAlgebra"),
    "Advanced_Simulation_Engine": ("agl.engines.advanced_simulation", "AdvancedSimulationEngine"),
    "Consistency_Checker":       ("agl.engines.consistency_checker", "ConsistencyChecker"),
    "Evolution_Engine":          ("agl.engines.evolution", None),
    "Math_Prover_Lite":          ("agl.engines.math_prover_lite", "MathProverLite"),
    "Plan-and-Execute_MicroPlanner": ("agl.engines.micro_planner", "MicroPlanner"),
    "OptimizationEngine":        ("agl.engines.optimization_engine", "OptimizationEngine"),
    "Quantum_Simulator_Wrapper": ("agl.engines.quantum_simulator_wrapper", "QuantumSimulatorWrapper"),
    "Rubric_Enforcer":           ("agl.engines.rubric_enforcer_engine", "RubricEnforcer"),
    "Self_Critique_and_Revise":  ("agl.engines.self_critique_and_revise", "SelfCritiqueAndRevise"),
    "Units_Validator":           ("agl.engines.units_validator", "UnitsValidator"),
    "Web_Search_Engine":         ("agl.engines.web_search", "WebSearchEngine"),
    "Volition_Engine":           ("agl.engines.volition_engine", "VolitionEngine"),
    
    # --- Newly Migrated Engines ---
    "Mathematical_Brain":        ("agl.engines.mathematical_brain", "MathematicalBrain"),
    "AdvancedMetaReasonerEngine": ("agl.engines.advanced_meta_reasoner", "AdvancedMetaReasonerEngine"),
    "AnalogyMappingEngine":      ("agl.engines.analogy_mapping", "AnalogyMappingEngine"),
    "HypothesisGeneratorEngine": ("agl.engines.hypothesis_generator", "HypothesisGeneratorEngine"),
    "Core_Consciousness":        ("agl.engines.consciousness", "create_engine"),

    # --- Scientific Engines ---
    "Automated_Theorem_Prover":  ("agl.engines.scientific_systems.Automated_Theorem_Prover", "AutomatedTheoremProver"),
    "Scientific_Research_Assistant": ("agl.engines.scientific_systems.Scientific_Research_Assistant", "ScientificResearchAssistant"),
    "Hardware_Simulator":        ("agl.engines.scientific_systems.Hardware_Simulator", "HardwareSimulator"),
    "Scientific_Integration_Orchestrator": ("agl.engines.scientific_systems.Scientific_Integration_Orchestrator", "ScientificIntegrationOrchestrator"),

    # --- Engineering Engines ---
    "Advanced_Code_Generator":   ("agl.engines.engineering.Advanced_Code_Generator", "AdvancedCodeGenerator"),
    "IoT_Protocol_Designer":     ("agl.engines.engineering.IoT_Protocol_Designer", "IoTProtocolDesigner"),

    # --- Self Improvement ---
    "Self_Improvement_Engine":   ("agl.engines.self_improvement.Self_Improvement_Engine", "SelfImprovementEngine"),
    "Self_Monitoring_System":    ("agl.engines.self_improvement.Self_Monitoring_System", "SelfMonitoringSystem"),
    "Self_Optimizer":            ("agl.engines.learning_system.Self_Optimizer", "SelfOptimizer"),
    "Knowledge_Graph_System":    ("agl.engines.self_improvement.Self_Improvement.Knowledge_Graph", "KnowledgeGraph"),

    # --- Learning System ---
    "Learning_System":           ("agl.engines.learning_system.Self_Learning", "SelfLearning"),
    "Generalization_Matrix":     ("agl.engines.learning_system.GeneralizationMatrix", "GeneralizationMatrix"),
    "Inference_Engine":          ("agl.engines.learning_system.Inference_Engine", "InferenceEngine"),
    "Experience_Memory":         ("agl.engines.learning_system.ExperienceMemory", "ExperienceMemory"),

    # --- Safety & Autonomous ---
    "Safety_Control_Layer":      ("agl.engines.safety.Safety_Control_Layer", "SafetyControlLayer"),
    "Safe_Autonomous_System":    ("agl.engines.safety.Safe_Autonomous_System", "SafeAutonomousSystem"),

    # --- Integration ---
    "AGI_Expansion":             ("agl.engines.integration.agi_expansion", "expansion_layer"), # Function
    
    # --- Resonance Optimizer ---
    "Resonance_Optimizer":       ("agl.engines.resonance_optimizer", "ResonanceOptimizer"),

    # --- Genesis & Hermes ---
    "Genesis_Omega_Core":        ("agl.engines.genesis_omega", "GENESIS_OMEGA_Entity"),
    "Genesis_Omega_Trainer":     ("agl.engines.genesis_omega.GENESIS_OMEGA_TRAINING_PLAN", "GenesisOmegaTrainer"),
    "Hermes_Omni_Engine":        ("agl.engines.hermes_omni", "HermesOmniEngine"),
    "Hermes_Genesis_Bridge":     ("agl.engines.hermes_omni.AGL_HERMES_GENESIS_BRIDGE", None), # Script only
}

def _is_already_registered_error(e: Exception) -> bool:
    """Check if error is due to duplicate registration."""
    return "already registered" in str(e).lower()

def bootstrap_register_all_engines(
    registry: Any,
    allow_optional: bool = True,
    config: Dict[str, Any] | None = None,
    verbose: bool = False,
    max_seconds: int | None = None,
) -> Dict[str, Any]:
    """
    Attempts to import, initialize, and register all engines defined in ENGINE_SPECS.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    start_time = time.time()
    registered: Dict[str, Any] = {}
    skipped: Dict[str, str] = {}

    print(f"🚀 [BOOTSTRAP] Initializing Engines...")

    for name, (module_path, class_name) in ENGINE_SPECS.items():
        # Timeout check
        if max_seconds is not None and (time.time() - start_time) > max_seconds:
            print(f"⚠️ [BOOTSTRAP] Timeout reached. Skipping remaining engines.")
            break

        try:
            # 1. Import Module
            module = importlib.import_module(module_path)
            
            # 2. Get Class/Factory
            if class_name:
                if not hasattr(module, class_name):
                    skipped[name] = f"Class {class_name} not found in {module_path}"
                    continue
                factory = getattr(module, class_name)
            else:
                # Module itself is the engine (rare)
                factory = module

            # 3. Initialize
            if class_name is None:
                # If no class name is provided, the module itself is the engine
                engine_obj = module
            elif not callable(factory):
                # If the attribute is not callable (e.g. an already instantiated object), use it directly
                engine_obj = factory
            else:
                try:
                    if config and hasattr(factory, '__init__') and 'config' in factory.__init__.__code__.co_varnames:
                        engine_obj = factory(config=config)
                    else:
                        engine_obj = factory()
                except TypeError:
                    # Fallback for engines requiring args we don't have
                    try:
                        engine_obj = factory()
                    except TypeError:
                         raise

            # 4. Register
            # Handle both dict registry and object registry
            if isinstance(registry, dict):
                registry[name] = engine_obj
            elif hasattr(registry, 'register'):
                registry.register(name, engine_obj)
            elif hasattr(registry, 'add'):
                registry.add(name, engine_obj)
            
            registered[name] = engine_obj
            if verbose:
                print(f"   ✅ Registered: {name}")

        except ImportError:
            if not allow_optional:
                raise
            skipped[name] = "ImportError (Module not found)"
        except Exception as e:
            if not allow_optional:
                raise
            skipped[name] = f"Initialization Error: {e}"

    print(f"✅ [BOOTSTRAP] Completed. Registered: {len(registered)}, Skipped: {len(skipped)}")
    return registered
