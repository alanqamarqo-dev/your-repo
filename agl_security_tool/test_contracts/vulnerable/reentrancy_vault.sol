// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title ReentrancyVault — Classic reentrancy vulnerability
/// SWC-107: Reentrancy
contract ReentrancyVault {
    mapping(address => uint256) public balances;
    uint256 public totalDeposits;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
        totalDeposits += msg.value;
    }

    // VULNERABLE: External call before state update
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient");
        
        // This is the classic reentrancy pattern:
        // 1. Check: balances >= amount ✓
        // 2. Effect: MISSING — should update balance here
        // 3. Interaction: external call that can re-enter
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        // State update AFTER external call — attacker can re-enter
        balances[msg.sender] -= amount;
        totalDeposits -= amount;
    }

    // VULNERABLE: Cross-function reentrancy
    function transfer(address to, uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }

    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }

    receive() external payable {
        deposit();
    }
}
