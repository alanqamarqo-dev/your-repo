// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
}

interface IPool {
    function flashLoan(address receiver, address[] calldata assets,
        uint256[] calldata amounts, uint256[] calldata modes,
        address onBehalfOf, bytes calldata params, uint16 referralCode) external;
}

contract VulnerableFlashReceiver {
    IPool public pool;
    address public owner;
    
    constructor(address _pool) {
        pool = IPool(_pool);
        owner = msg.sender;
    }
    
    // VULNERABLE: No msg.sender == pool check!
    function executeOperation(
        address[] calldata assets, uint256[] calldata amounts,
        uint256[] calldata premiums, address initiator,
        bytes calldata params
    ) external returns (bool) {
        for (uint i = 0; i < assets.length; i++) {
            uint256 amountOwed = amounts[i] + premiums[i];
            IERC20(assets[i]).approve(address(pool), amountOwed);
        }
        return true;
    }
    
    function doFlashLoan(address token, uint256 amount) external {
        require(msg.sender == owner);
        address[] memory assets = new address[](1);
        assets[0] = token;
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        uint256[] memory modes = new uint256[](1);
        modes[0] = 0;
        pool.flashLoan(address(this), assets, amounts, modes, address(this), "", 0);
    }
}
