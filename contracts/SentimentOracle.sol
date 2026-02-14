// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CommunitySentimentOracle {

    // ================================
    // STRUCT
    // ================================

    struct Sentiment {
        uint256 score;        // Sentiment score (0-100)
        uint256 timestamp;    // Block timestamp
        address contributor;  // Wallet address
    }

    // ================================
    // STATE VARIABLES
    // ================================

    Sentiment[] private sentiments;

    // Anti-spam: 1 submission per minute per wallet
    mapping(address => uint256) public lastSubmissionTime;

    uint256 public constant MIN_INTERVAL = 60; // 60 seconds

    // ================================
    // EVENTS (Frontend will use this for chart)
    // ================================

    event SentimentSubmitted(
        uint256 indexed score,
        uint256 indexed timestamp,
        address indexed contributor
    );

    // ================================
    // MAIN FUNCTION
    // ================================

    function submitSentiment(uint256 _score) external {

        require(_score <= 100, "Score must be between 0 and 100");

        require(
            block.timestamp >= lastSubmissionTime[msg.sender] + MIN_INTERVAL,
            "Wait before submitting again"
        );

        lastSubmissionTime[msg.sender] = block.timestamp;

        Sentiment memory newSentiment = Sentiment({
            score: _score,
            timestamp: block.timestamp,
            contributor: msg.sender
        });

        sentiments.push(newSentiment);

        emit SentimentSubmitted(
            _score,
            block.timestamp,
            msg.sender
        );
    }

    // ================================
    // VIEW FUNCTIONS
    // ================================

    function getSentiment(uint256 index) external view returns (
        uint256 score,
        uint256 timestamp,
        address contributor
    ) {
        Sentiment memory s = sentiments[index];
        return (s.score, s.timestamp, s.contributor);
    }

    function getTotalSubmissions() external view returns (uint256) {
        return sentiments.length;
    }
}