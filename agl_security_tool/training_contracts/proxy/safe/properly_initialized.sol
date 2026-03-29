// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// SAFE: Properly initialized upgradeable contract with gaps and access control

abstract contract Initializable {
    bool private _initialized;
    modifier initializer() {
        require(!_initialized);
        _initialized = true;
        _;
    }
}

abstract contract UUPSUpgradeable is Initializable {
    function _authorizeUpgrade(address newImpl) internal virtual;
}

contract SafeImpl is UUPSUpgradeable {
    address public owner;
    uint256 public treasuryBalance;

    // SAFE: No constructor state writes — uses initialize()
    function initialize(address _owner) public initializer {
        require(_owner != address(0), "Zero address");
        owner = _owner;
    }

    function withdraw(uint256 amount) external {
        require(msg.sender == owner, "Not owner");
        payable(owner).transfer(amount);
    }

    // SAFE: _authorizeUpgrade checks owner
    function _authorizeUpgrade(address) internal override {
        require(msg.sender == owner, "Not owner");
    }

    // SAFE: Storage gap for future upgrades
    uint256[50] private __gap;

    receive() external payable {
        treasuryBalance += msg.value;
    }
}
