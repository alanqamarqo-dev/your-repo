// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title UncheckedCallToken — Missing return value check
/// SWC-104: Unchecked Call Return Value
contract UncheckedCallToken {
    mapping(address => uint256) public balances;
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    // VULNERABLE: Low-level send without checking return
    function withdrawUnsafe(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        // send() returns bool but it's not checked!
        payable(msg.sender).send(amount);
    }

    // VULNERABLE: Low-level call without checking return
    function forwardPayment(address target) external payable {
        target.call{value: msg.value}("");
        // Return value ignored — if call fails, ETH is lost
    }

    // VULNERABLE: ERC20-style transfer without checking
    function unsafeTokenTransfer(address token, address to, uint256 amount) external {
        // Many non-standard ERC20s don't return bool
        (bool success,) = token.call(
            abi.encodeWithSignature("transfer(address,uint256)", to, amount)
        );
        // success check exists but not reverted on failure
    }
}
