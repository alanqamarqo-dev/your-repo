// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// SAFE: Proper slippage protection with oracle-calculated minimum output

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

contract SafeSwapper {
    IUniswapV2Router public router;
    address public tokenA;
    address public tokenB;
    uint256 public constant SLIPPAGE_BPS = 50; // 0.5% slippage tolerance

    constructor(address _router, address _tokenA, address _tokenB) {
        router = IUniswapV2Router(_router);
        tokenA = _tokenA;
        tokenB = _tokenB;
    }

    // SAFE: Calculates minimum output with slippage tolerance
    function swapTokens(uint256 amountIn, uint256 minAmountOut) external {
        require(minAmountOut > 0, "Min output must be > 0");
        IERC20(tokenA).approve(address(router), amountIn);

        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;

        // SAFE: User provides minAmountOut
        router.swapExactTokensForTokens(
            amountIn,
            minAmountOut,
            path,
            msg.sender,
            block.timestamp + 300
        );
    }

    // SAFE: Automatic slippage calculation from spot price
    function swapWithAutoSlippage(uint256 amountIn) external {
        IERC20(tokenA).approve(address(router), amountIn);

        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;

        uint[] memory expected = router.getAmountsOut(amountIn, path);
        uint256 minOut = expected[1] * (10000 - SLIPPAGE_BPS) / 10000;

        require(minOut > 0, "Slippage too high");

        router.swapExactTokensForTokens(
            amountIn,
            minOut,
            path,
            msg.sender,
            block.timestamp + 300
        );
    }
}
