"""
AGL Search Engine — Layer 4: Intelligent Economic Search
محرك البحث الاقتصادي الذكي

═══════════════════════════════════════════════════════════════
Layer 4 يبحث في فضاء Layer 2 باستخدام ذكاء Layer 3.

Layer 1–3 = رادار قوي يكتشف الأهداف
Layer 4   = صاروخ ذكي يصيب الهدف

Components:
    1. HeuristicPrioritizer  — أين نبدأ البحث
    2. EconomicWeaknessDetector — ما نقاط الضعف الاقتصادية
    3. GuidedSearchEngine — البحث الذكي (Beam/MCTS/Evolutionary)
    4. ProfitGradientEngine — تحسين المعاملات

Main class: SearchOrchestrator
    orchestrator = SearchOrchestrator()
    result = orchestrator.search(graph, action_space, attack_engine)

═══════════════════════════════════════════════════════════════
"""

from .models import (
    WeaknessType,
    SearchStrategy,
    SeedSource,
    NodeState,
    SearchConfig,
    HeuristicTarget,
    EconomicWeakness,
    SearchSeed,
    SearchNode,
    CandidateSequence,
    SearchStats,
    SearchResult,
)

from .heuristic_prioritizer import HeuristicPrioritizer
from .weakness_detector import EconomicWeaknessDetector
from .guided_search import GuidedSearchEngine
from .profit_gradient import ProfitGradientEngine
from .engine import SearchOrchestrator

__all__ = [
    # Engine
    "SearchOrchestrator",

    # Components
    "HeuristicPrioritizer",
    "EconomicWeaknessDetector",
    "GuidedSearchEngine",
    "ProfitGradientEngine",

    # Models
    "WeaknessType",
    "SearchStrategy",
    "SeedSource",
    "NodeState",
    "SearchConfig",
    "HeuristicTarget",
    "EconomicWeakness",
    "SearchSeed",
    "SearchNode",
    "CandidateSequence",
    "SearchStats",
    "SearchResult",
]

__version__ = "1.0.0"
