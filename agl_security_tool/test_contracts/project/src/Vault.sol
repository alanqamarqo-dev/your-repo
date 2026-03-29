// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./VaultToken.sol";

/**
 * @title Vault - الخزنة الرئيسية
 * @notice خزنة DeFi تسمح بالإيداع والسحب مع عائد
 * @dev يحتوي على عدة ثغرات للاختبار
 */
contract Vault {
    VaultToken public token;
    
    mapping(address => uint256) public deposits;
    mapping(address => uint256) public lastDeposit;
    
    uint256 public totalDeposits;
    uint256 public rewardRate = 100; // basis points
    address public owner;
    bool public locked;

    event Deposit(address indexed user, uint256 amount);
    event Withdraw(address indexed user, uint256 amount);
    event RewardClaimed(address indexed user, uint256 reward);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier nonReentrant() {
        require(!locked, "Reentrant");
        locked = true;
        _;
        locked = false;
    }

    constructor(address _token) {
        token = VaultToken(_token);
        owner = msg.sender;
    }

    /**
     * @notice إيداع توكنات في الخزنة
     * @param amount كمية التوكنات
     */
    function deposit(uint256 amount) external {
        require(amount > 0, "Zero amount");
        token.transferFrom(msg.sender, address(this), amount);
        deposits[msg.sender] += amount;
        lastDeposit[msg.sender] = block.timestamp;
        totalDeposits += amount;
        emit Deposit(msg.sender, amount);
    }

    /**
     * @notice سحب التوكنات — ⚠️ ثغرة Reentrancy!
     * تحديث الرصيد بعد التحويل (Checks-Effects-Interactions مخالف)
     */
    function withdraw(uint256 amount) external {
        require(deposits[msg.sender] >= amount, "Insufficient");
        
        // ⚠️ الخطأ: التحويل قبل تحديث الرصيد
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        deposits[msg.sender] -= amount;
        totalDeposits -= amount;
        emit Withdraw(msg.sender, amount);
    }

    /**
     * @notice سحب آمن مع حماية من Reentrancy
     */
    function safeWithdraw(uint256 amount) external nonReentrant {
        require(deposits[msg.sender] >= amount, "Insufficient");
        deposits[msg.sender] -= amount;
        totalDeposits -= amount;
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        emit Withdraw(msg.sender, amount);
    }

    /**
     * @notice حساب المكافأة — ⚠️ يعتمد على block.timestamp
     */
    function calculateReward(address user) public view returns (uint256) {
        uint256 duration = block.timestamp - lastDeposit[user];
        return (deposits[user] * rewardRate * duration) / (365 days * 10000);
    }

    /**
     * @notice المطالبة بالمكافأة
     */
    function claimReward() external {
        uint256 reward = calculateReward(msg.sender);
        require(reward > 0, "No reward");
        lastDeposit[msg.sender] = block.timestamp;
        token.mint(msg.sender, reward);
        emit RewardClaimed(msg.sender, reward);
    }

    /**
     * @notice تغيير معدل المكافأة — بدون حد أقصى!
     */
    function setRewardRate(uint256 _rate) external onlyOwner {
        rewardRate = _rate;
    }

    /**
     * @notice سحب طوارئ — ⚠️ tx.origin 
     */
    function emergencyWithdraw() external {
        require(tx.origin == owner, "Not owner");
        uint256 balance = address(this).balance;
        (bool sent, ) = owner.call{value: balance}("");
        require(sent, "Failed");
    }

    receive() external payable {}
}
