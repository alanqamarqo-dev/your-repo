"""
AGL State Extraction — Consistency Validator
التحقق من تناسق الرسم البياني المالي

يتحقق من:
  1. Balance Conservation — حفظ الأرصدة (كل تدفق يخفض مصدر ويزيد هدف)
  2. Illogical Cycles — الدورات غير المنطقية (أموال تدور بلا غرض)
  3. Orphan Nodes — عقد معزولة بلا اتصال
  4. Access Control Consistency — تناسق الصلاحيات
  5. Oracle Dependency Integrity — سلامة تبعيات الأوراكل
"""

from typing import Dict, List, Set, Tuple, Optional
from collections import deque

from .models import (
    FinancialGraph, GraphNode, GraphEdge,
    NodeType, EdgeType,
    ValidationResult, ValidationIssue,
)


class ConsistencyValidator:
    """
    محقق تناسق الرسم البياني المالي.

    يكتشف:
    - عدم حفظ الأرصدة (مصدر يخسر أكثر مما يكسب الهدف أو العكس)
    - دورات مالية غير منطقية
    - عقد معزولة
    - ثغرات في التحكم بالوصول
    - تبعيات أوراكل مفقودة
    """

    # ═══════════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════════

    def validate(self, graph: FinancialGraph) -> ValidationResult:
        """
        تحقق شامل من تناسق الرسم البياني.

        Returns:
            ValidationResult مع كل المشاكل المكتشفة
        """
        result = ValidationResult()
        issues: List[ValidationIssue] = []

        # ─── 1. Balance Conservation ───
        balance_issues = self._check_balance_conservation(graph)
        issues.extend(balance_issues)
        if any(i.severity == "error" for i in balance_issues):
            result.balance_conservation_ok = False

        # ─── 2. Illogical Cycles ───
        cycle_issues = self._check_illogical_cycles(graph)
        issues.extend(cycle_issues)
        if any(i.severity == "error" for i in cycle_issues):
            result.no_illogical_cycles = False

        # ─── 3. Orphan Nodes ───
        orphan_issues = self._check_orphan_nodes(graph)
        issues.extend(orphan_issues)
        if orphan_issues:
            result.all_nodes_connected = False

        # ─── 4. Access Control Consistency ───
        access_issues = self._check_access_control_consistency(graph)
        issues.extend(access_issues)

        # ─── 5. Oracle Dependency Integrity ───
        oracle_issues = self._check_oracle_integrity(graph)
        issues.extend(oracle_issues)

        # ─── 6. Fund Flow Completeness ───
        flow_issues = self._check_fund_flow_completeness(graph)
        issues.extend(flow_issues)

        # ─── Compile Result ───
        result.issues = issues
        result.is_consistent = all(i.severity != "error" for i in issues)

        # Summary
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        info_count = sum(1 for i in issues if i.severity == "info")
        result.summary = (
            f"تحقق: {len(issues)} مشكلة — "
            f"{error_count} خطأ, {warning_count} تحذير, {info_count} ملاحظة"
        )

        return result

    # ═══════════════════════════════════════════════════════════
    #  1. Balance Conservation Check
    # ═══════════════════════════════════════════════════════════

    def _check_balance_conservation(self, graph: FinancialGraph) -> List[ValidationIssue]:
        """
        التحقق من حفظ الأرصدة:
        - لكل توكن: مجموع التدفقات الداخلة = مجموع التدفقات الخارجة (باستثناء mint/burn)
        - المراكز (deposits) يجب أن يكون لها مقابل (withdrawals)
        """
        issues: List[ValidationIssue] = []

        # تجميع التدفقات حسب التوكن
        token_inflows: Dict[str, Dict[str, int]] = {}   # token → {node → count}
        token_outflows: Dict[str, Dict[str, int]] = {}   # token → {node → count}

        for flow in graph.fund_flows:
            token = flow.token_id
            if token not in token_inflows:
                token_inflows[token] = {}
                token_outflows[token] = {}

            # Mint → inflow only (no outflow source)
            if flow.flow_type == "mint":
                target = flow.target_account
                token_inflows[token][target] = token_inflows[token].get(target, 0) + 1
                continue

            # Burn → outflow only (no inflow target)
            if flow.flow_type == "burn":
                source = flow.source_account
                token_outflows[token][source] = token_outflows[token].get(source, 0) + 1
                continue

            # Normal flow → both
            source = flow.source_account
            target = flow.target_account
            token_outflows[token][source] = token_outflows[token].get(source, 0) + 1
            token_inflows[token][target] = token_inflows[token].get(target, 0) + 1

        # Check each token
        for token in set(list(token_inflows.keys()) + list(token_outflows.keys())):
            inflows = token_inflows.get(token, {})
            outflows = token_outflows.get(token, {})

            # عقد تستقبل بدون إرسال (sinks)
            pure_sinks = set(inflows.keys()) - set(outflows.keys())
            # عقد ترسل بدون استقبال (sources)  
            pure_sources = set(outflows.keys()) - set(inflows.keys())

            # Sinks that are not zero_address are potential issues
            for sink in pure_sinks:
                if sink == "zero_address":
                    continue
                if inflows[sink] > 1:  # Multiple inflows without outflow
                    issues.append(ValidationIssue(
                        issue_type="balance_accumulation",
                        severity="info",
                        description=(
                            f"العقدة '{sink}' تستقبل تدفقات من توكن '{token}' "
                            f"({inflows[sink]} تدفقات) بدون تدفق خارجي — "
                            f"قد يكون بالتصميم (treasury) أو تسرب أموال"
                        ),
                        involved_nodes=[sink],
                        details={"token": token, "inflow_count": inflows[sink]},
                    ))

            # Sources that are not zero_address
            for source in pure_sources:
                if source == "zero_address":
                    continue
                if outflows[source] > 1:
                    issues.append(ValidationIssue(
                        issue_type="balance_drain",
                        severity="warning",
                        description=(
                            f"العقدة '{source}' ترسل توكن '{token}' "
                            f"({outflows[source]} تدفقات) بدون تدفق داخلي — "
                            f"مصدر الأموال غير واضح"
                        ),
                        involved_nodes=[source],
                        details={"token": token, "outflow_count": outflows[source]},
                    ))

        # Check for mismatched credit/debit operations
        credit_count = sum(1 for f in graph.fund_flows if f.flow_type == "credit")
        debit_count = sum(1 for f in graph.fund_flows if f.flow_type == "debit")
        if credit_count > 0 and debit_count > 0:
            if abs(credit_count - debit_count) > credit_count * 0.5:
                issues.append(ValidationIssue(
                    issue_type="credit_debit_mismatch",
                    severity="warning",
                    description=(
                        f"عدم تطابق بين عمليات الرصيد: "
                        f"{credit_count} إضافة مقابل {debit_count} خصم — "
                        f"قد يدل على عدم حفظ الأرصدة"
                    ),
                    details={"credits": credit_count, "debits": debit_count},
                ))

        return issues

    # ═══════════════════════════════════════════════════════════
    #  2. Illogical Cycle Detection
    # ═══════════════════════════════════════════════════════════

    def _check_illogical_cycles(self, graph: FinancialGraph) -> List[ValidationIssue]:
        """
        كشف الدورات غير المنطقية في تدفقات الأموال:
        - دورة مالية A→B→C→A بدون قيمة إضافية
        - دورة تحكم A controls B controls A
        """
        issues: List[ValidationIssue] = []

        # ─── Fund Flow Cycles ───
        fund_flow_edges = {
            eid: e for eid, e in graph.edges.items()
            if e.edge_type == EdgeType.FUND_FLOW
        }

        if fund_flow_edges:
            cycles = self._find_cycles(graph, fund_flow_edges)
            for cycle in cycles:
                # Check if cycle involves same token (potential exploit path)
                cycle_tokens = set()
                for i in range(len(cycle) - 1):
                    edges = graph.get_edges_between(cycle[i], cycle[i + 1])
                    for e in edges:
                        if e.token:
                            cycle_tokens.add(e.token)

                if len(cycle_tokens) == 1:
                    # Same token cycling — suspicious
                    issues.append(ValidationIssue(
                        issue_type="illogical_fund_cycle",
                        severity="warning",
                        description=(
                            f"دورة مالية لتوكن واحد '{list(cycle_tokens)[0]}': "
                            f"{' → '.join(cycle)} — "
                            f"قد تمثل ثغرة إعادة الدخول أو تلاعب بالسعر"
                        ),
                        involved_nodes=cycle,
                        details={
                            "cycle_length": len(cycle),
                            "tokens": list(cycle_tokens),
                        },
                    ))
                elif len(cycle_tokens) > 1:
                    # Multi-token cycling — could be arbitrage
                    issues.append(ValidationIssue(
                        issue_type="multi_token_cycle",
                        severity="info",
                        description=(
                            f"دورة متعددة التوكنات: "
                            f"{' → '.join(cycle)} — "
                            f"قد تكون مسار مراجحة (arbitrage)"
                        ),
                        involved_nodes=cycle,
                        details={
                            "cycle_length": len(cycle),
                            "tokens": list(cycle_tokens),
                        },
                    ))

        # ─── Access Control Cycles ───
        access_edges = {
            eid: e for eid, e in graph.edges.items()
            if e.edge_type == EdgeType.ACCESS_CONTROL
        }
        if access_edges:
            access_cycles = self._find_cycles(graph, access_edges)
            for cycle in access_cycles:
                issues.append(ValidationIssue(
                    issue_type="access_control_cycle",
                    severity="error",
                    description=(
                        f"دورة في التحكم بالوصول: "
                        f"{' → '.join(cycle)} — "
                        f"A يتحكم في B و B يتحكم في A"
                    ),
                    involved_nodes=cycle,
                ))

        return issues

    def _find_cycles(
        self, graph: FinancialGraph,
        edge_subset: Dict[str, GraphEdge],
        max_depth: int = 8,
    ) -> List[List[str]]:
        """
        بحث DFS عن الدورات في مجموعة أضلاع محددة.
        max_depth يحد من طول الدورة المكتشفة.
        """
        # Build adjacency for this edge subset
        adj: Dict[str, Set[str]] = {}
        for edge in edge_subset.values():
            if edge.source_node not in adj:
                adj[edge.source_node] = set()
            adj[edge.source_node].add(edge.target_node)

        cycles: List[List[str]] = []
        visited_global: Set[str] = set()

        for start in adj:
            if start in visited_global:
                continue
            self._dfs_cycle(start, start, [start], set([start]),
                           adj, cycles, max_depth, visited_global)

        return cycles

    def _dfs_cycle(
        self, start: str, current: str, path: List[str],
        visited: Set[str], adj: Dict[str, Set[str]],
        cycles: List[List[str]], max_depth: int,
        visited_global: Set[str],
    ) -> None:
        """DFS recursion for cycle detection"""
        if len(path) > max_depth:
            return

        for neighbor in adj.get(current, set()):
            if neighbor == start and len(path) >= 3:
                # Found a cycle
                cycles.append(path + [start])
                return
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                self._dfs_cycle(start, neighbor, path, visited,
                               adj, cycles, max_depth, visited_global)
                path.pop()
                visited.discard(neighbor)

        visited_global.add(current)

    # ═══════════════════════════════════════════════════════════
    #  3. Orphan Node Detection
    # ═══════════════════════════════════════════════════════════

    def _check_orphan_nodes(self, graph: FinancialGraph) -> List[ValidationIssue]:
        """كشف العقد المعزولة بدون أضلاع"""
        issues: List[ValidationIssue] = []

        for nid, node in graph.nodes.items():
            out_edges = graph.adjacency_out.get(nid, [])
            in_edges = graph.adjacency_in.get(nid, [])

            if not out_edges and not in_edges:
                # Placeholder nodes are expected to be orphans sometimes
                if node.attributes.get("is_placeholder"):
                    continue

                issues.append(ValidationIssue(
                    issue_type="orphan_node",
                    severity="info",
                    description=(
                        f"العقدة '{node.label}' ({node.node_type.value}) "
                        f"معزولة — لا أضلاع داخلة أو خارجة"
                    ),
                    involved_nodes=[nid],
                ))

        return issues

    # ═══════════════════════════════════════════════════════════
    #  4. Access Control Consistency
    # ═══════════════════════════════════════════════════════════

    def _check_access_control_consistency(
        self, graph: FinancialGraph,
    ) -> List[ValidationIssue]:
        """التحقق من تناسق الصلاحيات"""
        issues: List[ValidationIssue] = []

        # Find all fund flow edges
        fund_edges = [
            e for e in graph.edges.values()
            if e.edge_type == EdgeType.FUND_FLOW
        ]

        # Find all access control edges
        access_edges = [
            e for e in graph.edges.values()
            if e.edge_type == EdgeType.ACCESS_CONTROL
        ]

        # Check: high-value functions without access control
        for edge in fund_edges:
            if not edge.guarded_by and not edge.required_role:
                # This fund flow has no access control
                # Check if it's a public function
                if edge.function_name and edge.function_name not in (
                    "transfer", "transferFrom", "approve",
                    "deposit", "withdraw", "redeem", "mint",
                    "swap", "receive", "fallback",
                ):
                    issues.append(ValidationIssue(
                        issue_type="unguarded_fund_flow",
                        severity="warning",
                        description=(
                            f"تدفق مالي عبر '{edge.function_name}' بين "
                            f"'{edge.source_node}' → '{edge.target_node}' "
                            f"بدون حماية وصول (modifier/role)"
                        ),
                        involved_edges=[edge.edge_id],
                        involved_nodes=[edge.source_node, edge.target_node],
                        details={
                            "function": edge.function_name,
                            "token": edge.token,
                        },
                    ))

        # Check: entities with admin roles but no access-controlled functions
        for nid, node in graph.nodes.items():
            roles = node.attributes.get("roles", [])
            if roles:
                # Check if there are access control edges for this node
                has_access = any(
                    e.target_node == nid
                    for e in access_edges
                )
                if not has_access:
                    issues.append(ValidationIssue(
                        issue_type="unused_roles",
                        severity="info",
                        description=(
                            f"العقدة '{node.label}' لديها أدوار {roles} "
                            f"لكن لا تُستخدم في التحكم بالوصول"
                        ),
                        involved_nodes=[nid],
                    ))

        return issues

    # ═══════════════════════════════════════════════════════════
    #  5. Oracle Dependency Integrity
    # ═══════════════════════════════════════════════════════════

    def _check_oracle_integrity(self, graph: FinancialGraph) -> List[ValidationIssue]:
        """التحقق من سلامة تبعيات الأوراكل"""
        issues: List[ValidationIssue] = []

        # Find oracle dependency edges
        oracle_edges = [
            e for e in graph.edges.values()
            if e.edge_type == EdgeType.PRICE_DEPENDENCY
        ]

        if not oracle_edges:
            return issues

        # Check: contracts reading oracle without staleness check
        oracle_readers = set()
        for edge in oracle_edges:
            oracle_readers.add(edge.source_node)

        # Check for nodes that have oracle links but no staleness validation
        for nid in oracle_readers:
            if nid in graph.nodes:
                node = graph.nodes[nid]
                # If it's a lending market or pool, oracle staleness is critical
                if node.node_type in (NodeType.POOL, NodeType.PROTOCOL):
                    entity_type = node.attributes.get("entity_type", "")
                    if entity_type in ("lending_market", "pool"):
                        issues.append(ValidationIssue(
                            issue_type="oracle_staleness_risk",
                            severity="info",
                            description=(
                                f"'{node.label}' يقرأ أسعاراً من أوراكل — "
                                f"تأكد من وجود فحص صلاحية الزمن (staleness check)"
                            ),
                            involved_nodes=[nid],
                        ))

        # Check: oracle nodes that no one reads from (dead oracles)
        oracle_nodes = {
            nid for nid, n in graph.nodes.items()
            if n.node_type == NodeType.ORACLE
        }
        read_oracles = set()
        for edge in oracle_edges:
            read_oracles.add(edge.target_node)

        dead_oracles = oracle_nodes - read_oracles
        for oracle_id in dead_oracles:
            if oracle_id in graph.nodes:
                issues.append(ValidationIssue(
                    issue_type="dead_oracle",
                    severity="info",
                    description=(
                        f"أوراكل '{graph.nodes[oracle_id].label}' "
                        f"معرّف لكن لا يُقرأ منه — قد يكون ميتاً"
                    ),
                    involved_nodes=[oracle_id],
                ))

        return issues

    # ═══════════════════════════════════════════════════════════
    #  6. Fund Flow Completeness
    # ═══════════════════════════════════════════════════════════

    def _check_fund_flow_completeness(
        self, graph: FinancialGraph,
    ) -> List[ValidationIssue]:
        """التحقق من اكتمال تدفقات الأموال"""
        issues: List[ValidationIssue] = []

        # Check for deposit without withdraw
        deposit_targets = set()
        withdraw_sources = set()

        for flow in graph.fund_flows:
            if flow.flow_type in ("deposit", "stake"):
                deposit_targets.add(flow.target_account)
            if flow.flow_type in ("withdraw", "unstake", "redeem"):
                withdraw_sources.add(flow.source_account)

        # Deposits without matching withdrawals
        locked_funds = deposit_targets - withdraw_sources
        for target in locked_funds:
            if target not in ("zero_address",):
                issues.append(ValidationIssue(
                    issue_type="no_withdrawal_path",
                    severity="warning",
                    description=(
                        f"إيداعات في '{target}' بدون مسار سحب مكتشف — "
                        f"قد تكون الأموال محتجزة"
                    ),
                    involved_nodes=[target],
                ))

        # Check for borrow without repay
        borrow_sources = set()
        repay_targets = set()

        for flow in graph.fund_flows:
            if flow.flow_type == "borrow":
                borrow_sources.add(flow.target_account)
            if flow.flow_type == "repay":
                repay_targets.add(flow.target_account)

        unrepayable = borrow_sources - repay_targets
        for source in unrepayable:
            issues.append(ValidationIssue(
                issue_type="no_repay_path",
                severity="info",
                description=(
                    f"اقتراض من '{source}' بدون مسار سداد مكتشف"
                ),
                involved_nodes=[source],
            ))

        return issues
