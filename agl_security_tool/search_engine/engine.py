"""
AGL Search Engine — Main Orchestrator (Layer 4 Engine)
المُنسق الرئيسي — القائد الذي يربط كل المكونات

═══════════════════════════════════════════════════════════════
Search Orchestrator — Layer 4 Complete Pipeline

Pipeline:
    ┌────────────┐     ┌──────────────┐     ┌───────────────┐
    │ Heuristic  │────▶│  Weakness    │────▶│ Guided Search │
    │ Prioritizer│     │  Detector    │     │ (Beam/MCTS/   │
    │            │     │              │     │  Evolutionary)│
    └────────────┘     └──────────────┘     └───────┬───────┘
         │                    │                      │
         │ targets            │ weaknesses           │ candidates
         ▼                    ▼                      ▼
    ┌─────────────────────────────────────────────────────────┐
    │                    Seed Pool                            │
    │  heuristic seeds + weakness seeds + Layer 2 paths       │
    └────────────────────────────────┬────────────────────────┘
                                     │
                                     ▼
                          ┌──────────────────┐
                          │ Profit Gradient  │
                          │ (optimize params)│
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  SearchResult    │
                          │ (final output)   │
                          └──────────────────┘

Input:  FinancialGraph (L1) + ActionSpace (L2)
Output: SearchResult مع كل الهجمات المربحة مرتبة

═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional

from .models import (
    SearchConfig,
    SearchStrategy,
    SearchResult,
    SearchStats,
    SearchSeed,
    CandidateSequence,
    HeuristicTarget,
    EconomicWeakness,
)
from .heuristic_prioritizer import HeuristicPrioritizer
from .weakness_detector import EconomicWeaknessDetector
from .guided_search import GuidedSearchEngine
from .profit_gradient import ProfitGradientEngine


class SearchOrchestrator:
    """
    المُنسق الرئيسي لـ Layer 4 — Intelligent Economic Search.

    يربط المكونات الأربعة:
        1. HeuristicPrioritizer → أين نبدأ
        2. EconomicWeaknessDetector → ما نقاط الضعف
        3. GuidedSearchEngine → البحث الذكي
        4. ProfitGradientEngine → التحسين

    Usage:
        orchestrator = SearchOrchestrator()
        result = orchestrator.search(graph, action_space, attack_engine)
    """

    VERSION = "1.0.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = self._build_config(config or {})

        self.prioritizer = HeuristicPrioritizer()
        self.weakness_detector = EconomicWeaknessDetector()
        self.search_engine = GuidedSearchEngine(self.config)
        self.gradient_engine = ProfitGradientEngine(
            gradient_steps=self.config.gradient_steps,
            amount_step_pct=self.config.amount_step_pct,
            min_improvement_usd=self.config.min_improvement_usd,
        )

    def _build_config(self, overrides: Dict[str, Any]) -> SearchConfig:
        """بناء SearchConfig من overrides"""
        config = SearchConfig()
        for key, val in overrides.items():
            if hasattr(config, key):
                # Convert string strategy to enum
                if key == "strategy" and isinstance(val, str):
                    try:
                        val = SearchStrategy(val)
                    except (ValueError, KeyError):
                        pass
                setattr(config, key, val)
        return config

    # ═══════════════════════════════════════════════════════
    #  Main Entry
    # ═══════════════════════════════════════════════════════

    def search(
        self,
        graph: Any,
        action_space: Any,
        attack_engine: Any,
    ) -> SearchResult:
        """
        تشغيل البحث الذكي الكامل.

        Args:
            graph: FinancialGraph من Layer 1
            action_space: ActionSpace من Layer 2
            attack_engine: AttackSimulationEngine من Layer 3

        Returns:
            SearchResult مع كل الهجمات المربحة
        """
        t0 = time.time()
        result = SearchResult(version=self.VERSION)
        stats = SearchStats()

        # === Validate inputs ===
        if action_space is None:
            result.errors.append("ActionSpace is None — لا يوجد فضاء أفعال")
            return result

        if attack_engine is None:
            result.errors.append("AttackEngine is None — لا يوجد محرك محاكاة")
            return result

        action_graph = getattr(action_space, 'graph', None)
        if not action_graph:
            result.errors.append("ActionGraph is None — لا يوجد رسم بياني")
            return result

        actions = getattr(action_graph, 'actions', {})
        if not actions:
            result.errors.append("No actions found — لا يوجد أفعال")
            return result

        # === 1. Load initial state ===
        initial_state = self._load_state(graph, attack_engine, result)
        if initial_state is None:
            return result

        # === 2. Heuristic Prioritization ===
        t1 = time.time()
        targets, heuristic_seeds = self._run_prioritizer(
            action_space, graph, result
        )
        result.targets = targets

        # === 3. Weakness Detection ===
        weaknesses, weakness_seeds = self._run_weakness_detector(
            action_space, graph, result
        )
        result.weaknesses = weaknesses

        # === 4. Merge seeds ===
        all_seeds = self._merge_seeds(heuristic_seeds, weakness_seeds)
        result.seeds_generated = len(all_seeds)

        # Count seeds by source
        for s in all_seeds:
            src = s.source.value
            if src == "heuristic":
                stats.seeds_from_heuristic += 1
            elif src == "weakness":
                stats.seeds_from_weakness += 1
            elif src == "layer2_path":
                stats.seeds_from_layer2 += 1
        stats.total_seeds = len(all_seeds)

        if not all_seeds:
            result.warnings.append("No seeds generated — البحث لن يجد شيئاً")
            result.stats = stats
            result.execution_time_ms = (time.time() - t0) * 1000
            return result

        # === 5. Guided Search ===
        t2 = time.time()
        simulate_fn = self._make_simulate_fn(attack_engine)

        candidates = self.search_engine.search(
            seeds=all_seeds,
            action_graph=action_graph,
            actions=actions,
            simulate_fn=simulate_fn,
            initial_state=initial_state,
        )

        # Merge stats from search engine
        se_stats = self.search_engine.stats
        stats.nodes_explored = se_stats.nodes_explored
        stats.nodes_pruned = se_stats.nodes_pruned
        stats.sequences_generated = se_stats.sequences_generated
        stats.sequences_simulated = se_stats.sequences_simulated
        stats.sequences_profitable = se_stats.sequences_profitable
        stats.simulation_time_ms = se_stats.simulation_time_ms
        stats.by_strategy = dict(se_stats.by_strategy)
        stats.search_time_ms = (time.time() - t2) * 1000

        # === 6. Profit Gradient Optimization ===
        t3 = time.time()
        if self.config.enable_gradient_optimization:
            # Optimize only promising candidates (top and near-miss)
            promising = [
                c for c in candidates
                if c.simulated and c.actual_profit_usd > -200
            ][:20]  # limit to avoid timeout

            if promising:
                optimized = self.gradient_engine.optimize(
                    promising, simulate_fn, initial_state, stats
                )

                # Replace originals with optimized
                opt_ids = {c.candidate_id for c in promising}
                non_optimized = [
                    c for c in candidates
                    if c.candidate_id not in opt_ids
                ]
                candidates = optimized + non_optimized
        stats.optimization_time_ms = (time.time() - t3) * 1000

        # === 7. Build result ===
        candidates.sort(key=lambda c: c.actual_profit_usd, reverse=True)
        result.candidates_tested = len(candidates)

        profitable = [c for c in candidates if c.simulated and c.actual_profit_usd > 0]
        result.candidates_profitable = len(profitable)
        result.total_profitable = len(profitable)

        for c in profitable:
            result.profitable_attacks.append(c.to_dict())
            result.total_profit_usd += c.actual_profit_usd

        if profitable:
            result.best_profit_usd = profitable[0].actual_profit_usd

        stats.total_time_ms = (time.time() - t0) * 1000
        result.stats = stats
        result.execution_time_ms = stats.total_time_ms

        return result

    # ═══════════════════════════════════════════════════════
    #  Internal Steps
    # ═══════════════════════════════════════════════════════

    def _load_state(
        self, graph: Any, attack_engine: Any, result: SearchResult
    ) -> Any:
        """Load initial protocol state via Layer 3"""
        try:
            state_loader = getattr(attack_engine, 'state_loader', None)
            if state_loader and hasattr(state_loader, 'load_from_graph'):
                return state_loader.load_from_graph(graph)
            else:
                # Fallback: try direct construction
                from ..attack_engine.protocol_state import ProtocolStateLoader
                loader = ProtocolStateLoader()
                return loader.load_from_graph(graph)
        except Exception as e:
            result.errors.append(f"فشل تحميل الحالة: {str(e)[:200]}")
            return None

    def _run_prioritizer(
        self,
        action_space: Any,
        graph: Any,
        result: SearchResult,
    ) -> tuple:
        """تشغيل HeuristicPrioritizer"""
        try:
            targets, seeds = self.prioritizer.analyze(action_space, graph)
            return targets, seeds
        except Exception as e:
            result.warnings.append(f"Heuristic error: {str(e)[:200]}")
            return [], []

    def _run_weakness_detector(
        self,
        action_space: Any,
        graph: Any,
        result: SearchResult,
    ) -> tuple:
        """تشغيل EconomicWeaknessDetector"""
        try:
            weaknesses, seeds = self.weakness_detector.detect(action_space, graph)
            return weaknesses, seeds
        except Exception as e:
            result.warnings.append(f"WeaknessDetector error: {str(e)[:200]}")
            return [], []

    def _merge_seeds(
        self,
        heuristic_seeds: List[SearchSeed],
        weakness_seeds: List[SearchSeed],
    ) -> List[SearchSeed]:
        """Merge and deduplicate seeds, sorted by priority"""
        all_seeds = heuristic_seeds + weakness_seeds

        # Deduplicate by action_sequence
        seen = set()
        unique = []
        for s in all_seeds:
            key = tuple(s.action_sequence)
            if key not in seen:
                seen.add(key)
                unique.append(s)

        # Sort by priority
        unique.sort(key=lambda s: s.priority, reverse=True)

        return unique

    def _make_simulate_fn(self, attack_engine: Any):
        """Create simulate_fn closure over attack_engine"""
        def simulate_fn(sequence, initial_state, seq_id):
            return attack_engine.simulate_sequence(
                sequence, initial_state, sequence_id=seq_id
            )
        return simulate_fn
