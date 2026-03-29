// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title GasDoS — Denial of service through unbounded loops
/// SWC-128: DoS With Block Gas Limit
/// SWC-113: DoS with Failed Call
contract GasDoS {
    address[] public recipients;
    mapping(address => uint256) public balances;
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function addRecipient(address r) external {
        recipients.push(r);
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    // VULNERABLE SWC-128: Unbounded loop over dynamic array
    // If recipients array grows large, this exceeds block gas limit
    function distributeAll() external {
        uint256 share = address(this).balance / recipients.length;
        for (uint256 i = 0; i < recipients.length; i++) {
            // SWC-113: If one transfer fails, entire distribution reverts
            payable(recipients[i]).transfer(share);
        }
    }

    // VULNERABLE: Anyone can push to array, causing gas DoS
    function register() external {
        recipients.push(msg.sender);
    }

    // VULNERABLE: Mass send with no failure handling
    function massRefund() external {
        require(msg.sender == owner, "Not owner");
        for (uint256 i = 0; i < recipients.length; i++) {
            (bool ok,) = recipients[i].call{value: balances[recipients[i]]}("");
            require(ok, "Transfer failed");  // One failure blocks all
        }
    }

    function getRecipientCount() external view returns (uint256) {
        return recipients.length;
    }

    receive() external payable {}
}
