// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract Vault {
    mapping(address => uint256) public shares;
    uint256 public totalShares;
    uint256 public totalAssets;
    function deposit() external payable {
        uint256 s = (totalShares == 0) ? msg.value : (msg.value * totalShares) / totalAssets;
        shares[msg.sender] += s;
        totalShares += s;
        totalAssets += msg.value;
    }
    function getSharePrice() public view returns (uint256) {
        if (totalShares == 0) return 1e18;
        return (totalAssets * 1e18) / totalShares;
    }
    function withdraw(uint256 shareAmt) external {
        require(shares[msg.sender] >= shareAmt);
        uint256 value = (shareAmt * totalAssets) / totalShares;
        shares[msg.sender] -= shareAmt;
        totalShares -= shareAmt;
        (bool ok,) = msg.sender.call{value: value}("");
        require(ok);
        totalAssets -= value;
    }
}
