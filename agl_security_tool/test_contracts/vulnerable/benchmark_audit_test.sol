// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// ═══════════════════════════════════════════════════════════
// BENCHMARK CONTRACT — 15 known vulnerabilities + 5 safe patterns
// Used to test AGL Security Tool detection accuracy
// ═══════════════════════════════════════════════════════════

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IOracle {
    function getPrice(address token) external view returns (uint256);
}

interface IFlashLender {
    function flashLoan(address borrower, uint256 amount) external;
}

// ═══════════════════════════════════════════════════════════
// CONTRACT 1: VulnerableVault — 8 vulnerabilities
// ═══════════════════════════════════════════════════════════

contract VulnerableVault {
    mapping(address => uint256) public balances;
    mapping(address => uint256) public shares;
    uint256 public totalShares;
    uint256 public totalDeposited;
    address public owner;
    address[] public depositors;
    IERC20 public token;
    IOracle public oracle;

    constructor(address _token, address _oracle) {
        owner = msg.sender;
        token = IERC20(_token);
        oracle = IOracle(_oracle);
    }

    // ═══ VULN 1: Classic Reentrancy (CRITICAL) ═══
    // External call before state update — textbook CEI violation
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient");
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Failed");
        
        balances[msg.sender] -= amount;  // STATE UPDATE AFTER CALL
    }

    // ═══ VULN 2: First Depositor Attack (HIGH) ═══
    // Share calculation without protection — classic ERC4626 inflation
    function deposit(uint256 amount) external {
        uint256 sharesToMint;
        if (totalShares == 0) {
            sharesToMint = amount;  // First depositor gets 1:1
        } else {
            sharesToMint = amount * totalShares / totalDeposited;  // Rounding attack
        }
        
        token.transferFrom(msg.sender, address(this), amount);
        shares[msg.sender] += sharesToMint;
        totalShares += sharesToMint;
        totalDeposited += amount;
        depositors.push(msg.sender);
    }

    // ═══ VULN 3: Oracle Manipulation (HIGH) ═══
    // Uses spot price — manipulable via flash loan
    function getTokenValue(uint256 amount) public view returns (uint256) {
        uint256 price = oracle.getPrice(address(token));
        return amount * price / 1e18;
    }

    // ═══ VULN 4: Unchecked ERC20 Return (HIGH) ═══
    // Some tokens return false instead of reverting
    function sendReward(address to, uint256 amount) external {
        require(msg.sender == owner, "Not owner");
        token.transfer(to, amount);  // Return value ignored!
    }

    // ═══ VULN 5: Unbounded Loop DoS (MEDIUM) ═══
    // Loops over all depositors — gas bomb
    function distributeRewards() external {
        uint256 reward = address(this).balance / depositors.length;
        for (uint256 i = 0; i < depositors.length; i++) {
            payable(depositors[i]).transfer(reward);
        }
    }

    // ═══ VULN 6: tx.origin Authentication (HIGH) ═══
    // Phishing vulnerability
    function emergencyWithdraw(address to) external {
        require(tx.origin == owner, "Not owner");
        payable(to).transfer(address(this).balance);
    }

    // ═══ VULN 7: Divide Before Multiply (MEDIUM) ═══
    // Precision loss
    function calculateFee(uint256 amount, uint256 rate, uint256 periods) public pure returns (uint256) {
        return amount / 10000 * rate * periods;  // Should be amount * rate * periods / 10000
    }

    // ═══ VULN 8: Missing Event (LOW) ═══
    // State change without event
    function setOwner(address newOwner) external {
        require(msg.sender == owner, "Not owner");
        owner = newOwner;
        // No event emitted!
    }

    receive() external payable {
        balances[msg.sender] += msg.value;
    }
}

// ═══════════════════════════════════════════════════════════
// CONTRACT 2: DangerousToken — 4 vulnerabilities
// ═══════════════════════════════════════════════════════════

contract DangerousToken {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    uint256 public totalSupply;
    address public owner;

    // ═══ VULN 9: Unprotected Withdraw (CRITICAL) ═══
    // Anyone can drain the contract
    function withdrawAll() external {
        uint256 balance = address(this).balance;
        (bool ok,) = msg.sender.call{value: balance}("");
        require(ok);
    }

    // ═══ VULN 10: Arbitrary transferFrom (HIGH) ═══
    // User-controlled `from` parameter
    function stealFrom(address from, address to, uint256 amount) external {
        IERC20(address(this)).transferFrom(from, to, amount);
    }

    // ═══ VULN 11: Unprotected selfdestruct (CRITICAL) ═══
    function kill() external {
        selfdestruct(payable(msg.sender));
    }

    // ═══ VULN 12: Dangerous delegatecall (CRITICAL) ═══
    function execute(address target, bytes calldata data) external {
        (bool ok,) = target.delegatecall(data);
        require(ok);
    }
}

// ═══════════════════════════════════════════════════════════
// CONTRACT 3: FlashLoanReceiver — 3 vulnerabilities
// ═══════════════════════════════════════════════════════════

contract FlashLoanReceiver {
    address public lender;
    mapping(address => uint256) public deposits;
    uint256 public totalDeposits;

    // ═══ VULN 13: Unchecked low-level call (HIGH) ═══
    function repay(address to, uint256 amount) external {
        to.call{value: amount}("");  // Return not checked!
    }

    // ═══ VULN 14: Fee-on-transfer not handled (MEDIUM) ═══
    function stake(uint256 amount) external {
        IERC20(lender).transferFrom(msg.sender, address(this), amount);
        deposits[msg.sender] += amount;  // Uses original amount, not received
        totalDeposits += amount;
    }

    // ═══ VULN 15: encodePacked collision (MEDIUM) ═══
    function getHash(string memory a, string memory b) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(a, b));
    }
}

// ═══════════════════════════════════════════════════════════
// CONTRACT 4: SafeVault — SHOULD NOT trigger findings
// ═══════════════════════════════════════════════════════════

contract SafeVault {
    mapping(address => uint256) public balances;
    address public owner;
    bool private locked;

    modifier nonReentrant() {
        require(!locked, "Locked");
        locked = true;
        _;
        locked = false;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    event OwnerChanged(address indexed oldOwner, address indexed newOwner);
    event Withdrawn(address indexed user, uint256 amount);

    // ═══ SAFE 1: CEI pattern — no reentrancy ═══
    function safeWithdraw(uint256 amount) external nonReentrant {
        require(balances[msg.sender] >= amount, "Insufficient");
        balances[msg.sender] -= amount;  // State updated BEFORE call
        (bool success,) = msg.sender.call{value: amount}("");
        require(success, "Failed");
        emit Withdrawn(msg.sender, amount);
    }

    // ═══ SAFE 2: Proper access control ═══
    function setOwner(address newOwner) external onlyOwner {
        emit OwnerChanged(owner, newOwner);
        owner = newOwner;
    }

    // ═══ SAFE 3: msg.sender authentication ═══
    function adminAction() external {
        require(msg.sender == owner, "Not authorized");
        // Safe operation
    }

    // ═══ SAFE 4: Checked low-level call ═══
    function safeSend(address to, uint256 amount) external onlyOwner {
        (bool success,) = to.call{value: amount}("");
        require(success, "Transfer failed");
    }

    // ═══ SAFE 5: View function — no state change ═══
    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }
}
