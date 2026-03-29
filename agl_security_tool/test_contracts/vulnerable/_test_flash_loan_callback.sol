
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

interface IPool {
    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata modes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

contract VulnerableFlashReceiver {
    IPool public pool;
    address public owner;
    
    constructor(address _pool) {
        pool = IPool(_pool);
        owner = msg.sender;
    }
    
    // VULNERABLE: No msg.sender validation!
    // Anyone can call this directly (not just the Aave pool)
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external returns (bool) {
        // Arbitrage logic — moves funds
        for (uint i = 0; i < assets.length; i++) {
            uint256 amountOwed = amounts[i] + premiums[i];
            IERC20(assets[i]).approve(address(pool), amountOwed);
        }
        
        // No check: require(msg.sender == address(pool))
        // No check: require(initiator == address(this))
        
        return true;
    }
    
    function doFlashLoan(address token, uint256 amount) external {
        require(msg.sender == owner, "not owner");
        address[] memory assets = new address[](1);
        assets[0] = token;
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        uint256[] memory modes = new uint256[](1);
        modes[0] = 0;
        pool.flashLoan(address(this), assets, amounts, modes, address(this), "", 0);
    }
}
