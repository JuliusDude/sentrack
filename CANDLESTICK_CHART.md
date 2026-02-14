# 📊 Candlestick Chart Implementation - SenTrack

## ✅ Stock Market-Style Candlestick Chart Added

### What Is a Candlestick Chart?

A candlestick chart is a financial visualization that shows price movements over time. Each "candle" displays four key values:

```
    │      High (top of wick)
    ┌─┐
    │█│    Body (Open to Close)
    └─┘
    │      Low (bottom of wick)
```

### How It Works for Sentiment Analysis

**Each Candle Represents One Analysis Run:**

- **Open**: Previous sentiment score (where the run started from)
- **Close**: Current sentiment score (where the run ended)
- **High**: Maximum sentiment (highest of smoothed/raw scores)
- **Low**: Minimum sentiment (lowest of smoothed/raw scores)

**Color Coding (Stock Market Style):**

- 🟢 **Green Candle** = Score Increased (Close > Open) - Bullish Delta
- 🔴 **Red Candle** = Score Decreased (Close < Open) - Bearish Delta

### Visual Example

```
Score
100 ┤
 80 ┤     🟢
 60 ┤   🔴│🟢
 40 ┤   │ │ 🔴
 20 ┤ 🟢└─┘ │
  0 ┤─┴─────┴─
     1  2  3  4  Run #
```

- **Run 1**: Green candle (score went up)
- **Run 2**: Red candle with long wick (volatility, ended lower)
- **Run 3**: Green candle (recovery)
- **Run 4**: Red candle (decline)

### What You'll See

**On the Dashboard:**

1. **Candlesticks** - Each analysis run appears as a candle
2. **Color-coded instantly** - Green = improvement, Red = decline
3. **Hover for details:**
   - Open: Starting score
   - Close: Ending score
   - High/Low: Score range
   - Delta: Exact change (+/-X.XX)
   - Classification: Bullish/Neutral/Bearish

### Why This Is Perfect for Your Demo

✅ **Stock Market Familiar** - Everyone recognizes this chart style
✅ **Delta Changes Visible** - Red/green immediately shows direction
✅ **Volatility Visible** - Long wicks show when raw scores varied widely
✅ **Professional Look** - Looks like real trading software
✅ **Real-time Updates** - New candles appear as you run more analyses

### Example Tooltip on Hover:

```
Run #3
Open: 49.55
Close: 47.19
High: 50.20
Low: 45.80
Delta: -2.36
Classification: Neutral
```

### Technical Implementation

- **Library**: Chart.js with chartjs-chart-financial extension
- **Real-time**: Updates immediately after each analysis
- **Responsive**: Works on all screen sizes
- **Color Scheme**: Matches stock market conventions (green/red)

### How to Use

1. **Refresh your browser** (F5) to load the new chart library
2. **Run multiple analyses** with Kaggle datasets
3. **Watch the candlesticks form** - each run adds a new candle
4. **Compare deltas** - See which datasets produce more volatility

The candlestick chart makes it instantly clear whether sentiment is trending up (more green candles) or down (more red candles), just like in stock trading! 📈📉
