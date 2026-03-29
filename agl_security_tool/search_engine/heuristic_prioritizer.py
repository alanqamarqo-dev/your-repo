"""
AGL Search Engine — Heuristic Prioritizer (Component 1)
محرك التحليل الاستدلالي — أين نبدأ البحث أصلاً؟

═══════════════════════════════════════════════════════════════
Attack Heuristic Engine

بدل أن تبحث في 10¹³ تسلسل عشوائياً،
هذا المكوّن يحدد:
    1. أي الدوال تستحق الدراسة (targets)
    2. أولوية كل هدف (score)
    3. لماذا هذا الهدف مهم (reasons)
    4. ما الأفعال المرتبطة به من Layer 2

المبدأ: لا تبحث أينما اتفق — ابدأ حيث تفوح رائحة الأموال.

═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional, Set, Tuple

from .models import HeuristicTarget, SearchSeed, SeedSource
from ..heikal_math import WaveDomainEvaluator, HolographicVulnerabilityMemory


# ═══════════════════════════════════════════════════════════════
#  Scoring Weights
# ═══════════════════════════════════════════════════════════════

# كل ميزة لها وزن → المجموع يحدد أولوية الهدف
HEURISTIC_WEIGHTS = {
    "moves_funds": 0.25,  # الدالة تحرّك أموال (أهم شيء)
    "cei_violation": 0.20,  # CEI violation → reentrancy vector
    "sends_eth": 0.15,  # ترسل ETH → callback ممكن
    "no_access_control": 0.12,  # أي شخص يستطيع استدعاءها
    "not_guarded": 0.10,  # لا يوجد nonReentrant
    "reads_oracle": 0.08,  # تعتمد على oracle → manipulation
    "has_state_conflict": 0.05,  # conflict مع دالة أخرى
    "modifies_balances": 0.05,  # تغير أرصدة
}


class HeuristicPrioritizer:
    """
    يحلل ActionSpace من Layer 2 ويرتب الأهداف بالأولوية.

    Pipeline:
        actions → _score_each() → _rank() → _generate_seeds() → targets + seeds
    """

    def __init__(self):
        self.weights = dict(HEURISTIC_WEIGHTS)
        self.wave_evaluator = WaveDomainEvaluator()
        self.holographic = HolographicVulnerabilityMemory()

    # ═══════════════════════════════════════════════════════
    #  Main Entry
    # ═══════════════════════════════════════════════════════

    def analyze(
        self,
        action_space: Any,
        graph: Any = None,
    ) -> Tuple[List[HeuristicTarget], List[SearchSeed]]:
        """
        تحليل فضاء الأفعال وتحديد الأهداف عالية القيمة.

        Returns:
            (targets, seeds) — أهداف مرتبة + بذور بحث
        """
        if action_space is None:
            return [], []

        action_graph = getattr(action_space, "graph", None)
        if not action_graph:
            return [], []

        actions = getattr(action_graph, "actions", {})
        if not actions:
            return [], []

        # 1. حلل كل action → target
        targets = self._analyze_actions(actions, action_graph, graph)

        # 2. رتّب بالأولوية
        targets.sort(key=lambda t: t.score, reverse=True)

        # 3. ولّد بذور بحث
        seeds = self._generate_seeds(targets, actions, action_graph)

        return targets, seeds

    # ═══════════════════════════════════════════════════════
    #  Action Analysis
    # ═══════════════════════════════════════════════════════

    def _analyze_actions(
        self,
        actions: Dict[str, Any],
        action_graph: Any,
        graph: Any,
    ) -> List[HeuristicTarget]:
        """تحليل كل action وبناء HeuristicTarget"""
        # مجمّع: function → target
        function_targets: Dict[str, HeuristicTarget] = {}

        for action_id, action in actions.items():
            fn_key = f"{action.contract_name}.{action.function_name}"

            if fn_key not in function_targets:
                function_targets[fn_key] = HeuristicTarget(
                    target_id=fn_key,
                    contract_name=action.contract_name,
                    function_name=action.function_name,
                )

            target = function_targets[fn_key]
            target.action_ids.append(action_id)

            # الأولى تحدد الخصائص
            self._extract_features(target, action)

        # حساب الأولوية لكل هدف
        for target in function_targets.values():
            target.score = self._compute_score(target)

        # عزّز بالسياق من FinancialGraph
        if graph:
            self._enrich_from_graph(function_targets, graph)

        return list(function_targets.values())

    def _extract_features(self, target: HeuristicTarget, action: Any) -> None:
        """استخراج خصائص مهمة من Action"""
        cat = (
            action.category.value
            if hasattr(action.category, "value")
            else str(action.category)
        )

        # هل تحرّك أموال؟
        if cat in (
            "fund_inflow",
            "fund_outflow",
            "borrow",
            "repay",
            "swap",
            "liquidate",
            "stake",
            "unstake",
            "claim",
            "flash_loan",
        ):
            target.moves_funds = True
            target.tags.add("fund_mover")

        # CEI violations
        if getattr(action, "has_cei_violation", False):
            target.has_cei_violation = True
            target.tags.add("cei_violation")

        # sends ETH
        if getattr(action, "sends_eth", False):
            target.sends_eth = True
            target.tags.add("sends_eth")

        # reentrancy guard
        if getattr(action, "reentrancy_guarded", False):
            target.reentrancy_guarded = True
        else:
            if target.sends_eth or target.has_cei_violation:
                target.tags.add("unguarded")

        # access control
        if not getattr(action, "requires_access", False):
            target.tags.add("public")
        else:
            target.requires_access = True
            target.tags.add("restricted")

        # oracle
        state_reads = getattr(action, "state_reads", [])
        for sr in state_reads:
            if any(k in sr.lower() for k in ("oracle", "price", "feed", "twap")):
                target.reads_oracle = True
                target.tags.add("oracle_dependent")

        # external calls
        ext_calls = getattr(action, "external_calls", [])
        if ext_calls:
            target.tags.add("external_calls")

        # attack types from Layer 2
        attack_types = getattr(action, "attack_types", [])
        for at in attack_types:
            at_val = at.value if hasattr(at, "value") else str(at)
            target.tags.add(f"attack:{at_val}")

        # category tag
        target.tags.add(f"category:{cat}")

        # profit potential from Layer 2
        pp = getattr(action, "profit_potential", 0)
        if pp and isinstance(pp, (int, float)):
            target.estimated_value_at_risk = max(
                target.estimated_value_at_risk, float(pp)
            )

    def _compute_score(self, target: HeuristicTarget) -> float:
        """
        حساب أولوية الهدف باستخدام Heikal Wave-Domain Boolean Logic.

        بدلاً من الجمع الخطي، نحوّل كل ميزة إلى موجة ψ = e^(i·x·π)
        ونكشف التداخل البنّاء (CEI + sends_eth) والهدّام (access_required).
        + مطابقة هولوغرافية لأنماط الثغرات المعروفة.
        """
        # === Build feature dict for wave evaluator ===
        features = {
            "moves_funds": 1.0 if target.moves_funds else 0.0,
            "cei_violation": 1.0 if target.has_cei_violation else 0.0,
            "sends_eth": 1.0 if target.sends_eth else 0.0,
            "no_access_control": 0.0 if target.requires_access else 1.0,
            "not_guarded": (
                1.0
                if (
                    not target.reentrancy_guarded
                    and (target.has_cei_violation or target.sends_eth)
                )
                else 0.0
            ),
            "reads_oracle": 1.0 if target.reads_oracle else 0.0,
            "has_state_conflict": 1.0 if "external_calls" in target.tags else 0.0,
            "modifies_balances": 1.0 if target.moves_funds else 0.0,
        }

        # === Heikal Wave-Domain Scoring ===
        wave_result = self.wave_evaluator.evaluate(features)
        score = wave_result.heuristic_score  # Born rule: |ψ|²

        # === Holographic Pattern Matching Bonus ===
        holo_features = {
            "has_external_call": 1.0 if "external_calls" in target.tags else 0.0,
            "state_after_call": 1.0 if target.has_cei_violation else 0.0,
            "no_reentrancy_guard": 0.0 if target.reentrancy_guarded else 1.0,
            "moves_funds": 1.0 if target.moves_funds else 0.0,
            "sends_eth": 1.0 if target.sends_eth else 0.0,
            "reads_oracle": 1.0 if target.reads_oracle else 0.0,
            "no_access_control": 0.0 if target.requires_access else 1.0,
            "modifies_balance": 1.0 if target.moves_funds else 0.0,
        }
        matches = self.holographic.match(holo_features)
        if matches:
            best_match = matches[0]
            # إضافة bonus بناءً على قوة المطابقة الهولوغرافية
            score += best_match.similarity * 0.15
            target.tags.add(f"holo_match:{best_match.pattern_name}")

        # === Access penalty ===
        if target.requires_access:
            score *= 0.3

        # === Build reasons ===
        target.reasons = self._build_reasons(target)

        # === Add wave/holo metadata to reasons ===
        if wave_result.constructive_pairs:
            for pair in wave_result.constructive_pairs:
                target.reasons.append(
                    f"تداخل بنّاء: {pair[0]} + {pair[1]} (wave constructive)"
                )
        if matches:
            target.reasons.append(
                f"نمط هولوغرافي: {matches[0].pattern_name} "
                f"(تشابه: {matches[0].similarity:.1%})"
            )

        return min(score, 1.0)

    def _build_reasons(self, target: HeuristicTarget) -> List[str]:
        """بناء قائمة أسباب مقروءة"""
        reasons = []
        if target.moves_funds:
            reasons.append("تحرّك أموال (fund mover)")
        if target.has_cei_violation:
            reasons.append("CEI violation → reentrancy vector")
        if target.sends_eth:
            reasons.append("ترسل ETH خارجياً → callback ممكن")
        if not target.reentrancy_guarded and target.has_cei_violation:
            reasons.append("بدون nonReentrant guard!")
        if not target.requires_access:
            reasons.append("public — أي شخص يستدعيها")
        if target.reads_oracle:
            reasons.append("تعتمد على oracle → manipulation")
        if target.requires_access:
            reasons.append("⚠ تحتاج صلاحية (access required)")
        return reasons

    # ═══════════════════════════════════════════════════════
    #  Graph Enrichment
    # ═══════════════════════════════════════════════════════

    def _enrich_from_graph(
        self,
        targets: Dict[str, HeuristicTarget],
        graph: Any,
    ) -> None:
        """عزّز الأهداف بمعلومات من FinancialGraph"""
        entities = getattr(graph, "entities", {})
        fund_flows = getattr(graph, "fund_flows", [])

        # تقدير القيمة المعرّضة للخطر
        for flow in fund_flows:
            fn = getattr(flow, "function_name", "")
            source = getattr(flow, "source_account", "")

            for tid, target in targets.items():
                if target.function_name == fn:
                    # ربط التدفق بالهدف
                    target.tags.add("flow_linked")

                    # تقدير القيمة من الكيان المصدر
                    if source in entities:
                        entity = entities[source]
                        cv = getattr(entity, "collateralization_ratio", 0)
                        if cv and isinstance(cv, (int, float)) and cv > 0:
                            target.estimated_value_at_risk = max(
                                target.estimated_value_at_risk, float(cv)
                            )

    # ═══════════════════════════════════════════════════════
    #  Seed Generation
    # ═══════════════════════════════════════════════════════

    def _generate_seeds(
        self,
        targets: List[HeuristicTarget],
        actions: Dict[str, Any],
        action_graph: Any,
    ) -> List[SearchSeed]:
        """
        توليد بذور بحث من الأهداف المرتبة.

        استراتيجيات:
        1. Reentrancy seed: deposit → vulnerable_withdraw
        2. Drain seed: أي outflow بدون حماية
        3. Pair seed: inflow+outflow على نفس العقد
        4. Graph path seeds: من attack_paths
        """
        seeds: List[SearchSeed] = []

        # قوائم مفيدة
        inflow_actions: Dict[str, List[str]] = {}  # contract → [action_ids]
        outflow_actions: Dict[str, List[str]] = {}
        vulnerable_actions: List[str] = []

        for action_id, action in actions.items():
            cat = (
                action.category.value
                if hasattr(action.category, "value")
                else str(action.category)
            )
            contract = action.contract_name

            if cat == "fund_inflow" and not getattr(action, "requires_access", False):
                inflow_actions.setdefault(contract, []).append(action_id)

            if cat == "fund_outflow" and not getattr(action, "requires_access", False):
                outflow_actions.setdefault(contract, []).append(action_id)

            if (
                getattr(action, "has_cei_violation", False)
                and getattr(action, "sends_eth", False)
                and not getattr(action, "reentrancy_guarded", False)
            ):
                vulnerable_actions.append(action_id)

        # === Strategy 1: Reentrancy Seeds ===
        for vuln_id in vulnerable_actions:
            vuln_action = actions[vuln_id]
            contract = vuln_action.contract_name
            if contract in inflow_actions:
                for inflow_id in inflow_actions[contract][:3]:
                    seeds.append(
                        SearchSeed(
                            seed_id=f"reent_{inflow_id}_{vuln_id}",
                            source=SeedSource.HEURISTIC,
                            action_sequence=[inflow_id, vuln_id],
                            estimated_profit=100_000,  # reentrancy عادة مربح جداً
                            priority=0.95,
                            notes="reentrancy: deposit → vulnerable withdraw",
                        )
                    )

        # === Strategy 2: Drain Seeds ===
        for contract, outflows in outflow_actions.items():
            for out_id in outflows[:3]:
                action = actions[out_id]
                if contract in inflow_actions:
                    for in_id in inflow_actions[contract][:2]:
                        seeds.append(
                            SearchSeed(
                                seed_id=f"drain_{in_id}_{out_id}",
                                source=SeedSource.HEURISTIC,
                                action_sequence=[in_id, out_id],
                                estimated_profit=10_000,
                                priority=0.7,
                                notes="drain: deposit → withdraw pair",
                            )
                        )

        # === Strategy 3: Graph path seeds ===
        attack_paths = []
        if hasattr(action_graph, "get_attack_paths"):
            try:
                attack_paths = action_graph.get_attack_paths()
            except Exception:
                pass

        for i, path in enumerate(attack_paths[:20]):
            seeds.append(
                SearchSeed(
                    seed_id=f"path_{i}",
                    source=SeedSource.LAYER2_PATH,
                    action_sequence=list(path),
                    estimated_profit=5_000,
                    priority=0.6,
                    notes=f"Layer 2 attack path #{i}",
                )
            )

        # === Strategy 4: High-value target exploration ===
        for target in targets[:5]:
            if target.score >= 0.5 and target.action_ids:
                for aid in target.action_ids[:2]:
                    seeds.append(
                        SearchSeed(
                            seed_id=f"target_{aid}",
                            source=SeedSource.HEURISTIC,
                            action_sequence=[aid],
                            estimated_profit=target.estimated_value_at_risk,
                            priority=target.score,
                            notes=f"high-value target: {', '.join(target.reasons[:2])}",
                        )
                    )

        # الترتيب بالأولوية
        seeds.sort(key=lambda s: s.priority, reverse=True)

        return seeds
