// SPDX-License-Identifier: GPL-3.0-or-later
// Source: https://github.com/ssvlabs/ssv-network/blob/main/contracts/modules/SSVClusters.sol
// Bug Bounty: Immunefi SSV Network (up to $1,000,000)
pragma solidity 0.8.24;

// ============================================================
//  Flattened types & interfaces for standalone audit
// ============================================================

interface ISSVNetworkCore {
    struct Cluster {
        uint32 validatorCount;
        uint64 networkFeeIndex;
        uint64 index;
        uint256 balance;
        bool active;
    }
    struct Operator {
        address owner;
        Snapshot snapshot;
        uint32 validatorCount;
        uint64 fee;
        bool whitelisted;
    }
    struct Snapshot {
        uint32 block;
        uint64 index;
        uint64 balance;
    }

    error ClusterDoesNotExists();
    error ClusterIsLiquidated();
    error ClusterAlreadyEnabled();
    error ClusterNotLiquidatable();
    error IncorrectClusterState();
    error IncorrectValidatorStateWithData(bytes publicKey);
    error InsufficientBalance();
    error ValidatorDoesNotExist();
    error EmptyPublicKeysList();
    error PublicKeysSharesLengthMismatch();
    error ExceedValidatorLimitWithData(uint64 operatorId);
    error UnsortedOperatorsList();
    error OperatorsListNotUnique();
    error OperatorDoesNotExist();
    error CallerNotOwnerWithData(address caller, address owner);
    error CallerNotWhitelistedWithData(uint64 operatorId);
}

library Types64 {
    function expand(uint64 val) internal pure returns (uint256) {
        return uint256(val) * 10000000;
    }
}

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

struct StorageData {
    IERC20 token;
    mapping(uint64 => ISSVNetworkCore.Operator) operators;
    mapping(bytes32 => bytes32) clusters;
    mapping(bytes32 => bytes32) validatorPKs;
    mapping(bytes32 => uint64) operatorsPKs;
    mapping(uint256 => address) ssvContracts;
    mapping(uint64 => address) operatorsWhitelist;
    mapping(address => mapping(uint256 => uint256)) addressWhitelistedForOperators;
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
    function currentNetworkFeeIndex(StorageProtocol storage sp) internal view returns (uint64) {
        return sp.networkFeeIndex + uint64(block.number - sp.daoIndexBlockNumber) * sp.networkFee;
    }
    function updateDAO(StorageProtocol storage sp, bool increase, uint32 deltaValidatorCount) internal {
        sp.daoBalance = sp.daoBalance + uint64(block.number - sp.daoIndexBlockNumber) * sp.networkFee;
        sp.daoIndexBlockNumber = uint32(block.number);
    }
}

library CoreLib {
    function deposit(uint256 amount) internal {
        SSVStorage.load().token.transferFrom(msg.sender, address(this), amount);
    }
    function transferBalance(address to, uint256 amount) internal {
        SSVStorage.load().token.transfer(to, amount);
    }
}

library ValidatorLib {
    function validateOperatorsLength(uint64[] memory operatorIds) internal pure {
        if (operatorIds.length < 4 || operatorIds.length > 13 || operatorIds.length % 3 != 1)
            revert ISSVNetworkCore.IncorrectClusterState();
    }
    function registerPublicKey(bytes memory publicKey, uint64[] memory operatorIds, StorageData storage s) internal {
        bytes32 hashedValidator = keccak256(abi.encodePacked(publicKey, msg.sender));
        if (s.validatorPKs[hashedValidator] != bytes32(0)) revert ISSVNetworkCore.IncorrectValidatorStateWithData(publicKey);
        s.validatorPKs[hashedValidator] = keccak256(abi.encodePacked(hashOperatorIds(operatorIds)));
    }
    function hashOperatorIds(uint64[] memory operatorIds) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(operatorIds));
    }
    function validateCorrectState(bytes32 validatorData, bytes32 hashedOperatorIds) internal pure returns (bool) {
        return validatorData == keccak256(abi.encodePacked(hashedOperatorIds));
    }
}

