"""
AGL Search Engine — Data Models (Layer 4)
نماذج البيانات لمحرك البحث الذكي

═══════════════════════════════════════════════════════════════
Layer 4 يبحث في فضاء Layer 2 باستخدام ذكاء Layer 3.

المشكلة:
    (20 actions × 10 variants)^5 ≈ 3.2×10¹³ تسلسل ممكن
    → مستحيل تجربها كلها

الحل:
    Search(ActionSpace) → profitable sequences
    باستخدام: Heuristics + Economic Weakness + Guided Search + Profit Gradient

═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import time
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
#  Enums
# ═══════════════════════════════════════════════════════════════

class WeaknessType(Enum):
    """أنواع نقاط الضعف الاقتصادية"""
    REENTRANCY_DRAIN = "reentrancy_drain"
    PRICE_IMBALANCE = "price_imbalance"
    INVARIANT_BREAK = "invariant_break"
    UNDER_COLLATERALIZATION = "under_collateralization"
    LIQUIDITY_ASYMMETRY = "liquidity_asymmetry"
    REWARD_MISPRICING = "reward_mispricing"
    ACCESS_LEAK = "access_leak"
    ORACLE_STALENESS = "oracle_staleness"
    ORACLE_MANIPULATION = "oracle_manipulation"
    FLASH_LOAN_VECTOR = "flash_loan_vector"
    CROSS_FUNCTION_STATE = "cross_function_state"
    DONATION_ATTACK = "donation_attack"
    FIRST_DEPOSITOR = "first_depositor"
    ROUNDING_ERROR = "rounding_error"


class SearchStrategy(Enum):
    """استراتيجيات البحث"""
    BEAM_SEARCH = "beam_search"
    MCTS = "mcts"                      # Monte Carlo Tree Search
    GREEDY_BEST_FIRST = "greedy_best_first"
    EVOLUTIONARY = "evolutionary"
    GRADIENT_ASCENT = "gradient_ascent"
    HYBRID = "hybrid"                  # كل الاستراتيجيات معاً


class SeedSource(Enum):
    """مصدر بذرة البحث"""
    HEURISTIC = "heuristic"            # من المحلل الأولي
    WEAKNESS = "weakness"              # من كاشف الضعف الاقتصادي
    LAYER2_PATH = "layer2_path"        # من مسارات Layer 2
    LAYER3_NEAR_MISS = "near_miss"     # تسلسل من Layer 3 كان قريباً من الربح
    MUTATION = "mutation"              # طفرة من تسلسل موجود
    GRADIENT = "gradient"              # من محرك التدرج


class NodeState(Enum):
    """حالة عقدة في شجرة البحث"""
    UNEXPLORED = "unexplored"
    EXPANDING = "expanding"
    EVALUATED = "evaluated"
    PROFITABLE = "profitable"
    PRUNED = "pruned"
    DEAD = "dead"                      # revert أو مستحيل


# ═══════════════════════════════════════════════════════════════
#  Search Configuration
# ═══════════════════════════════════════════════════════════════

@dataclass
class SearchConfig:
    """إعدادات محرك البحث"""

    # === Budget ===
    max_sequences_to_test: int = 500           # حد أقصى للتسلسلات
    max_search_time_seconds: float = 60.0      # حد زمني
    max_depth: int = 6                         # أقصى عمق تسلسل

    # === Beam Search ===
    beam_width: int = 10                       # عرض الشعاع
    beam_depth: int = 5                        # عمق الشعاع

    # === MCTS ===
    mcts_iterations: int = 200                 # عدد تكرارات MCTS
    mcts_exploration_weight: float = 1.414     # √2 — UCB1 constant
    mcts_rollout_depth: int = 4                # عمق rollout

    # === Evolutionary ===
    population_size: int = 30                  # حجم التجمع
    generations: int = 20                      # عدد الأجيال
    mutation_rate: float = 0.3                 # معدل الطفرة
    crossover_rate: float = 0.5                # معدل التهجين
    elite_count: int = 5                       # المتفوقون المحتفظ بهم

    # === Gradient ===
    gradient_steps: int = 20                   # خطوات التدرج
    amount_step_pct: float = 0.1               # 10% تغيير لكل خطوة
    min_improvement_usd: float = 10.0          # أقل تحسن لاستمرار التدرج

    # === Pruning ===
    min_profit_threshold_usd: float = -500.0   # اقطع إذا الخسارة > $500
    prune_reverted_branches: bool = True       # اقطع فرع إذا أي خطوة فشلت
    max_gas_budget_usd: float = 1000.0         # ميزانية غاز

    # === Strategy ===
    strategy: SearchStrategy = SearchStrategy.HYBRID
    enable_gradient_optimization: bool = True
    enable_weakness_seeding: bool = True
    enable_near_miss_mutation: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_sequences_to_test": self.max_sequences_to_test,
            "max_search_time_seconds": self.max_search_time_seconds,
            "max_depth": self.max_depth,
            "beam_width": self.beam_width,
            "mcts_iterations": self.mcts_iterations,
            "population_size": self.population_size,
            "generations": self.generations,
            "gradient_steps": self.gradient_steps,
            "strategy": self.strategy.value,
        }


# ═══════════════════════════════════════════════════════════════
#  Heuristic Target — هدف عالي القيمة
# ═══════════════════════════════════════════════════════════════

@dataclass
class HeuristicTarget:
    """
    هدف يستحق الدراسة — تم تحديده بالتحليل الأولي.

    كل هدف هو نقطة بداية محتملة للبحث:
    - function_name + contract_name → أين نبدأ
    - score → أولوية (0.0–1.0)
    - reasons → لماذا هذا الهدف مهم
    - related_actions → أفعال مرتبطة من Layer 2
    """
    target_id: str                              # contract.function
    contract_name: str = ""
    function_name: str = ""
    action_ids: List[str] = field(default_factory=list)  # من Layer 2

    # === Scoring ===
    score: float = 0.0                          # 0.0–1.0
    reasons: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)  # "fund_mover", "cei", "oracle", ...

    # === Metadata ===
    has_cei_violation: bool = False
    sends_eth: bool = False
    reentrancy_guarded: bool = False
    requires_access: bool = False
    moves_funds: bool = False
    reads_oracle: bool = False
    estimated_value_at_risk: float = 0.0        # $ تقدير

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "contract_name": self.contract_name,
            "function_name": self.function_name,
            "action_ids": self.action_ids,
            "score": round(self.score, 4),
            "reasons": self.reasons,
            "tags": list(self.tags),
            "has_cei_violation": self.has_cei_violation,
            "sends_eth": self.sends_eth,
            "estimated_value_at_risk": round(self.estimated_value_at_risk, 2),
        }


# ═══════════════════════════════════════════════════════════════
#  Economic Weakness — ضعف اقتصادي
# ═══════════════════════════════════════════════════════════════

@dataclass
class EconomicWeakness:
    """
    نقطة ضعف اقتصادية مكتشفة.

    كل weakness → بذرة بحث واحدة أو أكثر:
    - weakness_type → نوع الضعف
    - exploit_hint → كيف يُستغل
    - entry_actions → أفعال الدخول (من Layer 2)
    - exit_actions → أفعال الخروج
    - estimated_profit → تقدير أولي للربح

    الكاشف لا يُنفذ — فقط يُحدد أين يبحث المحرك.
    """
    weakness_id: str
    weakness_type: WeaknessType
    severity: str = "medium"                    # critical/high/medium/low
    confidence: float = 0.5                     # 0.0–1.0

    # === الاستغلال ===
    exploit_hint: str = ""                      # وصف مختصر
    exploit_hint_ar: str = ""                   # بالعربية
    entry_actions: List[str] = field(default_factory=list)   # action_ids
    exit_actions: List[str] = field(default_factory=list)
    auxiliary_actions: List[str] = field(default_factory=list)

    # === التقدير الاقتصادي ===
    estimated_profit_usd: float = 0.0
    affected_variable: str = ""                 # المتغير المتأثر
    affected_contract: str = ""
    invariant_expression: str = ""              # التعبير الذي يُخرق

    # === السياق ===
    related_targets: List[str] = field(default_factory=list)  # target_ids
    requires_flash_loan: bool = False
    requires_multiple_blocks: bool = False
    requires_price_manipulation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weakness_id": self.weakness_id,
            "weakness_type": self.weakness_type.value,
            "severity": self.severity,
            "confidence": round(self.confidence, 3),
            "exploit_hint": self.exploit_hint,
            "exploit_hint_ar": self.exploit_hint_ar,
            "entry_actions": self.entry_actions,
            "exit_actions": self.exit_actions,
            "estimated_profit_usd": round(self.estimated_profit_usd, 2),
            "affected_contract": self.affected_contract,
            "invariant_expression": self.invariant_expression,
            "requires_flash_loan": self.requires_flash_loan,
        }

    def generate_seed_sequences(self) -> List['SearchSeed']:
        """توليد بذور بحث من هذا الضعف"""
        seeds = []

        # Seed 1: entry → exit مباشر
        if self.entry_actions and self.exit_actions:
            for entry in self.entry_actions:
                for exit_a in self.exit_actions:
                    seeds.append(SearchSeed(
                        seed_id=f"{self.weakness_id}_{entry}_{exit_a}",
                        source=SeedSource.WEAKNESS,
                        action_sequence=[entry, exit_a],
                        weakness_ref=self.weakness_id,
                        estimated_profit=self.estimated_profit_usd,
                        priority=self.confidence,
                    ))

        # Seed 2: entry → aux → exit (مع خطوة وسيطة)
        if self.entry_actions and self.exit_actions and self.auxiliary_actions:
            for entry in self.entry_actions[:2]:
                for aux in self.auxiliary_actions[:2]:
                    for exit_a in self.exit_actions[:2]:
                        seeds.append(SearchSeed(
                            seed_id=f"{self.weakness_id}_{entry}_{aux}_{exit_a}",
                            source=SeedSource.WEAKNESS,
                            action_sequence=[entry, aux, exit_a],
                            weakness_ref=self.weakness_id,
                            estimated_profit=self.estimated_profit_usd * 0.8,
                            priority=self.confidence * 0.9,
                        ))

        return seeds


# ═══════════════════════════════════════════════════════════════
#  Search Seed — بذرة بحث
# ═══════════════════════════════════════════════════════════════

@dataclass
class SearchSeed:
    """
    بذرة بحث — نقطة بداية للبحث الموجه.

    كل بذرة = تسلسل مبدئي (action_ids) مع تقدير أولي.
    المحرك يتوسع من البذور.
    """
    seed_id: str
    source: SeedSource
    action_sequence: List[str] = field(default_factory=list)  # action_ids
    weakness_ref: str = ""                      # reference to EconomicWeakness
    estimated_profit: float = 0.0
    priority: float = 0.5                       # 0.0–1.0

    # === Context ===
    parameter_hints: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed_id": self.seed_id,
            "source": self.source.value,
            "action_sequence": self.action_sequence,
            "weakness_ref": self.weakness_ref,
            "estimated_profit": round(self.estimated_profit, 2),
            "priority": round(self.priority, 3),
        }


# ═══════════════════════════════════════════════════════════════
#  Search Node — عقدة في شجرة البحث
# ═══════════════════════════════════════════════════════════════

@dataclass
class SearchNode:
    """
    عقدة في شجرة البحث (MCTS/Beam).

    كل عقدة = حالة وسيطة في تسلسل الهجوم:
    - sequence_so_far → ما نُفذ حتى الآن
    - profit_so_far → الربح المتراكم
    - state_hash → بصمة الحالة الحالية
    """
    node_id: str
    parent_id: Optional[str] = None
    depth: int = 0
    state: NodeState = NodeState.UNEXPLORED

    # === Sequence ===
    sequence_so_far: List[str] = field(default_factory=list)  # action_ids
    last_action: str = ""

    # === Scores ===
    profit_so_far_usd: float = 0.0             # ربح متراكم
    heuristic_score: float = 0.0                # تقييم إرشادي
    ucb_score: float = 0.0                      # UCB1 score لـ MCTS

    # === MCTS stats ===
    visits: int = 0
    total_reward: float = 0.0
    children: List[str] = field(default_factory=list)  # node_ids

    # === Pruning ===
    is_terminal: bool = False
    pruned_reason: str = ""
    gas_used_so_far: int = 0

    @property
    def average_reward(self) -> float:
        return self.total_reward / max(self.visits, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "depth": self.depth,
            "state": self.state.value,
            "sequence": self.sequence_so_far,
            "profit_so_far": round(self.profit_so_far_usd, 2),
            "visits": self.visits,
            "average_reward": round(self.average_reward, 4),
            "children_count": len(self.children),
            "is_terminal": self.is_terminal,
        }


# ═══════════════════════════════════════════════════════════════
#  Candidate Sequence — تسلسل مرشح
# ═══════════════════════════════════════════════════════════════

@dataclass
class CandidateSequence:
    """
    تسلسل هجوم مرشح — جاهز للمحاكاة في Layer 3.

    يحتوي:
    - steps → خطوات Step Info (نفس format بين L2 و L3)
    - source → من أين جاء (heuristic, weakness, mcts, mutation)
    - estimated_profit → التقدير قبل المحاكاة
    """
    candidate_id: str
    steps: List[Dict[str, Any]] = field(default_factory=list)  # step_info dicts
    action_ids: List[str] = field(default_factory=list)
    source: SeedSource = SeedSource.HEURISTIC
    weakness_ref: str = ""

    # === Pre-simulation estimate ===
    estimated_profit_usd: float = 0.0
    priority_score: float = 0.0

    # === Post-simulation (filled by engine) ===
    simulated: bool = False
    actual_profit_usd: float = 0.0
    simulation_success: bool = False
    attack_type: str = ""
    severity: str = ""

    # === Optimization ===
    optimized: bool = False
    optimization_iterations: int = 0
    profit_before_optimization: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "action_ids": self.action_ids,
            "source": self.source.value,
            "weakness_ref": self.weakness_ref,
            "estimated_profit_usd": round(self.estimated_profit_usd, 2),
            "simulated": self.simulated,
            "actual_profit_usd": round(self.actual_profit_usd, 2),
            "simulation_success": self.simulation_success,
            "optimized": self.optimized,
            "attack_type": self.attack_type,
            "severity": self.severity,
        }


# ═══════════════════════════════════════════════════════════════
#  Search Statistics — إحصائيات البحث
# ═══════════════════════════════════════════════════════════════

@dataclass
class SearchStats:
    """إحصائيات تفصيلية عن عملية البحث"""
    # === Seeds ===
    total_seeds: int = 0
    seeds_from_heuristic: int = 0
    seeds_from_weakness: int = 0
    seeds_from_layer2: int = 0
    seeds_from_near_miss: int = 0
    seeds_from_mutation: int = 0

    # === Search ===
    nodes_explored: int = 0
    nodes_pruned: int = 0
    sequences_generated: int = 0
    sequences_simulated: int = 0
    sequences_profitable: int = 0

    # === Optimization ===
    gradient_steps_taken: int = 0
    improved_by_gradient: int = 0
    total_improvement_usd: float = 0.0

    # === Performance ===
    search_time_ms: float = 0.0
    simulation_time_ms: float = 0.0
    optimization_time_ms: float = 0.0
    total_time_ms: float = 0.0

    # === Strategy Breakdown ===
    by_strategy: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_seeds": self.total_seeds,
            "seeds_by_source": {
                "heuristic": self.seeds_from_heuristic,
                "weakness": self.seeds_from_weakness,
                "layer2": self.seeds_from_layer2,
                "near_miss": self.seeds_from_near_miss,
                "mutation": self.seeds_from_mutation,
            },
            "nodes_explored": self.nodes_explored,
            "nodes_pruned": self.nodes_pruned,
            "sequences_generated": self.sequences_generated,
            "sequences_simulated": self.sequences_simulated,
            "sequences_profitable": self.sequences_profitable,
            "gradient_steps": self.gradient_steps_taken,
            "improved_by_gradient": self.improved_by_gradient,
            "search_time_ms": round(self.search_time_ms, 2),
            "simulation_time_ms": round(self.simulation_time_ms, 2),
            "optimization_time_ms": round(self.optimization_time_ms, 2),
            "total_time_ms": round(self.total_time_ms, 2),
        }


# ═══════════════════════════════════════════════════════════════
#  Search Result — نتيجة البحث النهائية
# ═══════════════════════════════════════════════════════════════

@dataclass
class SearchResult:
    """
    نتيجة البحث الذكي — المخرج النهائي لـ Layer 4.

    يحتوي:
    - profitable_attacks → كل الهجمات المربحة (مرتبة بالربح)
    - weaknesses_found → نقاط الضعف المكتشفة
    - stats → إحصائيات البحث
    """
    version: str = "1.0.0"

    # === الهجمات المربحة (مرتبة بالربح) ===
    profitable_attacks: List[Dict[str, Any]] = field(default_factory=list)
    total_profitable: int = 0
    total_profit_usd: float = 0.0
    best_profit_usd: float = 0.0

    # === نقاط الضعف ===
    weaknesses: List[EconomicWeakness] = field(default_factory=list)
    targets: List[HeuristicTarget] = field(default_factory=list)

    # === البذور والمرشحات ===
    seeds_generated: int = 0
    candidates_tested: int = 0
    candidates_profitable: int = 0

    # === الإحصائيات ===
    stats: SearchStats = field(default_factory=SearchStats)

    # === أخطاء وتحذيرات ===
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # === Timing ===
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "total_profitable": self.total_profitable,
            "total_profit_usd": round(self.total_profit_usd, 2),
            "best_profit_usd": round(self.best_profit_usd, 2),
            "profitable_attacks": self.profitable_attacks,
            "weaknesses": [w.to_dict() for w in self.weaknesses],
            "targets_count": len(self.targets),
            "seeds_generated": self.seeds_generated,
            "candidates_tested": self.candidates_tested,
            "candidates_profitable": self.candidates_profitable,
            "stats": self.stats.to_dict(),
            "errors": self.errors,
            "warnings": self.warnings,
            "execution_time_ms": round(self.execution_time_ms, 2),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
