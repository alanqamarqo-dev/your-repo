// SPDX-License-Identifier: BUSL-1.1
pragma solidity 0.8.15;

/**
 * @title Compound V3 Comet — Real DeFi Lending Protocol
 * @notice Simplified but realistic version from Compound's bug bounty (Immunefi $150K)
 * @dev Contains real vulnerability patterns found in production DeFi
 * 
 * Based on: https://github.com/compound-finance/comet
 * Bug Bounty: https://immunefi.com/bounty/compound/
 */

// ============ Interfaces ============

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function decimals() external view returns (uint8);
}

interface IPriceFeed {
    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    );
    function decimals() external view returns (uint8);
}

// ============ Libraries ============

library SafeCast {
    function toInt104(int256 value) internal pure returns (int104) {
        require(value >= type(int104).min && value <= type(int104).max, "SafeCast: int104 overflow");
        return int104(value);
    }
    
    function toUint104(uint256 value) internal pure returns (uint104) {
        require(value <= type(uint104).max, "SafeCast: uint104 overflow");
        return uint104(value);
    }
    
    function toUint128(uint256 value) internal pure returns (uint128) {
        require(value <= type(uint128).max, "SafeCast: uint128 overflow");
        return uint128(value);
    }
    
    function toUint64(uint256 value) internal pure returns (uint64) {
        require(value <= type(uint64).max, "SafeCast: uint64 overflow");
        return uint64(value);
    }
}

// ============ Core Storage ============

contract CometStorage {
    struct UserBasic {
        int104 principal;
        uint64 baseTrackingIndex;
        uint64 baseTrackingAccrued;
        uint16 assetsIn;
    }
    
    struct UserCollateral {
        uint128 balance;
    }
    
    struct TotalsCollateral {
        uint128 totalSupplyAsset;
    }
    
    struct AssetInfo {
        uint8 offset;
        address asset;
        address priceFeed;
        uint64 scale;
        uint64 borrowCollateralFactor;
        uint64 liquidateCollateralFactor;
        uint64 liquidationFactor;
        uint128 supplyCap;
    }
    
    struct AssetConfig {
        address asset;
        address priceFeed;
        uint8 decimals;
        uint64 borrowCollateralFactor;
        uint64 liquidateCollateralFactor;
        uint64 liquidationFactor;
        uint128 supplyCap;
    }
    
    struct LiquidatorPoints {
        uint32 numAbsorbs;
        uint64 numAbsorbed;
        uint128 approxSpend;
    }

    // State variables
    mapping(address => UserBasic) public userBasic;
    mapping(address => mapping(address => UserCollateral)) public userCollateral;
    mapping(address => TotalsCollateral) public totalsCollateral;
    mapping(address => mapping(address => bool)) public isAllowed;
    mapping(address => LiquidatorPoints) public liquidatorPoints;
    
    uint64 public baseSupplyIndex;
    uint64 public baseBorrowIndex;
    uint64 public trackingSupplyIndex;
    uint64 public trackingBorrowIndex;
    uint104 public totalSupplyBase;
    uint104 public totalBorrowBase;
    uint40 public lastAccrualTime;
    uint8 public pauseFlags;
}

// ============ Main Comet Contract ============

