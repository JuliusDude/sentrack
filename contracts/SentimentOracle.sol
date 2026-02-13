// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SentimentOracle
 * @notice On-chain oracle for Community Vibe sentiment scores.
 *         Designed for low gas cost: stores only latest state,
 *         uses events for immutable history.
 */
contract SentimentOracle {
    address public owner;
    uint256 public latestScore;
    uint256 public lastUpdated;

    event ScoreUpdated(
        uint256 indexed score,
        uint256 timestamp,
        address indexed updatedBy
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
        latestScore = 50; // Default neutral
        lastUpdated = block.timestamp;
    }

    /**
     * @notice Update the sentiment score. Owner only.
     * @param _score Vibe score between 0 and 100.
     */
    function updateScore(uint256 _score) external onlyOwner {
        require(_score <= 100, "Score must be 0-100");
        latestScore = _score;
        lastUpdated = block.timestamp;
        emit ScoreUpdated(_score, block.timestamp, msg.sender);
    }

    /**
     * @notice Read the latest sentiment score.
     */
    function getScore() external view returns (uint256 score, uint256 updated) {
        return (latestScore, lastUpdated);
    }

    /**
     * @notice Transfer ownership to a new address.
     */
    function transferOwnership(address _newOwner) external onlyOwner {
        require(_newOwner != address(0), "Invalid address");
        owner = _newOwner;
    }
}
