// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title TimestampLottery — Weak randomness from block values
/// SWC-114/SWC-116/SWC-120: Timestamp Dependence + Weak Randomness
contract TimestampLottery {
    address public owner;
    uint256 public jackpot;
    uint256 public ticketPrice;
    mapping(address => uint256) public lastPlay;

    constructor() {
        owner = msg.sender;
        ticketPrice = 0.01 ether;
    }

    function fund() external payable {
        jackpot += msg.value;
    }

    // VULNERABLE: block.timestamp for randomness — miners can manipulate
    function play() external payable {
        require(msg.value >= ticketPrice, "Pay ticket price");
        jackpot += msg.value;

        // SWC-120: keccak256 of block values is NOT random
        bool winner = uint256(
            keccak256(abi.encodePacked(block.timestamp, msg.sender, block.number))
        ) % 10 == 0;

        if (winner) {
            uint256 prize = jackpot / 2;
            jackpot -= prize;
            payable(msg.sender).transfer(prize);
        }

        lastPlay[msg.sender] = block.timestamp;
    }

    // VULNERABLE: Time-based access control — miner can adjust
    function claimBonus() external {
        require(
            block.timestamp % 3600 < 60,
            "Only during first minute of each hour"
        );
        // This condition is manipulable by miners
        uint256 bonus = jackpot / 10;
        jackpot -= bonus;
        payable(msg.sender).transfer(bonus);
    }

    // VULNERABLE: Block number for timing
    function isEligible(address user) external view returns (bool) {
        return block.number % 2 == 0;
    }

    receive() external payable {
        jackpot += msg.value;
    }
}
