// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: upgradeTo is public without access control

abstract contract UUPSUpgradeable {
    address internal _implementation;

    function _upgradeTo(address newImpl) internal {
        _implementation = newImpl;
    }
}

contract VulnerableUpgradeProxy is UUPSUpgradeable {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // VULNERABILITY: Anyone can call upgradeTo — no access control
    function upgradeTo(address newImplementation) public {
        _upgradeTo(newImplementation);
    }

    // VULNERABILITY: upgradeToAndCall also unprotected
    function upgradeToAndCall(address newImpl, bytes memory data) public {
        _upgradeTo(newImpl);
        (bool ok,) = newImpl.delegatecall(data);
        require(ok);
    }
}
