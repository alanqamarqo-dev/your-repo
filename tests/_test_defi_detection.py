"""Deep check: Do DeFi detectors actually catch real patterns?"""

import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Write a contract with KNOWN DeFi vulns to see what the tool catches
DEFI_VULN_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IOracle {
    function getPrice(address token) external view returns (uint256);
}

contract VulnerableVault {
    mapping(address => uint256) public shares;
    mapping(address => uint256) public deposits;
    uint256 public totalShares;
    uint256 public totalAssets;
    address public owner;
    IOracle public oracle;
    IERC20 public token;
    
    constructor(address _token, address _oracle) {
        token = IERC20(_token);
        oracle = IOracle(_oracle);
        owner = msg.sender;
    }

    // VULN 1: First depositor attack — donation inflates share price
    function deposit(uint256 amount) external returns (uint256 shares_) {
        if (totalShares == 0) {
            shares_ = amount;
        } else {
            shares_ = (amount * totalShares) / totalAssets;
        }
        shares[msg.sender] += shares_;
        totalShares += shares_;
        totalAssets += amount;
        token.transferFrom(msg.sender, address(this), amount);
    }

    // VULN 2: Oracle manipulation — uses spot price
    function borrow(uint256 amount) external {
        uint256 price = oracle.getPrice(address(token));
        uint256 collateralValue = deposits[msg.sender] * price;
        require(collateralValue >= amount * 2, "Undercollateralized");
        payable(msg.sender).transfer(amount);
    }

    // VULN 3: Unchecked ERC20 transfer return
    function withdraw(uint256 shareAmount) external {
        require(shares[msg.sender] >= shareAmount);
        uint256 assetAmount = (shareAmount * totalAssets) / totalShares;
        shares[msg.sender] -= shareAmount;
        totalShares -= shareAmount;
        totalAssets -= assetAmount;
        token.transfer(msg.sender, assetAmount);  // no return check!
    }

    // VULN 4: Reentrancy via callback
    function flashLoan(uint256 amount, address callback) external {
        uint256 balBefore = token.balanceOf(address(this));
        token.transfer(callback, amount);
        // callback — attacker can reenter here
        (bool ok,) = callback.call(abi.encodeWithSignature("onFlashLoan(uint256)", amount));
        uint256 balAfter = token.balanceOf(address(this));
        require(balAfter >= balBefore, "Flash loan not repaid");
    }

    // VULN 5: Divide before multiply precision loss
    function calculateFee(uint256 amount, uint256 rate) external pure returns (uint256) {
        return (amount / 10000) * rate;  // precision loss!
    }

    // VULN 6: Arbitrary send — transfer to user-controlled address
    function rescueTokens(address _token, address to) external {
        require(msg.sender == owner);
        uint256 bal = IERC20(_token).balanceOf(address(this));
        IERC20(_token).transfer(to, bal);
    }

    // VULN 7: Missing flash loan callback validation
    function executeFlashLoan(address pool, uint256 amount) external {
        // no validation that callback came from the pool
    }
}
"""

import os, time

_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
path = os.path.join(_PROJECT_ROOT, "_test_defi_vulns.sol")
with open(path, "w") as f:
    f.write(DEFI_VULN_CONTRACT)

from agl_security_tool.core import AGLSecurityAudit

audit = AGLSecurityAudit({"skip_llm": True})
r = audit.scan(path)

print("=" * 60)
print("DeFi VULNERABILITY DETECTION TEST")
print("  7 known vulns in synthetic contract")
print("=" * 60)

# Check what each layer found
print(f"\nLayers: {r.get('layers_used')}")
print(f"Total unified: {r.get('total_findings', 0)}")
print(f"Severity: {r.get('severity_summary')}")

# Detailed findings
unified = r.get("all_findings_unified", [])
print(f"\n--- All findings ({len(unified)}) ---")
for i, f in enumerate(unified, 1):
    sev = f.get("severity", "?").upper()
    cat = f.get("category", f.get("detector", f.get("detector_id", "?")))
    line = f.get("line", 0)
    title = f.get("title", f.get("description", ""))[:80]
    sources = f.get("confirmed_by", ["?"])
    has_proof = "🔓" if f.get("exploit_proof") else "  "
    print(f"  {has_proof} [{sev}] L{line} [{cat}] {title}")
    print(f"       Sources: {sources}")

# Exploit reasoning
er = r.get("exploit_reasoning", {})
print(f"\n--- Exploit Proofs ({len(er.get('exploit_proofs', []))}) ---")
for p in er.get("exploit_proofs", []):
    tag = "EXPLOITABLE" if p["exploitable"] else "NOT PROVEN"
    print(f"  [{tag}] {p['function']}() — Z3:{p['z3_result']}, conf:{p['confidence']}")
    if p.get("invariant_violated"):
        print(f"    Invariant: {p['invariant_violated']['name']}")

# Score card
print("\n" + "=" * 60)
print("SCORECARD: What was detected vs what exists")
print("=" * 60)
known_vulns = [
    ("First depositor attack", ["first_deposit", "FirstDeposit", "share", "donation"]),
    ("Oracle manipulation", ["oracle", "Oracle", "spot_price", "price"]),
    ("Unchecked ERC20 transfer", ["unchecked", "UncheckedERC20", "return"]),
    ("Reentrancy via callback", ["reentrancy", "Reentrancy", "reentran"]),
    ("Divide before multiply", ["divide", "DivideBeforeMultiply", "precision"]),
    ("Arbitrary ERC20 send", ["arbitrary", "ArbitrarySend"]),
    ("Flash loan callback", ["flash", "FlashLoan", "callback"]),
]

for vuln_name, keywords in known_vulns:
    found = False
    for f in unified:
        cat = (
            str(f.get("category", ""))
            + str(f.get("detector", ""))
            + str(f.get("detector_id", ""))
            + str(f.get("title", ""))
        )
        if any(k.lower() in cat.lower() for k in keywords):
            found = True
            break
    status = "✅ DETECTED" if found else "❌ MISSED"
    print(f"  {status}  {vuln_name}")

os.remove(path)
