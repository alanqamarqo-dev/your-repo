// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Uses block.timestamp as deadline — provides no protection

interface IRouter {
    function swapExactTokensForTokens(
        uint amountIn, uint amountOutMin, address[] calldata path,
        address to, uint deadline
    ) external returns (uint[] memory);
    function addLiquidity(
        address tokenA, address tokenB,
        uint amountADesired, uint amountBDesired,
        uint amountAMin, uint amountBMin,
        address to, uint deadline
    ) external returns (uint amountA, uint amountB, uint liquidity);
}

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
}

contract NoDeadlineSwapper {
    IRouter public router;

    constructor(address _router) {
        router = IRouter(_router);
    }

    // VULNERABILITY: block.timestamp as deadline means tx always passes
    function swap(address tokenIn, address tokenOut, uint256 amount, uint256 minOut) external {
        IERC20(tokenIn).approve(address(router), amount);
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;

        router.swapExactTokensForTokens(
            amount,
            minOut,
            path,
            msg.sender,
            block.timestamp  // VULNERABILITY: always passes
        );
    }

    // VULNERABILITY: type(uint256).max as deadline
    function addLiq(address tA, address tB, uint256 amtA, uint256 amtB) external {
        IERC20(tA).approve(address(router), amtA);
        IERC20(tB).approve(address(router), amtB);

        router.addLiquidity(
            tA, tB, amtA, amtB, 0, 0, msg.sender,
            type(uint256).max  // VULNERABILITY: no deadline
        );
    }
}
