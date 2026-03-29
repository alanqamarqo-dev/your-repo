// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract SafeVault is ReentrancyGuard {
    mapping(address => uint256) public balances;
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    // SAFE: checks-effects-interactions + nonReentrant
    function withdraw() external nonReentrant {
        uint256 bal = balances[msg.sender];
        require(bal > 0, "No balance");
        balances[msg.sender] = 0;  // state update BEFORE external call
        (bool ok, ) = msg.sender.call{value: bal}("");
        require(ok, "Transfer failed");
    }
    
    // SAFE: has onlyOwner
    function drain(address to) external onlyOwner {
        payable(to).transfer(address(this).balance);
    }
}
