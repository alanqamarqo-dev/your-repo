
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IUniswapV3Pool {
    function slot0() external view returns (
        uint160 sqrtPriceX96, int24 tick, uint16 observationIndex,
        uint16 observationCardinality, uint16 observationCardinalityNext,
        uint8 feeProtocol, bool unlocked
    );
}

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract VulnerableLending {
    IUniswapV3Pool public priceOracle;
    IERC20 public collateralToken;
    IERC20 public borrowToken;
    mapping(address => uint256) public collateral;
    mapping(address => uint256) public debt;
    
    // VULNERABLE: slot0() = instant manipulable spot price
    function getPrice() public view returns (uint256) {
        (uint160 sqrtPriceX96,,,,,,) = priceOracle.slot0();
        return (uint256(sqrtPriceX96) * uint256(sqrtPriceX96)) >> 192;
    }
    
    function deposit(uint256 amount) external {
        collateralToken.transferFrom(msg.sender, address(this), amount);
        collateral[msg.sender] += amount;
    }
    
    function borrow(uint256 amount) external {
        uint256 price = getPrice();
        require(collateral[msg.sender] * price >= amount * 15 / 10);
        debt[msg.sender] += amount;
        borrowToken.transfer(msg.sender, amount);
    }
    
    function liquidate(address user) external {
        uint256 price = getPrice();
        require(collateral[user] * price < debt[user]);
        uint256 seized = collateral[user];
        collateral[user] = 0;
        debt[user] = 0;
        collateralToken.transfer(msg.sender, seized);
    }
}
