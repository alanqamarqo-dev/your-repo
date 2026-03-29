// SPDX-License-Identifier: Unlicense
pragma solidity ^0.8.13;

// ============================================================================
// Alchemix Finance - AlchemistV2 (Flattened)
// Self-repaying loans protocol - Main vault contract
// Bug Bounty: Up to $300,000 via Immunefi
// Source: https://github.com/alchemix-finance/v2-foundry/tree/master/src
// Version: 2.2.8
// ============================================================================

// --- Base Errors ---
error Unauthorized();
error IllegalState();
error IllegalArgument();

// --- Library: SafeCast ---
library SafeCast {
    function toInt256(uint256 y) internal pure returns (int256 z) {
        if (y >= 2**255) {
            revert IllegalArgument();
        }
        z = int256(y);
    }

    function toUint256(int256 y) internal pure returns (uint256 z) {
        if (y < 0) {
            revert IllegalArgument();
        }
        z = uint256(y);
    }
}

// --- Library: Sets ---
library Sets {
    using Sets for AddressSet;

    struct AddressSet {
        address[] values;
        mapping(address => uint256) indexes;
    }

    function add(AddressSet storage self, address value) internal returns (bool) {
        if (self.contains(value)) {
            return false;
        }
        self.values.push(value);
        self.indexes[value] = self.values.length;
        return true;
    }

    function remove(AddressSet storage self, address value) internal returns (bool) {
        uint256 index = self.indexes[value];
        if (index == 0) {
            return false;
        }
        index--;
        uint256 lastIndex = self.values.length - 1;
        if (index != lastIndex) {
            address lastValue = self.values[lastIndex];
            self.values[index] = lastValue;
            self.indexes[lastValue] = index + 1;
        }
        self.values.pop();
        delete self.indexes[value];
        return true;
    }

    function contains(AddressSet storage self, address value) internal view returns (bool) {
        return self.indexes[value] != 0;
    }
}

// --- Library: Limiters ---
library Limiters {
    using Limiters for LinearGrowthLimiter;

    uint256 constant public MAX_COOLDOWN_BLOCKS = 1 days / 12 seconds;
    uint256 constant public FIXED_POINT_SCALAR = 1e18;

    struct LinearGrowthLimiter {
        uint256 maximum;
        uint256 rate;
        uint256 lastValue;
        uint256 lastBlock;
        uint256 minLimit;
    }

    function createLinearGrowthLimiter(uint256 maximum, uint256 blocks, uint256 _minLimit)
        internal view returns (LinearGrowthLimiter memory)
    {
        if (blocks > MAX_COOLDOWN_BLOCKS) {
            revert IllegalArgument();
        }
        if (maximum < _minLimit) {
            revert IllegalArgument();
        }
        return LinearGrowthLimiter({
            maximum: maximum,
            rate: maximum * FIXED_POINT_SCALAR / blocks,
            lastValue: maximum,
            lastBlock: block.number,
            minLimit: _minLimit
        });
    }

    function configure(LinearGrowthLimiter storage self, uint256 maximum, uint256 blocks) internal {
        if (blocks > MAX_COOLDOWN_BLOCKS) {
            revert IllegalArgument();
        }
        if (maximum < self.minLimit) {
            revert IllegalArgument();
        }
        if (self.lastValue > maximum) {
            self.lastValue = maximum;
        }
        self.maximum = maximum;
        self.rate = maximum * FIXED_POINT_SCALAR / blocks;
    }

    function update(LinearGrowthLimiter storage self) internal {
        self.lastValue = self.get();
        self.lastBlock = block.number;
    }

    function increase(LinearGrowthLimiter storage self, uint256 amount) internal {
        uint256 value = self.get();
        self.lastValue = value + amount;
        self.lastBlock = block.number;
    }

    function decrease(LinearGrowthLimiter storage self, uint256 amount) internal {
        uint256 value = self.get();
        self.lastValue = value - amount;
        self.lastBlock = block.number;
    }

    function get(LinearGrowthLimiter storage self) internal view returns (uint256) {
        uint256 elapsed = block.number - self.lastBlock;
        if (elapsed == 0) {
            return self.lastValue;
        }
        uint256 delta = elapsed * self.rate / FIXED_POINT_SCALAR;
        uint256 value = self.lastValue + delta;
        return value > self.maximum ? self.maximum : value;
    }
}

// --- Library: TokenUtils ---
library TokenUtils {
    function expectDecimals(address token) internal view returns (uint8) {
        (bool success, bytes memory data) = token.staticcall(abi.encodeWithSignature("decimals()"));
        require(success, "TokenUtils: decimals failed");
        return abi.decode(data, (uint8));
    }

    function safeTransfer(address token, address recipient, uint256 amount) internal {
        (bool success, bytes memory data) = token.call(
            abi.encodeWithSignature("transfer(address,uint256)", recipient, amount)
        );
        require(success && (data.length == 0 || abi.decode(data, (bool))), "TokenUtils: transfer failed");
    }

    function safeTransferFrom(address token, address owner, address recipient, uint256 amount) internal {
        (bool success, bytes memory data) = token.call(
            abi.encodeWithSignature("transferFrom(address,address,uint256)", owner, recipient, amount)
        );
        require(success && (data.length == 0 || abi.decode(data, (bool))), "TokenUtils: transferFrom failed");
    }

    function safeApprove(address token, address spender, uint256 amount) internal {
        (bool success, bytes memory data) = token.call(
            abi.encodeWithSignature("approve(address,uint256)", spender, amount)
        );
        require(success && (data.length == 0 || abi.decode(data, (bool))), "TokenUtils: approve failed");
    }

    function safeMint(address token, address recipient, uint256 amount) internal {
        (bool success,) = token.call(
            abi.encodeWithSignature("mint(address,uint256)", recipient, amount)
        );
        require(success, "TokenUtils: mint failed");
    }

    function safeBurnFrom(address token, address owner, uint256 amount) internal {
        (bool success,) = token.call(
            abi.encodeWithSignature("burnFrom(address,uint256)", owner, amount)
        );
        require(success, "TokenUtils: burnFrom failed");
    }
}

// --- External Interfaces ---
interface IERC20TokenReceiver {
    function onERC20Received(address token, uint256 amount) external;
}

interface ITokenAdapter {
    function token() external view returns (address);
    function underlyingToken() external view returns (address);
    function price() external view returns (uint256);
    function wrap(uint256 amount, address recipient) external returns (uint256);
    function unwrap(uint256 amount, address recipient) external returns (uint256);
}

interface IAlchemicToken {
    function mint(address recipient, uint256 amount) external;
    function burnFrom(address owner, uint256 amount) external;
}

interface IWhitelist {
    function isWhitelisted(address account) external view returns (bool);
}

interface IRewardCollector {
    function claimAndDonateRewards(address token, uint256 minimumAmountOut) external returns (uint256);
}

// --- Base: Multicall ---
abstract contract Multicall {
    function multicall(bytes[] calldata data) external returns (bytes[] memory results) {
        results = new bytes[](data.length);
        for (uint256 i = 0; i < data.length; i++) {
            (bool success, bytes memory result) = address(this).delegatecall(data[i]);
            require(success);
            results[i] = result;
        }
    }
}

// --- Base: Mutex (Reentrancy Guard) ---
abstract contract Mutex {
    enum State { RESERVED, UNLOCKED, LOCKED }
    State private _state;

    modifier lock() {
        _claimLock();
        _;
        _freeLock();
    }

    function _claimLock() internal {
        if (State.LOCKED == _state) revert IllegalState();
        _state = State.LOCKED;
    }

    function _freeLock() internal {
        _state = State.UNLOCKED;
    }
}

// --- Initializable (simplified from OpenZeppelin) ---
abstract contract Initializable {
    uint8 private _initialized;
    bool private _initializing;

    modifier initializer() {
        require(!_initialized || _initializing, "Already initialized");
        bool isTopLevelCall = !_initializing;
        if (isTopLevelCall) {
            _initializing = true;
            _initialized = 1;
        }
        _;
        if (isTopLevelCall) {
            _initializing = false;
        }
    }
}

// --- IAlchemistV2 Errors ---
interface IAlchemistV2Errors {
    error UnsupportedToken(address token);
    error TokenDisabled(address token);
    error Undercollateralized();
    error ExpectedValueExceeded(address yieldToken, uint256 expectedValue, uint256 maximumExpectedValue);
    error LossExceeded(address yieldToken, uint256 loss, uint256 maximumLoss);
    error MintingLimitExceeded(uint256 amount, uint256 available);
    error RepayLimitExceeded(address underlyingToken, uint256 amount, uint256 available);
    error LiquidationLimitExceeded(address underlyingToken, uint256 amount, uint256 available);
    error SlippageExceeded(uint256 amount, uint256 minimumAmountOut);
}

