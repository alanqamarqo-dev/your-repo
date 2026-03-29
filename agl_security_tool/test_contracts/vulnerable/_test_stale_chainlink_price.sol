
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface AggregatorV3Interface {
    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    );
}

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
}

contract VulnerablePriceConsumer {
    AggregatorV3Interface public priceFeed;
    
    constructor(address _priceFeed) {
        priceFeed = AggregatorV3Interface(_priceFeed);
    }
    
    // VULNERABLE: No freshness check!
    // - No check: updatedAt > block.timestamp - MAX_DELAY
    // - No check: answeredInRound >= roundId
    // - No check: price > 0
    function getLatestPrice() public view returns (int256) {
        (
            ,
            int256 price,
            ,
            ,
            
        ) = priceFeed.latestRoundData();
        // Missing: require(price > 0, "negative price");
        // Missing: require(updatedAt > block.timestamp - 3600, "stale");
        // Missing: require(answeredInRound >= roundId, "stale round");
        return price;
    }
    
    function swap(uint256 amount) external {
        int256 price = getLatestPrice();  // Could be stale/zero/negative
        uint256 output = (amount * uint256(price)) / 1e8;
        // ... execute swap with potentially stale price
    }
}
