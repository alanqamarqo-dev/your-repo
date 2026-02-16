"""
AGL State Extraction — Entity Extractor
مستخرج الكيانات المالية من العقود الذكية

يحلل كود Solidity ويستخرج:
  - Tokens (ERC20/ERC721/ERC1155)
  - Pools (AMM, Lending)
  - Vaults (ERC4626, Yield)
  - Oracles (Chainlink, TWAP)
  - Governance (DAO, Timelock, AccessControl)
  - Staking, Bridge, Router
  - Debt/Collateral positions
  - Balance mappings
  - Access control structures
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass

from .models import (
    Entity, EntityType, Relationship, RelationType,
)

# استيراد المحلل الدلالي من detectors
import sys
from pathlib import Path
_TOOL_DIR = Path(__file__).parent.parent.resolve()
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

try:
    from detectors.solidity_parser import SoliditySemanticParser
    from detectors import ParsedContract, ParsedFunction, StateVar
except ImportError:
    from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
    from agl_security_tool.detectors import ParsedContract, ParsedFunction, StateVar


# ═══════════════════════════════════════════════════════════════
#  Token Detection Patterns — أنماط اكتشاف التوكنات
# ═══════════════════════════════════════════════════════════════

# ERC20 core interface functions
_ERC20_FUNCTIONS = {
    "transfer", "transferFrom", "approve", "allowance",
    "balanceOf", "totalSupply", "name", "symbol", "decimals",
}
_ERC20_VARS = {"_balances", "balances", "_allowances", "allowances", "_totalSupply", "totalSupply"}
_ERC20_EVENTS = {"Transfer", "Approval"}

# ERC721 interface
_ERC721_FUNCTIONS = {
    "ownerOf", "safeTransferFrom", "transferFrom", "approve",
    "getApproved", "setApprovalForAll", "isApprovedForAll",
    "tokenURI", "balanceOf",
}
_ERC721_VARS = {"_owners", "_tokenApprovals", "_operatorApprovals"}
_ERC721_EVENTS = {"Transfer", "Approval", "ApprovalForAll"}

# ERC1155 interface
_ERC1155_FUNCTIONS = {
    "safeTransferFrom", "safeBatchTransferFrom",
    "balanceOf", "balanceOfBatch", "setApprovalForAll", "isApprovedForAll",
    "uri",
}

# ERC4626 Vault
_ERC4626_FUNCTIONS = {
    "deposit", "withdraw", "redeem", "mint",
    "totalAssets", "convertToShares", "convertToAssets",
    "maxDeposit", "maxWithdraw", "maxRedeem", "maxMint",
    "previewDeposit", "previewWithdraw", "previewRedeem", "previewMint",
    "asset",
}

# Oracle patterns
_ORACLE_PATTERNS = {
    "latestRoundData", "latestAnswer", "getRoundData",
    "getPrice", "consult", "observe", "slot0",
    "priceFeed", "oracle", "chainlinkOracle",
}

# AMM Pool patterns
_POOL_FUNCTIONS = {
    "swap", "addLiquidity", "removeLiquidity", "mint", "burn",
    "getReserves", "token0", "token1", "liquidity",
    "flash", "flashLoan",
}

# Lending patterns
_LENDING_FUNCTIONS = {
    "borrow", "repay", "liquidate", "liquidationCall",
    "supply", "deposit", "withdraw", "getReserveData",
    "getUserAccountData", "getConfiguration",
    "setUserUseReserveAsCollateral",
}

# Governance patterns
_GOV_PATTERNS = {
    "propose", "castVote", "execute", "queue", "cancel",
    "quorum", "votingDelay", "votingPeriod", "proposalThreshold",
    "grantRole", "revokeRole", "renounceRole", "hasRole",
    "getRoleMember", "DEFAULT_ADMIN_ROLE",
}

# Staking patterns
_STAKING_FUNCTIONS = {
    "stake", "unstake", "getReward", "earned", "rewardPerToken",
    "notifyRewardAmount", "rewardRate", "periodFinish",
    "cooldownDuration", "setCooldownDuration",
}

# Bridge patterns
_BRIDGE_FUNCTIONS = {
    "sendMessage", "receiveMessage", "bridge", "relay",
    "verifyMessage", "processMessage", "finalize",
}

# Access Control patterns
_ACCESS_CONTROL_MODIFIERS = {
    "onlyOwner", "onlyAdmin", "onlyRole", "onlyGovernance",
    "onlyMinter", "onlyOperator", "authorized",
    "whenNotPaused", "whenPaused",
    "onlyProxy", "onlyDelegateCall",
}

# Known inheritance for type detection
_INHERITANCE_TOKEN = {
    "ERC20", "ERC20Upgradeable", "ERC20Burnable", "ERC20Pausable",
    "ERC20Permit", "ERC20Votes", "ERC20Wrapper", "ERC20Snapshot",
    "ERC721", "ERC721Upgradeable", "ERC721Enumerable",
    "ERC1155", "ERC1155Upgradeable",
}
_INHERITANCE_VAULT = {
    "ERC4626", "ERC4626Upgradeable",
}
_INHERITANCE_GOV = {
    "Governor", "GovernorCompatibilityBravo", "GovernorVotes",
    "GovernorTimelockControl", "GovernorCountingSimple",
    "TimelockController", "Ownable", "Ownable2Step",
    "AccessControl", "AccessControlEnumerable",
    "AccessControlDefaultAdminRules",
}
_INHERITANCE_PROXY = {
    "UUPSUpgradeable", "TransparentUpgradeableProxy",
    "Proxy", "ERC1967Proxy", "BeaconProxy", "Initializable",
}


class EntityExtractor:
    """
    مستخرج الكيانات المالية من العقود المحللة.

    يستقبل قائمة ParsedContract (من SoliditySemanticParser)
    ويعيد قائمة Entity مع تصنيف دقيق.
    """

    def __init__(self):
        self._parser = SoliditySemanticParser()
        self._entity_counter = 0

    def _next_id(self, prefix: str) -> str:
        """معرف فريد تصاعدي"""
        self._entity_counter += 1
        return f"{prefix}_{self._entity_counter}"

    # ═══════════════════════════════════════════════════════════
    #  Main API
    # ═══════════════════════════════════════════════════════════

    def extract_from_source(self, source: str, file_path: str = "") -> List[Entity]:
        """استخراج الكيانات مباشرة من كود Solidity"""
        contracts = self._parser.parse(source, file_path)
        return self.extract_from_contracts(contracts, file_path)

    def extract_from_contracts(self, contracts: List[ParsedContract],
                                file_path: str = "") -> List[Entity]:
        """استخراج الكيانات من قائمة عقود محللة"""
        entities: List[Entity] = []

        for contract in contracts:
            # تخطي الواجهات (لا تحتوي على منطق)
            if contract.contract_type == "interface":
                continue

            # تصنيف نوع الكيان
            entity_type, confidence = self._classify_contract(contract)

            # إنشاء الكيان الرئيسي
            entity = Entity(
                entity_id=f"contract:{contract.name}",
                entity_type=entity_type,
                name=contract.name,
                contract_name=contract.name,
                source_file=file_path or contract.source_file,
                line_start=contract.line_start,
                line_end=contract.line_end,
                confidence=confidence,
            )

            # استخراج تفاصيل حسب النوع
            self._extract_token_details(contract, entity)
            self._extract_vault_details(contract, entity)
            self._extract_oracle_details(contract, entity)
            self._extract_governance_details(contract, entity)
            self._extract_financial_vars(contract, entity)
            self._extract_access_control(contract, entity)
            self._extract_balance_vars(contract, entity)
            self._extract_state_vars_map(contract, entity)

            entities.append(entity)

            # استخراج كيانات فرعية (متغيرات الأرصدة كعقد منفصلة)
            sub_entities = self._extract_sub_entities(contract, entity, file_path)
            entities.extend(sub_entities)

        return entities

    # ═══════════════════════════════════════════════════════════
    #  Contract Classification — تصنيف العقد
    # ═══════════════════════════════════════════════════════════

    def _classify_contract(self, contract: ParsedContract) -> Tuple[EntityType, float]:
        """
        تصنيف نوع العقد بناءً على:
        1. الوراثة (أعلى ثقة)
        2. الدوال المعروفة
        3. متغيرات الحالة
        4. الأسماء
        """
        inherits = set(contract.inherits)
        func_names = set(contract.functions.keys())
        var_names = set(contract.state_vars.keys())
        name_lower = contract.name.lower()

        scores: Dict[EntityType, float] = {}

        # ─── Inheritance-based (عالية الثقة) ───
        if inherits & _INHERITANCE_VAULT:
            scores[EntityType.VAULT] = 0.95
        if inherits & _INHERITANCE_TOKEN:
            if inherits & {"ERC721", "ERC721Upgradeable", "ERC721Enumerable"}:
                scores[EntityType.TOKEN] = 0.95  # NFT but still token
            elif inherits & {"ERC1155", "ERC1155Upgradeable"}:
                scores[EntityType.TOKEN] = 0.93
            else:
                scores[EntityType.TOKEN] = 0.95
        if inherits & _INHERITANCE_GOV:
            scores[EntityType.GOVERNANCE] = 0.90
        if inherits & _INHERITANCE_PROXY:
            scores[EntityType.PROXY] = 0.90

        # ─── Function-based (متوسطة الثقة) ───
        erc20_overlap = len(func_names & _ERC20_FUNCTIONS)
        if erc20_overlap >= 4:
            scores[EntityType.TOKEN] = max(scores.get(EntityType.TOKEN, 0), 0.80)

        erc4626_overlap = len(func_names & _ERC4626_FUNCTIONS)
        if erc4626_overlap >= 5:
            scores[EntityType.VAULT] = max(scores.get(EntityType.VAULT, 0), 0.85)

        pool_overlap = len(func_names & _POOL_FUNCTIONS)
        if pool_overlap >= 3:
            scores[EntityType.POOL] = max(scores.get(EntityType.POOL, 0), 0.80)

        lending_overlap = len(func_names & _LENDING_FUNCTIONS)
        if lending_overlap >= 3:
            scores[EntityType.LENDING_MARKET] = max(
                scores.get(EntityType.LENDING_MARKET, 0), 0.80
            )

        oracle_overlap = len(func_names & _ORACLE_PATTERNS)
        if oracle_overlap >= 2:
            scores[EntityType.ORACLE] = max(scores.get(EntityType.ORACLE, 0), 0.75)

        gov_overlap = len(func_names & _GOV_PATTERNS)
        if gov_overlap >= 3:
            scores[EntityType.GOVERNANCE] = max(scores.get(EntityType.GOVERNANCE, 0), 0.75)

        staking_overlap = len(func_names & _STAKING_FUNCTIONS)
        if staking_overlap >= 3:
            scores[EntityType.STAKING] = max(scores.get(EntityType.STAKING, 0), 0.80)

        bridge_overlap = len(func_names & _BRIDGE_FUNCTIONS)
        if bridge_overlap >= 2:
            scores[EntityType.BRIDGE] = max(scores.get(EntityType.BRIDGE, 0), 0.75)

        # ─── Name-based (منخفضة الثقة، لكن إشارة مفيدة) ───
        name_hints = {
            "token": EntityType.TOKEN,
            "coin": EntityType.TOKEN,
            "vault": EntityType.VAULT,
            "pool": EntityType.POOL,
            "amm": EntityType.POOL,
            "oracle": EntityType.ORACLE,
            "pricefeed": EntityType.ORACLE,
            "governor": EntityType.GOVERNANCE,
            "timelock": EntityType.GOVERNANCE,
            "staking": EntityType.STAKING,
            "stake": EntityType.STAKING,
            "bridge": EntityType.BRIDGE,
            "router": EntityType.ROUTER,
            "swap": EntityType.ROUTER,
            "treasury": EntityType.TREASURY,
            "reward": EntityType.REWARD,
            "lending": EntityType.LENDING_MARKET,
        }
        for hint, etype in name_hints.items():
            if hint in name_lower:
                scores[etype] = max(scores.get(etype, 0), 0.55)

        # ─── Variable-based (تكميلي) ───
        if var_names & _ERC20_VARS:
            scores[EntityType.TOKEN] = max(scores.get(EntityType.TOKEN, 0), 0.70)

        # اختيار الأعلى
        if scores:
            best_type = max(scores, key=scores.get)
            return best_type, scores[best_type]

        return EntityType.GENERIC_CONTRACT, 0.50

    # ═══════════════════════════════════════════════════════════
    #  Detail Extractors — استخراج التفاصيل
    # ═══════════════════════════════════════════════════════════

    def _extract_token_details(self, contract: ParsedContract, entity: Entity) -> None:
        """استخراج تفاصيل التوكن"""
        if entity.entity_type not in (EntityType.TOKEN, EntityType.VAULT):
            return

        func_names = set(contract.functions.keys())
        inherits = set(contract.inherits)

        # نوع التوكن
        if inherits & {"ERC721", "ERC721Upgradeable", "ERC721Enumerable"}:
            entity.token_type = "ERC721"
        elif inherits & {"ERC1155", "ERC1155Upgradeable"}:
            entity.token_type = "ERC1155"
        elif inherits & _INHERITANCE_TOKEN or len(func_names & _ERC20_FUNCTIONS) >= 4:
            entity.token_type = "ERC20"

        # هل يوجد mint/burn
        entity.is_mintable = "mint" in func_names or "_mint" in func_names
        entity.is_burnable = "burn" in func_names or "_burn" in func_names

        # pausable
        entity.is_pausable = any(
            p in " ".join(contract.inherits) for p in ["Pausable", "pausable"]
        ) or "whenNotPaused" in str(contract.modifiers)

        # Total supply variable
        for vname in contract.state_vars:
            if "supply" in vname.lower() or "total" in vname.lower():
                entity.total_supply_var = vname
                break

        # Symbol from name heuristic
        name = contract.name
        if name.startswith("ERC20") or name.startswith("ERC721"):
            entity.token_symbol = name
        elif len(name) <= 6 and name.isupper():
            entity.token_symbol = name

    def _extract_vault_details(self, contract: ParsedContract, entity: Entity) -> None:
        """استخراج تفاصيل Vault/ERC4626"""
        if entity.entity_type != EntityType.VAULT:
            return
        func_names = set(contract.functions.keys())
        entity.token_type = "ERC4626"

        # البحث عن asset المرتبط
        if "asset" in func_names:
            entity.state_vars["underlying_asset"] = "address"

    def _extract_oracle_details(self, contract: ParsedContract, entity: Entity) -> None:
        """استخراج تفاصيل Oracle"""
        # البحث عن متغيرات أوراكل في أي عقد
        for vname, svar in contract.state_vars.items():
            vname_lower = vname.lower()
            if any(p in vname_lower for p in ["oracle", "pricefeed", "feed", "aggregator"]):
                entity.oracle_link = vname

    def _extract_governance_details(self, contract: ParsedContract, entity: Entity) -> None:
        """استخراج تفاصيل الحوكمة"""
        # البحث عن أدوار
        roles: List[str] = []
        for vname, svar in contract.state_vars.items():
            if "ROLE" in vname or "role" in vname.lower():
                roles.append(vname)
            if vname in ("owner", "_owner"):
                entity.owner_var = vname
        entity.admin_roles = roles

        # البحث عن modifiers الوصول
        for mname in contract.modifiers:
            if mname in _ACCESS_CONTROL_MODIFIERS:
                entity.access_modifiers.append(mname)

    def _extract_financial_vars(self, contract: ParsedContract, entity: Entity) -> None:
        """استخراج المتغيرات المالية"""
        for vname, svar in contract.state_vars.items():
            vname_lower = vname.lower()

            # نسبة الضمان
            if any(p in vname_lower for p in ["collateral", "ratio", "ltv", "factor"]):
                if entity.collateralization_ratio is None:
                    entity.collateralization_ratio = 0.0  # يحتاج حساب فعلي

            # سعر الفائدة
            if any(p in vname_lower for p in ["rate", "interest", "borrow", "supply"]):
                if "rate" in vname_lower:
                    entity.interest_rate_var = vname

            # الرسوم
            if any(p in vname_lower for p in ["fee", "commission", "tax", "spread"]):
                entity.fee_percentage_var = vname

    def _extract_access_control(self, contract: ParsedContract, entity: Entity) -> None:
        """استخراج هيكل التحكم في الوصول"""
        # Owner variable
        for vname in contract.state_vars:
            if vname in ("owner", "_owner", "admin", "_admin"):
                entity.owner_var = vname
                break

        # Modifiers as access controls
        for func_name, func in contract.functions.items():
            for mod in func.modifiers:
                if mod in _ACCESS_CONTROL_MODIFIERS and mod not in entity.access_modifiers:
                    entity.access_modifiers.append(mod)

    def _extract_balance_vars(self, contract: ParsedContract, entity: Entity) -> None:
        """استخراج متغيرات الأرصدة"""
        balance_patterns = [
            "balance", "balances", "_balances", "shares", "_shares",
            "deposits", "amounts", "stakes", "staked",
            "debt", "borrowed", "collateral", "liquidity",
            "reserves", "totalDeposits", "totalBorrowed",
        ]
        for vname, svar in contract.state_vars.items():
            vname_lower = vname.lower()
            if any(p.lower() in vname_lower for p in balance_patterns):
                entity.balance_vars.append(vname)
            # mappings that look like balance ledgers
            elif svar.is_mapping and any(
                p in vname_lower for p in ["amount", "supply", "reserve", "fund"]
            ):
                entity.balance_vars.append(vname)

    def _extract_state_vars_map(self, contract: ParsedContract, entity: Entity) -> None:
        """بناء خريطة المتغيرات"""
        for vname, svar in contract.state_vars.items():
            entity.state_vars[vname] = svar.var_type

    # ═══════════════════════════════════════════════════════════
    #  Sub-Entity Extraction — كيانات فرعية
    # ═══════════════════════════════════════════════════════════

    def _extract_sub_entities(self, contract: ParsedContract,
                               parent: Entity, file_path: str) -> List[Entity]:
        """
        استخراج كيانات فرعية من داخل العقد:
        - متغيرات mapping كحسابات/أرصدة
        - أنماط collateral/debt كمراكز مالية
        - مراجع oracle كروابط أسعار
        """
        sub_entities: List[Entity] = []

        for vname, svar in contract.state_vars.items():
            vname_lower = vname.lower()

            # Debt positions
            if any(p in vname_lower for p in ["debt", "borrow", "loan"]) and svar.is_mapping:
                sub = Entity(
                    entity_id=f"debt:{contract.name}.{vname}",
                    entity_type=EntityType.DEBT,
                    name=f"{contract.name}.{vname}",
                    contract_name=contract.name,
                    source_file=file_path,
                    line_start=svar.line,
                    confidence=0.75,
                )
                sub_entities.append(sub)

            # Collateral positions
            elif any(p in vname_lower for p in ["collateral", "deposit", "staked"]) and svar.is_mapping:
                sub = Entity(
                    entity_id=f"collateral:{contract.name}.{vname}",
                    entity_type=EntityType.COLLATERAL,
                    name=f"{contract.name}.{vname}",
                    contract_name=contract.name,
                    source_file=file_path,
                    line_start=svar.line,
                    confidence=0.70,
                )
                sub_entities.append(sub)

            # Reward distributors
            elif any(p in vname_lower for p in ["reward", "incentive", "emission"]) and svar.is_mapping:
                sub = Entity(
                    entity_id=f"reward:{contract.name}.{vname}",
                    entity_type=EntityType.REWARD,
                    name=f"{contract.name}.{vname}",
                    contract_name=contract.name,
                    source_file=file_path,
                    line_start=svar.line,
                    confidence=0.65,
                )
                sub_entities.append(sub)

        return sub_entities

    # ═══════════════════════════════════════════════════════════
    #  Utilities
    # ═══════════════════════════════════════════════════════════

    def get_entity_summary(self, entities: List[Entity]) -> Dict[str, Any]:
        """ملخص الكيانات المستخرجة"""
        type_counts = {}
        for e in entities:
            t = e.entity_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_entities": len(entities),
            "by_type": type_counts,
            "entities": [
                {
                    "id": e.entity_id,
                    "type": e.entity_type.value,
                    "name": e.name,
                    "confidence": e.confidence,
                    "balance_vars": e.balance_vars,
                    "access_modifiers": e.access_modifiers,
                }
                for e in entities
            ],
        }
