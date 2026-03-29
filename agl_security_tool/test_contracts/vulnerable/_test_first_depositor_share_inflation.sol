
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract VulnerableVault {
    IERC20 public asset;
    
    mapping(address => uint256) public shares;
    uint256 public totalShares;
    
    constructor(address _asset) {
        asset = IERC20(_asset);
    }
    
    function totalAssets() public view returns (uint256) {
        return asset.balanceOf(address(this));
    }
    
    // VULNERABLE: No minimum deposit, no virtual offset
    // Attack: deposit 1 wei → donate large amount → next depositor gets 0 shares
    function deposit(uint256 assets) external returns (uint256) {
        uint256 supply = totalShares;
        uint256 newShares;
        
        if (supply == 0) {
            newShares = assets;  // First deposit: 1:1
        } else {
            // shares = assets * totalShares / totalAssets
            // After donation: totalAssets is huge, so newShares rounds to 0
            newShares = (assets * totalShares) / totalAssets();
        }
        
        // No check for newShares > 0!
        shares[msg.sender] += newShares;
        totalShares += newShares;
        
        asset.transferFrom(msg.sender, address(this), assets);
        return newShares;
    }
    
    function redeem(uint256 sharesToBurn) external returns (uint256) {
        uint256 assets = (sharesToBurn * totalAssets()) / totalShares;
        shares[msg.sender] -= sharesToBurn;
        totalShares -= sharesToBurn;
        asset.transfer(msg.sender, assets);
        return assets;
    }
}
