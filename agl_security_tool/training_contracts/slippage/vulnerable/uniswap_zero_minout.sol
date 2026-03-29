// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Swap with amountOutMin = 0 — no slippage protection

interface IUniswapV2Router {
    function swapExactTokensForTokens(
        uint amountIn, uint amountOutMin, address[] calldata path,
        address to, uint deadline
    ) external returns (uint[] memory amounts);
}

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract VulnerableSwapper {
    IUniswapV2Router public router;
    address public tokenA;
    address public tokenB;

    constructor(address _router, address _tokenA, address _tokenB) {
        router = IUniswapV2Router(_router);
        tokenA = _tokenA;
        tokenB = _tokenB;
    }

    // VULNERABILITY: amountOutMin = 0 allows sandwich attacks
    function swapTokens(uint256 amountIn) external {
        IERC20(tokenA).approve(address(router), amountIn);

        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;

        // amountOutMin = 0 means any output is accepted
        router.swapExactTokensForTokens(
            amountIn,
            0,  // VULNERABILITY: zero minimum output
            path,
            msg.sender,
            block.timestamp + 300
        );
    }

    // VULNERABILITY: removeLiquidity with both mins = 0
    function removeLiq(address pair, uint256 liquidity) external {
        // Both minimums are 0 — can be sandwiched
        // removeLiquidity(tokenA, tokenB, liquidity, 0, 0, msg.sender, deadline)
    }
}
