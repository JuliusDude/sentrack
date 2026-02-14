# ⚡ SenTrack — AI-Powered Crypto Sentiment Analysis

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Solidity](https://img.shields.io/badge/Solidity-%23363636.svg?style=for-the-badge&logo=solidity&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=for-the-badge)

**SenTrack** is a sophisticated, multi-modal sentiment analysis platform for the crypto ecosystem. It gauges community "vibe" by analyzing real-time social data and news using advanced NLP models, and optionally publishes these sentiment scores on-chain via a Solidity Oracle.

![SenTrack Dashboard](static/sentiment_dashboard_screenshot.png) <!-- meaningful placeholder if image exists, otherwise generic accessible text -->

---

## 🌟 Key Features

### 1. **Triple-Mode Analysis Engine**

- **⚡ Live Mode (Farcaster)**: Connects to the **Neynar API** to analyze real-time conversations on the Farcaster protocol. Catch the alpha before it trends.
- **📰 News Mode (NewsAPI)**: Fetches and analyzes the latest crypto news articles to gauge market sentiment from media outlets.
- **🧪 Test Mode**: Validates the NLP engine using curated datasets (Kaggle, CSV) to ensure accuracy against known benchmarks.

### 2. **Dual-Core NLP Engine**

- **Primary**: **FinBERT** (ProsusAI/finbert) — A BERT model pre-trained specifically on financial text for high-accuracy market sentiment detection.
- **Fallback**: **VADER** — A rule-based model optimized for social media text, ensuring 100% uptime even on lower-resource environments.

### 3. **⛓️ On-Chain Oracle**

- **Solidity Smart Contract**: A `SentimentOracle` contract that allows vetted publishers to push "Vibe Scores" on-chain.
- **DeFi Integration**: Other dApps can query the `SentimentOracle` to build sentiment-aware trading bots or dynamic NFTs.

### 4. **Interactive Dashboard**

- **Real-Time Data**: Live updating charts using Chart.js.
- **Vibe Score**: A 0-100 aggregated community sentiment metric (0=Extreme Fear, 100=Extreme Greed).

---

## 🛠️ Tech Stack

- **Backend**: Python 3.9+, **FastAPI** (High-performance async API).
- **AI/ML**: **PyTorch**, **Hugging Face Transformers**, **NLTK/VADER**.
- **Smart Contracts**: **Solidity** (v0.8.20), **Hardhat**, **Ethers.js**.
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (Clean, dependency-free dashboard).
- **Data Sources**: Neynar (Farcaster), NewsAPI, KaggleHub.

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Node.js & npm (for smart contracts)
- API Keys:
  - **Neynar API Key** (for Live Mode)
  - **NewsAPI Key** (for News Mode)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sentrack.git
cd sentrack
```

### 2. Backend Setup (Python)

```bash
# Create a virtual environment
python -m venv myenv

# Activate usage
# Windows:
myenv\Scripts\activate
# Mac/Linux:
# source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Smart Contract Setup (Node.js)

```bash
# Install Hardhat and plugins
npm install
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
# API Keys
NEYNAR_API_KEY=your_farcaster_neynar_key
NEWS_API_KEY=your_newsapi_key

# Blockchain (Optional - for deployment)
PRIVATE_KEY=your_wallet_private_key
RPC_URL_AMOY=https://rpc-amoy.polygon.technology/
```

---

## 🏃 Usage

### Start the Application

Run the FastAPI server with live reload:

```bash
uvicorn app:app --reload
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### Deploy Smart Contracts

Deploy the Sentiment Oracle to a testnet (e.g., Polygon Amoy):

```bash
npx hardhat run scripts/deploy.js --network amoy
```

### Running Tests

Run the Python test suite to verify the NLP engine:

```bash
pytest
```

---

## 📂 Project Structure

```text
sentrack/
├── app.py                 # FastAPI Application entry point
├── sentiment.py           # NLP Engine (FinBERT + VADER)
├── vibe_score.py          # Sentiment aggregation logic
├── contracts/             # Solidity Smart Contracts
│   └── SentimentOracle.sol
├── scripts/               # Deployment scripts
│   └── deploy.js
├── static/                # Frontend assets (HTML/CSS/JS)
├── data/                  # Local datasets for Test Mode
└── tests/                 # Python unit tests
```

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.
