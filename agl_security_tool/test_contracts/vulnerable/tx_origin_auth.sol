// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title TxOriginAuth — Authentication via tx.origin
/// SWC-115: Authorization through tx.origin
contract TxOriginAuth {
    address public owner;
    mapping(address => bool) public authorized;
    mapping(address => uint256) public balances;

    constructor() {
        owner = msg.sender;
    }

    // VULNERABLE: tx.origin instead of msg.sender
    // A phishing contract can trick the owner into calling
    // another contract which then calls this
    function transferOwnership(address newOwner) external {
        require(tx.origin == owner, "Not owner");
        owner = newOwner;
    }

    // VULNERABLE: Same tx.origin pattern for fund withdrawal
    function withdrawAll(address to) external {
        require(tx.origin == owner, "Not owner");
        uint256 bal = address(this).balance;
        payable(to).transfer(bal);
    }

    // VULNERABLE: Authorize using tx.origin
    function setAuthorized(address user, bool status) external {
        require(tx.origin == owner, "Not owner");
        authorized[user] = status;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    receive() external payable {}
}
