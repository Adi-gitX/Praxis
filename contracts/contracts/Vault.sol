// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

import "./EmergencyPause.sol";

/// @title PraxisVault
/// @notice ERC-4626 vault. Depositors mint shares; the agent operator
///         executes strategies via `agent` calls. The vault never makes
///         autonomous decisions — the off-chain agent assembles trades and
///         the operator submits them, gated by the timelocked emergency-pause.
contract PraxisVault is ERC4626, Ownable, Pausable, ReentrancyGuard {
    address public agent;
    EmergencyPause public immutable emergency;

    event AgentUpdated(address indexed previousAgent, address indexed newAgent);
    event AgentCall(address indexed target, uint256 value, bytes data, bytes result);

    error NotAgent();
    error EmergencyHalted();

    modifier onlyAgent() {
        if (msg.sender != agent) revert NotAgent();
        _;
    }

    modifier whenNotEmergencyHalted() {
        if (emergency.isHalted()) revert EmergencyHalted();
        _;
    }

    constructor(
        IERC20 asset_,
        string memory name_,
        string memory symbol_,
        address initialAgent,
        EmergencyPause emergency_
    ) ERC4626(asset_) ERC20(name_, symbol_) Ownable(msg.sender) {
        agent = initialAgent;
        emergency = emergency_;
        emit AgentUpdated(address(0), initialAgent);
    }

    function setAgent(address newAgent) external onlyOwner {
        emit AgentUpdated(agent, newAgent);
        agent = newAgent;
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function deposit(uint256 assets, address receiver)
        public
        override
        whenNotPaused
        whenNotEmergencyHalted
        nonReentrant
        returns (uint256)
    {
        return super.deposit(assets, receiver);
    }

    function mint(uint256 shares, address receiver)
        public
        override
        whenNotPaused
        whenNotEmergencyHalted
        nonReentrant
        returns (uint256)
    {
        return super.mint(shares, receiver);
    }

    function withdraw(uint256 assets, address receiver, address owner_)
        public
        override
        whenNotEmergencyHalted
        nonReentrant
        returns (uint256)
    {
        return super.withdraw(assets, receiver, owner_);
    }

    function redeem(uint256 shares, address receiver, address owner_)
        public
        override
        whenNotEmergencyHalted
        nonReentrant
        returns (uint256)
    {
        return super.redeem(shares, receiver, owner_);
    }

    /// @notice Generic agent call — used by the off-chain operator to route
    /// vault funds through approved DEX adapters. Owner whitelists targets via
    /// the StrategyRegistry; this contract trusts the agent EOA to only call
    /// registry-approved addresses. The on-chain check lives in the caller's
    /// pre-tx simulation; we deliberately keep this contract minimal.
    function agentCall(address target, uint256 value, bytes calldata data)
        external
        onlyAgent
        whenNotPaused
        whenNotEmergencyHalted
        nonReentrant
        returns (bytes memory result)
    {
        (bool ok, bytes memory ret) = target.call{value: value}(data);
        require(ok, "agent call failed");
        emit AgentCall(target, value, data, ret);
        return ret;
    }
}
