// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./Vault.sol";
import "./VaultToken.sol";

/**
 * @title VaultFactory - مصنع الخزنات
 * @notice ينشئ ويدير عدة خزنات
 */
contract VaultFactory {
    address public admin;
    Vault[] public vaults;
    mapping(address => address[]) public userVaults;
    
    event VaultCreated(address indexed vault, address indexed token, address indexed creator);

    constructor() {
        admin = msg.sender;
    }

    /**
     * @notice إنشاء خزنة جديدة مع توكن مخصص
     */
    function createVault(
        string memory tokenName,
        string memory tokenSymbol,
        uint256 initialSupply
    ) external returns (address) {
        VaultToken token = new VaultToken(tokenName, tokenSymbol, initialSupply);
        Vault vault = new Vault(address(token));
        
        vaults.push(vault);
        userVaults[msg.sender].push(address(vault));
        
        emit VaultCreated(address(vault), address(token), msg.sender);
        return address(vault);
    }

    /**
     * @notice عدد الخزنات
     */
    function vaultCount() external view returns (uint256) {
        return vaults.length;
    }

    /**
     * @notice إيقاف خزنة — ⚠️ بدون فحص الملكية!
     * أي شخص يمكنه استدعاء هذه الدالة
     */
    function pauseVault(uint256 index) external {
        // ⚠️ لا يوجد فحص صلاحيات
        Vault vault = vaults[index];
        // ⚠️ delegatecall خطير — يمكن أن يفسد storage
        (bool success, ) = address(vault).delegatecall(
            abi.encodeWithSignature("pause()")
        );
        require(success, "Pause failed");
    }

    /**
     * @notice سحب الرسوم — ⚠️ unchecked call
     */
    function collectFees(address payable to) external {
        require(msg.sender == admin, "Not admin");
        to.call{value: address(this).balance}("");
        // ⚠️ لا يتحقق من نجاح التحويل
    }

    /**
     * @notice تنفيذ عملية مخصصة — ⚠️ delegatecall لعنوان خارجي!
     */
    function execute(address target, bytes calldata data) external {
        require(msg.sender == admin, "Not admin");
        (bool success, ) = target.delegatecall(data);
        require(success, "Execution failed");
    }

    receive() external payable {}
}
