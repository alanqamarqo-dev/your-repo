// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// SAFE: Chainlink VRF for randomness

interface IVRFCoordinator {
    function requestRandomWords(
        bytes32 keyHash, uint64 subId, uint16 minConfirmations,
        uint32 callbackGasLimit, uint32 numWords
    ) external returns (uint256 requestId);
}

abstract contract VRFConsumerBase {
    function fulfillRandomWords(uint256 requestId, uint256[] memory randomWords) internal virtual;
}

contract SafeLottery is VRFConsumerBase {
    IVRFCoordinator public immutable COORDINATOR;
    bytes32 public immutable keyHash;
    uint64 public immutable subId;

    address[] public players;
    uint256 public pot;
    mapping(uint256 => bool) public pendingRequests;

    constructor(address coordinator, bytes32 _keyHash, uint64 _subId) {
        COORDINATOR = IVRFCoordinator(coordinator);
        keyHash = _keyHash;
        subId = _subId;
    }

    function enter() external payable {
        require(msg.value >= 0.01 ether, "Min bet");
        players.push(msg.sender);
        pot += msg.value;
    }

    // SAFE: Uses Chainlink VRF for verifiable randomness
    function pickWinner() external {
        require(players.length > 0, "No players");
        uint256 requestId = COORDINATOR.requestRandomWords(
            keyHash, subId, 3, 200000, 1
        );
        pendingRequests[requestId] = true;
    }

    // SAFE: Randomness comes from VRF oracle — not block variables
    function fulfillRandomWords(uint256 requestId, uint256[] memory randomWords) internal override {
        require(pendingRequests[requestId], "Unknown request");
        delete pendingRequests[requestId];

        uint256 index = randomWords[0] % players.length;
        address winner = players[index];
        payable(winner).transfer(pot);
        pot = 0;
        delete players;
    }
}