library ClusterLib {
    using Types64 for uint64;
    using ProtocolLib for StorageProtocol;

    function updateBalance(ISSVNetworkCore.Cluster memory cluster, uint64 newIndex, uint64 currentNetworkFeeIndex_) internal pure {
        uint64 networkFee = uint64(currentNetworkFeeIndex_ - cluster.networkFeeIndex) * cluster.validatorCount;
        uint64 usage = (newIndex - cluster.index) * cluster.validatorCount + networkFee;
        cluster.balance = usage.expand() > cluster.balance ? 0 : cluster.balance - usage.expand();
    }

    function isLiquidatable(
        ISSVNetworkCore.Cluster memory cluster,
        uint64 burnRate,
        uint64 networkFee,
        uint64 minimumBlocksBeforeLiquidation,
        uint64 minimumLiquidationCollateral
    ) internal pure returns (bool) {
        if (cluster.validatorCount != 0) {
            if (cluster.balance < minimumLiquidationCollateral.expand()) return true;
            uint64 liquidationThreshold = minimumBlocksBeforeLiquidation * (burnRate + networkFee) * cluster.validatorCount;
            return cluster.balance < liquidationThreshold.expand();
        }
        return false;
    }

    function validateClusterIsNotLiquidated(ISSVNetworkCore.Cluster memory cluster) internal pure {
        if (!cluster.active) revert ISSVNetworkCore.ClusterIsLiquidated();
    }

    function validateHashedCluster(
        ISSVNetworkCore.Cluster memory cluster,
        address owner,
        uint64[] memory operatorIds,
        StorageData storage s
    ) internal view returns (bytes32 hashedCluster) {
        hashedCluster = keccak256(abi.encodePacked(owner, operatorIds));
        bytes32 hashedClusterData = hashClusterData(cluster);
        bytes32 clusterData = s.clusters[hashedCluster];
        if (clusterData == bytes32(0)) revert ISSVNetworkCore.ClusterDoesNotExists();
        else if (clusterData != hashedClusterData) revert ISSVNetworkCore.IncorrectClusterState();
    }

    function updateClusterData(ISSVNetworkCore.Cluster memory cluster, uint64 clusterIndex, uint64 currentNetworkFeeIndex_) internal pure {
        updateBalance(cluster, clusterIndex, currentNetworkFeeIndex_);
        cluster.index = clusterIndex;
        cluster.networkFeeIndex = currentNetworkFeeIndex_;
    }

    function hashClusterData(ISSVNetworkCore.Cluster memory cluster) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(cluster.validatorCount, cluster.networkFeeIndex, cluster.index, cluster.balance, cluster.active));
    }

    function validateClusterOnRegistration(
        ISSVNetworkCore.Cluster memory cluster,
        uint64[] memory operatorIds,
        StorageData storage s
    ) internal view returns (bytes32 hashedCluster) {
        hashedCluster = keccak256(abi.encodePacked(msg.sender, operatorIds));
        bytes32 clusterData = s.clusters[hashedCluster];
        if (clusterData == bytes32(0)) {
            if (cluster.validatorCount != 0 || cluster.networkFeeIndex != 0 || cluster.index != 0 || cluster.balance != 0 || !cluster.active)
                revert ISSVNetworkCore.IncorrectClusterState();
        } else if (clusterData != hashClusterData(cluster)) {
            revert ISSVNetworkCore.IncorrectClusterState();
        } else {
            validateClusterIsNotLiquidated(cluster);
        }
    }

    function updateClusterOnRegistration(
        ISSVNetworkCore.Cluster memory cluster,
        uint64[] memory operatorIds,
        bytes32 hashedCluster,
        uint32 validatorCountDelta,
        StorageData storage s,
        StorageProtocol storage sp
    ) internal {
        uint64 cumulativeIndex;
        uint64 cumulativeFee;
        uint256 operatorsLength = operatorIds.length;
        for (uint256 i; i < operatorsLength; ++i) {
            ISSVNetworkCore.Operator storage operator = s.operators[operatorIds[i]];
            if (operator.snapshot.block == 0) revert ISSVNetworkCore.OperatorDoesNotExist();
            uint64 blockDiffFee = (uint32(block.number) - operator.snapshot.block) * operator.fee;
            operator.snapshot.index += blockDiffFee;
            operator.snapshot.balance += blockDiffFee * operator.validatorCount;
            operator.snapshot.block = uint32(block.number);
            if ((operator.validatorCount += validatorCountDelta) > sp.validatorsPerOperatorLimit)
                revert ISSVNetworkCore.ExceedValidatorLimitWithData(operatorIds[i]);
            cumulativeFee += operator.fee;
            cumulativeIndex += operator.snapshot.index;
        }

        updateClusterData(cluster, cumulativeIndex, sp.currentNetworkFeeIndex());
        sp.updateDAO(true, validatorCountDelta);
        cluster.validatorCount += validatorCountDelta;

        if (isLiquidatable(cluster, cumulativeFee, sp.networkFee, sp.minimumBlocksBeforeLiquidation, sp.minimumLiquidationCollateral))
            revert ISSVNetworkCore.InsufficientBalance();

        s.clusters[hashedCluster] = hashClusterData(cluster);
    }
}

