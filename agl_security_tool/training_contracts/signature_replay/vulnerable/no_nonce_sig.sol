// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Signature replay — no nonce, no chainId, no EIP-712

contract VulnerableSigReplay {
    address public trustedSigner;
    mapping(address => uint256) public balances;

    constructor(address _signer) {
        trustedSigner = _signer;
    }

    // VULNERABILITY: No nonce tracking — same signature can be replayed
    function withdrawWithSig(
        address to,
        uint256 amount,
        uint8 v, bytes32 r, bytes32 s
    ) external {
        // VULNERABILITY: No nonce, no chainId in hash
        bytes32 hash = keccak256(abi.encodePacked(to, amount));
        address signer = ecrecover(hash, v, r, s);

        // VULNERABILITY: ecrecover can return address(0) — not checked
        require(signer == trustedSigner, "Invalid signer");

        balances[to] -= amount;
        payable(to).transfer(amount);
    }

    receive() external payable {
        balances[msg.sender] += msg.value;
    }
}
