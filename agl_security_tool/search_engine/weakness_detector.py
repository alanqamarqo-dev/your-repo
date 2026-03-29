"""
AGL Search Engine — Economic Weakness Detector (Component 2)
كاشف نقاط الضعف الاقتصادية

═══════════════════════════════════════════════════════════════
Economic Weakness Detector

لا يبحث هذا المكوّن عن bugs — بل يبحث عن:
    نقاط ضعف اقتصادية يمكن استغلالها لتحقيق ربح.

14 نوعاً من الضعف:
    1.  REENTRANCY_DRAIN — withdraw بدون guard
    2.  PRICE_IMBALANCE — oracle + swap = manipulation
    3.  INVARIANT_BREAK — totalDeposits ≠ sum(deposits)
    4.  UNDER_COLLATERALIZATION — borrow بأقل من الضمان
    5.  LIQUIDITY_ASYMMETRY — deposit سهل + withdraw صعب
    6.  REWARD_MISPRICING — مكافأة أعلى من تكلفة
    7.  ACCESS_LEAK — admin function بدون onlyOwner
    8.  ORACLE_STALENESS — oracle بدون freshness check
    9.  ORACLE_MANIPULATION — oracle + flash_loan
    10. FLASH_LOAN_VECTOR — callback + state change
    11. CROSS_FUNCTION_STATE — shared state بين دوال
    12. DONATION_ATTACK — direct transfer يغيّر rate
    13. FIRST_DEPOSITOR — أول مودع يتحكم بالسعر
    14. ROUNDING_ERROR — تقريب في الحساب

كل ضعف → بذور بحث → محرك البحث

═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional, Set, Tuple

from .models import (
    EconomicWeakness,
    WeaknessType,
    SearchSeed,
    SeedSource,
)


class EconomicWeaknessDetector:
    """
    يحلل ActionSpace + FinancialGraph ويكتشف نقاط ضعف اقتصادية.

    لا يُنفذ شيئاً — فقط يُحدد أنماطاً خطيرة ويقترح
    تسلسلات أولية (seeds) لمحرك البحث.
    """

    def __init__(self):
        self._weakness_counter = 0

    # ═══════════════════════════════════════════════════════
    #  Main Entry
    # ═══════════════════════════════════════════════════════

    def detect(
        self,
        action_space: Any,
        graph: Any = None,
    ) -> Tuple[List[EconomicWeakness], List[SearchSeed]]:
        """
        تحليل شامل لاكتشاف نقاط الضعف الاقتصادية.

        Returns:
            (weaknesses, seeds) — نقاط ضعف + بذور بحث مشتقة
        """
        if action_space is None:
            return [], []

        action_graph = getattr(action_space, 'graph', None)
        if not action_graph:
            return [], []

        actions = getattr(action_graph, 'actions', {})
        if not actions:
            return [], []

        weaknesses: List[EconomicWeakness] = []

        # تصنيف الأفعال
        classified = self._classify_actions(actions)

        # === كل detector يبحث عن نوع مختلف ===
        weaknesses.extend(self._detect_reentrancy_drain(classified, actions))
        weaknesses.extend(self._detect_invariant_break(classified, actions))
        weaknesses.extend(self._detect_access_leak(classified, actions))
        weaknesses.extend(self._detect_cross_function_state(classified, actions))
        weaknesses.extend(self._detect_oracle_manipulation(classified, actions))
        weaknesses.extend(self._detect_flash_loan_vector(classified, actions))
        weaknesses.extend(self._detect_liquidity_asymmetry(classified, actions))
        weaknesses.extend(self._detect_donation_attack(classified, actions, graph))
        weaknesses.extend(self._detect_first_depositor(classified, actions))
        weaknesses.extend(self._detect_rounding_error(classified, actions))
        weaknesses.extend(self._detect_reward_mispricing(classified, actions))
        weaknesses.extend(self._detect_price_imbalance(classified, actions))
        weaknesses.extend(self._detect_under_collateralization(classified, actions))
        weaknesses.extend(self._detect_oracle_staleness(classified, actions))

        # ترتيب بالخطورة
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        weaknesses.sort(key=lambda w: (severity_order.get(w.severity, 4), -w.confidence))

        # توليد بذور بحث
        seeds: List[SearchSeed] = []
        for w in weaknesses:
            seeds.extend(w.generate_seed_sequences())

        return weaknesses, seeds

    # ═══════════════════════════════════════════════════════
    #  Action Classification
    # ═══════════════════════════════════════════════════════

    def _classify_actions(self, actions: Dict[str, Any]) -> Dict[str, List[str]]:
        """تصنيف الأفعال حسب الفئة"""
        classified: Dict[str, List[str]] = {
            "inflows": [],
            "outflows": [],
            "borrows": [],
            "repays": [],
            "swaps": [],
            "claims": [],
            "oracles": [],
            "admins": [],
            "flash_loans": [],
            "stakes": [],
            "unstakes": [],
            "views": [],
            "cei_violators": [],
            "eth_senders": [],
            "unguarded": [],
            "public": [],
            "state_changers": [],
        }

        for action_id, action in actions.items():
            cat = action.category.value if hasattr(action.category, 'value') else str(action.category)

            # Category-based
            cat_map = {
                "fund_inflow": "inflows",
                "fund_outflow": "outflows",
                "borrow": "borrows",
                "repay": "repays",
                "swap": "swaps",
                "claim": "claims",
                "oracle_update": "oracles",
                "admin": "admins",
                "flash_loan": "flash_loans",
                "stake": "stakes",
                "unstake": "unstakes",
                "view": "views",
            }
            if cat in cat_map:
                classified[cat_map[cat]].append(action_id)

            if cat not in ("view",):
                classified["state_changers"].append(action_id)

            # Feature-based
            if getattr(action, 'has_cei_violation', False):
                classified["cei_violators"].append(action_id)

            if getattr(action, 'sends_eth', False):
                classified["eth_senders"].append(action_id)

            if not getattr(action, 'reentrancy_guarded', False):
                classified["unguarded"].append(action_id)

            if not getattr(action, 'requires_access', False):
                classified["public"].append(action_id)

        return classified

    # ═══════════════════════════════════════════════════════
    #  Detectors
    # ═══════════════════════════════════════════════════════

    def _next_id(self, prefix: str) -> str:
        self._weakness_counter += 1
        return f"{prefix}_{self._weakness_counter}"

    # --- 1. REENTRANCY DRAIN ---
    def _detect_reentrancy_drain(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """CEI violation + sends ETH + no guard = reentrancy drain"""
        results = []
        cei = set(classified["cei_violators"])
        eth = set(classified["eth_senders"])
        unguarded = set(classified["unguarded"])

        # الحالة المثالية: الثلاثة معاً
        prime_targets = cei & eth & unguarded
        for aid in prime_targets:
            action = actions[aid]
            contract = action.contract_name

            # أفعال الدخول: inflows على نفس العقد
            entries = [
                iid for iid in classified["inflows"]
                if actions[iid].contract_name == contract
                and iid in classified["public"]
            ]

            results.append(EconomicWeakness(
                weakness_id=self._next_id("reent"),
                weakness_type=WeaknessType.REENTRANCY_DRAIN,
                severity="CRITICAL",
                confidence=0.9,
                exploit_hint=f"Reentrancy: {action.function_name} has CEI violation + sends ETH without guard",
                exploit_hint_ar=f"ثغرة إعادة الدخول: {action.function_name} ينتهك CEI ويرسل ETH بدون حماية",
                entry_actions=entries[:3],
                exit_actions=[aid],
                estimated_profit_usd=100_000,
                affected_contract=contract,
                affected_variable="balance",
            ))

        # CEI + ETH لكن مع guard → أقل خطورة
        guarded_cei_eth = (cei & eth) - prime_targets
        for aid in guarded_cei_eth:
            action = actions[aid]
            contract = action.contract_name

            entries = [
                iid for iid in classified["inflows"]
                if actions[iid].contract_name == contract
            ]

            results.append(EconomicWeakness(
                weakness_id=self._next_id("reent"),
                weakness_type=WeaknessType.REENTRANCY_DRAIN,
                severity="MEDIUM",
                confidence=0.4,
                exploit_hint=f"Potential reentrancy in {action.function_name} (has guard, check cross-function)",
                exploit_hint_ar=f"احتمال إعادة دخول في {action.function_name} (محمية لكن افحص cross-function)",
                entry_actions=entries[:2],
                exit_actions=[aid],
                estimated_profit_usd=20_000,
                affected_contract=contract,
            ))

        return results

    # --- 3. INVARIANT BREAK ---
    def _detect_invariant_break(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """
        أي دالة تعدّل state variable بدون مكافئ رياضي واضح.
        مثال: totalSupply يتغير بدون mint/burn.
        """
        results = []
        contracts: Dict[str, Dict[str, Set[str]]] = {}

        for aid, action in actions.items():
            c = action.contract_name
            if c not in contracts:
                contracts[c] = {"writes": set(), "reads": set(), "action_ids": []}

            for w in getattr(action, 'state_writes', []):
                contracts[c]["writes"].add(w)
            for r in getattr(action, 'state_reads', []):
                contracts[c]["reads"].add(r)
            contracts[c]["action_ids"].append(aid)

        for contract, info in contracts.items():
            # متغيرات تُكتب وتُقرأ من دوال مختلفة
            shared = info["writes"] & info["reads"]
            if shared:
                # بحث عن متغيرات "balance-like"
                balance_vars = [
                    v for v in shared
                    if any(k in v.lower() for k in
                           ('balance', 'deposit', 'supply', 'total', 'reserve', 'amount'))
                ]
                if balance_vars:
                    results.append(EconomicWeakness(
                        weakness_id=self._next_id("invariant"),
                        weakness_type=WeaknessType.INVARIANT_BREAK,
                        severity="HIGH",
                        confidence=0.5,
                        exploit_hint=f"Shared balance variables in {contract}: {balance_vars[:3]}",
                        exploit_hint_ar=f"متغيرات أرصدة مشتركة في {contract}: {balance_vars[:3]}",
                        entry_actions=info["action_ids"][:3],
                        exit_actions=info["action_ids"][:3],
                        estimated_profit_usd=50_000,
                        affected_contract=contract,
                        affected_variable=", ".join(balance_vars[:3]),
                        invariant_expression="sum(balances) == totalDeposits",
                    ))

        return results

    # --- 7. ACCESS LEAK ---
    def _detect_access_leak(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """دوال admin بدون access control"""
        results = []
        public = set(classified["public"])

        for aid in classified["admins"]:
            if aid in public:
                action = actions[aid]
                results.append(EconomicWeakness(
                    weakness_id=self._next_id("access"),
                    weakness_type=WeaknessType.ACCESS_LEAK,
                    severity="CRITICAL",
                    confidence=0.85,
                    exploit_hint=f"Admin function {action.function_name} has no access control",
                    exploit_hint_ar=f"دالة إدارية {action.function_name} بدون حماية صلاحيات",
                    entry_actions=[aid],
                    exit_actions=[aid],
                    estimated_profit_usd=500_000,
                    affected_contract=action.contract_name,
                ))

        return results

    # --- 11. CROSS FUNCTION STATE ---
    def _detect_cross_function_state(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """
        Two public functions share state variables and one sends ETH.
        Cross-function reentrancy.
        """
        results = []
        public = set(classified["public"])
        eth_senders = set(classified["eth_senders"])

        # Group by contract
        by_contract: Dict[str, List[Tuple[str, Any]]] = {}
        for aid, action in actions.items():
            if aid in public:
                by_contract.setdefault(action.contract_name, []).append((aid, action))

        for contract, contract_actions in by_contract.items():
            if len(contract_actions) < 2:
                continue

            # Find shared state writes
            for i, (aid1, a1) in enumerate(contract_actions):
                writes1 = set(getattr(a1, 'state_writes', []))
                if not writes1:
                    continue

                for j, (aid2, a2) in enumerate(contract_actions):
                    if i >= j:
                        continue
                    reads2 = set(getattr(a2, 'state_reads', []))
                    shared = writes1 & reads2

                    if shared and (aid1 in eth_senders or aid2 in eth_senders):
                        eth_action = aid1 if aid1 in eth_senders else aid2
                        other = aid2 if eth_action == aid1 else aid1

                        results.append(EconomicWeakness(
                            weakness_id=self._next_id("xfunc"),
                            weakness_type=WeaknessType.CROSS_FUNCTION_STATE,
                            severity="HIGH",
                            confidence=0.65,
                            exploit_hint=(
                                f"Cross-function reentrancy: {a1.function_name} writes "
                                f"{list(shared)[:2]} read by {a2.function_name}"
                            ),
                            exploit_hint_ar=(
                                f"إعادة دخول عبر دوال: {a1.function_name} يكتب "
                                f"{list(shared)[:2]} يقرأها {a2.function_name}"
                            ),
                            entry_actions=[other],
                            exit_actions=[eth_action],
                            auxiliary_actions=[other],
                            estimated_profit_usd=80_000,
                            affected_contract=contract,
                            affected_variable=", ".join(list(shared)[:3]),
                        ))

        return results

    # --- 9. ORACLE MANIPULATION ---
    def _detect_oracle_manipulation(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """Oracle-dependent + flash loan = manipulation vector"""
        results = []

        oracle_deps = []
        for aid, action in actions.items():
            reads = getattr(action, 'state_reads', [])
            if any(k in r.lower() for r in reads for k in ('oracle', 'price', 'feed', 'twap')):
                oracle_deps.append(aid)

        if oracle_deps and classified["flash_loans"]:
            for od in oracle_deps[:3]:
                action = actions[od]
                results.append(EconomicWeakness(
                    weakness_id=self._next_id("oracle_manip"),
                    weakness_type=WeaknessType.ORACLE_MANIPULATION,
                    severity="HIGH",
                    confidence=0.6,
                    exploit_hint=f"Oracle-dependent {action.function_name} + flash loan available",
                    exploit_hint_ar=f"دالة تعتمد على oracle {action.function_name} + قرض فلاش متاح",
                    entry_actions=classified["flash_loans"][:2],
                    exit_actions=[od],
                    estimated_profit_usd=200_000,
                    affected_contract=action.contract_name,
                    requires_flash_loan=True,
                    requires_price_manipulation=True,
                ))

        return results

    # --- 10. FLASH LOAN VECTOR ---
    def _detect_flash_loan_vector(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """Flash loan callback + state changes"""
        results = []

        for fl_id in classified["flash_loans"]:
            fl_action = actions[fl_id]
            contract = fl_action.contract_name

            # Any state-changing action on same contract available to public
            state_changes = [
                aid for aid in classified["state_changers"]
                if actions[aid].contract_name == contract
                and aid in classified["public"]
                and aid != fl_id
            ]

            if state_changes:
                results.append(EconomicWeakness(
                    weakness_id=self._next_id("flash"),
                    weakness_type=WeaknessType.FLASH_LOAN_VECTOR,
                    severity="HIGH",
                    confidence=0.55,
                    exploit_hint=f"Flash loan on {contract} with {len(state_changes)} callable state-changing functions",
                    exploit_hint_ar=f"قرض فلاش على {contract} مع {len(state_changes)} دالة تغيّر الحالة",
                    entry_actions=[fl_id],
                    exit_actions=state_changes[:3],
                    auxiliary_actions=state_changes[:5],
                    estimated_profit_usd=150_000,
                    affected_contract=contract,
                    requires_flash_loan=True,
                ))

        return results

    # --- 5. LIQUIDITY ASYMMETRY ---
    def _detect_liquidity_asymmetry(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """Deposit easy, withdraw hard — or vice versa"""
        results = []
        by_contract: Dict[str, Dict] = {}

        for aid in classified["inflows"]:
            c = actions[aid].contract_name
            by_contract.setdefault(c, {"in": [], "out": []})
            by_contract[c]["in"].append(aid)

        for aid in classified["outflows"]:
            c = actions[aid].contract_name
            by_contract.setdefault(c, {"in": [], "out": []})
            by_contract[c]["out"].append(aid)

        for contract, flows in by_contract.items():
            if flows["in"] and not flows["out"]:
                # funds go in, can't come out → stuck
                results.append(EconomicWeakness(
                    weakness_id=self._next_id("liq"),
                    weakness_type=WeaknessType.LIQUIDITY_ASYMMETRY,
                    severity="MEDIUM",
                    confidence=0.4,
                    exploit_hint=f"Contract {contract} accepts deposits but has no public withdraw",
                    exploit_hint_ar=f"العقد {contract} يقبل إيداعات لكن لا يوجد سحب عام",
                    entry_actions=flows["in"][:3],
                    exit_actions=[],
                    estimated_profit_usd=0,
                    affected_contract=contract,
                ))

            if flows["out"] and not flows["in"]:
                # funds go out without needing deposit?
                public_outs = [
                    aid for aid in flows["out"]
                    if aid in classified["public"]
                ]
                if public_outs:
                    results.append(EconomicWeakness(
                        weakness_id=self._next_id("liq"),
                        weakness_type=WeaknessType.LIQUIDITY_ASYMMETRY,
                        severity="HIGH",
                        confidence=0.5,
                        exploit_hint=f"Contract {contract} has public withdraws without deposits",
                        exploit_hint_ar=f"العقد {contract} فيه سحب عام بدون إيداع",
                        entry_actions=[],
                        exit_actions=public_outs[:3],
                        estimated_profit_usd=50_000,
                        affected_contract=contract,
                    ))

        return results

    # --- 12. DONATION ATTACK ---
    def _detect_donation_attack(
        self, classified: Dict, actions: Dict, graph: Any,
    ) -> List[EconomicWeakness]:
        """
        Direct ETH/token transfer to contract changes exchange rate.
        Common in vault share price manipulation.
        """
        results = []

        # Look for contracts with both shares/deposits AND exchange rate logic
        by_contract: Dict[str, List[str]] = {}
        for aid, action in actions.items():
            c = action.contract_name
            by_contract.setdefault(c, []).append(aid)

        for contract, aids in by_contract.items():
            has_shares = False
            has_balance_read = False

            for aid in aids:
                action = actions[aid]
                reads = getattr(action, 'state_reads', [])
                writes = getattr(action, 'state_writes', [])
                all_vars = reads + writes

                for v in all_vars:
                    vl = v.lower()
                    if any(k in vl for k in ('shares', 'totalsupply', 'supply')):
                        has_shares = True
                    if any(k in vl for k in ('balance', 'reserve', 'totalassets')):
                        has_balance_read = True

            if has_shares and has_balance_read:
                inflows = [aid for aid in classified["inflows"] if actions[aid].contract_name == contract]
                outflows = [aid for aid in classified["outflows"] if actions[aid].contract_name == contract]

                results.append(EconomicWeakness(
                    weakness_id=self._next_id("donation"),
                    weakness_type=WeaknessType.DONATION_ATTACK,
                    severity="HIGH",
                    confidence=0.5,
                    exploit_hint=f"Contract {contract} uses shares + balance — donation may skew rate",
                    exploit_hint_ar=f"العقد {contract} يستخدم أسهم + رصيد — التبرع قد يشوّه السعر",
                    entry_actions=inflows[:3],
                    exit_actions=outflows[:3],
                    estimated_profit_usd=30_000,
                    affected_contract=contract,
                ))

        return results

    # --- 13. FIRST DEPOSITOR ---
    def _detect_first_depositor(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """First depositor can manipulate share price in empty vault"""
        results = []

        for aid in classified["inflows"]:
            action = actions[aid]
            reads = getattr(action, 'state_reads', [])
            writes = getattr(action, 'state_writes', [])
            all_vars = reads + writes

            has_supply_check = any(
                any(k in v.lower() for k in ('totalsupply', 'supply', 'shares'))
                for v in all_vars
            )
            has_division = any(
                any(k in v.lower() for k in ('ratio', 'rate', 'price', 'exchange'))
                for v in all_vars
            )

            if has_supply_check or has_division:
                results.append(EconomicWeakness(
                    weakness_id=self._next_id("first_dep"),
                    weakness_type=WeaknessType.FIRST_DEPOSITOR,
                    severity="MEDIUM",
                    confidence=0.4,
                    exploit_hint=f"First depositor attack on {action.function_name} — supply/share manipulation",
                    exploit_hint_ar=f"هجوم أول مودع على {action.function_name} — تلاعب بالأسهم",
                    entry_actions=[aid],
                    exit_actions=[],
                    estimated_profit_usd=10_000,
                    affected_contract=action.contract_name,
                ))

        return results

    # --- 14. ROUNDING ERROR ---
    def _detect_rounding_error(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """
        Functions that divide amounts may have rounding issues.
        Look for state variables with ratio/price/rate in name.
        """
        results = []

        for aid, action in actions.items():
            reads = getattr(action, 'state_reads', [])
            writes = getattr(action, 'state_writes', [])
            all_vars = reads + writes

            ratio_vars = [
                v for v in all_vars
                if any(k in v.lower() for k in ('ratio', 'rate', 'price', 'pershar', 'exchange'))
            ]

            if ratio_vars and aid in classified["public"]:
                cat = action.category.value if hasattr(action.category, 'value') else str(action.category)
                if cat in ("fund_inflow", "fund_outflow", "swap", "claim"):
                    results.append(EconomicWeakness(
                        weakness_id=self._next_id("round"),
                        weakness_type=WeaknessType.ROUNDING_ERROR,
                        severity="LOW",
                        confidence=0.3,
                        exploit_hint=f"Rounding in {action.function_name} with {ratio_vars[:2]}",
                        exploit_hint_ar=f"خطأ تقريب في {action.function_name} مع {ratio_vars[:2]}",
                        entry_actions=[aid],
                        exit_actions=[aid],
                        estimated_profit_usd=5_000,
                        affected_contract=action.contract_name,
                        affected_variable=", ".join(ratio_vars[:3]),
                    ))

        return results

    # --- 6. REWARD MISPRICING ---
    def _detect_reward_mispricing(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """Claim rewards > staking cost"""
        results = []

        if classified["claims"] and (classified["stakes"] or classified["inflows"]):
            for claim_id in classified["claims"]:
                action = actions[claim_id]
                contract = action.contract_name

                entries = [
                    aid for aid in (classified["stakes"] + classified["inflows"])
                    if actions[aid].contract_name == contract
                ]

                if entries and claim_id in classified["public"]:
                    results.append(EconomicWeakness(
                        weakness_id=self._next_id("reward"),
                        weakness_type=WeaknessType.REWARD_MISPRICING,
                        severity="MEDIUM",
                        confidence=0.4,
                        exploit_hint=f"Reward claim {action.function_name} may exceed staking cost",
                        exploit_hint_ar=f"مطالبة المكافأة {action.function_name} قد تتجاوز تكلفة الإيداع",
                        entry_actions=entries[:3],
                        exit_actions=[claim_id],
                        estimated_profit_usd=20_000,
                        affected_contract=contract,
                    ))

        return results

    # --- 2. PRICE IMBALANCE ---
    def _detect_price_imbalance(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """Swap + oracle = price manipulation opportunity"""
        results = []

        if classified["swaps"] and classified["oracles"]:
            for swap_id in classified["swaps"]:
                action = actions[swap_id]
                contract = action.contract_name

                oracles = [
                    aid for aid in classified["oracles"]
                    if actions[aid].contract_name == contract
                ]

                if oracles and swap_id in classified["public"]:
                    results.append(EconomicWeakness(
                        weakness_id=self._next_id("price"),
                        weakness_type=WeaknessType.PRICE_IMBALANCE,
                        severity="HIGH",
                        confidence=0.55,
                        exploit_hint=f"Swap {action.function_name} + oracle on same contract",
                        exploit_hint_ar=f"مبادلة {action.function_name} + أوراكل على نفس العقد",
                        entry_actions=oracles[:2],
                        exit_actions=[swap_id],
                        estimated_profit_usd=100_000,
                        affected_contract=contract,
                        requires_price_manipulation=True,
                    ))

        return results

    # --- 4. UNDER COLLATERALIZATION ---
    def _detect_under_collateralization(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """Borrow without sufficient collateral checks"""
        results = []

        for borrow_id in classified["borrows"]:
            action = actions[borrow_id]
            if borrow_id in classified["public"]:
                results.append(EconomicWeakness(
                    weakness_id=self._next_id("collat"),
                    weakness_type=WeaknessType.UNDER_COLLATERALIZATION,
                    severity="HIGH",
                    confidence=0.45,
                    exploit_hint=f"Borrow {action.function_name} — check collateral requirements",
                    exploit_hint_ar=f"اقتراض {action.function_name} — افحص متطلبات الضمان",
                    entry_actions=classified["inflows"][:2],
                    exit_actions=[borrow_id],
                    estimated_profit_usd=200_000,
                    affected_contract=action.contract_name,
                ))

        return results

    # --- 8. ORACLE STALENESS ---
    def _detect_oracle_staleness(
        self, classified: Dict, actions: Dict,
    ) -> List[EconomicWeakness]:
        """Oracle reads without freshness validation"""
        results = []

        for aid, action in actions.items():
            reads = getattr(action, 'state_reads', [])
            oracle_reads = [
                r for r in reads
                if any(k in r.lower() for k in ('oracle', 'price', 'feed'))
            ]

            if oracle_reads:
                # Check if there's a timestamp/block check
                has_freshness = any(
                    any(k in r.lower() for k in ('timestamp', 'updatedat', 'staleness', 'heartbeat'))
                    for r in reads
                )

                if not has_freshness:
                    results.append(EconomicWeakness(
                        weakness_id=self._next_id("stale"),
                        weakness_type=WeaknessType.ORACLE_STALENESS,
                        severity="MEDIUM",
                        confidence=0.5,
                        exploit_hint=f"{action.function_name} reads oracle without freshness check",
                        exploit_hint_ar=f"{action.function_name} يقرأ الأوراكل بدون فحص الحداثة",
                        entry_actions=[aid],
                        exit_actions=[aid],
                        estimated_profit_usd=50_000,
                        affected_contract=action.contract_name,
                    ))

        return results
