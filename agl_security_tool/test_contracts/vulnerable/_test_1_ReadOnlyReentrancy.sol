
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract VulnerablePool {
    mapping(address => uint256) public deposits;
    uint256 public totalShares;
    uint256 public totalAssets;
    IERC20 public token;
    
    function deposit(uint256 amount) external {
        uint256 shares = (totalShares == 0) ? amount : (amount * totalShares) / totalAssets;
        deposits[msg.sender] += shares;
        totalShares += shares;
        totalAssets += amount;
    }
    
    function withdraw(uint256 shares) external {
        uint256 amount = (shares * totalAssets) / totalShares;
        totalAssets -= amount;
        // External call with STALE totalShares
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        totalShares -= shares;
        deposits[msg.sender] -= shares;
    }
    
    // VIEW reads inconsistent state during withdraw's external call
    function getExchangeRate() public view returns (uint256) {
        if (totalShares == 0) return 1e18;
        return (totalAssets * 1e18) / totalShares;
    }
    
    function getShareValue(uint256 shares) external view returns (uint256) {
        return (shares * getExchangeRate()) / 1e18;
    }
}
