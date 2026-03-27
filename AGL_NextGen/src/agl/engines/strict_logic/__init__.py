"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    AGL STRICT LOGIC CORE - النواة المنطقية الصارمة            ║
║══════════════════════════════════════════════════════════════════════════════║
║  المفهوم الجوهري:                                                             ║
║  ─────────────────                                                            ║
║  هذا ليس "ذكاء اصطناعي" - هذا آلة استدلال منطقي + احتمالي + ذاكرة            ║
║  الذكاء سيظهر كنتيجة وليس كهدف.                                               ║
║                                                                               ║
║  المعادلة الأساسية:                                                           ║
║  L(x) = { decision, confidence, trace }                                       ║
║    - decision: ناتج منطقي أو عددي                                            ║
║    - confidence: احتمال محسوب (ليس عشوائي)                                   ║
║    - trace: أثر منطقي (أي البوابات شاركت)                                    ║
║                                                                               ║
║  إذا لم تُنتج trace → النظام أعمى.                                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from .observable import Observable, Signal, StateSpace
from .logic_gates import (
    # Deterministic Gates
    ANDGate, ORGate, XORGate, NOTGate, NANDGate, NORGate, XNORGate,
    # Weighted Gates
    WeightedGate, WeightedAND, WeightedOR,
    # Wave Projection Gates
    WaveProjectionGate, WaveState,
    # Gate Network
    GateNetwork, GateTrace
)
from .memory_registers import (
    AssociativeMemory, MemoryPattern, LogicalBias,
    FlipFlop, Register, ExperienceBuffer
)
from .learning_engine import (
    LogicAdaptiveNetwork, LogicalError, TraceBackPropagation
)
from .core_logic_unit import CoreLogicUnit, DecisionResult
from .entropy_extractor import EntropyExtractor, NoiseSeed

# Engine Bridge - جسر المحركات
from .engine_bridge import (
    EngineBridge, RealTimeLearningSystem,
    EngineAdapter, EngineType, EngineSignal,
    GenesisOmegaAdapter, HermesOmniAdapter, QuantumCoreAdapter,
    create_unified_system
)

# Interactive Learning - التعلم التفاعلي
from .interactive_learning import (
    InteractiveLearningSession, CommandLineLearner, LiveIntegration,
    run_interactive, run_live_system
)

# Full Power Core - النواة الكاملة (10 محركات حقيقية)
try:
    from .full_power_core import (
        FullPowerCore, UnifiedDecision, POWER_REGISTRY
    )
    FULL_POWER_AVAILABLE = True
except ImportError:
    FULL_POWER_AVAILABLE = False

__version__ = "2.0.0"  # Upgraded to Full Power
__author__ = "Hussam Heikal - AGL System"

# Core exports
__all__ = [
    # Observable Layer
    "Observable", "Signal", "StateSpace",
    
    # Logic Gates
    "ANDGate", "ORGate", "XORGate", "NOTGate", "NANDGate", "NORGate", "XNORGate",
    "WeightedGate", "WeightedAND", "WeightedOR",
    "WaveProjectionGate", "WaveState",
    "GateNetwork", "GateTrace",
    
    # Memory
    "AssociativeMemory", "MemoryPattern", "LogicalBias",
    "FlipFlop", "Register", "ExperienceBuffer",
    
    # Learning
    "LogicAdaptiveNetwork", "LogicalError", "TraceBackPropagation",
    
    # Core
    "CoreLogicUnit", "DecisionResult",
    
    # Entropy
    "EntropyExtractor", "NoiseSeed",
    
    # Engine Bridge
    "EngineBridge", "RealTimeLearningSystem",
    "EngineAdapter", "EngineType", "EngineSignal",
    "GenesisOmegaAdapter", "HermesOmniAdapter", "QuantumCoreAdapter",
    "create_unified_system",
    
    # Interactive Learning
    "InteractiveLearningSession", "CommandLineLearner", "LiveIntegration",
    "run_interactive", "run_live_system",
    
    # Full Power Core (NEW!)
    "FullPowerCore", "UnifiedDecision", "POWER_REGISTRY",
    "FULL_POWER_AVAILABLE",
]
