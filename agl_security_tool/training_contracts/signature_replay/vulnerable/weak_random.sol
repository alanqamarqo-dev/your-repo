// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Using block.prevrandao/timestamp for randomness

contract WeakLottery {
    address public lastWinner;
    uint256 public pot;

    // VULNERABILITY: Predictable randomness from block variables
    function pickWinner(address[] calldata players) external {
        require(players.length > 0, "No players");

        // VULNERABILITY: Miner/validator can influence these values
        uint256 random = uint256(keccak256(abi.encodePacked(
            block.timestamp,
            block.prevrandao,
            msg.sender,
            players.length
        )));

        uint256 index = random % players.length;
        lastWinner = players[index];
        payable(lastWinner).transfer(pot);
        pot = 0;
    }

    // VULNERABILITY: block.number for dice roll
    function rollDice() external view returns (uint256) {
        return uint256(keccak256(abi.encodePacked(block.timestamp, msg.sender))) % 6 + 1;
    }

    function enter() external payable {
        require(msg.value >= 0.01 ether, "Min bet");
        pot += msg.value;
    }
}
