// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Missing zero-address check on critical state variable

contract ZeroAddressVuln {
    address public owner;
    address public feeRecipient;
    address public treasury;

    constructor() {
        owner = msg.sender;
        feeRecipient = msg.sender;
        treasury = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    // VULNERABILITY: owner can be set to address(0) — permanent lockout
    function setOwner(address _owner) external onlyOwner {
        owner = _owner;  // VULNERABILITY: no zero-address check
    }

    // VULNERABILITY: feeRecipient = 0 means fees go to burn address
    function setFeeRecipient(address _recipient) external onlyOwner {
        feeRecipient = _recipient;  // VULNERABILITY: no zero-address check
    }

    // VULNERABILITY: treasury = 0 means funds are lost
    function setTreasury(address _treasury) external onlyOwner {
        treasury = _treasury;  // VULNERABILITY: no zero-address check
    }

    function collectFees() external {
        payable(feeRecipient).transfer(address(this).balance);
    }

    receive() external payable {}
}
