// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Governance vote based on current balance — flash loan attackable

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function totalSupply() external view returns (uint256);
}

contract VulnerableGovernance {
    IERC20 public token;

    struct Proposal {
        address proposer;
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        uint256 endBlock;
        bool executed;
        mapping(address => bool) hasVoted;
    }

    uint256 public proposalCount;
    mapping(uint256 => Proposal) public proposals;
    uint256 public constant VOTING_PERIOD = 17280; // ~3 days

    constructor(address _token) {
        token = IERC20(_token);
    }

    function propose(string calldata description) external returns (uint256) {
        proposalCount++;
        Proposal storage p = proposals[proposalCount];
        p.proposer = msg.sender;
        p.description = description;
        p.endBlock = block.number + VOTING_PERIOD;
        return proposalCount;
    }

    // VULNERABILITY: Uses current balanceOf — flash loan can inflate voting power
    function castVote(uint256 proposalId, bool support) external {
        Proposal storage p = proposals[proposalId];
        require(block.number <= p.endBlock, "Voting ended");
        require(!p.hasVoted[msg.sender], "Already voted");

        // VULNERABILITY: Reads current balance — manipulable via flash loan
        uint256 votes = token.balanceOf(msg.sender);
        require(votes > 0, "No voting power");

        p.hasVoted[msg.sender] = true;
        if (support) {
            p.forVotes += votes;
        } else {
            p.againstVotes += votes;
        }
    }
}
