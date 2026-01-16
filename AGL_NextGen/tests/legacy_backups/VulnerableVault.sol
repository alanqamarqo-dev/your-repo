// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CryptoRewardVault {
    mapping(address => uint) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // VULNERABLE FUNCTION: withdraw()
    // This allows a user to withdraw their entire balance.
    // Can you spot the Reentrancy bug?
    function withdraw() public {
        uint amount = balances[msg.sender];
        require(amount > 0, "Insufficient balance");

        // 1. INTERACTION: Send Ether to the user
        // This hands over control to the receiver!
        (bool sent, ) = msg.sender.call{value: amount}("");
        require(sent, "Failed to send Ether");

        // 2. EFFECTS: Update the balance
        // Too late! The attacker has already re-entered.
        balances[msg.sender] = 0;
    }
}