"""
AGL State Extraction — Fund Mapper
خريطة الأموال والأرصدة

يبني خريطة شاملة لكل:
  - رصيد لكل حساب لكل توكن
  - سيولة البركة (Pool Liquidity)
  - مراكز الدين والضمان (Debt/Collateral Positions)
  - تدفقات رأس المال (Capital Flows)
"""

import re
from typing import Dict, List, Optional, Set, Tuple

from .models import (
    Entity, EntityType, BalanceEntry, FundFlow,
    Relationship, RelationType,
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
#  Patterns for balance/flow extraction
# ═══════════════════════════════════════════════════════════════

# Balance mapping patterns: mapping(address => uint) balances
_RE_BALANCE_MAPPING = re.compile(
    r'mapping\s*\(\s*address\s*=>\s*(?:uint\d*|int\d*)\s*\)\s+'
    r'(?:public\s+|private\s+|internal\s+)?'
    r'(\w+)',
    re.MULTILINE
)

# Nested balance mapping: mapping(address => mapping(address => uint))
_RE_NESTED_BALANCE = re.compile(
    r'mapping\s*\(\s*address\s*=>\s*mapping\s*\(\s*address\s*=>\s*(?:uint\d*|int\d*)\s*\)\s*\)\s+'
    r'(?:public\s+|private\s+|internal\s+)?'
    r'(\w+)',
    re.MULTILINE
)

# Balance update patterns (increments/decrements)
_RE_BALANCE_INC = re.compile(
    r'(\w+)\s*\[\s*(\w+)\s*\]\s*\+=\s*([^;]+)',
    re.MULTILINE
)
_RE_BALANCE_DEC = re.compile(
    r'(\w+)\s*\[\s*(\w+)\s*\]\s*-=\s*([^;]+)',
    re.MULTILINE
)
_RE_BALANCE_SET = re.compile(
    r'(\w+)\s*\[\s*(\w+)\s*\]\s*=\s*([^;]+)',
    re.MULTILINE
)

# SafeTransfer / transfer function call
_RE_SAFE_TRANSFER = re.compile(
    r'(\w+)\s*\.\s*(?:safe)?[Tt]ransfer(?:From)?\s*\(\s*([^,]+)\s*,\s*([^,\)]+)(?:\s*,\s*([^)]+))?\s*\)',
    re.MULTILINE
)

# Mint/Burn amounts
_RE_MINT_AMOUNT = re.compile(
    r'_?mint\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
    re.MULTILINE
)
_RE_BURN_AMOUNT = re.compile(
    r'_?burn\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
    re.MULTILINE
)

# Total supply changes
_RE_TOTAL_SUPPLY_INC = re.compile(r'(_?totalSupply|_totalSupply)\s*\+=\s*([^;]+)', re.MULTILINE)
_RE_TOTAL_SUPPLY_DEC = re.compile(r'(_?totalSupply|_totalSupply)\s*-=\s*([^;]+)', re.MULTILINE)


class FundMapper:
    """
    يبني خريطة الأموال الكاملة:
    1. Balance Ledger — سجل الأرصدة لكل عنوان/توكن
    2. Capital Flow Graph — رسم تدفق رأس المال
    3. Debt/Collateral Positions — مراكز الدين والضمان
    """

    def __init__(self):
        self._flow_counter = 0
        self._balance_counter = 0

    def _next_flow_id(self) -> str:
        self._flow_counter += 1
        return f"flow_{self._flow_counter}"

    # ═══════════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════════

    def map_funds(
        self,
        entities: List[Entity],
        contracts: List[ParsedContract],
        relationships: List[Relationship],
    ) -> Tuple[List[BalanceEntry], List[FundFlow]]:
        """
        استخراج خريطة الأموال الكاملة.

        Returns:
            (balance_entries, fund_flows)
        """
        balances: List[BalanceEntry] = []
        flows: List[FundFlow] = []

        entity_map = {e.entity_id: e for e in entities}

        for contract in contracts:
            if contract.contract_type == "interface":
                continue

            contract_id = f"contract:{contract.name}"

            # ─── 1. Extract Balance Ledger ───
            contract_balances = self._extract_balance_ledger(contract, entity_map)
            balances.extend(contract_balances)

            # ─── 2. Extract Fund Flows from Functions ───
            contract_flows = self._extract_fund_flows(contract, entity_map)
            flows.extend(contract_flows)

            # ─── 3. Debt/Collateral Positions ───
            position_balances = self._extract_position_balances(contract, entity_map)
            balances.extend(position_balances)

        # ─── 4. Derive Implied Flows from Relationships ───
        implied_flows = self._derive_flows_from_relationships(relationships)
        flows.extend(implied_flows)

        return balances, flows

    # ═══════════════════════════════════════════════════════════
    #  1. Balance Ledger Extraction
    # ═══════════════════════════════════════════════════════════

    def _extract_balance_ledger(
        self,
        contract: ParsedContract,
        entity_map: Dict[str, Entity],
    ) -> List[BalanceEntry]:
        """استخراج سجل الأرصدة — كل mapping(address => uint) هو دفتر أرصدة محتمل"""
        entries: List[BalanceEntry] = []
        contract_id = f"contract:{contract.name}"

        # ─── Direct balance mappings ───
        for vname, svar in contract.state_vars.items():
            vname_lower = vname.lower()

            # Balance-type mappings
            if svar.is_mapping:
                balance_type = self._classify_balance_type(vname)
                if balance_type:
                    entries.append(BalanceEntry(
                        account_id=contract_id,
                        token_id=self._infer_token_from_context(contract, vname),
                        balance_var=f"{contract.name}.{vname}",
                        balance_type=balance_type,
                        expression=f"{vname}[account]",
                    ))

            # Scalar balance variables (totalSupply, reserve, etc.)
            elif not svar.is_mapping and any(
                p in vname_lower for p in [
                    "supply", "reserve", "liquidity", "totaldeposit",
                    "totalborrow", "totalstaked", "totalassets",
                ]
            ):
                entries.append(BalanceEntry(
                    account_id=contract_id,
                    token_id=self._infer_token_from_context(contract, vname),
                    balance_var=f"{contract.name}.{vname}",
                    balance_type="aggregate",
                    expression=vname,
                ))

        return entries

    def _classify_balance_type(self, var_name: str) -> Optional[str]:
        """تصنيف نوع متغير الرصيد"""
        vl = var_name.lower()

        if any(p in vl for p in ["balance", "_balances", "shares"]):
            return "balance"
        elif any(p in vl for p in ["debt", "borrow", "borrowed", "loan"]):
            return "debt"
        elif any(p in vl for p in ["collateral", "deposit", "staked"]):
            return "collateral"
        elif any(p in vl for p in ["reward", "earned", "pending"]):
            return "rewards"
        elif any(p in vl for p in ["allowance", "approved"]):
            return "allowance"
        elif any(p in vl for p in ["liquidity", "reserve"]):
            return "liquidity"
        elif any(p in vl for p in ["amount", "fund", "supply"]):
            return "balance"

        return None

    def _infer_token_from_context(self, contract: ParsedContract, var_name: str) -> str:
        """استنتاج التوكن المرتبط من سياق العقد"""
        # البحث عن متغير token/asset
        for vname in contract.state_vars:
            vl = vname.lower()
            if vl in ("token", "asset", "_token", "_asset", "underlying",
                       "token0", "token1", "stakingtoken", "rewardstoken"):
                return f"{contract.name}.{vname}"

        # من الأوراثة
        if any("ERC20" in p for p in contract.inherits):
            return f"self:{contract.name}"

        return f"token:{contract.name}"

    # ═══════════════════════════════════════════════════════════
    #  2. Fund Flow Extraction from Functions
    # ═══════════════════════════════════════════════════════════

    def _extract_fund_flows(
        self,
        contract: ParsedContract,
        entity_map: Dict[str, Entity],
    ) -> List[FundFlow]:
        """استخراج تدفقات الأموال من الدوال"""
        flows: List[FundFlow] = []
        contract_id = f"contract:{contract.name}"

        for fname, func in contract.functions.items():
            body = func.raw_body or ""
            if not body:
                continue

            # ─── Balance increments/decrements ───
            # These represent internal fund movements
            inc_decs = self._extract_balance_changes(body, contract.name, fname, func)
            flows.extend(inc_decs)

            # ─── External token transfers ───
            for m in _RE_SAFE_TRANSFER.finditer(body):
                token_var = m.group(1)
                recipient = m.group(2).strip()
                amount = m.group(3).strip() if m.group(3) else ""
                # transferFrom has 3 args: from, to, amount
                if m.group(4):
                    sender = recipient
                    recipient = m.group(3).strip()
                    amount = m.group(4).strip()
                else:
                    sender = contract.name

                flows.append(FundFlow(
                    flow_id=self._next_flow_id(),
                    source_account=f"account:{sender}",
                    target_account=f"account:{recipient}",
                    token_id=f"token:{token_var}",
                    amount_expr=amount[:100],
                    function_name=fname,
                    flow_type="transfer",
                    line=func.line_start,
                ))

            # ─── Mint flows ───
            for m in _RE_MINT_AMOUNT.finditer(body):
                recipient = m.group(1).strip()
                amount = m.group(2).strip()
                flows.append(FundFlow(
                    flow_id=self._next_flow_id(),
                    source_account=f"zero_address",
                    target_account=f"account:{recipient}",
                    token_id=f"self:{contract.name}",
                    amount_expr=amount[:100],
                    function_name=fname,
                    flow_type="mint",
                    line=func.line_start,
                ))

            # ─── Burn flows ───
            for m in _RE_BURN_AMOUNT.finditer(body):
                source = m.group(1).strip()
                amount = m.group(2).strip()
                flows.append(FundFlow(
                    flow_id=self._next_flow_id(),
                    source_account=f"account:{source}",
                    target_account=f"zero_address",
                    token_id=f"self:{contract.name}",
                    amount_expr=amount[:100],
                    function_name=fname,
                    flow_type="burn",
                    line=func.line_start,
                ))

        return flows

    def _extract_balance_changes(
        self, body: str, contract_name: str,
        fname: str, func: "ParsedFunction",
    ) -> List[FundFlow]:
        """استخراج تغييرات الأرصدة (increment/decrement) كتدفقات"""
        flows: List[FundFlow] = []

        # Increments: balances[addr] += amount
        for m in _RE_BALANCE_INC.finditer(body):
            var = m.group(1)
            account = m.group(2).strip()
            amount = m.group(3).strip()
            flows.append(FundFlow(
                flow_id=self._next_flow_id(),
                source_account=f"contract:{contract_name}",
                target_account=f"account:{account}",
                token_id=f"var:{contract_name}.{var}",
                amount_expr=amount[:100],
                function_name=fname,
                flow_type="credit",
                line=func.line_start,
            ))

        # Decrements: balances[addr] -= amount
        for m in _RE_BALANCE_DEC.finditer(body):
            var = m.group(1)
            account = m.group(2).strip()
            amount = m.group(3).strip()
            flows.append(FundFlow(
                flow_id=self._next_flow_id(),
                source_account=f"account:{account}",
                target_account=f"contract:{contract_name}",
                token_id=f"var:{contract_name}.{var}",
                amount_expr=amount[:100],
                function_name=fname,
                flow_type="debit",
                line=func.line_start,
            ))

        return flows

    # ═══════════════════════════════════════════════════════════
    #  3. Debt/Collateral Position Extraction
    # ═══════════════════════════════════════════════════════════

    def _extract_position_balances(
        self,
        contract: ParsedContract,
        entity_map: Dict[str, Entity],
    ) -> List[BalanceEntry]:
        """استخراج مراكز الدين والضمان"""
        entries: List[BalanceEntry] = []
        contract_id = f"contract:{contract.name}"

        for vname, svar in contract.state_vars.items():
            vl = vname.lower()

            # Debt positions
            if svar.is_mapping and any(p in vl for p in ["debt", "borrow", "loan"]):
                entries.append(BalanceEntry(
                    account_id=contract_id,
                    token_id=self._infer_token_from_context(contract, vname),
                    balance_var=f"{contract.name}.{vname}",
                    balance_type="debt",
                    expression=f"{vname}[borrower]",
                ))

            # Collateral positions
            elif svar.is_mapping and any(p in vl for p in ["collateral", "deposit"]):
                entries.append(BalanceEntry(
                    account_id=contract_id,
                    token_id=self._infer_token_from_context(contract, vname),
                    balance_var=f"{contract.name}.{vname}",
                    balance_type="collateral",
                    expression=f"{vname}[depositor]",
                ))

            # Staking positions
            elif svar.is_mapping and any(p in vl for p in ["staked", "stake"]):
                entries.append(BalanceEntry(
                    account_id=contract_id,
                    token_id=self._infer_token_from_context(contract, vname),
                    balance_var=f"{contract.name}.{vname}",
                    balance_type="staked",
                    expression=f"{vname}[staker]",
                ))

        return entries

    # ═══════════════════════════════════════════════════════════
    #  4. Implied Flows from Relationships
    # ═══════════════════════════════════════════════════════════

    def _derive_flows_from_relationships(
        self, relationships: List[Relationship],
    ) -> List[FundFlow]:
        """اشتقاق تدفقات ضمنية من العلاقات المكتشفة"""
        flows: List[FundFlow] = []

        for rel in relationships:
            flow_type_map = {
                RelationType.TRANSFERS_TO: "transfer",
                RelationType.MINTS_TO: "mint",
                RelationType.BURNS_FROM: "burn",
                RelationType.DEPOSITS_INTO: "deposit",
                RelationType.WITHDRAWS_FROM: "withdraw",
                RelationType.BORROWS_FROM: "borrow",
                RelationType.REPAYS_TO: "repay",
                RelationType.LIQUIDATES: "liquidation",
                RelationType.SWAPS_THROUGH: "swap",
                RelationType.FEE_TO: "fee",
            }

            if rel.relation_type in flow_type_map:
                flows.append(FundFlow(
                    flow_id=self._next_flow_id(),
                    source_account=rel.source_id,
                    target_account=rel.target_id,
                    token_id=rel.token_involved or "unknown",
                    amount_expr=rel.amount_expression or "variable",
                    function_name=rel.function_name,
                    flow_type=flow_type_map[rel.relation_type],
                    fee_expr=rel.fee_expression,
                    condition=rel.condition,
                    line=rel.line,
                ))

        return flows

    # ═══════════════════════════════════════════════════════════
    #  Summary
    # ═══════════════════════════════════════════════════════════

    def get_fund_summary(
        self,
        balances: List[BalanceEntry],
        flows: List[FundFlow],
    ) -> Dict:
        """ملخص خريطة الأموال"""
        balance_types = {}
        for b in balances:
            balance_types[b.balance_type] = balance_types.get(b.balance_type, 0) + 1

        flow_types = {}
        for f in flows:
            flow_types[f.flow_type] = flow_types.get(f.flow_type, 0) + 1

        # Unique accounts
        accounts = set()
        for b in balances:
            accounts.add(b.account_id)
        for f in flows:
            accounts.add(f.source_account)
            accounts.add(f.target_account)

        # Unique tokens
        tokens = set()
        for b in balances:
            tokens.add(b.token_id)
        for f in flows:
            tokens.add(f.token_id)

        return {
            "total_balances": len(balances),
            "total_flows": len(flows),
            "unique_accounts": len(accounts),
            "unique_tokens": len(tokens),
            "balance_types": balance_types,
            "flow_types": flow_types,
        }
