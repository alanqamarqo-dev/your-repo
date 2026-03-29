// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * This contract has PURE BUSINESS LOGIC vulnerabilities — NOT pattern-based.
 * No reentrancy, no tx.origin, no unchecked calls.
 * A tool must UNDERSTAND the protocol logic to catch these.
 */

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

interface IPriceOracle {
    function getPrice(address token) external view returns (uint256);
}

contract VulnerableLending {
    
    // ═══════════════════════════════════════════════════════
    // STATE
    // ═══════════════════════════════════════════════════════
    
    mapping(address => mapping(address => uint256)) public deposits;  // user => token => amount
    mapping(address => mapping(address => uint256)) public borrows;   // user => token => amount
    mapping(address => bool) public supportedTokens;
    
    IPriceOracle public oracle;
    address public owner;
    
    uint256 public constant COLLATERAL_FACTOR = 75;  // 75%
    uint256 public constant LIQUIDATION_THRESHOLD = 80;  // 80%
    uint256 public constant LIQUIDATION_BONUS = 10;  // 10%
    
    // ═══════════════════════════════════════════════════════
    // BUG 1: donate() reduces user balance but doesn't update 
    //        health factor calculation — attacker can manipulate
    //        their own health factor through self-donation
    // ═══════════════════════════════════════════════════════
    
    function deposit(address token, uint256 amount) external {
        require(supportedTokens[token], "Token not supported");
        require(IERC20(token).transferFrom(msg.sender, address(this), amount), "Transfer failed");
        deposits[msg.sender][token] += amount;
    }
    
    function donateToReserves(address token, uint256 amount) external {
        require(deposits[msg.sender][token] >= amount, "Insufficient balance");
        // BUG: Reduces deposit but doesn't check if user has borrows
        // An attacker can deposit, borrow, then donate to become undercollateralized
        // without triggering liquidation checks
        deposits[msg.sender][token] -= amount;
        // reserves increase, but user's borrow remains
    }
    
    // ═══════════════════════════════════════════════════════
    // BUG 2: borrow() uses stale price — oracle can be 
    //        manipulated in the same transaction via flash loan
    // ═══════════════════════════════════════════════════════
    
    function borrow(address token, uint256 amount) external {
        uint256 collateralValue = getCollateralValue(msg.sender);
        uint256 borrowValue = getBorrowValue(msg.sender);
        
        uint256 tokenPrice = oracle.getPrice(token);
        uint256 newBorrowValue = borrowValue + (amount * tokenPrice / 1e18);
        
        // BUG: No flash loan protection — price can be manipulated
        // in the same transaction before calling borrow()
        require(newBorrowValue * 100 <= collateralValue * COLLATERAL_FACTOR, "Undercollateralized");
        
        borrows[msg.sender][token] += amount;
        require(IERC20(token).transfer(msg.sender, amount), "Transfer failed");
    }
    
    // ═══════════════════════════════════════════════════════
    // BUG 3: liquidate() allows self-liquidation — attacker
    //        can liquidate themselves to claim the bonus
    // ═══════════════════════════════════════════════════════
    
    function liquidate(address borrower, address collateralToken, address borrowToken, uint256 repayAmount) external {
        // BUG: No check that msg.sender != borrower
        // Attacker can self-liquidate to extract the liquidation bonus
        
        uint256 healthFactor = getHealthFactor(borrower);
        require(healthFactor < 1e18, "Cannot liquidate healthy position");
        
        // Repay debt
        require(IERC20(borrowToken).transferFrom(msg.sender, address(this), repayAmount), "Repay failed");
        borrows[borrower][borrowToken] -= repayAmount;
        
        // Calculate collateral to seize (with bonus!)
        uint256 borrowPrice = oracle.getPrice(borrowToken);
        uint256 collateralPrice = oracle.getPrice(collateralToken);
        uint256 seizeAmount = (repayAmount * borrowPrice * (100 + LIQUIDATION_BONUS)) / (collateralPrice * 100);
        
        deposits[borrower][collateralToken] -= seizeAmount;
        // BUG: Bonus goes to liquidator — if self-liquidating, net profit
        deposits[msg.sender][collateralToken] += seizeAmount;
    }

    // ═══════════════════════════════════════════════════════
    // BUG 4: withdraw() doesn't check borrow health after
    //        withdrawal — user can withdraw collateral while
    //        still having borrows
    // ═══════════════════════════════════════════════════════
    
    function withdraw(address token, uint256 amount) external {
        require(deposits[msg.sender][token] >= amount, "Insufficient balance");
        deposits[msg.sender][token] -= amount;
        
        // BUG: No health factor check after withdrawal!
        // User can withdraw all collateral while keeping borrows
        
        require(IERC20(token).transfer(msg.sender, amount), "Transfer failed");
    }
    
    // ═══════════════════════════════════════════════════════
    // BUG 5: Interest accrual missing — borrows don't grow
    //        over time, so protocol loses money
    // ═══════════════════════════════════════════════════════
    
    function getCollateralValue(address user) public view returns (uint256) {
        // Simplified — in real protocol would iterate all tokens
        return 0; // placeholder
    }
    
    function getBorrowValue(address user) public view returns (uint256) {
        return 0; // placeholder
    }
    
    function getHealthFactor(address user) public view returns (uint256) {
        uint256 collateral = getCollateralValue(user);
        uint256 borrow = getBorrowValue(user);
        if (borrow == 0) return type(uint256).max;
        return (collateral * LIQUIDATION_THRESHOLD * 1e18) / (borrow * 100);
    }
}
