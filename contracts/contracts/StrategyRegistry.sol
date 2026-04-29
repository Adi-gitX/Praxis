// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "@openzeppelin/contracts/access/Ownable.sol";

/// @title StrategyRegistry
/// @notice On-chain whitelist of approved strategy adapters. Each strategy is
///         registered with its own circuit-breaker flag. The off-chain agent
///         queries this registry pre-trade and refuses to route through any
///         strategy that is unregistered or tripped.
contract StrategyRegistry is Ownable {
    struct Strategy {
        bytes32 nameHash;
        address adapter;
        bool active;
        bool tripped;
        uint256 maxNotional;
    }

    mapping(uint256 => Strategy) private _strategies;
    uint256 public nextStrategyId = 1;

    event StrategyRegistered(uint256 indexed id, bytes32 nameHash, address adapter, uint256 maxNotional);
    event StrategyActivated(uint256 indexed id, bool active);
    event CircuitBreakerTripped(uint256 indexed id, address indexed by, string reason);
    event CircuitBreakerReset(uint256 indexed id);
    event MaxNotionalUpdated(uint256 indexed id, uint256 newMaxNotional);

    error StrategyNotFound(uint256 id);
    error CircuitBreakerActive(uint256 id);

    constructor() Ownable(msg.sender) {}

    function register(bytes32 nameHash, address adapter, uint256 maxNotional)
        external
        onlyOwner
        returns (uint256 id)
    {
        id = nextStrategyId++;
        _strategies[id] = Strategy({
            nameHash: nameHash,
            adapter: adapter,
            active: true,
            tripped: false,
            maxNotional: maxNotional
        });
        emit StrategyRegistered(id, nameHash, adapter, maxNotional);
    }

    function setActive(uint256 id, bool active) external onlyOwner {
        if (_strategies[id].adapter == address(0)) revert StrategyNotFound(id);
        _strategies[id].active = active;
        emit StrategyActivated(id, active);
    }

    function setMaxNotional(uint256 id, uint256 newMax) external onlyOwner {
        if (_strategies[id].adapter == address(0)) revert StrategyNotFound(id);
        _strategies[id].maxNotional = newMax;
        emit MaxNotionalUpdated(id, newMax);
    }

    /// @notice Anyone with a sufficient stake/role can trip the breaker; in
    /// this minimal scaffold we restrict to owner. Production would extend to
    /// a guardian multisig.
    function trip(uint256 id, string calldata reason) external onlyOwner {
        if (_strategies[id].adapter == address(0)) revert StrategyNotFound(id);
        _strategies[id].tripped = true;
        emit CircuitBreakerTripped(id, msg.sender, reason);
    }

    function resetBreaker(uint256 id) external onlyOwner {
        if (_strategies[id].adapter == address(0)) revert StrategyNotFound(id);
        _strategies[id].tripped = false;
        emit CircuitBreakerReset(id);
    }

    function isApproved(uint256 id, uint256 notional) external view returns (bool) {
        Strategy storage s = _strategies[id];
        return s.active && !s.tripped && notional <= s.maxNotional;
    }

    function get(uint256 id) external view returns (Strategy memory) {
        if (_strategies[id].adapter == address(0)) revert StrategyNotFound(id);
        return _strategies[id];
    }
}
