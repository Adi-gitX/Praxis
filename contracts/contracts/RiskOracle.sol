// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "@openzeppelin/contracts/access/AccessControl.sol";

/// @title RiskOracle
/// @notice Read-only surface for the agent's current risk posture. The
///         off-chain agent pushes signed metrics on each rebalance; depositors
///         and integrators read them on-chain. Designed as a passive oracle —
///         downstream contracts can refuse to interact with the vault when
///         metrics breach their thresholds.
contract RiskOracle is AccessControl {
    bytes32 public constant WRITER_ROLE = keccak256("WRITER_ROLE");

    enum Regime { Trending, Ranging, HighVol, Crisis }

    struct Snapshot {
        uint64 ts;
        uint16 drawdownBps;     // basis points; 10000 = 100%
        uint16 grossLeverageBps;
        int16  netLeverageBps;   // signed (negative => net short)
        Regime regime;
    }

    Snapshot public latest;

    event SnapshotPushed(
        uint64 ts,
        uint16 drawdownBps,
        uint16 grossLeverageBps,
        int16 netLeverageBps,
        Regime regime
    );

    error InvalidTimestamp();

    constructor(address admin, address writer) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(WRITER_ROLE, writer);
    }

    function push(Snapshot calldata s) external onlyRole(WRITER_ROLE) {
        if (s.ts < latest.ts) revert InvalidTimestamp();
        latest = s;
        emit SnapshotPushed(s.ts, s.drawdownBps, s.grossLeverageBps, s.netLeverageBps, s.regime);
    }

    function isStale(uint256 maxAgeSeconds) external view returns (bool) {
        return block.timestamp > uint256(latest.ts) + maxAgeSeconds;
    }
}
