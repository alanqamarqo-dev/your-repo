// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Fee parameter has no upper bound — can be set to 100%

contract NoBoundsConfig {
    uint256 public fee;           // in basis points
    uint256 public withdrawDelay; // in seconds
    uint256 public maxLeverage;   // multiplier

    address public owner;

    constructor() {
        owner = msg.sender;
        fee = 30;          // 0.3%
        withdrawDelay = 1 days;
        maxLeverage = 5;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    // VULNERABILITY: fee can be set to 10000 (100%) or even higher
    function setFee(uint256 _fee) external onlyOwner {
        fee = _fee;  // VULNERABILITY: no upper bound
    }

    // VULNERABILITY: delay can be set to years, effectively locking funds
    function setWithdrawDelay(uint256 _delay) external onlyOwner {
        withdrawDelay = _delay;  // VULNERABILITY: no bounds
    }

    // VULNERABILITY: leverage can be set to extreme values
    function setMaxLeverage(uint256 _leverage) external onlyOwner {
        maxLeverage = _leverage;  // VULNERABILITY: no bounds
    }
}
