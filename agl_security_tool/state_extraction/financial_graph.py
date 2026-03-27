"""
AGL State Extraction — Financial Graph Builder
بناء الرسم البياني المالي الديناميكي

يأخذ كل المخرجات (Entities, Relationships, Balances, Flows)
ويبني رسماً بيانياً مالياً متكاملاً:
  - Nodes: كيانات مالية مع سماتها (نوع التوكن، المبلغ، الصلاحيات، الأوراكل، نسبة الضمان)
  - Edges: علاقات مالية (تحويلات، صلاحيات، تبعيات أسعار، هيكلي)
  - Dynamic: قابل للتحديث أثناء المحاكاة
"""

from typing import Dict, List, Optional, Set, Tuple

from .models import (
    Entity, EntityType,
    Relationship, RelationType,
    BalanceEntry, FundFlow,
    GraphNode, GraphEdge, NodeType, EdgeType,
    FinancialGraph,
)


# ═══════════════════════════════════════════════════════════════
#  Mapping tables
# ═══════════════════════════════════════════════════════════════

_ENTITY_TO_NODE_TYPE = {
    EntityType.TOKEN: NodeType.TOKEN,
    EntityType.POOL: NodeType.POOL,
    EntityType.VAULT: NodeType.VAULT,
    EntityType.LENDING_MARKET: NodeType.POOL,
    EntityType.ORACLE: NodeType.ORACLE,
    EntityType.GOVERNANCE: NodeType.GOVERNANCE,
    EntityType.STAKING: NodeType.PROTOCOL,
    EntityType.BRIDGE: NodeType.PROTOCOL,
    EntityType.ROUTER: NodeType.PROTOCOL,
    EntityType.PROXY: NodeType.PROTOCOL,
    EntityType.ACCOUNT: NodeType.ADDRESS,
    EntityType.COLLATERAL: NodeType.STATE_VARIABLE,
    EntityType.DEBT: NodeType.STATE_VARIABLE,
    EntityType.REWARD: NodeType.STATE_VARIABLE,
    EntityType.TREASURY: NodeType.PROTOCOL,
    EntityType.GENERIC_CONTRACT: NodeType.PROTOCOL,
}

# Fund flow relation types
_FUND_FLOW_RELATIONS = {
    RelationType.TRANSFERS_TO, RelationType.MINTS_TO,
    RelationType.BURNS_FROM, RelationType.DEPOSITS_INTO,
    RelationType.WITHDRAWS_FROM, RelationType.BORROWS_FROM,
    RelationType.REPAYS_TO, RelationType.LIQUIDATES,
    RelationType.SWAPS_THROUGH, RelationType.STAKES_IN,
    RelationType.CLAIMS_FROM, RelationType.COLLATERALIZES,
    RelationType.BRIDGES_TO, RelationType.FEE_TO,
}

_ACCESS_RELATIONS = {
    RelationType.OWNS, RelationType.ADMIN_OF,
    RelationType.CAN_CALL, RelationType.CAN_PAUSE,
    RelationType.CAN_UPGRADE, RelationType.ROLE_GRANTS,
    RelationType.GOVERNS,
}

_ORACLE_RELATIONS = {
    RelationType.PRICE_FEED_FOR, RelationType.READS_PRICE_FROM,
    RelationType.TWAP_SOURCE,
}

_STRUCTURAL_RELATIONS = {
    RelationType.INHERITS_FROM, RelationType.DELEGATES_TO,
    RelationType.PROXIED_BY, RelationType.USES_LIBRARY,
    RelationType.WRAPS, RelationType.BACKED_BY,
}


