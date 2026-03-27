# ═══════════════════════════════════════════════════════════════════════════════
# [AGL] استيرادات آمنة - كل محرك يُحمّل بشكل مستقل لمنع سلسلة الفشل
# Safe imports - each engine loads independently to prevent cascade failures
# ═══════════════════════════════════════════════════════════════════════════════

QuantumNeuralCore = None
HeikalHybridLogicCore = None
VectorizedWaveProcessor = None
AdvancedMetaReasonerEngine = None
MissionControl = None
execute_mission = None

try:
    from .quantum_neural import QuantumNeuralCore
except ImportError:
    pass

try:
    from .heikal_hybrid_logic import HeikalHybridLogicCore
except ImportError:
    pass

try:
    from .vectorized_wave_processor import VectorizedWaveProcessor
except ImportError:
    pass

try:
    from .advanced_meta_reasoner import AdvancedMetaReasonerEngine
except ImportError:
    pass

try:
    from .mission_control import EnhancedMissionController as MissionControl
    from .mission_control import execute_mission
except ImportError:
    pass
