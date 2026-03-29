// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: ecrecover returns address(0) without check

contract EcrecoverZeroVuln {
    mapping(address => bool) public authorized;

    // VULNERABILITY: If signer param is uninitialized (address(0)),
    // and ecrecover returns address(0) from invalid sig, check passes
    function verifyAndExecute(
        bytes32 messageHash,
        uint8 v, bytes32 r, bytes32 s,
        address expectedSigner
    ) external {
        address recovered = ecrecover(messageHash, v, r, s);
        // VULNERABILITY: no check for recovered != address(0)
        require(recovered == expectedSigner, "Bad sig");

        // If expectedSigner is address(0) (uninitialized), any invalid sig works
        authorized[recovered] = true;
    }
}
