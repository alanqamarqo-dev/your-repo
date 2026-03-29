// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// SAFE: Returndata ignored + Governance with snapshot

// --- Safe Multicall: ignores returndata ---

contract SafeMulticall {
    struct Call {
        address target;
        bytes callData;
    }

    // SAFE: Does not capture returndata — ignores it
    function multicall(Call[] calldata calls) external returns (bool[] memory successes) {
        successes = new bool[](calls.length);
        for (uint i = 0; i < calls.length; i++) {
            (bool ok, ) = calls[i].target.call(calls[i].callData);
            successes[i] = ok;
        }
    }
}

// --- Safe Governance: uses snapshot-based voting ---

interface IERC20Votes {
    function getPastVotes(address account, uint256 blockNumber) external view returns (uint256);
}

contract SafeGovernance {
    IERC20Votes public token;

    struct Proposal {
        address proposer;
        uint256 forVotes;
        uint256 againstVotes;
        uint256 snapshotBlock;
        uint256 endBlock;
        bool executed;
        mapping(address => bool) hasVoted;
    }

    uint256 public proposalCount;
    mapping(uint256 => Proposal) public proposals;

    constructor(address _token) {
        token = IERC20Votes(_token);
    }

    function propose() external returns (uint256) {
        proposalCount++;
        Proposal storage p = proposals[proposalCount];
        p.proposer = msg.sender;
        p.snapshotBlock = block.number - 1;  // SAFE: snapshot before proposal
        p.endBlock = block.number + 17280;
        return proposalCount;
    }

    // SAFE: Uses getPastVotes (snapshot) — flash loan cannot inflate
    function castVote(uint256 proposalId, bool support) external {
        Proposal storage p = proposals[proposalId];
        require(block.number <= p.endBlock, "Voting ended");
        require(!p.hasVoted[msg.sender], "Already voted");

        // SAFE: Reads historical balance — cannot be flash-loaned
        uint256 votes = token.getPastVotes(msg.sender, p.snapshotBlock);
        require(votes > 0, "No voting power");

        p.hasVoted[msg.sender] = true;
        if (support) {
            p.forVotes += votes;
        } else {
            p.againstVotes += votes;
        }
    }
}
