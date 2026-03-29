// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// SAFE: Proper EIP-712 signature with nonce and ECDSA library

library ECDSA {
    function recover(bytes32 hash, uint8 v, bytes32 r, bytes32 s)
        internal pure returns (address)
    {
        address signer = ecrecover(hash, v, r, s);
        require(signer != address(0), "ECDSA: invalid signature");
        return signer;
    }
}

contract SafeSignatureVerifier {
    using ECDSA for bytes32;

    address public trustedSigner;
    mapping(address => uint256) public nonces;
    mapping(address => uint256) public balances;

    bytes32 public immutable DOMAIN_SEPARATOR;

    bytes32 constant WITHDRAW_TYPEHASH = keccak256(
        "Withdraw(address to,uint256 amount,uint256 nonce)"
    );

    constructor(address _signer) {
        trustedSigner = _signer;
        DOMAIN_SEPARATOR = keccak256(abi.encode(
            keccak256("EIP712Domain(string name,uint256 chainId,address verifyingContract)"),
            keccak256("SafeVerifier"),
            block.chainid,
            address(this)
        ));
    }

    // SAFE: EIP-712 + nonce + address(0) check via ECDSA library
    function withdrawWithSig(
        address to,
        uint256 amount,
        uint256 nonce,
        uint8 v, bytes32 r, bytes32 s
    ) external {
        require(nonce == nonces[to], "Invalid nonce");

        bytes32 structHash = keccak256(abi.encode(
            WITHDRAW_TYPEHASH, to, amount, nonce
        ));
        bytes32 digest = keccak256(abi.encodePacked(
            "\x19\x01", DOMAIN_SEPARATOR, structHash
        ));

        // SAFE: ECDSA.recover checks for address(0) internally
        address signer = digest.recover(v, r, s);
        require(signer == trustedSigner, "Invalid signer");

        // SAFE: Increment nonce to prevent replay
        nonces[to]++;

        balances[to] -= amount;
        payable(to).transfer(amount);
    }

    receive() external payable {
        balances[msg.sender] += msg.value;
    }
}
