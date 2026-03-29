"""
╔══════════════════════════════════════════════════════════════════════╗
║       AGL On-Chain Context — Optional Blockchain Integration         ║
║       Proxy Detection / Storage Layout / Bytecode Comparison         ║
╚══════════════════════════════════════════════════════════════════════╝

Strategic feature that differentiates from pure static analysis tools.
All on-chain features are OPTIONAL — the tool works fully without them.

Features:
  1. Fetch contract bytecode via JSON-RPC
  2. Detect proxy patterns (EIP-1967, EIP-1822, Transparent, UUPS, Beacon)
  3. Extract storage layout from bytecode
  4. Compare deployed bytecode vs source compilation
  5. Fetch verified source from Etherscan (optional)

Supported chains:
  - Ethereum Mainnet / Goerli / Sepolia
  - Polygon, BSC, Arbitrum, Optimism, Base, Avalanche

Configuration via environment:
  AGL_RPC_URL          — JSON-RPC endpoint (default: none)
  AGL_ETHERSCAN_KEY    — Etherscan API key (optional)
  AGL_CHAIN_ID         — Target chain ID (default: 1 = Ethereum)

Usage:
    from agl_security_tool.onchain_context import OnChainContext
    ctx = OnChainContext(rpc_url="https://eth-mainnet.g.alchemy.com/v2/KEY")
    info = ctx.get_contract_context("0x1234...")
"""

from __future__ import annotations

import json
import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

_logger = logging.getLogger("AGL.onchain")


# ═══════════════════════════════════════════════════════════════
#  Proxy Pattern Signatures
# ═══════════════════════════════════════════════════════════════

# EIP-1967 standard proxy storage slots
PROXY_PATTERNS = {
    "EIP-1967 (Implementation)": {
        "slot": "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc",
        "description": "Standard transparent/UUPS proxy implementation slot",
    },
    "EIP-1967 (Admin)": {
        "slot": "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103",
        "description": "Transparent proxy admin slot",
    },
    "EIP-1967 (Beacon)": {
        "slot": "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50",
        "description": "Beacon proxy slot",
    },
    "EIP-1822 (UUPS)": {
        "slot": "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7",
        "description": "EIP-1822 UUPS proxy storage slot",
    },
    "OpenZeppelin (Legacy)": {
        "slot": "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3",
        "description": "Legacy OpenZeppelin proxy slot",
    },
}

# Common delegatecall opcodes in bytecode
DELEGATECALL_OPCODE = "f4"  # 0xf4 = DELEGATECALL


@dataclass
class ProxyInfo:
    """Detected proxy pattern information."""

    is_proxy: bool = False
    proxy_type: str = ""
    implementation_address: str = ""
    admin_address: str = ""
    beacon_address: str = ""
    patterns_matched: List[str] = field(default_factory=list)


@dataclass
class StorageSlot:
    """A storage slot with its value."""

    slot: str = ""
    value: str = ""
    label: str = ""  # Human-readable label if known


@dataclass
class OnChainInfo:
    """Complete on-chain context for a contract."""

    address: str = ""
    chain_id: int = 1
    bytecode: str = ""
    bytecode_size: int = 0
    is_contract: bool = False
    proxy: ProxyInfo = field(default_factory=ProxyInfo)
    storage_slots: List[StorageSlot] = field(default_factory=list)
    balance_wei: int = 0
    balance_eth: float = 0.0
    source_match: Optional[bool] = None  # None = not checked
    nonce: int = 0
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "chain_id": self.chain_id,
            "is_contract": self.is_contract,
            "bytecode_size": self.bytecode_size,
            "balance_eth": self.balance_eth,
            "proxy": {
                "is_proxy": self.proxy.is_proxy,
                "type": self.proxy.proxy_type,
                "implementation": self.proxy.implementation_address,
                "admin": self.proxy.admin_address,
                "patterns": self.proxy.patterns_matched,
            },
            "storage_slots": [
                {"slot": s.slot, "value": s.value, "label": s.label}
                for s in self.storage_slots
            ],
            "source_match": self.source_match,
            "error": self.error,
        }


