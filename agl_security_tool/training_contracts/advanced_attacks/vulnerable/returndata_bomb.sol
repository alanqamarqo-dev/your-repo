// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// VULNERABILITY: Returndata bomb — copies unbounded return data from untrusted callee

contract VulnerableMulticall {
    struct Call {
        address target;
        bytes callData;
    }

    // VULNERABILITY: Captures bytes memory from arbitrary target
    function multicall(Call[] calldata calls)
        external
        returns (bytes[] memory results)
    {
        results = new bytes[](calls.length);
        for (uint i = 0; i < calls.length; i++) {
            // VULNERABILITY: Malicious target can return huge payload
            // causing excessive gas consumption in memory expansion
            (bool success, bytes memory data) = calls[i].target.call(calls[i].callData);
            require(success, "Call failed");
            results[i] = data;
        }
    }

    // VULNERABILITY: Single call with returndata capture
    function forwardCall(address target, bytes calldata payload)
        external
        returns (bytes memory)
    {
        (bool success, bytes memory returnData) = target.call(payload);
        require(success, "Forward failed");
        return returnData;
    }
}
