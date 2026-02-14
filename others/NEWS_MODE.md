# News Mode Integration - Documentation

## Overview

News Mode is a new sentiment analysis mode that fetches and analyzes cryptocurrency news articles from NewsAPI with configurable time intervals. The system collects news over a specified period and outputs the averaged sentiment score.

## Features

### Time Intervals
- **30s** - 30 seconds (ultra-fast monitoring)
- **1min** - 1 minute (quick updates)
- **2min** - 2 minutes
- **5min** - 5 minutes
- **10min** - 10 minutes
- **30min** - 30 minutes
- **1hr** - 1 hour (comprehensive analysis)

### How It Works

1. **Collection Phase**: News articles are fetched from NewsAPI covering crypto topics (Bitcoin, Ethereum, cryptocurrency, blockchain, DeFi)
2. **Interval Wait**: System waits for the specified interval period
3. **Analysis Phase**: All collected articles are analyzed for sentiment
4. **Averaging**: Sentiment scores are averaged and output
5. **Repeat**: Process repeats continuously until stopped

## API Endpoints

### 1. Start/Stop News Mode
```http
POST /api/news/control
Content-Type: application/json

{
  "action": "start",           // "start" or "stop"
  "interval": "1min",          // 30s, 1min, 2min, 5min, 10min, 30min, 1hr
  "query": "bitcoin ethereum"  // optional custom search query
}
```

**Response (Start)**:
```json
{
  "message": "News mode started with 1min interval",
  "interval": "1min",
  "interval_seconds": 60,
  "active": true
}
```

**Response (Stop)**:
```json
{
  "message": "News mode stopped",
  "active": false
}
```

### 2. Manual News Analysis (Single Fetch)
```http
POST /api/analyze
Content-Type: application/json

{
  "mode": "news",
  "interval": "5min",         // lookback period
  "query": "bitcoin"          // optional
}
```

**Response**:
```json
{
  "message": "Analysis complete.",
  "score": 67.5,
  "classification": "Bullish",
  "timestamp": "2026-02-14T10:30:00Z",
  "source": "News (5min)",
  "mode": "news",
  "interval": "5min"
}
```

### 3. Get Latest Score
```http
GET /api/score?mode=news
```

**Response**:
```json
{
  "score": 67.5,
  "classification": "Bullish",
  "timestamp": "2026-02-14T10:30:00Z",
  "sample_size": 15,
  "raw_score": 68.2,
  "source": "News (1min)",
  "interval": "1min",
  "nlp_engine": "finbert",
  "mode": "news",
  "highest_tweet": {
    "text": "Bitcoin reaches new all-time high...",
    "score": 95.5,
    "label": "positive",
    "confidence": 0.98
  },
  "lowest_tweet": {
    "text": "Crypto market faces regulatory concerns...",
    "score": 32.1,
    "label": "negative",
    "confidence": 0.87
  }
}
```

### 4. Get History
```http
GET /api/history?mode=news
```

**Response**:
```json
{
  "history": [
    {
      "score": 65.3,
      "classification": "Bullish",
      "timestamp": "2026-02-14T10:00:00Z",
      "sample_size": 12,
      "raw_score": 66.1,
      "source": "News (1min)",
      "interval": "1min"
    },
    ...
  ],
  "mode": "news"
}
```

### 5. Check Configuration
```http
GET /api/settings
```

**Response**:
```json
{
  "neynar_configured": true,
  "news_configured": true,
  "available_modes": ["test", "live", "news"],
  "test_datasets": {...},
  "news_intervals": {
    "30s": 30,
    "1min": 60,
    "2min": 120,
    "5min": 300,
    "10min": 600,
    "30min": 1800,
    "1hr": 3600
  },
  "news_mode_active": true,
  "news_current_interval": "1min",
  "nlp_engine": "finbert"
}
```

## Setup

### 1. Add News API Key
Add to `.env` file:
```bash
NEWS_API_KEY=your_news_api_key_here
```

Get your key from: https://newsapi.org

### 2. Start Server
```bash
.\myenv\Scripts\Activate.ps1
python app.py
```

### 3. Test News Mode
```bash
python test_news_mode.py
```

## Usage Examples

### Example 1: Quick Monitoring (30s intervals)
```bash
curl -X POST http://localhost:8000/api/news/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start", "interval": "30s"}'
```

### Example 2: Hourly Analysis
```bash
curl -X POST http://localhost:8000/api/news/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start", "interval": "1hr"}'
```

### Example 3: Custom Query (Bitcoin only)
```bash
curl -X POST http://localhost:8000/api/news/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start", "interval": "5min", "query": "bitcoin"}'
```

### Example 4: Get Current Sentiment
```bash
curl http://localhost:8000/api/score?mode=news
```

### Example 5: Stop News Mode
```bash
curl -X POST http://localhost:8000/api/news/control \
  -H "Content-Type: application/json" \
  -d '{"action": "stop"}'
```

## Architecture

```
NewsAPI → news_data.py → sentiment.py (FinBERT) → vibe_score.py → app.py (FastAPI)
   ↓
Time Intervals: 30s, 1min, 2min, 5min, 10min, 30min, 1hr
   ↓
Background Task (asyncio) collects news continuously
   ↓
After each interval: Analyze sentiment & output average score
   ↓
Store in news_history for tracking
```

## Integration with Live Mode

News Mode complements the existing Farcaster Live Mode:

- **Live Mode**: Real-time social media sentiment (Twitter-like)
- **News Mode**: Professional news outlet sentiment
- **Test Mode**: Historical dataset analysis

All three modes can be used together to get a comprehensive market sentiment picture.

## Rate Limits

- **NewsAPI Free Tier**: 100 requests/day
- **Recommended Intervals**: 5min or higher for continuous monitoring
- **Shorter Intervals** (30s, 1min): Best for short-term monitoring sessions

## Benefits

✅ **Real-time news tracking**: Stay updated with latest crypto news  
✅ **Averaged sentiment**: More stable than single-article analysis  
✅ **Configurable intervals**: Match your monitoring needs  
✅ **Historical tracking**: Build sentiment trend data  
✅ **Professional sources**: News outlets vs social media  
✅ **Automated collection**: Background task handles everything  

## Next Steps

1. **Frontend Integration**: Add news mode UI controls to dashboard
2. **Chart Visualization**: Display news sentiment trends
3. **Combined Analysis**: Merge news + social sentiment
4. **Alerting**: Notify on significant sentiment changes
5. **Export Data**: Save historical news sentiment data
