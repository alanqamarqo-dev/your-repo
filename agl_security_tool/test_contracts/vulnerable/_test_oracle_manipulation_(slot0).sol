
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IUniswapV3Pool {
    function slot0() external view returns (
        uint160 sqrtPriceX96,
        int24 tick,
        uint16 observationIndex,
        uint16 observationCardinality,
        uint16 observationCardinalityNext,
        uint8 feeProtocol,
        bool unlocked
    );
    function observe(uint32[] calldata secondsAgos) external view returns (
        int56[] memory tickCumulatives,
        uint160[] memory secondsPerLiquidityCumulativeX128s
    );
}

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract VulnerableLending {
    IUniswapV3Pool public priceOracle;
    IERC20 public collateralToken;
    IERC20 public borrowToken;
    
    mapping(address => uint256) public collateral;
    mapping(address => uint256) public debt;
    
    // VULNERABLE: Uses slot0() — instant spot price, manipulable via flash loan
    // Should use observe() with TWAP instead
    function getPrice() public view returns (uint256) {
        (uint160 sqrtPriceX96,,,,,,) = priceOracle.slot0();
        // Convert sqrtPriceX96 to price
        uint256 price = (uint256(sqrtPriceX96) * uint256(sqrtPriceX96)) >> 192;
        return price;
    }
    
    function deposit(uint256 amount) external {
        collateralToken.transferFrom(msg.sender, address(this), amount);
        collateral[msg.sender] += amount;
    }
    
    function borrow(uint256 amount) external {
        uint256 price = getPrice();  // Spot price — manipulable!
        uint256 collateralValue = collateral[msg.sender] * price;
        require(collateralValue >= amount * 15 / 10, "undercollateralized");
        
        debt[msg.sender] += amount;
        borrowToken.transfer(msg.sender, amount);
    }
    
    function liquidate(address user) external {
        uint256 price = getPrice();  // Spot price — manipulable!
        uint256 collateralValue = collateral[user] * price;
        require(collateralValue < debt[user], "not liquidatable");
        
        // Liquidate
        uint256 seized = collateral[user];
        collateral[user] = 0;
        debt[user] = 0;
        collateralToken.transfer(msg.sender, seized);
    }
}