// ============================================================
//  SSVClusters — Core cluster management (SECURITY CRITICAL)
//  Handles: register/remove validators, liquidate, reactivate,
//  deposit, withdraw
// ============================================================
contract SSVClusters is ISSVNetworkCore {
    using ClusterLib for Cluster;
    using Types64 for uint64;

    function registerValidator(
        bytes calldata publicKey,
        uint64[] memory operatorIds,
        bytes calldata sharesData,
        uint256 amount,
        Cluster memory cluster
    ) external {
        StorageData storage s = SSVStorage.load();
        StorageProtocol storage sp = SSVStorageProtocol.load();
        ValidatorLib.validateOperatorsLength(operatorIds);
        ValidatorLib.registerPublicKey(publicKey, operatorIds, s);
        bytes32 hashedCluster = cluster.validateClusterOnRegistration(operatorIds, s);
        cluster.balance += amount;
        cluster.updateClusterOnRegistration(operatorIds, hashedCluster, 1, s, sp);
        if (amount != 0) CoreLib.deposit(amount);
        emit ValidatorAdded(msg.sender, operatorIds, publicKey, sharesData, cluster);
    }

    function bulkRegisterValidator(
        bytes[] memory publicKeys,
        uint64[] memory operatorIds,
        bytes[] calldata sharesData,
        uint256 amount,
        Cluster memory cluster
    ) external {
        uint256 validatorsLength = publicKeys.length;
        if (validatorsLength == 0) revert EmptyPublicKeysList();
        if (validatorsLength != sharesData.length) revert PublicKeysSharesLengthMismatch();
        StorageData storage s = SSVStorage.load();
        StorageProtocol storage sp = SSVStorageProtocol.load();
        ValidatorLib.validateOperatorsLength(operatorIds);
        for (uint i; i < validatorsLength; ++i) {
            ValidatorLib.registerPublicKey(publicKeys[i], operatorIds, s);
        }
        bytes32 hashedCluster = cluster.validateClusterOnRegistration(operatorIds, s);
        cluster.balance += amount;
        cluster.updateClusterOnRegistration(operatorIds, hashedCluster, uint32(validatorsLength), s, sp);
        if (amount != 0) CoreLib.deposit(amount);
    }

    function removeValidator(
        bytes calldata publicKey,
        uint64[] memory operatorIds,
        Cluster memory cluster
    ) external {
        StorageData storage s = SSVStorage.load();
        bytes32 hashedCluster = cluster.validateHashedCluster(msg.sender, operatorIds, s);
        bytes32 hashedOperatorIds = ValidatorLib.hashOperatorIds(operatorIds);
        bytes32 hashedValidator = keccak256(abi.encodePacked(publicKey, msg.sender));
        bytes32 validatorData = s.validatorPKs[hashedValidator];
        if (validatorData == bytes32(0)) revert ValidatorDoesNotExist();
        if (!ValidatorLib.validateCorrectState(validatorData, hashedOperatorIds))
            revert IncorrectValidatorStateWithData(publicKey);
        delete s.validatorPKs[hashedValidator];
        if (cluster.active) {
            StorageProtocol storage sp = SSVStorageProtocol.load();
            uint64 clusterIndex;
            uint256 operatorsLength = operatorIds.length;
            for (uint256 i; i < operatorsLength; ++i) {
                ISSVNetworkCore.Operator storage operator = s.operators[operatorIds[i]];
                if (operator.snapshot.block != 0) {
                    uint64 blockDiffFee = (uint32(block.number) - operator.snapshot.block) * operator.fee;
                    operator.snapshot.index += blockDiffFee;
                    operator.snapshot.balance += blockDiffFee * operator.validatorCount;
                    operator.snapshot.block = uint32(block.number);
                    operator.validatorCount -= 1;
                }
                clusterIndex += operator.snapshot.index;
            }
            cluster.updateClusterData(clusterIndex, sp.currentNetworkFeeIndex());
            sp.updateDAO(false, 1);
        }
        --cluster.validatorCount;
        s.clusters[hashedCluster] = cluster.hashClusterData();
        emit ValidatorRemoved(msg.sender, operatorIds, publicKey, cluster);
    }

    function liquidate(
        address clusterOwner,
        uint64[] calldata operatorIds,
        Cluster memory cluster
    ) external {
        StorageData storage s = SSVStorage.load();
        bytes32 hashedCluster = cluster.validateHashedCluster(clusterOwner, operatorIds, s);
        cluster.validateClusterIsNotLiquidated();
        StorageProtocol storage sp = SSVStorageProtocol.load();

        uint64 clusterIndex;
        uint64 burnRate;
        uint256 operatorsLength = operatorIds.length;
        for (uint256 i; i < operatorsLength; ++i) {
            ISSVNetworkCore.Operator storage operator = s.operators[operatorIds[i]];
            if (operator.snapshot.block != 0) {
                uint64 blockDiffFee = (uint32(block.number) - operator.snapshot.block) * operator.fee;
                operator.snapshot.index += blockDiffFee;
                operator.snapshot.balance += blockDiffFee * operator.validatorCount;
                operator.snapshot.block = uint32(block.number);
                operator.validatorCount -= cluster.validatorCount;
                burnRate += operator.fee;
            }
            clusterIndex += operator.snapshot.index;
        }

        cluster.updateBalance(clusterIndex, sp.currentNetworkFeeIndex());

        uint256 balanceLiquidatable;
        if (
            clusterOwner != msg.sender &&
            !cluster.isLiquidatable(burnRate, sp.networkFee, sp.minimumBlocksBeforeLiquidation, sp.minimumLiquidationCollateral)
        ) {
            revert ClusterNotLiquidatable();
        }

        sp.updateDAO(false, cluster.validatorCount);

        if (cluster.balance != 0) {
            balanceLiquidatable = cluster.balance;
            cluster.balance = 0;
        }
        cluster.index = 0;
        cluster.networkFeeIndex = 0;
        cluster.active = false;
        s.clusters[hashedCluster] = cluster.hashClusterData();

        if (balanceLiquidatable != 0) {
            CoreLib.transferBalance(msg.sender, balanceLiquidatable);
        }
        emit ClusterLiquidated(clusterOwner, operatorIds, cluster);
    }

    function reactivate(uint64[] calldata operatorIds, uint256 amount, Cluster memory cluster) external {
        StorageData storage s = SSVStorage.load();
        bytes32 hashedCluster = cluster.validateHashedCluster(msg.sender, operatorIds, s);
        if (cluster.active) revert ClusterAlreadyEnabled();
        StorageProtocol storage sp = SSVStorageProtocol.load();

        uint64 clusterIndex;
        uint64 burnRate;
        uint256 operatorsLength = operatorIds.length;
        for (uint256 i; i < operatorsLength; ++i) {
            ISSVNetworkCore.Operator storage operator = s.operators[operatorIds[i]];
            if (operator.snapshot.block != 0) {
                uint64 blockDiffFee = (uint32(block.number) - operator.snapshot.block) * operator.fee;
                operator.snapshot.index += blockDiffFee;
                operator.snapshot.balance += blockDiffFee * operator.validatorCount;
                operator.snapshot.block = uint32(block.number);
                if ((operator.validatorCount += cluster.validatorCount) > sp.validatorsPerOperatorLimit)
                    revert ExceedValidatorLimitWithData(operatorIds[i]);
                burnRate += operator.fee;
            }
            clusterIndex += operator.snapshot.index;
        }

        cluster.balance += amount;
        cluster.active = true;
        cluster.index = clusterIndex;
        cluster.networkFeeIndex = sp.currentNetworkFeeIndex();
        sp.updateDAO(true, cluster.validatorCount);

        if (cluster.isLiquidatable(burnRate, sp.networkFee, sp.minimumBlocksBeforeLiquidation, sp.minimumLiquidationCollateral))
            revert InsufficientBalance();

        s.clusters[hashedCluster] = cluster.hashClusterData();
        if (amount > 0) CoreLib.deposit(amount);
        emit ClusterReactivated(msg.sender, operatorIds, cluster);
    }

    function deposit(
        address clusterOwner,
        uint64[] calldata operatorIds,
        uint256 amount,
        Cluster memory cluster
    ) external {
        StorageData storage s = SSVStorage.load();
        bytes32 hashedCluster = cluster.validateHashedCluster(clusterOwner, operatorIds, s);
        cluster.balance += amount;
        s.clusters[hashedCluster] = cluster.hashClusterData();
        CoreLib.deposit(amount);
        emit ClusterDeposited(clusterOwner, operatorIds, amount, cluster);
    }

    function withdraw(uint64[] calldata operatorIds, uint256 amount, Cluster memory cluster) external {
        StorageData storage s = SSVStorage.load();
        bytes32 hashedCluster = cluster.validateHashedCluster(msg.sender, operatorIds, s);
        cluster.validateClusterIsNotLiquidated();
        StorageProtocol storage sp = SSVStorageProtocol.load();

        uint64 burnRate;
        if (cluster.active) {
            uint64 clusterIndex;
            uint256 operatorsLength = operatorIds.length;
            for (uint256 i; i < operatorsLength; ++i) {
                ISSVNetworkCore.Operator storage operator = SSVStorage.load().operators[operatorIds[i]];
                clusterIndex += operator.snapshot.index + (uint64(block.number) - operator.snapshot.block) * operator.fee;
                burnRate += operator.fee;
            }
            cluster.updateClusterData(clusterIndex, sp.currentNetworkFeeIndex());
        }
        if (cluster.balance < amount) revert InsufficientBalance();
        cluster.balance -= amount;

        if (
            cluster.active &&
            cluster.validatorCount != 0 &&
            cluster.isLiquidatable(burnRate, sp.networkFee, sp.minimumBlocksBeforeLiquidation, sp.minimumLiquidationCollateral)
        ) {
            revert InsufficientBalance();
        }

        s.clusters[hashedCluster] = cluster.hashClusterData();
        CoreLib.transferBalance(msg.sender, amount);
        emit ClusterWithdrawn(msg.sender, operatorIds, amount, cluster);
    }

    // Events
    event ValidatorAdded(address indexed owner, uint64[] operatorIds, bytes publicKey, bytes sharesData, Cluster cluster);
    event ValidatorRemoved(address indexed owner, uint64[] operatorIds, bytes publicKey, Cluster cluster);
    event ClusterLiquidated(address indexed owner, uint64[] operatorIds, Cluster cluster);
    event ClusterReactivated(address indexed owner, uint64[] operatorIds, Cluster cluster);
    event ClusterDeposited(address indexed owner, uint64[] operatorIds, uint256 value, Cluster cluster);
    event ClusterWithdrawn(address indexed owner, uint64[] operatorIds, uint256 value, Cluster cluster);
}
