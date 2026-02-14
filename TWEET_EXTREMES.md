# 🔥 Highest & Lowest Sentiment Tweets Display - SenTrack

## ✅ Feature Overview

The dashboard now displays the **highest and lowest sentiment tweets** from each analysis batch, complete with their sentiment scores and confidence levels.

## 📊 What You'll See

### Two New Cards

Located between the sentiment chart and score history:

**1. 🔥 Most Bullish Tweet (Left Card)**

- Green border and background
- Displays the tweet with the highest sentiment score
- Shows sentiment label badge (POSITIVE/NEUTRAL/NEGATIVE)
- Large green score number
- Full tweet text (truncated if over 200 characters)
- Confidence percentage

**2. ❄️ Most Bearish Tweet (Right Card)**

- Red border and background
- Displays the tweet with the lowest sentiment score
- Shows sentiment label badge
- Large red score number
- Full tweet text (truncated if over 200 characters)
- Confidence percentage

## 🎯 Example Display

```
┌──────────────────────────────┬──────────────────────────────┐
│ 🔥 Most Bullish Tweet        │ ❄️ Most Bearish Tweet        │
├──────────────────────────────┼──────────────────────────────┤
│ [POSITIVE]          Score: 95.2│ [NEGATIVE]          Score: 12.8│
│                              │                              │
│ "Bitcoin just broke $50k!    │ "Terrible dump today, lost   │
│  This is incredibly bullish  │  everything. Worst day ever."│
│  for crypto!"                │                              │
│                              │                              │
│ Confidence: 98%              │ Confidence: 92%              │
└──────────────────────────────┴──────────────────────────────┘
```

## 🔢 How Scores Are Calculated

The sentiment score is converted to a 0-100 scale:

- **Positive tweets**: `50 + (confidence × 50)` = **50-100**
- **Negative tweets**: `50 - (confidence × 50)` = **0-50**
- **Neutral tweets**: **50** (baseline)

### Example:

- **Positive with 90% confidence** = 50 + (0.9 × 50) = **95.0**
- **Negative with 80% confidence** = 50 - (0.8 × 50) = **10.0**

## 🎨 Visual Design

### Highest Tweet Card

- **Border**: 3px solid green (#22c55e)
- **Background**: Light green tint
- **Score Color**: Bold green
- **Sentiment Badge**: Color-coded (green/red/yellow)

### Lowest Tweet Card

- **Border**: 3px solid red (#ef4444)
- **Background**: Light red tint
- **Score Color**: Bold red
- **Sentiment Badge**: Color-coded (green/red/yellow)

## 📱 Layout

```
Main Dashboard
├── Top Stats (Score, Classification, Sample Size)
├── ── Sentiment Trend Chart ──────────────
├── ┌──────────────┬──────────────┐
│   │ 🔥 Highest   │ ❄️ Lowest     │  ← NEW!
│   └──────────────┴──────────────┘
└── Score History (Timeline)
```

## 💡 Use Cases

1. **Quick Insight** - Instantly see what's driving the extreme sentiments
2. **Spot Trends** - Identify what makes tweets bullish vs bearish
3. **Dataset Quality** - Verify that the analysis is working on real data
4. **Demo Value** - Show actual tweets being processed in real-time

## 🚀 How It Updates

1. **Run Analysis** - Click "Run Test Analysis"
2. **Backend Processing** - Analyzes 128 tweets from Kaggle
3. **Find Extremes** - Identifies highest and lowest scoring tweets
4. **Update UI** - Both cards populate automatically
5. **Persist** - Tweets from the latest run stay visible

## 📊 What Happens When...

### No Analysis Run Yet

- Both cards show placeholder text
- "Run an analysis to see the highest/lowest sentiment tweet"

### After Analysis

- Both cards immediately populate
- Shows real tweet text from the batch
- Scores and badges update

### Multiple Runs

- Cards always show extremes from the **latest run**
- Previous extremes are not stored (only current)

## 🎯 Perfect for Your Demo

- **Shows Real Data** - Actual tweets from Kaggle datasets
- **Clear Comparison** - Side-by-side bullish vs bearish
- **Professional Look** - Clean, modern card design
- **Instant Feedback** - Updates immediately after analysis

The highest and lowest tweets give you instant insight into what's driving sentiment extremes in your dataset! 🔥❄️