class FinancialGraphBuilder:
    """
    يبني الرسم البياني المالي من كل البيانات المستخرجة.

    Pipeline:
      entities → nodes
      relationships → edges
      balances → node attributes
      fund_flows → fund_flow edges
    """

    def __init__(self):
        self._edge_counter = 0

    def _next_edge_id(self) -> str:
        self._edge_counter += 1
        return f"edge_{self._edge_counter}"

    # ═══════════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════════

    def build(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        balances: List[BalanceEntry],
        fund_flows: List[FundFlow],
        source_files: Optional[List[str]] = None,
    ) -> FinancialGraph:
        """
        بناء الرسم البياني المالي الكامل.

        Args:
            entities: الكيانات المستخرجة
            relationships: العلاقات المكتشفة
            balances: سجل الأرصدة
            fund_flows: تدفقات الأموال
            source_files: الملفات المصدرية

        Returns:
            FinancialGraph — رسم بياني مالي ديناميكي
        """
        graph = FinancialGraph()
        graph.source_files = source_files or []

        # Store raw data in graph
        graph.entities = {e.entity_id: e for e in entities}
        graph.relationships = list(relationships)
        graph.balances = list(balances)
        graph.fund_flows = list(fund_flows)

        # ─── 1. Create Nodes from Entities ───
        self._build_nodes_from_entities(graph, entities)

        # ─── 2. Create Edges from Relationships ───
        self._build_edges_from_relationships(graph, relationships)

        # ─── 3. Attach Balances to Nodes ───
        self._attach_balances_to_nodes(graph, balances)

        # ─── 4. Create Fund Flow Edges ───
        self._build_fund_flow_edges(graph, fund_flows)

        # ─── 5. Ensure referenced nodes exist ───
        self._ensure_referenced_nodes(graph)

        return graph

    # ═══════════════════════════════════════════════════════════
    #  1. Nodes from Entities
    # ═══════════════════════════════════════════════════════════

    def _build_nodes_from_entities(
        self, graph: FinancialGraph, entities: List[Entity],
    ) -> None:
        """تحويل كل كيان إلى عقدة في الرسم"""
        for entity in entities:
            node_type = _ENTITY_TO_NODE_TYPE.get(
                entity.entity_type, NodeType.PROTOCOL
            )

            # بناء السمات
            attributes = self._build_node_attributes(entity)

            node = GraphNode(
                node_id=entity.entity_id,
                node_type=node_type,
                label=entity.name,
                entity_ref=entity.entity_id,
                attributes=attributes,
                contract_name=entity.contract_name,
                source_file=entity.source_file,
                line=entity.line_start,
            )
            graph.add_node(node)

    def _build_node_attributes(self, entity: Entity) -> Dict:
        """بناء سمات العقدة من بيانات الكيان"""
        attrs = {
            "entity_type": entity.entity_type.value,
            "confidence": entity.confidence,
        }

        # Token attributes
        if entity.token_type:
            attrs["token_type"] = entity.token_type
        if entity.token_symbol:
            attrs["token_symbol"] = entity.token_symbol
        if entity.decimals != 18:
            attrs["decimals"] = entity.decimals

        # Financial attributes
        if entity.total_supply_var:
            attrs["total_supply_var"] = entity.total_supply_var
        if entity.collateralization_ratio is not None:
            attrs["collateralization_ratio"] = entity.collateralization_ratio
        if entity.oracle_link:
            attrs["oracle_link"] = entity.oracle_link
        if entity.interest_rate_var:
            attrs["interest_rate_var"] = entity.interest_rate_var
        if entity.fee_percentage_var:
            attrs["fee_rate_var"] = entity.fee_percentage_var

        # Permissions
        if entity.owner_var:
            attrs["owner"] = entity.owner_var
        if entity.admin_roles:
            attrs["roles"] = entity.admin_roles
        if entity.access_modifiers:
            attrs["access_modifiers"] = entity.access_modifiers

        # Capabilities
        if entity.is_mintable:
            attrs["is_mintable"] = True
        if entity.is_burnable:
            attrs["is_burnable"] = True
        if entity.is_pausable:
            attrs["is_pausable"] = True
        if entity.is_upgradeable:
            attrs["is_upgradeable"] = True

        # Balance vars
        if entity.balance_vars:
            attrs["balance_vars"] = entity.balance_vars

        return attrs

    # ═══════════════════════════════════════════════════════════
    #  2. Edges from Relationships
    # ═══════════════════════════════════════════════════════════

    def _build_edges_from_relationships(
        self, graph: FinancialGraph, relationships: List[Relationship],
    ) -> None:
        """تحويل العلاقات إلى أضلاع في الرسم"""
        for rel in relationships:
            # تصنيف نوع الضلع
            if rel.relation_type in _FUND_FLOW_RELATIONS:
                edge_type = EdgeType.FUND_FLOW
            elif rel.relation_type in _ACCESS_RELATIONS:
                edge_type = EdgeType.ACCESS_CONTROL
            elif rel.relation_type in _ORACLE_RELATIONS:
                edge_type = EdgeType.PRICE_DEPENDENCY
            elif rel.relation_type in _STRUCTURAL_RELATIONS:
                edge_type = EdgeType.STRUCTURAL
            else:
                edge_type = EdgeType.DATA_FLOW

            # Build edge attributes
            attributes = {
                "relation_type": rel.relation_type.value,
            }
            if rel.condition:
                attributes["condition"] = rel.condition

            edge = GraphEdge(
                edge_id=self._next_edge_id(),
                source_node=rel.source_id,
                target_node=rel.target_id,
                edge_type=edge_type,
                label=rel.relation_type.value,
                attributes=attributes,
                token=rel.token_involved,
                amount_expr=rel.amount_expression,
                fee_expr=rel.fee_expression,
                required_role=rel.required_role,
                guarded_by=rel.modifier_guard,
                function_name=rel.function_name,
                line=rel.line,
                confidence=rel.confidence,
            )
            graph.add_edge(edge)

    # ═══════════════════════════════════════════════════════════
    #  3. Attach Balances to Nodes
    # ═══════════════════════════════════════════════════════════

    def _attach_balances_to_nodes(
        self, graph: FinancialGraph, balances: List[BalanceEntry],
    ) -> None:
        """ربط الأرصدة بالعقد المناسبة"""
        for balance in balances:
            node_id = balance.account_id
            if node_id in graph.nodes:
                key = f"{balance.balance_type}:{balance.token_id}"
                graph.nodes[node_id].balances[key] = balance.expression
            else:
                # Create placeholder node if needed
                # (will be cleaned up in ensure_referenced_nodes)
                pass

    # ═══════════════════════════════════════════════════════════
    #  4. Fund Flow Edges
    # ═══════════════════════════════════════════════════════════

    def _build_fund_flow_edges(
        self, graph: FinancialGraph, fund_flows: List[FundFlow],
    ) -> None:
        """بناء أضلاع التدفق المالي"""
        for flow in fund_flows:
            attributes = {
                "flow_type": flow.flow_type,
            }
            if flow.condition:
                attributes["condition"] = flow.condition

            # Determine direction
            direction = "unidirectional"
            if flow.flow_type == "swap":
                direction = "bidirectional"

            edge = GraphEdge(
                edge_id=self._next_edge_id(),
                source_node=flow.source_account,
                target_node=flow.target_account,
                edge_type=EdgeType.FUND_FLOW,
                label=f"{flow.flow_type}: {flow.token_id}",
                attributes=attributes,
                token=flow.token_id,
                amount_expr=flow.amount_expr,
                fee_expr=flow.fee_expr,
                direction=direction,
                function_name=flow.function_name,
                line=flow.line,
            )
            graph.add_edge(edge)

    # ═══════════════════════════════════════════════════════════
    #  5. Ensure Referenced Nodes Exist
    # ═══════════════════════════════════════════════════════════

    def _ensure_referenced_nodes(self, graph: FinancialGraph) -> None:
        """
        التأكد من وجود كل العقد المشار إليها في الأضلاع.
        إنشاء عقد placeholder للعقد الخارجية/المجهولة.
        """
        referenced_nodes = set()
        for edge in graph.edges.values():
            referenced_nodes.add(edge.source_node)
            referenced_nodes.add(edge.target_node)

        for node_id in referenced_nodes:
            if node_id not in graph.nodes:
                # Infer node type from ID prefix
                node_type = NodeType.ADDRESS
                label = node_id

                if node_id.startswith("contract:"):
                    node_type = NodeType.PROTOCOL
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("external:"):
                    node_type = NodeType.ADDRESS
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("account:"):
                    node_type = NodeType.ADDRESS
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("role:"):
                    node_type = NodeType.GOVERNANCE
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("oracle:"):
                    node_type = NodeType.ORACLE
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("token:"):
                    node_type = NodeType.TOKEN
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("fee_collector:"):
                    node_type = NodeType.PROTOCOL
                    label = "Fee Collector"
                elif node_id == "zero_address":
                    node_type = NodeType.ADDRESS
                    label = "Zero Address (Mint/Burn)"
                elif node_id.startswith("var:"):
                    node_type = NodeType.STATE_VARIABLE
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("debt:"):
                    node_type = NodeType.STATE_VARIABLE
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("collateral:"):
                    node_type = NodeType.STATE_VARIABLE
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("implementation:"):
                    node_type = NodeType.PROTOCOL
                    label = f"Impl: {node_id.split(':', 1)[1]}"
                elif node_id.startswith("governed:"):
                    node_type = NodeType.PROTOCOL
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("self:"):
                    node_type = NodeType.TOKEN
                    label = node_id.split(":", 1)[1]
                elif node_id.startswith("reward:"):
                    node_type = NodeType.STATE_VARIABLE
                    label = node_id.split(":", 1)[1]

                placeholder = GraphNode(
                    node_id=node_id,
                    node_type=node_type,
                    label=label,
                    attributes={"is_placeholder": True},
                )
                graph.add_node(placeholder)

    # ═══════════════════════════════════════════════════════════
    #  Utilities
    # ═══════════════════════════════════════════════════════════

    def merge_graphs(self, *graphs: FinancialGraph) -> FinancialGraph:
        """دمج عدة رسومات بيانية في رسم واحد"""
        merged = FinancialGraph()

        for g in graphs:
            # Merge nodes
            for nid, node in g.nodes.items():
                if nid not in merged.nodes:
                    merged.add_node(node)
                else:
                    # Merge attributes
                    merged.nodes[nid].attributes.update(node.attributes)
                    merged.nodes[nid].balances.update(node.balances)

            # Merge edges (re-ID to avoid conflicts)
            for eid, edge in g.edges.items():
                new_edge = GraphEdge(
                    edge_id=self._next_edge_id(),
                    source_node=edge.source_node,
                    target_node=edge.target_node,
                    edge_type=edge.edge_type,
                    label=edge.label,
                    attributes=edge.attributes.copy(),
                    token=edge.token,
                    amount_expr=edge.amount_expr,
                    fee_expr=edge.fee_expr,
                    direction=edge.direction,
                    required_role=edge.required_role,
                    guarded_by=edge.guarded_by,
                    function_name=edge.function_name,
                    line=edge.line,
                    confidence=edge.confidence,
                )
                merged.add_edge(new_edge)

            # Merge entities
            merged.entities.update(g.entities)
            merged.relationships.extend(g.relationships)
            merged.balances.extend(g.balances)
            merged.fund_flows.extend(g.fund_flows)
            merged.source_files.extend(g.source_files)

        # Deduplicate source files
        merged.source_files = list(set(merged.source_files))

        return merged
