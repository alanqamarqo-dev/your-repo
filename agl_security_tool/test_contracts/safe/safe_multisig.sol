// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title SafeMultisig — Properly implemented multisig
/// No known vulnerabilities — should be classified as safe
contract SafeMultisig {
    address[] public owners;
    uint256 public requiredConfirmations;
    
    struct Transaction {
        address to;
        uint256 value;
        bytes data;
        bool executed;
        uint256 confirmationCount;
    }

    mapping(uint256 => Transaction) public transactions;
    mapping(uint256 => mapping(address => bool)) public isConfirmed;
    uint256 public transactionCount;

    modifier onlyOwner() {
        bool isOwner = false;
        for (uint256 i = 0; i < owners.length; i++) {
            if (owners[i] == msg.sender) {
                isOwner = true;
                break;
            }
        }
        require(isOwner, "Not owner");
        _;
    }

    constructor(address[] memory _owners, uint256 _required) {
        require(_owners.length > 0, "Owners required");
        require(_required > 0 && _required <= _owners.length, "Invalid required");
        owners = _owners;
        requiredConfirmations = _required;
    }

    // SAFE: Proper access control, no reentrancy risk
    function submitTransaction(address to, uint256 value, bytes calldata data) 
        external onlyOwner returns (uint256) 
    {
        uint256 txId = transactionCount;
        transactions[txId] = Transaction({
            to: to,
            value: value,
            data: data,
            executed: false,
            confirmationCount: 0
        });
        transactionCount++;
        return txId;
    }

    // SAFE: Only owners can confirm
    function confirmTransaction(uint256 txId) external onlyOwner {
        require(!isConfirmed[txId][msg.sender], "Already confirmed");
        require(!transactions[txId].executed, "Already executed");
        
        isConfirmed[txId][msg.sender] = true;
        transactions[txId].confirmationCount++;
    }

    // SAFE: Requires threshold confirmations, proper state update before call
    function executeTransaction(uint256 txId) external onlyOwner {
        Transaction storage txn = transactions[txId];
        require(!txn.executed, "Already executed");
        require(txn.confirmationCount >= requiredConfirmations, "Not enough confirmations");
        
        txn.executed = true;  // State update BEFORE external call
        
        (bool success, ) = txn.to.call{value: txn.value}(txn.data);
        require(success, "Tx failed");
    }

    receive() external payable {}
}
