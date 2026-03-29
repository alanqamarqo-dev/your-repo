// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// SAFE: Proper user-provided deadline with validation

interface IRouter {
    function swapExactTokensForTokens(
        uint amountIn, uint amountOutMin, address[] calldata path,
        address to, uint deadline
    ) external returns (uint[] memory);
}

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
}

contract SafeDeadlineSwapper {
    IRouter public router;

    constructor(address _router) {
        router = IRouter(_router);
    }

    // SAFE: User-provided deadline with validation
    function swap(
        address tokenIn, address tokenOut,
        uint256 amount, uint256 minOut, uint256 deadline
    ) external {
        require(deadline >= block.timestamp, "Expired");
        IERC20(tokenIn).approve(address(router), amount);
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;

        router.swapExactTokensForTokens(
            amount, minOut, path, msg.sender, deadline
        );
    }
}
