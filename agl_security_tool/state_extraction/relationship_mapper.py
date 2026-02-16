"""
AGL State Extraction — Relationship Mapper
محلل العلاقات بين الكيانات المالية

يستخرج ويصنف العلاقات بين الكيانات:
  - Access Control: من يملك الصلاحية لاستدعاء ماذا
  - Fund Flow: من يستطيع تحريك الأموال وأين
  - Price Dependencies: تبعيات الأسعار والأوراكل
  - Structural: التوارث، الوكالة، المكتبات
"""

import re
from typing import Dict, List, Optional, Set, Tuple

from .models import (
    Entity, EntityType, Relationship, RelationType,
)

import sys
from pathlib import Path
_TOOL_DIR = Path(__file__).parent.parent.resolve()
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

try:
    from detectors import ParsedContract, ParsedFunction, StateVar, OpType
except ImportError:
    from agl_security_tool.detectors import ParsedContract, ParsedFunction, StateVar, OpType


# ═══════════════════════════════════════════════════════════════
#  Regex patterns for relationship detection
# ═══════════════════════════════════════════════════════════════

# Transfer patterns
_RE_TRANSFER = re.compile(
    r'(\w[\w.\[\]]*)\s*\.\s*(transfer|transferFrom|safeTransfer|safeTransferFrom)\s*\(',
    re.MULTILINE
)
_RE_ETH_TRANSFER = re.compile(
    r'(\w[\w.\[\]]*)\s*\.\s*(call|transfer|send)\s*[\({]',
    re.MULTILINE
)

# Mint/Burn
_RE_MINT = re.compile(r'_?mint\s*\(([^)]*)\)', re.MULTILINE)
_RE_BURN = re.compile(r'_?burn\s*\(([^)]*)\)', re.MULTILINE)

# Oracle reads
_RE_ORACLE_READ = re.compile(
    r'(\w+)\s*\.\s*(latestRoundData|latestAnswer|getPrice|consult|observe|slot0)\s*\(',
    re.MULTILINE
)
_RE_PRICE_FEED = re.compile(
    r'(\w+)\s*=\s*(?:I?AggregatorV\d+|I?ChainlinkOracle|priceFeed)',
    re.MULTILINE
)

# Approval patterns
_RE_APPROVE = re.compile(
    r'(\w[\w.\[\]]*)\s*\.\s*(approve|safeApprove|safeIncreaseAllowance)\s*\(',
    re.MULTILINE
)

# DelegateCall
_RE_DELEGATECALL = re.compile(
    r'(\w[\w.\[\]]*)\s*\.\s*delegatecall\s*[\({]',
    re.MULTILINE
)

# Role management
_RE_GRANT_ROLE = re.compile(
    r'(grantRole|_grantRole|_setupRole)\s*\(([^)]*)\)',
    re.MULTILINE
)
_RE_REVOKE_ROLE = re.compile(
    r'(revokeRole|_revokeRole|renounceRole)\s*\(([^)]*)\)',
    re.MULTILINE
)

# Owner transfer
_RE_TRANSFER_OWNERSHIP = re.compile(
    r'(transferOwnership|_transferOwnership)\s*\(([^)]*)\)',
    re.MULTILINE
)

# Deposit/Withdraw
_RE_DEPOSIT_CALL = re.compile(
    r'(\w[\w.\[\]]*)\s*\.\s*(deposit|supply|stake)\s*\(',
    re.MULTILINE
)
_RE_WITHDRAW_CALL = re.compile(
    r'(\w[\w.\[\]]*)\s*\.\s*(withdraw|redeem|unstake)\s*\(',
    re.MULTILINE
)

# Borrow/Repay
_RE_BORROW_CALL = re.compile(
    r'(\w[\w.\[\]]*)\s*\.\s*(borrow|flashLoan|flash)\s*\(',
    re.MULTILINE
)
_RE_REPAY_CALL = re.compile(
    r'(\w[\w.\[\]]*)\s*\.\s*(repay|repayBorrow)\s*\(',
    re.MULTILINE
)

# Liquidation
_RE_LIQUIDATE = re.compile(
    r'(\w[\w.\[\]]*)\s*\.\s*(liquidate|liquidationCall|liquidateBorrow)\s*\(',
    re.MULTILINE
)

# Swap
_RE_SWAP = re.compile(
    r'(\w[\w.\[\]]*)\s*\.\s*(swap|exactInputSingle|exactInput|exactOutputSingle|exactOutput)\s*\(',
    re.MULTILINE
)


