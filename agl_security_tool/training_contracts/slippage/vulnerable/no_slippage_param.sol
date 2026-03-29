// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Swap function with no slippage parameter at all

interface IRouter {
    function swapExactTokensForETH(
        uint amountIn, uint amountOutMin, address[] calldata path,
        address to, uint deadline
    ) external returns (uint[] memory);
}

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
}

contract NoSlippageSwapper {
    IRouter public router;
    address public token;
    address public WETH;

    constructor(address _router, address _token, address _weth) {
        router = IRouter(_router);
        token = _token;
        WETH = _weth;
    }

    // VULNERABILITY: No minimum output, no slippage calculation
    function sellAllTokens() external {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).approve(address(router), balance);

        address[] memory path = new address[](2);
        path[0] = token;
        path[1] = WETH;

        router.swapExactTokensForETH(
            balance,
            0,  // VULNERABILITY: accepts any output
            path,
            msg.sender,
            block.timestamp
        );
    }
}

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
}
