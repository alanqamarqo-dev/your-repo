// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title DelegatecallProxy — Unsafe delegatecall to user-controlled address
/// SWC-112: Delegatecall to Untrusted Callee
contract DelegatecallProxy {
    address public owner;
    address public implementation;
    uint256 public value;

    constructor() {
        owner = msg.sender;
    }

    // VULNERABLE: delegatecall to arbitrary address
    // Attacker can change contract state through malicious implementation
    function upgradeAndCall(address newImpl, bytes calldata data) external {
        require(msg.sender == owner, "Not owner");
        implementation = newImpl;
        // DANGEROUS: delegatecall runs in this contract's storage context
        (bool success,) = newImpl.delegatecall(data);
        require(success, "Delegatecall failed");
    }

    // VULNERABLE: Even worse — anyone can call delegatecall
    function execute(address target, bytes calldata data) external {
        // No access control on delegatecall!
        (bool success,) = target.delegatecall(data);
    }

    // VULNERABLE: Proxy pattern without proper storage alignment
    fallback() external payable {
        address impl = implementation;
        assembly {
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), impl, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }

    receive() external payable {}
}
