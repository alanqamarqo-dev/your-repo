// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint256) public balances;
    mapping(address => bool) public isEditor;
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerability 1: Reentrancy
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        // External call before state update
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        balances[msg.sender] -= amount;
    }

    // Vulnerability 2: tx.origin phishing
    function transferTo(address to, uint256 amount) external {
        require(tx.origin == owner, "Not owner");
        payable(to).transfer(amount);
    }
    
    // Vulnerability 3: Unchecked external call
    function ping(address target) external {
        target.call(abi.encodeWithSignature("pong()"));
    }

    // Vulnerability 4: Block Timestamp
    function isLucky() external view returns (bool) {
        return block.timestamp % 2 == 0;
    }
}