// --- IAlchemistV2 Events ---
interface IAlchemistV2Events {
    event PendingAdminUpdated(address pendingAdmin);
    event AdminUpdated(address admin);
    event SentinelSet(address sentinel, bool flag);
    event KeeperSet(address sentinel, bool flag);
    event AddUnderlyingToken(address indexed underlyingToken);
    event AddYieldToken(address indexed yieldToken);
    event UnderlyingTokenEnabled(address indexed underlyingToken, bool enabled);
    event YieldTokenEnabled(address indexed yieldToken, bool enabled);
    event RepayLimitUpdated(address indexed underlyingToken, uint256 maximum, uint256 blocks);
    event LiquidationLimitUpdated(address indexed underlyingToken, uint256 maximum, uint256 blocks);
    event TransmuterUpdated(address transmuter);
    event MinimumCollateralizationUpdated(uint256 minimumCollateralization);
    event ProtocolFeeUpdated(uint256 protocolFee);
    event ProtocolFeeReceiverUpdated(address protocolFeeReceiver);
    event MintingLimitUpdated(uint256 maximum, uint256 blocks);
    event CreditUnlockRateUpdated(address yieldToken, uint256 blocks);
    event TokenAdapterUpdated(address yieldToken, address tokenAdapter);
    event MaximumExpectedValueUpdated(address indexed yieldToken, uint256 maximumExpectedValue);
    event MaximumLossUpdated(address indexed yieldToken, uint256 maximumLoss);
    event Snap(address indexed yieldToken, uint256 expectedValue);
    event SweepRewardTokens(address indexed rewardToken, uint256 amount);
    event SweepTokens(address indexed token, uint256 amount);
    event ApproveMint(address indexed owner, address indexed spender, uint256 amount);
    event ApproveWithdraw(address indexed owner, address indexed spender, address indexed yieldToken, uint256 amount);
    event Deposit(address indexed sender, address indexed yieldToken, uint256 amount, address recipient);
    event Withdraw(address indexed owner, address indexed yieldToken, uint256 shares, address recipient);
    event Mint(address indexed owner, uint256 amount, address recipient);
    event Burn(address indexed sender, uint256 amount, address recipient);
    event Repay(address indexed sender, address indexed underlyingToken, uint256 amount, address recipient, uint256 credit);
    event Liquidate(address indexed owner, address indexed yieldToken, address indexed underlyingToken, uint256 shares, uint256 credit);
    event Donate(address indexed sender, address indexed yieldToken, uint256 amount);
    event Harvest(address indexed yieldToken, uint256 minimumAmountOut, uint256 totalHarvested, uint256 credit);
}

// --- IAlchemistV2 Immutables ---
interface IAlchemistV2Immutables {
    function version() external view returns (string memory);
    function debtToken() external view returns (address);
}

// --- IAlchemistV2 State ---
interface IAlchemistV2State {
    struct UnderlyingTokenParams {
        uint8 decimals;
        uint256 conversionFactor;
        bool enabled;
    }

    struct YieldTokenParams {
        uint8 decimals;
        address underlyingToken;
        address adapter;
        uint256 maximumLoss;
        uint256 maximumExpectedValue;
        uint256 creditUnlockRate;
        uint256 activeBalance;
        uint256 harvestableBalance;
        uint256 totalShares;
        uint256 expectedValue;
        uint256 pendingCredit;
        uint256 distributedCredit;
        uint256 lastDistributionBlock;
        uint256 accruedWeight;
        bool enabled;
    }

    function admin() external view returns (address);
    function pendingAdmin() external view returns (address);
    function transferAdapter() external view returns (address);
    function sentinels(address sentinel) external view returns (bool);
    function keepers(address keeper) external view returns (bool);
    function transmuter() external view returns (address);
    function minimumCollateralization() external view returns (uint256);
    function protocolFee() external view returns (uint256);
    function protocolFeeReceiver() external view returns (address);
    function whitelist() external view returns (address);
    function getUnderlyingTokensPerShare(address yieldToken) external view returns (uint256);
    function getYieldTokensPerShare(address yieldToken) external view returns (uint256);
    function getSupportedUnderlyingTokens() external view returns (address[] memory);
    function getSupportedYieldTokens() external view returns (address[] memory);
    function isSupportedUnderlyingToken(address underlyingToken) external view returns (bool);
    function isSupportedYieldToken(address yieldToken) external view returns (bool);
    function accounts(address owner) external view returns (int256 debt, address[] memory depositedTokens);
    function positions(address owner, address yieldToken) external view returns (uint256 shares, uint256 lastAccruedWeight);
    function mintAllowance(address owner, address spender) external view returns (uint256);
    function withdrawAllowance(address owner, address spender, address yieldToken) external view returns (uint256);
    function getUnderlyingTokenParameters(address underlyingToken) external view returns (UnderlyingTokenParams memory);
    function getYieldTokenParameters(address yieldToken) external view returns (YieldTokenParams memory);
    function getMintLimitInfo() external view returns (uint256 currentLimit, uint256 rate, uint256 maximum);
    function getRepayLimitInfo(address underlyingToken) external view returns (uint256 currentLimit, uint256 rate, uint256 maximum);
    function getLiquidationLimitInfo(address underlyingToken) external view returns (uint256 currentLimit, uint256 rate, uint256 maximum);
    function totalValue(address account) external view returns (uint256);
}

// --- IAlchemistV2 Admin Actions ---
interface IAlchemistV2AdminActions {
    struct InitializationParams {
        address admin;
        address debtToken;
        address transmuter;
        uint256 minimumCollateralization;
        uint256 protocolFee;
        address protocolFeeReceiver;
        uint256 mintingLimitMinimum;
        uint256 mintingLimitMaximum;
        uint256 mintingLimitBlocks;
        address whitelist;
    }

    struct UnderlyingTokenConfig {
        uint256 repayLimitMinimum;
        uint256 repayLimitMaximum;
        uint256 repayLimitBlocks;
        uint256 liquidationLimitMinimum;
        uint256 liquidationLimitMaximum;
        uint256 liquidationLimitBlocks;
    }

    struct YieldTokenConfig {
        address adapter;
        uint256 maximumLoss;
        uint256 maximumExpectedValue;
        uint256 creditUnlockBlocks;
    }

    function initialize(InitializationParams memory params) external;
    function setPendingAdmin(address value) external;
    function acceptAdmin() external;
    function setSentinel(address sentinel, bool flag) external;
    function setKeeper(address keeper, bool flag) external;
    function addUnderlyingToken(address underlyingToken, UnderlyingTokenConfig calldata config) external;
    function addYieldToken(address yieldToken, YieldTokenConfig calldata config) external;
    function setUnderlyingTokenEnabled(address underlyingToken, bool enabled) external;
    function setYieldTokenEnabled(address yieldToken, bool enabled) external;
    function configureRepayLimit(address underlyingToken, uint256 maximum, uint256 blocks) external;
    function configureLiquidationLimit(address underlyingToken, uint256 maximum, uint256 blocks) external;
    function setTransmuter(address value) external;
    function setMinimumCollateralization(uint256 value) external;
    function setProtocolFee(uint256 value) external;
    function setProtocolFeeReceiver(address value) external;
    function configureMintingLimit(uint256 maximum, uint256 rate) external;
    function configureCreditUnlockRate(address yieldToken, uint256 blocks) external;
    function setTokenAdapter(address yieldToken, address adapter) external;
    function setMaximumExpectedValue(address yieldToken, uint256 value) external;
    function setMaximumLoss(address yieldToken, uint256 value) external;
    function snap(address yieldToken) external;
    function setTransferAdapterAddress(address transferAdapterAddress) external;
    function transferDebtV1(address owner, int256 debt) external;
}

// --- IAlchemistV2 Actions ---
interface IAlchemistV2Actions {
    function approveMint(address spender, uint256 amount) external;
    function approveWithdraw(address spender, address yieldToken, uint256 shares) external;
    function poke(address owner) external;
    function deposit(address yieldToken, uint256 amount, address recipient) external returns (uint256);
    function depositUnderlying(address yieldToken, uint256 amount, address recipient, uint256 minimumAmountOut) external returns (uint256);
    function withdraw(address yieldToken, uint256 shares, address recipient) external returns (uint256);
    function withdrawFrom(address owner, address yieldToken, uint256 shares, address recipient) external returns (uint256);
    function withdrawUnderlying(address yieldToken, uint256 shares, address recipient, uint256 minimumAmountOut) external returns (uint256);
    function withdrawUnderlyingFrom(address owner, address yieldToken, uint256 shares, address recipient, uint256 minimumAmountOut) external returns (uint256);
    function mint(uint256 amount, address recipient) external;
    function mintFrom(address owner, uint256 amount, address recipient) external;
    function burn(uint256 amount, address recipient) external returns (uint256);
    function repay(address underlyingToken, uint256 amount, address recipient) external returns (uint256);
    function liquidate(address yieldToken, uint256 shares, uint256 minimumAmountOut) external returns (uint256);
    function donate(address yieldToken, uint256 amount) external;
    function harvest(address yieldToken, uint256 minimumAmountOut) external;
}

