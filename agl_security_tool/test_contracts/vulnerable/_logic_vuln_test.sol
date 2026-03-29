// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * Lending Protocol with REAL business logic bugs
 * (inspired by Euler Finance $197M hack pattern)
 */

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract VulnerableLending {
    
    mapping(address => uint256) public deposits;
    mapping(address => uint256) public borrows;
    mapping(address => uint256) public collateral;
    
    uint256 public totalDeposits;
    uint256 public totalBorrows;
    uint256 public totalReserves;
    
    uint256 public constant COLLATERAL_FACTOR = 75; // 75%
    uint256 public constant LIQUIDATION_THRESHOLD = 80; // 80%
    uint256 public constant MIN_HEALTH_FACTOR = 1e18;
    
    IERC20 public token;
    IERC20 public collateralToken;
    
    // Oracle - uses spot price (no TWAP!)
    address public priceOracle;
    
    function getPrice() public view returns (uint256) {
        // BUG 1: Uses spot price from AMM - flash loan manipulable
        (uint256 reserve0, uint256 reserve1) = IUniswapPair(priceOracle).getReserves();
        return reserve0 * 1e18 / reserve1;
    }
    
    function deposit(uint256 amount) external {
        token.transferFrom(msg.sender, address(this), amount);
        deposits[msg.sender] += amount;
        totalDeposits += amount;
    }
    
    function borrow(uint256 amount) external {
        require(getHealthFactor(msg.sender) > MIN_HEALTH_FACTOR, "Unhealthy");
        
        borrows[msg.sender] += amount;
        totalBorrows += amount;
        token.transfer(msg.sender, amount);
        
        // BUG 2: Health factor checked BEFORE borrow is added
        // Should check AFTER: require(getHealthFactor(msg.sender) > MIN_HEALTH_FACTOR)
    }
    
    function donateToReserves(uint256 amount) external {
        // BUG 3: Euler-style - donate reduces YOUR deposit but doesn't trigger liquidation check
        require(deposits[msg.sender] >= amount, "Insufficient deposits");
        deposits[msg.sender] -= amount;
        totalReserves += amount;
        // No health factor check after reducing deposits!
        // Attacker: deposit → borrow max → donate deposit → now undercollateralized
        //           but no one can liquidate because donateToReserves doesn't check health
    }
    
    function liquidate(address user, uint256 repayAmount) external {
        // BUG 4: Liquidation uses same manipulable oracle
        require(getHealthFactor(user) < MIN_HEALTH_FACTOR, "Still healthy");
        
        uint256 collateralValue = collateral[user] * getPrice() / 1e18;
        // BUG 5: liquidation bonus calculated on full collateral, not repay amount
        uint256 bonus = collateralValue * 10 / 100; // 10% bonus
        uint256 seizeAmount = repayAmount + bonus;
        
        token.transferFrom(msg.sender, address(this), repayAmount);
        borrows[user] -= repayAmount;
        collateral[user] -= seizeAmount;
        collateral[msg.sender] += seizeAmount;
    }
    
    function getHealthFactor(address user) public view returns (uint256) {
        if (borrows[user] == 0) return type(uint256).max;
        
        uint256 collateralValue = collateral[user] * getPrice() / 1e18;
        uint256 adjustedCollateral = collateralValue * COLLATERAL_FACTOR / 100;
        
        // BUG 6: Division precision loss - divides before multiply
        return adjustedCollateral / borrows[user] * 1e18;
    }
    
    function withdraw(uint256 amount) external {
        require(deposits[msg.sender] >= amount, "Insufficient");
        deposits[msg.sender] -= amount;
        totalDeposits -= amount;
        token.transfer(msg.sender, amount);
        // BUG 7: No health factor check after withdraw
    }
    
    // BUG 8: No access control on interest rate setting
    function setInterestRate(uint256 newRate) external {
        // Missing: onlyOwner or onlyAdmin
        // Anyone can change the interest rate!
    }
    
    function calculateInterest(uint256 principal, uint256 rate, uint256 time) public pure returns (uint256) {
        // BUG 9: Rounding DOWN on interest calculation favors borrowers
        return principal * rate * time / 365 / 1e18 / 100;
    }
}

interface IUniswapPair {
    function getReserves() external view returns (uint256, uint256);
}
