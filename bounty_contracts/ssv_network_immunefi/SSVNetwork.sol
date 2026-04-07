// SPDX-License-Identifier: GPL-3.0-or-later
// Source: https://github.com/ssvlabs/ssv-network/blob/main/contracts/SSVNetwork.sol
// Bug Bounty: Immunefi SSV Network (up to $1,000,000)
// https://immunefi.com/bounty/ssvnetwork/
pragma solidity 0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/Ownable2StepUpgradeable.sol";

// ============================================================
//  SSV Network Core Interfaces & Types (flattened for audit)
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

    struct OperatorFeeChangeRequest {
        uint64 fee;
        uint64 approvalBeginTime;
        uint64 approvalEndTime;
    }

    error CallerNotOwnerWithData(address caller, address owner);
    error CallerNotWhitelistedWithData(uint64 operatorId);
    error ClusterDoesNotExists();
    error ClusterIsLiquidated();
    error ExceedValidatorLimitWithData(uint64 operatorId);
    error FeeTooHigh();
    error FeeTooLow();
    error IncorrectClusterState();
    error IncorrectValidatorStateWithData(bytes publicKey);
    error InsufficientBalance();
    error InvalidOperatorIdsLength();
    error InvalidWhitelistAddressesLength();
    error OperatorAlreadyExists();
    error OperatorDoesNotExist();
    error UnsortedOperatorsList();
    error OperatorsListNotUnique();
    error ValidatorDoesNotExist();
    error ZeroAddressNotAllowed();
    error AddressIsWhitelistingContract(address addr);
}

// ============================================================
//  Type conversion library
// ============================================================
library Types64 {
    function expand(uint64 val) internal pure returns (uint256) {
        return uint256(val) * 10000000;
    }
}

library Types256 {
    function shrink(uint256 val) internal pure returns (uint64) {
        require(val % 10000000 == 0, "Precision error");
        return uint64(val / 10000000);
    }
}

// ============================================================
//  SSV Storage
// ============================================================
enum SSVModules {
    SSV_OPERATORS,
    SSV_CLUSTERS,
    SSV_DAO,
    SSV_VIEWS,
    SSV_OPERATORS_WHITELIST
}

struct StorageData {
    IERC20 token;
    mapping(uint64 => ISSVNetworkCore.Operator) operators;
    mapping(bytes32 => bytes32) clusters;
    mapping(bytes32 => bytes32) validatorPKs;
    mapping(bytes32 => uint64) operatorsPKs;
    mapping(SSVModules => address) ssvContracts;
    mapping(uint64 => address) operatorsWhitelist;
    mapping(uint64 => ISSVNetworkCore.OperatorFeeChangeRequest) operatorFeeChangeRequests;
    mapping(address => mapping(uint256 => uint256)) addressWhitelistedForOperators;
    uint64 lastOperatorId;
}

library SSVStorage {
    bytes32 constant SSV_STORAGE_POSITION = keccak256("ssv.network.storage.main");

    function load() internal pure returns (StorageData storage sd) {
        bytes32 position = SSV_STORAGE_POSITION;
        assembly {
            sd.slot := position
        }
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
        assembly {
            sp.slot := position
        }
    }
}

// ============================================================
//  Protocol Library
// ============================================================
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

    function updateDAO(StorageProtocol storage sp, bool increase, uint32 deltaValidatorCount) internal {
        sp.daoBalance = networkTotalEarnings(sp);
        sp.daoIndexBlockNumber = uint32(block.number);
    }
}

// ============================================================
//  Core Library
// ============================================================
library CoreLib {
    function getVersion() internal pure returns (string memory) {
        return "v1.2.0";
    }

    function deposit(uint256 amount) internal {
        SSVStorage.load().token.transferFrom(msg.sender, address(this), amount);
    }

    function transferBalance(address to, uint256 amount) internal {
        SSVStorage.load().token.transfer(to, amount);
    }

    function setModuleContract(SSVModules moduleId, address moduleAddress) internal {
        SSVStorage.load().ssvContracts[moduleId] = moduleAddress;
    }
}

// ============================================================
//  Cluster Library
// ============================================================
library ClusterLib {
    using Types64 for uint64;
    using ProtocolLib for StorageProtocol;

    function updateBalance(
        ISSVNetworkCore.Cluster memory cluster,
        uint64 newIndex,
        uint64 currentNetworkFeeIndex_
    ) internal pure {
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
    ) internal pure returns (bool liquidatable) {
        if (cluster.validatorCount != 0) {
            if (cluster.balance < minimumLiquidationCollateral.expand()) return true;
            uint64 liquidationThreshold = minimumBlocksBeforeLiquidation *
                (burnRate + networkFee) *
                cluster.validatorCount;
            return cluster.balance < liquidationThreshold.expand();
        }
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
        if (clusterData == bytes32(0)) {
            revert ISSVNetworkCore.ClusterDoesNotExists();
        } else if (clusterData != hashedClusterData) {
            revert ISSVNetworkCore.IncorrectClusterState();
        }
    }

    function updateClusterData(
        ISSVNetworkCore.Cluster memory cluster,
        uint64 clusterIndex,
        uint64 currentNetworkFeeIndex_
    ) internal pure {
        updateBalance(cluster, clusterIndex, currentNetworkFeeIndex_);
        cluster.index = clusterIndex;
        cluster.networkFeeIndex = currentNetworkFeeIndex_;
    }

    function hashClusterData(ISSVNetworkCore.Cluster memory cluster) internal pure returns (bytes32) {
        return keccak256(
            abi.encodePacked(
                cluster.validatorCount,
                cluster.networkFeeIndex,
                cluster.index,
                cluster.balance,
                cluster.active
            )
        );
    }
}

