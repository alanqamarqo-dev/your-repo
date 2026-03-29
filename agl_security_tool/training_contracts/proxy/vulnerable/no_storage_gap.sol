// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: No storage gap in inheritable upgradeable contract

abstract contract Initializable {
    bool private _initialized;
    modifier initializer() {
        require(!_initialized);
        _initialized = true;
        _;
    }
}

contract BaseTokenV1 is Initializable {
    // slot 0: _initialized (from Initializable)
    // slot 1: name
    string public name;
    // slot 2: symbol
    string public symbol;
    // slot 3: totalSupply
    uint256 public totalSupply;
    // slot 4: balances mapping
    mapping(address => uint256) public balances;

    // VULNERABILITY: No __gap — adding vars in V2 will overwrite child storage

    function initialize(string memory _name, string memory _symbol) public initializer {
        name = _name;
        symbol = _symbol;
    }

    function mint(address to, uint256 amount) public virtual {
        balances[to] += amount;
        totalSupply += amount;
    }
}

// V2 adds a new variable — causes storage collision if V1 had no gap
contract BaseTokenV2 is BaseTokenV1 {
    // This variable overlaps with the next slot after V1's layout
    // If another contract inherited from V1, this corrupts storage
    uint256 public maxSupply;  // VULNERABILITY: collision risk

    function setMaxSupply(uint256 _max) external {
        maxSupply = _max;
    }
}
