// SPDX-License-Identifier: GPL-3.0-or-later
// Source: https://github.com/ssvlabs/ssv-network/blob/main/contracts/modules/SSVDAO.sol
// Bug Bounty: Immunefi SSV Network (up to $1,000,000)
pragma solidity 0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

// ============================================================
//  Flattened interfaces & types for standalone audit
// ============================================================

interface ISSVNetworkCore {
    error InsufficientBalance();
    error NewBlockPeriodIsBelowMinimum();
}

library Types64 {
    function expand(uint64 val) internal pure returns (uint256) {
        return uint256(val) * 10000000;
    }
}

library Types256 {
    function shrink(uint256 val) internal pure returns (uint64) {
        return uint64(val / 10000000);
    }
}

struct StorageData {
    IERC20 token;
}

library SSVStorage {
    bytes32 constant SSV_STORAGE_POSITION = keccak256("ssv.network.storage.main");
    function load() internal pure returns (StorageData storage sd) {
        bytes32 position = SSV_STORAGE_POSITION;
        assembly { sd.slot := position }
    }
}

struct StorageProtocol {
    uint32 daoIndexBlockNumber;
    uint64 daoBalance;
    uint64 networkFee;
    uint64 networkFeeIndex;
    uint64 minimumBlocksBeforeLiquidation;
    uint64 minimumLiquidationCollateral;
    uint32 validatorsPerOperatorLimit;
    uint64 declareOperatorFeePeriod;
    uint64 executeOperatorFeePeriod;
    uint64 operatorMaxFeeIncrease;
    uint64 operatorMaxFee;
}

library SSVStorageProtocol {
    bytes32 constant SSV_STORAGE_PROTOCOL_POSITION = keccak256("ssv.network.storage.protocol");
    function load() internal pure returns (StorageProtocol storage sp) {
        bytes32 position = SSV_STORAGE_PROTOCOL_POSITION;
        assembly { sp.slot := position }
    }
}

library ProtocolLib {
    using Types64 for uint64;

    function currentNetworkFeeIndex(StorageProtocol storage sp) internal view returns (uint64) {
        return sp.networkFeeIndex + uint64(block.number - sp.daoIndexBlockNumber) * sp.networkFee;
    }

    function networkTotalEarnings(StorageProtocol storage sp) internal view returns (uint64) {
        return sp.daoBalance + uint64(block.number - sp.daoIndexBlockNumber) * sp.networkFee;
    }

    function updateNetworkFee(StorageProtocol storage sp, uint256 fee) internal {
        sp.daoBalance = networkTotalEarnings(sp);
        sp.daoIndexBlockNumber = uint32(block.number);
        sp.networkFee = uint64(fee / 10000000);
        sp.networkFeeIndex = currentNetworkFeeIndex(sp);
    }
}

library CoreLib {
    function transferBalance(address to, uint256 amount) internal {
        SSVStorage.load().token.transfer(to, amount);
    }
}

// ============================================================
//  SSVDAO — DAO governance functions (SECURITY CRITICAL)
//  Handles: network fee, earnings withdrawal, protocol params
// ============================================================
contract SSVDAO is ISSVNetworkCore {
    using Types64 for uint64;
    using Types256 for uint256;
    using ProtocolLib for StorageProtocol;

    uint64 private constant MINIMAL_LIQUIDATION_THRESHOLD = 100_800;

    function updateNetworkFee(uint256 fee) external {
        StorageProtocol storage sp = SSVStorageProtocol.load();
        uint64 previousFee = sp.networkFee;
        sp.updateNetworkFee(fee);
        emit NetworkFeeUpdated(previousFee.expand(), fee);
    }

    function withdrawNetworkEarnings(uint256 amount) external {
        StorageProtocol storage sp = SSVStorageProtocol.load();
        uint64 shrunkAmount = amount.shrink();
        uint64 networkBalance = sp.networkTotalEarnings();
        if (shrunkAmount > networkBalance) revert InsufficientBalance();
        sp.daoBalance = networkBalance - shrunkAmount;
        sp.daoIndexBlockNumber = uint32(block.number);
        CoreLib.transferBalance(msg.sender, amount);
        emit NetworkEarningsWithdrawn(amount, msg.sender);
    }

    function updateOperatorFeeIncreaseLimit(uint64 percentage) external {
        SSVStorageProtocol.load().operatorMaxFeeIncrease = percentage;
        emit OperatorFeeIncreaseLimitUpdated(percentage);
    }

    function updateDeclareOperatorFeePeriod(uint64 timeInSeconds) external {
        SSVStorageProtocol.load().declareOperatorFeePeriod = timeInSeconds;
        emit DeclareOperatorFeePeriodUpdated(timeInSeconds);
    }

    function updateExecuteOperatorFeePeriod(uint64 timeInSeconds) external {
        SSVStorageProtocol.load().executeOperatorFeePeriod = timeInSeconds;
        emit ExecuteOperatorFeePeriodUpdated(timeInSeconds);
    }

    function updateLiquidationThresholdPeriod(uint64 blocks) external {
        if (blocks < MINIMAL_LIQUIDATION_THRESHOLD) revert NewBlockPeriodIsBelowMinimum();
        SSVStorageProtocol.load().minimumBlocksBeforeLiquidation = blocks;
        emit LiquidationThresholdPeriodUpdated(blocks);
    }

    function updateMinimumLiquidationCollateral(uint256 amount) external {
        SSVStorageProtocol.load().minimumLiquidationCollateral = amount.shrink();
        emit MinimumLiquidationCollateralUpdated(amount);
    }

    function updateMaximumOperatorFee(uint64 maxFee) external {
        SSVStorageProtocol.load().operatorMaxFee = maxFee;
        emit OperatorMaximumFeeUpdated(maxFee);
    }

    // Events
    event NetworkFeeUpdated(uint256 oldFee, uint256 newFee);
    event NetworkEarningsWithdrawn(uint256 value, address recipient);
    event OperatorFeeIncreaseLimitUpdated(uint64 value);
    event DeclareOperatorFeePeriodUpdated(uint64 value);
    event ExecuteOperatorFeePeriodUpdated(uint64 value);
    event LiquidationThresholdPeriodUpdated(uint64 value);
    event MinimumLiquidationCollateralUpdated(uint256 value);
    event OperatorMaximumFeeUpdated(uint64 value);
}
