// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title SafeVault — Properly secured vault contract
/// No known vulnerabilities — should be classified as safe
contract SafeVault {
    mapping(address => uint256) public balances;
    address public owner;
    bool private locked;

    modifier nonReentrant() {
        require(!locked, "ReentrancyGuard: reentrant call");
        locked = true;
        _;
        locked = false;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    // SAFE: ReentrancyGuard + CEI pattern
    function withdraw(uint256 amount) external nonReentrant {
        require(balances[msg.sender] >= amount, "Insufficient");
        balances[msg.sender] -= amount;  // State update BEFORE external call
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
    }

    // SAFE: msg.sender for auth (not tx.origin)
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Zero address");
        owner = newOwner;
    }

    function getBalance() external view returns (uint256) {
        return balances[msg.sender];
    }

    receive() external payable {
        balances[msg.sender] += msg.value;
    }
}
