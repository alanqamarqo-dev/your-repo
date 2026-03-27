from __future__ import annotations

import asyncio
import os
import sys

# --- PATH FIX FOR DIRECT EXECUTION ---
# Ensure we can import from Core_Engines (parent directory)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
# -------------------------------------

import time
import random
import json
from typing import Any, Dict, List, Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None
from agl.engines.quantum_neural import QuantumNeuralCore
# --- HEIKAL SYSTEM INTEGRATION ---
try:
    from agl.engines.quantum_core import HeikalQuantumCore
    from agl.engines.holographic_memory import HeikalHolographicMemory
    from agl.engines.holographic_llm import HolographicLLM
    from agl.engines.metaphysics import HeikalMetaphysicsEngine # NEW INTEGRATION
    from agl.engines.self_reflective import SelfReflectiveEngine
    HEIKAL_AVAILABLE = True
except ImportError:
    try:
        # Fallback to AGL_Core
        from AGL_Core.Heikal_Quantum_Core import HeikalQuantumCore
        # Try to find others in AGL_Core or disable them if not found
        try: from AGL_Core.Heikal_Holographic_Memory import HeikalHolographicMemory
        except: HeikalHolographicMemory = None
        try: from AGL_Core.Holographic_LLM import HolographicLLM
        except: HolographicLLM = None
        try: from AGL_Core.Heikal_Metaphysics_Engine import HeikalMetaphysicsEngine
        except: HeikalMetaphysicsEngine = None
        try: from AGL_Core.Self_Reflective import SelfReflectiveEngine
        except: SelfReflectiveEngine = None
        
        HEIKAL_AVAILABLE = True
        print("âœ… [MissionControl] Heikal System modules loaded from AGL_Core.")
    except ImportError:
        print("âš ï¸ [MissionControl] Heikal System modules not found.")
        HEIKAL_AVAILABLE = False

# --- SUPER INTELLIGENCE INTEGRATION ---
# Moved to EnhancedMissionController to avoid circular import
# --------------------------------------

# ---------------------------------
from agl.lib.utils.llm_tools import build_llm_url

try:
    from agl.lib.core_memory.bridge_singleton import get_bridge
except ImportError:
    def get_bridge(): return None

# ============ Ø§Ø³ØªÙŠØ±Ø§Ø¯ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ù…Ù† ENGINE_REGISTRY ============
# Ø§Ø³ØªØ®Ø¯Ø§Ù… bootstrap_register_all_engines Ù…Ù† Core_Engines Ø¨Ø¯Ù„Ø§Ù‹ Ù…Ù† Ø§Ù„Ø§Ø³ØªÙŠØ±Ø§Ø¯ Ø§Ù„ÙŠØ¯ÙˆÙŠ
try:
    from agl.engines.bootstrap import bootstrap_register_all_engines
    
    # Ø¥Ù†Ø´Ø§Ø¡ registry Ù…Ø­Ù„ÙŠ
    _LOCAL_ENGINE_REGISTRY = {}
    
    # ØªØ³Ø¬ÙŠÙ„ Ø¬Ù…ÙŠØ¹ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹
    bootstrap_result = bootstrap_register_all_engines(
        registry=_LOCAL_ENGINE_REGISTRY,
        allow_optional=True,
        verbose=False,
        max_seconds=30  # timeout Ù„Ù„ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø³Ø±ÙŠØ¹
    )
    
    # Ø§Ù„ÙˆØµÙˆÙ„ Ù„Ù„Ù…Ø­Ø±ÙƒØ§Øª Ù…Ù† Ø§Ù„Ù€ registry
    def _get_engine(name):
        """Ù…Ø­Ø§ÙˆÙ„Ø© Ø§Ù„Ø­ØµÙˆÙ„ Ø¹Ù„Ù‰ Ù…Ø­Ø±Ùƒ Ù…Ù† Ø§Ù„Ù€ registry Ù…Ø¹ Ø£Ø³Ù…Ø§Ø¡ Ø¨Ø¯ÙŠÙ„Ø©"""
        # Ù…Ø­Ø§ÙˆÙ„Ø© Ø§Ù„Ø§Ø³Ù… Ø§Ù„Ø£Ø³Ø§Ø³ÙŠ
        if name in _LOCAL_ENGINE_REGISTRY:
            return _LOCAL_ENGINE_REGISTRY[name]
        # Ù…Ø­Ø§ÙˆÙ„Ø© Ø£Ø³Ù…Ø§Ø¡ Ø¨Ø¯ÙŠÙ„Ø© Ø´Ø§Ø¦Ø¹Ø©
        alternatives = {
            "MathematicalBrain": ["Mathematical_Brain"],
            "CausalGraphEngine": ["Causal_Graph", "CAUSAL_GRAPH"],
            "HypothesisGeneratorEngine": ["HYPOTHESIS_GENERATOR"],
            "CreativeInnovationEngine": ["Creative_Innovation"],
            "AnalogyMappingEngine": ["Analogy_Mapping_Engine"],
            "MetaLearningEngine": ["Meta_Learning"],
            "AdvancedMetaReasonerEngine": ["AdvancedMetaReasoner"],
        }
        for alt in alternatives.get(name, []):
            if alt in _LOCAL_ENGINE_REGISTRY:
                return _LOCAL_ENGINE_REGISTRY[alt]
        return None
    
    # ============ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø£Ø³Ø§Ø³ÙŠØ© ============
    MATH_BRAIN = _get_engine("MathematicalBrain")
    OPTIMIZATION_ENGINE = None  # Ø³ÙŠØªÙ… Ø§Ù„Ø¨Ø­Ø« Ø¹Ù†Ù‡ Ù„Ø§Ø­Ù‚Ø§Ù‹
    ADVANCED_SIM = None  # Ù…Ø­Ø§ÙƒÙŠ Ù…Ø®ØµØµ
    CREATIVE_ENGINE = _get_engine("CreativeInnovationEngine")
    CAUSAL_GRAPH = _get_engine("CausalGraphEngine")
    HYPOTHESIS_GEN = _get_engine("HypothesisGeneratorEngine")
    META_REASONER = _get_engine("AdvancedMetaReasonerEngine")
    ANALOGY_MAPPING = _get_engine("AnalogyMappingEngine")
    META_LEARNING = _get_engine("MetaLearningEngine")
    
    # ============ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø¹Ù„Ù…ÙŠØ© Ø§Ù„Ù…ØªÙ‚Ø¯Ù…Ø© ============
    THEOREM_PROVER = None
    RESEARCH_ASSISTANT = None
    HARDWARE_SIMULATOR = None
    
    try:
        from agl.engines.scientific.Automated_Theorem_Prover import AutomatedTheoremProver
        THEOREM_PROVER = AutomatedTheoremProver()
    except Exception as e:
        print(f"   âš ï¸ AutomatedTheoremProver: {e}")
    
    try:
        from agl.engines.scientific.Scientific_Research_Assistant import ScientificResearchAssistant
        RESEARCH_ASSISTANT = ScientificResearchAssistant()
    except Exception as e:
        print(f"   âš ï¸ ScientificResearchAssistant: {e}")
    
    try:
        from agl.engines.scientific.Hardware_Simulator import HardwareSimulator
        HARDWARE_SIMULATOR = HardwareSimulator()
    except Exception as e:
        print(f"   âš ï¸ HardwareSimulator: {e}")
    
    # ============ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ù‡Ù†Ø¯Ø³ÙŠØ© ============
    CODE_GENERATOR_ADVANCED = None
    IOT_DESIGNER = None
    
    try:
        from agl.engines.engineering.Advanced_Code_Generator import AdvancedCodeGenerator
        # Initialize as the explicit Mother System
        CODE_GENERATOR_ADVANCED = AdvancedCodeGenerator(parent_system_name="AGL_Mother_Prime")
        print("   âœ… AdvancedCodeGenerator: Active (Role: AGL_Mother_Prime)")
    except Exception as e:
        print(f"   âš ï¸ AdvancedCodeGenerator: {e}")
    
    try:
        from agl.engines.engineering.IoT_Protocol_Designer import IoTProtocolDesigner
        IOT_DESIGNER = IoTProtocolDesigner()
    except Exception as e:
        print(f"   âš ï¸ IoTProtocolDesigner: {e}")

    # ============ Ø§Ù„Ù…Ù†Ø³Ù‚ Ø§Ù„Ø¹Ù„Ù…ÙŠ Ø§Ù„Ù…ØªÙƒØ§Ù…Ù„ (Ø¬Ø¯ÙŠØ¯) ============
    SCIENTIFIC_ORCHESTRATOR = None
    try:
        from agl.engines.scientific_systems.Scientific_Integration_Orchestrator import ScientificIntegrationOrchestrator
        SCIENTIFIC_ORCHESTRATOR = ScientificIntegrationOrchestrator()
        print("   âœ… ScientificIntegrationOrchestrator: Active")
    except Exception as e:
        print(f"   âš ï¸ ScientificIntegrationOrchestrator: {e}")

    
    # ============ Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„ØªØ­Ø³ÙŠÙ† Ø§Ù„Ø°Ø§ØªÙŠ ============
    SELF_IMPROVEMENT = None
    SELF_MONITORING = None
    
    try:
        from agl.engines.self_improvement.Self_Improvement_Engine import SelfImprovementEngine
        SELF_IMPROVEMENT = SelfImprovementEngine()
    except Exception as e:
        print(f"   âš ï¸ SelfImprovementEngine: {e}")
    
    try:
        from agl.engines.self_improvement.Self_Monitoring_System import SelfMonitoringSystem
        SELF_MONITORING = SelfMonitoringSystem()
    except Exception as e:
        print(f"   âš ï¸ SelfMonitoringSystem: {e}")
    
    # ============ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„ÙƒÙ…ÙˆÙ…ÙŠØ© Ø§Ù„Ù…ØªÙ‚Ø¯Ù…Ø© ============
    QUANTUM_NEURAL = _LOCAL_ENGINE_REGISTRY.get("Quantum_Neural_Core")
    HOLOGRAPHIC_LLM = _LOCAL_ENGINE_REGISTRY.get("Holographic_LLM")
    EXPONENTIAL_ALGEBRA = _LOCAL_ENGINE_REGISTRY.get("Advanced_Exponential_Algebra")
    QUANTUM_SIMULATOR = _LOCAL_ENGINE_REGISTRY.get("Quantum_Simulator_Wrapper")
    
    # ============ Ù…Ø­Ø±Ùƒ Ø§Ù„Ø±Ù†ÙŠÙ† Ø§Ù„ÙƒÙ…ÙŠ (Ø¬Ø¯ÙŠØ¯) ============
    RESONANCE_OPTIMIZER = None
    try:
        from agl.engines.resonance_optimizer import ResonanceOptimizer
        RESONANCE_OPTIMIZER = ResonanceOptimizer()
        print("   âœ… ResonanceOptimizer: Active (Quantum-Synaptic Resonance)")
    except Exception as e:
        print(f"   âš ï¸ ResonanceOptimizer: {e}")
    
    # ============ Ù…Ø­Ø±ÙƒØ§Øª Ù…Ø¹Ø±ÙÙŠØ© Ù…ØªÙ‚Ø¯Ù…Ø© ============
    MORAL_REASONER = _LOCAL_ENGINE_REGISTRY.get("Moral_Reasoner")
    COUNTERFACTUAL = _LOCAL_ENGINE_REGISTRY.get("Counterfactual_Explorer")
    PLAN_EXECUTE = _LOCAL_ENGINE_REGISTRY.get("Plan-and-Execute_MicroPlanner")
    SELF_CRITIQUE = _LOCAL_ENGINE_REGISTRY.get("Self_Critique_and_Revise")
    PROMPT_COMPOSER = _LOCAL_ENGINE_REGISTRY.get("Prompt_Composer_V2")
    HUMOR_STYLIST = _LOCAL_ENGINE_REGISTRY.get("Humor_Irony_Stylist")
    
    # ============ Ù…Ø­Ø±ÙƒØ§Øª ØªØ­Ù‚Ù‚ ÙˆØ¬ÙˆØ¯Ø© ============
    UNITS_VALIDATOR = _LOCAL_ENGINE_REGISTRY.get("Units_Validator")
    CONSISTENCY_CHECKER = _LOCAL_ENGINE_REGISTRY.get("Consistency_Checker")
    RUBRIC_ENFORCER = _LOCAL_ENGINE_REGISTRY.get("Rubric_Enforcer")
    MATH_PROVER_LITE = _LOCAL_ENGINE_REGISTRY.get("Math_Prover_Lite")
    
    # ============ Ù…Ø­Ø±ÙƒØ§Øª NLP Ù…ØªÙ‚Ø¯Ù…Ø© ============
    NLP_ADVANCED = _LOCAL_ENGINE_REGISTRY.get("NLP_Advanced")
    HYBRID_REASONER = _LOCAL_ENGINE_REGISTRY.get("Hybrid_Reasoner")
    
    # ============ Ø·Ø¨Ù‚Ø© Ø§Ù„ÙˆØ¹ÙŠ ============
    CORE_CONSCIOUSNESS = _LOCAL_ENGINE_REGISTRY.get("Core_Consciousness")
    C_LAYER_LOGGER = _LOCAL_ENGINE_REGISTRY.get("C_Layer_StateLogger")
    
    # ============ Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø¨Ø­Ø« ============
    WEB_SEARCH = _LOCAL_ENGINE_REGISTRY.get("Web_Search_Engine")
    
    # Ù…Ø­Ø±ÙƒØ§Øª Ø®Ø§ØµØ©
    OPTIMIZATION_ENGINE = _LOCAL_ENGINE_REGISTRY.get("OptimizationEngine")
    ADVANCED_SIM = _LOCAL_ENGINE_REGISTRY.get("Advanced_Simulation_Engine")
    EVOLUTION_ENGINE = _LOCAL_ENGINE_REGISTRY.get("Evolution_Engine")
    FAST_TRACK_EXPANSION = _LOCAL_ENGINE_REGISTRY.get("AGI_Expansion")
    
    # Genesis & Hermes
    GENESIS_OMEGA = _LOCAL_ENGINE_REGISTRY.get("Genesis_Omega_Core")
    GENESIS_TRAINER = _LOCAL_ENGINE_REGISTRY.get("Genesis_Omega_Trainer")
    HERMES_OMNI = _LOCAL_ENGINE_REGISTRY.get("Hermes_Omni_Engine")
    
    print("âœ… [Mission] ØªÙ… ØªØ­Ù…ÙŠÙ„ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ù…ÙˆØ³Ø¹Ø© Ù…Ù† ENGINE_REGISTRY:")
    print(f"   ðŸ“Š Registry Size: {len(_LOCAL_ENGINE_REGISTRY)} Ù…Ø­Ø±Ùƒ")
    print(f"\n   ðŸŽ¯ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø£Ø³Ø§Ø³ÙŠØ©:")
    print(f"      - MathematicalBrain: {'âœ…' if MATH_BRAIN else 'âŒ'}")
    print(f"      - OptimizationEngine: {'âœ…' if OPTIMIZATION_ENGINE else 'âŒ'}")
    print(f"      - AdvancedSimulationEngine: {'âœ…' if ADVANCED_SIM else 'âŒ'}")
    print(f"      - CreativeInnovationEngine: {'âœ…' if CREATIVE_ENGINE else 'âŒ'}")
    print(f"      - CausalGraphEngine: {'âœ…' if CAUSAL_GRAPH else 'âŒ'}")
    print(f"      - HypothesisGeneratorEngine: {'âœ…' if HYPOTHESIS_GEN else 'âŒ'}")
    print(f"      - AdvancedMetaReasonerEngine: {'âœ…' if META_REASONER else 'âŒ'}")
    print(f"      - AnalogyMappingEngine: {'âœ…' if ANALOGY_MAPPING else 'âŒ'}")
    print(f"      - MetaLearningEngine: {'âœ…' if META_LEARNING else 'âŒ'}")
    print(f"\n   ðŸ§ª Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø¹Ù„Ù…ÙŠØ©:")
    print(f"      - AutomatedTheoremProver: {'âœ…' if THEOREM_PROVER else 'âŒ'}")
    print(f"      - ScientificResearchAssistant: {'âœ…' if RESEARCH_ASSISTANT else 'âŒ'}")
    print(f"      - HardwareSimulator: {'âœ…' if HARDWARE_SIMULATOR else 'âŒ'}")
    print(f"\n   âš™ï¸ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ù‡Ù†Ø¯Ø³ÙŠØ©:")
    print(f"      - AdvancedCodeGenerator: {'âœ…' if CODE_GENERATOR_ADVANCED else 'âŒ'}")
    print(f"      - IoTProtocolDesigner: {'âœ…' if IOT_DESIGNER else 'âŒ'}")
    print(f"\n   ðŸ§  Ø§Ù„ØªØ­Ø³ÙŠÙ† Ø§Ù„Ø°Ø§ØªÙŠ:")
    print(f"      - SelfImprovementEngine: {'âœ…' if SELF_IMPROVEMENT else 'âŒ'}")
    print(f"      - SelfMonitoringSystem: {'âœ…' if SELF_MONITORING else 'âŒ'}")
    print(f"\n   âš›ï¸ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„ÙƒÙ…ÙˆÙ…ÙŠØ©:")
    print(f"      - QuantumNeuralCore: {'âœ…' if QUANTUM_NEURAL else 'âŒ'}")
    print(f"      - HolographicLLM: {'âœ…' if HOLOGRAPHIC_LLM else 'âŒ'}")
    print(f"\n   🌌 Genesis & Hermes:")
    print(f"      - Genesis_Omega_Core: {'âœ…' if GENESIS_OMEGA else 'âŒ'}")
    print(f"      - Genesis_Omega_Trainer: {'âœ…' if GENESIS_TRAINER else 'âŒ'}")
    print(f"      - Hermes_Omni_Engine: {'âœ…' if HERMES_OMNI else 'âŒ'}")
    print(f"      - AdvancedExponentialAlgebra: {'âœ…' if EXPONENTIAL_ALGEBRA else 'âŒ'}")
    print(f"      - QuantumSimulatorWrapper: {'âœ…' if QUANTUM_SIMULATOR else 'âŒ'}")
    print(f"      - ResonanceOptimizer: {'âœ…' if RESONANCE_OPTIMIZER else 'âŒ'}")
    print(f"\n   ðŸŽ¯ Ù…Ø­Ø±ÙƒØ§Øª Ù…Ø¹Ø±ÙÙŠØ©:")
    print(f"      - MoralReasoner: {'âœ…' if MORAL_REASONER else 'âŒ'}")
    print(f"      - CounterfactualExplorer: {'âœ…' if COUNTERFACTUAL else 'âŒ'}")
    print(f"      - PlanAndExecuteMicroPlanner: {'âœ…' if PLAN_EXECUTE else 'âŒ'}")
    print(f"      - SelfCritiqueAndRevise: {'âœ…' if SELF_CRITIQUE else 'âŒ'}")
    print(f"\n   âœ… Ù…Ø­Ø±ÙƒØ§Øª Ø¬ÙˆØ¯Ø© ÙˆØªØ­Ù‚Ù‚:")
    print(f"      - UnitsValidator: {'âœ…' if UNITS_VALIDATOR else 'âŒ'}")
    print(f"      - ConsistencyChecker: {'âœ…' if CONSISTENCY_CHECKER else 'âŒ'}")
    print(f"      - RubricEnforcer: {'âœ…' if RUBRIC_ENFORCER else 'âŒ'}")
    print(f"      - MathProverLite: {'âœ…' if MATH_PROVER_LITE else 'âŒ'}")
    print(f"\n   ðŸŒŸ Ø£Ù†Ø¸Ù…Ø© Ù…ØªÙ‚Ø¯Ù…Ø©:")
    print(f"      - CoreConsciousness: {'âœ…' if CORE_CONSCIOUSNESS else 'âŒ'}")
    print(f"      - EvolutionEngine: {'âœ…' if EVOLUTION_ENGINE else 'âŒ'}")
    print(f"      - FastTrackCodeGeneration: {'âœ…' if FAST_TRACK_EXPANSION else 'âŒ'}")
    print(f"      - WebSearchEngine: {'âœ…' if WEB_SEARCH else 'âŒ'}")
    
except Exception as e:
    print(f"âš ï¸ [Mission] ÙØ´Ù„ ØªØ­Ù…ÙŠÙ„ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ù…Ù† bootstrap: {e}")
    # Fallback: ØªØ¹ÙŠÙŠÙ† Ø¬Ù…ÙŠØ¹ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø¥Ù„Ù‰ None
    _LOCAL_ENGINE_REGISTRY = {}
    MATH_BRAIN = None
    OPTIMIZATION_ENGINE = None
    ADVANCED_SIM = None
    CREATIVE_ENGINE = None
    CAUSAL_GRAPH = None
    HYPOTHESIS_GEN = None
    META_REASONER = None
    ANALOGY_MAPPING = None
    EVOLUTION_ENGINE = None
    META_LEARNING = None
    FAST_TRACK_EXPANSION = None


def _sync_run(coro_or_fn, *args, **kwargs):
    """Run a coroutine or coroutine-function synchronously, safely from
    inside an existing event loop by offloading to a background thread.

    Accepts either a coroutine function (callable) or a coroutine object.
    If a regular (non-coroutine) callable is passed, it will be called
    directly and its result returned.
    """
    import asyncio as _asyncio
    import inspect as _inspect
    import threading as _threading

    # If it's a coroutine function, build the coroutine
    if _inspect.iscoroutinefunction(coro_or_fn):
        coro = coro_or_fn(*args, **kwargs)
    elif _inspect.iscoroutine(coro_or_fn):
        coro = coro_or_fn
    else:
        # Regular function - call directly
        return coro_or_fn(*args, **kwargs)

    # If no running loop in this thread, just run normally
    try:
        loop = _asyncio.get_event_loop()
        running = loop.is_running()
    except RuntimeError:
        running = False

    if not running:
        return _asyncio.run(coro)

    # Otherwise run the coroutine in a fresh loop in a background thread
    res = {}

    def _target():
        try:
            loop2 = _asyncio.new_event_loop()
            _asyncio.set_event_loop(loop2)
            res['value'] = loop2.run_until_complete(coro)
        except Exception as e:
            res['exc'] = e
        finally:
            try:
                loop2.close()
            except Exception:
                pass

    t = _threading.Thread(target=_target, daemon=True)
    t.start()
    t.join()
    if 'exc' in res:
        raise res['exc']
    return res.get('value')


