// SPDX-License-Identifier: GPL-3.0-or-later
// Source: https://github.com/ssvlabs/ssv-network/blob/main/contracts/modules/SSVOperators.sol
// Bug Bounty: Immunefi SSV Network (up to $1,000,000)
pragma solidity 0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

// ============================================================
//  Flattened interfaces & types for standalone audit
// ============================================================

interface ISSVNetworkCore {
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
    error FeeTooLow();
    error FeeTooHigh();
    error OperatorAlreadyExists();
    error OperatorDoesNotExist();
    error InsufficientBalance();
    error NoFeeDeclared();
    error ApprovalNotWithinTimeframe();
    error SameFeeChangeNotAllowed();
    error FeeIncreaseNotAllowed();
    error FeeExceedsIncreaseLimit();
    error InvalidOperatorIdsLength();
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
    mapping(uint64 => ISSVNetworkCore.Operator) operators;
    mapping(bytes32 => bytes32) clusters;
    mapping(bytes32 => uint64) operatorsPKs;
    mapping(uint64 => address) operatorsWhitelist;
    mapping(uint64 => ISSVNetworkCore.OperatorFeeChangeRequest) operatorFeeChangeRequests;
    uint64 lastOperatorId;
}

library SSVStorage {
    bytes32 constant SSV_STORAGE_POSITION = keccak256("ssv.network.storage.main");
    function load() internal pure returns (StorageData storage sd) {
        bytes32 position = SSV_STORAGE_POSITION;
        assembly { sd.slot := position }
    }
}

struct StorageProtocol {
    uint64 operatorMaxFee;
    uint64 operatorMaxFeeIncrease;
    uint64 declareOperatorFeePeriod;
    uint64 executeOperatorFeePeriod;
    uint32 validatorsPerOperatorLimit;
}

library SSVStorageProtocol {
    bytes32 constant SSV_STORAGE_PROTOCOL_POSITION = keccak256("ssv.network.storage.protocol");
    function load() internal pure returns (StorageProtocol storage sp) {
        bytes32 position = SSV_STORAGE_PROTOCOL_POSITION;
        assembly { sp.slot := position }
    }
}

library CoreLib {
    function transferBalance(address to, uint256 amount) internal {
        SSVStorage.load().token.transfer(to, amount);
    }
}

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

    function updatePrivacyStatus(uint64[] calldata operatorIds, bool setPrivate, StorageData storage s) internal {
        uint256 operatorsLength = operatorIds.length;
        if (operatorsLength == 0) revert ISSVNetworkCore.InvalidOperatorIdsLength();
        for (uint256 i; i < operatorsLength; ++i) {
            ISSVNetworkCore.Operator storage operator = s.operators[operatorIds[i]];
            checkOwner(operator);
            operator.whitelisted = setPrivate;
        }
    }

    function checkOwner(ISSVNetworkCore.Operator storage operator) internal view {
        if (operator.snapshot.block == 0) revert ISSVNetworkCore.OperatorDoesNotExist();
        if (operator.owner != msg.sender) revert ISSVNetworkCore.CallerNotOwnerWithData(msg.sender, operator.owner);
    }
}

