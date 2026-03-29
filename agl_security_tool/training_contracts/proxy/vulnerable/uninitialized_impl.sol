// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Upgradeable contract without initializer — state set in constructor

abstract contract Initializable {
    bool private _initialized;
    modifier initializer() {
        require(!_initialized, "Already initialized");
        _initialized = true;
        _;
    }
}

abstract contract UUPSUpgradeable is Initializable {
    function upgradeTo(address newImplementation) external virtual;
}

contract VulnerableImpl is UUPSUpgradeable {
    address public owner;
    uint256 public treasuryBalance;

    // VULNERABILITY: Constructor sets state — won't run through proxy
    constructor() {
        owner = msg.sender;
        treasuryBalance = 0;
    }

    // No initialize() function with initializer modifier
    // The proxy will have owner = address(0)

    function withdraw(uint256 amount) external {
        require(msg.sender == owner, "Not owner");
        payable(owner).transfer(amount);
    }

    function upgradeTo(address newImpl) external override {
        require(msg.sender == owner, "Not owner");
        // upgrade logic
    }

    receive() external payable {
        treasuryBalance += msg.value;
    }
}
