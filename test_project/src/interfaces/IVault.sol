// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IVault - واجهة الخزنة
 */
interface IVault {
    function deposit(uint256 amount) external;
    function withdraw(uint256 amount) external;
    function calculateReward(address user) external view returns (uint256);
    function claimReward() external;
}

/**
 * @title IPriceOracle - واجهة أوراكل الأسعار
 */
interface IPriceOracle {
    function getPrice(address token) external view returns (uint256);
    function updatePrice(address token, uint256 price) external;
}
