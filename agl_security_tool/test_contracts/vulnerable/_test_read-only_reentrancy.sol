
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract VulnerablePool {
    mapping(address => uint256) public deposits;
    uint256 public totalDeposits;
    IERC20 public token;
    
    // State variable shared between withdraw() and getExchangeRate()
    uint256 public totalShares;
    uint256 public totalAssets;
    
    function deposit(uint256 amount) external {
        uint256 shares = (totalShares == 0) ? amount : (amount * totalShares) / totalAssets;
        token.transfer(address(this), amount);  // placeholder
        deposits[msg.sender] += shares;
        totalShares += shares;
        totalAssets += amount;
    }
    
    function withdraw(uint256 shares) external {
        uint256 amount = (shares * totalAssets) / totalShares;
        
        // State is inconsistent HERE — totalAssets updated but totalShares not yet
        totalAssets -= amount;
        
        // External call with inconsistent state
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");
        
        // State updated AFTER external call
        totalShares -= shares;
        deposits[msg.sender] -= shares;
    }
    
    // VIEW function reads inconsistent state during reentrancy
    // An attacker can call this during withdraw() and see wrong exchange rate
    function getExchangeRate() public view returns (uint256) {
        if (totalShares == 0) return 1e18;
        return (totalAssets * 1e18) / totalShares;
    }
    
    // Another contract uses this price — gets manipulated value
    function getShareValue(uint256 shares) external view returns (uint256) {
        return (shares * getExchangeRate()) / 1e18;
    }
}
