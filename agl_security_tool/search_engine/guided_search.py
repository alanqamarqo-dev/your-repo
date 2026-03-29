"""
AGL Search Engine — Guided Search (Component 3)
محرك البحث الموجَّه — القلب الذكي

═══════════════════════════════════════════════════════════════
Guided Search Engine

هذا ليس brute force.
هذا محرك بحث ذكي يستخدم 3 استراتيجيات:

    1. Beam Search — يوسّع أفضل K مسارات فقط
    2. MCTS — يوازن بين الاستكشاف والاستغلال (UCB1)
    3. Evolutionary — mutation + crossover + selection

المبدأ:
    بدلاً من 3.2×10¹³ تسلسل → نختبر ~500 فقط
    لكن: نختار الـ 500 الأذكى.

═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import math
import random
import time
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple, Callable

from .models import (
    SearchConfig,
    SearchSeed,
    SearchNode,
    NodeState,
    CandidateSequence,
    SearchStats,
    SeedSource,
)
from ..heikal_math import HolographicVulnerabilityMemory


class GuidedSearchEngine:
    """
    محرك بحث ذكي عن تسلسلات هجوم مربحة.

    Integration:
        - يأخذ بذور (seeds) من HeuristicPrioritizer + WeaknessDetector
        - يتوسع باستخدام ActionGraph من Layer 2
        - يقيّم باستخدام AttackSimulationEngine من Layer 3
        - يُرجع CandidateSequences مُرتبة بالربح
    """

    def __init__(self, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()
        self.stats = SearchStats()
        self._nodes: Dict[str, SearchNode] = {}
        self._best_profit: float = 0.0
        self._start_time: float = 0.0
        self.holographic = HolographicVulnerabilityMemory()

    # ═══════════════════════════════════════════════════════
    #  Main Entry
    # ═══════════════════════════════════════════════════════

    def search(
        self,
        seeds: List[SearchSeed],
        action_graph: Any,
        actions: Dict[str, Any],
        simulate_fn: Callable,
        initial_state: Any,
    ) -> List[CandidateSequence]:
        """
        البحث الموجه عن تسلسلات هجوم مربحة.

        Args:
            seeds: بذور بحث أولية
            action_graph: رسم بياني للأفعال (Layer 2)
            actions: قاموس الأفعال {id → Action}
            simulate_fn: دالة المحاكاة من Layer 3
                         (sequence, initial_state, seq_id) → AttackResult
            initial_state: الحالة الأولية من Layer 3

        Returns:
            قائمة CandidateSequence مرتبة بالربح
        """
        self._start_time = time.time()
        self._nodes.clear()
        self.stats = SearchStats()

        if not seeds:
            return []

        # حساب إحصائيات البذور
        self._count_seeds(seeds)

        candidates: List[CandidateSequence] = []
        strategy = (
            self.config.strategy.value
            if hasattr(self.config.strategy, "value")
            else str(self.config.strategy)
        )

        if strategy == "beam_search":
            candidates = self._beam_search(
                seeds, action_graph, actions, simulate_fn, initial_state
            )
        elif strategy == "mcts":
            candidates = self._mcts_search(
                seeds, action_graph, actions, simulate_fn, initial_state
            )
        elif strategy == "evolutionary":
            candidates = self._evolutionary_search(
                seeds, action_graph, actions, simulate_fn, initial_state
            )
        elif strategy == "greedy_best_first":
            candidates = self._greedy_search(
                seeds, action_graph, actions, simulate_fn, initial_state
            )
        elif strategy == "hybrid":
            candidates = self._hybrid_search(
                seeds, action_graph, actions, simulate_fn, initial_state
            )
        else:
            candidates = self._beam_search(
                seeds, action_graph, actions, simulate_fn, initial_state
            )

        # ترتيب بالربح الفعلي
        candidates.sort(key=lambda c: c.actual_profit_usd, reverse=True)

        self.stats.search_time_ms = (time.time() - self._start_time) * 1000
        return candidates

    # ═══════════════════════════════════════════════════════
    #  Strategy 1: Beam Search
    # ═══════════════════════════════════════════════════════

    def _beam_search(
        self,
        seeds: List[SearchSeed],
        action_graph: Any,
        actions: Dict[str, Any],
        simulate_fn: Callable,
        initial_state: Any,
    ) -> List[CandidateSequence]:
        """
        Beam Search: في كل عمق، احتفظ بأفضل K تسلسل فقط.

        width = beam_width (default 10)
        depth = beam_depth (default 5)

        في كل خطوة:
            1. لكل تسلسل حالي → وسّع بكل الأفعال الممكنة
            2. قيّم كل توسعة (محاكاة سريعة)
            3. احتفظ بأفضل K فقط
            4. كرر حتى العمق المطلوب
        """
        candidates: List[CandidateSequence] = []
        width = self.config.beam_width
        depth = self.config.beam_depth

        # تحويل البذور لشعاعات أولية
        beams: List[Tuple[List[str], float, str]] = []
        for seed in seeds[: width * 2]:
            if seed.action_sequence:
                beams.append(
                    (
                        list(seed.action_sequence),
                        seed.priority,
                        seed.source.value,
                    )
                )

        if not beams:
            return candidates

        # === Beam search loop ===
        for d in range(depth):
            if self._time_exceeded() or self._budget_exceeded():
                break

            next_beams: List[Tuple[List[str], float, str]] = []

            for seq, score, source in beams:
                if self._time_exceeded():
                    break

                # Evaluate current sequence
                candidate = self._evaluate_sequence(
                    seq, actions, simulate_fn, initial_state, source
                )
                if candidate and candidate.simulated:
                    candidates.append(candidate)
                    self.stats.sequences_simulated += 1
                    if candidate.actual_profit_usd > 0:
                        self.stats.sequences_profitable += 1

                # Expand: get successors of last action
                last_action = seq[-1]
                successors = self._get_successors(last_action, action_graph)

                for succ_id in successors:
                    if succ_id in seq:  # avoid cycles
                        continue
                    if len(seq) >= self.config.max_depth:
                        continue

                    new_seq = seq + [succ_id]
                    # Heuristic score for ordering
                    h_score = self._heuristic_score(new_seq, actions)
                    next_beams.append((new_seq, h_score, source))
                    self.stats.nodes_explored += 1

            # Prune to beam width
            next_beams.sort(key=lambda x: x[1], reverse=True)
            beams = next_beams[:width]
            self.stats.nodes_pruned += max(0, len(next_beams) - width)
            self.stats.sequences_generated += len(next_beams)

        # Evaluate remaining beams
        for seq, score, source in beams:
            if self._time_exceeded() or self._budget_exceeded():
                break
            candidate = self._evaluate_sequence(
                seq, actions, simulate_fn, initial_state, source
            )
            if candidate and candidate.simulated:
                candidates.append(candidate)
                self.stats.sequences_simulated += 1
                if candidate.actual_profit_usd > 0:
                    self.stats.sequences_profitable += 1

        self.stats.by_strategy["beam_search"] = len(candidates)
        return candidates

    # ═══════════════════════════════════════════════════════
    #  Strategy 2: MCTS (Monte Carlo Tree Search)
    # ═══════════════════════════════════════════════════════

    def _mcts_search(
        self,
        seeds: List[SearchSeed],
        action_graph: Any,
        actions: Dict[str, Any],
        simulate_fn: Callable,
        initial_state: Any,
    ) -> List[CandidateSequence]:
        """
        Monte Carlo Tree Search مع UCB1.

        UCB1 = avg_reward + C * sqrt(ln(N) / n_i)

        C = mcts_exploration_weight (√2)
        N = total visits of parent
        n_i = visits of child

        Loop:
            1. SELECT: follow UCB1 to leaf
            2. EXPAND: add children (successor actions)
            3. SIMULATE (rollout): random playout to depth
            4. BACKPROPAGATE: update visit counts + rewards
        """
        candidates: List[CandidateSequence] = []
        iterations = self.config.mcts_iterations
        C = self.config.mcts_exploration_weight

        # Create root node
        root = SearchNode(
            node_id="root",
            depth=0,
            state=NodeState.EXPANDING,
            sequence_so_far=[],
        )
        self._nodes["root"] = root

        # Initialize children from seeds
        for seed in seeds[:20]:
            if seed.action_sequence:
                child_id = f"seed_{seed.seed_id}"
                child = SearchNode(
                    node_id=child_id,
                    parent_id="root",
                    depth=1,
                    sequence_so_far=list(seed.action_sequence),
                    last_action=(
                        seed.action_sequence[-1] if seed.action_sequence else ""
                    ),
                    heuristic_score=seed.priority,
                )
                self._nodes[child_id] = child
                root.children.append(child_id)

        # === MCTS iterations ===
        for iteration in range(iterations):
            if self._time_exceeded() or self._budget_exceeded():
                break

            # 1. SELECT
            node = self._mcts_select(root, C)

            # 2. EXPAND
            if node.state != NodeState.DEAD:
                child = self._mcts_expand(node, action_graph, actions)
            else:
                child = node

            # 3. SIMULATE (rollout)
            reward = self._mcts_rollout(
                child, action_graph, actions, simulate_fn, initial_state
            )

            # 4. BACKPROPAGATE
            self._mcts_backpropagate(child, reward)

            self.stats.nodes_explored += 1

        # Collect best candidates
        for node_id, node in self._nodes.items():
            if node.visits > 0 and node.sequence_so_far:
                candidate = self._evaluate_sequence(
                    node.sequence_so_far, actions, simulate_fn, initial_state, "mcts"
                )
                if candidate and candidate.simulated:
                    candidates.append(candidate)
                    self.stats.sequences_simulated += 1
                    if candidate.actual_profit_usd > 0:
                        self.stats.sequences_profitable += 1

                if self._time_exceeded() or self._budget_exceeded():
                    break

        self.stats.by_strategy["mcts"] = len(candidates)
        return candidates

    def _mcts_select(self, node: SearchNode, C: float) -> SearchNode:
        """Follow UCB1 scores down the tree to a leaf"""
        current = node
        while current.children and current.state != NodeState.DEAD:
            best_child_id = None
            best_ucb = -float("inf")

            for child_id in current.children:
                child = self._nodes.get(child_id)
                if not child:
                    continue

                if child.state == NodeState.PRUNED or child.state == NodeState.DEAD:
                    continue

                if child.visits == 0:
                    return child  # unexplored — prioritize

                total_parent = max(current.visits, 1)
                ucb = child.average_reward + C * math.sqrt(
                    math.log(total_parent) / child.visits
                )
                child.ucb_score = ucb

                if ucb > best_ucb:
                    best_ucb = ucb
                    best_child_id = child_id

            if best_child_id:
                current = self._nodes[best_child_id]
            else:
                break

        return current

    def _mcts_expand(
        self, node: SearchNode, action_graph: Any, actions: Dict[str, Any]
    ) -> SearchNode:
        """Add children to a leaf node"""
        if node.depth >= self.config.max_depth:
            node.is_terminal = True
            return node

        last_action = node.last_action or (
            node.sequence_so_far[-1] if node.sequence_so_far else ""
        )

        if not last_action:
            return node

        successors = self._get_successors(last_action, action_graph)
        existing_seqs = {
            tuple(self._nodes[cid].sequence_so_far)
            for cid in node.children
            if cid in self._nodes
        }

        for succ_id in successors:
            if succ_id in node.sequence_so_far:
                continue

            new_seq = node.sequence_so_far + [succ_id]
            if tuple(new_seq) in existing_seqs:
                continue

            child_id = f"mcts_{uuid.uuid4().hex[:8]}"
            child = SearchNode(
                node_id=child_id,
                parent_id=node.node_id,
                depth=node.depth + 1,
                sequence_so_far=new_seq,
                last_action=succ_id,
                heuristic_score=self._heuristic_score(new_seq, actions),
            )
            self._nodes[child_id] = child
            node.children.append(child_id)

        node.state = NodeState.EXPANDING

        # Return random unexplored child
        unexplored = [
            cid
            for cid in node.children
            if cid in self._nodes and self._nodes[cid].visits == 0
        ]
        if unexplored:
            return self._nodes[random.choice(unexplored)]
        return node

    def _mcts_rollout(
        self,
        node: SearchNode,
        action_graph: Any,
        actions: Dict[str, Any],
        simulate_fn: Callable,
        initial_state: Any,
    ) -> float:
        """
        Random rollout from node to a terminal state.
        Returns reward (profit in USD).
        """
        if not node.sequence_so_far:
            return 0.0

        # Extend sequence randomly up to rollout_depth
        seq = list(node.sequence_so_far)
        for _ in range(self.config.mcts_rollout_depth):
            if len(seq) >= self.config.max_depth:
                break
            last = seq[-1]
            successors = self._get_successors(last, action_graph)
            valid = [s for s in successors if s not in seq]
            if not valid:
                break
            seq.append(random.choice(valid))

        # Simulate the sequence
        try:
            candidate = self._evaluate_sequence(
                seq, actions, simulate_fn, initial_state, "mcts_rollout"
            )
            if candidate and candidate.simulated:
                return candidate.actual_profit_usd
        except Exception:
            pass

        return 0.0

    def _mcts_backpropagate(self, node: SearchNode, reward: float) -> None:
        """Propagate reward back up the tree"""
        current: Optional[SearchNode] = node
        while current:
            current.visits += 1
            current.total_reward += reward
            if reward > 0 and reward > current.profit_so_far_usd:
                current.profit_so_far_usd = reward
                current.state = NodeState.PROFITABLE

            parent_id = current.parent_id
            current = self._nodes.get(parent_id) if parent_id else None

    # ═══════════════════════════════════════════════════════
    #  Strategy 3: Evolutionary
    # ═══════════════════════════════════════════════════════

    def _evolutionary_search(
        self,
        seeds: List[SearchSeed],
        action_graph: Any,
        actions: Dict[str, Any],
        simulate_fn: Callable,
        initial_state: Any,
    ) -> List[CandidateSequence]:
        """
        Evolutionary search:
            Population = set of candidate sequences
            Fitness = actual profit (from simulation)

            Each generation:
            1. Evaluate fitness
            2. Selection (tournament)
            3. Crossover
            4. Mutation
            5. Elitism (keep best N)
        """
        candidates: List[CandidateSequence] = []
        pop_size = self.config.population_size
        generations = self.config.generations
        mutation_rate = self.config.mutation_rate
        crossover_rate = self.config.crossover_rate
        elite_count = self.config.elite_count

        # Initialize population from seeds
        population: List[List[str]] = []
        for seed in seeds[:pop_size]:
            if seed.action_sequence:
                population.append(list(seed.action_sequence))

        # Fill remaining with random expansions
        all_action_ids = list(actions.keys())
        while len(population) < pop_size and all_action_ids:
            seq_len = random.randint(2, min(4, self.config.max_depth))
            seq = random.sample(all_action_ids, min(seq_len, len(all_action_ids)))
            population.append(seq)

        if not population:
            return candidates

        # Fitness cache
        fitness_cache: Dict[str, float] = {}

        for gen in range(generations):
            if self._time_exceeded() or self._budget_exceeded():
                break

            # 1. Evaluate fitness
            fitted: List[Tuple[List[str], float]] = []
            for seq in population:
                cache_key = ",".join(seq)
                if cache_key in fitness_cache:
                    fitted.append((seq, fitness_cache[cache_key]))
                else:
                    candidate = self._evaluate_sequence(
                        seq, actions, simulate_fn, initial_state, "evolutionary"
                    )
                    if candidate and candidate.simulated:
                        fit = candidate.actual_profit_usd
                        fitness_cache[cache_key] = fit
                        fitted.append((seq, fit))
                        candidates.append(candidate)
                        self.stats.sequences_simulated += 1
                        if fit > 0:
                            self.stats.sequences_profitable += 1
                    else:
                        fitness_cache[cache_key] = -1000
                        fitted.append((seq, -1000))

                if self._time_exceeded() or self._budget_exceeded():
                    break

            # Sort by fitness
            fitted.sort(key=lambda x: x[1], reverse=True)

            # 2. Elitism — keep best
            next_pop = [seq for seq, _ in fitted[:elite_count]]

            # 3. Selection + Crossover + Mutation
            while len(next_pop) < pop_size:
                if self._time_exceeded():
                    break

                if random.random() < crossover_rate and len(fitted) >= 2:
                    # Tournament selection
                    parent1 = self._tournament_select(fitted)
                    parent2 = self._tournament_select(fitted)
                    child = self._crossover(parent1, parent2)
                else:
                    parent = self._tournament_select(fitted)
                    child = list(parent)

                # Mutation
                if random.random() < mutation_rate:
                    child = self._mutate(child, action_graph, actions)

                if child:
                    next_pop.append(child)

            population = next_pop
            self.stats.sequences_generated += len(population)

        self.stats.by_strategy["evolutionary"] = len(candidates)
        return candidates

    def _tournament_select(
        self, fitted: List[Tuple[List[str], float]], k: int = 3
    ) -> List[str]:
        """Tournament selection — pick best of k random"""
        sample = random.sample(fitted, min(k, len(fitted)))
        return max(sample, key=lambda x: x[1])[0]

    def _crossover(self, p1: List[str], p2: List[str]) -> List[str]:
        """Single-point crossover of two sequences"""
        if len(p1) <= 1 or len(p2) <= 1:
            return list(p1) if random.random() < 0.5 else list(p2)

        cut1 = random.randint(1, len(p1) - 1)
        cut2 = random.randint(1, len(p2) - 1)
        child = p1[:cut1] + p2[cut2:]

        # Deduplicate (keep first occurrence)
        seen = set()
        result = []
        for aid in child:
            if aid not in seen:
                seen.add(aid)
                result.append(aid)

        return result[: self.config.max_depth] if result else list(p1)

    def _mutate(
        self, seq: List[str], action_graph: Any, actions: Dict[str, Any]
    ) -> List[str]:
        """Mutate a sequence: insert, delete, or swap an action"""
        if not seq:
            return seq

        mutation_type = random.choice(["insert", "delete", "swap", "replace"])
        result = list(seq)

        if mutation_type == "insert" and len(result) < self.config.max_depth:
            # Insert a successor of a random element
            idx = random.randint(0, len(result) - 1)
            successors = self._get_successors(result[idx], action_graph)
            valid = [s for s in successors if s not in result]
            if valid:
                result.insert(idx + 1, random.choice(valid))

        elif mutation_type == "delete" and len(result) > 1:
            # Delete random action
            idx = random.randint(0, len(result) - 1)
            result.pop(idx)

        elif mutation_type == "swap" and len(result) >= 2:
            # Swap two random actions
            i, j = random.sample(range(len(result)), 2)
            result[i], result[j] = result[j], result[i]

        elif mutation_type == "replace":
            # Replace random action with random action
            idx = random.randint(0, len(result) - 1)
            all_ids = list(actions.keys())
            candidates = [a for a in all_ids if a not in result]
            if candidates:
                result[idx] = random.choice(candidates)

        return result

    # ═══════════════════════════════════════════════════════
    #  Strategy 4: Greedy Best-First
    # ═══════════════════════════════════════════════════════

    def _greedy_search(
        self,
        seeds: List[SearchSeed],
        action_graph: Any,
        actions: Dict[str, Any],
        simulate_fn: Callable,
        initial_state: Any,
    ) -> List[CandidateSequence]:
        """
        Greedy best-first: always expand the most promising node.
        Fast but incomplete — good for quick wins.
        """
        candidates: List[CandidateSequence] = []

        # Priority queue (sorted list)
        open_list: List[Tuple[float, List[str], str]] = []
        for seed in seeds:
            if seed.action_sequence:
                open_list.append(
                    (
                        -seed.priority,  # negative for min-heap behavior
                        list(seed.action_sequence),
                        seed.source.value,
                    )
                )

        open_list.sort(key=lambda x: x[0])
        visited: Set[str] = set()

        while open_list and not self._time_exceeded() and not self._budget_exceeded():
            _, seq, source = open_list.pop(0)  # best first
            seq_key = ",".join(seq)

            if seq_key in visited:
                continue
            visited.add(seq_key)

            # Evaluate
            candidate = self._evaluate_sequence(
                seq, actions, simulate_fn, initial_state, source
            )
            if candidate and candidate.simulated:
                candidates.append(candidate)
                self.stats.sequences_simulated += 1
                if candidate.actual_profit_usd > 0:
                    self.stats.sequences_profitable += 1

            self.stats.nodes_explored += 1

            # Expand
            if len(seq) < self.config.max_depth:
                last = seq[-1]
                for succ in self._get_successors(last, action_graph):
                    if succ not in seq:
                        new_seq = seq + [succ]
                        h = self._heuristic_score(new_seq, actions)
                        open_list.append((-h, new_seq, source))

                open_list.sort(key=lambda x: x[0])
                # Trim to avoid memory explosion
                open_list = open_list[: self.config.max_sequences_to_test]

        self.stats.by_strategy["greedy"] = len(candidates)
        return candidates

    # ═══════════════════════════════════════════════════════
    #  Strategy 5: Hybrid (all strategies)
    # ═══════════════════════════════════════════════════════

    def _hybrid_search(
        self,
        seeds: List[SearchSeed],
        action_graph: Any,
        actions: Dict[str, Any],
        simulate_fn: Callable,
        initial_state: Any,
    ) -> List[CandidateSequence]:
        """
        Hybrid: يُشغل كل الاستراتيجيات بميزانية مقسّمة.

        - 40% Beam Search (الأسرع والأكثر تركيزاً)
        - 30% MCTS (الأعمق استكشافاً)
        - 20% Evolutionary (الأكثر تنوعاً)
        - 10% Greedy (أسرع نتائج أولية)
        """
        all_candidates: List[CandidateSequence] = []

        # Save original config
        orig_time = self.config.max_search_time_seconds
        orig_sequences = self.config.max_sequences_to_test
        orig_iters = self.config.mcts_iterations
        orig_gens = self.config.generations

        # === Phase 1: Greedy (10% budget) — quick wins ===
        self.config.max_search_time_seconds = orig_time * 0.1
        self.config.max_sequences_to_test = max(20, orig_sequences // 10)
        greedy = self._greedy_search(
            seeds, action_graph, actions, simulate_fn, initial_state
        )
        all_candidates.extend(greedy)

        # Reset timer for remaining phases
        self._start_time = time.time()

        # === Phase 2: Beam Search (40% budget) ===
        self.config.max_search_time_seconds = orig_time * 0.4
        self.config.max_sequences_to_test = max(50, orig_sequences * 4 // 10)
        beam = self._beam_search(
            seeds, action_graph, actions, simulate_fn, initial_state
        )
        all_candidates.extend(beam)

        self._start_time = time.time()

        # === Phase 3: MCTS (30% budget) ===
        self.config.max_search_time_seconds = orig_time * 0.3
        self.config.mcts_iterations = max(30, orig_iters * 3 // 10)
        mcts = self._mcts_search(
            seeds, action_graph, actions, simulate_fn, initial_state
        )
        all_candidates.extend(mcts)

        self._start_time = time.time()

        # === Phase 4: Evolutionary (20% budget) ===
        self.config.max_search_time_seconds = orig_time * 0.2
        self.config.population_size = max(10, self.config.population_size // 2)
        self.config.generations = max(5, orig_gens // 3)

        # Add near-miss mutations as extra seeds
        near_miss_seeds = self._extract_near_misses(all_candidates, seeds)
        combined_seeds = seeds + near_miss_seeds

        evo = self._evolutionary_search(
            combined_seeds, action_graph, actions, simulate_fn, initial_state
        )
        all_candidates.extend(evo)

        # Restore config
        self.config.max_search_time_seconds = orig_time
        self.config.max_sequences_to_test = orig_sequences
        self.config.mcts_iterations = orig_iters
        self.config.generations = orig_gens
        self.config.population_size = self.config.population_size  # already loaded

        # Deduplicate
        seen: Set[str] = set()
        unique: List[CandidateSequence] = []
        for c in all_candidates:
            key = ",".join(c.action_ids)
            if key not in seen:
                seen.add(key)
                unique.append(c)

        self.stats.by_strategy["hybrid"] = len(unique)
        return unique

    # ═══════════════════════════════════════════════════════
    #  Helper Methods
    # ═══════════════════════════════════════════════════════

    def _evaluate_sequence(
        self,
        action_ids: List[str],
        actions: Dict[str, Any],
        simulate_fn: Callable,
        initial_state: Any,
        source: str,
    ) -> Optional[CandidateSequence]:
        """
        Convert action_ids to step_info dicts and simulate.

        Uses Layer 3's simulate_sequence(sequence, initial_state, seq_id)
        """
        if not action_ids:
            return None

        # Build step_info dicts (L2 → L3 format)
        steps: List[Dict[str, Any]] = []
        for aid in action_ids:
            if aid not in actions:
                continue
            action = actions[aid]
            step = self._action_to_step(action)
            steps.append(step)

        if not steps:
            return None

        candidate_id = f"cand_{uuid.uuid4().hex[:8]}"

        candidate = CandidateSequence(
            candidate_id=candidate_id,
            steps=steps,
            action_ids=list(action_ids),
            source=(
                SeedSource(source)
                if source in [s.value for s in SeedSource]
                else SeedSource.HEURISTIC
            ),
            estimated_profit_usd=self._heuristic_score(action_ids, actions) * 10000,
        )

        # Simulate via Layer 3
        try:
            seq_id = f"search_{candidate_id}"
            t0 = time.time()
            result = simulate_fn(steps, initial_state, seq_id)
            sim_time = (time.time() - t0) * 1000
            self.stats.simulation_time_ms += sim_time

            candidate.simulated = True
            candidate.actual_profit_usd = getattr(result, "net_profit_usd", 0.0)
            candidate.simulation_success = getattr(result, "is_profitable", False)
            candidate.attack_type = getattr(result, "attack_type", "")
            candidate.severity = getattr(result, "severity", "")

            if candidate.actual_profit_usd > self._best_profit:
                self._best_profit = candidate.actual_profit_usd

        except Exception:
            candidate.simulated = True
            candidate.actual_profit_usd = 0.0
            candidate.simulation_success = False

        return candidate

    def _action_to_step(self, action: Any) -> Dict[str, Any]:
        """Convert a Layer 2 Action to a step_info dict for Layer 3"""
        cat = (
            action.category.value
            if hasattr(action.category, "value")
            else str(action.category)
        )
        attack_types = [
            at.value if hasattr(at, "value") else str(at)
            for at in getattr(action, "attack_types", [])
        ]

        # Build parameters
        params = []
        for p in getattr(action, "parameters", []):
            params.append(
                {
                    "name": p.name,
                    "concrete_values": getattr(p, "concrete_values", []),
                    "is_amount": getattr(p, "is_amount", False),
                }
            )

        return {
            "action_id": action.action_id,
            "contract_name": action.contract_name,
            "function_name": action.function_name,
            "category": cat,
            "net_delta": getattr(action, "net_delta", 0),
            "external_calls": getattr(action, "external_calls", []),
            "sends_eth": getattr(action, "sends_eth", False),
            "has_cei_violation": getattr(action, "has_cei_violation", False),
            "reentrancy_guarded": getattr(action, "reentrancy_guarded", False),
            "preconditions": getattr(action, "preconditions", []),
            "parameters": params,
            "msg_value": "1000000000000000000" if cat == "fund_inflow" else "0",
            "attack_types": attack_types,
        }

    def _get_successors(self, action_id: str, action_graph: Any) -> List[str]:
        """Get successor action IDs from ActionGraph"""
        if hasattr(action_graph, "get_successors"):
            try:
                succs = action_graph.get_successors(action_id)
                # get_successors may return Action objects — extract action_id strings
                result = []
                for s in succs:
                    if isinstance(s, str):
                        result.append(s)
                    elif hasattr(s, "action_id"):
                        result.append(s.action_id)
                    else:
                        result.append(str(s))
                return result
            except Exception:
                pass

        # Fallback: successors adjacency → extract target_action from edges
        successors_map = getattr(action_graph, "successors", {})
        edge_ids = successors_map.get(action_id, [])
        if edge_ids:
            edges = getattr(action_graph, "edges", {})
            result = []
            for eid in edge_ids:
                edge = edges.get(eid)
                if edge and hasattr(edge, "target_action"):
                    result.append(edge.target_action)
            return result

        return []

    def _heuristic_score(self, action_ids: List[str], actions: Dict[str, Any]) -> float:
        """
        Heuristic score for a sequence — enhanced with Holographic Pattern Matching.

        يستخدم الذاكرة الهولوغرافية للبحث عن أنماط الثغرات المعروفة:
        - FFT-based circular convolution لمقارنة الأنماط
        - phase modulation للتشفير
        - cross-correlation للتشابه

        Factors:
        - CEI violations → high score
        - ETH sends → high score
        - Fund movers → medium score
        - Access required → penalty
        - Holographic pattern match → bonus
        """
        score = 0.0

        # === Aggregate features across all actions in sequence ===
        agg_features = {
            "has_external_call": 0.0,
            "state_after_call": 0.0,
            "no_reentrancy_guard": 0.0,
            "moves_funds": 0.0,
            "sends_eth": 0.0,
            "reads_oracle": 0.0,
            "no_access_control": 0.0,
            "modifies_balance": 0.0,
        }

        for aid in action_ids:
            action = actions.get(aid)
            if not action:
                continue

            cat = (
                action.category.value
                if hasattr(action.category, "value")
                else str(action.category)
            )

            if cat in ("fund_outflow", "claim"):
                score += 0.3
                agg_features["moves_funds"] = 1.0
            elif cat in ("fund_inflow", "stake"):
                score += 0.1
            elif cat in ("borrow", "flash_loan"):
                score += 0.25

            if getattr(action, "has_cei_violation", False):
                score += 0.4
                agg_features["state_after_call"] = 1.0
            if getattr(action, "sends_eth", False):
                score += 0.2
                agg_features["sends_eth"] = 1.0
                agg_features["has_external_call"] = 1.0
            if not getattr(action, "reentrancy_guarded", False):
                score += 0.1
                agg_features["no_reentrancy_guard"] = 1.0
            if getattr(action, "requires_access", False):
                score -= 0.5
            else:
                agg_features["no_access_control"] = 1.0
            if getattr(action, "reads_oracle", False):
                agg_features["reads_oracle"] = 1.0

        # === Holographic Pattern Matching Bonus ===
        try:
            matches = self.holographic.match(agg_features)
            if matches:
                best = matches[0]
                # مكافأة بناءً على قوة التشابه الهولوغرافي
                score += best.similarity * 0.2
        except Exception:
            pass

        return max(score, 0.0)

    def _extract_near_misses(
        self,
        candidates: List[CandidateSequence],
        original_seeds: List[SearchSeed],
    ) -> List[SearchSeed]:
        """
        Near-miss: sequences that almost made profit (e.g., -$100 < profit < $0).
        Convert them to seeds for evolutionary mutation.
        """
        near_misses: List[SearchSeed] = []

        for c in candidates:
            if c.simulated and -500 < c.actual_profit_usd <= 0:
                near_misses.append(
                    SearchSeed(
                        seed_id=f"near_{c.candidate_id}",
                        source=SeedSource.LAYER3_NEAR_MISS,
                        action_sequence=list(c.action_ids),
                        estimated_profit=abs(c.actual_profit_usd),
                        priority=0.75,
                        notes=f"Near-miss: profit=${c.actual_profit_usd:.2f}",
                    )
                )

        return near_misses[:10]

    def _count_seeds(self, seeds: List[SearchSeed]) -> None:
        """Count seeds by source"""
        self.stats.total_seeds = len(seeds)
        for s in seeds:
            if s.source == SeedSource.HEURISTIC:
                self.stats.seeds_from_heuristic += 1
            elif s.source == SeedSource.WEAKNESS:
                self.stats.seeds_from_weakness += 1
            elif s.source == SeedSource.LAYER2_PATH:
                self.stats.seeds_from_layer2 += 1
            elif s.source == SeedSource.LAYER3_NEAR_MISS:
                self.stats.seeds_from_near_miss += 1
            elif s.source == SeedSource.MUTATION:
                self.stats.seeds_from_mutation += 1

    def _time_exceeded(self) -> bool:
        elapsed = time.time() - self._start_time
        return elapsed >= self.config.max_search_time_seconds

    def _budget_exceeded(self) -> bool:
        return self.stats.sequences_simulated >= self.config.max_sequences_to_test