contract Comet is CometStorage {
    using SafeCast for uint256;
    using SafeCast for int256;

    // ============ Constants ============
    
    uint64 constant FACTOR_SCALE = 1e18;
    uint64 constant BASE_INDEX_SCALE = 1e15;
    uint64 constant BASE_ACCRUAL_SCALE = 1e6;
    uint8 constant PRICE_FEED_DECIMALS = 8;
    uint256 constant SECONDS_PER_YEAR = 365 days;
    uint8 constant MAX_ASSETS = 15;
    
    uint8 constant PAUSE_SUPPLY_OFFSET = 0;
    uint8 constant PAUSE_TRANSFER_OFFSET = 1;
    uint8 constant PAUSE_WITHDRAW_OFFSET = 2;
    uint8 constant PAUSE_ABSORB_OFFSET = 3;
    uint8 constant PAUSE_BUY_OFFSET = 4;

    // ============ Immutables ============
    
    address public immutable governor;
    address public immutable pauseGuardian;
    address public immutable baseToken;
    address public immutable baseTokenPriceFeed;
    address public immutable extensionDelegate;
    
    uint64 public immutable supplyKink;
    uint64 public immutable supplyPerSecondInterestRateSlopeLow;
    uint64 public immutable supplyPerSecondInterestRateSlopeHigh;
    uint64 public immutable supplyPerSecondInterestRateBase;
    uint64 public immutable borrowKink;
    uint64 public immutable borrowPerSecondInterestRateSlopeLow;
    uint64 public immutable borrowPerSecondInterestRateSlopeHigh;
    uint64 public immutable borrowPerSecondInterestRateBase;
    uint64 public immutable storeFrontPriceFactor;
    uint64 public immutable baseScale;
    uint64 public immutable trackingIndexScale;
    uint64 public immutable baseTrackingSupplySpeed;
    uint64 public immutable baseTrackingBorrowSpeed;
    uint104 public immutable baseMinForRewards;
    uint104 public immutable baseBorrowMin;
    uint256 public immutable targetReserves;
    uint8 public immutable override_decimals;
    uint8 public immutable numAssets;
    
    AssetConfig[] internal _assetConfigs;
    
    // ============ Reentrancy Guard ============
    
    uint256 private _reentrancyStatus;
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;

    // ============ Events ============
    
    event Supply(address indexed from, address indexed dst, uint256 amount);
    event Withdraw(address indexed src, address indexed to, uint256 amount);
    event Transfer(address indexed from, address indexed to, uint256 amount);
    event SupplyCollateral(address indexed from, address indexed dst, address indexed asset, uint128 amount);
    event WithdrawCollateral(address indexed src, address indexed to, address indexed asset, uint128 amount);
    event TransferCollateral(address indexed from, address indexed to, address indexed asset, uint128 amount);
    event AbsorbCollateral(address indexed absorber, address indexed account, address indexed asset, uint128 amount, uint256 value);
    event AbsorbDebt(address indexed absorber, address indexed account, uint256 basePaidOut, uint256 valueOfBasePaidOut);
    event BuyCollateral(address indexed buyer, address indexed asset, uint256 baseAmount, uint256 collateralAmount);
    event WithdrawReserves(address indexed to, uint256 amount);
    event PauseAction(bool supplyPaused, bool transferPaused, bool withdrawPaused, bool absorbPaused, bool buyPaused);
    
    // ============ Errors ============
    
    error Unauthorized();
    error Paused();
    error BadPrice();
    error BadDecimals();
    error BadDiscount();
    error TooManyAssets();
    error BadMinimum();
    error BadAsset();
    error NotLiquidatable();
    error NotCollateralized();
    error BorrowTooSmall();
    error InsufficientReserves();
    error SupplyCapExceeded();
    error TooMuchSlippage();
    error NoSelfTransfer();
    error NotForSale();
    error AlreadyInitialized();
    error ReentrantCallBlocked();

    // ============ Constructor ============
    
    constructor(
        address _governor,
        address _pauseGuardian,
        address _baseToken,
        address _baseTokenPriceFeed,
        address _extensionDelegate,
        AssetConfig[] memory assetConfigs,
        uint64 _supplyKink,
        uint64 _borrowKink,
        uint64 _supplyPerYearInterestRateSlopeLow,
        uint64 _supplyPerYearInterestRateSlopeHigh,
        uint64 _supplyPerYearInterestRateBase,
        uint64 _borrowPerYearInterestRateSlopeLow,
        uint64 _borrowPerYearInterestRateSlopeHigh,
        uint64 _borrowPerYearInterestRateBase,
        uint64 _storeFrontPriceFactor,
        uint64 _trackingIndexScale,
        uint64 _baseTrackingSupplySpeed,
        uint64 _baseTrackingBorrowSpeed,
        uint104 _baseMinForRewards,
        uint104 _baseBorrowMin,
        uint256 _targetReserves
    ) {
        governor = _governor;
        pauseGuardian = _pauseGuardian;
        baseToken = _baseToken;
        baseTokenPriceFeed = _baseTokenPriceFeed;
        extensionDelegate = _extensionDelegate;
        
        uint8 decimals_ = IERC20(_baseToken).decimals();
        override_decimals = decimals_;
        baseScale = uint64(10 ** decimals_);
        
        storeFrontPriceFactor = _storeFrontPriceFactor;
        trackingIndexScale = _trackingIndexScale;
        baseTrackingSupplySpeed = _baseTrackingSupplySpeed;
        baseTrackingBorrowSpeed = _baseTrackingBorrowSpeed;
        baseMinForRewards = _baseMinForRewards;
        baseBorrowMin = _baseBorrowMin;
        targetReserves = _targetReserves;
        
        supplyKink = _supplyKink;
        supplyPerSecondInterestRateSlopeLow = _supplyPerYearInterestRateSlopeLow / uint64(SECONDS_PER_YEAR);
        supplyPerSecondInterestRateSlopeHigh = _supplyPerYearInterestRateSlopeHigh / uint64(SECONDS_PER_YEAR);
        supplyPerSecondInterestRateBase = _supplyPerYearInterestRateBase / uint64(SECONDS_PER_YEAR);
        borrowKink = _borrowKink;
        borrowPerSecondInterestRateSlopeLow = _borrowPerYearInterestRateSlopeLow / uint64(SECONDS_PER_YEAR);
        borrowPerSecondInterestRateSlopeHigh = _borrowPerYearInterestRateSlopeHigh / uint64(SECONDS_PER_YEAR);
        borrowPerSecondInterestRateBase = _borrowPerYearInterestRateBase / uint64(SECONDS_PER_YEAR);
        
        require(assetConfigs.length <= MAX_ASSETS, "Too many assets");
        numAssets = uint8(assetConfigs.length);
        
        for (uint i = 0; i < assetConfigs.length; i++) {
            _assetConfigs.push(assetConfigs[i]);
        }
        
        _reentrancyStatus = _NOT_ENTERED;
    }
    
    // ============ Modifiers ============
    
    modifier nonReentrant() {
        if (_reentrancyStatus == _ENTERED) revert ReentrantCallBlocked();
        _reentrancyStatus = _ENTERED;
        _;
        _reentrancyStatus = _NOT_ENTERED;
    }

    // ============ Initialization ============
    
    function initializeStorage() external {
        if (lastAccrualTime != 0) revert AlreadyInitialized();
        lastAccrualTime = getNowInternal();
        baseSupplyIndex = BASE_INDEX_SCALE;
        baseBorrowIndex = BASE_INDEX_SCALE;
    }

    // ============ Asset Info ============
    
    function getAssetInfo(uint8 i) public view returns (AssetInfo memory) {
        if (i >= numAssets) revert BadAsset();
        AssetConfig memory config = _assetConfigs[i];
        return AssetInfo({
            offset: i,
            asset: config.asset,
            priceFeed: config.priceFeed,
            scale: uint64(10 ** config.decimals),
            borrowCollateralFactor: config.borrowCollateralFactor,
            liquidateCollateralFactor: config.liquidateCollateralFactor,
            liquidationFactor: config.liquidationFactor,
            supplyCap: config.supplyCap
        });
    }
    
    function getAssetInfoByAddress(address asset) public view returns (AssetInfo memory) {
        for (uint8 i = 0; i < numAssets; ) {
            AssetInfo memory assetInfo = getAssetInfo(i);
            if (assetInfo.asset == asset) {
                return assetInfo;
            }
            unchecked { i++; }
        }
        revert BadAsset();
    }

    // ============ Interest / Accrual ============
    
    function getNowInternal() internal view returns (uint40) {
        return uint40(block.timestamp);
    }

    function getUtilization() public view returns (uint) {
        uint totalSupply_ = presentValueSupply(baseSupplyIndex, totalSupplyBase);
        uint totalBorrow_ = presentValueBorrow(baseBorrowIndex, totalBorrowBase);
        if (totalSupply_ == 0) {
            return 0;
        } else {
            return totalBorrow_ * FACTOR_SCALE / totalSupply_;
        }
    }

    function getSupplyRate(uint utilization) public view returns (uint64) {
        if (utilization <= supplyKink) {
            return uint64(supplyPerSecondInterestRateBase + mulFactor(supplyPerSecondInterestRateSlopeLow, utilization));
        } else {
            return uint64(supplyPerSecondInterestRateBase + mulFactor(supplyPerSecondInterestRateSlopeLow, supplyKink) + mulFactor(supplyPerSecondInterestRateSlopeHigh, (utilization - supplyKink)));
        }
    }

    function getBorrowRate(uint utilization) public view returns (uint64) {
        if (utilization <= borrowKink) {
            return uint64(borrowPerSecondInterestRateBase + mulFactor(borrowPerSecondInterestRateSlopeLow, utilization));
        } else {
            return uint64(borrowPerSecondInterestRateBase + mulFactor(borrowPerSecondInterestRateSlopeLow, borrowKink) + mulFactor(borrowPerSecondInterestRateSlopeHigh, (utilization - borrowKink)));
        }
    }

    function accruedInterestIndices(uint timeElapsed) internal view returns (uint64, uint64) {
        uint64 baseSupplyIndex_ = baseSupplyIndex;
        uint64 baseBorrowIndex_ = baseBorrowIndex;
        if (timeElapsed > 0) {
            uint utilization = getUtilization();
            uint supplyRate = getSupplyRate(utilization);
            uint borrowRate = getBorrowRate(utilization);
            baseSupplyIndex_ += uint64(mulFactor(baseSupplyIndex_, supplyRate * timeElapsed));
            baseBorrowIndex_ += uint64(mulFactor(baseBorrowIndex_, borrowRate * timeElapsed));
        }
        return (baseSupplyIndex_, baseBorrowIndex_);
    }

    function accrueInternal() internal {
        uint40 now_ = getNowInternal();
        uint timeElapsed = uint256(now_ - lastAccrualTime);
        if (timeElapsed > 0) {
            (baseSupplyIndex, baseBorrowIndex) = accruedInterestIndices(timeElapsed);
            if (totalSupplyBase >= baseMinForRewards) {
                trackingSupplyIndex += uint64(divBaseWei(baseTrackingSupplySpeed * timeElapsed, totalSupplyBase));
            }
            if (totalBorrowBase >= baseMinForRewards) {
                trackingBorrowIndex += uint64(divBaseWei(baseTrackingBorrowSpeed * timeElapsed, totalBorrowBase));
            }
            lastAccrualTime = now_;
        }
    }

    // ============ Price Feed ============
    
    /**
     * @notice Get the current price from a feed
     * @dev VULNERABILITY: No staleness check on oracle data
     * @dev VULNERABILITY: No check on roundId vs answeredInRound
     */
    function getPrice(address priceFeed) public view returns (uint256) {
        (, int price, , , ) = IPriceFeed(priceFeed).latestRoundData();
        if (price <= 0) revert BadPrice();
        return uint256(price);
    }

    // ============ Collateral & Reserves ============
    
    function getCollateralReserves(address asset) public view returns (uint) {
        return IERC20(asset).balanceOf(address(this)) - totalsCollateral[asset].totalSupplyAsset;
    }

    function getReserves() public view returns (int) {
        (uint64 baseSupplyIndex_, uint64 baseBorrowIndex_) = accruedInterestIndices(getNowInternal() - lastAccrualTime);
        uint balance = IERC20(baseToken).balanceOf(address(this));
        uint totalSupply_ = presentValueSupply(baseSupplyIndex_, totalSupplyBase);
        uint totalBorrow_ = presentValueBorrow(baseBorrowIndex_, totalBorrowBase);
        return signed256(balance) - signed256(totalSupply_) + signed256(totalBorrow_);
    }

    // ============ Collateralization Checks ============
    
    function isBorrowCollateralized(address account) public view returns (bool) {
        int104 principal = userBasic[account].principal;
        if (principal >= 0) {
            return true;
        }

        uint16 assetsIn = userBasic[account].assetsIn;
        int liquidity = signedMulPrice(
            presentValue(principal),
            getPrice(baseTokenPriceFeed),
            uint64(baseScale)
        );

        for (uint8 i = 0; i < numAssets; ) {
            if (isInAsset(assetsIn, i)) {
                if (liquidity >= 0) {
                    return true;
                }
                AssetInfo memory asset = getAssetInfo(i);
                uint newAmount = mulPrice(
                    userCollateral[account][asset.asset].balance,
                    getPrice(asset.priceFeed),
                    asset.scale
                );
                liquidity += signed256(mulFactor(newAmount, asset.borrowCollateralFactor));
            }
            unchecked { i++; }
        }

        return liquidity >= 0;
    }

    function isLiquidatable(address account) public view returns (bool) {
        int104 principal = userBasic[account].principal;
        if (principal >= 0) {
            return false;
        }

        uint16 assetsIn = userBasic[account].assetsIn;
        int liquidity = signedMulPrice(
            presentValue(principal),
            getPrice(baseTokenPriceFeed),
            uint64(baseScale)
        );

        for (uint8 i = 0; i < numAssets; ) {
            if (isInAsset(assetsIn, i)) {
                if (liquidity >= 0) {
                    return false;
                }
                AssetInfo memory asset = getAssetInfo(i);
                uint newAmount = mulPrice(
                    userCollateral[account][asset.asset].balance,
                    getPrice(asset.priceFeed),
                    asset.scale
                );
                liquidity += signed256(mulFactor(newAmount, asset.liquidateCollateralFactor));
            }
            unchecked { i++; }
        }

        return liquidity < 0;
    }

    // ============ Supply ============
    
    function supply(address asset, uint amount) external {
        supplyInternal(msg.sender, msg.sender, msg.sender, asset, amount);
    }

    function supplyTo(address dst, address asset, uint amount) external {
        supplyInternal(msg.sender, msg.sender, dst, asset, amount);
    }

    function supplyFrom(address from, address dst, address asset, uint amount) external {
        supplyInternal(msg.sender, from, dst, asset, amount);
    }

    function supplyInternal(address operator, address from, address dst, address asset, uint amount) internal nonReentrant {
        if (isSupplyPaused()) revert Paused();
        if (!hasPermission(from, operator)) revert Unauthorized();

        if (asset == baseToken) {
            if (amount == type(uint256).max) {
                amount = borrowBalanceOf(dst);
            }
            supplyBase(from, dst, amount);
        } else {
            supplyCollateral(from, dst, asset, uint128(amount));
        }
    }

    function supplyBase(address from, address dst, uint256 amount) internal {
        doTransferIn(baseToken, from, amount);
        accrueInternal();

        UserBasic memory dstUser = userBasic[dst];
        int104 dstPrincipal = dstUser.principal;
        int256 dstBalance = presentValue(dstPrincipal) + signed256(amount);
        int104 dstPrincipalNew = principalValue(dstBalance);

        (uint104 repayAmount, uint104 supplyAmount) = repayAndSupplyAmount(dstPrincipal, dstPrincipalNew);

        totalSupplyBase += supplyAmount;
        totalBorrowBase -= repayAmount;

        updateBasePrincipal(dst, dstUser, dstPrincipalNew);

        emit Supply(from, dst, amount);
    }

    function supplyCollateral(address from, address dst, address asset, uint128 amount) internal {
        doTransferIn(asset, from, amount);

        AssetInfo memory assetInfo = getAssetInfoByAddress(asset);
        TotalsCollateral memory totals = totalsCollateral[asset];
        totals.totalSupplyAsset += amount;
        if (totals.totalSupplyAsset > assetInfo.supplyCap) revert SupplyCapExceeded();

        uint128 dstCollateral = userCollateral[dst][asset].balance;
        uint128 dstCollateralNew = dstCollateral + amount;

        totalsCollateral[asset] = totals;
        userCollateral[dst][asset].balance = dstCollateralNew;

        updateAssetsIn(dst, assetInfo, dstCollateral, dstCollateralNew);

        emit SupplyCollateral(from, dst, asset, amount);
    }

    // ============ Withdraw ============
    
    function withdraw(address asset, uint amount) external {
        withdrawInternal(msg.sender, msg.sender, msg.sender, asset, amount);
    }

    function withdrawTo(address to, address asset, uint amount) external {
        withdrawInternal(msg.sender, msg.sender, to, asset, amount);
    }

    function withdrawFrom(address src, address to, address asset, uint amount) external {
        withdrawInternal(msg.sender, src, to, asset, amount);
    }

    function withdrawInternal(address operator, address src, address to, address asset, uint amount) internal nonReentrant {
        if (isWithdrawPaused()) revert Paused();
        if (!hasPermission(src, operator)) revert Unauthorized();

        if (asset == baseToken) {
            if (amount == type(uint256).max) {
                amount = balanceOf(src);
            }
            withdrawBase(src, to, amount);
        } else {
            withdrawCollateral(src, to, asset, uint128(amount));
        }
    }

    function withdrawBase(address src, address to, uint256 amount) internal {
        accrueInternal();

        UserBasic memory srcUser = userBasic[src];
        int104 srcPrincipal = srcUser.principal;
        int256 srcBalance = presentValue(srcPrincipal) - signed256(amount);
        int104 srcPrincipalNew = principalValue(srcBalance);

        (uint104 withdrawAmount, uint104 borrowAmount) = withdrawAndBorrowAmount(srcPrincipal, srcPrincipalNew);

        totalSupplyBase -= withdrawAmount;
        totalBorrowBase += borrowAmount;

        updateBasePrincipal(src, srcUser, srcPrincipalNew);

        if (srcBalance < 0) {
            if (uint256(-srcBalance) < baseBorrowMin) revert BorrowTooSmall();
            if (!isBorrowCollateralized(src)) revert NotCollateralized();
        }

        doTransferOut(baseToken, to, amount);

        emit Withdraw(src, to, amount);
    }

    function withdrawCollateral(address src, address to, address asset, uint128 amount) internal {
        uint128 srcCollateral = userCollateral[src][asset].balance;
        uint128 srcCollateralNew = srcCollateral - amount;

        totalsCollateral[asset].totalSupplyAsset -= amount;
        userCollateral[src][asset].balance = srcCollateralNew;

        AssetInfo memory assetInfo = getAssetInfoByAddress(asset);
        updateAssetsIn(src, assetInfo, srcCollateral, srcCollateralNew);

        // Note: no accrue interest, BorrowCF < LiquidationCF covers small changes
        if (!isBorrowCollateralized(src)) revert NotCollateralized();

        doTransferOut(asset, to, amount);

        emit WithdrawCollateral(src, to, asset, amount);
    }

    // ============ Transfer ============
    
    function transfer(address dst, uint amount) external returns (bool) {
        transferInternal(msg.sender, msg.sender, dst, baseToken, amount);
        return true;
    }

    function transferFrom(address src, address dst, uint amount) external returns (bool) {
        transferInternal(msg.sender, src, dst, baseToken, amount);
        return true;
    }

    function transferAsset(address dst, address asset, uint amount) external {
        transferInternal(msg.sender, msg.sender, dst, asset, amount);
    }

    function transferAssetFrom(address src, address dst, address asset, uint amount) external {
        transferInternal(msg.sender, src, dst, asset, amount);
    }

    function transferInternal(address operator, address src, address dst, address asset, uint amount) internal nonReentrant {
        if (isTransferPaused()) revert Paused();
        if (!hasPermission(src, operator)) revert Unauthorized();
        if (src == dst) revert NoSelfTransfer();

        if (asset == baseToken) {
            if (amount == type(uint256).max) {
                amount = balanceOf(src);
            }
            transferBase(src, dst, amount);
        } else {
            transferCollateral(src, dst, asset, uint128(amount));
        }
    }

    function transferBase(address src, address dst, uint256 amount) internal {
        accrueInternal();

        UserBasic memory srcUser = userBasic[src];
        UserBasic memory dstUser = userBasic[dst];

        int104 srcPrincipal = srcUser.principal;
        int104 dstPrincipal = dstUser.principal;
        int256 srcBalance = presentValue(srcPrincipal) - signed256(amount);
        int256 dstBalance = presentValue(dstPrincipal) + signed256(amount);
        int104 srcPrincipalNew = principalValue(srcBalance);
        int104 dstPrincipalNew = principalValue(dstBalance);

        (uint104 withdrawAmount, uint104 borrowAmount) = withdrawAndBorrowAmount(srcPrincipal, srcPrincipalNew);
        (uint104 repayAmount, uint104 supplyAmount) = repayAndSupplyAmount(dstPrincipal, dstPrincipalNew);

        totalSupplyBase = totalSupplyBase + supplyAmount - withdrawAmount;
        totalBorrowBase = totalBorrowBase + borrowAmount - repayAmount;

        updateBasePrincipal(src, srcUser, srcPrincipalNew);
        updateBasePrincipal(dst, dstUser, dstPrincipalNew);

        if (srcBalance < 0) {
            if (uint256(-srcBalance) < baseBorrowMin) revert BorrowTooSmall();
            if (!isBorrowCollateralized(src)) revert NotCollateralized();
        }
    }

    function transferCollateral(address src, address dst, address asset, uint128 amount) internal {
        uint128 srcCollateral = userCollateral[src][asset].balance;
        uint128 dstCollateral = userCollateral[dst][asset].balance;
        uint128 srcCollateralNew = srcCollateral - amount;
        uint128 dstCollateralNew = dstCollateral + amount;

        userCollateral[src][asset].balance = srcCollateralNew;
        userCollateral[dst][asset].balance = dstCollateralNew;

        AssetInfo memory assetInfo = getAssetInfoByAddress(asset);
        updateAssetsIn(src, assetInfo, srcCollateral, srcCollateralNew);
        updateAssetsIn(dst, assetInfo, dstCollateral, dstCollateralNew);

        if (!isBorrowCollateralized(src)) revert NotCollateralized();

        emit TransferCollateral(src, dst, asset, amount);
    }

    // ============ Liquidation (Absorb) ============
    
    /**
     * @notice Absorb underwater accounts
     * @dev VULNERABILITY AREA: Complex liquidation logic with multiple price lookups
     */
    function absorb(address absorber, address[] calldata accounts) external {
        if (isAbsorbPaused()) revert Paused();

        uint startGas = gasleft();
        accrueInternal();
        for (uint i = 0; i < accounts.length; ) {
            absorbInternal(absorber, accounts[i]);
            unchecked { i++; }
        }
        uint gasUsed = startGas - gasleft();

        LiquidatorPoints memory points = liquidatorPoints[absorber];
        points.numAbsorbs++;
        points.numAbsorbed += uint64(accounts.length);
        points.approxSpend += uint128(gasUsed * block.basefee);
        liquidatorPoints[absorber] = points;
    }

    function absorbInternal(address absorber, address account) internal {
        if (!isLiquidatable(account)) revert NotLiquidatable();

        UserBasic memory accountUser = userBasic[account];
        int104 oldPrincipal = accountUser.principal;
        int256 oldBalance = presentValue(oldPrincipal);
        uint16 assetsIn = accountUser.assetsIn;

        uint256 basePrice = getPrice(baseTokenPriceFeed);
        uint256 deltaValue = 0;

        for (uint8 i = 0; i < numAssets; ) {
            if (isInAsset(assetsIn, i)) {
                AssetInfo memory assetInfo = getAssetInfo(i);
                address asset = assetInfo.asset;
                uint128 seizeAmount = userCollateral[account][asset].balance;
                userCollateral[account][asset].balance = 0;
                totalsCollateral[asset].totalSupplyAsset -= seizeAmount;

                uint256 value = mulPrice(seizeAmount, getPrice(assetInfo.priceFeed), assetInfo.scale);
                deltaValue += mulFactor(value, assetInfo.liquidationFactor);

                emit AbsorbCollateral(absorber, account, asset, seizeAmount, value);
            }
            unchecked { i++; }
        }

        uint256 deltaBalance = divPrice(deltaValue, basePrice, uint64(baseScale));
        int256 newBalance = oldBalance + signed256(deltaBalance);
        if (newBalance < 0) {
            newBalance = 0;
        }

        int104 newPrincipal = principalValue(newBalance);
        updateBasePrincipal(account, accountUser, newPrincipal);

        userBasic[account].assetsIn = 0;

        (uint104 repayAmount, uint104 supplyAmount) = repayAndSupplyAmount(oldPrincipal, newPrincipal);

        totalSupplyBase += supplyAmount;
        totalBorrowBase -= repayAmount;

        uint256 basePaidOut = unsigned256(newBalance - oldBalance);
        uint256 valueOfBasePaidOut = mulPrice(basePaidOut, basePrice, uint64(baseScale));
        emit AbsorbDebt(absorber, account, basePaidOut, valueOfBasePaidOut);
    }

    // ============ Buy Collateral ============
    
    /**
     * @notice Buy collateral from the protocol 
     * @dev KNOWN ISSUE: Re-entrancy comment from Compound team:
     *      "Note: Re-entrancy can skip the reserves check above on a second buyCollateral call."
     *      "Note: Pre-transfer hook can re-enter buyCollateral with stale collateral ERC20 balance."
     */
    function buyCollateral(address asset, uint minAmount, uint baseAmount, address recipient) external nonReentrant {
        if (isBuyPaused()) revert Paused();

        int reserves = getReserves();
        if (reserves >= 0 && uint(reserves) >= targetReserves) revert NotForSale();

        // VULNERABILITY: doTransferIn before state update — potential for reentrancy via token hooks
        baseAmount = doTransferIn(baseToken, msg.sender, baseAmount);

        uint collateralAmount = quoteCollateral(asset, baseAmount);
        if (collateralAmount < minAmount) revert TooMuchSlippage();
        if (collateralAmount > getCollateralReserves(asset)) revert InsufficientReserves();

        // Transfer out — state not fully updated before external call
        doTransferOut(asset, recipient, uint128(collateralAmount));

        emit BuyCollateral(msg.sender, asset, baseAmount, collateralAmount);
    }

    function quoteCollateral(address asset, uint baseAmount) public view returns (uint) {
        AssetInfo memory assetInfo = getAssetInfoByAddress(asset);
        uint256 assetPrice = getPrice(assetInfo.priceFeed);
        uint256 discountFactor = mulFactor(storeFrontPriceFactor, FACTOR_SCALE - assetInfo.liquidationFactor);
        uint256 assetPriceDiscounted = mulFactor(assetPrice, FACTOR_SCALE - discountFactor);
        uint256 basePrice = getPrice(baseTokenPriceFeed);
        return basePrice * baseAmount * assetInfo.scale / assetPriceDiscounted / baseScale;
    }

    // ============ Governance ============
    
    function pause(
        bool supplyPaused,
        bool transferPaused,
        bool withdrawPaused,
        bool absorbPaused,
        bool buyPaused
    ) external {
        if (msg.sender != governor && msg.sender != pauseGuardian) revert Unauthorized();

        pauseFlags =
            uint8(0) |
            (toUInt8(supplyPaused) << PAUSE_SUPPLY_OFFSET) |
            (toUInt8(transferPaused) << PAUSE_TRANSFER_OFFSET) |
            (toUInt8(withdrawPaused) << PAUSE_WITHDRAW_OFFSET) |
            (toUInt8(absorbPaused) << PAUSE_ABSORB_OFFSET) |
            (toUInt8(buyPaused) << PAUSE_BUY_OFFSET);

        emit PauseAction(supplyPaused, transferPaused, withdrawPaused, absorbPaused, buyPaused);
    }

    function withdrawReserves(address to, uint amount) external {
        if (msg.sender != governor) revert Unauthorized();

        int reserves = getReserves();
        if (reserves < 0 || amount > unsigned256(reserves)) revert InsufficientReserves();

        doTransferOut(baseToken, to, amount);

        emit WithdrawReserves(to, amount);
    }

    /**
     * @notice Approve a manager to manage assets
     * @dev VULNERABILITY: No check for existing non-zero allowance (USDT approval race)
     */
    function approveThis(address manager, address asset, uint amount) external {
        if (msg.sender != governor) revert Unauthorized();
        IERC20(asset).approve(manager, amount);
    }

    // ============ Permission ============
    
    function allow(address manager, bool isAllowed_) external {
        isAllowed[msg.sender][manager] = isAllowed_;
    }

    function hasPermission(address owner, address manager) internal view returns (bool) {
        return owner == manager || isAllowed[owner][manager];
    }

    // ============ Pause Checks ============
    
    function isSupplyPaused() public view returns (bool) {
        return toBool(pauseFlags & (uint8(1) << PAUSE_SUPPLY_OFFSET));
    }

    function isTransferPaused() public view returns (bool) {
        return toBool(pauseFlags & (uint8(1) << PAUSE_TRANSFER_OFFSET));
    }

    function isWithdrawPaused() public view returns (bool) {
        return toBool(pauseFlags & (uint8(1) << PAUSE_WITHDRAW_OFFSET));
    }

    function isAbsorbPaused() public view returns (bool) {
        return toBool(pauseFlags & (uint8(1) << PAUSE_ABSORB_OFFSET));
    }

    function isBuyPaused() public view returns (bool) {
        return toBool(pauseFlags & (uint8(1) << PAUSE_BUY_OFFSET));
    }

    // ============ Balance Views ============
    
    function totalSupply() external view returns (uint256) {
        (uint64 baseSupplyIndex_, ) = accruedInterestIndices(getNowInternal() - lastAccrualTime);
        return presentValueSupply(baseSupplyIndex_, totalSupplyBase);
    }

    function totalBorrow() external view returns (uint256) {
        (, uint64 baseBorrowIndex_) = accruedInterestIndices(getNowInternal() - lastAccrualTime);
        return presentValueBorrow(baseBorrowIndex_, totalBorrowBase);
    }

    function balanceOf(address account) public view returns (uint256) {
        (uint64 baseSupplyIndex_, ) = accruedInterestIndices(getNowInternal() - lastAccrualTime);
        int104 principal = userBasic[account].principal;
        return principal > 0 ? presentValueSupply(baseSupplyIndex_, uint104(principal)) : 0;
    }

    function borrowBalanceOf(address account) public view returns (uint256) {
        (, uint64 baseBorrowIndex_) = accruedInterestIndices(getNowInternal() - lastAccrualTime);
        int104 principal = userBasic[account].principal;
        return principal < 0 ? presentValueBorrow(baseBorrowIndex_, uint104(-principal)) : 0;
    }

    // ============ Internal Math ============
    
    function mulFactor(uint n, uint factor) internal pure returns (uint) {
        return n * factor / FACTOR_SCALE;
    }

    function divBaseWei(uint n, uint baseWei) internal view returns (uint) {
        return n * baseScale / baseWei;
    }

    function mulPrice(uint n, uint price, uint64 fromScale) internal pure returns (uint) {
        return n * price / fromScale;
    }

    function signedMulPrice(int n, uint price, uint64 fromScale) internal pure returns (int) {
        return n * signed256(price) / int256(uint256(fromScale));
    }

    function divPrice(uint n, uint price, uint64 toScale) internal pure returns (uint) {
        return n * toScale / price;
    }

    function presentValue(int104 principalValue_) internal view returns (int256) {
        if (principalValue_ >= 0) {
            return signed256(presentValueSupply(baseSupplyIndex, uint104(principalValue_)));
        } else {
            return -signed256(presentValueBorrow(baseBorrowIndex, uint104(-principalValue_)));
        }
    }

    function presentValueSupply(uint64 baseSupplyIndex_, uint104 principalValue_) internal pure returns (uint256) {
        return uint256(principalValue_) * baseSupplyIndex_ / BASE_INDEX_SCALE;
    }

    function presentValueBorrow(uint64 baseBorrowIndex_, uint104 principalValue_) internal pure returns (uint256) {
        return uint256(principalValue_) * baseBorrowIndex_ / BASE_INDEX_SCALE;
    }

    function principalValue(int256 presentValue_) internal view returns (int104) {
        if (presentValue_ >= 0) {
            return int104(int256(uint256(presentValue_) * BASE_INDEX_SCALE / baseSupplyIndex));
        } else {
            return -int104(int256(uint256(uint256(-presentValue_)) * BASE_INDEX_SCALE / baseBorrowIndex));
        }
    }

    function repayAndSupplyAmount(int104 oldPrincipal, int104 newPrincipal) internal pure returns (uint104, uint104) {
        if (newPrincipal < oldPrincipal) return (0, 0);
        if (newPrincipal <= 0) {
            return (uint104(newPrincipal - oldPrincipal), 0);
        } else if (oldPrincipal >= 0) {
            return (0, uint104(newPrincipal - oldPrincipal));
        } else {
            return (uint104(-oldPrincipal), uint104(newPrincipal));
        }
    }

    function withdrawAndBorrowAmount(int104 oldPrincipal, int104 newPrincipal) internal pure returns (uint104, uint104) {
        if (newPrincipal > oldPrincipal) return (0, 0);
        if (newPrincipal >= 0) {
            return (uint104(oldPrincipal - newPrincipal), 0);
        } else if (oldPrincipal <= 0) {
            return (0, uint104(oldPrincipal - newPrincipal));
        } else {
            return (uint104(oldPrincipal), uint104(-newPrincipal));
        }
    }

    // ============ Helpers ============
    
    function isInAsset(uint16 assetsIn, uint8 assetOffset) internal pure returns (bool) {
        return (assetsIn & (uint16(1) << assetOffset) != 0);
    }

    function updateAssetsIn(address account, AssetInfo memory assetInfo, uint128 initialUserBalance, uint128 finalUserBalance) internal {
        if (initialUserBalance == 0 && finalUserBalance != 0) {
            userBasic[account].assetsIn |= (uint16(1) << assetInfo.offset);
        } else if (initialUserBalance != 0 && finalUserBalance == 0) {
            userBasic[account].assetsIn &= ~(uint16(1) << assetInfo.offset);
        }
    }

    function updateBasePrincipal(address account, UserBasic memory basic, int104 principalNew) internal {
        int104 principal = basic.principal;
        basic.principal = principalNew;

        if (principal >= 0) {
            uint indexDelta = uint256(trackingSupplyIndex - basic.baseTrackingIndex);
            basic.baseTrackingAccrued += uint64(uint104(principal) * indexDelta / trackingIndexScale / (baseScale / BASE_ACCRUAL_SCALE));
        } else {
            uint indexDelta = uint256(trackingBorrowIndex - basic.baseTrackingIndex);
            basic.baseTrackingAccrued += uint64(uint104(-principal) * indexDelta / trackingIndexScale / (baseScale / BASE_ACCRUAL_SCALE));
        }

        if (principalNew >= 0) {
            basic.baseTrackingIndex = trackingSupplyIndex;
        } else {
            basic.baseTrackingIndex = trackingBorrowIndex;
        }

        userBasic[account] = basic;
    }

    // ============ Token Transfer ============

    /**
     * @dev Transfer tokens in — does NOT check return value properly for fee-on-transfer tokens
     */
    function doTransferIn(address asset, address from, uint amount) internal returns (uint) {
        uint256 preBalance = IERC20(asset).balanceOf(address(this));
        IERC20(asset).transferFrom(from, address(this), amount);
        // VULNERABILITY: Assumes transfer always succeeds, no bool check
        // VULNERABILITY: Does not account for fee-on-transfer tokens in all cases
        return IERC20(asset).balanceOf(address(this)) - preBalance;
    }

    function doTransferOut(address asset, address to, uint amount) internal {
        IERC20(asset).transfer(to, amount);
        // VULNERABILITY: No return value check
    }

    // ============ Type Conversion Helpers ============
    
    function signed256(uint256 n) internal pure returns (int256) {
        require(n <= uint256(type(int256).max), "Overflow");
        return int256(n);
    }

    function unsigned256(int256 n) internal pure returns (uint256) {
        require(n >= 0, "Negative");
        return uint256(n);
    }

    function unsigned104(int104 n) internal pure returns (uint104) {
        require(n >= 0, "Negative");
        return uint104(n);
    }

    function toUInt8(bool x) internal pure returns (uint8) {
        return x ? 1 : 0;
    }

    function toBool(uint8 x) internal pure returns (bool) {
        return x != 0;
    }

    // ============ Fallback (Delegate) ============
    
    /**
     * @dev Delegates all unknown calls to extensionDelegate
     * VULNERABILITY: delegatecall to mutable/configurable address
     */
    fallback() external payable {
        address delegate = extensionDelegate;
        assembly {
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), delegate, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}
