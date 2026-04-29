// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "@openzeppelin/contracts/access/AccessControl.sol";

/// @title EmergencyPause
/// @notice Killswitch with a one-way fast halt and a timelocked unhalt.
///         Anyone with GUARDIAN_ROLE can halt instantly. Unhalting requires
///         the admin and only takes effect after `unhaltDelay`. Vault and
///         downstream contracts read `isHalted()` and freeze writes.
contract EmergencyPause is AccessControl {
    bytes32 public constant GUARDIAN_ROLE = keccak256("GUARDIAN_ROLE");

    bool public halted;
    uint256 public unhaltDelay;
    uint256 public unhaltScheduledAt;

    event Halted(address indexed by, string reason);
    event UnhaltScheduled(address indexed by, uint256 effectiveAt);
    event Unhalted(address indexed by);
    event UnhaltDelayUpdated(uint256 newDelay);

    error AlreadyHalted();
    error NotHalted();
    error UnhaltNotScheduled();
    error UnhaltNotReady(uint256 readyAt);

    constructor(address admin, address guardian, uint256 unhaltDelay_) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(GUARDIAN_ROLE, guardian);
        unhaltDelay = unhaltDelay_;
    }

    function isHalted() external view returns (bool) {
        return halted;
    }

    function halt(string calldata reason) external onlyRole(GUARDIAN_ROLE) {
        if (halted) revert AlreadyHalted();
        halted = true;
        emit Halted(msg.sender, reason);
    }

    function scheduleUnhalt() external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (!halted) revert NotHalted();
        unhaltScheduledAt = block.timestamp + unhaltDelay;
        emit UnhaltScheduled(msg.sender, unhaltScheduledAt);
    }

    function unhalt() external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (!halted) revert NotHalted();
        if (unhaltScheduledAt == 0) revert UnhaltNotScheduled();
        if (block.timestamp < unhaltScheduledAt) revert UnhaltNotReady(unhaltScheduledAt);
        halted = false;
        unhaltScheduledAt = 0;
        emit Unhalted(msg.sender);
    }

    function setUnhaltDelay(uint256 newDelay) external onlyRole(DEFAULT_ADMIN_ROLE) {
        unhaltDelay = newDelay;
        emit UnhaltDelayUpdated(newDelay);
    }
}