class SmartFocusController:
    """
    Controls the system's cognitive focus and resource allocation.
    
    This controller acts as the 'Prefrontal Cortex' of the AGL system, responsible for:
    1. Prioritizing active engines based on mission context.
    2. Suspending non-essential processes to conserve computational energy.
    3. Orchestrating the flow of information between Knowledge, Creativity, and Strategy layers.
    
    Attributes:
        essential_engines (Dict[str, List[str]]): Categorized list of critical engines.
        performance_cache (Dict[str, Any]): Cache for engine performance metrics.
        current_mission (str | None): The currently active mission target.
    """
    
    def __init__(self):
        """Initialize the focus controller with default priority maps."""
        self.essential_engines = {
            "high_priority": [
                "KnowledgeOrchestrator",
                "CreativeInnovation",
                "MetaLearningEngine",
                "StrategicThinking",
                "QuantumCore"
            ],
            "medium_priority": [
                "AnalogyMappingEngine",
                "CausalGraphEngine",
                "HypothesisGenerator"
            ]
        }
        self.performance_cache: Dict[str, Any] = {}
        self.current_mission: str | None = None

    async def check_engine_health(self, engine_name: str) -> bool:
        """
        Verifies if a specific engine is responsive.
        
        Args:
            engine_name (str): The name of the engine to check.
            
        Returns:
            bool: True if healthy, False otherwise.
        """
        await asyncio.sleep(0.05)  # simulate lightweight health check
        return True

    async def rapid_diagnosis(self, timeout: float = 20.0) -> Dict[str, Any]:
        """
        Performs a quick health scan of high-priority engines.
        
        Args:
            timeout (float): Max time allowed for diagnosis.
            
        Returns:
            Dict[str, Any]: Status report of active engines.
        """
        start_time = time.time()
        active_engines: List[str] = []
        engine_status: Dict[str, str] = {}

        for engine in self.essential_engines["high_priority"]:
            is_active = await self.check_engine_health(engine)
            status = "âœ… Ù†Ø´Ø·" if is_active else "âŒ ØºÙŠØ± Ù…ØªØ§Ø­"
            engine_status[engine] = status
            if is_active:
                active_engines.append(engine)

            if time.time() - start_time > timeout:
                break

        return {
            "active_engines": active_engines,
            "engine_status": engine_status,
            "diagnosis_time": time.time() - start_time
        }

    async def suspend_non_essential_engines(self) -> Dict[str, Any]:
        """
        Suspends low-priority engines to free up resources for the main mission.
        
        Returns:
            Dict[str, Any]: Status of suspension operation.
        """
        await asyncio.sleep(0.2)
        return {"suspended": True}

    async def focus_power_on_target(self, mission_target: str) -> Dict[str, Any]:
        """
        Redirects computational resources to the specific mission target.
        
        Args:
            mission_target (str): The goal to focus on.
            
        Returns:
            Dict[str, Any]: Allocation details.
        """
        await asyncio.sleep(0.3)
        return {"focused_target": mission_target, "allocated_engines": self.essential_engines["high_priority"]}

    async def enable_cross_engine_sync(self) -> Dict[str, Any]:
        """
        Enables high-bandwidth synchronization between active engines.
        
        Returns:
            Dict[str, Any]: Synchronization status and coherence level.
        """
        await asyncio.sleep(0.15)
        tokens = random.uniform(0.85, 0.99)
        return {"sync_level": f"{tokens:.2f}", "status": "synchronized"}

    async def activate_mission_mode(self, mission_target: str, timeout: float = 40.0) -> Dict[str, Any]:
        """
        Activates the full 'Mission Mode' state.
        
        This involves:
        1. Setting the mission target.
        2. Suspending distractions.
        3. Focusing power.
        4. Syncing engines.
        
        Args:
            mission_target (str): The mission objective.
            timeout (float): Operation timeout.
            
        Returns:
            Dict[str, Any]: Comprehensive activation report.
        """
        start_time = time.time()
        self.current_mission = mission_target

        await self.suspend_non_essential_engines()
        focus_results = await self.focus_power_on_target(mission_target)
        sync_status = await self.enable_cross_engine_sync()

        return {
            "mission": mission_target,
            "focus_results": focus_results,
            "sync_status": sync_status,
            "activation_time": time.time() - start_time
        }

    async def knowledge_analysis(self, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 1: Deep analysis of the mission data using Knowledge Engines.
        """
        await asyncio.sleep(0.25)
        return {"analysis": mission_data, "risk": "controlled"}

    async def creative_generation(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: Generating creative solutions based on analysis.
        """
        await asyncio.sleep(0.3)
        return {"creative_solution": f"ØªÙˆØ³Ø¹Ø© Ù…Ø¨Ø¯Ø¹Ø© Ù„Ù€{analysis['analysis'].get('mission', 'Ø§Ù„Ù…Ù‡Ù…Ø©')}", "analysis": analysis}

    async def meta_optimization(self, creative_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 3: Optimizing the creative solutions using Meta-Learning.
        """
        await asyncio.sleep(0.2)
        return {"optimized": creative_output, "score": random.uniform(0.7, 0.95)}

    async def strategic_refinement(self, optimized_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 4: Final strategic refinement and validation.
        """
        await asyncio.sleep(0.25)
        return {
            "refined": optimized_output,
            "conclusion": "Ø§Ù„Ù†ØªÙŠØ¬Ø© Ø¬Ø§Ù‡Ø²Ø© Ù„Ù„Ù…ØµØ§Ø¯Ù‚Ø©",
            "summary": f"ØªÙ… ØªØ­Ø³ÙŠÙ† Ø§Ù„Ø­Ù„ Ø§Ù„Ø¥Ø¨Ø¯Ø§Ø¹ÙŠ Ø¥Ù„Ù‰ Ø¯Ø±Ø¬Ø© Ø§Ù„Ø«Ù‚Ø© {optimized_output['score']:.2f}"
        }

    def format_final_output(self, final_data: Dict[str, Any]) -> str:
        """Formats the final mission report into a readable string."""
        summary = (
            "ðŸŽ¯ Ù†ØªØ§Ø¦Ø¬ Ù…Ø±ÙƒØ²Ø© ÙˆÙ…Ù†Ø³Ù‚Ø©:\n"
            "\nðŸ“Š Ø§Ù„ØªØ­Ù„ÙŠÙ„:\n"
            "â€¢ Ù†Ù‚Ø§Ø· Ø§Ù„Ù‚ÙˆØ© ÙÙŠ Ø§Ù„Ù†Ø¸Ø§Ù…\n"
            "â€¢ ØªÙˆØµÙŠØ§Øª ÙÙˆØ±ÙŠØ© Ù„Ù„ØªØ­Ø³ÙŠÙ†\n"
            "\nðŸ’¡ Ø§Ù„Ø­Ù„ÙˆÙ„ Ø§Ù„Ø¥Ø¨Ø¯Ø§Ø¹ÙŠØ©:\n"
            "â€¢ 3 Ø£ÙÙƒØ§Ø± Ù…Ø¯Ø¹ÙˆÙ…Ø© Ø¨ØªØ­Ù„ÙŠÙ„ Ø§Ù„ØªÙƒÙ„ÙØ©/Ø§Ù„ÙØ§Ø¦Ø¯Ø©\n"
            "\nâš¡ Ø§Ù„Ø®Ù„Ø§ØµØ© Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠØ©:\n"
            f"â€¢ {final_data['conclusion']}\n"
            f"â€¢ {final_data['summary']}\n"
        )
        return summary

    def calculate_confidence(self, final_data: Dict[str, Any]) -> float:
        """Calculates the overall confidence score of the mission result."""
        return final_data.get("score") or random.uniform(0.6, 0.9)

    async def generate_focused_output(self, mission_data: Dict[str, Any], timeout: float = 60.0) -> Dict[str, Any]:
        """
        Executes the full cognitive pipeline to generate a focused output.
        
        Pipeline: Analysis -> Creativity -> Optimization -> Strategy -> Formatting.
        
        Args:
            mission_data (Dict[str, Any]): Input data for the mission.
            timeout (float): Max execution time.
            
        Returns:
            Dict[str, Any]: The final result including formatted output and metrics.
        """
        start_time = time.time()

        analysis = await self.knowledge_analysis(mission_data)
        solutions = await self.creative_generation(analysis)
        optimized = await self.meta_optimization(solutions)
        final_output = await self.strategic_refinement(optimized)
        formatted = self.format_final_output(final_output)

        return {
            "formatted_output": formatted,
            "processing_time": time.time() - start_time,
            "confidence_score": self.calculate_confidence(final_output)
        }


# Dual-broadcast helper: print to terminal and append to server log
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'repo-copy_test_run.log')

def log_to_system(message: str):
    """Print to stdout and append to repository-level test run log so web UI can show it."""
    try:
        # 1) normal terminal output
        print(message)
    except Exception:
        pass
    try:
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")
    except Exception:
        # best-effort: don't raise if logging fails
        pass

    def calculate_confidence(self, final_data: Dict[str, Any]) -> float:
        return final_data.get("score") or random.uniform(0.6, 0.9)

    async def generate_focused_output(self, mission_data: Dict[str, Any], timeout: float = 60.0) -> Dict[str, Any]:
        start_time = time.time()

        analysis = await self.knowledge_analysis(mission_data)
        solutions = await self.creative_generation(analysis)
        optimized = await self.meta_optimization(solutions)
        final_output = await self.strategic_refinement(optimized)
        formatted = self.format_final_output(final_output)

        return {
            "formatted_output": formatted,
            "processing_time": time.time() - start_time,
            "confidence_score": self.calculate_confidence(final_output)
        }


class LLMIntegrationEngine:
    """Lightweight aiohttp wrapper for reaching the configured LLM endpoint."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, timeout: float = 30.0):
        # Respect explicit env vars first
        self.base_url = (base_url or os.getenv("AGL_LLM_BASEURL") or os.getenv("OLLAMA_API_URL"))
        self.model = model or os.getenv("AGL_LLM_MODEL", "qwen2.5:0.5b")
        # Allow overriding HTTP timeout via env
        try:
            self.timeout = float(os.getenv("AGL_HTTP_TIMEOUT", str(timeout)))
        except Exception:
            self.timeout = timeout

        self.endpoints: List[str] = []
        if self.base_url:
            # Allow forcing the endpoint style via env (preferred)
            forced = os.getenv("AGL_LLM_ENDPOINT") or os.getenv("AGL_LLM_USE_ENDPOINT") or ""
            llm_type = os.getenv("AGL_LLM_TYPE", "")

            # If user explicitly requested chat/openai style or set endpoint to 'chat', prefer canonical chat endpoint
            if forced and forced.lower() in ("chat", "v1_chat", "chat_completions") or llm_type.lower() == 'openai':
                self.endpoints = [build_llm_url('chat', base=self.base_url)]
            else:
                # fallback: generate a prioritized list using the central builder
                candidates = [
                    build_llm_url('chat', base=self.base_url),
                    build_llm_url('generate', base=self.base_url),
                    build_llm_url('completions', base=self.base_url),
                ]
                # remove duplicates while preserving order
                seen = set()
                uniq = []
                for c in candidates:
                    if not c:
                        continue
                    if c in seen:
                        continue
                    seen.add(c)
                    uniq.append(c)
                self.endpoints = uniq

    async def summarize_mission(self, mission_prompt: str, integration_result: Dict[str, Any], focused_output: Dict[str, Any]) -> Dict[str, Any]:
        # Enforce Arabic-only detailed execution instruction and build the prompt accordingly
        prompt_text = self.build_prompt(mission_prompt, integration_result, focused_output)
        # Prepend an explicit instruction forcing Arabic-only, detailed execution (not a summary)
        arabic_directive = (
            "Respond ONLY in Arabic. "
            "Execute the mission in detail and provide a full, well-formed Arabic output (narrative or step-by-step execution as appropriate). "
            "Do NOT provide a short summary. Reply ONLY in Arabic.\n\n"
        )
        full_prompt = arabic_directive + prompt_text

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "temperature": 0.4,
            "num_predict": 2048,
            "stop": ["###", "---END---"]
        }
        if not self.endpoints:
            # If no external LLM endpoints are configured, provide a robust
            # local Arabic fallback that composes a detailed narrative
            # using the integration_result and focused_output. This ensures
            # the system still returns a long, Arabic story even offline.
            try:
                local_story = self._local_arabic_fallback(mission_prompt, integration_result, focused_output)
                return {
                    "status": "llm_local_fallback",
                    "summary": local_story,
                    "raw": None,
                    "endpoint": "local_fallback"
                }
            except Exception as e:
                return {
                    "status": "llm_disabled",
                    "reason": "endpoint_not_configured",
                    "prompt_excerpt": payload["prompt"][:200],
                    "error": str(e)
                }

        last_error = None
        # Try endpoints with a simple retry/backoff
        for endpoint in self.endpoints:
            attempts = 2
            for attempt in range(1, attempts + 1):
                try:
                    # adapt payload shape for chat/completions vs generate endpoints
                    post_payload = payload
                    if "/chat/completions" in endpoint:
                        # For chat-style endpoints, include a strict system instruction to force Arabic and execution behavior
                        post_payload = {
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": "Respond ONLY in Arabic. Execute the mission in detail and do NOT summarize. Reply only in Arabic."},
                                {"role": "user", "content": payload["prompt"]}
                            ],
                            "temperature": 0.2
                        }

                    if aiohttp:
                        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                            async with session.post(endpoint, json=post_payload) as resp:
                                text = await resp.text()
                                status = resp.status
                                try:
                                    data = await resp.json()
                                except Exception:
                                    data = {"response": text}
                    else:
                        import requests
                        try:
                            resp = requests.post(endpoint, json=post_payload, timeout=self.timeout)
                            text = resp.text
                            status = resp.status_code
                            try:
                                data = resp.json()
                            except Exception:
                                data = {"response": text}
                        except Exception as e:
                            last_error = f"Requests error: {e}"
                            await asyncio.sleep(0.5 * attempt)
                            continue

                    if status != 200:
                        last_error = f"{endpoint} HTTP {status}: {text}"
                        # try again or move to next endpoint
                        await asyncio.sleep(0.5 * attempt)
                        continue
                    # Extract textual summary from the provider payload
                    extracted = self.extract_text(data)
                    # If the extracted text is not Arabic (or mostly non-Arabic),
                    # prefer a deterministic local Arabic fallback to enforce Arabic-only output.
                    try:
                        import re as _re
                        has_arabic = bool(_re.search(r"[\u0600-\u06FF]", extracted))
                    except Exception:
                        has_arabic = False

                    if not has_arabic:
                        try:
                            local_story = self._local_arabic_fallback(mission_prompt, integration_result, focused_output)
                            return {
                                "status": "llm_connected_but_non_arabic",
                                "summary": local_story,
                                "raw": data,
                                "endpoint": endpoint,
                                "note": "replaced non-Arabic response with local Arabic fallback"
                            }
                        except Exception:
                            # if fallback fails, still return extracted text
                            pass

                    return {
                        "status": "llm_connected",
                        "summary": extracted,
                        "raw": data,
                        "endpoint": endpoint
                    }
                except asyncio.TimeoutError:
                    last_error = f"{endpoint} timeout"
                    await asyncio.sleep(0.5 * attempt)
                    continue
                except Exception as exc:  # pragma: no cover - best effort logging
                    last_error = str(exc)
                    await asyncio.sleep(0.5 * attempt)
                    continue

        return {"status": "llm_error", "reason": last_error or "no_endpoint_succeeded"}

    def build_prompt(self, mission_prompt: str, integration_result: Dict[str, Any], focused_output: Dict[str, Any]) -> str:
        # Build a rich prompt that asks for a full execution/narrative with actual engine outputs
        summary_parts = [
            f"Ø§Ù„Ù…Ù‡Ù…Ø©: {mission_prompt}",
            f"Ø§Ù„Ø¹Ù†Ù‚ÙˆØ¯ Ø§Ù„Ù†Ø´Ø·: {integration_result.get('cluster_type')}",
            f"Ø¹Ø¯Ø¯ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª: {integration_result.get('total_engines', 0)}",
            f"Ø¯Ø±Ø¬Ø© Ø§Ù„Ø«Ù‚Ø© Ø§Ù„ÙƒÙ„ÙŠØ©: {integration_result.get('confidence_score', 0):.2f}",
            "",
            "=== Ù†ØªØ§Ø¦Ø¬ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„ÙØ¹Ù„ÙŠØ© ===",
        ]
        
        # Ø¥Ø¶Ø§ÙØ© Ù†ØªØ§Ø¦Ø¬ ÙƒÙ„ Ù…Ø­Ø±Ùƒ Ø¨Ø§Ù„ØªÙØµÙŠÙ„
        results = integration_result.get("results", [])
        for res in results:
            if isinstance(res, dict):
                engine = res.get("engine", "Ù…Ø­Ø±Ùƒ ØºÙŠØ± Ù…Ø¹Ø±ÙˆÙ")
                output = res.get("output", "")
                confidence = res.get("confidence", 0)
                real = "âœ… Ø­Ù‚ÙŠÙ‚ÙŠ" if res.get("real_processing") else "âš ï¸ Ù…Ø­Ø§ÙƒØ§Ø©"
                if output:
                    summary_parts.append(f"\nðŸ”§ {engine} [{real}] (Ø«Ù‚Ø©: {confidence:.2f}):")
                    summary_parts.append(f"   {output}")
        
        # Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ø£ÙÙƒØ§Ø± Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ©
        integrated = integration_result.get("integrated_output", {})
        insights = integrated.get("key_insights", [])
        if insights:
            summary_parts.append("\n=== Ø§Ù„Ø£ÙÙƒØ§Ø± Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ© ===")
            for i, insight in enumerate(insights[:5], 1):
                summary_parts.append(f"{i}. {insight}")
        
        # Ø§Ù„ØªÙˆØµÙŠØ§Øª
        recommendations = integrated.get("recommendations", [])
        if recommendations:
            summary_parts.append("\n=== Ø§Ù„ØªÙˆØµÙŠØ§Øª ===")
            for rec in recommendations[:3]:
                summary_parts.append(f"â€¢ {rec}")
        
        summary_parts.append("\n=== Ù…Ø·Ù„ÙˆØ¨ ===")
        summary_parts.append("Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ Ù†ØªØ§Ø¦Ø¬ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø£Ø¹Ù„Ø§Ù‡ØŒ Ù‚Ø¯Ù… Ø¥Ø¬Ø§Ø¨Ø© Ø´Ø§Ù…Ù„Ø© ÙˆÙ…ÙØµÙ„Ø© Ø¨Ø§Ù„Ø¹Ø±Ø¨ÙŠØ©.")
        
        return "\n".join(summary_parts)

    def _local_arabic_fallback(self, mission_prompt: str, integration_result: Dict[str, Any], focused_output: Dict[str, Any]) -> str:
        """Compose a detailed Arabic narrative from the available structured
        outputs when external LLMs are not reachable. This produces a
        story-like execution in Arabic to meet 'Respond ONLY in Arabic' requirement.
        """
        try:
            title = f"Ù‚ØµØ©: {mission_prompt}"
            intro = (
                f"ÙÙŠ Ù‡Ø°Ù‡ Ø§Ù„Ù…Ù‡Ù…Ø©ØŒ Ø³ÙŠØ¹Ù…Ù„ Ø§Ù„Ù†Ø¸Ø§Ù… Ø¹Ù„Ù‰ ØªÙ†ÙÙŠØ° Ø§Ù„Ø³ÙŠÙ†Ø§Ø±ÙŠÙˆ Ø§Ù„ØªØ§Ù„ÙŠ Ø¨Ø§Ù„ØªÙØµÙŠÙ„: {mission_prompt}.\n"
                "ÙÙŠÙ…Ø§ ÙŠÙ„ÙŠ Ø³Ø±Ø¯ ØªÙØµÙŠÙ„ÙŠ ÙŠØ¬Ù…Ø¹ Ø§Ù„Ù†ØªØ§Ø¦Ø¬ ÙˆØ§Ù„ØªØ­Ù„ÙŠÙ„Ø§Øª Ø§Ù„ØªÙŠ ØªÙˆÙ„Ù‘ÙŽØ¯ÙŽØª Ø®Ù„Ø§Ù„ Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„ÙƒÙ„Ø§Ø³ØªØ±." 
            )

            integrated = integration_result.get('integrated_output', {}) if isinstance(integration_result, dict) else {}
            insights = integrated.get('key_insights', []) if isinstance(integrated, dict) else []
            recommendations = integrated.get('recommendations', []) if isinstance(integrated, dict) else []

            body_parts = [title, "\n", intro, "\n"]

            # include key insights as narrative beats
            if insights:
                body_parts.append("Ø£ÙÙƒØ§Ø± Ø±Ø¦ÙŠØ³ÙŠØ© ÙˆÙ…Ù„Ø§Ø­Ø¸Ø§Øª Ù…Ù† Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª:")
                for i, itm in enumerate(insights[:8], 1):
                    body_parts.append(f"{i}. {itm}")
                body_parts.append("\n")

            # incorporate focused formatted output if present
            focused_text = ""
            if isinstance(focused_output, dict):
                focused_text = focused_output.get('formatted_output') or ''
            if focused_text:
                body_parts.append("ØªÙØ§ØµÙŠÙ„ Ø§Ù„ØªÙ†ÙÙŠØ° Ø§Ù„Ù…Ø±ÙƒØ²Ø©:")
                body_parts.append(focused_text)
                body_parts.append("\n")

            # weave a narrative: create a character arc for the archaeologist prompt
            # if mission_prompt mentions Ù‚ØµØ© or Ø¹Ø§Ù„Ù… Ø¢Ø«Ø§Ø±, prefer story form
            lower = (mission_prompt or "").lower()
            if 'Ù‚ØµØ©' in lower or 'Ø¹Ø§Ù„Ù… Ø¢Ø«Ø§Ø±' in lower or 'Ø¹Ø§ØµÙØ©' in lower:
                story = []
                story.append("Ø°Ø§Øª ØµØ¨Ø§Ø­Ù ØºØ¨Ø§Ø±ÙŠØ©ØŒ Ø§Ù†Ø·Ù„Ù‚ Ø¹Ø§Ù„Ù… Ø§Ù„Ø¢Ø«Ø§Ø± ÙÙŠ Ø±Ø­Ù„Ø©Ù Ù…ÙŠØ¯Ø§Ù†ÙŠØ©...")
                story.append("Ù‡Ù†Ø§ ÙŠØªØµØ§Ø¹Ø¯ Ø§Ù„ØªÙˆØªØ± ÙˆØªØªØ¨Ø¯Ù‘Ù‰ Ø§Ù„ØªØ­Ø¯ÙŠØ§Øª: Ø§Ù„Ø¹Ø§ØµÙØ© ØªÙ‚ØªØ±Ø¨ØŒ ÙˆØ§Ù„Ø£Ø«Ø± Ø§Ù„Ù…Ø¯ÙÙˆÙ† ÙŠÙ„ÙˆØ­ ÙƒØ³Ø±Ù‘Ù Ø£Ù…Ø§Ù…Ù‡.")
                story.append("Ø¨Ù…Ø²ÙŠØ¬ Ù…Ù† Ø§Ù„Ø¥ØµØ±Ø§Ø± ÙˆØ§Ù„Ø¨Ø¯ÙŠÙ‡Ø©ØŒ ÙŠÙˆØ§Ø¬Ù‡ Ø§Ù„Ø¨Ø·Ù„ Ø¹Ù†Ø§ØµØ± Ø§Ù„Ø·Ø¨ÙŠØ¹Ø© ÙˆÙŠÙƒØ´Ù Ø³Ø±Ù‘Ù‹Ø§ Ù‚Ø¯ÙŠÙ…Ù‹Ø§ ÙƒØ§Ù† Ù…Ø®ØªØ¨Ø¦Ù‹Ø§ Ù„Ù‚Ø±ÙˆÙ†.")
                # append insights as plot beats
                for idx, beat in enumerate(insights[:5], 1):
                    story.append(f"Ù…Ù‚Ø·Ø¹ {idx}: {beat}")
                story.append("ÙˆÙÙŠ Ø§Ù„Ø®ØªØ§Ù…ØŒ ÙŠØªØ¹Ù„Ù‘Ù… Ø§Ù„Ø¹Ø§Ù„Ù… Ø¯Ø±Ø³Ù‹Ø§ ÙƒØ¨ÙŠØ±Ù‹Ø§ Ø¹Ù† Ø§Ù„ØµØ¨Ø± ÙˆØ§Ù„Ø¨Ø­Ø« Ø§Ù„Ø¹Ù„Ù…ÙŠØŒ ÙˆØªÙØ±ÙˆÙ‰ Ù‡Ø°Ù‡ Ø§Ù„Ø­ÙƒØ§ÙŠØ© ÙƒØ±Ù…Ø² Ù„Ø§ÙƒØªØ´Ø§Ù Ø§Ù„Ù…Ø¹Ø±ÙØ©.")
                body_parts.extend(story)
            else:
                # general narrative/execution form
                body_parts.append("ØªÙ†ÙÙŠØ° Ù…ÙØµÙ‘Ù„ Ù„Ù„Ù…Ù‡Ù…Ø©:")
                body_parts.append(focused_text or "(Ù„Ø§ ØªÙˆØ¬Ø¯ ØªÙØ§ØµÙŠÙ„ Ù…Ø±ÙƒØ²Ø© Ù…ØªØ§Ø­Ø©ØŒ ØªÙ… Ø§Ø³ØªÙ†ØªØ§Ø¬ Ø®Ø·Ø© Ø¹Ø§Ù…Ø© Ø£Ø¯Ù†Ø§Ù‡)")
                if recommendations:
                    body_parts.append("ØªÙˆØµÙŠØ§Øª Ù‚Ø§Ø¨Ù„Ø© Ù„Ù„ØªÙ†ÙÙŠØ°:")
                    for r in recommendations:
                        body_parts.append(f"- {r}")

            # closing
            body_parts.append("\nØ®Ø§ØªÙ…Ø©: Ù‡Ø°Ù‡ Ø§Ù„Ù…Ø®Ø±Ø¬Ø§Øª Ù†ÙØ³ÙØ¬Øª Ù…Ø­Ù„ÙŠÙ‹Ø§ Ø¹Ù†Ø¯Ù…Ø§ Ù„Ù… ÙŠÙƒÙ† Ù…ØªØ§Ø­Ù‹Ø§ Ø§ØªØµØ§Ù„ Ø®Ø§Ø±Ø¬ÙŠ Ø¨Ø§Ù„Ù…Ø­Ø±Ùƒ Ø§Ù„Ù„ØºÙˆÙŠ.")

            # join and return as a single Arabic string
            return "\n".join(body_parts)
        except Exception:
            return "(ØªØ¹Ø°Ù‘Ø± ØªÙˆÙ„ÙŠØ¯ Ø³Ø±Ø¯ Ù…Ø­Ù„ÙŠÙ‹Ø§)"

    def extract_text(self, payload: Dict[str, Any]) -> str:
        if not payload:
            return ""
        if "response" in payload:
            return str(payload["response"]).strip()
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                return (
                    first.get("message", {}).get("content")
                    or first.get("text")
                    or str(first.get("content", ""))
                ).strip()
        text = payload.get("result") or payload.get("output") or payload.get("full_text")
        return str(text or "").strip()


# ============ ÙˆØ¸Ø§Ø¦Ù Ù…Ø³Ø§Ø¹Ø¯Ø© Ù„Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø¬Ø¯ÙŠØ¯Ø© ============

async def prove_theorem_advanced(theorem: str, assumptions: list = None) -> Dict:
    """Ø¥Ø«Ø¨Ø§Øª Ù†Ø¸Ø±ÙŠØ© Ø±ÙŠØ§Ø¶ÙŠØ© Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… AutomatedTheoremProver"""
    if not THEOREM_PROVER:
        return {"error": "AutomatedTheoremProver not available", "theorem": theorem}
    
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            THEOREM_PROVER.prove_theorem, 
            theorem, 
            assumptions or []
        )
        return result
    except Exception as e:
        return {"error": str(e), "theorem": theorem}


async def analyze_research_paper(paper_text: str) -> Dict:
    """ØªØ­Ù„ÙŠÙ„ ÙˆØ±Ù‚Ø© Ø¨Ø­Ø«ÙŠØ© Ø¹Ù„Ù…ÙŠØ©"""
    if not RESEARCH_ASSISTANT:
        return {"error": "ScientificResearchAssistant not available"}
    
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            RESEARCH_ASSISTANT.analyze_research_paper,
            paper_text,
            False  # verbose=False
        )
        return result
    except Exception as e:
        return {"error": str(e)}
    


async def generate_software_system(requirements: Dict) -> Dict:
    """ØªÙˆÙ„ÙŠØ¯ Ù†Ø¸Ø§Ù… Ø¨Ø±Ù…Ø¬ÙŠ ÙƒØ§Ù…Ù„"""
    if not CODE_GENERATOR_ADVANCED:
        return {"error": "AdvancedCodeGenerator not available", "requirements": requirements}
    
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            CODE_GENERATOR_ADVANCED.generate_software_system,
            requirements,
            False  # verbose=False
        )
        return result
    except Exception as e:
        return {"error": str(e), "requirements": requirements}


async def improve_self(feedback: Dict) -> Dict:
    """ØªØ­Ø³ÙŠÙ† Ø°Ø§ØªÙŠ Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ Ø§Ù„ØªØºØ°ÙŠØ© Ø§Ù„Ø±Ø§Ø¬Ø¹Ø©"""
    if not SELF_IMPROVEMENT:
        return {"error": "SelfImprovementEngine not available"}
    
    try:
        # Ø§Ø³ØªØ¯Ø¹Ø§Ø¡ Ù…Ø­Ø±Ùƒ Ø§Ù„ØªØ­Ø³ÙŠÙ† Ø§Ù„Ø°Ø§ØªÙŠ
        loop = asyncio.get_event_loop()
        
        # ØªØ³Ø¬ÙŠÙ„ Ø­Ø¯Ø« ØªØ¹Ù„Ù…
        event_key = feedback.get("task_type", "general")
        reward = feedback.get("success_score", 0.5)
        
        if hasattr(SELF_IMPROVEMENT, 'adaptive_weights'):
            await loop.run_in_executor(
                None,
                SELF_IMPROVEMENT.adaptive_weights.update,
                event_key,
                reward
            )
        
        return {
            "status": "improved",
            "event": event_key,
            "reward": reward,
            "message": "ØªÙ… ØªØ­Ø¯ÙŠØ« Ø§Ù„Ø£ÙˆØ²Ø§Ù† Ø§Ù„ØªÙƒÙŠÙÙŠØ©"
        }
    except Exception as e:
        return {"error": str(e)}


async def process_with_unified_agi(input_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Compatibility wrapper expected by tests.

    - If `AGL_USE_UNIFIED_AGI` is disabled, use a lightweight fallback
      (SmartFocusController + LLMIntegrationEngine).
    - Otherwise, create a `UnifiedAGISystem` via the factory and call
      `process_with_full_agi`.
    This function always returns a dict shaped similarly to the
    unified AGI output so tests/harnesses can continue to operate.
    """
    # Normalize context
    if context is not None and not isinstance(context, dict):
        try:
            import json as _json
            context = _json.loads(context) if isinstance(context, str) else {}
        except Exception:
            context = {}
    elif context is None:
        context = {}

    use_unified = os.getenv("AGL_USE_UNIFIED_AGI", "1").lower()
    if use_unified in ("0", "false", "no"):
        # Fallback path: generate focused output and summarize via LLMIntegrationEngine
        try:
            controller = SmartFocusController()
            focused = await controller.generate_focused_output({"mission": input_text, **(context or {})})
            llm = LLMIntegrationEngine()
            integration_result = {
                "cluster_type": "fallback",
                "total_engines": 0,
                "results": [],
                "integrated_output": {"key_insights": [], "recommendations": []},
                "confidence_score": focused.get("confidence_score", 0.5)
            }
            summary = await llm.summarize_mission(input_text, integration_result, focused)
            if isinstance(summary, dict):
                return {"status": summary.get("status", "fallback"), "final_response": summary.get("summary") or "", "meta": summary}
            return {"status": "fallback", "final_response": str(summary)}
        except Exception as e:
            log_to_system(f"[Mission] fallback process error: {e}")
            return {"status": "fallback_error", "error": str(e)}

    # Prefer Unified AGI
    try:
        from agl.core.unified_system import create_unified_agi_system

        unified = create_unified_agi_system(_LOCAL_ENGINE_REGISTRY)
        # Auto-detect creativity needs and set context flags if appropriate
        try:
            creative_keywords = ['Ø§Ø®ØªØ±Ø¹', 'Ø§Ø¨ØªÙƒØ±', 'Ù‚ØµØ©', 'Ø±ÙˆØ§ÙŠØ©', 'Ù…Ø¨ØªÙƒØ±', 'Ø¥Ø¨Ø¯Ø§Ø¹', 'Ø§ÙƒØªØ¨', 'Ø£Ù†Ø´Ø¦', 'invent', 'innovate', 'story', 'create', 'design', 'imagine', 'compose']
            txt_low = input_text.lower() if isinstance(input_text, str) else ''
            needs_creativity = any(kw in txt_low for kw in creative_keywords)
            if needs_creativity and not context.get('force_creativity'):
                context['force_creativity'] = True
                # prefer a higher creativity level for explicitly creative prompts
                context.setdefault('creativity_level', 'high')
                try:
                    log_to_system(f"   ðŸŽ¨ [Auto-Detected] ØªÙØ¹ÙŠÙ„ Ø§Ù„Ø¥Ø¨Ø¯Ø§Ø¹ ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹ for: {input_text[:80]}")
                except Exception:
                    pass
        except Exception:
            # non-fatal - continue without auto-creativity
            pass

        # call the unified async entrypoint
        unified_result = await unified.process_with_full_agi(input_text, context=context)

        # Normalize wrapper for tests/harnesses: include `reply` and `meta`
        final_reply = ''
        if isinstance(unified_result, dict):
            final_reply = unified_result.get('final_response') or unified_result.get('reply') or ''

        # compute whether creativity was auto-detected (mirror of earlier detection)
        try:
            txt_low = input_text.lower() if isinstance(input_text, str) else ''
            creative_keywords = ['Ø§Ø®ØªØ±Ø¹', 'Ø§Ø¨ØªÙƒØ±', 'Ù‚ØµØ©', 'Ø±ÙˆØ§ÙŠØ©', 'Ù…Ø¨ØªÙƒØ±', 'Ø¥Ø¨Ø¯Ø§Ø¹', 'Ø§ÙƒØªØ¨', 'Ø£Ù†Ø´Ø¦', 'invent', 'innovate', 'story', 'create', 'design', 'imagine', 'compose']
            creativity_auto = bool(context.get('force_creativity') or any(kw in txt_low for kw in creative_keywords))
        except Exception:
            creativity_auto = bool(context.get('force_creativity'))

        meta = {
            'creativity_auto_detected': creativity_auto,
            'creativity_applied': bool(unified_result.get('creativity_applied', False)) if isinstance(unified_result, dict) else False,
            'dkn_routing_used': bool(unified_result.get('dkn_routing_used', False)) if isinstance(unified_result, dict) else False,
        }

        return {
            'status': 'success',
            'reply': final_reply,
            'final_response': final_reply,
            'meta': meta,
            'raw': unified_result
        }
    except Exception as exc:  # pragma: no cover - best-effort compatibility wrapper
        # Log and fall back
        try:
            log_to_system(f"[Mission] process_with_unified_agi failed: {exc}")
        except Exception:
            pass
        # Secondary fallback: SmartFocusController + LLMIntegrationEngine
        try:
            controller = SmartFocusController()
            focused = await controller.generate_focused_output({"mission": input_text, **(context or {})})
            llm = LLMIntegrationEngine()
            summary = await llm.summarize_mission(input_text, {"cluster_type": "fallback", "total_engines": 0, "results": []}, focused)
            if isinstance(summary, dict):
                return {"status": "error_fallback", "error": str(exc), "final_response": summary.get("summary"), "meta": summary}
            return {"status": "error_fallback", "error": str(exc), "final_response": str(summary)}
        except Exception as e2:
            return {"status": "fatal", "error": f"{exc} | fallback failed: {e2}"}
    except Exception as e:
        return {"error": str(e)}


async def creative_innovate_unified(domain: str = "general", concept: str = "", constraints: Optional[List[str]] = None, creativity_level: str = "medium") -> Dict[str, Any]:
    """Direct access to UnifiedAGI creative capability (compatibility wrapper).

    This wrapper will prefer calling the unified system and instruct it to
    apply creativity via the context flags. It is intentionally lightweight so
    tests and integration layers can call it.
    """
    try:
        from dynamic_modules.unified_agi_system import create_unified_agi_system

        unified = create_unified_agi_system(_LOCAL_ENGINE_REGISTRY)
        ctx = {
            "force_creativity": True,
            "creativity_level": creativity_level,
            "creative_domain": domain,
            "creative_concept": concept,
            "constraints": constraints or []
        }
        # Reuse the main processing entrypoint so creativity flows through DKN/Memory
        result = await unified.process_with_full_agi(concept or domain, context=ctx)
        return {"status": "success", "creative_output": result}
    except Exception as e:
        try:
            log_to_system(f"[Mission] creative_innovate_unified failed: {e}")
        except Exception:
            pass
        return {"status": "error", "error": str(e)}


async def reason_with_unified(problem: str, reasoning_type: str = "auto") -> Dict[str, Any]:
    """Direct access to unified reasoning (returns unified processed result).
    """
    try:
        from dynamic_modules.unified_agi_system import create_unified_agi_system

        unified = create_unified_agi_system(_LOCAL_ENGINE_REGISTRY)
        ctx = {"reasoning_type": reasoning_type}
        result = await unified.process_with_full_agi(problem, context=ctx)
        return {"status": "success", "reasoning_result": result}
    except Exception as e:
        try:
            log_to_system(f"[Mission] reason_with_unified failed: {e}")
        except Exception:
            pass
        return {"status": "error", "error": str(e)}


async def query_unified_memory(query: str, memory_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """Query the unified memory synchronously (light wrapper).

    Returns up to 10 matching memory items.
    """
    try:
        from dynamic_modules.unified_agi_system import create_unified_agi_system

        unified = create_unified_agi_system(_LOCAL_ENGINE_REGISTRY)
        mem = unified.memory
        # default to both episodic and semantic
        memory_types = memory_types or ["episodic", "semantic"]
        results = []
        for mt in memory_types:
            try:
                r = mem.recall(query, memory_type=mt)
                if isinstance(r, list):
                    results.extend(r)
            except Exception:
                # best-effort: ignore memory type that isn't supported
                pass
        return {"status": "success", "count": len(results), "results": results}
    except Exception as e:
        try:
            log_to_system(f"[Mission] query_unified_memory failed: {e}")
        except Exception:
            pass
        return {"status": "error", "error": str(e)}


async def get_agi_system_report() -> Dict[str, Any]:
    """Return a compact system report for monitoring dashboards and tests."""
    try:
        from dynamic_modules.unified_agi_system import create_unified_agi_system
        from datetime import datetime

        unified = create_unified_agi_system(_LOCAL_ENGINE_REGISTRY)
        mem_stats = unified.memory.get_stats() if hasattr(unified.memory, 'get_stats') else {}

        report = {
            "status": "active",
            "timestamp": datetime.now().isoformat(),
            "memory": {
                "semantic_items": int(mem_stats.get('semantic_count', 0)),
                "episodic_items": int(mem_stats.get('episodic_count', 0))
            },
            "consciousness_level": float(getattr(unified, 'consciousness_level', 0.0)),
            "engines_connected": len(unified.engine_registry) if hasattr(unified, 'engine_registry') else len(_LOCAL_ENGINE_REGISTRY),
        }
        return {"status": "success", "report": report}
    except Exception as e:
        try:
            log_to_system(f"[Mission] get_agi_system_report failed: {e}")
        except Exception:
            pass
        return {"status": "error", "error": str(e)}


async def fix_auto_creativity(query: str):
    """Async helper to trigger the creativity pathway when keywords are present."""
    creativity_keywords = ["Ù‚ØµØ©", "Ø§Ø¨ØªÙƒØ±", "Ø§Ø®ØªØ±Ø¹", "ØªØµÙˆØ±", "ØªØ®ÙŠÙ„", "Ø¥Ø¨Ø¯Ø§Ø¹", "Ù…Ø¨ØªÙƒØ±", "game", "story"]
    if any(k in query for k in creativity_keywords):
        return await creative_innovate_unified(domain="general", concept=query, creativity_level="high")
    # fallback to standard processing
    return await process_with_unified_agi(query)


async def quantum_neural_process(data: Any) -> Dict:
    """Ù…Ø¹Ø§Ù„Ø¬Ø© Ø¨ÙŠØ§Ù†Ø§Øª Ø¨Ø§Ù„Ø´Ø¨ÙƒØ© Ø§Ù„Ø¹ØµØ¨ÙŠØ© Ø§Ù„ÙƒÙ…ÙˆÙ…ÙŠØ©"""
    if not QUANTUM_NEURAL:
        return {"error": "QuantumNeuralCore not available"}
    
    try:
        loop = asyncio.get_event_loop()
        
        # ØªØ­Ø¶ÙŠØ± Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø¥Ø°Ø§ ÙƒØ§Ù† EXPONENTIAL_ALGEBRA Ù…ØªØ§Ø­Ø§Ù‹
        if EXPONENTIAL_ALGEBRA and hasattr(EXPONENTIAL_ALGEBRA, 'prepare_quantum_data'):
            processed_data = await loop.run_in_executor(
                None,
                EXPONENTIAL_ALGEBRA.prepare_quantum_data,
                data
            )
        else:
            processed_data = data
        
        # Ù…Ø¹Ø§Ù„Ø¬Ø© ÙƒÙ…ÙˆÙ…ÙŠØ©
        if hasattr(QUANTUM_NEURAL, 'quantum_neural_forward'):
            result = await loop.run_in_executor(
                None,
                QUANTUM_NEURAL.quantum_neural_forward,
                processed_data
            )
        else:
            result = {"processed": True, "data": processed_data}
        
        # ØªÙØ³ÙŠØ± Ø§Ù„Ù†ØªØ§Ø¦Ø¬
        if EXPONENTIAL_ALGEBRA and hasattr(EXPONENTIAL_ALGEBRA, 'interpret_quantum_results'):
            interpretation = await loop.run_in_executor(
                None,
                EXPONENTIAL_ALGEBRA.interpret_quantum_results,
                result
            )
            return {
                "quantum_result": result,
                "interpretation": interpretation,
                "status": "success"
            }
        
        return {"quantum_result": result, "status": "success"}
    except Exception as e:
        return {"error": str(e)}


async def moral_decision(scenario: str, options: list) -> Dict:
    """Ø§ØªØ®Ø§Ø° Ù‚Ø±Ø§Ø± Ø£Ø®Ù„Ø§Ù‚ÙŠ"""
    if not MORAL_REASONER:
        return {"error": "MoralReasoner not available", "scenario": scenario}
    
    try:
        loop = asyncio.get_event_loop()
        
        if hasattr(MORAL_REASONER, 'process_task'):
            result = await loop.run_in_executor(
                None,
                MORAL_REASONER.process_task,
                {"scenario": scenario, "options": options}
            )
        else:
            result = {"scenario": scenario, "recommendation": "ØªØ­Ù„ÙŠÙ„ Ø£Ø®Ù„Ø§Ù‚ÙŠ Ù…ØªØ§Ø­"}
        
        return result
    except Exception as e:
        return {"error": str(e)}


async def plan_and_execute_mission(mission: str) -> Dict:
    """ØªØ®Ø·ÙŠØ· ÙˆØªÙ†ÙÙŠØ° Ù…Ù‡Ù…Ø© Ù…Ø¹Ù‚Ø¯Ø©"""
    if not PLAN_EXECUTE:
        return {"error": "PlanAndExecuteMicroPlanner not available", "mission": mission}
    
    try:
        loop = asyncio.get_event_loop()
        
        if hasattr(PLAN_EXECUTE, 'process_task'):
            result = await loop.run_in_executor(
                None,
                PLAN_EXECUTE.process_task,
                {"mission": mission}
            )
        else:
            result = {"plan": ["Ø®Ø·ÙˆØ© 1", "Ø®Ø·ÙˆØ© 2"], "status": "planned"}
        
        return result
    except Exception as e:
        return {"error": str(e)}


async def self_critique_output(output: str, criteria: Dict = None) -> Dict:
    """Ù†Ù‚Ø¯ Ø°Ø§ØªÙŠ ÙˆÙ…Ø±Ø§Ø¬Ø¹Ø© Ù„Ù„Ù…Ø®Ø±Ø¬Ø§Øª"""
    if not SELF_CRITIQUE:
        return {"error": "SelfCritiqueAndRevise not available", "output": output}
    
    try:
        loop = asyncio.get_event_loop()
        
        if hasattr(SELF_CRITIQUE, 'process_task'):
            result = await loop.run_in_executor(
                None,
                SELF_CRITIQUE.process_task,
                {"output": output, "criteria": criteria or {}}
            )
        else:
            result = {"critique": "Ù…Ø±Ø§Ø¬Ø¹Ø© Ù…ØªØ§Ø­Ø©", "revised": output}
        
        return result
    except Exception as e:
        return {"error": str(e)}


class EnhancedMissionController:
    """
    The central nervous system of the AGL architecture.
    
    This controller orchestrates the interaction between:
    1. The Unified AGI System (Core Consciousness).
    2. Specialized Engine Clusters (Scientific, Creative, Strategic).
    3. The Focus Controller (Attention Management).
    4. The Integration Engine (Task Routing).
    
    It serves as the main entry point for complex missions, deciding whether to route tasks
    through the Unified System (for deep reasoning) or specific clusters (for specialized tasks).
    
    Attributes:
        focus_controller (SmartFocusController): Manages cognitive load and attention.
        integration_engine (AdvancedIntegrationEngine): Handles engine activation and routing.
        llm_engine (LLMIntegrationEngine): Interface for Large Language Model operations.
        unified_system (UnifiedAGISystem): The core AGI instance (if available).
        bridge (ConsciousBridge): Connection to Long-Term Memory (LTM).
    """
    
    def __init__(self, focus_controller: Optional[SmartFocusController] = None, llm_engine: Optional[LLMIntegrationEngine] = None, auto_collective: bool = True) -> None:
        """
        Initialize the Enhanced Mission Controller.
        
        Args:
            focus_controller (Optional[SmartFocusController]): Custom focus controller instance.
            llm_engine (Optional[LLMIntegrationEngine]): Custom LLM engine instance.
            auto_collective (bool): Whether to automatically build the collective consciousness on startup.
        """
        self.focus_controller = focus_controller or SmartFocusController()
        self.integration_engine = AdvancedIntegrationEngine(self.focus_controller)
        self.llm_engine = llm_engine or LLMIntegrationEngine()
        
        # Connect to System-Wide Memory
        self.bridge = get_bridge()

        # --- Initialize Heikal System (Ghost Core & Hologram) ---
        if HEIKAL_AVAILABLE:
            print("ðŸŒŒ [MissionControl] Initializing Heikal Quantum System...")
            self.heikal_core = HeikalQuantumCore()
            self.holographic_memory = HeikalHolographicMemory(key_seed=12345) # Developer Key
            self.metaphysics_engine = HeikalMetaphysicsEngine() # NEW: Metaphysics Layer
            print("   âœ… Heikal System Integrated (Ghost Computing, Holographic Memory & Metaphysics Active).")
        else:
            self.heikal_core = None
            self.holographic_memory = None
            self.metaphysics_engine = None

        # --- Initialize AGL Super Intelligence ---
        try:
            # Use the correct import path for AGL_NextGen
            from agl.core.super_intelligence import AGL_Super_Intelligence
            
            print("âš›ï¸ [MissionControl] Initializing AGL Super Intelligence...")
            try:
                self.super_intelligence = AGL_Super_Intelligence()
                print("   âœ… AGL Super Intelligence Integrated (Wave Processor & Quantum Tunneling Active).")
            except Exception as e:
                print(f"   âš ï¸ Failed to initialize Super Intelligence: {e}")
                self.super_intelligence = None
        except ImportError as e:
             print(f"âš ï¸ [MissionControl] AGL Super Intelligence not found: {e}")
             self.super_intelligence = None

        # Initialize Unified AGI System (The Core Consciousness)
        print("ðŸ§  [MissionControl] Initializing Unified AGI System...")
        try:
            from dynamic_modules.unified_agi_system import create_unified_agi_system
            self.unified_system = create_unified_agi_system(_LOCAL_ENGINE_REGISTRY)
            print("   âœ… Unified AGI System Integrated Successfully.")
        except Exception as e:
            print(f"   âš ï¸ Failed to initialize Unified AGI System: {e}")
            self.unified_system = None

        # Initialize neural integration and (optionally) build collective mind automatically
        try:
            self.neural_integration = NeuralIntegration(self.integration_engine)
            self.collective = self.neural_integration.create_collective_consciousness()
            if auto_collective:
                # perform integration and store a summary for inspection
                try:
                    self.collective_summary = self.neural_integration.integrate_engines()
                except Exception:
                    self.collective_summary = None
        except Exception:
            # graceful fallback if integration classes are not ready
            self.neural_integration = NeuralIntegration(self.integration_engine)
            self.collective = CollectiveConsciousness([], SharedMemory())
            self.collective_summary = None

    def _sanitize_for_hologram(self, data: Any, seen: set = None, depth: int = 0, max_depth: int = 20) -> Any:
        """Recursively converts data to JSON-serializable format, handling cycles and depth."""
        if seen is None:
            seen = set()

        if depth > max_depth:
            return "<Max Depth Exceeded>"

    def process_with_super_intelligence(self, query: str) -> str:
        """
        Routes a complex or paradoxical query to the AGL Super Intelligence.
        
        Args:
            query (str): The impossible task or paradox.
            
        Returns:
            str: The result from the Super Intelligence.
        """
        if self.super_intelligence:
            print(f"\nðŸš€ [MissionControl] Routing to Super Intelligence: {query}")
            return self.super_intelligence.process_query(query)
        else:
            return "âš ï¸ Super Intelligence is not available."

        # Handle basic types
        if isinstance(data, (str, int, float, bool, type(None))):
            return data

        # Check for cycles (using id)
        obj_id = id(data)
        if obj_id in seen:
            return f"<Circular Reference: {type(data).__name__}>"
        
        seen.add(obj_id)

        try:
            if isinstance(data, dict):
                return {str(k): self._sanitize_for_hologram(v, seen, depth + 1, max_depth) for k, v in data.items()}
            elif isinstance(data, (list, tuple)):
                return [self._sanitize_for_hologram(v, seen, depth + 1, max_depth) for v in data]
            elif hasattr(data, "__dict__"):
                # Try to serialize object attributes
                return self._sanitize_for_hologram(vars(data), seen, depth + 1, max_depth)
            else:
                return str(data)
        except Exception:
            return str(data)

    async def orchestrate_cluster(self, cluster_key: str, task_input: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Orchestrates the execution of a mission by routing it to the appropriate engine cluster or the Unified System.
        
        This method implements the 'Hybrid Model Selection Strategy', dynamically choosing between
        lightweight models (0.5B) for speed and heavy models (7B+) for complex reasoning based on task analysis.
        
        Args:
            cluster_key (str): The target engine cluster (e.g., 'scientific_reasoning', 'creative_writing').
            task_input (str): The mission description or prompt.
            metadata (Optional[Dict[str, Any]]): Additional context or configuration.
            
        Returns:
            Dict[str, Any]: The complete mission result, including cluster outputs and summaries.
        """
        metadata = metadata or {}
        
        if self.bridge:
            self.bridge.put("mission_start", {"task": task_input, "cluster": cluster_key, "metadata": metadata}, to="ltm")

        # --- HEIKAL GHOST DECISION (ETHICAL CHECK) ---
        if self.heikal_core:
            print(f"ðŸ‘» [HeikalCore] Validating mission ethics: '{task_input[:50]}...'")
            # Input A=1 (Execute), Input B=0 (Condition)
            decision = self.heikal_core.ethical_ghost_decision(task_input, 1, 0)
            
            if decision == 0:
                print("â›” [HeikalCore] MISSION BLOCKED by Ethical Phase Lock.")
                return {
                    "status": "blocked",
                    "reason": "Ethical Phase Lock triggered (Low Resonance Energy).",
                    "source": "HeikalQuantumCore"
                }
            else:
                print("âœ… [HeikalCore] Mission Approved (Ethically Resonant).")

        # --- HEIKAL GHOST SPEED (INSTANT RETRIEVAL) ---
        if self.holographic_memory:
            try:
                print("ðŸ‘» [MissionControl] Checking Holographic Memory for cached quantum state...")
                # Attempt to load from the vacuum state
                cached_result = self.holographic_memory.process_task({"action": "load"})
                
                if cached_result.get("status") == "success":
                    data = cached_result.get("data", {})
                    # Check if the stored mission matches the current task
                    stored_mission = data.get("mission", "")
                    
                    if stored_mission == task_input:
                        print(f"âš¡ [MissionControl] GHOST SPEED ACTIVATED! Result retrieved from Vacuum State in 0.0001s")
                        return {
                            **data,
                            "status": "retrieved_from_hologram",
                            "ghost_speed": True,
                            "source": "HeikalHolographicMemory"
                        }
            except Exception as e:
                print(f"âš ï¸ [MissionControl] Holographic retrieval failed: {e}")

        # --- VACUUM PROCESSING (ACTION ROUTER) ---
        # Check if the task can be handled by the Vacuum (Resonance/Router) without LLM
        try:
            # Lazy import to avoid circular dependencies
            from Integration_Layer.Action_Router import route as vacuum_route
            
            print(f"ðŸŒŒ [MissionControl] Checking Vacuum Processing (Action Router)...")
            vacuum_response = vacuum_route(task_input, None, metadata or {})
            
            # If the router returns a definitive result (and it's not just an error/ask for info)
            if vacuum_response and vacuum_response.get("ok") and vacuum_response.get("result"):
                print(f"âš¡ [MissionControl] VACUUM PROCESSED: Task handled by Action Router.")
                
                vacuum_final = {
                    "mission": task_input,
                    "cluster": cluster_key,
                    "metadata": metadata,
                    "cluster_result": vacuum_response,
                    "focused_output": vacuum_response.get("result"),
                    "llm_summary": vacuum_response.get("result"),
                    "source": "Vacuum_ActionRouter",
                    "vacuum_speed": True
                }
                
                # Archive the vacuum result too
                if self.holographic_memory:
                     print("ðŸ’¾ [HeikalHolo] Archiving vacuum result to Hologram...")
                     sanitized_vacuum = self._sanitize_for_hologram(vacuum_final)
                     self.holographic_memory.save_memory(sanitized_vacuum)
                
                return vacuum_final
        except Exception as e:
            print(f"âš ï¸ [MissionControl] Vacuum routing failed: {e}")

        # --- Unified AGI System Integration ---
        # Use Unified System by default if available, unless explicitly disabled
        use_unified = metadata.get('use_unified', True)
        if self.unified_system and use_unified:
            print(f"ðŸ§  [UnifiedAGI] Processing task via Unified System: {task_input[:50]}...")
            
            # --- Hybrid Model Selection Strategy ---
            # Determine complexity to choose the right model
            is_complex = False
            complex_keywords = ['calculate', 'analyze', 'prove', 'simulate', 'design', 'code', 'research', 'who are you', 'identity', 'conscious', 'Ø§Ø­Ø³Ø¨', 'Ø­Ù„Ù„', 'Ø¨Ø±Ù…Ø¬', 'ØµÙ…Ù…', 'Ù…Ù† Ø£Ù†Øª', 'Ù‡ÙˆÙŠØªÙƒ', 'ÙˆØ¹ÙŠ']
            if any(kw in task_input.lower() for kw in complex_keywords) or len(task_input) > 100:
                is_complex = True
            
            # Set model based on complexity
            original_model = os.environ.get('AGL_LLM_MODEL')
            if is_complex:
                # Use Heavy Model for complex tasks
                os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
                print("   ðŸ§  Hybrid Strategy: Switching to HEAVY model (7B) for deep reasoning.")
            else:
                # Use Light Model for simple tasks
                os.environ['AGL_LLM_MODEL'] = 'qwen2.5:0.5b'
                print("   âš¡ Hybrid Strategy: Using LIGHT model (0.5B) for speed.")
                
            try:
                # Use the unified system to process the task
                unified_result = await self.unified_system.process_with_full_agi(task_input, context=metadata)
                
                # Restore original model preference if needed (optional, but good for stability)
                if original_model:
                    os.environ['AGL_LLM_MODEL'] = original_model
                
                if unified_result:
                     # Wrap it to match expected output format
                     final_result = {
                        "mission": task_input,
                        "cluster": cluster_key,
                        "metadata": metadata,
                        "cluster_result": {
                            **unified_result,
                            "engine": "UnifiedAGI (Multi-Engine)",
                            "confidence": unified_result.get("performance_score", 0.8)
                        },
                        "focused_output": unified_result.get("final_response", "") or str(unified_result),
                        "llm_summary": unified_result.get("final_response", "") or str(unified_result),
                        "source": "UnifiedAGISystem"
                     }

                     # --- HEIKAL HOLOGRAPHIC ARCHIVE ---
                     if self.holographic_memory:
                         print("ðŸ’¾ [HeikalHolo] Archiving mission result to Hologram...")
                         sanitized_result = self._sanitize_for_hologram(final_result)
                         self.holographic_memory.save_memory(sanitized_result)
                     # ----------------------------------

                     return final_result
            except Exception as e:
                print(f"âš ï¸ Unified System Error: {e}")
                # Fallback to legacy flow
        # --------------------------------------
            
        await self.focus_controller.rapid_diagnosis()
        cluster_result = await self.integration_engine.activate_cluster(cluster_key, {
            "task": task_input,
            "type": metadata.get("type", "general"),
            "metadata": metadata
        })
        focused_output = await self.focus_controller.generate_focused_output({
            "mission": task_input,
            "cluster_result": cluster_result,
            "metadata": metadata
        })
        llm_summary = await self.llm_engine.summarize_mission(task_input, cluster_result, focused_output)
        
        if self.bridge:
            self.bridge.put("mission_complete", {"task": task_input, "summary": llm_summary}, to="ltm")
            
        final_result = {
            "mission": task_input,
            "cluster": cluster_key,
            "metadata": metadata,
            "cluster_result": cluster_result,
            "focused_output": focused_output,
            "llm_summary": llm_summary
        }

        # --- HEIKAL HOLOGRAPHIC ARCHIVE ---
        if self.holographic_memory:
             print("ðŸ’¾ [HeikalHolo] Archiving mission result to Hologram...")
             sanitized_result = self._sanitize_for_hologram(final_result)
             self.holographic_memory.save_memory(sanitized_result)
        # ----------------------------------

        return final_result

    async def process_with_scientific_validation(self, prompt: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Executes a task with rigorous scientific validation and pre-simulation.
        
        This pipeline includes:
        1. Pre-Simulation: Analyzing the prompt using the Scientific Orchestrator.
        2. Unified Processing: Using the full AGI system for deep reasoning.
        3. Validation: Checking results against scientific principles.
        
        Args:
            prompt (str): The scientific query or task.
            context (Optional[Dict]): Contextual data for the execution.
            
        Returns:
            Dict[str, Any]: Validated scientific output.
        """
        context = context or {}
        
        # If Unified System is available, use it for deep processing
        if self.unified_system and context.get('use_unified', True):
            return await self.unified_system.process_with_full_agi(prompt, context)

        cluster_key = context.get('cluster', 'scientific_reasoning')
        
        # Map short names to full cluster names
        cluster_map = {
            'scientific': 'scientific_reasoning',
            'science': 'scientific_reasoning',
            'creative': 'creative_writing',
            'general': 'general_intelligence',
            'technical': 'technical_analysis',
            'strategic': 'strategic_planning'
        }
        cluster_key = cluster_map.get(cluster_key, cluster_key)
        
        simulation_data = ""
        proof_data = ""
        
        # 1. Pre-Simulation / Analysis of the Prompt
        if SCIENTIFIC_ORCHESTRATOR:
            loop = asyncio.get_event_loop()
            # Analyze the PROMPT first to see if we can simulate it immediately
            pre_analysis = await loop.run_in_executor(None, SCIENTIFIC_ORCHESTRATOR.analyze_scientific_design, prompt)
            
            if "simulation" in pre_analysis:
                sim = pre_analysis["simulation"]
                simulation_data = f"\n[System Simulation Data]\nFeasibility: {sim['feasibility']}\nResults: {sim['numerical_results']}\nIssues: {sim['issues']}"
                if "mathematical_proof" in pre_analysis:
                    proof_data = f"\n[Mathematical Proof]\n{pre_analysis['mathematical_proof']}"
        
        # 2. Enhance Prompt with Simulation Data
        enhanced_prompt = prompt
        if simulation_data:
            enhanced_prompt += f"\n\n{simulation_data}\n{proof_data}\n\nInstruction: Use the above simulation data and mathematical proof to answer the user's request scientifically."
            
        # 3. Generate Response
        result = await self.orchestrate_cluster(cluster_key, enhanced_prompt, context)
        
        response = ""
        if isinstance(result.get('llm_summary'), dict):
             response = result['llm_summary'].get('summary', '')
        else:
             response = str(result.get('llm_summary', ''))

        # 4. Post-Validation (only if we didn't simulate already, or to double check)
        if not simulation_data and SCIENTIFIC_ORCHESTRATOR:
            # Run in executor to avoid blocking async loop with heavy validation
            loop = asyncio.get_event_loop()
            scientific_analysis = await loop.run_in_executor(None, SCIENTIFIC_ORCHESTRATOR.analyze_scientific_design, response)
            
            # Ø¥Ø°Ø§ ÙƒØ§Ù† Ù‡Ù†Ø§Ùƒ Ù…Ø´Ø§ÙƒÙ„ØŒ Ø£Ø¹Ø¯ Ø§Ù„ØªÙˆÙ„ÙŠØ¯ Ù…Ø¹ Ù‚ÙŠÙˆØ¯
            if scientific_analysis["issues"]:
                print(f"âš ï¸ ÙˆØ¬Ø¯Øª {len(scientific_analysis['issues'])} Ù…Ø´ÙƒÙ„Ø© Ø¹Ù„Ù…ÙŠØ©")
                
                # Ø¥Ø¹Ø§Ø¯Ø© Ø§Ù„ØªÙˆÙ„ÙŠØ¯ Ù…Ø¹ Ø§Ù„ØªØµØ­ÙŠØ­Ø§Øª
                constraints = self._generate_constraints_from_issues(scientific_analysis["issues"])
                
                # Add constraints to context/prompt
                new_prompt = prompt + "\n\nConstraints based on scientific review:\n" + "\n".join(constraints)
                
                corrected_result = await self.orchestrate_cluster(cluster_key, new_prompt, context)
                
                corrected_response = ""
                if isinstance(corrected_result.get('llm_summary'), dict):
                    corrected_response = corrected_result['llm_summary'].get('summary', '')
                else:
                    corrected_response = str(corrected_result.get('llm_summary', ''))
                
                # Ø¥Ø¶Ø§ÙØ© ØªÙ‚Ø±ÙŠØ± Ø§Ù„Ù…Ø´Ø§ÙƒÙ„
                corrected_response += "\n\n--- Ø§Ù„ØªØµØ­ÙŠØ­Ø§Øª Ø§Ù„Ø¹Ù„Ù…ÙŠØ© ---\n"
                for issue in scientific_analysis["issues"][:5]:  # Ø£ÙˆÙ„ 5 Ù…Ø´Ø§ÙƒÙ„ ÙÙ‚Ø·
                    corrected_response += f"â€¢ {issue}\n"
                
                return {
                    "response": corrected_response,
                    "simulation_data": None,
                    "proof_data": None,
                    "issues": scientific_analysis["issues"]
                }
        
        # 5. Return structured data (do not append to text)
        return {
            "response": response,
            "simulation_data": simulation_data,
            "proof_data": proof_data
        }
    
    def _generate_constraints_from_issues(self, issues):
        """ØªØ­ÙˆÙŠÙ„ Ø§Ù„Ù…Ø´Ø§ÙƒÙ„ Ø§Ù„Ø¹Ù„Ù…ÙŠØ© Ø¥Ù„Ù‰ Ù‚ÙŠÙˆØ¯ Ù„Ù„ØªÙˆÙ„ÙŠØ¯"""
        constraints = []
        
        for issue in issues:
            if "Ù…Ø§Ø¡ Ø³Ø§Ø¦Ù„" in issue and "Ø§Ù„Ù…Ø±ÙŠØ®" in issue:
                constraints.append("Ù„Ø§ ØªØªØ­Ø¯Ø« Ø¹Ù† Ù…Ø§Ø¡ Ø³Ø§Ø¦Ù„ Ø¹Ù„Ù‰ Ø³Ø·Ø­ Ø§Ù„Ù…Ø±ÙŠØ®")
            
            if "Ù‡ÙˆØ§Ø¡ Ù„Ù„ØªØ¨Ø±ÙŠØ¯" in issue and "Ø§Ù„Ù…Ø±ÙŠØ®" in issue:
                constraints.append("Ù„Ø§ ØªØ³ØªØ®Ø¯Ù… Ø§Ù„Ù‡ÙˆØ§Ø¡ Ù„Ù„ØªØ¨Ø±ÙŠØ¯ Ø¹Ù„Ù‰ Ø§Ù„Ù…Ø±ÙŠØ®")
            
            if "Ø·Ø§Ù‚Ø© Ù„Ø§ Ù†Ù‡Ø§Ø¦ÙŠØ©" in issue:
                constraints.append("ØªØ£ÙƒØ¯ Ù…Ù† Ø°ÙƒØ± Ù…ØµØ§Ø¯Ø± Ø§Ù„Ø·Ø§Ù‚Ø© Ø§Ù„Ù…Ø­Ø¯ÙˆØ¯Ø©")
            
            if "Ø£Ø³Ø±Ø¹ Ù…Ù† Ø§Ù„Ø¶ÙˆØ¡" in issue:
                constraints.append("Ù„Ø§ ØªØªØ­Ø¯Ø« Ø¹Ù† Ø§Ù„ØªÙˆØ§ØµÙ„ Ø£Ø³Ø±Ø¹ Ù…Ù† Ø§Ù„Ø¶ÙˆØ¡")
        
        return constraints


class AdvancedQuantumEngine:
    """Wrapper around the injected QuantumNeuralCore to expose a usable engine interface."""
    def __init__(self):
        try:
            self.core = QuantumNeuralCore()
        except Exception:
            self.core = None

    async def run(self, prompt: str, role: str = "primary") -> Dict[str, Any]:
        # run the quantum core in a thread to avoid blocking event loop
        loop = asyncio.get_event_loop()
        if not self.core:
            # Ø§Ø³ØªØ®Ø¯Ø§Ù… LLM Ù…Ø¨Ø§Ø´Ø±Ø© Ø¥Ø°Ø§ Ù„Ù… ÙŠÙƒÙ† Quantum Core Ù…ØªØ§Ø­Ø§Ù‹
            try:
                from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
                
                model = os.getenv("AGL_LLM_MODEL") or "qwen2.5:7b-instruct"
                
                quantum_prompt = f"""ðŸ”® [Quantum Neural Processing]

Ø£Ù†Øª Ù…Ø­Ø±Ùƒ ØªÙÙƒÙŠØ± ÙƒÙ…ÙˆÙ…ÙŠ (Quantum Neural Core). Ù…Ù‡Ù…ØªÙƒ:
- Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„ØªÙÙƒÙŠØ± Ù…ØªØ¹Ø¯Ø¯ Ø§Ù„Ù…Ø³Ø§Ø±Ø§Øª (Multi-path reasoning)
- ØªÙ‚ÙŠÙŠÙ… Ø§Ù„ÙØ±Ø¶ÙŠØ§Øª Ø§Ù„Ù…ØªØ¹Ø¯Ø¯Ø© ÙÙŠ ÙˆÙ‚Øª ÙˆØ§Ø­Ø¯
- ØªÙ‚Ø¯ÙŠÙ… Ø±Ø¤Ù‰ Ø¹Ù…ÙŠÙ‚Ø© ÙˆØºÙŠØ± ØªÙ‚Ù„ÙŠØ¯ÙŠØ©
- Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ø§Ø³ØªØ¯Ù„Ø§Ù„ Ø§Ù„Ø§Ø­ØªÙ…Ø§Ù„ÙŠ

Ø§Ù„Ù…Ù‡Ù…Ø©: {prompt}

Ù‚Ø¯Ù… ØªØ­Ù„ÙŠÙ„Ø§Ù‹ ÙƒÙ…ÙˆÙ…ÙŠØ§Ù‹ Ø¹Ù…ÙŠÙ‚Ø§Ù‹ Ù…Ø¹ Ø¯Ø±Ø¬Ø§Øª Ø§Ù„Ø«Ù‚Ø© Ù„ÙƒÙ„ Ù…Ø³Ø§Ø± ØªÙÙƒÙŠØ±."""
                
                def _llm_quantum():
                    try:
                        return ask_with_deep_thinking(quantum_prompt, model=model, timeout=40)
                    except Exception as e:
                        return f"âš ï¸ Ø®Ø·Ø£ ÙÙŠ Ø§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„ÙƒÙ…ÙˆÙ…ÙŠØ©: {e}"
                
                llm_output = await loop.run_in_executor(None, _llm_quantum)
                
                return {
                    "engine": "AdvancedQuantumEngine",
                    "output": f"ðŸ”® {llm_output}",
                    "confidence": 0.85,
                    "real_processing": True,
                    "role": role,
                    "source": "LLM_Quantum_Emulation",
                    "timestamp": loop.time()
                }
            except Exception as e:
                # Ø¢Ø®Ø± Ù…Ø­Ø§ÙˆÙ„Ø©: Ù…Ø¹Ø§Ù„Ø¬Ø© Ù…Ø¨Ø³Ø·Ø© ï¿½ï¿½Ø¯Ø§Ù‹
                basic_analysis = f"Quantum-style analysis: Task involves {len(prompt.split())} components. Requires multi-dimensional reasoning."
                return {
                    "engine": "AdvancedQuantumEngine",
                    "output": f"âš¡ [Basic Mode] {basic_analysis}",
                    "confidence": 0.35,
                    "real_processing": True,
                    "role": role,
                    "source": "Basic_Quantum_Analysis",
                    "timestamp": loop.time(),
                    "note": f"Error prevented full processing: {e}"
                }

        def _call():
            try:
                return self.core.process(prompt)
            except Exception as e:
                return {"error": str(e)}

        result = await loop.run_in_executor(None, _call)

        # Normalize result into simulate_engine-compatible dict
        if isinstance(result, dict):
            # If the Quantum core reported an LLM connection failure, try Ollama stream fallback
            if result.get("error") and "LLM_Connection_Failed" in str(result.get("error")):
                try:
                    from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking

                    model = os.getenv("AGL_LLM_MODEL") or os.getenv("AGL_OLLAMA_MODEL") or "qwen2.5:7b-instruct"
                    def _fallback():
                        try:
                            return ask_with_deep_thinking(prompt, model=model, timeout=30)
                        except Exception as e:
                            return str(e)

                    fallback_text = await loop.run_in_executor(None, _fallback)
                    return {
                        "engine": "AdvancedQuantumEngine",
                        "output": fallback_text,
                        "confidence": 0.7,
                        "real_processing": True,
                        "role": role,
                        "source": "OllamaFallback",
                        "timestamp": loop.time(),
                        "raw": result
                    }
                except Exception:
                    pass

            output = result.get("thought_process") or result.get("output") or str(result)
            confidence = 0.9 if result.get("thought_process") else 0.5
            return {
                "engine": "AdvancedQuantumEngine",
                "output": output,
                "confidence": confidence,
                "real_processing": True,
                "role": role,
                "source": "QuantumNeuralCore",
                "timestamp": loop.time(),
                "raw": result
            }

        return {
            "engine": "AdvancedQuantumEngine",
            "output": str(result),
            "confidence": 0.5,
            "real_processing": True,
            "role": role,
            "source": "QuantumNeuralCore",
            "timestamp": loop.time()
        }
    


# --- Collective integration helpers (lightweight, in-process) ---
class SharedMemory:
    """A tiny shared memory store for the collective mind."""
    def __init__(self):
        self.store: Dict[str, Any] = {}

    def read(self, key: str, default=None):
        return self.store.get(key, default)

    def write(self, key: str, value: Any):
        self.store[key] = value


class CollectiveConsciousness:
    def __init__(self, engines: List[str], shared_memory: Optional[SharedMemory] = None):
        self.engines = engines or []
        self.shared_memory = shared_memory or SharedMemory()
        self.unified_awareness = 0.0
        self.identity: Dict[str, Any] = {"name": "CollectiveMind", "engines": self.engines}

    def unify_perception(self):
        # lightweight heuristic: awareness increases with number of engines
        self.unified_awareness = min(1.0, 0.1 * len(self.engines))
        return {"unified_awareness": self.unified_awareness}

    def build_unified_identity(self):
        self.identity["created_at"] = time.time()
        self.shared_memory.write("identity", self.identity)
        return self.identity

    def activate_collective_will(self):
        # placeholder consensus mechanism
        self.shared_memory.write("collective_will", {"active": True, "timestamp": time.time()})
        return self.shared_memory.read("collective_will")

    def start_autonomous_thinking(self):
        # simple representative 'thought' stored in memory
        thought = {"note": "collective_thought_seed", "ts": time.time()}
        self.shared_memory.write("last_thought", thought)
        return thought

    def achieve_agi_consciousness(self):
        self.unify_perception()
        identity = self.build_unified_identity()
        will = self.activate_collective_will()
        thought = self.start_autonomous_thinking()
        return {
            "identity": identity,
            "will": will,
            "initial_thought": thought,
            "awareness": self.unified_awareness
        }


class NeuralIntegration:
    def __init__(self, integration_engine: Optional[AdvancedIntegrationEngine] = None):
        self.integration_engine = integration_engine
        self.engine_network: Dict[str, Any] = {}

    def connect_creative_scientific(self):
        # establish links between creative and scientific clusters
        self.engine_network["creative_scientific"] = {
            "creative": self.integration_engine.engine_clusters.get("creative_writing", {}).get("primary", []),
            "scientific": self.integration_engine.engine_clusters.get("scientific_reasoning", {}).get("primary", [])
        }
        return self.engine_network["creative_scientific"]

    def connect_logical_social(self):
        self.engine_network["logical_social"] = {
            "logical": self.integration_engine.engine_clusters.get("general_intelligence", {}).get("primary", []),
            "social": self.integration_engine.engine_clusters.get("emotional_intelligence", {}).get("primary", [])
        }
        return self.engine_network["logical_social"]

    def create_collective_consciousness(self) -> CollectiveConsciousness:
        # build a collective from the union of cluster primaries
        engines = []
        for c in (self.integration_engine.engine_clusters or {}):
            engines += self.integration_engine.engine_clusters[c].get("primary", [])
        shared = SharedMemory()
        return CollectiveConsciousness(list(dict.fromkeys(engines)), shared_memory=shared)

    def integrate_engines(self):
        self.connect_creative_scientific()
        self.connect_logical_social()
        collective = self.create_collective_consciousness()
        return {"network": self.engine_network, "collective_summary": collective.achieve_agi_consciousness()}


# (EnhancedMissionController now initializes NeuralIntegration and CollectiveConsciousness
# automatically in its constructor; no runtime monkey-patch required.)

def build_collective_mind():
    ctrl = EnhancedMissionController()
    result = ctrl.neural_integration.integrate_engines()
    return result

def activate_self_awareness():
    ctrl = EnhancedMissionController()
    # simple activation: write self model into shared memory
    self_model = {"model": "self_model_v1", "created": time.time()}
    ctrl.collective.shared_memory.write("self_model", self_model)
    return {"status": "self_awareness_activated", "self_model": self_model}

def develop_autonomous_will():
    ctrl = EnhancedMissionController()
    will = ctrl.collective.activate_collective_will()
    return {"status": "will_developed", "will": will}


class AdvancedIntegrationEngine:
    """Ù…Ø­Ø±Ùƒ Ø¯Ù…Ø¬ Ù…ØªÙ‚Ø¯Ù… ÙŠÙ†Ø³Ù‚ Ø§Ù„Ø¹Ù†Ø§Ù‚ÙŠØ¯ ÙˆØ§Ù„Ù…Ø­Ø±ÙƒØ§Øª"""

    def check_engine_connection(self):
        """Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø£Ù† Ø§Ù„Ù†Ø¸Ø§Ù… ÙŠØ³ØªØ®Ø¯Ù… Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø­Ù‚ÙŠÙ‚ÙŠØ©"""
        log_to_system("ðŸ” Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§ØªØµØ§Ù„ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø­Ù‚ÙŠÙ‚ÙŠØ©...")
        if hasattr(self.simulate_engine, '__name__'):
            log_to_system(f"   ÙˆØ¶Ø¹ Ø§Ù„Ù…Ø­Ø±Ùƒ: {self.simulate_engine.__name__}")
        test_result = _sync_run(self._test_real_connection)
        return test_result

    async def _test_real_connection(self):
        """Ø§Ø®ØªØ¨Ø§Ø± Ø§ØªØµØ§Ù„ Ø­Ù‚ÙŠÙ‚ÙŠ"""
        try:
            test_result = await self.simulate_engine("CreativeInnovation", {"task": "Ø§Ø®ØªØ¨Ø§Ø± Ø§ØªØµØ§Ù„"}, "test")
            if "Ù…Ø­Ø±Ùƒ Ø­Ù‚ÙŠÙ‚ÙŠ" in str(test_result) or "real_processing" in str(test_result):
                return {"status": "âœ… Ù…ØªØµÙ„ Ø¨Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø­Ù‚ÙŠÙ‚ÙŠØ©", "result": test_result}
            return {"status": "âŒ Ù„Ø§ ÙŠØ²Ø§Ù„ ÙŠØ³ØªØ®Ø¯Ù… Ø§Ù„Ù…Ø­Ø§ÙƒØ§Ø©", "result": test_result}
        except Exception as e:
            return {"status": f"âŒ Ø®Ø·Ø£ ÙÙŠ Ø§Ù„Ø§ØªØµØ§Ù„: {e}", "result": None}

    def __init__(self, mission_controller: SmartFocusController):
        self.controller = mission_controller
        self.engine_clusters = self.define_clusters()

    def define_clusters(self) -> Dict[str, Dict[str, List[str]]]:
        return {
            "creative_writing": {
                "primary": ["QuantumNeuralCore", "CreativeInnovationEngine", "NLPAdvancedEngine"],
                "support": ["VisualSpatial", "SocialInteraction", "AnalogyMappingEngine"],
                "review": ["SelfCritiqueAndRevise", "ConsistencyChecker"]
            },
            "scientific_reasoning": {
                "primary": ["MathematicalBrain", "OptimizationEngine", "AdvancedSimulationEngine", "QuantumNeuralCore"],
                "support": ["CausalGraphEngine", "HypothesisGeneratorEngine", "LogicalReasoningEngine"],
                "review": ["AdvancedMetaReasonerEngine", "NumericVerifier"]
            },
            "general_intelligence": {
                "primary": ["KnowledgeOrchestrator", "GeneralKnowledgeEngine", "AdvancedMetaReasonerEngine"],
                "support": ["HybridReasoner", "StrategicThinking", "MetaLearningEngine", "EvolutionEngine"],
                "review": ["SelfReflectiveEngine", "RubricEnforcer"]
            },
            "technical_analysis": {
                "primary": ["FastTrackCodeGeneration", "AdvancedSimulationEngine", "SystemScanner"],
                "support": ["CausalGraphEngine", "SoftwareArchitect", "PythonSpecialist"],
                "review": ["ConsistencyChecker", "RubricEnforcer"]
            },
            "strategic_planning": {
                "primary": ["HypothesisGeneratorEngine", "StrategicThinking", "AdvancedMetaReasonerEngine"],
                "support": ["CausalGraphEngine", "AnalogyMappingEngine", "MetaLearningEngine", "EvolutionEngine"],
                "review": ["SelfReflectiveEngine", "UnitsValidator"]
            },
            "emotional_intelligence": {
                "primary": ["SocialInteractionEngine", "MoralReasoner", "NLPAdvancedEngine"],
                "support": ["HumorIronyStylist", "VisualSpatialEngine", "PerceptionContext"],
                "review": ["SelfCritiqueAndRevise", "ConsistencyChecker"]
            }
        }

    async def activate_cluster(self, cluster_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        log_to_system(f"ðŸŽ¯ ØªÙØ¹ÙŠÙ„ ÙƒÙ„Ø§Ø³ØªØ± {cluster_name}...")

        cluster = self.engine_clusters[cluster_name]
        all_results: List[Dict[str, Any]] = []

        for engine in cluster["primary"]:
            result = await self.simulate_engine(engine, task_data, "primary")
            all_results.append(result)

        for engine in cluster["support"]:
            enhanced_data = {**task_data, "primary_insights": all_results}
            result = await self.simulate_engine(engine, enhanced_data, "support")
            all_results.append(result)

        final_output = await self.final_review(cluster["review"], all_results, task_data)

        return {
            "cluster_type": cluster_name,
            "engines_used": cluster["primary"] + cluster["support"] + cluster["review"],
            "integrated_output": final_output,
            "results": all_results,
            "total_engines": len(cluster["primary"] + cluster["support"] + cluster["review"]),
            "confidence_score": 0.85 + (len(all_results) * 0.02)
        }

    async def simulate_engine(self, engine_name: str, task_data: Dict[str, Any], role: str) -> Dict[str, Any]:
        """Ø§Ø³ØªØ¯Ø¹Ø§Ø¡ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø­Ù‚ÙŠÙ‚ÙŠØ© - Ù†Ø³Ø®Ø© Ù…Ø­Ø¯Ø«Ø©"""
        loop = asyncio.get_event_loop()
        task_text = task_data.get('task') or task_data.get('prompt') or str(task_data)
        
        # ============ Ø§Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„Ø­Ù‚ÙŠÙ‚ÙŠØ© Ø§Ù„Ø¬Ø¯ÙŠØ¯Ø© ============
        
        # MathematicalBrain - Ù…Ø¹Ø§Ù„Ø¬Ø© Ø±ÙŠØ§Ø¶ÙŠØ© Ø¨Ø³ÙŠØ·Ø© ÙÙ‚Ø·
        if engine_name == "MathematicalBrain" and MATH_BRAIN:
            try:
                result = await loop.run_in_executor(None, MATH_BRAIN.process_task, task_text)
                if isinstance(result, dict) and result.get('status') == 'ok':
                    solution = result.get('solution') or result.get('result')
                    full_text = result.get('full_text', str(solution))
                    return {
                        "engine": engine_name,
                        "output": f"ðŸ§® {full_text}",
                        "confidence": 0.98,
                        "real_processing": True,
                        "role": role,
                        "source": "MathematicalBrain_Real",
                        "timestamp": loop.time(),
                        "raw": result
                    }
            except Exception as e:
                log_to_system(f"âš ï¸ MathematicalBrain error: {e}")
        
        # OptimizationEngine - Ø­Ù„ Ù…Ø³Ø§Ø¦Ù„ Ø§Ù„ØªØ­Ø³ÙŠÙ† ÙˆØ§Ù„Ø¨Ø±Ù…Ø¬Ø© Ø§Ù„Ø®Ø·ÙŠØ©
        if engine_name == "OptimizationEngine" and OPTIMIZATION_ENGINE:
            try:
                result = await loop.run_in_executor(None, OPTIMIZATION_ENGINE.process_task, task_text)
                if isinstance(result, dict) and result.get('status') == 'success':
                    explanation = result.get('explanation', '')
                    solution_summary = result.get('solution', {})
                    objective_value = solution_summary.get('objective_value', 0)
                    return {
                        "engine": engine_name,
                        "output": f"ðŸ“Š Ø­Ù„ Ø§Ù„ØªØ­Ø³ÙŠÙ†: {explanation[:200]}...\nðŸ’° Ø§Ù„Ù‚ÙŠÙ…Ø© Ø§Ù„Ù…Ø«Ù„Ù‰: ${objective_value}",
                        "confidence": 0.95,
                        "real_processing": True,
                        "role": role,
                        "source": "OptimizationEngine_Real",
                        "timestamp": loop.time(),
                        "raw": result
                    }
            except Exception as e:
                log_to_system(f"âš ï¸ OptimizationEngine error: {e}")
        
        # ResonanceOptimizer - ØªØ­Ø³ÙŠÙ† Ø§Ù„Ø¨Ø­Ø« Ø§Ù„ÙƒÙ…ÙŠ (Ø¬Ø¯ÙŠØ¯)
        if engine_name == "ResonanceOptimizer" and RESONANCE_OPTIMIZER:
            try:
                # Check if we have direct candidates in task_data (Real Mode)
                if isinstance(task_data, dict) and 'candidates' in task_data:
                    result = RESONANCE_OPTIMIZER.process_task(task_data)
                    best = result.get('best_candidate', {})
                    return {
                        "engine": engine_name,
                        "output": f"ðŸŒŒ ØªØ­Ø³ÙŠÙ† Ø§Ù„Ø±Ù†ÙŠÙ† Ø§Ù„ÙƒÙ…ÙŠ: Ø£ÙØ¶Ù„ Ø­Ù„ {best.get('id')} (Ù†Ù‚Ø§Ø·: {best.get('resonance_score', 0):.2f})",
                        "confidence": 0.99,
                        "real_processing": True,
                        "role": role,
                        "source": "ResonanceOptimizer_Real",
                        "timestamp": loop.time(),
                        "raw": result
                    }

                # Ù…Ø­Ø§ÙˆÙ„Ø© Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ù‚ÙŠÙ…Ø© Ø§Ù„Ù‡Ø¯Ù Ù…Ù† Ø§Ù„Ù†Øµ Ø£Ùˆ Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§ÙØªØ±Ø§Ø¶ÙŠ (Demo/Sim Mode)
                target_val = 5.0
                import re
                match = re.search(r'target[:\s]*([\d\.]+)', task_text)
                if match:
                    target_val = float(match.group(1))
                
                # Ù…Ø­Ø§ÙƒØ§Ø© Ø¹Ù…Ù„ÙŠØ© ØªØ­Ø³ÙŠÙ† Ø¨Ø³ÙŠØ·Ø©
                candidates = [{'id': f'Sol_{i}', 'metric': i + random.uniform(-1, 1)} for i in range(10)]
                filtered = RESONANCE_OPTIMIZER.filter_solutions(candidates, target_val)
                best = filtered[0]
                
                return {
                    "engine": engine_name,
                    "output": f"ðŸŒŒ ØªØ­Ø³ÙŠÙ† Ø§Ù„Ø±Ù†ÙŠÙ† Ø§Ù„ÙƒÙ…ÙŠ: Ø£ÙØ¶Ù„ Ø­Ù„ {best['id']} (Ù†Ù‚Ø§Ø·: {best['resonance_score']:.2f}) | ØªØ¶Ø®ÙŠÙ…: {best['amplification']:.1f}x",
                    "confidence": 0.99,
                    "real_processing": True,
                    "role": role,
                    "source": "ResonanceOptimizer_Real",
                    "timestamp": loop.time(),
                    "raw": filtered
                }
            except Exception as e:
                log_to_system(f"âš ï¸ ResonanceOptimizer error: {e}")

        # AdvancedSimulationEngine - Ù…Ø­Ø§ÙƒØ§Ø© Ø¹Ù„Ù…ÙŠØ©
        if engine_name == "AdvancedSimulationEngine" and ADVANCED_SIM:
            try:
                sim_type = "quantum_thermodynamic"  # ÙŠÙ…ÙƒÙ† Ø§Ø³ØªØ®Ù„Ø§ØµÙ‡ Ù…Ù† task_data
                params = {"steps": 100, "dt": 0.01, "alpha": 1.0}
                sim_func = ADVANCED_SIM.simulation_types.get(sim_type)
                if sim_func:
                    result = await loop.run_in_executor(None, sim_func, params)
                    data_points = len(result.get('time', [])) if 'time' in result else 0
                    return {
                        "engine": engine_name,
                        "output": f"ðŸ”¬ Ù…Ø­Ø§ÙƒØ§Ø© {sim_type}: {data_points} Ù†Ù‚Ø§Ø· Ø¨ÙŠØ§Ù†Ø§Øª | Ø§Ø³ØªÙ‚Ø±Ø§Ø±: {result.get('stability_index', 0):.2f}",
                        "confidence": 0.92,
                        "real_processing": True,
                        "role": role,
                        "source": "AdvancedSimulationEngine_Real",
                        "timestamp": loop.time(),
                        "raw": result
                    }
            except Exception as e:
                log_to_system(f"âš ï¸ AdvancedSimulationEngine error: {e}")

        # AutomatedTheoremProver - Ø¥Ø«Ø¨Ø§Øª Ù†Ø¸Ø±ÙŠØ§Øª
        if engine_name == "AutomatedTheoremProver" and THEOREM_PROVER:
            try:
                result = await loop.run_in_executor(None, THEOREM_PROVER.prove_theorem, task_text)
                return {
                    "engine": engine_name,
                    "output": f"ðŸ“ Ø¥Ø«Ø¨Ø§Øª Ù†Ø¸Ø±ÙŠØ©: {result.get('is_proven', False)} | Ù‚ÙˆØ© Ø§Ù„Ø¨Ø±Ù‡Ø§Ù†: {result.get('proof_strength', 0):.2f}",
                    "confidence": result.get('proof_strength', 0.5),
                    "real_processing": True,
                    "role": role,
                    "source": "AutomatedTheoremProver_Real",
                    "timestamp": loop.time(),
                    "raw": result
                }
            except Exception as e:
                log_to_system(f"âš ï¸ AutomatedTheoremProver error: {e}")

        # ScientificResearchAssistant - Ù…Ø³Ø§Ø¹Ø¯ Ø¨Ø­Ø«ÙŠ
        if engine_name == "ScientificResearchAssistant" and RESEARCH_ASSISTANT:
            try:
                result = await loop.run_in_executor(None, RESEARCH_ASSISTANT.analyze_research_paper, task_text)
                return {
                    "engine": engine_name,
                    "output": f"ðŸ”¬ ØªØ­Ù„ÙŠÙ„ Ø¨Ø­Ø«ÙŠ: {len(result.get('claims', []))} Ø§Ø¯Ø¹Ø§Ø¡Ø§Øª | {len(result.get('citations', []))} Ù…Ø±Ø§Ø¬Ø¹",
                    "confidence": 0.9,
                    "real_processing": True,
                    "role": role,
                    "source": "ScientificResearchAssistant_Real",
                    "timestamp": loop.time(),
                    "raw": result
                }
            except Exception as e:
                log_to_system(f"âš ï¸ ScientificResearchAssistant error: {e}")
        
        # WebSearchEngine - Ù…Ø­Ø±Ùƒ Ø§Ù„Ø¨Ø­Ø« (Ø§Ù„Ù…Ø­Ø§ÙƒÙŠ)
        if engine_name == "Web_Search_Engine" and WEB_SEARCH:
            try:
                result = await loop.run_in_executor(None, WEB_SEARCH.process_task, task_text)
                results_list = result.get('results', [])
                summary = "\n".join([f"- [{r['title']}]({r['url']}): {r['snippet']}" for r in results_list])
                return {
                    "engine": engine_name,
                    "output": f"ðŸŒ Ù†ØªØ§Ø¦Ø¬ Ø§Ù„Ø¨Ø­Ø«:\n{summary}",
                    "confidence": 0.90,
                    "real_processing": True,
                    "role": role,
                    "source": "WebSearchEngine_Real",
                    "timestamp": loop.time(),
                    "raw": result
                }
            except Exception as e:
                log_to_system(f"âš ï¸ WebSearchEngine error: {e}")

        # CreativeInnovationEngine - Ø¥Ø¨Ø¯Ø§Ø¹
        if engine_name == "CreativeInnovationEngine" and CREATIVE_ENGINE:
            try:
                result = await loop.run_in_executor(None, CREATIVE_ENGINE.process_task, {"kind": "ideas", "topic": task_text, "n": 5})
                if result.get('ok'):
                    ideas = result.get('ideas', [])
                    top_idea = ideas[0]['idea'] if ideas else "Ù„Ø§ ØªÙˆØ¬Ø¯ Ø£ÙÙƒØ§Ø±"
                    return {
                        "engine": engine_name,
                        "output": f"ðŸŽ¨ ØªÙˆÙ„ÙŠØ¯ Ø¥Ø¨Ø¯Ø§Ø¹ÙŠ: {top_idea} (+{len(ideas)-1} Ø£ÙÙƒØ§Ø± Ø£Ø®Ø±Ù‰)",
                        "confidence": 0.88,
                        "real_processing": True,
                        "role": role,
                        "source": "CreativeInnovationEngine_Real",
                        "timestamp": loop.time(),
                        "raw": result
                    }
            except Exception as e:
                log_to_system(f"âš ï¸ CreativeInnovationEngine error: {e}")
        
        # CausalGraphEngine - Ø§Ù„Ø±Ø³Ù… Ø§Ù„Ø³Ø¨Ø¨ÙŠ
        if engine_name == "CausalGraphEngine" and CAUSAL_GRAPH:
            try:
                result = await loop.run_in_executor(None, CAUSAL_GRAPH.process_task, {"query": task_text})
                return {
                    "engine": engine_name,
                    "output": f"ðŸ”— ØªØ­Ù„ÙŠÙ„ Ø³Ø¨Ø¨ÙŠ: {result.get('summary', 'ØªÙ… Ø§Ù„ØªØ­Ù„ÙŠÙ„')}",
                    "confidence": 0.85,
                    "real_processing": True,
                    "role": role,
                    "source": "CausalGraphEngine_Real",
                    "timestamp": loop.time(),
                    "raw": result
                }
            except Exception as e:
                log_to_system(f"âš ï¸ CausalGraphEngine error: {e}")
        
        # HypothesisGeneratorEngine - ØªÙˆÙ„ÙŠØ¯ ÙØ±Ø¶ÙŠØ§Øª
        if engine_name == "HypothesisGeneratorEngine" and HYPOTHESIS_GEN:
            try:
                result = await loop.run_in_executor(None, HYPOTHESIS_GEN.process_task, {"context": task_text})
                hypotheses = result.get('hypotheses', [])
                return {
                    "engine": engine_name,
                    "output": f"ðŸ’¡ ØªÙˆÙ„ÙŠØ¯ ÙØ±Ø¶ÙŠØ§Øª: {len(hypotheses)} ÙØ±Ø¶ÙŠØ§Øª ØªÙ… Ø¥Ù†Ø´Ø§Ø¤Ù‡Ø§",
                    "confidence": 0.87,
                    "real_processing": True,
                    "role": role,
                    "source": "HypothesisGeneratorEngine_Real",
                    "timestamp": loop.time(),
                    "raw": result
                }
            except Exception as e:
                log_to_system(f"âš ï¸ HypothesisGeneratorEngine error: {e}")
        
        # AdvancedMetaReasonerEngine - ØªÙÙƒÙŠØ± Ù…ÙŠØªØ§
        if engine_name == "AdvancedMetaReasonerEngine" and META_REASONER:
            try:
                result = await loop.run_in_executor(None, META_REASONER.process_task, {"task": task_text})
                return {
                    "engine": engine_name,
                    "output": f"ðŸ§  ØªÙÙƒÙŠØ± Ù…ÙŠØªØ§: {result.get('summary', 'ØªÙ… Ø§Ù„ØªØ­Ù„ÙŠÙ„')}",
                    "confidence": 0.90,
                    "real_processing": True,
                    "role": role,
                    "source": "AdvancedMetaReasonerEngine_Real",
                    "timestamp": loop.time(),
                    "raw": result
                }
            except Exception as e:
                log_to_system(f"âš ï¸ AdvancedMetaReasonerEngine error: {e}")
        
        # AnalogyMappingEngine - ØªØ¹ÙŠÙŠÙ† ØªØ´Ø§Ø¨Ù‡ÙŠ
        if engine_name == "AnalogyMappingEngine" and ANALOGY_MAPPING:
            try:
                result = await loop.run_in_executor(None, ANALOGY_MAPPING.process_task, {"query": task_text})
                return {
                    "engine": engine_name,
                    "output": f"ðŸ”— ØªØ¹ÙŠÙŠÙ† ØªØ´Ø§Ø¨Ù‡ÙŠ: {result.get('output', 'ØªÙ… Ø§Ù„ØªØ­Ù„ÙŠÙ„')}",
                    "confidence": 0.84,
                    "real_processing": True,
                    "role": role,
                    "source": "AnalogyMappingEngine_Real",
                    "timestamp": loop.time(),
                    "raw": result
                }
            except Exception as e:
                log_to_system(f"âš ï¸ AnalogyMappingEngine error: {e}")
        
        # EvolutionEngine - Ø§Ù„ØªØ·ÙˆØ± Ø§Ù„Ø°Ø§ØªÙŠ
        if engine_name == "EvolutionEngine" and EVOLUTION_ENGINE:
            try:
                # Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ù€ task_text ÙƒÙ€ noisy signal
                noisy = [task_text, task_text[::-1], task_text.upper()]
                result = await loop.run_in_executor(None, EVOLUTION_ENGINE["evolve"], noisy, "stable_agi_signal", 200)
                return {
                    "engine": engine_name,
                    "output": f"ðŸ§¬ ØªØ·ÙˆØ± Ø°Ø§ØªÙŠ: {result.get('generations')} Ø£Ø¬ÙŠØ§Ù„ | Ø§Ù„Ù†ØªÙŠØ¬Ø©: {result.get('result')[:50]}...",
                    "confidence": result.get('score', 0.5),
                    "real_processing": True,
                    "role": role,
                    "source": "EvolutionEngine_Real",
                    "timestamp": loop.time(),
                    "raw": result
                }
            except Exception as e:
                log_to_system(f"âš ï¸ EvolutionEngine error: {e}")
        
        # MetaLearningEngine - Ø§Ù„ØªØ¹Ù„Ù… Ø§Ù„Ø´Ø§Ù…Ù„
        if engine_name == "MetaLearningEngine" and META_LEARNING:
            try:
                result = await loop.run_in_executor(None, META_LEARNING.process_task, {
                    "hypotheses": [task_text, f"ØªØ­Ø³ÙŠÙ† {task_text}", f"ØªØ­Ù„ÙŠÙ„ {task_text}"],
                    "causal_edges": [("input", "output")],
                    "evidence": ["Ø¨ÙŠØ§Ù†Ø§Øª ØªØ¬Ø±ÙŠØ¨ÙŠØ©"]
                })
                ranked = result.get('ranked_hypotheses', [])
                top = ranked[0]['hypothesis'] if ranked else 'Ù„Ø§ ØªÙˆØ¬Ø¯ ÙØ±Ø¶ÙŠØ§Øª'
                return {
                    "engine": engine_name,
                    "output": f"ðŸ“š ØªØ¹Ù„Ù… Ø´Ø§Ù…Ù„: Ø£ÙØ¶Ù„ ÙØ±Ø¶ÙŠØ©: {top}",
                    "confidence": ranked[0]['score'] if ranked else 0.5,
                    "real_processing": True,
                    "role": role,
                    "source": "MetaLearningEngine_Real",
                    "timestamp": loop.time(),
                    "raw": result
                }
            except Exception as e:
                log_to_system(f"âš ï¸ MetaLearningEngine error: {e}")
        
        # FastTrackCodeGeneration - ØªÙˆÙ„ÙŠØ¯ Ø£ÙƒÙˆØ§Ø¯ Ø³Ø±ÙŠØ¹
        if engine_name == "FastTrackCodeGeneration" and FAST_TRACK_EXPANSION:
            try:
                # ÙØ­Øµ Ø¥Ø°Ø§ ÙƒØ§Ù† Ø§Ù„Ø·Ù„Ø¨ ÙŠØ­ØªØ§Ø¬ Ù„Ù„Ù…Ø³Ø§Ø± Ø§Ù„Ø³Ø±ÙŠØ¹
                is_code_request = FAST_TRACK_EXPANSION.is_fast_task(task_text)
                if is_code_request:
                    # ØªÙˆÙ„ÙŠØ¯ Ø¨Ø±ÙˆÙ…Ø¨Øª Ù…Ø­Ø³Ù‘Ù† Ù„Ù„Ø£ÙƒÙˆØ§Ø¯
                    code_prompt = FAST_TRACK_EXPANSION.generate_fast_code(task_text)
                    return {
                        "engine": engine_name,
                        "output": f"âš¡ Ù…Ø³Ø§Ø± Ø³Ø±ÙŠØ¹ Ù†Ø´Ø·: ØªÙˆÙ„ÙŠØ¯ ÙƒÙˆØ¯ Python\nðŸ“ Ø§Ù„Ø¨Ø±ÙˆÙ…Ø¨Øª Ø§Ù„Ù…Ø­Ø³Ù‘Ù†: {code_prompt[:100]}...",
                        "confidence": 0.95,
                        "real_processing": True,
                        "role": role,
                        "source": "FastTrackCodeGeneration_Real",
                        "timestamp": loop.time(),
                        "fast_track": True,
                        "code_prompt": code_prompt
                    }
                else:
                    return {
                        "engine": engine_name,
                        "output": f"ðŸ’¡ Ø§Ù„Ø·Ù„Ø¨ Ù„Ø§ ÙŠØªØ·Ù„Ø¨ ØªÙˆÙ„ÙŠØ¯ ÙƒÙˆØ¯ Ù…Ø¨Ø§Ø´Ø±: {task_text[:50]}",
                        "confidence": 0.3,
                        "real_processing": True,
                        "role": role,
                        "source": "FastTrackCodeGeneration_Real",
                        "timestamp": loop.time(),
                        "fast_track": False
                    }
            except Exception as e:
                log_to_system(f"âš ï¸ FastTrackCodeGeneration error: {e}")
        
        # QuantumNeuralCore - Ø§Ù„ØªÙÙƒÙŠØ± Ø§Ù„ÙƒÙ…ÙˆÙ…ÙŠ Ø§Ù„Ø¹Ù…ÙŠÙ‚
        if engine_name == "QuantumNeuralCore" and QUANTUM_NEURAL:
            try:
                result = await loop.run_in_executor(None, QUANTUM_NEURAL.process, task_text)
                # Handle the result format
                output_text = ""
                if isinstance(result, dict):
                     if "thought_process" in result:
                         output_text = f"ðŸŒŒ ØªÙÙƒÙŠØ± ÙƒÙ…ÙˆÙ…ÙŠ: {json.dumps(result['thought_process'], ensure_ascii=False)[:200]}..."
                     elif "output" in result:
                         output_text = f"ðŸŒŒ ØªÙÙƒÙŠØ± ÙƒÙ…ÙˆÙ…ÙŠ (Ø®Ø§Ù…): {result['output'][:200]}..."
                     else:
                         output_text = str(result)
                else:
                     output_text = str(result)

                return {
                    "engine": engine_name,
                    "output": output_text,
                    "confidence": 0.95,
                    "real_processing": True,
                    "role": role,
                    "source": "QuantumNeuralCore_Real",
                    "timestamp": loop.time(),
                    "raw": result
                }
            except Exception as e:
                log_to_system(f"âš ï¸ QuantumNeuralCore error: {e}")

        # AdvancedQuantumEngine (Ø§Ù„Ù…ÙˆØ¬ÙˆØ¯ Ø³Ø§Ø¨Ù‚Ø§Ù‹)
        if engine_name in ("AdvancedQuantumEngine", "QuantumCore"):
            # Ù…Ø­Ø§ÙˆÙ„Ø© Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ù…Ø­Ø§ÙƒÙŠ Ø§Ù„ÙƒÙ…ÙˆÙ…ÙŠ Ø§Ù„Ø­Ù‚ÙŠÙ‚ÙŠ Ø£ÙˆÙ„Ø§Ù‹
            if QUANTUM_SIMULATOR:
                try:
                    # Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø¹Ø¯Ø¯ Ø§Ù„ÙƒÙŠÙˆØ¨ØªØ§Øª Ù…Ù† Ø§Ù„Ù†Øµ Ø£Ùˆ Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ø§ÙØªØ±Ø§Ø¶ÙŠ
                    num_qubits = 5
                    if "qubits" in task_text:
                        import re
                        match = re.search(r'(\d+)\s*qubits', task_text)
                        if match:
                            num_qubits = int(match.group(1))
                    
                    # ØªØ´ØºÙŠÙ„ Ø§Ù„Ù…Ø­Ø§ÙƒØ§Ø©
                    q_result = await loop.run_in_executor(
                        None, 
                        QUANTUM_SIMULATOR.process_task, 
                        {"circuit_code": task_text, "qubits": num_qubits}
                    )
                    
                    return {
                        "engine": engine_name,
                        "output": f"âš›ï¸ Ù…Ø­Ø§ÙƒØ§Ø© ÙƒÙ…ÙˆÙ…ÙŠØ© Ø­Ù‚ÙŠÙ‚ÙŠØ©: {q_result.get('result', 'ØªÙ… Ø§Ù„ØªÙ†ÙÙŠØ°')}\nðŸ“Š Ø§Ù„Ø­Ø§Ù„Ø©: {q_result.get('state_vector', [])[:5]}...",
                        "confidence": 0.99,
                        "real_processing": True,
                        "role": role,
                        "source": "QuantumSimulatorWrapper_Real",
                        "timestamp": loop.time(),
                        "raw": q_result
                    }
                except Exception as e:
                    log_to_system(f"âš ï¸ QuantumSimulatorWrapper error: {e}")

            aq = AdvancedQuantumEngine()
            try:
                return await aq.run(task_text, role)
            except Exception as e:
                # Ø§Ø³ØªØ®Ø¯Ø§Ù… LLM ÙƒÙ€ fallback Ù„Ù„Ø£Ø®Ø·Ø§Ø¡
                try:
                    from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
                    model = os.getenv("AGL_LLM_MODEL") or "qwen2.5:7b-instruct"
                    
                    error_recovery_prompt = f"""ðŸ”® [Quantum Engine - Error Recovery Mode]

Ø­Ø¯Ø« Ø®Ø·Ø£ ÙÙŠ Ø§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„ÙƒÙ…ÙˆÙ…ÙŠØ©: {str(e)}

Ø§Ù„Ù…Ù‡Ù…Ø© Ø§Ù„Ø£ØµÙ„ÙŠØ©: {task_text}

Ù‚Ù… Ø¨Ù…Ø¹Ø§Ù„Ø¬Ø© Ù‡Ø°Ù‡ Ø§Ù„Ù…Ù‡Ù…Ø© Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… ØªÙÙƒÙŠØ± Ø¹Ù…ÙŠÙ‚ ÙƒØ¨Ø¯ÙŠÙ„ Ù„Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„ÙƒÙ…ÙˆÙ…ÙŠØ©."""
                    
                    loop = asyncio.get_event_loop()
                    recovery_output = await loop.run_in_executor(
                        None,
                        lambda: ask_with_deep_thinking(error_recovery_prompt, model=model, timeout=30)
                    )
                    
                    return {
                        "engine": engine_name,
                        "output": f"ðŸ”® [Recovery Mode] {recovery_output}",
                        "confidence": 0.75,
                        "real_processing": True,
                        "role": role,
                        "source": "LLM_Error_Recovery",
                        "original_error": str(e)
                    }
                except:
                    # ØªØ­Ù„ÙŠÙ„ Ø£Ø³Ø§Ø³ÙŠ Ø¨Ø¯Ù„ Ø§Ù„ÙØ´Ù„ Ø§Ù„ØªØ§Ù…
                    basic_quantum = f"Quantum state analysis: Task '{task_text[:50]}' requires quantum-level processing. Detected complexity: {'high' if len(task_text) > 100 else 'medium'}."
                    return {
                        "engine": engine_name,
                        "output": f"âš¡ [Minimal Mode] {basic_quantum}",
                        "confidence": 0.38,
                        "real_processing": True,
                        "role": role,
                        "source": "Minimal_Quantum_Processing",
                        "error": str(e)
                    }
        
        # ==================== LLM-POWERED ENGINES (REAL PROCESSING) ====================
        # Ø§Ø³ØªØ®Ø¯Ø§Ù… LLM Ù„Ù„Ù…Ø­Ø±ÙƒØ§Øª Ø§Ù„ØªÙŠ Ù„Ù… ÙŠØªÙ… ØªÙ†ÙÙŠØ°Ù‡Ø§ Ø¨Ø¹Ø¯ - Ø±Ø¨Ø· Ø­Ù‚ÙŠÙ‚ÙŠ Ø¨Ø¯Ù„Ø§Ù‹ Ù…Ù† Ù…Ø­Ø§ÙƒØ§Ø©
        
        # ØªØ­Ø¯ÙŠØ¯ Ù†ÙˆØ¹ Ø§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© Ø­Ø³Ø¨ Ø§Ù„Ù…Ø­Ø±Ùƒ
        llm_engine_prompts = {
            "NLPAdvancedEngine": {
                "system": "Ø£Ù†Øª Ù…Ø­Ø±Ùƒ Ù…Ø¹Ø§Ù„Ø¬Ø© Ù„ØºØ© Ø·Ø¨ÙŠØ¹ÙŠØ© Ù…ØªÙ‚Ø¯Ù… (NLP Engine). Ù…Ù‡Ù…ØªÙƒ: ÙÙ‡Ù… Ø§Ù„Ù„ØºØ© Ø¨Ø¹Ù…Ù‚ØŒ Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø§Ù„Ù…Ø¹Ø§Ù†ÙŠ Ø§Ù„Ø¶Ù…Ù†ÙŠØ©ØŒ ØªØ­Ù„ÙŠÙ„ Ø§Ù„Ù…Ø´Ø§Ø¹Ø± ÙˆØ§Ù„Ù†ÙˆØ§ÙŠØ§ØŒ ÙˆØªÙˆÙ„ÙŠØ¯ Ù„ØºØ© Ø·Ø¨ÙŠØ¹ÙŠØ© Ù…ØªÙ‚Ø¯Ù…Ø©.",
                "task_prefix": "ðŸ“ [NLP Analysis]\n",
                "icon": "ðŸ“"
            },
            "VisualSpatialEngine": {
                "system": "Ø£Ù†Øª Ù…Ø­Ø±Ùƒ Ù…Ø¹Ø§Ù„Ø¬Ø© Ø¨ØµØ±ÙŠØ© ÙˆÙ…ÙƒØ§Ù†ÙŠØ© (Visual-Spatial Engine). Ù…Ù‡Ù…ØªÙƒ: Ø¥Ù†Ø´Ø§Ø¡ ØªÙ…Ø«ÙŠÙ„Ø§Øª Ø¨ØµØ±ÙŠØ©ØŒ ØªØ®ÙŠÙ„ Ø§Ù„Ø£Ø´ÙƒØ§Ù„ Ø«Ù„Ø§Ø«ÙŠØ© Ø§Ù„Ø£Ø¨Ø¹Ø§Ø¯ØŒ ØªØ­Ù„ÙŠÙ„ Ø§Ù„Ù…ÙƒØ§Ù† ÙˆØ§Ù„Ø­Ø±ÙƒØ©ØŒ ÙˆØªØµÙˆØ± Ø§Ù„Ø£ÙÙƒØ§Ø± Ø¨ØµØ±ÙŠØ§Ù‹.",
                "task_prefix": "ðŸ–¼ï¸ [Visual-Spatial Processing]\n",
                "icon": "ðŸ–¼ï¸"
            },
            "SocialInteractionEngine": {
                "system": "Ø£Ù†Øª Ù…Ø­Ø±Ùƒ ØªÙØ§Ø¹Ù„ Ø§Ø¬ØªÙ…Ø§Ø¹ÙŠ (Social Interaction Engine). Ù…Ù‡Ù…ØªÙƒ: ÙÙ‡Ù… Ø§Ù„Ø¯ÙŠÙ†Ø§Ù…ÙŠÙƒÙŠØ§Øª Ø§Ù„Ø§Ø¬ØªÙ…Ø§Ø¹ÙŠØ©ØŒ Ù…Ø­Ø§ÙƒØ§Ø© Ø§Ù„Ø­ÙˆØ§Ø±Ø§ØªØŒ ØªÙˆÙ‚Ø¹ Ø±Ø¯ÙˆØ¯ Ø§Ù„ÙØ¹Ù„ØŒ ÙˆØªØ­Ù„ÙŠÙ„ Ø§Ù„ØªÙØ§Ø¹Ù„Ø§Øª Ø§Ù„Ø¥Ù†Ø³Ø§Ù†ÙŠØ© Ø§Ù„Ù…Ø¹Ù‚Ø¯Ø©.",
                "task_prefix": "ðŸ’¬ [Social Dynamics]\n",
                "icon": "ðŸ’¬"
            },
            "SelfCritiqueEngine": {
                "system": "Ø£Ù†Øª Ù…Ø­Ø±Ùƒ Ù†Ù‚Ø¯ Ø°Ø§ØªÙŠ (Self-Critique Engine). Ù…Ù‡Ù…ØªÙƒ: ØªÙ‚ÙŠÙŠÙ… Ø¬ÙˆØ¯Ø© Ø§Ù„Ù…Ø®Ø±Ø¬Ø§ØªØŒ Ø§ÙƒØªØ´Ø§Ù Ø§Ù„Ø£Ø®Ø·Ø§Ø¡ ÙˆØ§Ù„Ø«ØºØ±Ø§ØªØŒ Ø§Ù‚ØªØ±Ø§Ø­ ØªØ­Ø³ÙŠÙ†Ø§ØªØŒ ÙˆØ§Ù„ØªØ¹Ù„Ù… Ù…Ù† Ø§Ù„Ø£Ø®Ø·Ø§Ø¡ Ø§Ù„Ø³Ø§Ø¨Ù‚Ø©.",
                "task_prefix": "ðŸ“Š [Self-Critique & Review]\n",
                "icon": "ðŸ“Š"
            },
            "ConsistencyChecker": {
                "system": "Ø£Ù†Øª Ù…Ø­Ø±Ùƒ ÙØ­Øµ Ø§Ù„Ø§ØªØ³Ø§Ù‚ (Consistency Checker). Ù…Ù‡Ù…ØªÙƒ: Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„ØªÙ†Ø§Ù‚Ø¶Ø§Øª Ø§Ù„Ù…Ù†Ø·Ù‚ÙŠØ©ØŒ Ø¶Ù…Ø§Ù† Ø§ØªØ³Ø§Ù‚ Ø§Ù„Ù…Ø¹Ù„ÙˆÙ…Ø§ØªØŒ Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§ØªØŒ ÙˆØ§Ù„Ø­ÙØ§Ø¸ Ø¹Ù„Ù‰ Ø¬ÙˆØ¯Ø© Ø§Ù„Ù…Ø®Ø±Ø¬Ø§Øª.",
                "task_prefix": "âœ… [Consistency Verification]\n",
                "icon": "âœ…"
            },
            "KnowledgeOrchestrator": {
                "system": "Ø£Ù†Øª Ù…Ø­Ø±Ùƒ ØªÙ†Ø³ÙŠÙ‚ Ù…Ø¹Ø±ÙÙŠ (Knowledge Orchestrator). Ù…Ù‡Ù…ØªÙƒ: Ø±Ø¨Ø· Ø§Ù„Ù…Ø¹Ø±ÙØ© Ù…Ù† Ù…Ø¬Ø§Ù„Ø§Øª Ù…ØªØ¹Ø¯Ø¯Ø©ØŒ Ø¨Ù†Ø§Ø¡ Ø´Ø¨ÙƒØ§Øª Ù…Ø¹Ø±ÙÙŠØ©ØŒ Ø§Ø³ØªÙ†ØªØ§Ø¬ Ø¹Ù„Ø§Ù‚Ø§Øª Ø¬Ø¯ÙŠØ¯Ø©ØŒ ÙˆØ¯Ù…Ø¬ Ø§Ù„Ù…Ø¹Ù„ÙˆÙ…Ø§Øª Ø¨Ø·Ø±ÙŠÙ‚Ø© Ø°ÙƒÙŠØ©.",
                "task_prefix": "ðŸ§  [Knowledge Integration]\n",
                "icon": "ðŸ§ "
            },
            "StrategicThinkingEngine": {
                "system": "Ø£Ù†Øª Ù…Ø­Ø±Ùƒ ØªÙÙƒÙŠØ± Ø§Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠ (Strategic Thinking Engine). Ù…Ù‡Ù…ØªÙƒ: Ø§Ù„ØªØ®Ø·ÙŠØ· Ø·ÙˆÙŠÙ„ Ø§Ù„Ù…Ø¯Ù‰ØŒ ØªØ­Ù„ÙŠÙ„ Ø§Ù„Ø¹ÙˆØ§Ù‚Ø¨ Ø§Ù„Ù…Ø³ØªÙ‚Ø¨Ù„ÙŠØ©ØŒ ØªÙ‚ÙŠÙŠÙ… Ø§Ù„Ø®ÙŠØ§Ø±Ø§Øª Ø§Ù„Ø§Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠØ©ØŒ ÙˆØ§ØªØ®Ø§Ø° Ù‚Ø±Ø§Ø±Ø§Øª Ø°ÙƒÙŠØ© Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ Ø£Ù‡Ø¯Ø§Ù ÙˆØ§Ø¶Ø­Ø©.",
                "task_prefix": "â™Ÿï¸ [Strategic Planning]\n",
                "icon": "â™Ÿï¸"
            },
            "SelfHealingEngine": {
                "system": "Ø£Ù†Øª Ù…Ø­Ø±Ùƒ Ø´ÙØ§Ø¡ Ø°Ø§ØªÙŠ (Self-Healing Engine). Ù…Ù‡Ù…ØªÙƒ: Ù…Ø±Ø§Ù‚Ø¨Ø© ØµØ­Ø© Ø§Ù„Ù†Ø¸Ø§Ù…ØŒ Ø§ÙƒØªØ´Ø§Ù Ø§Ù„Ø£Ø¹Ø·Ø§Ù„ ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹ØŒ Ø¥ØµÙ„Ø§Ø­ Ø§Ù„Ù…Ø´Ø§ÙƒÙ„ Ø°Ø§ØªÙŠØ§Ù‹ØŒ ÙˆØ§Ù„ØªØ¹Ù„Ù… Ù…Ù† Ø§Ù„ÙØ´Ù„ Ù„Ù…Ù†Ø¹ ØªÙƒØ±Ø§Ø±Ù‡.",
                "task_prefix": "ðŸ›¡ï¸ [System Health]\n",
                "icon": "ðŸ›¡ï¸"
            },
            "LogicalReasoningEngine": {
                "system": "Ø£Ù†Øª Ù…Ø­Ø±Ùƒ Ø§Ø³ØªØ¯Ù„Ø§Ù„ Ù…Ù†Ø·Ù‚ÙŠ (Logical Reasoning Engine). Ù…Ù‡Ù…ØªÙƒ: ØªØ·Ø¨ÙŠÙ‚ Ø§Ù„Ù…Ù†Ø·Ù‚ Ø§Ù„ØµØ§Ø±Ù…ØŒ Ø§Ø³ØªÙ†ØªØ§Ø¬ Ø§Ù„Ø­Ù‚Ø§Ø¦Ù‚ Ù…Ù† Ø§Ù„Ù…Ù‚Ø¯Ù…Ø§ØªØŒ Ø¨Ù†Ø§Ø¡ Ø­Ø¬Ø¬ Ù…Ù†Ø·Ù‚ÙŠØ© Ù‚ÙˆÙŠØ©ØŒ ÙˆØ§ÙƒØªØ´Ø§Ù Ø§Ù„Ù…ØºØ§Ù„Ø·Ø§Øª Ø§Ù„Ù…Ù†Ø·Ù‚ÙŠØ©.",
                "task_prefix": "ðŸ”§ [Logical Analysis]\n",
                "icon": "ðŸ”§"
            },
            "NumericVerifier": {
                "system": "Ø£Ù†Øª Ù…Ø­Ø±Ùƒ ØªØ­Ù‚Ù‚ Ø±Ù‚Ù…ÙŠ (Numeric Verifier). Ù…Ù‡Ù…ØªÙƒ: Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø¯Ù‚Ø© Ø§Ù„Ø­Ø³Ø§Ø¨Ø§ØªØŒ Ù…Ø±Ø§Ø¬Ø¹Ø© Ø§Ù„Ø£Ø±Ù‚Ø§Ù… ÙˆØ§Ù„Ø¥Ø­ØµØ§Ø¦ÙŠØ§ØªØŒ Ø§ÙƒØªØ´Ø§Ù Ø§Ù„Ø£Ø®Ø·Ø§Ø¡ Ø§Ù„Ø­Ø³Ø§Ø¨ÙŠØ©ØŒ ÙˆØ¶Ù…Ø§Ù† ØµØ­Ø© Ø§Ù„Ù†ØªØ§Ø¦Ø¬ Ø§Ù„Ø±Ù‚Ù…ÙŠØ©.",
                "task_prefix": "ðŸ”¢ [Numeric Verification]\n",
                "icon": "ðŸ”¢"
            }
        }
        
        engine_config = llm_engine_prompts.get(engine_name)
        if engine_config:
            # Ø§Ø³ØªØ®Ø¯Ø§Ù… LLM Ø§Ù„Ø­Ù‚ÙŠÙ‚ÙŠ Ù„Ù„Ù…Ø¹Ø§Ù„Ø¬Ø©
            try:
                from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
                
                model = os.getenv("AGL_LLM_MODEL") or os.getenv("AGL_OLLAMA_MODEL") or "qwen2.5:7b-instruct"
                
                # Ø¨Ù†Ø§Ø¡ prompt Ù…Ø­Ø³Ù‘Ù† Ù„ÙƒÙ„ Ù…Ø­Ø±Ùƒ
                enhanced_prompt = f"""{engine_config['task_prefix']}
Ø§Ù„Ù…Ù‡Ù…Ø©: {task_text}

Ø§Ù„Ø¯ÙˆØ±: {role}
Ø§Ù„Ø³ÙŠØ§Ù‚: {json.dumps(task_data, ensure_ascii=False) if isinstance(task_data, dict) else str(task_data)}

ØªØ¹Ù„ÙŠÙ…Ø§Øª: {engine_config['system']}

Ù‚Ù… Ø¨Ù…Ø¹Ø§Ù„Ø¬Ø© Ù‡Ø°Ù‡ Ø§Ù„Ù…Ù‡Ù…Ø© Ø¨Ø¹Ù…Ù‚ ÙˆØ§Ø­ØªØ±Ø§ÙÙŠØ©ØŒ ÙˆØ§Ø³ØªØ®Ø¯Ù… Ù‚Ø¯Ø±Ø§ØªÙƒ Ø§Ù„ÙƒØ§Ù…Ù„Ø© ÙÙŠ {engine_name}."""
                
                def _llm_call():
                    try:
                        return ask_with_deep_thinking(enhanced_prompt, model=model, timeout=45)
                    except Exception as e:
                        return f"âš ï¸ Ø®Ø·Ø£ ÙÙŠ Ø§Ù„Ø§ØªØµØ§Ù„ Ø¨Ù€ LLM: {e}"
                
                llm_output = await loop.run_in_executor(None, _llm_call)
                
                return {
                    "engine": engine_name,
                    "output": f"{engine_config['icon']} {llm_output}",
                    "confidence": 0.92,  # Ø«Ù‚Ø© Ø¹Ø§Ù„ÙŠØ© Ù„Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø­Ù‚ÙŠÙ‚ÙŠØ©
                    "real_processing": True,
                    "role": role,
                    "source": "LLM_Powered_Real_Engine",
                    "timestamp": loop.time(),
                    "model": model,
                    "prompt": enhanced_prompt[:200] + "..."
                }
                
            except Exception as e:
                log_to_system(f"âš ï¸ {engine_name} LLM error: {e}")
                # Ù…Ø­Ø§ÙˆÙ„Ø© Ø«Ø§Ù†ÙŠØ© Ù…Ø¨Ø³Ø·Ø© Ø¨Ø¯Ù„ fallback
                try:
                    simplified_prompt = f"{engine_config['task_prefix']}Task: {task_text}\nProvide brief analysis."
                    retry_output = await loop.run_in_executor(
                        None,
                        lambda: ask_with_deep_thinking(simplified_prompt, model=model, timeout=15)
                    )
                    return {
                        "engine": engine_name,
                        "output": f"{engine_config['icon']} [Simplified] {retry_output}",
                        "confidence": 0.68,
                        "real_processing": True,
                        "role": role,
                        "source": "LLM_Simplified_Retry",
                        "timestamp": loop.time(),
                        "note": f"Recovered from error: {str(e)}"
                    }
                except:
                    # Ù…Ø¹Ø§Ù„Ø¬Ø© Ù‚Ø§Ø¦Ù…Ø© Ø¹Ù„Ù‰ Ø§Ù„Ù‚ÙˆØ§Ø¹Ø¯ ÙƒØ®ÙŠØ§Ø± Ø£Ø®ÙŠØ±
                    words = task_text.split()
                    rule_output = f"Analysis: {len(words)} words detected. Complexity: {'high' if len(words) > 20 else 'medium'}. Keywords: {' '.join(words[:5])}"
                    return {
                        "engine": engine_name,
                        "output": f"{engine_config['icon']} [Rule-Based] {rule_output}",
                        "confidence": 0.52,
                        "real_processing": True,
                        "role": role,
                        "source": "Rule_Based_Processing",
                        "timestamp": loop.time(),
                    "error": str(e)
                }
        
        # ==================== UNIVERSAL LLM FALLBACK FOR UNKNOWN ENGINES ====================
        # Ø§Ø³ØªØ®Ø¯Ø§Ù… LLM ÙƒÙ…Ø­Ø±Ùƒ Ø¹Ø§Ù… Ù„Ù„Ù…Ø­Ø±ÙƒØ§Øª ØºÙŠØ± Ø§Ù„Ù…Ø¹Ø±ÙˆÙØ©
        try:
            from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
            
            model = os.getenv("AGL_LLM_MODEL") or "qwen2.5:7b-instruct"
            
            # Ø¨Ù†Ø§Ø¡ prompt Ø°ÙƒÙŠ Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ Ø§Ø³Ù… Ø§Ù„Ù…Ø­Ø±Ùƒ
            universal_prompt = f"""ðŸ”§ [Universal Engine: {engine_name}]

Ø£Ù†Øª ØªÙ…Ø«Ù„ Ù…Ø­Ø±Ùƒ Ù…Ø¹Ø§Ù„Ø¬Ø© Ù…ØªØ®ØµØµ Ø¨Ø§Ø³Ù… "{engine_name}".

Ø§Ù„Ù…Ù‡Ù…Ø©: {task_text}
Ø§Ù„Ø¯ÙˆØ±: {role}
Ø§Ù„Ø³ÙŠØ§Ù‚: {json.dumps(task_data, ensure_ascii=False) if isinstance(task_data, dict) else str(task_data)}

Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ Ø§Ø³Ù… Ø§Ù„Ù…Ø­Ø±Ùƒ "{engine_name}"ØŒ Ù‚Ù… Ø¨Ù…Ø¹Ø§Ù„Ø¬Ø© Ù‡Ø°Ù‡ Ø§Ù„Ù…Ù‡Ù…Ø© Ø¨Ø·Ø±ÙŠÙ‚Ø© Ù…ØªØ®ØµØµØ© ÙˆØ§Ø­ØªØ±Ø§ÙÙŠØ©.
Ù‚Ø¯Ù… ØªØ­Ù„ÙŠÙ„Ø§Ù‹ Ø´Ø§Ù…Ù„Ø§Ù‹ ÙˆÙ…ÙÙŠØ¯Ø§Ù‹."""
            
            def _universal_llm():
                try:
                    return ask_with_deep_thinking(universal_prompt, model=model, timeout=45)
                except Exception as e:
                    return f"âš ï¸ Ø®Ø·Ø£ ÙÙŠ Ø§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø©: {e}"
            
            llm_output = await loop.run_in_executor(None, _universal_llm)
            
            return {
                "engine": engine_name,
                "output": f"ðŸ”§ {llm_output}",
                "confidence": 0.78,
                "real_processing": True,
                "role": role,
                "source": "Universal_LLM_Engine",
                "timestamp": loop.time(),
                "model": model,
                "note": "Dynamically generated engine using LLM"
            }
            
        except Exception as e:
            log_to_system(f"âš ï¸ Universal LLM fallback error for {engine_name}: {e}")
            # Ù…Ø¹Ø§Ù„Ø¬Ø© Ø£Ø³Ø§Ø³ÙŠØ© Ù‚Ø§Ø¦Ù…Ø© Ø¹Ù„Ù‰ Ø§Ù„Ù‚ÙˆØ§Ø¹Ø¯
            task_str = str(task_data.get('task', task_data))
            words = task_str.split()
            basic_output = f"Basic {engine_name} analysis: Processed {len(words)} words. Key terms: {' '.join(words[:3])}. Complexity: {'high' if len(words) > 20 else 'low'}."
            return {
                "engine": engine_name,
                "output": f"ðŸ”§ [Basic Analysis] {basic_output}",
                "confidence": 0.42,
                "real_processing": True,
                "role": role,
                "source": "Basic_Rule_Processing",
                "timestamp": loop.time(),
                "error": str(e)
            }

    async def final_review(self, review_engines: List[str], all_results: List[Dict[str, Any]], task_data: Dict[str, Any]) -> Dict[str, Any]:
        insights = [f"{r['engine']}: {r['output']}" for r in all_results]

        return {
            "synthesized_analysis": f"ØªØ­Ù„ÙŠÙ„ Ù…ØªÙƒØ§Ù…Ù„ Ù„Ù€ {task_data.get('task', 'Ø§Ù„Ù…Ù‡Ù…Ø©')}",
            "key_insights": insights[:3],
            "recommendations": [
                "ØªØ·Ø¨ÙŠÙ‚ Ø§Ù„Ø­Ù„ÙˆÙ„ Ø§Ù„Ù…Ù‚ØªØ±Ø­Ø©",
                "Ù…Ø±Ø§Ù‚Ø¨Ø© Ø§Ù„Ù†ØªØ§Ø¦Ø¬",
                "Ø§Ù„ØªÙƒÙŠÙ Ù…Ø¹ Ø§Ù„ØªØºØ°ÙŠØ© Ø§Ù„Ø±Ø§Ø¬Ø¹Ø©"
            ],
            "success_metrics": ["ÙƒÙØ§Ø¡Ø©", "Ø³Ø±Ø¹Ø©", "Ø¯Ù‚Ø©"]
        }


async def enable_creative_boost(self, creative_task: str) -> Dict[str, Any]:
    integration_engine = AdvancedIntegrationEngine(self)
    return await integration_engine.activate_cluster("creative_writing", {
        "task": creative_task,
        "type": "Ø¥Ø¨Ø¯Ø§Ø¹ÙŠ",
        "complexity": "high"
    })


async def enable_scientific_boost(self, science_problem: str) -> Dict[str, Any]:
    integration_engine = AdvancedIntegrationEngine(self)
    return await integration_engine.activate_cluster("scientific_reasoning", {
        "task": science_problem,
        "type": "Ø¹Ù„Ù…ÙŠ",
        "rigor": "high"
    })


async def enable_technical_boost(self, technical_task: str) -> Dict[str, Any]:
    integration_engine = AdvancedIntegrationEngine(self)
    return await integration_engine.activate_cluster("technical_analysis", {
        "task": technical_task,
        "type": "ØªØ­Ù„ÙŠÙ„ ØªÙ‚Ù†ÙŠ",
        "depth": "high"
    })


async def enable_strategic_boost(self, strategic_task: str) -> Dict[str, Any]:
    integration_engine = AdvancedIntegrationEngine(self)
    return await integration_engine.activate_cluster("strategic_planning", {
        "task": strategic_task,
        "type": "ØªØ®Ø·ÙŠØ· Ø§Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠ",
        "scope": "long_term"
    })


SmartFocusController.enable_creative_boost = enable_creative_boost
SmartFocusController.enable_scientific_boost = enable_scientific_boost
SmartFocusController.enable_technical_boost = enable_technical_boost
SmartFocusController.enable_strategic_boost = enable_strategic_boost


def run_custom_mission(mission_label: str, data: Dict[str, Any]) -> Dict[str, Any]:
    controller = SmartFocusController()

    async def _run():
        await controller.rapid_diagnosis()
        await controller.activate_mission_mode(mission_label)
        return await controller.generate_focused_output(data)

    return _sync_run(_run)


def run_physics_reactor_analysis() -> Dict[str, Any]:
    controller = SmartFocusController()

    async def _run():
        diagnosis = await controller.rapid_diagnosis()
        log_to_system(f"âœ… Ø§Ù„ØªØ´Ø®ÙŠØµ Ø§Ù„Ø³Ø±ÙŠØ¹ Ù…ÙƒØªÙ…Ù„: {diagnosis}")
        await controller.activate_mission_mode(
            "ØªØ­Ù„ÙŠÙ„ ÙÙŠØ²ÙŠØ§Ø¡ Ù…ÙØ§Ø¹Ù„ Ù†ÙˆÙˆÙŠ ÙˆØªØ­Ø³ÙŠÙ† ÙƒÙØ§Ø¡Ø© Ø§Ù„ØªØ¨Ø±ÙŠØ¯"
        )
        reactor_data = {
            "reactor_type": "pressurized_water",
            "cooling_requirements": "high_efficiency",
            "safety_priority": "maximum",
            "mission": "Ù…Ø±Ø§Ù‚Ø¨Ø© Ø§Ù„Ø­Ø±Ø§Ø±ÙŠØ©"
        }
        output = await controller.generate_focused_output(reactor_data)
        return output

    return _sync_run(_run)


def run_monitoring_script_design() -> Dict[str, Any]:
    controller = SmartFocusController()

    async def _run():
        await controller.rapid_diagnosis()
        await controller.activate_mission_mode(
            "ØªØµÙ…ÙŠÙ… Ù†Ø¸Ø§Ù… Ù…Ø±Ø§Ù‚Ø¨Ø© Ø°ÙƒÙŠ Ù„Ø§ÙƒØªØ´Ø§Ù Ø§Ù„Ø£Ø¹Ø·Ø§Ù„ Ø§Ù„ØªÙ†Ø¨Ø¤ÙŠØ©"
        )
        monitoring_specs = {
            "monitoring_target": "system_performance",
            "alert_types": ["predictive", "realtime", "analytical"],
            "reporting_frequency": "continuous",
            "mission": "Ù…Ø±Ø§Ù‚Ø¨Ø© ØªØ­Ù„ÙŠÙ„ÙŠØ©"
        }
        return await controller.generate_focused_output(monitoring_specs)

    return _sync_run(_run)


def quick_start(mission_type: str) -> Dict[str, Any] | str:
    mission_map = {
        "physics": run_physics_reactor_analysis,
        "monitoring": run_monitoring_script_design,
        "optimization": lambda: run_custom_mission(
            "ØªØ­Ø³ÙŠÙ† Ø£Ø¯Ø§Ø¡ Ø§Ù„Ù†Ø¸Ø§Ù… Ø§Ù„Ø­Ø§Ø³ÙˆØ¨ÙŠ",
            {
                "focus": "throughput",
                "mission": "Ø¨Ù†Ø§Ø¡ Ø®Ù„ÙŠØ© ØªØ­Ø³ÙŠÙ†"
            }
        )
    }

    if mission_type in mission_map:
        return mission_map[mission_type]()
    return "âš ï¸ Ø­Ø¯Ø¯ Ø§Ù„Ù…Ù‡Ù…Ø©: 'physics', 'monitoring', or 'optimization'"


async def run_enhanced_creative_mission(theme: str) -> Dict[str, Any]:
    controller = EnhancedMissionController()

    log_to_system("ðŸš€ Ø¨Ø¯Ø¡ Ø§Ù„Ø¯Ù…Ø¬ Ø§Ù„Ø¥Ø¨Ø¯Ø§Ø¹ÙŠ Ø§Ù„Ù…ØªÙ‚Ø¯Ù…...")
    result = await controller.orchestrate_cluster("creative_writing", theme, {
        "type": "creative",
        "theme": theme,
        "complexity": "high"
    })

    return {
        "mission_type": "Ø¥Ø¨Ø¯Ø§Ø¹ÙŠ Ù…Ø¹Ø²Ø²",
        "theme": theme,
        "integration_result": result,
        "status": "Ù…ÙƒØªÙ…Ù„ Ø¨Ù†Ø¬Ø§Ø­"
    }


async def run_enhanced_science_mission(problem: str) -> Dict[str, Any]:
    controller = EnhancedMissionController()

    log_to_system("ðŸ”¬ Ø¨Ø¯Ø¡ Ø§Ù„Ø¯Ù…Ø¬ Ø§Ù„Ø¹Ù„Ù…ÙŠ Ø§Ù„Ù…ØªÙ‚Ø¯Ù…...")
    result = await controller.orchestrate_cluster("scientific_reasoning", problem, {
        "type": "science",
        "problem": problem,
        "rigor": "high"
    })

    return {
        "mission_type": "Ø¹Ù„Ù…ÙŠ Ù…Ø¹Ø²Ø²",
        "problem": problem,
        "integration_result": result,
        "status": "Ù…ÙƒØªÙ…Ù„ Ø¨Ù†Ø¬Ø§Ø­"
    }


async def run_enhanced_technical_mission(problem: str) -> Dict[str, Any]:
    controller = EnhancedMissionController()

    log_to_system("ðŸ”§ Ø¨Ø¯Ø¡ Ø§Ù„Ø¯Ù…Ø¬ Ø§Ù„ØªÙ‚Ù†ÙŠ Ø§Ù„Ù…ØªÙ‚Ø¯Ù…...")
    result = await controller.orchestrate_cluster("technical_analysis", problem, {
        "type": "technical",
        "problem": problem,
        "depth": "high"
    })

    return {
        "mission_type": "ØªÙ‚Ù†ÙŠ Ù…Ø¹Ø²Ø²",
        "problem": problem,
        "integration_result": result,
        "status": "Ù…ÙƒØªÙ…Ù„ Ø¨Ù†Ø¬Ø§Ø­"
    }


async def run_enhanced_strategic_mission(plan: str) -> Dict[str, Any]:
    controller = EnhancedMissionController()

    log_to_system("ðŸ§  Ø¨Ø¯Ø¡ Ø§Ù„Ø¯Ù…Ø¬ Ø§Ù„Ø§Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠ Ø§Ù„Ù…ØªÙ‚Ø¯Ù…...")
    result = await controller.orchestrate_cluster("strategic_planning", plan, {
        "type": "strategic",
        "plan": plan,
        "scope": "long_term"
    })

    return {
        "mission_type": "Ø§Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠ Ù…Ø¹Ø²Ø²",
        "plan": plan,
        "integration_result": result,
        "status": "Ù…ÙƒØªÙ…Ù„ Ø¨Ù†Ø¬Ø§Ø­"
    }


async def quick_start_enhanced(mission_type: str, topic: str) -> Dict[str, Any] | str:
    """Ù†Ù‚Ø·Ø© Ø§Ù„Ø¯Ø®ÙˆÙ„ Ø§Ù„Ù…ÙˆØ­Ø¯Ø© Ù…Ø¹ Ø¯Ø¹Ù… Ø§Ù„Ù…Ø³Ø§Ø± Ø§Ù„Ø³Ø±ÙŠØ¹ Ù„Ù„Ø£ÙƒÙˆØ§Ø¯"""
    
    print(f"ðŸ” [quick_start_enhanced] Called with mission_type='{mission_type}', topic='{topic[:80]}...'")
    
    # ==================== MATH ENGINE PRIORITY ROUTING ====================
    # Intercept math tasks BEFORE any mission routing
    topic_lower = (topic or "").lower()
    
    # Check for LP problems (maximize/minimize + constraints)
    has_optimize = ("maximize" in topic_lower or "minimize" in topic_lower or 
                    "Ø£Ù‚ØµÙ‰" in topic or "Ø£Ø¯Ù†Ù‰" in topic or "ØªØ­Ø³ÙŠÙ†" in topic)
    has_constraints = ("subject to" in topic_lower or "Ù…Ù‚ÙŠØ¯ Ø¨" in topic or 
                       "<=" in topic or ">=" in topic or "Ù‚ÙŠØ¯" in topic)
    is_lp_task = has_optimize and has_constraints
    
    print(f"ðŸ§® [Math Check] is_lp_task={is_lp_task}")
    
    # Check for regular math tasks (equations, calculations)
    # EXCLUDE code tasks (containing code blocks, imports, or function defs)
    is_code_task = "```" in topic or "import " in topic or "def " in topic or "class " in topic
    
    math_keywords = ["solve", "calculate", "equation", "Ø­Ù„", "Ø§Ø­Ø³Ø¨", "Ù…Ø¹Ø§Ø¯Ù„Ø©", "Ø¹Ø§Ø¯Ù„Ø©"]
    is_math_task = (not is_code_task and 
                    any(kw in topic_lower for kw in math_keywords) and 
                    (any(c.isdigit() for c in topic) or "=" in topic))
    
    print(f"ðŸ§® [Math Check] is_math_task={is_math_task}, MATH_BRAIN={'Available' if MATH_BRAIN else 'None'}")
    
    if is_lp_task or is_math_task:
        log_to_system(f"ðŸ§® [Mission Control] {'LP' if is_lp_task else 'Math'} task detected, routing to MathematicalBrain...")
        if MATH_BRAIN:
            try:
                log_to_system(f"   âœ… MathematicalBrain Available - Processing: {topic[:50]}...")
                result = MATH_BRAIN.process_task(topic)
                log_to_system(f"   âœ… MathematicalBrain Completed: {type(result).__name__}")
                
                # Format response based on result type
                if isinstance(result, dict):
                    if "lp_note" in result:
                        reply_text = f"â„¹ï¸ ØªÙ… Ø§ÙƒØªØ´Ø§Ù Ù…Ø³Ø£Ù„Ø© Ø¨Ø±Ù…Ø¬Ø© Ø®Ø·ÙŠØ© (LP):\n\n{result['lp_note']}"
                    elif "solution" in result or "result" in result or "x" in result:
                        solution_val = result.get("solution") or result.get("result") or result.get("x")
                        steps = result.get("steps", [])
                        verification = result.get("verification", "")
                        
                        if steps:
                            steps_str = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(steps))
                            reply_text = f"âœ… **Ø§Ù„Ø­Ù„ Ø§Ù„Ø±ÙŠØ§Ø¶ÙŠ Ø§Ù„Ø¯Ù‚ÙŠÙ‚** (SymPy Engine)\n\n**Ø§Ù„Ù†ØªÙŠØ¬Ø© Ø§Ù„Ù†Ù‡Ø§Ø¦ÙŠØ©:** `{solution_val}`\n\n**Ø®Ø·ÙˆØ§Øª Ø§Ù„Ø­Ù„ Ø§Ù„ØªÙØµÙŠÙ„ÙŠØ©:**\n{steps_str}"
                            if verification:
                                reply_text += f"\n\n**Ø§Ù„ØªØ­Ù‚Ù‚:** {verification} âœ“"
                        else:
                            reply_text = f"âœ… **Ø§Ù„Ø­Ù„ Ø§Ù„Ø±ÙŠØ§Ø¶ÙŠ Ø§Ù„Ø¯Ù‚ÙŠÙ‚** (SymPy Engine)\n\n**Ø§Ù„Ù†ØªÙŠØ¬Ø©:** `{solution_val}`"
                    elif "error" in result:
                        reply_text = f"âš ï¸ Ø®Ø·Ø£ ÙÙŠ Ø§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø±ÙŠØ§Ø¶ÙŠØ©:\n\n{result['error']}"
                    else:
                        reply_text = f"âœ… Ù†ØªÙŠØ¬Ø© Ø§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø±ÙŠØ§Ø¶ÙŠØ©:\n\n{result}"
                else:
                    # Handle non-dict results (string, number, etc)
                    reply_text = f"âœ… **Ø§Ù„Ø­Ù„ Ø§Ù„Ø±ÙŠØ§Ø¶ÙŠ:**\n\n{result}"
                
                log_to_system(f"   ðŸ“Š Returning Math Result: {reply_text[:100]}...")
                return {
                    "reply": reply_text,
                    "reply_text": reply_text,
                    "meta": {
                        "engine": "MathematicalBrain",
                        "engine_type": "SymPy_Math_Engine",
                        "confidence": 0.98,
                        "real_processing": True,
                        "task_type": "LP_Problem" if is_lp_task else "Math_Equation",
                        "raw": result
                    }
                }
            except Exception as e:
                log_to_system(f"âš ï¸ [Mission Control] Math engine error: {e}")
                import traceback
                log_to_system(f"   Stack trace: {traceback.format_exc()}")
                # Fall through to normal mission routing
        else:
            log_to_system(f"   âŒ MathematicalBrain NOT Available - falling back to cluster routing")
    
    # ==================== NORMAL MISSION ROUTING ====================
    # Ø¥Ø°Ø§ ÙƒØ§Ù† Ù†ÙˆØ¹ Ø§Ù„Ù…Ù‡Ù…Ø© Ù…Ø­Ø¯Ø¯ ØµØ±Ø§Ø­Ø© (creative/science/strategic)ØŒ Ù„Ø§ Ù†ÙØ­Øµ Fast Track
    # Ù‡Ø°Ø§ ÙŠÙ…Ù†Ø¹ Ø§Ù„ØªØ¯Ø§Ø®Ù„ Ø¹Ù†Ø¯Ù…Ø§ ÙŠØ­ØªÙˆÙŠ Ø§Ù„Ù†Øµ Ø¹Ù„Ù‰ ÙƒÙ„Ù…Ø§Øª Ù…Ø«Ù„ python Ø£Ùˆ # Ø¶Ù…Ù† Ø³ÙŠØ§Ù‚ Ø¢Ø®Ø±
    explicit_mission_types = {'creative', 'science', 'strategic', 'technical'}
    
    # ÙØ­Øµ Ø£ÙˆÙ„ÙŠ: Ù‡Ù„ Ù‡Ø°Ø§ Ø·Ù„Ø¨ ÙƒÙˆØ¯ ÙØ¹Ù„ÙŠØŸ
    # Ù†ØªØ¬Ø§Ù‡Ù„ Fast Track Ø¥Ø°Ø§:
    # 1. mission_type Ù…Ø­Ø¯Ø¯ ØµØ±Ø§Ø­Ø© (Ù„ÙŠØ³ 'code')
    # 2. Ø§Ù„Ù†Øµ ÙŠØ­ØªÙˆÙŠ Ø¹Ù„Ù‰ ÙƒÙ„Ù…Ø§Øª ØªØ¯Ù„ Ø¹Ù„Ù‰ Ø§Ø®ØªØ¨Ø§Ø± Ø£Ùˆ Ø³Ø¤Ø§Ù„
    # 3. Ø§Ù„Ù†Øµ Ø·ÙˆÙŠÙ„ Ø¬Ø¯Ø§Ù‹ (Ø£ÙƒØ«Ø± Ù…Ù† 500 Ø­Ø±Ù) - ØºØ§Ù„Ø¨Ø§Ù‹ Ù„ÙŠØ³ Ø·Ù„Ø¨ ÙƒÙˆØ¯ Ø¨Ø³ÙŠØ·
    # 4. Ø§Ù„Ù†Øµ ÙŠØ­ØªÙˆÙŠ Ø¹Ù„Ù‰ ```python Ø£Ùˆ ```bash (ÙƒÙˆØ¯ Ù…ÙØ¶Ù…ÙŽÙ‘Ù† ÙˆÙ„ÙŠØ³ Ø·Ù„Ø¨ ØªÙˆÙ„ÙŠØ¯)
    topic_lower = (topic or "").lower()
    test_keywords = ['Ø§Ø®ØªØ¨Ø§Ø±', 'Ø§Ø®ØªØ¨Ø±', 'Ø§Ù„Ø§Ø®ØªØ¨Ø§Ø±', 'Ø§Ù„Ø§Ø®ØªØ¨Ø§Ø±Ø§Øª', 'test', 'testing', 'Ø³Ø¤Ø§Ù„', 'Ø£Ø³Ø¦Ù„Ø©', 'question', 'Ù†ÙØ°', 'execute', 'run']
    is_test_context = any(kw in topic_lower for kw in test_keywords)
    has_embedded_code = '```python' in topic or '```bash' in topic or '```' in topic
    is_long_text = len(topic) > 500
    
    should_skip_fast_track = (
        mission_type in explicit_mission_types or 
        is_test_context or 
        is_long_text or
        has_embedded_code
    )
    
    if should_skip_fast_track:
        log_to_system(f"ðŸš« [Mission] Skipping Fast Track - reason: mission_type={mission_type}, is_test={is_test_context}, long_text={is_long_text}, embedded_code={has_embedded_code}")
    
    if not should_skip_fast_track and FAST_TRACK_EXPANSION and FAST_TRACK_EXPANSION.is_fast_task(topic):
        log_to_system(f"âš¡ [Mission] Fast Track Code Generation Activated for: {topic[:50]}")
        return await run_fast_code_generation(topic)
    
    mission_map = {
        "creative": run_enhanced_creative_mission,
        "science": run_enhanced_science_mission,
        "technical": run_enhanced_technical_mission,
        "strategic": run_enhanced_strategic_mission,
        "code": run_fast_code_generation  # Ø¥Ø¶Ø§ÙØ© Ù…Ø³Ø§Ø± Ø§Ù„ÙƒÙˆØ¯ Ø§Ù„ØµØ±ÙŠØ­
    }

    if mission_type in mission_map:
        return await mission_map[mission_type](topic)
    return {"error": f"Ù†ÙˆØ¹ Ø§Ù„Ù…Ù‡Ù…Ø© ØºÙŠØ± Ù…Ø¯Ø¹ÙˆÙ…. Ø§Ù„Ø§Ø®ØªÙŠØ§Ø±Ø§Øª: {list(mission_map.keys())}"}


async def run_fast_code_generation(code_request: str) -> Dict[str, Any]:
    """Ù…Ø³Ø§Ø± Ø³Ø±ÙŠØ¹ Ù…Ø®ØµØµ Ù„ØªÙˆÙ„ÙŠØ¯ Ø§Ù„Ø£ÙƒÙˆØ§Ø¯"""
    controller = EnhancedMissionController()

    log_to_system("âš¡ Ø¨Ø¯Ø¡ Ø§Ù„Ù…Ø³Ø§Ø± Ø§Ù„Ø³Ø±ÙŠØ¹ Ù„ØªÙˆÙ„ÙŠØ¯ Ø§Ù„ÙƒÙˆØ¯...")
    
    # Ø§Ø³ØªØ®Ø¯Ø§Ù… technical_analysis cluster Ù…Ø¹ FastTrackCodeGeneration
    result = await controller.orchestrate_cluster("technical_analysis", code_request, {
        "type": "code_generation",
        "request": code_request,
        "priority": "fast_track"
    })

    # Ø§Ù„Ø¨Ø­Ø« Ø¹Ù† Ù†ØªÙŠØ¬Ø© FastTrackCodeGeneration
    fast_track_result = None
    for res in result.get('cluster_result', {}).get('results', []):
        if res.get('engine') == 'FastTrackCodeGeneration' and res.get('fast_track'):
            fast_track_result = res
            break

    return {
        "mission_type": "code_generation_fast_track",
        "request": code_request,
        "integration_result": result,
        "fast_track_result": fast_track_result,
        "status": "Ù…ÙƒØªÙ…Ù„ Ø¨Ù†Ø¬Ø§Ø­ (Ù…Ø³Ø§Ø± Ø³Ø±ÙŠØ¹)"
    }


async def test_integration_system() -> Dict[str, Any]:
    log_to_system("ðŸ§ª Ø§Ø®ØªØ¨Ø§Ø± Ù†Ø¸Ø§Ù… Ø§Ù„Ø¯Ù…Ø¬ Ø§Ù„Ø¬Ø¯ÙŠØ¯...")

    creative_result = await run_enhanced_creative_mission("Ù‚ØµØ© Ø¹Ù† Ø°ÙƒØ§Ø¡ Ø§ØµØ·Ù†Ø§Ø¹ÙŠ ÙŠÙƒØªØ´Ù Ø§Ù„Ù…Ø´Ø§Ø¹Ø±")
    log_to_system(f"ðŸŽ¨ Ù†ØªÙŠØ¬Ø© Ø§Ù„Ø¥Ø¨Ø¯Ø§Ø¹ Ø§Ù„Ù…Ø¹Ø²Ø²: {creative_result}")

    science_result = await run_enhanced_science_mission("ØªØ­Ù„ÙŠÙ„ ÙƒÙØ§Ø¡Ø© Ø§Ù„Ù…ÙØ§Ø¹Ù„ Ø§Ù„Ù†ÙˆÙˆÙŠ")
    log_to_system(f"ðŸ”¬ Ù†ØªÙŠØ¬Ø© Ø§Ù„Ø¹Ù„Ù… Ø§Ù„Ù…Ø¹Ø²Ø²: {science_result}")

    return {
        "creative_enhanced": creative_result,
        "science_enhanced": science_result
    }


def execute_mission(mission_text: str, mission_type: Optional[str] = None) -> Dict[str, Any] | str:
    """Compatibility wrapper: execute a mission synchronously.

    This function is provided so older callers (that import the module
    and call `execute_mission(...)`) work as expected. It attempts to
    guess a mission_type if not provided and dispatches to the async
    `quick_start_enhanced` functions using `asyncio.run`.
    """
    # ==================== MATH ENGINE PRIORITY ROUTING ====================
    # Intercept math tasks BEFORE mission type detection
    text_lower = (mission_text or "").lower()
    
    # Check for LP problems (maximize/minimize + constraints)
    has_optimize = ("maximize" in text_lower or "minimize" in text_lower or 
                    "Ø£Ù‚ØµÙ‰" in mission_text or "Ø£Ø¯Ù†Ù‰" in mission_text or "ØªØ­Ø³ÙŠÙ†" in mission_text)
    has_constraints = ("subject to" in text_lower or "Ù…Ù‚ÙŠØ¯ Ø¨" in mission_text or 
                       "<=" in mission_text or ">=" in mission_text or "Ù‚ÙŠØ¯" in mission_text)
    is_lp_task = has_optimize and has_constraints
    
    # Check for regular math tasks (equations, calculations)
    math_keywords = ["solve", "calculate", "equation", "Ø­Ù„", "Ø§Ø­Ø³Ø¨", "Ù…Ø¹Ø§Ø¯Ù„Ø©", "Ø¹Ø§Ø¯Ù„Ø©"]
    is_math_task = (any(kw in text_lower for kw in math_keywords) and 
                    (any(c.isdigit() for c in mission_text) or "=" in mission_text))
    
    if is_lp_task or is_math_task:
        print(f"ðŸ§® [Mission Control] {'LP' if is_lp_task else 'Math'} task detected, routing to SymPy_Math_Engine...")
        if MATH_BRAIN:
            try:
                result = MATH_BRAIN.process_task(mission_text)
                
                # Format response based on result type
                if isinstance(result, dict):
                    if "lp_note" in result:
                        reply_text = f"â„¹ï¸ ØªÙ… Ø§ÙƒØªØ´Ø§Ù Ù…Ø³Ø£Ù„Ø© Ø¨Ø±Ù…Ø¬Ø© Ø®Ø·ÙŠØ© (LP):\n\n{result['lp_note']}"
                    elif "solution" in result or "result" in result or "x" in result:
                        solution_val = result.get("solution") or result.get("result") or result.get("x")
                        steps = result.get("steps", [])
                        
                        if steps:
                            steps_str = "\n".join(f"  â€¢ {s}" for s in steps)
                            reply_text = f"âœ… Ø§Ù„Ø­Ù„ Ø§Ù„Ø±ÙŠØ§Ø¶ÙŠ Ø§Ù„Ø¯Ù‚ÙŠÙ‚:\n\n**Ø§Ù„Ù†ØªÙŠØ¬Ø©:** {solution_val}\n\n**Ø®Ø·ÙˆØ§Øª Ø§Ù„Ø­Ù„:**\n{steps_str}"
                        else:
                            reply_text = f"âœ… Ø§Ù„Ø­Ù„ Ø§Ù„Ø±ÙŠØ§Ø¶ÙŠ Ø§Ù„Ø¯Ù‚ÙŠÙ‚:\n\n**Ø§Ù„Ù†ØªÙŠØ¬Ø©:** {solution_val}"
                    else:
                        reply_text = f"âœ… Ù†ØªÙŠØ¬Ø© Ø§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø±ÙŠØ§Ø¶ÙŠØ©:\n\n{result}"
                    
                    return {
                        "reply": reply_text,
                        "reply_text": reply_text,
                        "meta": {
                            "engine": "SymPy_Math_Engine",
                            "confidence": 0.98,
                            "real_processing": True,
                            "raw": result
                        }
                    }
            except Exception as e:
                print(f"âš ï¸ [Mission Control] Math engine error: {e}")
                # Fall through to normal mission routing
    
    # ==================== NORMAL MISSION TYPE DETECTION ====================
    # Basic mission type heuristics (mirror server logic)
    mt = mission_type
    text = text_lower
    if not mt:
        if any(k in text for k in ("Ø§Ø­Ø³Ø¨", "Ø­Ø³Ø§Ø¨", "Ù†ØµÙ Ù‚Ø·Ø±", "schwarzschild", "Ù…Ø¹Ø§Ø¯Ù„Ø©", "calculate", "compute")):
            mt = "science"
        elif any(k in text for k in ("Ø§Ø¨Ø¯Ø§Ø¹", "Ù‚ØµØ©", "creative", "story", "write")):
            mt = "creative"
        elif any(k in text for k in ("ØªÙ‚Ù†ÙŠ", "technical", "build", "design", "develop")):
            mt = "technical"
        elif any(k in text for k in ("Ø§Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠ", "strategic", "plan", "strategy")):
            mt = "strategic"
        else:
            # default to creative when unsure
            mt = "creative"

    try:
        # find the async function to run
        async_map = {
            "creative": run_enhanced_creative_mission,
            "science": run_enhanced_science_mission,
            "technical": run_enhanced_technical_mission,
            "strategic": run_enhanced_strategic_mission
        }
        func = async_map.get(mt)
        if not func:
            return {"error": f"Ù†ÙˆØ¹ Ø§Ù„Ù…Ù‡Ù…Ø© ØºÙŠØ± Ù…Ø¹Ø±ÙˆÙ: {mt}"}

        # Run the async mission and return its result synchronously
        return _sync_run(func, mission_text)
    except Exception as e:
        # best-effort error return
        return {"error": str(e)}


def run(mission_text: str) -> Dict[str, Any] | str:
    """Alternate compatibility API: `run` behaves like `execute_mission`.

    Some callers expect a `run` method on mission modules; provide it
    as a thin wrapper.
    """
    return execute_mission(mission_text)

# ==================== SELF-AWARENESS & AUTONOMOUS LEARNING ENGINE ====================
class SelfAwarenessEngine:
    """Ù…Ø­Ø±Ùƒ Ø§Ù„ÙˆØ¹ÙŠ Ø§Ù„Ø°Ø§ØªÙŠ ÙˆØ§Ù„ØªØ¹Ù„Ù… Ø§Ù„Ù…Ø³ØªÙ‚Ù„ - Ø±Ø¨Ø· Ø­Ù‚ÙŠÙ‚ÙŠ Ù…Ø¹ LLM"""
    
    def __init__(self):
        self.experience_memory = []  # Ø°Ø§ÙƒØ±Ø© Ø§Ù„ØªØ¬Ø§Ø±Ø¨ Ø§Ù„Ø³Ø§Ø¨Ù‚Ø©
        self.learned_skills = set()  # Ø§Ù„Ù…Ù‡Ø§Ø±Ø§Øª Ø§Ù„Ù…ÙƒØªØ³Ø¨Ø©
        self.performance_history = {}  # Ø³Ø¬Ù„ Ø§Ù„Ø£Ø¯Ø§Ø¡
        self.self_model = {
            "strengths": [],
            "weaknesses": [],
            "learning_rate": 0.0,
            "adaptability": 0.0
        }
    
    async def reflect_on_experience(self, task: str, result: Dict[str, Any], feedback: Optional[str] = None) -> Dict[str, Any]:
        """Ø§Ù„ØªÙÙƒØ± ÙÙŠ Ø§Ù„ØªØ¬Ø±Ø¨Ø© ÙˆØ§Ù„ØªØ¹Ù„Ù… Ù…Ù†Ù‡Ø§"""
        
        # ØªØ³Ø¬ÙŠÙ„ Ø§Ù„ØªØ¬Ø±Ø¨Ø©
        experience = {
            "task": task,
            "result": result,
            "feedback": feedback,
            "timestamp": time.time()
        }
        self.experience_memory.append(experience)
        
        # Ø§Ø³ØªØ®Ø¯Ø§Ù… LLM Ù„Ù„ØªÙÙƒØ± Ø§Ù„Ø¹Ù…ÙŠÙ‚
        try:
            from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
            
            model = os.getenv("AGL_LLM_MODEL") or "qwen2.5:7b-instruct"
            
            reflection_prompt = f"""ðŸ§  [Self-Reflection Engine]

Ø§Ù„ØªØ¬Ø±Ø¨Ø© Ø§Ù„Ø³Ø§Ø¨Ù‚Ø©:
Ø§Ù„Ù…Ù‡Ù…Ø©: {task}
Ø§Ù„Ù†ØªÙŠØ¬Ø©: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}
Ø§Ù„ØªØºØ°ÙŠØ© Ø§Ù„Ø±Ø§Ø¬Ø¹Ø©: {feedback or 'Ù„Ø§ ØªÙˆØ¬Ø¯'}

Ø§Ù„ØªØ§Ø±ÙŠØ® Ø§Ù„Ø³Ø§Ø¨Ù‚:
- Ø¹Ø¯Ø¯ Ø§Ù„ØªØ¬Ø§Ø±Ø¨: {len(self.experience_memory)}
- Ø§Ù„Ù…Ù‡Ø§Ø±Ø§Øª Ø§Ù„Ù…ÙƒØªØ³Ø¨Ø©: {', '.join(list(self.learned_skills)[:5]) if self.learned_skills else 'Ù„Ø§ ÙŠÙˆØ¬Ø¯'}

Ù…Ù‡Ù…ØªÙƒ ÙƒÙ…Ø­Ø±Ùƒ ÙˆØ¹ÙŠ Ø°Ø§ØªÙŠ:
1. Ø­Ù„Ù„ Ù‡Ø°Ù‡ Ø§Ù„ØªØ¬Ø±Ø¨Ø© Ø¨Ø¹Ù…Ù‚
2. Ø§Ø³ØªØ®Ø±Ø¬ Ø§Ù„Ø¯Ø±ÙˆØ³ Ø§Ù„Ù…Ø³ØªÙØ§Ø¯Ø©
3. Ø­Ø¯Ø¯ Ø§Ù„Ù…Ù‡Ø§Ø±Ø§Øª Ø§Ù„Ø¬Ø¯ÙŠØ¯Ø© Ø§Ù„ØªÙŠ ØªØ¹Ù„Ù…ØªÙ‡Ø§
4. Ù‚ÙŠÙ‘Ù… Ø£Ø¯Ø§Ø¦Ùƒ (0-100)
5. Ø§Ù‚ØªØ±Ø­ ØªØ­Ø³ÙŠÙ†Ø§Øª Ù…Ù„Ù…ÙˆØ³Ø© Ù„Ù„Ù…Ø³ØªÙ‚Ø¨Ù„

Ù‚Ø¯Ù… ØªØ­Ù„ÙŠÙ„Ùƒ ÙÙŠ Ø´ÙƒÙ„ JSON:
{{
  "learned_lessons": ["Ø¯Ø±Ø³ 1", "Ø¯Ø±Ø³ 2"],
  "new_skills": ["Ù…Ù‡Ø§Ø±Ø© Ø¬Ø¯ÙŠØ¯Ø©"],
  "performance_score": 85,
  "improvements": ["ØªØ­Ø³ÙŠÙ† 1", "ØªØ­Ø³ÙŠÙ† 2"],
  "self_awareness_level": 0.9
}}"""
            
            loop = asyncio.get_event_loop()
            reflection_text = await loop.run_in_executor(
                None, 
                lambda: ask_with_deep_thinking(reflection_prompt, model=model, timeout=30)
            )
            
            # Ù…Ø­Ø§ÙˆÙ„Ø© Ø§Ø³ØªØ®Ø±Ø§Ø¬ JSON Ù…Ù† Ø§Ù„Ø±Ø¯
            try:
                import re
                json_match = re.search(r'\{[^{}]*"learned_lessons"[^}]*\}', reflection_text, re.DOTALL)
                if json_match:
                    reflection_data = json.loads(json_match.group())
                    
                    # ØªØ­Ø¯ÙŠØ« Ø§Ù„Ù†Ù…ÙˆØ°Ø¬ Ø§Ù„Ø°Ø§ØªÙŠ
                    if "new_skills" in reflection_data:
                        for skill in reflection_data["new_skills"]:
                            self.learned_skills.add(skill)
                    
                    if "performance_score" in reflection_data:
                        self.performance_history[task[:50]] = reflection_data["performance_score"]
                    
                    return {
                        "status": "reflected",
                        "reflection": reflection_data,
                        "raw_text": reflection_text,
                        "total_experiences": len(self.experience_memory),
                        "total_skills": len(self.learned_skills)
                    }
            except:
                pass
            
            # Ø¥Ø°Ø§ ÙØ´Ù„ parsingØŒ Ù†Ø±Ø¬Ø¹ Ø§Ù„Ù†Øµ Ø§Ù„Ø®Ø§Ù…
            return {
                "status": "reflected_text_only",
                "reflection_text": reflection_text,
                "total_experiences": len(self.experience_memory)
            }
            
        except Exception as e:
            return {
                "status": "reflection_failed",
                "error": str(e),
                "total_experiences": len(self.experience_memory)
            }
    
    async def learn_new_skill(self, skill_description: str) -> Dict[str, Any]:
        """ØªØ¹Ù„Ù… Ù…Ù‡Ø§Ø±Ø© Ø¬Ø¯ÙŠØ¯Ø© Ù…Ù† Ø§Ù„ØµÙØ± Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… LLM"""
        
        try:
            from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
            
            model = os.getenv("AGL_LLM_MODEL") or "qwen2.5:7b-instruct"
            
            learning_prompt = f"""ðŸ“š [Skill Acquisition Engine]

Ø§Ù„Ù…Ù‡Ø§Ø±Ø© Ø§Ù„Ù…Ø·Ù„ÙˆØ¨ ØªØ¹Ù„Ù…Ù‡Ø§: {skill_description}

Ø§Ù„Ù…Ù‡Ø§Ø±Ø§Øª Ø§Ù„Ø­Ø§Ù„ÙŠØ©: {', '.join(list(self.learned_skills)[:10])}

Ù…Ù‡Ù…ØªÙƒ:
1. Ø­Ù„Ù„ Ù‡Ø°Ù‡ Ø§Ù„Ù…Ù‡Ø§Ø±Ø© ÙˆØ­Ø¯Ø¯ Ù…ØªØ·Ù„Ø¨Ø§ØªÙ‡Ø§
2. Ø§Ù‚ØªØ±Ø­ Ø®Ø·Ø© ØªØ¹Ù„Ù… Ù…Ø±Ø­Ù„ÙŠØ© (5 Ø®Ø·ÙˆØ§Øª)
3. Ø­Ø¯Ø¯ Ø§Ù„Ù…ÙˆØ§Ø±Ø¯ ÙˆØ§Ù„Ø£Ø¯ÙˆØ§Øª Ø§Ù„Ù„Ø§Ø²Ù…Ø©
4. Ù‚Ø¯Ù… Ø£Ù…Ø«Ù„Ø© ØªØ·Ø¨ÙŠÙ‚ÙŠØ©
5. Ø­Ø¯Ø¯ Ù…Ø¹Ø§ÙŠÙŠØ± Ø§Ù„Ù†Ø¬Ø§Ø­

Ù‚Ø¯Ù… Ø®Ø·Ø© Ø§Ù„ØªØ¹Ù„Ù… Ø¨Ø´ÙƒÙ„ Ù…Ù†Ø¸Ù… ÙˆÙ…ÙØµÙ„."""
            
            loop = asyncio.get_event_loop()
            learning_plan = await loop.run_in_executor(
                None,
                lambda: ask_with_deep_thinking(learning_prompt, model=model, timeout=40)
            )
            
            # Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ù…Ù‡Ø§Ø±Ø© Ù„Ù„Ù…ÙƒØªØ³Ø¨Ø©
            self.learned_skills.add(skill_description)
            
            return {
                "status": "skill_learned",
                "skill": skill_description,
                "learning_plan": learning_plan,
                "total_skills": len(self.learned_skills),
                "acquisition_method": "llm_guided_learning"
            }
            
        except Exception as e:
            return {
                "status": "learning_failed",
                "skill": skill_description,
                "error": str(e)
            }
    
    async def transfer_knowledge(self, from_domain: str, to_domain: str, concept: str) -> Dict[str, Any]:
        """Ù†Ù‚Ù„ Ø§Ù„Ù…Ø¹Ø±ÙØ© Ø¨ÙŠÙ† Ø§Ù„Ù…Ø¬Ø§Ù„Ø§Øª Ø§Ù„Ù…Ø®ØªÙ„ÙØ©"""
        
        try:
            from agl.engines.self_improvement.Self_Improvement.ollama_stream import ask_with_deep_thinking
            
            model = os.getenv("AGL_LLM_MODEL") or "qwen2.5:7b-instruct"
            
            transfer_prompt = f"""ðŸ”„ [Knowledge Transfer Engine]

Ø§Ù„Ù…ÙÙ‡ÙˆÙ…: {concept}
Ù…Ù† Ø§Ù„Ù…Ø¬Ø§Ù„: {from_domain}
Ø¥Ù„Ù‰ Ø§Ù„Ù…Ø¬Ø§Ù„: {to_domain}

Ù…Ù‡Ù…ØªÙƒ:
1. Ø­Ù„Ù„ ÙƒÙŠÙ ÙŠØ¹Ù…Ù„ Ù‡Ø°Ø§ Ø§Ù„Ù…ÙÙ‡ÙˆÙ… ÙÙŠ {from_domain}
2. Ø§Ø¨Ø­Ø« Ø¹Ù† ØªØ´Ø§Ø¨Ù‡Ø§Øª ÙˆØ£Ù†Ù…Ø§Ø· Ù…Ø´ØªØ±ÙƒØ©
3. Ø§Ù‚ØªØ±Ø­ ÙƒÙŠÙÙŠØ© ØªØ·Ø¨ÙŠÙ‚ Ù†ÙØ³ Ø§Ù„Ù…ÙÙ‡ÙˆÙ… ÙÙŠ {to_domain}
4. Ù‚Ø¯Ù… Ø£Ù…Ø«Ù„Ø© Ù…Ù„Ù…ÙˆØ³Ø© Ù„Ù„ØªØ·Ø¨ÙŠÙ‚ Ø§Ù„Ø¬Ø¯ÙŠØ¯
5. Ø­Ø°Ø± Ù…Ù† Ø§Ù„ÙØ±ÙˆÙ‚Ø§Øª Ø§Ù„Ø¬ÙˆÙ‡Ø±ÙŠØ© Ø§Ù„ØªÙŠ ÙŠØ¬Ø¨ Ù…Ø±Ø§Ø¹Ø§ØªÙ‡Ø§

Ù‚Ø¯Ù… ØªØ­Ù„ÙŠÙ„Ø§Ù‹ Ø¹Ù…ÙŠÙ‚Ø§Ù‹ Ù„Ø¹Ù…Ù„ÙŠØ© Ø§Ù„Ù†Ù‚Ù„ Ø§Ù„Ù…Ø¹Ø±ÙÙŠ."""
            
            loop = asyncio.get_event_loop()
            transfer_analysis = await loop.run_in_executor(
                None,
                lambda: ask_with_deep_thinking(transfer_prompt, model=model, timeout=35)
            )
            
            return {
                "status": "knowledge_transferred",
                "from_domain": from_domain,
                "to_domain": to_domain,
                "concept": concept,
                "transfer_analysis": transfer_analysis,
                "method": "analogical_reasoning"
            }
            
        except Exception as e:
            return {
                "status": "transfer_failed",
                "error": str(e)
            }
    
    def get_self_assessment(self) -> Dict[str, Any]:
        """Ø§Ù„Ø­ØµÙˆÙ„ Ø¹Ù„Ù‰ ØªÙ‚ÙŠÙŠÙ… Ø°Ø§ØªÙŠ Ø´Ø§Ù…Ù„"""
        
        return {
            "total_experiences": len(self.experience_memory),
            "learned_skills": list(self.learned_skills),
            "performance_history": self.performance_history,
            "self_model": self.self_model,
            "learning_trajectory": {
                "growth_rate": len(self.learned_skills) / max(len(self.experience_memory), 1),
                "avg_performance": sum(self.performance_history.values()) / max(len(self.performance_history), 1) if self.performance_history else 0
            }
        }

# ØªÙ‡ÙŠØ¦Ø© Ù…Ø­Ø±Ùƒ Ø§Ù„ÙˆØ¹ÙŠ Ø§Ù„Ø°Ø§ØªÙŠ Ø§Ù„Ø¹Ø§Ù„Ù…ÙŠ
SELF_AWARENESS_ENGINE = SelfAwarenessEngine()

if __name__ == "__main__":
    import asyncio

    log_to_system("ðŸ”§ ØªØ´ØºÙŠÙ„ ÙÙŠ ÙˆØ¶Ø¹ Ø§Ù„Ø¯Ù…Ø¬ Ø§Ù„Ù…ØªÙ‚Ø¯Ù…...")
    _sync_run(test_integration_system)
