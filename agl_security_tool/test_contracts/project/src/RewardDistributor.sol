// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./Vault.sol";

/**
 * @title RewardDistributor - موزع المكافآت
 * @notice يوزع المكافآت على المودعين حسب حصتهم
 */
contract RewardDistributor {
    Vault public vault;
    address public rewardToken;
    
    mapping(address => uint256) public pendingRewards;
    mapping(address => uint256) public lastClaim;
    
    uint256 public totalDistributed;
    address[] public recipients;

    event RewardDistributed(address indexed user, uint256 amount);

    constructor(address _vault, address _rewardToken) {
        vault = Vault(payable(_vault));
        rewardToken = _rewardToken;
    }

    /**
     * @notice إضافة مستلم للمكافآت
     */
    function addRecipient(address user) external {
        recipients.push(user);
    }

    /**
     * @notice توزيع المكافآت — ⚠️ حلقة غير محدودة (DoS potential)
     * إذا كان عدد المستلمين كبيراً جداً، ينفد الغاز
     */
    function distributeRewards(uint256 totalReward) external {
        // ⚠️ حلقة على كل المستلمين — DoS إذا كان العدد كبيراً
        for (uint256 i = 0; i < recipients.length; i++) {
            uint256 share = totalReward / recipients.length;
            pendingRewards[recipients[i]] += share;
        }
        totalDistributed += totalReward;
    }

    /**
     * @notice المطالبة بالمكافأة — ⚠️ Reentrancy
     */
    function claim() external {
        uint256 amount = pendingRewards[msg.sender];
        require(amount > 0, "Nothing to claim");
        
        // ⚠️ التحويل قبل التصفير — Reentrancy
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        pendingRewards[msg.sender] = 0;
        lastClaim[msg.sender] = block.timestamp;
        
        emit RewardDistributed(msg.sender, amount);
    }

    /**
     * @notice حساب عشوائي — ⚠️ block.timestamp كمصدر عشوائية
     */
    function getRandomBonus(address user) external view returns (uint256) {
        // ⚠️ استخدام block.timestamp كعشوائية — قابل للتلاعب
        uint256 random = uint256(keccak256(abi.encodePacked(block.timestamp, user))) % 100;
        return pendingRewards[user] * random / 100;
    }

    receive() external payable {}
}