// --- Combined IAlchemistV2 ---
interface IAlchemistV2 is
    IAlchemistV2Actions,
    IAlchemistV2AdminActions,
    IAlchemistV2Errors,
    IAlchemistV2Immutables,
    IAlchemistV2Events,
    IAlchemistV2State
{}

// ============================================================================
// Main Contract: AlchemistV2
// ============================================================================
contract AlchemistV2 is IAlchemistV2, Initializable, Multicall, Mutex {
    using Limiters for Limiters.LinearGrowthLimiter;
    using Sets for Sets.AddressSet;

    /// @notice A user account.
    struct Account {
        // Positive values indicate debt, negative values indicate credit.
        int256 debt;
        // The share balances for each yield token.
        mapping(address => uint256) balances;
        // The last values recorded for accrued weights for each yield token.
        mapping(address => uint256) lastAccruedWeights;
        // The set of yield tokens that the account has deposited into the system.
        Sets.AddressSet depositedTokens;
        // The allowances for mints.
        mapping(address => uint256) mintAllowances;
        // The allowances for withdrawals.
        mapping(address => mapping(address => uint256)) withdrawAllowances;
    }

    /// @notice The number of basis points there are to represent exactly 100%.
    uint256 public constant BPS = 10_000;

    /// @notice The scalar used for conversion of integral numbers to fixed point numbers.
    uint256 public constant FIXED_POINT_SCALAR = 1e18;

    /// @inheritdoc IAlchemistV2Immutables
    string public constant override version = "2.2.8";

    /// @inheritdoc IAlchemistV2Immutables
    address public override debtToken;

    /// @inheritdoc IAlchemistV2State
    address public override admin;

    /// @inheritdoc IAlchemistV2State
    address public override pendingAdmin;

    /// @inheritdoc IAlchemistV2State
    mapping(address => bool) public override sentinels;

    /// @inheritdoc IAlchemistV2State
    mapping(address => bool) public override keepers;

    /// @inheritdoc IAlchemistV2State
    address public override transmuter;

    /// @inheritdoc IAlchemistV2State
    uint256 public override minimumCollateralization;

    /// @inheritdoc IAlchemistV2State
    uint256 public override protocolFee;

    /// @inheritdoc IAlchemistV2State
    address public override protocolFeeReceiver;

    /// @inheritdoc IAlchemistV2State
    address public override whitelist;

    /// @dev A linear growth function that limits the amount of debt-token minted.
    Limiters.LinearGrowthLimiter private _mintingLimiter;

    // @dev The repay limiters for each underlying token.
    mapping(address => Limiters.LinearGrowthLimiter) private _repayLimiters;

    // @dev The liquidation limiters for each underlying token.
    mapping(address => Limiters.LinearGrowthLimiter) private _liquidationLimiters;

    /// @dev Accounts mapped by the address that owns them.
    mapping(address => Account) private _accounts;

    /// @dev Underlying token parameters mapped by token address.
    mapping(address => UnderlyingTokenParams) private _underlyingTokens;

    /// @dev Yield token parameters mapped by token address.
    mapping(address => YieldTokenParams) private _yieldTokens;

    /// @dev An iterable set of the underlying tokens that are supported by the system.
    Sets.AddressSet private _supportedUnderlyingTokens;

    /// @dev An iterable set of the yield tokens that are supported by the system.
    Sets.AddressSet private _supportedYieldTokens;

    /// @inheritdoc IAlchemistV2State
    address public override transferAdapter;

    constructor() initializer {}

    // ========================================================================
    // View Functions
    // ========================================================================

    /// @inheritdoc IAlchemistV2State
    function getYieldTokensPerShare(address yieldToken) external view override returns (uint256) {
        return convertSharesToYieldTokens(yieldToken, 10**_yieldTokens[yieldToken].decimals);
    }

    /// @inheritdoc IAlchemistV2State
    function getUnderlyingTokensPerShare(address yieldToken) external view override returns (uint256) {
        return convertSharesToUnderlyingTokens(yieldToken, 10**_yieldTokens[yieldToken].decimals);
    }

    /// @inheritdoc IAlchemistV2State
    function getSupportedUnderlyingTokens() external view override returns (address[] memory) {
        return _supportedUnderlyingTokens.values;
    }

    /// @inheritdoc IAlchemistV2State
    function getSupportedYieldTokens() external view override returns (address[] memory) {
        return _supportedYieldTokens.values;
    }

    /// @inheritdoc IAlchemistV2State
    function isSupportedUnderlyingToken(address underlyingToken) external view override returns (bool) {
        return _supportedUnderlyingTokens.contains(underlyingToken);
    }

    /// @inheritdoc IAlchemistV2State
    function isSupportedYieldToken(address yieldToken) external view override returns (bool) {
        return _supportedYieldTokens.contains(yieldToken);
    }

    /// @inheritdoc IAlchemistV2State
    function accounts(address owner)
        external view override
        returns (
            int256 debt,
            address[] memory depositedTokens
        )
    {
        Account storage account = _accounts[owner];
        return (
            _calculateUnrealizedDebt(owner),
            account.depositedTokens.values
        );
    }

    /// @inheritdoc IAlchemistV2State
    function positions(address owner, address yieldToken)
        external view override
        returns (
            uint256 shares,
            uint256 lastAccruedWeight
        )
    {
        Account storage account = _accounts[owner];
        return (account.balances[yieldToken], account.lastAccruedWeights[yieldToken]);
    }

    /// @inheritdoc IAlchemistV2State
    function mintAllowance(address owner, address spender)
        external view override
        returns (uint256)
    {
        Account storage account = _accounts[owner];
        return account.mintAllowances[spender];
    }

    /// @inheritdoc IAlchemistV2State
    function withdrawAllowance(address owner, address spender, address yieldToken)
        external view override
        returns (uint256)
    {
        Account storage account = _accounts[owner];
        return account.withdrawAllowances[spender][yieldToken];
    }

    /// @inheritdoc IAlchemistV2State
    function getUnderlyingTokenParameters(address underlyingToken)
        external view override
        returns (UnderlyingTokenParams memory)
    {
        return _underlyingTokens[underlyingToken];
    }

    /// @inheritdoc IAlchemistV2State
    function getYieldTokenParameters(address yieldToken)
        external view override
        returns (YieldTokenParams memory)
    {
        return _yieldTokens[yieldToken];
    }

    /// @inheritdoc IAlchemistV2State
    function getMintLimitInfo()
        external view override
        returns (
            uint256 currentLimit,
            uint256 rate,
            uint256 maximum
        )
    {
        return (
            _mintingLimiter.get(),
            _mintingLimiter.rate,
            _mintingLimiter.maximum
        );
    }

    /// @inheritdoc IAlchemistV2State
    function getRepayLimitInfo(address underlyingToken)
        external view override
        returns (
            uint256 currentLimit,
            uint256 rate,
            uint256 maximum
        )
    {
        Limiters.LinearGrowthLimiter storage limiter = _repayLimiters[underlyingToken];
        return (
            limiter.get(),
            limiter.rate,
            limiter.maximum
        );
    }

    /// @inheritdoc IAlchemistV2State
    function getLiquidationLimitInfo(address underlyingToken)
        external view override
        returns (
            uint256 currentLimit,
            uint256 rate,
            uint256 maximum
        )
    {
        Limiters.LinearGrowthLimiter storage limiter = _liquidationLimiters[underlyingToken];
        return (
            limiter.get(),
            limiter.rate,
            limiter.maximum
        );
    }

    // ========================================================================
    // Admin Functions
    // ========================================================================

    /// @inheritdoc IAlchemistV2AdminActions
    function initialize(InitializationParams memory params) external initializer {
        _checkArgument(params.protocolFee <= BPS);

        debtToken                = params.debtToken;
        admin                    = params.admin;
        transmuter               = params.transmuter;
        minimumCollateralization = params.minimumCollateralization;
        protocolFee              = params.protocolFee;
        protocolFeeReceiver      = params.protocolFeeReceiver;
        whitelist                = params.whitelist;

        _mintingLimiter = Limiters.createLinearGrowthLimiter(
            params.mintingLimitMaximum,
            params.mintingLimitBlocks,
            params.mintingLimitMinimum
        );

        emit AdminUpdated(admin);
        emit TransmuterUpdated(transmuter);
        emit MinimumCollateralizationUpdated(minimumCollateralization);
        emit ProtocolFeeUpdated(protocolFee);
        emit MintingLimitUpdated(params.mintingLimitMaximum, params.mintingLimitBlocks);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setPendingAdmin(address value) external override {
        _onlyAdmin();
        pendingAdmin = value;
        emit PendingAdminUpdated(value);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function acceptAdmin() external override {
        _checkState(pendingAdmin != address(0));
        if (msg.sender != pendingAdmin) {
            revert Unauthorized();
        }
        admin = pendingAdmin;
        pendingAdmin = address(0);
        emit AdminUpdated(admin);
        emit PendingAdminUpdated(address(0));
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setSentinel(address sentinel, bool flag) external override {
        _onlyAdmin();
        sentinels[sentinel] = flag;
        emit SentinelSet(sentinel, flag);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setKeeper(address keeper, bool flag) external override {
        _onlyAdmin();
        keepers[keeper] = flag;
        emit KeeperSet(keeper, flag);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function addUnderlyingToken(address underlyingToken, UnderlyingTokenConfig calldata config) external override lock {
        _onlyAdmin();
        _checkState(!_supportedUnderlyingTokens.contains(underlyingToken));

        uint8 tokenDecimals = TokenUtils.expectDecimals(underlyingToken);
        uint8 debtTokenDecimals = TokenUtils.expectDecimals(debtToken);

        _checkArgument(tokenDecimals <= debtTokenDecimals);

        _underlyingTokens[underlyingToken] = UnderlyingTokenParams({
            decimals:         tokenDecimals,
            conversionFactor: 10**(debtTokenDecimals - tokenDecimals),
            enabled:          false
        });

        _repayLimiters[underlyingToken] = Limiters.createLinearGrowthLimiter(
            config.repayLimitMaximum,
            config.repayLimitBlocks,
            config.repayLimitMinimum
        );

        _liquidationLimiters[underlyingToken] = Limiters.createLinearGrowthLimiter(
            config.liquidationLimitMaximum,
            config.liquidationLimitBlocks,
            config.liquidationLimitMinimum
        );

        _supportedUnderlyingTokens.add(underlyingToken);

        emit AddUnderlyingToken(underlyingToken);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function addYieldToken(address yieldToken, YieldTokenConfig calldata config) external override lock {
        _onlyAdmin();
        _checkArgument(config.maximumLoss <= BPS);
        _checkArgument(config.creditUnlockBlocks > 0);

        _checkState(!_supportedYieldTokens.contains(yieldToken));

        ITokenAdapter adapter = ITokenAdapter(config.adapter);

        _checkState(yieldToken == adapter.token());
        _checkSupportedUnderlyingToken(adapter.underlyingToken());

        _yieldTokens[yieldToken] = YieldTokenParams({
            decimals:              TokenUtils.expectDecimals(yieldToken),
            underlyingToken:       adapter.underlyingToken(),
            adapter:               config.adapter,
            maximumLoss:           config.maximumLoss,
            maximumExpectedValue:  config.maximumExpectedValue,
            creditUnlockRate:      FIXED_POINT_SCALAR / config.creditUnlockBlocks,
            activeBalance:         0,
            harvestableBalance:    0,
            totalShares:           0,
            expectedValue:         0,
            accruedWeight:         0,
            pendingCredit:         0,
            distributedCredit:     0,
            lastDistributionBlock: 0,
            enabled:               false
        });

        _supportedYieldTokens.add(yieldToken);

        TokenUtils.safeApprove(yieldToken, config.adapter, type(uint256).max);
        TokenUtils.safeApprove(adapter.underlyingToken(), config.adapter, type(uint256).max);

        emit AddYieldToken(yieldToken);
        emit TokenAdapterUpdated(yieldToken, config.adapter);
        emit MaximumLossUpdated(yieldToken, config.maximumLoss);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setUnderlyingTokenEnabled(address underlyingToken, bool enabled) external override {
        _onlySentinelOrAdmin();
        _checkSupportedUnderlyingToken(underlyingToken);
        _underlyingTokens[underlyingToken].enabled = enabled;
        emit UnderlyingTokenEnabled(underlyingToken, enabled);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setYieldTokenEnabled(address yieldToken, bool enabled) external override {
        _onlySentinelOrAdmin();
        _checkSupportedYieldToken(yieldToken);
        _yieldTokens[yieldToken].enabled = enabled;
        emit YieldTokenEnabled(yieldToken, enabled);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function configureRepayLimit(address underlyingToken, uint256 maximum, uint256 blocks) external override {
        _onlyAdmin();
        _checkSupportedUnderlyingToken(underlyingToken);
        _repayLimiters[underlyingToken].update();
        _repayLimiters[underlyingToken].configure(maximum, blocks);
        emit RepayLimitUpdated(underlyingToken, maximum, blocks);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function configureLiquidationLimit(address underlyingToken, uint256 maximum, uint256 blocks) external override {
        _onlyAdmin();
        _checkSupportedUnderlyingToken(underlyingToken);
        _liquidationLimiters[underlyingToken].update();
        _liquidationLimiters[underlyingToken].configure(maximum, blocks);
        emit LiquidationLimitUpdated(underlyingToken, maximum, blocks);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setTransmuter(address value) external override {
        _onlyAdmin();
        _checkArgument(value != address(0));
        transmuter = value;
        emit TransmuterUpdated(value);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setMinimumCollateralization(uint256 value) external override {
        _onlyAdmin();
        _checkArgument(value >= 1e18);
        minimumCollateralization = value;
        emit MinimumCollateralizationUpdated(value);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setProtocolFee(uint256 value) external override {
        _onlyAdmin();
        _checkArgument(value <= BPS);
        protocolFee = value;
        emit ProtocolFeeUpdated(value);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setProtocolFeeReceiver(address value) external override {
        _onlyAdmin();
        _checkArgument(value != address(0));
        protocolFeeReceiver = value;
        emit ProtocolFeeReceiverUpdated(value);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function configureMintingLimit(uint256 maximum, uint256 rate) external override {
        _onlyAdmin();
        _mintingLimiter.update();
        _mintingLimiter.configure(maximum, rate);
        emit MintingLimitUpdated(maximum, rate);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function configureCreditUnlockRate(address yieldToken, uint256 blocks) external override {
        _onlyAdmin();
        _checkArgument(blocks > 0);
        _checkSupportedYieldToken(yieldToken);
        _yieldTokens[yieldToken].creditUnlockRate = FIXED_POINT_SCALAR / blocks;
        emit CreditUnlockRateUpdated(yieldToken, blocks);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setTokenAdapter(address yieldToken, address adapter) external override {
        _onlyAdmin();
        _checkState(yieldToken == ITokenAdapter(adapter).token());
        _checkSupportedYieldToken(yieldToken);
        _yieldTokens[yieldToken].adapter = adapter;
        TokenUtils.safeApprove(yieldToken, adapter, type(uint256).max);
        TokenUtils.safeApprove(ITokenAdapter(adapter).underlyingToken(), adapter, type(uint256).max);
        emit TokenAdapterUpdated(yieldToken, adapter);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setMaximumExpectedValue(address yieldToken, uint256 value) external override {
        _onlyAdmin();
        _checkSupportedYieldToken(yieldToken);
        _yieldTokens[yieldToken].maximumExpectedValue = value;
        emit MaximumExpectedValueUpdated(yieldToken, value);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setMaximumLoss(address yieldToken, uint256 value) external override {
        _onlyAdmin();
        _checkArgument(value <= BPS);
        _checkSupportedYieldToken(yieldToken);
        _yieldTokens[yieldToken].maximumLoss = value;
        emit MaximumLossUpdated(yieldToken, value);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function snap(address yieldToken) external override lock {
        _onlyAdmin();
        _checkSupportedYieldToken(yieldToken);
        uint256 expectedValue = convertYieldTokensToUnderlying(yieldToken, _yieldTokens[yieldToken].activeBalance);
        _yieldTokens[yieldToken].expectedValue = expectedValue;
        emit Snap(yieldToken, expectedValue);
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function setTransferAdapterAddress(address transferAdapterAddress) external override lock {
        _onlyAdmin();
        transferAdapter = transferAdapterAddress;
    }

    /// @inheritdoc IAlchemistV2AdminActions
    function transferDebtV1(
        address owner,
        int256 debt
    ) external override lock {
        _onlyTransferAdapter();
        _poke(owner);
        _updateDebt(owner, debt);
        _validate(owner);
    }

    // ========================================================================
    // User Actions
    // ========================================================================

    /// @inheritdoc IAlchemistV2Actions
    function approveMint(address spender, uint256 amount) external override {
        _onlyWhitelisted();
        _approveMint(msg.sender, spender, amount);
    }

    /// @inheritdoc IAlchemistV2Actions
    function approveWithdraw(address spender, address yieldToken, uint256 shares) external override {
        _onlyWhitelisted();
        _checkSupportedYieldToken(yieldToken);
        _approveWithdraw(msg.sender, spender, yieldToken, shares);
    }

    /// @inheritdoc IAlchemistV2Actions
    function poke(address owner) external override lock {
        _onlyWhitelisted();
        _preemptivelyHarvestDeposited(owner);
        _distributeUnlockedCreditDeposited(owner);
        _poke(owner);
    }

    /// @inheritdoc IAlchemistV2Actions
    function deposit(
        address yieldToken,
        uint256 amount,
        address recipient
    ) external override lock returns (uint256) {
        _onlyWhitelisted();
        _checkArgument(recipient != address(0));
        _checkSupportedYieldToken(yieldToken);

        // Deposit the yield tokens to the recipient.
        uint256 shares = _deposit(yieldToken, amount, recipient);

        // Transfer tokens from the message sender now that the internal storage updates have been committed.
        TokenUtils.safeTransferFrom(yieldToken, msg.sender, address(this), amount);

        return shares;
    }

    /// @inheritdoc IAlchemistV2Actions
    function depositUnderlying(
        address yieldToken,
        uint256 amount,
        address recipient,
        uint256 minimumAmountOut
    ) external override lock returns (uint256) {
        _onlyWhitelisted();
        _checkArgument(recipient != address(0));
        _checkSupportedYieldToken(yieldToken);

        // Before depositing, the underlying tokens must be wrapped into yield tokens.
        uint256 amountYieldTokens = _wrap(yieldToken, amount, minimumAmountOut);

        // Deposit the yield-tokens to the recipient.
        return _deposit(yieldToken, amountYieldTokens, recipient);
    }

    /// @inheritdoc IAlchemistV2Actions
    function withdraw(
        address yieldToken,
        uint256 shares,
        address recipient
    ) external override lock returns (uint256) {
        _onlyWhitelisted();
        _checkArgument(recipient != address(0));
        _checkSupportedYieldToken(yieldToken);

        // Withdraw the shares from the system.
        uint256 amountYieldTokens = _withdraw(yieldToken, msg.sender, shares, recipient);

        // Transfer the yield tokens to the recipient.
        TokenUtils.safeTransfer(yieldToken, recipient, amountYieldTokens);

        return amountYieldTokens;
    }

    /// @inheritdoc IAlchemistV2Actions
    function withdrawFrom(
        address owner,
        address yieldToken,
        uint256 shares,
        address recipient
    ) external override lock returns (uint256) {
        _onlyWhitelisted();
        _checkArgument(recipient != address(0));
        _checkSupportedYieldToken(yieldToken);

        // Preemptively try and decrease the withdrawal allowance.
        _decreaseWithdrawAllowance(owner, msg.sender, yieldToken, shares);

        // Withdraw the shares from the system.
        uint256 amountYieldTokens = _withdraw(yieldToken, owner, shares, recipient);

        // Transfer the yield tokens to the recipient.
        TokenUtils.safeTransfer(yieldToken, recipient, amountYieldTokens);

        return amountYieldTokens;
    }

    /// @inheritdoc IAlchemistV2Actions
    function withdrawUnderlying(
        address yieldToken,
        uint256 shares,
        address recipient,
        uint256 minimumAmountOut
    ) external override lock returns (uint256) {
        _onlyWhitelisted();
        _checkArgument(recipient != address(0));
        _checkSupportedYieldToken(yieldToken);
        _checkLoss(yieldToken);

        uint256 amountYieldTokens = _withdraw(yieldToken, msg.sender, shares, recipient);

        return _unwrap(yieldToken, amountYieldTokens, recipient, minimumAmountOut);
    }

    /// @inheritdoc IAlchemistV2Actions
    function withdrawUnderlyingFrom(
        address owner,
        address yieldToken,
        uint256 shares,
        address recipient,
        uint256 minimumAmountOut
    ) external override lock returns (uint256) {
        _onlyWhitelisted();
        _checkArgument(recipient != address(0));
        _checkSupportedYieldToken(yieldToken);
        _checkLoss(yieldToken);
        _decreaseWithdrawAllowance(owner, msg.sender, yieldToken, shares);

        uint256 amountYieldTokens = _withdraw(yieldToken, owner, shares, recipient);

        return _unwrap(yieldToken, amountYieldTokens, recipient, minimumAmountOut);
    }

    /// @inheritdoc IAlchemistV2Actions
    function mint(uint256 amount, address recipient) external override lock {
        _onlyWhitelisted();
        _checkArgument(amount > 0);
        _checkArgument(recipient != address(0));

        // Mint tokens from the message sender's account to the recipient.
        _mint(msg.sender, amount, recipient);
    }

    /// @inheritdoc IAlchemistV2Actions
    function mintFrom(
        address owner,
        uint256 amount,
        address recipient
    ) external override lock {
        _onlyWhitelisted();
        _checkArgument(amount > 0);
        _checkArgument(recipient != address(0));

        // Preemptively try and decrease the minting allowance.
        _decreaseMintAllowance(owner, msg.sender, amount);

        // Mint tokens from the owner's account to the recipient.
        _mint(owner, amount, recipient);
    }

    /// @inheritdoc IAlchemistV2Actions
    function burn(uint256 amount, address recipient) external override lock returns (uint256) {
        _onlyWhitelisted();

        _checkArgument(amount > 0);
        _checkArgument(recipient != address(0));

        // Distribute unlocked credit to depositors.
        _distributeUnlockedCreditDeposited(recipient);

        // Update the recipient's account, decrease the debt of the recipient by the number of tokens burned.
        _poke(recipient);

        // Check that the debt is greater than zero.
        int256 debt;
        _checkState((debt = _accounts[recipient].debt) > 0);

        // Casts here are safe because it is asserted that debt is greater than zero.
        uint256 credit = amount > uint256(debt) ? uint256(debt) : amount;

        // Update the recipient's debt.
        _updateDebt(recipient, -SafeCast.toInt256(credit));

        // Burn the tokens from the message sender.
        TokenUtils.safeBurnFrom(debtToken, msg.sender, credit);

        // Increase the global amount of mintable debt tokens.
        _mintingLimiter.increase(credit);

        emit Burn(msg.sender, credit, recipient);

        return credit;
    }

    /// @inheritdoc IAlchemistV2Actions
    function repay(address underlyingToken, uint256 amount, address recipient) external override lock returns (uint256) {
        _onlyWhitelisted();

        _checkArgument(amount > 0);
        _checkArgument(recipient != address(0));

        _checkSupportedUnderlyingToken(underlyingToken);
        _checkUnderlyingTokenEnabled(underlyingToken);

        // Distribute unlocked credit to depositors.
        _distributeUnlockedCreditDeposited(recipient);

        // Update the recipient's account and decrease the amount of debt incurred.
        _poke(recipient);

        // Check that the debt is greater than zero.
        int256 debt;
        _checkState((debt = _accounts[recipient].debt) > 0);

        // Determine the maximum amount of underlying tokens that can be repaid.
        uint256 maximumAmount = normalizeDebtTokensToUnderlying(underlyingToken, uint256(debt));

        // Limit the number of underlying tokens to repay up to the maximum allowed.
        uint256 actualAmount = amount > maximumAmount ? maximumAmount : amount;

        Limiters.LinearGrowthLimiter storage limiter = _repayLimiters[underlyingToken];

        // Check to make sure that the underlying token repay limit has not been breached.
        uint256 currentRepayLimit = limiter.get();
        if (actualAmount > currentRepayLimit) {
            revert RepayLimitExceeded(underlyingToken, actualAmount, currentRepayLimit);
        }

        uint256 credit = normalizeUnderlyingTokensToDebt(underlyingToken, actualAmount);

        // Update the recipient's debt.
        _updateDebt(recipient, -SafeCast.toInt256(credit));

        // Decrease the amount of the underlying token which is globally available to be repaid.
        limiter.decrease(actualAmount);

        // Transfer the repaid tokens to the transmuter.
        TokenUtils.safeTransferFrom(underlyingToken, msg.sender, transmuter, actualAmount);

        // Inform the transmuter that it has received tokens.
        IERC20TokenReceiver(transmuter).onERC20Received(underlyingToken, actualAmount);

        emit Repay(msg.sender, underlyingToken, actualAmount, recipient, credit);

        return actualAmount;
    }

    /// @inheritdoc IAlchemistV2Actions
    function liquidate(
        address yieldToken,
        uint256 shares,
        uint256 minimumAmountOut
    ) external override lock returns (uint256) {
        _onlyWhitelisted();

        _checkArgument(shares > 0);

        YieldTokenParams storage yieldTokenParams = _yieldTokens[yieldToken];
        address underlyingToken = yieldTokenParams.underlyingToken;

        _checkSupportedYieldToken(yieldToken);
        _checkYieldTokenEnabled(yieldToken);
        _checkUnderlyingTokenEnabled(underlyingToken);
        _checkLoss(yieldToken);

        // Calculate the unrealized debt.
        int256 unrealizedDebt;
        _checkState((unrealizedDebt = _calculateUnrealizedDebt(msg.sender)) > 0);

        // Determine the maximum amount of shares that can be liquidated from the unrealized debt.
        uint256 maximumShares = convertUnderlyingTokensToShares(
            yieldToken,
            normalizeDebtTokensToUnderlying(underlyingToken, uint256(unrealizedDebt))
        );

        // Limit the number of shares to liquidate up to the maximum allowed.
        uint256 actualShares = shares > maximumShares ? maximumShares : shares;

        // Unwrap the yield tokens that the shares are worth.
        uint256 amountYieldTokens      = convertSharesToYieldTokens(yieldToken, actualShares);
        uint256 amountUnderlyingTokens = _unwrap(yieldToken, amountYieldTokens, address(this), minimumAmountOut);

        // Perform another noop check.
        _checkState(amountUnderlyingTokens > 0);

        Limiters.LinearGrowthLimiter storage limiter = _liquidationLimiters[underlyingToken];

        // Check to make sure that the underlying token liquidation limit has not been breached.
        uint256 liquidationLimit = limiter.get();
        if (amountUnderlyingTokens > liquidationLimit) {
            revert LiquidationLimitExceeded(underlyingToken, amountUnderlyingTokens, liquidationLimit);
        }

        // Buffers any harvestable yield tokens.
        _preemptivelyHarvest(yieldToken);

        // Distribute unlocked credit to depositors.
        _distributeUnlockedCreditDeposited(msg.sender);

        uint256 credit = normalizeUnderlyingTokensToDebt(underlyingToken, amountUnderlyingTokens);

        // Update the message sender's account, proactively burn shares, decrease the amount of debt incurred.
        _poke(msg.sender, yieldToken);
        _burnShares(msg.sender, yieldToken, actualShares);
        _updateDebt(msg.sender, -SafeCast.toInt256(credit));
        _sync(yieldToken, amountYieldTokens, _usub);

        // Decrease the amount of the underlying token which is globally available to be liquidated.
        limiter.decrease(amountUnderlyingTokens);

        // Transfer the liquidated tokens to the transmuter.
        TokenUtils.safeTransfer(underlyingToken, transmuter, amountUnderlyingTokens);

        // Inform the transmuter that it has received tokens.
        IERC20TokenReceiver(transmuter).onERC20Received(underlyingToken, amountUnderlyingTokens);

        // In the case that slippage allowed by minimumAmountOut would create an undercollateralized position
        _validate(msg.sender);

        emit Liquidate(msg.sender, yieldToken, underlyingToken, actualShares, credit);

        return actualShares;
    }

    /// @inheritdoc IAlchemistV2Actions
    function donate(address yieldToken, uint256 amount) external override lock {
        _onlyWhitelisted();
        _checkArgument(amount > 0);

        // Distribute any unlocked credit so that the accrued weight is up to date.
        _distributeUnlockedCredit(yieldToken);

        // Update the message sender's account. This will assure that any credit that was earned is not overridden.
        _poke(msg.sender);

        uint256 shares = _yieldTokens[yieldToken].totalShares - _accounts[msg.sender].balances[yieldToken];

        _yieldTokens[yieldToken].accruedWeight += amount * FIXED_POINT_SCALAR / shares;
        _accounts[msg.sender].lastAccruedWeights[yieldToken] = _yieldTokens[yieldToken].accruedWeight;

        TokenUtils.safeBurnFrom(debtToken, msg.sender, amount);

        // Increase the global amount of mintable debt tokens.
        _mintingLimiter.increase(amount);

        emit Donate(msg.sender, yieldToken, amount);
    }

    /// @inheritdoc IAlchemistV2Actions
    function harvest(address yieldToken, uint256 minimumAmountOut) external override lock {
        _onlyKeeper();
        _checkSupportedYieldToken(yieldToken);

        YieldTokenParams storage yieldTokenParams = _yieldTokens[yieldToken];

        // Buffer any harvestable yield tokens.
        _preemptivelyHarvest(yieldToken);

        // Load and proactively clear the amount of harvestable tokens.
        uint256 harvestableAmount = yieldTokenParams.harvestableBalance;
        yieldTokenParams.harvestableBalance = 0;

        // Check that the harvest will not be a no-op.
        _checkState(harvestableAmount != 0);

        address underlyingToken = yieldTokenParams.underlyingToken;
        uint256 amountUnderlyingTokens = _unwrap(yieldToken, harvestableAmount, address(this), minimumAmountOut);

        // Calculate how much of the unwrapped underlying tokens will be allocated for fees and distributed to users.
        uint256 feeAmount = amountUnderlyingTokens * protocolFee / BPS;
        uint256 distributeAmount = amountUnderlyingTokens - feeAmount;

        uint256 credit = normalizeUnderlyingTokensToDebt(underlyingToken, distributeAmount);

        // Distribute credit to all of the users who hold shares of the yield token.
        _distributeCredit(yieldToken, credit);

        // Transfer the tokens to the fee receiver and transmuter.
        TokenUtils.safeTransfer(underlyingToken, protocolFeeReceiver, feeAmount);
        TokenUtils.safeTransfer(underlyingToken, transmuter, distributeAmount);

        // Inform the transmuter that it has received tokens.
        IERC20TokenReceiver(transmuter).onERC20Received(underlyingToken, distributeAmount);

        emit Harvest(yieldToken, minimumAmountOut, amountUnderlyingTokens, credit);
    }

    // ========================================================================
    // Internal Functions - Access Control
    // ========================================================================

    function _onlyAdmin() internal view {
        if (msg.sender != admin) {
            revert Unauthorized();
        }
    }

    function _onlySentinelOrAdmin() internal view {
        if (msg.sender == admin) {
            return;
        }
        if (!sentinels[msg.sender]) {
            revert Unauthorized();
        }
    }

    function _onlyKeeper() internal view {
        if (!keepers[msg.sender]) {
            revert Unauthorized();
        }
    }

    function _onlyTransferAdapter() internal view {
        if (msg.sender != transferAdapter) {
            revert Unauthorized();
        }
    }

    // ========================================================================
    // Internal Functions - Harvesting
    // ========================================================================

    function _preemptivelyHarvestDeposited(address owner) internal {
        Sets.AddressSet storage depositedTokens = _accounts[owner].depositedTokens;
        for (uint256 i = 0; i < depositedTokens.values.length; ++i) {
            _preemptivelyHarvest(depositedTokens.values[i]);
        }
    }

    function _preemptivelyHarvest(address yieldToken) internal {
        uint256 activeBalance = _yieldTokens[yieldToken].activeBalance;
        if (activeBalance == 0) {
            return;
        }

        uint256 currentValue = convertYieldTokensToUnderlying(yieldToken, activeBalance);
        uint256 expectedValue = _yieldTokens[yieldToken].expectedValue;
        if (currentValue <= expectedValue) {
            return;
        }

        uint256 harvestable = convertUnderlyingTokensToYield(yieldToken, currentValue - expectedValue);
        if (harvestable == 0) {
            return;
        }
        _yieldTokens[yieldToken].activeBalance -= harvestable;
        _yieldTokens[yieldToken].harvestableBalance += harvestable;
    }

    // ========================================================================
    // Internal Functions - Token Checks
    // ========================================================================

    function _checkYieldTokenEnabled(address yieldToken) internal view {
        if (!_yieldTokens[yieldToken].enabled) {
            revert TokenDisabled(yieldToken);
        }
    }

    function _checkUnderlyingTokenEnabled(address underlyingToken) internal view {
        if (!_underlyingTokens[underlyingToken].enabled) {
            revert TokenDisabled(underlyingToken);
        }
    }

    function _checkSupportedYieldToken(address yieldToken) internal view {
        if (!_supportedYieldTokens.contains(yieldToken)) {
            revert UnsupportedToken(yieldToken);
        }
    }

    function _checkSupportedUnderlyingToken(address underlyingToken) internal view {
        if (!_supportedUnderlyingTokens.contains(underlyingToken)) {
            revert UnsupportedToken(underlyingToken);
        }
    }

    function _checkMintingLimit(uint256 amount) internal view {
        uint256 limit = _mintingLimiter.get();
        if (amount > limit) {
            revert MintingLimitExceeded(amount, limit);
        }
    }

    function _checkLoss(address yieldToken) internal view {
        uint256 loss = _loss(yieldToken);
        uint256 maximumLoss = _yieldTokens[yieldToken].maximumLoss;
        if (loss > maximumLoss) {
            revert LossExceeded(yieldToken, loss, maximumLoss);
        }
    }

    // ========================================================================
    // Internal Functions - Core Logic
    // ========================================================================

    function _deposit(
        address yieldToken,
        uint256 amount,
        address recipient
    ) internal returns (uint256) {
        _checkArgument(amount > 0);

        YieldTokenParams storage yieldTokenParams = _yieldTokens[yieldToken];
        address underlyingToken = yieldTokenParams.underlyingToken;

        _checkYieldTokenEnabled(yieldToken);
        _checkUnderlyingTokenEnabled(underlyingToken);
        _checkLoss(yieldToken);

        // Buffers any harvestable yield tokens.
        _preemptivelyHarvest(yieldToken);

        // Distribute unlocked credit to depositors.
        _distributeUnlockedCreditDeposited(recipient);

        // Update the recipient's account.
        _poke(recipient, yieldToken);
        uint256 shares = _issueSharesForAmount(recipient, yieldToken, amount);
        _sync(yieldToken, amount, _uadd);

        // Check that the maximum expected value has not been breached.
        uint256 maximumExpectedValue = yieldTokenParams.maximumExpectedValue;
        if (yieldTokenParams.expectedValue > maximumExpectedValue) {
            revert ExpectedValueExceeded(yieldToken, amount, maximumExpectedValue);
        }

        emit Deposit(msg.sender, yieldToken, amount, recipient);

        return shares;
    }

    function _withdraw(
        address yieldToken,
        address owner,
        uint256 shares,
        address recipient
    ) internal returns (uint256) {
        // Buffers any harvestable yield tokens that the owner of the account has deposited.
        _preemptivelyHarvestDeposited(owner);

        // Distribute unlocked credit for all of the tokens that the user has deposited into the system.
        _distributeUnlockedCreditDeposited(owner);

        uint256 amountYieldTokens = convertSharesToYieldTokens(yieldToken, shares);

        // Update the owner's account, burn shares from the owner's account.
        _poke(owner);
        _burnShares(owner, yieldToken, shares);
        _sync(yieldToken, amountYieldTokens, _usub);

        // Validate the owner's account to assure that the collateralization invariant is still held.
        _validate(owner);

        emit Withdraw(owner, yieldToken, shares, recipient);

        return amountYieldTokens;
    }

    function _mint(address owner, uint256 amount, address recipient) internal {
        // Check that the system will allow for the specified amount to be minted.
        _checkMintingLimit(amount);

        // Preemptively harvest all tokens that the user has deposited into the system.
        _preemptivelyHarvestDeposited(owner);

        // Distribute unlocked credit.
        _distributeUnlockedCreditDeposited(owner);

        // Update the owner's account, increase their debt.
        _poke(owner);
        _updateDebt(owner, SafeCast.toInt256(amount));
        _validate(owner);

        // Decrease the global amount of mintable debt tokens.
        _mintingLimiter.decrease(amount);

        // Mint the debt tokens to the recipient.
        TokenUtils.safeMint(debtToken, recipient, amount);

        emit Mint(owner, amount, recipient);
    }

    function _sync(
        address yieldToken,
        uint256 amount,
        function(uint256, uint256) internal pure returns (uint256) operation
    ) internal {
        YieldTokenParams memory yieldTokenParams = _yieldTokens[yieldToken];

        uint256 amountUnderlyingTokens = convertYieldTokensToUnderlying(yieldToken, amount);
        uint256 updatedActiveBalance   = operation(yieldTokenParams.activeBalance, amount);
        uint256 updatedExpectedValue   = operation(yieldTokenParams.expectedValue, amountUnderlyingTokens);

        _yieldTokens[yieldToken].activeBalance = updatedActiveBalance;
        _yieldTokens[yieldToken].expectedValue = updatedExpectedValue;
    }

    function _loss(address yieldToken) internal view returns (uint256) {
        YieldTokenParams memory yieldTokenParams = _yieldTokens[yieldToken];

        uint256 amountUnderlyingTokens = convertYieldTokensToUnderlying(yieldToken, yieldTokenParams.activeBalance);
        uint256 expectedUnderlyingValue = yieldTokenParams.expectedValue;

        return expectedUnderlyingValue > amountUnderlyingTokens
            ? ((expectedUnderlyingValue - amountUnderlyingTokens) * BPS) / expectedUnderlyingValue
            : 0;
    }

    // ========================================================================
    // Internal Functions - Credit Distribution
    // ========================================================================

    function _distributeCredit(address yieldToken, uint256 amount) internal {
        YieldTokenParams storage yieldTokenParams = _yieldTokens[yieldToken];

        uint256 pendingCredit     = yieldTokenParams.pendingCredit;
        uint256 distributedCredit = yieldTokenParams.distributedCredit;
        uint256 unlockedCredit    = _calculateUnlockedCredit(yieldToken);
        uint256 lockedCredit      = pendingCredit - (distributedCredit + unlockedCredit);

        // Distribute any unlocked credit before overriding it.
        if (unlockedCredit > 0) {
            yieldTokenParams.accruedWeight += unlockedCredit * FIXED_POINT_SCALAR / yieldTokenParams.totalShares;
        }

        yieldTokenParams.pendingCredit         = amount + lockedCredit;
        yieldTokenParams.distributedCredit     = 0;
        yieldTokenParams.lastDistributionBlock = block.number;
    }

    function _distributeUnlockedCreditDeposited(address owner) internal {
        Sets.AddressSet storage depositedTokens = _accounts[owner].depositedTokens;
        for (uint256 i = 0; i < depositedTokens.values.length; ++i) {
            _distributeUnlockedCredit(depositedTokens.values[i]);
        }
    }

    function _distributeUnlockedCredit(address yieldToken) internal {
        YieldTokenParams storage yieldTokenParams = _yieldTokens[yieldToken];

        uint256 unlockedCredit = _calculateUnlockedCredit(yieldToken);
        if (unlockedCredit == 0) {
            return;
        }

        yieldTokenParams.accruedWeight     += unlockedCredit * FIXED_POINT_SCALAR / yieldTokenParams.totalShares;
        yieldTokenParams.distributedCredit += unlockedCredit;
    }

    // ========================================================================
    // Internal Functions - Wrapping
    // ========================================================================

    function _wrap(
        address yieldToken,
        uint256 amount,
        uint256 minimumAmountOut
    ) internal returns (uint256) {
        YieldTokenParams storage yieldTokenParams = _yieldTokens[yieldToken];

        ITokenAdapter adapter = ITokenAdapter(yieldTokenParams.adapter);
        address underlyingToken = yieldTokenParams.underlyingToken;

        TokenUtils.safeTransferFrom(underlyingToken, msg.sender, address(this), amount);
        uint256 wrappedShares = adapter.wrap(amount, address(this));
        if (wrappedShares < minimumAmountOut) {
            revert SlippageExceeded(wrappedShares, minimumAmountOut);
        }

        return wrappedShares;
    }

    function _unwrap(
        address yieldToken,
        uint256 amount,
        address recipient,
        uint256 minimumAmountOut
    ) internal returns (uint256) {
        ITokenAdapter adapter = ITokenAdapter(_yieldTokens[yieldToken].adapter);
        uint256 amountUnwrapped = adapter.unwrap(amount, recipient);
        if (amountUnwrapped < minimumAmountOut) {
            revert SlippageExceeded(amountUnwrapped, minimumAmountOut);
        }
        return amountUnwrapped;
    }

    // ========================================================================
    // Internal Functions - Account Management
    // ========================================================================

    function _poke(address owner) internal {
        Sets.AddressSet storage depositedTokens = _accounts[owner].depositedTokens;
        for (uint256 i = 0; i < depositedTokens.values.length; ++i) {
            _poke(owner, depositedTokens.values[i]);
        }
    }

    function _poke(address owner, address yieldToken) internal {
        Account storage account = _accounts[owner];

        uint256 currentAccruedWeight = _yieldTokens[yieldToken].accruedWeight;
        uint256 lastAccruedWeight    = account.lastAccruedWeights[yieldToken];

        if (currentAccruedWeight == lastAccruedWeight) {
            return;
        }

        uint256 balance          = account.balances[yieldToken];
        uint256 unrealizedCredit = (currentAccruedWeight - lastAccruedWeight) * balance / FIXED_POINT_SCALAR;

        account.debt                           -= SafeCast.toInt256(unrealizedCredit);
        account.lastAccruedWeights[yieldToken]  = currentAccruedWeight;
    }

    function _updateDebt(address owner, int256 amount) internal {
        Account storage account = _accounts[owner];
        account.debt += amount;
    }

    function _approveMint(address owner, address spender, uint256 amount) internal {
        Account storage account = _accounts[owner];
        account.mintAllowances[spender] = amount;
        emit ApproveMint(owner, spender, amount);
    }

    function _decreaseMintAllowance(address owner, address spender, uint256 amount) internal {
        Account storage account = _accounts[owner];
        account.mintAllowances[spender] -= amount;
    }

    function _approveWithdraw(address owner, address spender, address yieldToken, uint256 shares) internal {
        Account storage account = _accounts[owner];
        account.withdrawAllowances[spender][yieldToken] = shares;
        emit ApproveWithdraw(owner, spender, yieldToken, shares);
    }

    function _decreaseWithdrawAllowance(address owner, address spender, address yieldToken, uint256 amount) internal {
        Account storage account = _accounts[owner];
        account.withdrawAllowances[spender][yieldToken] -= amount;
    }

    // ========================================================================
    // Internal Functions - Validation
    // ========================================================================

    function _validate(address owner) internal view {
        int256 debt = _accounts[owner].debt;
        if (debt <= 0) {
            return;
        }

        uint256 collateralization = totalValue(owner) * FIXED_POINT_SCALAR / uint256(debt);

        if (collateralization < minimumCollateralization) {
            revert Undercollateralized();
        }
    }

    function totalValue(address owner) public view returns (uint256) {
        uint256 total = 0;

        Sets.AddressSet storage depositedTokens = _accounts[owner].depositedTokens;
        for (uint256 i = 0; i < depositedTokens.values.length; ++i) {
            address yieldToken             = depositedTokens.values[i];
            address underlyingToken        = _yieldTokens[yieldToken].underlyingToken;
            uint256 shares                 = _accounts[owner].balances[yieldToken];
            uint256 amountUnderlyingTokens = convertSharesToUnderlyingTokens(yieldToken, shares);

            total += normalizeUnderlyingTokensToDebt(underlyingToken, amountUnderlyingTokens);
        }

        return total;
    }

    // ========================================================================
    // Internal Functions - Share Management
    // ========================================================================

    function _issueSharesForAmount(
        address recipient,
        address yieldToken,
        uint256 amount
    ) internal returns (uint256) {
        uint256 shares = convertYieldTokensToShares(yieldToken, amount);

        if (_accounts[recipient].balances[yieldToken] == 0) {
            _accounts[recipient].depositedTokens.add(yieldToken);
        }

        _accounts[recipient].balances[yieldToken] += shares;
        _yieldTokens[yieldToken].totalShares += shares;

        return shares;
    }

    function _burnShares(address owner, address yieldToken, uint256 shares) internal {
        Account storage account = _accounts[owner];

        account.balances[yieldToken] -= shares;
        _yieldTokens[yieldToken].totalShares -= shares;

        if (account.balances[yieldToken] == 0) {
            account.depositedTokens.remove(yieldToken);
        }
    }

    // ========================================================================
    // Internal Functions - Debt Calculation
    // ========================================================================

    function _calculateUnrealizedDebt(address owner) internal view returns (int256) {
        int256 debt = _accounts[owner].debt;

        Sets.AddressSet storage depositedTokens = _accounts[owner].depositedTokens;
        for (uint256 i = 0; i < depositedTokens.values.length; ++i) {
            address yieldToken = depositedTokens.values[i];

            uint256 currentAccruedWeight = _yieldTokens[yieldToken].accruedWeight;
            uint256 lastAccruedWeight    = _accounts[owner].lastAccruedWeights[yieldToken];
            uint256 unlockedCredit       = _calculateUnlockedCredit(yieldToken);

            currentAccruedWeight += unlockedCredit > 0
                ? unlockedCredit * FIXED_POINT_SCALAR / _yieldTokens[yieldToken].totalShares
                : 0;

            if (currentAccruedWeight == lastAccruedWeight) {
                continue;
            }

            uint256 balance = _accounts[owner].balances[yieldToken];
            uint256 unrealizedCredit = ((currentAccruedWeight - lastAccruedWeight) * balance) / FIXED_POINT_SCALAR;

            debt -= SafeCast.toInt256(unrealizedCredit);
        }

        return debt;
    }

    function _calculateUnrealizedActiveBalance(address yieldToken) internal view returns (uint256) {
        YieldTokenParams storage yieldTokenParams = _yieldTokens[yieldToken];

        uint256 activeBalance = yieldTokenParams.activeBalance;
        if (activeBalance == 0) {
            return activeBalance;
        }

        uint256 currentValue = convertYieldTokensToUnderlying(yieldToken, activeBalance);
        uint256 expectedValue = yieldTokenParams.expectedValue;
        if (currentValue <= expectedValue) {
            return activeBalance;
        }

        uint256 harvestable = convertUnderlyingTokensToYield(yieldToken, currentValue - expectedValue);
        if (harvestable == 0) {
            return activeBalance;
        }

        return activeBalance - harvestable;
    }

    function _calculateUnlockedCredit(address yieldToken) internal view returns (uint256) {
        YieldTokenParams storage yieldTokenParams = _yieldTokens[yieldToken];

        uint256 pendingCredit = yieldTokenParams.pendingCredit;
        if (pendingCredit == 0) {
            return 0;
        }

        uint256 creditUnlockRate      = yieldTokenParams.creditUnlockRate;
        uint256 distributedCredit     = yieldTokenParams.distributedCredit;
        uint256 lastDistributionBlock = yieldTokenParams.lastDistributionBlock;

        uint256 percentUnlocked = (block.number - lastDistributionBlock) * creditUnlockRate;

        return percentUnlocked < FIXED_POINT_SCALAR
            ? (pendingCredit * percentUnlocked / FIXED_POINT_SCALAR) - distributedCredit
            : pendingCredit - distributedCredit;
    }

    // ========================================================================
    // Public View Functions - Conversion
    // ========================================================================

    function convertYieldTokensToShares(address yieldToken, uint256 amount) public view returns (uint256) {
        if (_yieldTokens[yieldToken].totalShares == 0) {
            return amount;
        }
        return amount * _yieldTokens[yieldToken].totalShares / _calculateUnrealizedActiveBalance(yieldToken);
    }

    function convertSharesToYieldTokens(address yieldToken, uint256 shares) public view returns (uint256) {
        uint256 totalShares = _yieldTokens[yieldToken].totalShares;
        if (totalShares == 0) {
            return shares;
        }
        return (shares * _calculateUnrealizedActiveBalance(yieldToken)) / totalShares;
    }

    function convertSharesToUnderlyingTokens(address yieldToken, uint256 shares) public view returns (uint256) {
        uint256 amountYieldTokens = convertSharesToYieldTokens(yieldToken, shares);
        return convertYieldTokensToUnderlying(yieldToken, amountYieldTokens);
    }

    function convertYieldTokensToUnderlying(address yieldToken, uint256 amount) public view returns (uint256) {
        YieldTokenParams storage yieldTokenParams = _yieldTokens[yieldToken];
        ITokenAdapter adapter = ITokenAdapter(yieldTokenParams.adapter);
        return amount * adapter.price() / 10**yieldTokenParams.decimals;
    }

    function convertUnderlyingTokensToYield(address yieldToken, uint256 amount) public view returns (uint256) {
        YieldTokenParams storage yieldTokenParams = _yieldTokens[yieldToken];
        ITokenAdapter adapter = ITokenAdapter(yieldTokenParams.adapter);
        return amount * 10**yieldTokenParams.decimals / adapter.price();
    }

    function convertUnderlyingTokensToShares(address yieldToken, uint256 amount) public view returns (uint256) {
        uint256 amountYieldTokens = convertUnderlyingTokensToYield(yieldToken, amount);
        return convertYieldTokensToShares(yieldToken, amountYieldTokens);
    }

    function normalizeUnderlyingTokensToDebt(address underlyingToken, uint256 amount) public view returns (uint256) {
        return amount * _underlyingTokens[underlyingToken].conversionFactor;
    }

    function normalizeDebtTokensToUnderlying(address underlyingToken, uint256 amount) public view returns (uint256) {
        return amount / _underlyingTokens[underlyingToken].conversionFactor;
    }

    // ========================================================================
    // Internal Functions - Whitelist
    // ========================================================================

    function _onlyWhitelisted() internal view {
        // Check if the message sender is an EOA.
        if (tx.origin == msg.sender) {
            return;
        }
        // Only check the whitelist for calls from contracts.
        if (!IWhitelist(whitelist).isWhitelisted(msg.sender)) {
            revert Unauthorized();
        }
    }

    // ========================================================================
    // Internal Functions - Utility
    // ========================================================================

    function _checkArgument(bool expression) internal pure {
        if (!expression) {
            revert IllegalArgument();
        }
    }

    function _checkState(bool expression) internal pure {
        if (!expression) {
            revert IllegalState();
        }
    }

    function _uadd(uint256 x, uint256 y) internal pure returns (uint256 z) { z = x + y; }

    function _usub(uint256 x, uint256 y) internal pure returns (uint256 z) { z = x - y; }
}
