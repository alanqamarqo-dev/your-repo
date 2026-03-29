// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// SAFE: Proper input validation with SafeCast, zero checks, and bounds

import {SafeCast} from "@openzeppelin/contracts/utils/math/SafeCast.sol";

contract SafeInputValidation {
    using SafeCast for uint256;
    using SafeCast for int256;

    address public owner;
    address public feeRecipient;
    uint256 public fee;
    uint256 public constant MAX_FEE = 1000; // 10% max

    mapping(address => uint128) public userDeposits;

    constructor() {
        owner = msg.sender;
        feeRecipient = msg.sender;
        fee = 30;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    // SAFE: Zero-address validation
    function setOwner(address _owner) external onlyOwner {
        require(_owner != address(0), "Zero address");
        owner = _owner;
    }

    // SAFE: Zero-address validation
    function setFeeRecipient(address _recipient) external onlyOwner {
        require(_recipient != address(0), "Zero address");
        feeRecipient = _recipient;
    }

    // SAFE: Upper bound validation
    function setFee(uint256 _fee) external onlyOwner {
        require(_fee <= MAX_FEE, "Fee exceeds max");
        fee = _fee;
    }

    // SAFE: SafeCast prevents silent truncation
    function deposit(uint256 amount) external payable {
        require(msg.value == amount, "Wrong amount");
        uint128 safe = amount.toUint128();  // SAFE: reverts on overflow
        userDeposits[msg.sender] += safe;
    }

    receive() external payable {}
}
