"""
AGL Attack Engine — Layer 3: Economic Physics Engine
محرك الفيزياء الاقتصادية — الطبقة الثالثة

═══════════════════════════════════════════════════════════════
الغرض: حساب دالة واحدة فقط:

    Profit(attacker) = Value(final) - Value(initial) - Gas - Fees

المكونات:
    1. ProtocolStateLoader  — نموذج الحالة الشاملة للبروتوكول
    2. ActionExecutor       — محرك التنفيذ الدلالي
    3. StateMutator         — محرك تحويل الحالة + Rollback
    4. EconomicEngine       — محرك الأحداث الاقتصادية
    5. ProfitCalculator     — حاسب الأرباح (القلب)
    6. AttackSimulationEngine — المنسق الرئيسي

Pipeline:
    Load State → Convert Actions → Execute Sequence → Compute Profit → Return
═══════════════════════════════════════════════════════════════
"""

__version__ = "1.0.0"

# === Models ===
from .models import (
    TokenSymbol,
    RevertReason,
    SimulationMode,
    AccountState,
    TokenState,
    PoolState,
    LendingState,
    OracleState,
    ProtocolState,
    BalanceChange,
    StorageChange,
    StateDelta,
    ExecutableAction,
    StepResult,
    AttackResult,
    SimulationConfig,
    SimulationSummary,
)

# === Components ===
from .protocol_state import ProtocolStateLoader, ATTACKER_ADDRESS
from .state_mutator import StateMutator, StateStack
from .action_executor import ActionExecutor
from .economic_engine import EconomicEngine
from .profit_calculator import ProfitCalculator

# === Main Engine ===
from .engine import AttackSimulationEngine

__all__ = [
    # Version
    "__version__",
    # Models
    "TokenSymbol",
    "RevertReason",
    "SimulationMode",
    "AccountState",
    "TokenState",
    "PoolState",
    "LendingState",
    "OracleState",
    "ProtocolState",
    "BalanceChange",
    "StorageChange",
    "StateDelta",
    "ExecutableAction",
    "StepResult",
    "AttackResult",
    "SimulationConfig",
    "SimulationSummary",
    # Components
    "ProtocolStateLoader",
    "ATTACKER_ADDRESS",
    "StateMutator",
    "StateStack",
    "ActionExecutor",
    "EconomicEngine",
    "ProfitCalculator",
    # Engine
    "AttackSimulationEngine",
]