class RelationshipMapper:
    """
    محلل العلاقات بين الكيانات المالية.

    يتلقى قائمة كيانات (Entity) وعقود محللة (ParsedContract)
    ويبني خريطة كاملة للعلاقات.
    """

    def __init__(self):
        self._rel_counter = 0

    def _next_rel_id(self) -> str:
        self._rel_counter += 1
        return f"rel_{self._rel_counter}"

    # ═══════════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════════

    def map_relationships(
        self,
        entities: List[Entity],
        contracts: List[ParsedContract],
    ) -> List[Relationship]:
        """
        استخراج كل العلاقات بين الكيانات.
        يحلل:
          1. Access Control — من يملك ماذا
          2. Fund Flow — من يحرك الأموال
          3. Price Dependencies — تبعيات الأسعار
          4. Structural — التوارث والوكالة
        """
        relationships: List[Relationship] = []

        # بناء خرائط مرجعية
        entity_map = {e.entity_id: e for e in entities}
        contract_map = {c.name: c for c in contracts}

        # ─── 1. Structural Relationships (التوارث والوكالة) ───
        relationships.extend(
            self._extract_structural_relationships(contracts, entity_map)
        )

        # ─── 2. Access Control Relationships (صلاحيات الوصول) ───
        relationships.extend(
            self._extract_access_relationships(contracts, entity_map)
        )

        # ─── 3. Fund Flow Relationships (تدفق الأموال) ───
        relationships.extend(
            self._extract_fund_flow_relationships(contracts, entity_map)
        )

        # ─── 4. Price/Oracle Dependencies (تبعيات الأسعار) ───
        relationships.extend(
            self._extract_oracle_relationships(contracts, entity_map)
        )

        return relationships

    # ═══════════════════════════════════════════════════════════
    #  1. Structural Relationships
    # ═══════════════════════════════════════════════════════════

    def _extract_structural_relationships(
        self,
        contracts: List[ParsedContract],
        entity_map: Dict[str, Entity],
    ) -> List[Relationship]:
        """استخراج علاقات التوارث والوكالة والمكتبات"""
        rels: List[Relationship] = []

        for contract in contracts:
            source_id = f"contract:{contract.name}"

            # ─── Inheritance ───
            for parent in contract.inherits:
                target_id = f"contract:{parent}"
                rels.append(Relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=RelationType.INHERITS_FROM,
                    confidence=1.0,
                    line=contract.line_start,
                ))

            # ─── Using...for (Library) ───
            for u in contract.using_for:
                lib_name = u.get("library", "")
                if lib_name:
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"contract:{lib_name}",
                        relation_type=RelationType.USES_LIBRARY,
                        confidence=0.90,
                    ))

            # ─── DelegateCall ───
            for fname, func in contract.functions.items():
                if func.has_delegatecall:
                    body = func.raw_body or ""
                    for m in _RE_DELEGATECALL.finditer(body):
                        target = m.group(1)
                        rels.append(Relationship(
                            source_id=source_id,
                            target_id=f"external:{target}",
                            relation_type=RelationType.DELEGATES_TO,
                            function_name=fname,
                            line=func.line_start,
                            confidence=0.85,
                        ))

            # ─── Proxy detection ───
            if contract.is_upgradeable or any(
                p in " ".join(contract.inherits).lower()
                for p in ["proxy", "upgradeable", "uups"]
            ):
                rels.append(Relationship(
                    source_id=source_id,
                    target_id=f"implementation:{contract.name}",
                    relation_type=RelationType.PROXIED_BY,
                    confidence=0.80,
                ))

        return rels

    # ═══════════════════════════════════════════════════════════
    #  2. Access Control Relationships
    # ═══════════════════════════════════════════════════════════

    def _extract_access_relationships(
        self,
        contracts: List[ParsedContract],
        entity_map: Dict[str, Entity],
    ) -> List[Relationship]:
        """
        استخراج علاقات التحكم في الوصول:
        - Owner relationships
        - Role-based access
        - Function permissions (who can call what)
        - Pause capabilities
        """
        rels: List[Relationship] = []

        for contract in contracts:
            source_id = f"contract:{contract.name}"

            # ─── Owner Variable ───
            for vname, svar in contract.state_vars.items():
                if vname in ("owner", "_owner"):
                    rels.append(Relationship(
                        source_id=f"role:owner",
                        target_id=source_id,
                        relation_type=RelationType.OWNS,
                        confidence=0.95,
                    ))

            # ─── Role Grants in Functions ───
            for fname, func in contract.functions.items():
                body = func.raw_body or ""

                # grantRole / _setupRole
                for m in _RE_GRANT_ROLE.finditer(body):
                    args = m.group(2).strip()
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"role:{args.split(',')[0].strip()}",
                        relation_type=RelationType.ROLE_GRANTS,
                        function_name=fname,
                        line=func.line_start,
                        confidence=0.90,
                    ))

                # transferOwnership
                for m in _RE_TRANSFER_OWNERSHIP.finditer(body):
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"role:owner",
                        relation_type=RelationType.OWNS,
                        function_name=fname,
                        line=func.line_start,
                        confidence=0.85,
                    ))

            # ─── Function-Level Permissions ───
            for fname, func in contract.functions.items():
                if func.visibility not in ("external", "public"):
                    continue

                # Check modifiers for access control
                for mod in func.modifiers:
                    if mod in (
                        "onlyOwner", "onlyAdmin", "onlyRole", "onlyGovernance",
                        "onlyMinter", "onlyOperator", "authorized",
                    ):
                        rels.append(Relationship(
                            source_id=f"role:{mod}",
                            target_id=source_id,
                            relation_type=RelationType.CAN_CALL,
                            function_name=fname,
                            modifier_guard=mod,
                            confidence=0.90,
                        ))

                    # Pause capability
                    if mod in ("whenNotPaused", "whenPaused"):
                        rels.append(Relationship(
                            source_id=f"role:pauser",
                            target_id=source_id,
                            relation_type=RelationType.CAN_PAUSE,
                            function_name=fname,
                            modifier_guard=mod,
                            confidence=0.85,
                        ))

                # Check body for access control patterns
                if func.has_access_control and not func.modifiers:
                    body = func.raw_body or ""
                    if "msg.sender" in body and ("==" in body or "require" in body):
                        rels.append(Relationship(
                            source_id=f"role:restricted",
                            target_id=source_id,
                            relation_type=RelationType.CAN_CALL,
                            function_name=fname,
                            condition="msg.sender check",
                            confidence=0.70,
                        ))

            # ─── Governance Control ───
            entity = entity_map.get(source_id)
            if entity and entity.entity_type == EntityType.GOVERNANCE:
                # Governance contracts govern other contracts
                for fname in contract.functions:
                    if fname in ("execute", "executeTransaction", "executeOperations"):
                        rels.append(Relationship(
                            source_id=source_id,
                            target_id=f"governed:targets",
                            relation_type=RelationType.GOVERNS,
                            function_name=fname,
                            confidence=0.80,
                        ))

        return rels

    # ═══════════════════════════════════════════════════════════
    #  3. Fund Flow Relationships
    # ═══════════════════════════════════════════════════════════

    def _extract_fund_flow_relationships(
        self,
        contracts: List[ParsedContract],
        entity_map: Dict[str, Entity],
    ) -> List[Relationship]:
        """
        استخراج علاقات تدفق الأموال:
        - Token transfers
        - Deposits/Withdrawals
        - Borrows/Repays
        - Liquidations
        - Swaps
        - Mint/Burn
        - Fee flows
        """
        rels: List[Relationship] = []

        for contract in contracts:
            source_id = f"contract:{contract.name}"

            for fname, func in contract.functions.items():
                body = func.raw_body or ""
                if not body:
                    continue

                guard_modifier = ""
                for mod in func.modifiers:
                    if mod in ("onlyOwner", "onlyAdmin", "onlyRole", "nonReentrant"):
                        guard_modifier = mod

                # ─── ERC20 Transfers ───
                for m in _RE_TRANSFER.finditer(body):
                    target_obj = m.group(1)
                    method = m.group(2)
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"external:{target_obj}",
                        relation_type=RelationType.TRANSFERS_TO,
                        function_name=fname,
                        token_involved=target_obj,
                        line=func.line_start,
                        modifier_guard=guard_modifier,
                        confidence=0.90,
                    ))

                # ─── ETH Transfers ───
                for m in _RE_ETH_TRANSFER.finditer(body):
                    target_obj = m.group(1)
                    method = m.group(2)
                    if method in ("call", "transfer", "send"):
                        # Check if it sends value
                        context = body[max(0, m.start()-50):m.end()+100]
                        if "value" in context or method in ("transfer", "send"):
                            rels.append(Relationship(
                                source_id=source_id,
                                target_id=f"external:{target_obj}",
                                relation_type=RelationType.TRANSFERS_TO,
                                function_name=fname,
                                token_involved="ETH",
                                amount_expression=self._extract_amount_expr(context),
                                line=func.line_start,
                                modifier_guard=guard_modifier,
                                confidence=0.85,
                            ))

                # ─── Mint ───
                for m in _RE_MINT.finditer(body):
                    args = m.group(1).strip()
                    parts = [p.strip() for p in args.split(",")]
                    target = parts[0] if parts else "unknown"
                    amount = parts[1] if len(parts) > 1 else "unknown"
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"account:{target}",
                        relation_type=RelationType.MINTS_TO,
                        function_name=fname,
                        amount_expression=amount,
                        line=func.line_start,
                        confidence=0.90,
                    ))

                # ─── Burn ───
                for m in _RE_BURN.finditer(body):
                    args = m.group(1).strip()
                    parts = [p.strip() for p in args.split(",")]
                    source = parts[0] if parts else "unknown"
                    amount = parts[1] if len(parts) > 1 else (parts[0] if parts else "unknown")
                    rels.append(Relationship(
                        source_id=f"account:{source}",
                        target_id=source_id,
                        relation_type=RelationType.BURNS_FROM,
                        function_name=fname,
                        amount_expression=amount,
                        line=func.line_start,
                        confidence=0.90,
                    ))

                # ─── Deposit ───
                for m in _RE_DEPOSIT_CALL.finditer(body):
                    target_obj = m.group(1)
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"external:{target_obj}",
                        relation_type=RelationType.DEPOSITS_INTO,
                        function_name=fname,
                        line=func.line_start,
                        confidence=0.85,
                    ))

                # ─── Withdraw ───
                for m in _RE_WITHDRAW_CALL.finditer(body):
                    target_obj = m.group(1)
                    rels.append(Relationship(
                        source_id=f"external:{target_obj}",
                        target_id=source_id,
                        relation_type=RelationType.WITHDRAWS_FROM,
                        function_name=fname,
                        line=func.line_start,
                        confidence=0.85,
                    ))

                # ─── Borrow ───
                for m in _RE_BORROW_CALL.finditer(body):
                    target_obj = m.group(1)
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"external:{target_obj}",
                        relation_type=RelationType.BORROWS_FROM,
                        function_name=fname,
                        line=func.line_start,
                        confidence=0.80,
                    ))

                # ─── Repay ───
                for m in _RE_REPAY_CALL.finditer(body):
                    target_obj = m.group(1)
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"external:{target_obj}",
                        relation_type=RelationType.REPAYS_TO,
                        function_name=fname,
                        line=func.line_start,
                        confidence=0.80,
                    ))

                # ─── Liquidation ───
                for m in _RE_LIQUIDATE.finditer(body):
                    target_obj = m.group(1)
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"external:{target_obj}",
                        relation_type=RelationType.LIQUIDATES,
                        function_name=fname,
                        line=func.line_start,
                        confidence=0.80,
                    ))

                # ─── Swap ───
                for m in _RE_SWAP.finditer(body):
                    target_obj = m.group(1)
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"external:{target_obj}",
                        relation_type=RelationType.SWAPS_THROUGH,
                        function_name=fname,
                        line=func.line_start,
                        confidence=0.80,
                    ))

                # ─── Fee Extraction ───
                self._extract_fee_relationships(
                    body, source_id, fname, func, rels
                )

        return rels

    # ═══════════════════════════════════════════════════════════
    #  4. Oracle/Price Dependencies
    # ═══════════════════════════════════════════════════════════

    def _extract_oracle_relationships(
        self,
        contracts: List[ParsedContract],
        entity_map: Dict[str, Entity],
    ) -> List[Relationship]:
        """استخراج تبعيات الأسعار والأوراكل"""
        rels: List[Relationship] = []

        for contract in contracts:
            source_id = f"contract:{contract.name}"

            # ─── Oracle state variables ───
            for vname, svar in contract.state_vars.items():
                vname_lower = vname.lower()
                if any(p in vname_lower for p in [
                    "oracle", "pricefeed", "feed", "aggregator", "twap"
                ]):
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"oracle:{vname}",
                        relation_type=RelationType.READS_PRICE_FROM,
                        confidence=0.85,
                    ))

            # ─── Oracle calls in functions ───
            for fname, func in contract.functions.items():
                body = func.raw_body or ""
                if not body:
                    continue

                for m in _RE_ORACLE_READ.finditer(body):
                    oracle_var = m.group(1)
                    oracle_func = m.group(2)
                    rels.append(Relationship(
                        source_id=source_id,
                        target_id=f"oracle:{oracle_var}",
                        relation_type=RelationType.READS_PRICE_FROM,
                        function_name=fname,
                        line=func.line_start,
                        confidence=0.90,
                    ))

                # Price feed assignment
                for m in _RE_PRICE_FEED.finditer(body):
                    feed_var = m.group(1)
                    rels.append(Relationship(
                        source_id=f"oracle:{feed_var}",
                        target_id=source_id,
                        relation_type=RelationType.PRICE_FEED_FOR,
                        function_name=fname,
                        line=func.line_start,
                        confidence=0.80,
                    ))

        return rels

    # ═══════════════════════════════════════════════════════════
    #  Fee Extraction Helpers
    # ═══════════════════════════════════════════════════════════

    def _extract_fee_relationships(
        self, body: str, source_id: str,
        fname: str, func: "ParsedFunction",
        rels: List[Relationship],
    ) -> None:
        """استخراج علاقات الرسوم من جسم الدالة"""
        # التقاط حسابات الرسوم
        fee_patterns = [
            re.compile(r'(\w+Fee)\s*=\s*([^;]+);'),
            re.compile(r'fee\s*=\s*([^;]+);'),
            re.compile(r'(\w+)\s*\*\s*\w*[fF]ee\w*\s*/'),
            re.compile(r'(\w+)\s*/\s*\w*[fF]ee\w*'),
        ]
        for pat in fee_patterns:
            for m in pat.finditer(body):
                rels.append(Relationship(
                    source_id=source_id,
                    target_id=f"fee_collector:{source_id}",
                    relation_type=RelationType.FEE_TO,
                    function_name=fname,
                    fee_expression=m.group(0).strip()[:100],
                    line=func.line_start,
                    confidence=0.65,
                ))
                break  # واحدة فقط لكل دالة

    def _extract_amount_expr(self, context: str) -> str:
        """استخراج تعبير المبلغ من سياق الكود"""
        # نبحث عن value: X أو (X) بعد الدالة
        m = re.search(r'value\s*:\s*([^,}\)]+)', context)
        if m:
            return m.group(1).strip()[:80]
        m = re.search(r'\(\s*([^,\)]+)', context)
        if m:
            return m.group(1).strip()[:80]
        return ""

    # ═══════════════════════════════════════════════════════════
    #  Summary
    # ═══════════════════════════════════════════════════════════

    def get_relationship_summary(self, relationships: List[Relationship]) -> Dict:
        """ملخص العلاقات المستخرجة"""
        type_counts = {}
        for r in relationships:
            t = r.relation_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        access_rels = [
            r for r in relationships
            if r.relation_type in (
                RelationType.OWNS, RelationType.ADMIN_OF, RelationType.CAN_CALL,
                RelationType.CAN_PAUSE, RelationType.CAN_UPGRADE,
                RelationType.ROLE_GRANTS, RelationType.GOVERNS,
            )
        ]
        fund_rels = [
            r for r in relationships
            if r.relation_type in (
                RelationType.TRANSFERS_TO, RelationType.MINTS_TO,
                RelationType.BURNS_FROM, RelationType.DEPOSITS_INTO,
                RelationType.WITHDRAWS_FROM, RelationType.BORROWS_FROM,
                RelationType.REPAYS_TO, RelationType.LIQUIDATES,
                RelationType.SWAPS_THROUGH, RelationType.FEE_TO,
            )
        ]
        oracle_rels = [
            r for r in relationships
            if r.relation_type in (
                RelationType.PRICE_FEED_FOR, RelationType.READS_PRICE_FROM,
                RelationType.TWAP_SOURCE,
            )
        ]
        struct_rels = [
            r for r in relationships
            if r.relation_type in (
                RelationType.INHERITS_FROM, RelationType.DELEGATES_TO,
                RelationType.PROXIED_BY, RelationType.USES_LIBRARY,
                RelationType.WRAPS, RelationType.BACKED_BY,
            )
        ]

        return {
            "total_relationships": len(relationships),
            "by_type": type_counts,
            "categories": {
                "access_control": len(access_rels),
                "fund_flow": len(fund_rels),
                "oracle_price": len(oracle_rels),
                "structural": len(struct_rels),
            },
        }
