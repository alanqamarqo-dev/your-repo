// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title UnprotectedSelfDestruct — Anyone can kill the contract
/// SWC-106: Unprotected SELFDESTRUCT
contract UnprotectedSelfDestruct {
    address public owner;
    mapping(address => uint256) public deposits;
    uint256 public totalFunds;

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable {
        deposits[msg.sender] += msg.value;
        totalFunds += msg.value;
    }

    function withdraw(uint256 amount) external {
        require(deposits[msg.sender] >= amount, "Insufficient");
        deposits[msg.sender] -= amount;
        totalFunds -= amount;
        payable(msg.sender).transfer(amount);
    }

    // VULNERABLE: No access control on selfdestruct
    // Anyone can call this and destroy the contract, stealing all ETH
    function destroy() external {
        selfdestruct(payable(msg.sender));
    }

    // VULNERABLE: kill() also unprotected
    function kill(address payable beneficiary) external {
        selfdestruct(beneficiary);
    }

    receive() external payable {
        deposits[msg.sender] += msg.value;
        totalFunds += msg.value;
    }
}
