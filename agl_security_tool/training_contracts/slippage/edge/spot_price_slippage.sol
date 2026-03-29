// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// EDGE: Slippage protection exists but uses oracle price from same block (flashloanable)

interface IUniswapV2Router {
    function swapExactTokensForTokens(
        uint amountIn, uint amountOutMin, address[] calldata path,
        address to, uint deadline
    ) external returns (uint[] memory amounts);
    function getAmountsOut(uint amountIn, address[] calldata path)
        external view returns (uint[] memory amounts);
}

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
}

contract EdgeSlippageSwapper {
    IUniswapV2Router public router;
    address public tokenA;
    address public tokenB;

    constructor(address _router, address _tokenA, address _tokenB) {
        router = IUniswapV2Router(_router);
        tokenA = _tokenA;
        tokenB = _tokenB;
    }

    // EDGE: Uses spot-price from same block as minOut — manipulable via flash loan
    // This technically has slippage protection but it reads the manipulated price
    function swapWithSpotSlippage(uint256 amountIn) external {
        IERC20(tokenA).approve(address(router), amountIn);

        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;

        // Reads current pool price — attacker can manipulate in same tx
        uint[] memory expected = router.getAmountsOut(amountIn, path);
        uint256 minOut = expected[1] * 99 / 100;

        router.swapExactTokensForTokens(
            amountIn,
            minOut,
            path,
            msg.sender,
            block.timestamp + 300
        );
    }
}
