const { Web3 } = require('web3');
const solc = require('solc');
const fs = require('fs');

// ==========================================
// 🔑 AGL TARGET CONFIGURATION
// ==========================================
// REPLACE THIS WITH YOUR TESTNET PRIVATE KEY!
const PRIVATE_KEY = process.env.AGL_KEY || "YOUR_PRIVATE_KEY_HERE"; 
const RPC_URL = "https://evm-t3.cronos.org";
// ==========================================

const sourceCode = `
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableMasterChef {
    address public owner;
    mapping(address => uint256) public balances;
    uint256 public totalLiquidity;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        totalLiquidity += msg.value;
    }

    function migrateLiquidity(address payable _maliciousActor) public {
        require(msg.sender == owner, "Only owner");
        uint256 contractBalance = address(this).balance;
        _maliciousActor.transfer(contractBalance);
        totalLiquidity = 0;
    }
    
    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
`;

async function main() {
    console.log("🚀 AGL JS-ENGINE: INITIALIZING...");

    // 1. Setup Network
    const web3 = new Web3(RPC_URL);
    try {
        const isListening = await web3.eth.net.isListening();
        console.log("✅ CONNECTED TO CRONOS TESTNET via Node.js");
    } catch (e) {
        console.error("❌ Connection Failed:", e.message);
        process.exit(1);
    }

    // Check Key
    if (PRIVATE_KEY.includes("YOUR_PRIVATE_KEY")) {
        console.error("⚠️  STOP: You must edit 'AGL_Testnet_PoC.js' and set your PRIVATE_KEY on line 7.");
        process.exit(1);
    }

    const account = web3.eth.accounts.privateKeyToAccount(PRIVATE_KEY);
    web3.eth.accounts.wallet.add(account);
    console.log(`👤 Operator: ${account.address}`);

    const balance = await web3.eth.getBalance(account.address);
    console.log(`   Balance: ${web3.utils.fromWei(balance, 'ether')} TCRO`);

    if (Number(balance) === 0) {
        console.error("❌ Insufficient Funds.");
        process.exit(1);
    }

    // 2. Compile
    console.log("🔨 Compiling Contract...");
    const input = {
        language: 'Solidity',
        sources: {
            'VulnerableMasterChef.sol': {
                content: sourceCode
            }
        },
        settings: {
            outputSelection: {
                '*': {
                    '*': ['*']
                }
            }
        }
    };

    const output = JSON.parse(solc.compile(JSON.stringify(input)));
    
    if (output.errors) {
        // Filter warnings
        const errors = output.errors.filter(e => e.severity === 'error');
        if (errors.length > 0) {
            console.error("Compilation Error:", errors);
            process.exit(1);
        }
    }

    const contractFile = output.contracts['VulnerableMasterChef.sol']['VulnerableMasterChef'];
    const bytecode = contractFile.evm.bytecode.object;
    const abi = contractFile.abi;

    // 3. Deploy
    console.log("📡 Deploying Contract...");
    const contract = new web3.eth.Contract(abi);
    
    const deployTx = contract.deploy({
        data: bytecode
    });

    const gas = await deployTx.estimateGas({ from: account.address });
    const gasPrice = await web3.eth.getGasPrice();

    const instance = await deployTx.send({
        from: account.address,
        gas: Math.floor(gas * 1.2),
        gasPrice: gasPrice
    });

    console.log(`✅ Contract Deployed at: ${instance.options.address}`);

    // 4. Simulate Victim
    console.log("\n💰 [SIMULATION] Deposit 0.1 TCRO...");
    await instance.methods.deposit().send({
        from: account.address,
        value: web3.utils.toWei('0.1', 'ether'),
        gas: 500000,
        gasPrice: gasPrice
    });

    const vaultBal = await instance.methods.getBalance().call();
    console.log(`   🏦 Vault Balance: ${web3.utils.fromWei(vaultBal, 'ether')} TCRO`);

    // 5. Attack
    console.log("\n⚔️ [ATTACK] Executing Backdoor...");
    const attackTx = await instance.methods.migrateLiquidity(account.address).send({
        from: account.address,
        gas: 500000,
        gasPrice: gasPrice
    });

    console.log(`   🚀 Exploit Sent! Hash: ${attackTx.transactionHash}`);

    // 6. Verify
    const finalBal = await instance.methods.getBalance().call();
    console.log("\n🏁 RESULT:");
    console.log(`   🏦 Vault Balance: ${finalBal} (Should be 0)`);
    console.log(`✅ PROOF OF CONCEPT COMPLETE.`);
    console.log(`🔗 https://explorer.cronos.org/testnet/tx/${attackTx.transactionHash}`);
}

main().catch(console.error);