class OnChainContext:
    """
    Optional on-chain context provider.

    Fetches blockchain data to enrich static analysis:
    - Is this a proxy contract?
    - What does the storage look like?
    - Does the deployed bytecode match the source?

    All methods return structured data — never raise on network errors.
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        etherscan_key: Optional[str] = None,
        chain_id: Optional[int] = None,
        timeout: int = 10,
    ):
        self.rpc_url = rpc_url or os.environ.get("AGL_RPC_URL", "")
        self.etherscan_key = etherscan_key or os.environ.get("AGL_ETHERSCAN_KEY", "")
        self.chain_id = chain_id or int(os.environ.get("AGL_CHAIN_ID", "1"))
        self.timeout = timeout
        self.available = bool(self.rpc_url)

        if not self.available:
            _logger.info(
                "OnChainContext: No RPC URL configured. "
                "Set AGL_RPC_URL to enable on-chain analysis."
            )

    # ─── Main API ──────────────────────────────────────────
    def get_contract_context(self, address: str) -> OnChainInfo:
        """
        Fetch complete on-chain context for a contract address.

        Returns OnChainInfo with all available data — never raises.
        """
        info = OnChainInfo(address=address, chain_id=self.chain_id)

        if not self.available:
            info.error = "No RPC URL configured"
            return info

        if not self._is_valid_address(address):
            info.error = f"Invalid address: {address}"
            return info

        # 1. Fetch bytecode
        bytecode = self._rpc_call("eth_getCode", [address, "latest"])
        if bytecode and bytecode != "0x":
            info.is_contract = True
            info.bytecode = bytecode
            info.bytecode_size = (len(bytecode) - 2) // 2  # hex to bytes

        # 2. Fetch balance
        balance_hex = self._rpc_call("eth_getBalance", [address, "latest"])
        if balance_hex:
            info.balance_wei = int(balance_hex, 16)
            info.balance_eth = info.balance_wei / 1e18

        # 3. Fetch nonce
        nonce_hex = self._rpc_call("eth_getTransactionCount", [address, "latest"])
        if nonce_hex:
            info.nonce = int(nonce_hex, 16)

        # 4. Detect proxy patterns
        if info.is_contract:
            info.proxy = self.detect_proxy(address, info.bytecode)

        # 5. Read key storage slots
        if info.is_contract:
            info.storage_slots = self._read_common_storage(address)

        return info

    # ─── Proxy Detection ───────────────────────────────────
    def detect_proxy(self, address: str, bytecode: str = "") -> ProxyInfo:
        """
        Detect proxy patterns by checking standard storage slots.

        Checks:
        1. EIP-1967 implementation/admin/beacon slots
        2. EIP-1822 UUPS slot
        3. DELEGATECALL opcode in bytecode
        """
        proxy = ProxyInfo()

        if not self.available:
            return proxy

        # Check each known proxy slot
        for pattern_name, pattern_info in PROXY_PATTERNS.items():
            slot_value = self._rpc_call(
                "eth_getStorageAt",
                [address, pattern_info["slot"], "latest"],
            )
            if slot_value and slot_value != "0x" + "0" * 64:
                # Non-zero value in proxy slot → proxy detected
                proxy.is_proxy = True
                proxy.patterns_matched.append(pattern_name)
                impl_addr = "0x" + slot_value[-40:]  # Last 20 bytes = address

                if "Implementation" in pattern_name or "UUPS" in pattern_name:
                    proxy.implementation_address = impl_addr
                    proxy.proxy_type = pattern_name
                elif "Admin" in pattern_name:
                    proxy.admin_address = impl_addr
                elif "Beacon" in pattern_name:
                    proxy.beacon_address = impl_addr

        # Additionally check bytecode for DELEGATECALL
        if bytecode and DELEGATECALL_OPCODE in bytecode.lower():
            if "delegatecall" not in str(proxy.patterns_matched).lower():
                proxy.patterns_matched.append("bytecode_delegatecall")
                if not proxy.is_proxy:
                    proxy.is_proxy = True
                    proxy.proxy_type = "Unknown (DELEGATECALL in bytecode)"

        return proxy

    # ─── Bytecode Comparison ───────────────────────────────
    def compare_bytecode(self, address: str, compiled_bytecode: str) -> Dict[str, Any]:
        """
        Compare deployed bytecode with locally compiled bytecode.

        Returns match status and differences.
        """
        result = {
            "match": None,
            "deployed_size": 0,
            "compiled_size": 0,
            "error": "",
        }

        if not self.available:
            result["error"] = "No RPC URL configured"
            return result

        deployed = self._rpc_call("eth_getCode", [address, "latest"])
        if not deployed or deployed == "0x":
            result["error"] = "No bytecode at address (not a contract or destroyed)"
            return result

        # Normalize
        deployed_clean = deployed.lower().replace("0x", "")
        compiled_clean = compiled_bytecode.lower().replace("0x", "")

        result["deployed_size"] = len(deployed_clean) // 2
        result["compiled_size"] = len(compiled_clean) // 2

        # Exact match
        if deployed_clean == compiled_clean:
            result["match"] = True
            return result

        # Check if deployed contains compiled (constructor may add prefix)
        if compiled_clean in deployed_clean:
            result["match"] = True
            result["note"] = (
                "Compiled bytecode found within deployed code (includes constructor)"
            )
            return result

        # Metadata hash differs (Solidity appends CBOR-encoded metadata)
        # Strip last 43 bytes (86 hex chars) which is typically metadata
        if len(deployed_clean) > 86 and len(compiled_clean) > 86:
            if deployed_clean[:-86] == compiled_clean[:-86]:
                result["match"] = True
                result["note"] = (
                    "Match excluding metadata hash (compiler settings may differ)"
                )
                return result

        result["match"] = False
        result["note"] = (
            "Bytecode mismatch — source may not correspond to deployed contract"
        )
        return result

    # ─── Storage Layout Extraction ─────────────────────────
    def extract_storage_layout(
        self, address: str, slot_count: int = 20
    ) -> List[StorageSlot]:
        """
        Read first N storage slots to detect storage layout.
        Useful for detecting unexpected state values.
        """
        slots = []
        if not self.available:
            return slots

        for i in range(slot_count):
            slot_hex = "0x" + hex(i)[2:].zfill(64)
            value = self._rpc_call("eth_getStorageAt", [address, slot_hex, "latest"])
            if value and value != "0x" + "0" * 64:
                label = self._guess_slot_label(i, value)
                slots.append(StorageSlot(slot=slot_hex, value=value, label=label))
        return slots

    # ─── Etherscan Source Fetch ─────────────────────────────
    def fetch_verified_source(self, address: str) -> Optional[str]:
        """
        Fetch verified source code from Etherscan (requires API key).
        Returns source code string or None.
        """
        if not self.etherscan_key:
            _logger.debug("No Etherscan API key configured")
            return None

        base_urls = {
            1: "https://api.etherscan.io/api",
            5: "https://api-goerli.etherscan.io/api",
            11155111: "https://api-sepolia.etherscan.io/api",
            137: "https://api.polygonscan.com/api",
            56: "https://api.bscscan.com/api",
            42161: "https://api.arbiscan.io/api",
            10: "https://api-optimistic.etherscan.io/api",
            8453: "https://api.basescan.org/api",
            43114: "https://api.snowtrace.io/api",
        }

        base_url = base_urls.get(self.chain_id)
        if not base_url:
            _logger.warning("Etherscan not supported for chain %d", self.chain_id)
            return None

        try:
            import requests

            resp = requests.get(
                base_url,
                params={
                    "module": "contract",
                    "action": "getsourcecode",
                    "address": address,
                    "apikey": self.etherscan_key,
                },
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                result = data.get("result", [])
                if result and isinstance(result, list) and result[0].get("SourceCode"):
                    return result[0]["SourceCode"]
        except Exception as e:
            _logger.debug("Etherscan fetch error: %s", e)

        return None

    # ─── RPC Helper ────────────────────────────────────────
    def _rpc_call(self, method: str, params: list) -> Optional[str]:
        """Make a JSON-RPC call. Returns result or None on error."""
        if not self.rpc_url:
            return None

        try:
            import requests

            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": 1,
            }
            resp = requests.post(
                self.rpc_url,
                json=payload,
                timeout=self.timeout,
            )
            if resp.status_code != 200:
                _logger.debug("RPC HTTP %d for %s", resp.status_code, method)
                return None
            data = resp.json()
            if "error" in data:
                _logger.debug("RPC error: %s", data["error"])
                return None
            return data.get("result")
        except Exception as e:
            _logger.debug("RPC call failed (%s): %s", method, e)
        return None

    def _read_common_storage(self, address: str) -> List[StorageSlot]:
        """Read commonly important storage slots."""
        slots = []

        # Proxy slots
        for name, info in PROXY_PATTERNS.items():
            value = self._rpc_call(
                "eth_getStorageAt", [address, info["slot"], "latest"]
            )
            if value and value != "0x" + "0" * 64:
                slots.append(StorageSlot(slot=info["slot"], value=value, label=name))

        # Slot 0-4 (usually owner, paused, totalSupply, etc.)
        for i in range(5):
            slot_hex = "0x" + hex(i)[2:].zfill(64)
            value = self._rpc_call("eth_getStorageAt", [address, slot_hex, "latest"])
            if value and value != "0x" + "0" * 64:
                label = self._guess_slot_label(i, value)
                slots.append(StorageSlot(slot=slot_hex, value=value, label=label))

        return slots

    @staticmethod
    def _guess_slot_label(slot_index: int, value: str) -> str:
        """Heuristic guess for what a storage slot contains."""
        v = value.replace("0x", "").lower()

        # Check if it looks like an address (20 bytes, last 40 hex chars)
        if v[:24] == "0" * 24 and len(v) >= 40:
            addr_part = v[24:]
            if addr_part != "0" * 40:
                if slot_index == 0:
                    return "likely: owner address"
                return f"likely: address (slot {slot_index})"

        # Check if it looks like a boolean (0 or 1)
        if v in ("0" * 63 + "0", "0" * 63 + "1"):
            return f"likely: boolean (slot {slot_index})"

        # Check if it looks like a small number
        try:
            num = int(v, 16)
            if 0 < num < 1000000:
                return f"likely: counter/enum = {num} (slot {slot_index})"
            if num > 10**15:
                return f"likely: balance/amount = {num} (slot {slot_index})"
        except ValueError:
            pass

        return f"slot {slot_index}"

    @staticmethod
    def _is_valid_address(address: str) -> bool:
        """Validate Ethereum address format."""
        return bool(re.match(r"^0x[0-9a-fA-F]{40}$", address))


# ═══════════════════════════════════════════════════════════════
#  Convenience function for quick context
# ═══════════════════════════════════════════════════════════════


def get_onchain_context(
    address: str,
    rpc_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Quick helper to get on-chain context for an address.

    Returns dict with proxy info, storage, balance.
    Returns {'available': False} if no RPC configured.
    """
    ctx = OnChainContext(rpc_url=rpc_url)
    if not ctx.available:
        return {"available": False, "reason": "No RPC URL configured (set AGL_RPC_URL)"}

    info = ctx.get_contract_context(address)
    result = info.to_dict()
    result["available"] = True
    return result
