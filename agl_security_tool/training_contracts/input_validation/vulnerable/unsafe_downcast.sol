// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Unsafe integer downcast without bounds check

contract UnsafeDowncaster {
    mapping(address => uint128) public userDeposits;
    mapping(address => uint96) public votingPower;

    // VULNERABILITY: uint256 → uint128 truncation
    function deposit(uint256 amount) external payable {
        require(msg.value == amount, "Wrong amount");
        // If amount > type(uint128).max, upper bits silently lost
        uint128 truncated = uint128(amount);  // VULNERABILITY: silent truncation
        userDeposits[msg.sender] += truncated;
    }

    // VULNERABILITY: uint256 → uint96 truncation (Compound governance style)
    function setVotingPower(address user, uint256 power) external {
        // uint96 max = 79_228_162_514_264_337_593_543_950_335
        // If power exceeds this, truncation occurs silently
        votingPower[user] = uint96(power);  // VULNERABILITY: unsafe downcast
    }

    // VULNERABILITY: int256 → int8 can flip sign
    function compressScore(int256 score) external pure returns (int8) {
        return int8(score);  // VULNERABILITY: sign flip possible
    }
}
