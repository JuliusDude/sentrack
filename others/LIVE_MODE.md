# ⚡ Live Mode - Real-Time Sentiment Analysis

## 🌟 Feature Overview

Live Mode connects your SenTrack dashboard to the **Farcaster** social network via the **Neynar API** to analyze real-time conversations about crypto.

Instead of using static datasets, you are now analyzing what people are saying **right now**.

## 🚀 How to Use

1. **Switch to Live Mode**
   - Click the **⚡ Live Mode** button in the top control bar.
   - The button will turn green and the indicator will glow.

2. **Enter a Custom Query (Optional)**
   - A search bar will appear below the mode toggle.
   - **Default**: If left empty, it searches for general crypto terms (`bitcoin`, `ethereum`, `defi`, etc).
   - **Custom**: Type any term to analyze specific sentiment!
     - Examples: `solana`, `base`, `memecoins`, `vitalik`, `etf`

3. **Run Analysis**
   - Click **⚡ Run Live Analysis**.
   - The system will fetch the latest ~100 casts from Farcaster matching your query.
   - Sentiment analysis is performed on the fly.

4. **View Results**
   - **Score**: See the real-time vibe score.
   - **Chart**: Watch the trend update with every run.
   - **Tweets**: See the **actual casts** that are driving the bullish/bearish sentiment in the "Highest/Lowest" cards.

## 🔧 Configuration

Live Mode requires a **Neynar API Key**.

- Check your `.env` file:
  ```env
  NEYNAR_API_KEY=your_api_key_here
  ```
- If the key is missing, the Live Mode button will be locked/disabled.

## 💡 Pro Tips

- **Trend Spotting**: Run analysis on "bitcoin" every 5 minutes to track sentiment shifts during volatility.
- **Alpha Hunting**: Search for specific new tokens to see if the community vibe is bullish before investing.
- **Compare**: Run a test analysis on historical data, then switch to Live Mode to see how today compares to the past.

## ⚠️ Note

- Live calls use your Neynar API quota.
- Analysis might take a few seconds depending on the volume of casts found.