// ============================================================
//  SSVOperators — Operator management module (SECURITY CRITICAL)
//  Handles: register/remove operators, fee management, withdrawals
// ============================================================
contract SSVOperators is ISSVNetworkCore {
    uint64 private constant MINIMAL_OPERATOR_FEE = 1_000_000_000;
    uint64 private constant PRECISION_FACTOR = 10_000;

    using Types256 for uint256;
    using Types64 for uint64;
    using OperatorLib for Operator;

    function registerOperator(
        bytes calldata publicKey,
        uint256 fee,
        bool setPrivate
    ) external returns (uint64 id) {
        if (fee != 0 && fee < MINIMAL_OPERATOR_FEE) revert FeeTooLow();
        if (fee > SSVStorageProtocol.load().operatorMaxFee) revert FeeTooHigh();

        StorageData storage s = SSVStorage.load();
        bytes32 hashedPk = keccak256(publicKey);
        if (s.operatorsPKs[hashedPk] != 0) revert OperatorAlreadyExists();

        s.lastOperatorId++;
        id = s.lastOperatorId;
        s.operators[id] = Operator({
            owner: msg.sender,
            snapshot: Snapshot({block: uint32(block.number), index: 0, balance: 0}),
            validatorCount: 0,
            fee: fee.shrink(),
            whitelisted: setPrivate
        });
        s.operatorsPKs[hashedPk] = id;

        emit OperatorAdded(id, msg.sender, publicKey, fee);
    }

    function removeOperator(uint64 operatorId) external {
        StorageData storage s = SSVStorage.load();
        Operator memory operator = s.operators[operatorId];
        operator.checkOwner();
        operator.updateSnapshot();
        uint64 currentBalance = operator.snapshot.balance;
        operator.snapshot.block = 0;
        operator.snapshot.balance = 0;
        operator.validatorCount = 0;
        operator.fee = 0;
        s.operators[operatorId] = operator;
        delete s.operatorsWhitelist[operatorId];
        if (currentBalance > 0) {
            _transferOperatorBalanceUnsafe(operatorId, currentBalance.expand());
        }
        emit OperatorRemoved(operatorId);
    }

    function declareOperatorFee(uint64 operatorId, uint256 fee) external {
        StorageData storage s = SSVStorage.load();
        s.operators[operatorId].checkOwner();
        StorageProtocol storage sp = SSVStorageProtocol.load();

        if (fee != 0 && fee < MINIMAL_OPERATOR_FEE) revert FeeTooLow();
        if (fee > sp.operatorMaxFee) revert FeeTooHigh();

        uint64 operatorFee = s.operators[operatorId].fee;
        uint64 shrunkFee = fee.shrink();

        if (operatorFee == shrunkFee) revert SameFeeChangeNotAllowed();
        else if (shrunkFee != 0 && operatorFee == 0) revert FeeIncreaseNotAllowed();

        uint64 maxAllowedFee = (operatorFee * (PRECISION_FACTOR + sp.operatorMaxFeeIncrease)) / PRECISION_FACTOR;
        if (shrunkFee > maxAllowedFee) revert FeeExceedsIncreaseLimit();

        s.operatorFeeChangeRequests[operatorId] = OperatorFeeChangeRequest(
            shrunkFee,
            uint64(block.timestamp) + sp.declareOperatorFeePeriod,
            uint64(block.timestamp) + sp.declareOperatorFeePeriod + sp.executeOperatorFeePeriod
        );
        emit OperatorFeeDeclared(msg.sender, operatorId, block.number, fee);
    }

    function executeOperatorFee(uint64 operatorId) external {
        StorageData storage s = SSVStorage.load();
        Operator memory operator = s.operators[operatorId];
        operator.checkOwner();

        OperatorFeeChangeRequest memory feeChangeRequest = s.operatorFeeChangeRequests[operatorId];
        if (feeChangeRequest.approvalBeginTime == 0) revert NoFeeDeclared();
        if (block.timestamp < feeChangeRequest.approvalBeginTime || block.timestamp > feeChangeRequest.approvalEndTime)
            revert ApprovalNotWithinTimeframe();
        if (feeChangeRequest.fee.expand() > SSVStorageProtocol.load().operatorMaxFee) revert FeeTooHigh();

        operator.updateSnapshot();
        operator.fee = feeChangeRequest.fee;
        s.operators[operatorId] = operator;
        delete s.operatorFeeChangeRequests[operatorId];

        emit OperatorFeeExecuted(msg.sender, operatorId, block.number, feeChangeRequest.fee.expand());
    }

    function cancelDeclaredOperatorFee(uint64 operatorId) external {
        StorageData storage s = SSVStorage.load();
        s.operators[operatorId].checkOwner();
        if (s.operatorFeeChangeRequests[operatorId].approvalBeginTime == 0) revert NoFeeDeclared();
        delete s.operatorFeeChangeRequests[operatorId];
        emit OperatorFeeDeclarationCancelled(msg.sender, operatorId);
    }

    function reduceOperatorFee(uint64 operatorId, uint256 fee) external {
        StorageData storage s = SSVStorage.load();
        Operator memory operator = s.operators[operatorId];
        operator.checkOwner();
        if (fee != 0 && fee < MINIMAL_OPERATOR_FEE) revert FeeTooLow();
        uint64 shrunkAmount = fee.shrink();
        if (shrunkAmount >= operator.fee) revert FeeIncreaseNotAllowed();
        operator.updateSnapshot();
        operator.fee = shrunkAmount;
        s.operators[operatorId] = operator;
        delete s.operatorFeeChangeRequests[operatorId];
        emit OperatorFeeExecuted(msg.sender, operatorId, block.number, fee);
    }

    function setOperatorsPrivateUnchecked(uint64[] calldata operatorIds) external {
        OperatorLib.updatePrivacyStatus(operatorIds, true, SSVStorage.load());
        emit OperatorPrivacyStatusUpdated(operatorIds, true);
    }

    function setOperatorsPublicUnchecked(uint64[] calldata operatorIds) external {
        OperatorLib.updatePrivacyStatus(operatorIds, false, SSVStorage.load());
        emit OperatorPrivacyStatusUpdated(operatorIds, false);
    }

    function withdrawOperatorEarnings(uint64 operatorId, uint256 amount) external {
        _withdrawOperatorEarnings(operatorId, amount);
    }

    function withdrawAllOperatorEarnings(uint64 operatorId) external {
        _withdrawOperatorEarnings(operatorId, 0);
    }

    function _withdrawOperatorEarnings(uint64 operatorId, uint256 amount) private {
        StorageData storage s = SSVStorage.load();
        Operator memory operator = s.operators[operatorId];
        operator.checkOwner();
        operator.updateSnapshot();

        uint64 shrunkWithdrawn;
        uint64 shrunkAmount = amount.shrink();

        if (amount == 0 && operator.snapshot.balance > 0) {
            shrunkWithdrawn = operator.snapshot.balance;
        } else if (amount > 0 && operator.snapshot.balance >= shrunkAmount) {
            shrunkWithdrawn = shrunkAmount;
        } else {
            revert InsufficientBalance();
        }

        operator.snapshot.balance -= shrunkWithdrawn;
        s.operators[operatorId] = operator;
        _transferOperatorBalanceUnsafe(operatorId, shrunkWithdrawn.expand());
    }

    function _transferOperatorBalanceUnsafe(uint64 operatorId, uint256 amount) private {
        CoreLib.transferBalance(msg.sender, amount);
        emit OperatorWithdrawn(msg.sender, operatorId, amount);
    }

    // Events
    event OperatorAdded(uint64 indexed operatorId, address indexed owner, bytes publicKey, uint256 fee);
    event OperatorRemoved(uint64 indexed operatorId);
    event OperatorFeeDeclared(address indexed owner, uint64 indexed operatorId, uint256 blockNumber, uint256 fee);
    event OperatorFeeExecuted(address indexed owner, uint64 indexed operatorId, uint256 blockNumber, uint256 fee);
    event OperatorFeeDeclarationCancelled(address indexed owner, uint64 indexed operatorId);
    event OperatorWithdrawn(address indexed owner, uint64 indexed operatorId, uint256 value);
    event OperatorPrivacyStatusUpdated(uint64[] operatorIds, bool toPrivate);
}