// ============================================================
//  Operator Library
// ============================================================
library OperatorLib {
    using Types64 for uint64;

    function updateSnapshot(ISSVNetworkCore.Operator memory operator) internal view {
        uint64 blockDiffFee = (uint32(block.number) - operator.snapshot.block) * operator.fee;
        operator.snapshot.index += blockDiffFee;
        operator.snapshot.balance += blockDiffFee * operator.validatorCount;
        operator.snapshot.block = uint32(block.number);
    }

    function checkOwner(ISSVNetworkCore.Operator memory operator) internal view {
        if (operator.snapshot.block == 0) revert ISSVNetworkCore.OperatorDoesNotExist();
        if (operator.owner != msg.sender) revert ISSVNetworkCore.CallerNotOwnerWithData(msg.sender, operator.owner);
    }
}

// ============================================================
//  SSV Proxy — delegatecall router
// ============================================================
contract SSVProxy {
    function _delegate(address implementation) internal {
        assembly {
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), implementation, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}

// ============================================================
//  SSVNetwork — Main entry-point (UUPS proxy pattern)
//  Bug Bounty Scope: Immunefi SSV Network
// ============================================================
contract SSVNetwork is
    UUPSUpgradeable,
    Ownable2StepUpgradeable,
    ISSVNetworkCore,
    SSVProxy
{
    using Types256 for uint256;

    function initialize(
        IERC20 token_,
        address ssvOperators_,
        address ssvClusters_,
        address ssvDAO_,
        address ssvViews_,
        uint64 minimumBlocksBeforeLiquidation_,
        uint256 minimumLiquidationCollateral_,
        uint32 validatorsPerOperatorLimit_,
        uint64 declareOperatorFeePeriod_,
        uint64 executeOperatorFeePeriod_,
        uint64 operatorMaxFeeIncrease_
    ) external initializer onlyProxy {
        __UUPSUpgradeable_init();
        __Ownable_init_unchained();
        StorageData storage s = SSVStorage.load();
        StorageProtocol storage sp = SSVStorageProtocol.load();
        s.token = token_;
        s.ssvContracts[SSVModules.SSV_OPERATORS] = ssvOperators_;
        s.ssvContracts[SSVModules.SSV_CLUSTERS] = ssvClusters_;
        s.ssvContracts[SSVModules.SSV_DAO] = ssvDAO_;
        s.ssvContracts[SSVModules.SSV_VIEWS] = ssvViews_;
        sp.minimumBlocksBeforeLiquidation = minimumBlocksBeforeLiquidation_;
        sp.minimumLiquidationCollateral = minimumLiquidationCollateral_.shrink();
        sp.validatorsPerOperatorLimit = validatorsPerOperatorLimit_;
        sp.declareOperatorFeePeriod = declareOperatorFeePeriod_;
        sp.executeOperatorFeePeriod = executeOperatorFeePeriod_;
        sp.operatorMaxFeeIncrease = operatorMaxFeeIncrease_;
    }

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    function _authorizeUpgrade(address) internal override onlyOwner {}

    fallback() external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_VIEWS]);
    }

    // ── Operator functions (delegate to SSV_OPERATORS module) ──
    function registerOperator(bytes calldata publicKey, uint256 fee, bool setPrivate) external returns (uint64 id) {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_OPERATORS]);
    }

    function removeOperator(uint64 operatorId) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_OPERATORS]);
    }

    function declareOperatorFee(uint64 operatorId, uint256 fee) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_OPERATORS]);
    }

    function executeOperatorFee(uint64 operatorId) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_OPERATORS]);
    }

    function cancelDeclaredOperatorFee(uint64 operatorId) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_OPERATORS]);
    }

    function reduceOperatorFee(uint64 operatorId, uint256 fee) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_OPERATORS]);
    }

    function withdrawOperatorEarnings(uint64 operatorId, uint256 amount) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_OPERATORS]);
    }

    function withdrawAllOperatorEarnings(uint64 operatorId) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_OPERATORS]);
    }

    // ── Cluster functions (delegate to SSV_CLUSTERS module) ──
    function registerValidator(
        bytes calldata publicKey,
        uint64[] calldata operatorIds,
        bytes calldata sharesData,
        uint256 amount,
        Cluster memory cluster
    ) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_CLUSTERS]);
    }

    function removeValidator(
        bytes calldata publicKey,
        uint64[] calldata operatorIds,
        Cluster memory cluster
    ) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_CLUSTERS]);
    }

    function liquidate(
        address clusterOwner,
        uint64[] calldata operatorIds,
        Cluster memory cluster
    ) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_CLUSTERS]);
    }

    function reactivate(uint64[] calldata operatorIds, uint256 amount, Cluster memory cluster) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_CLUSTERS]);
    }

    function deposit(
        address clusterOwner,
        uint64[] calldata operatorIds,
        uint256 amount,
        Cluster memory cluster
    ) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_CLUSTERS]);
    }

    function withdraw(uint64[] calldata operatorIds, uint256 amount, Cluster memory cluster) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_CLUSTERS]);
    }

    // ── DAO functions (delegate to SSV_DAO module) ──
    function updateNetworkFee(uint256 fee) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_DAO]);
    }

    function withdrawNetworkEarnings(uint256 amount) external {
        _delegate(SSVStorage.load().ssvContracts[SSVModules.SSV_DAO]);
    }

    function setFeeRecipientAddress(address recipientAddress) external {
        // emit FeeRecipientAddressUpdated(msg.sender, recipientAddress);
    }

    function getVersion() external pure returns (string memory) {
        return CoreLib.getVersion();
    }

    function updateModule(SSVModules moduleId, address moduleAddress) external onlyOwner {
        CoreLib.setModuleContract(moduleId, moduleAddress);
    }
}
