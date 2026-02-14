# 📊 Multi-Chart Type Selector - SenTrack Dashboard

## ✅ Feature Overview

You can now switch between **three different chart types** on the SenTrack dashboard:

1. **📊 Candlestick Chart** (Default) - Stock market style showing deltas
2. **📈 Line Chart** - Classic smooth trend visualization
3. **📊 Bar Chart** - Color-coded bars by sentiment classification

## 🎯 How to Use

### Chart Switcher Buttons

Located in the top-right corner of the "Sentiment Trend" card, you'll see three buttons:

```
┌─────────────────────────────────────────────────┐
│ Sentiment Trend    [📊 Candlestick] [📈 Line] [📊 Bar] │
├─────────────────────────────────────────────────┤
│                                                 │
│              [Chart appears here]               │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Simply click any button to switch chart types instantly!**

## 📊 Chart Type Details

### 1. Candlestick Chart (Default)

**Best for:** Seeing sentiment deltas (changes between runs)

**Features:**

- 🟢 Green candles = Score increased
- 🔴 Red candles = Score decreased
- Shows Open, Close, High, Low for each run
- Wicks show volatility (difference between raw and smoothed)

**Use when:** You want to see if sentiment is trending up or down, just like stock trading

---

### 2. Line Chart

**Best for:** Seeing overall trends over time

**Features:**

- Smooth line showing sentiment progression
- Blue line (Test mode) or Green line (Live mode)
- Dotted gray line shows raw unsmoothed scores
- Filled area under the curve

**Use when:** You want a clean overview of how sentiment evolved across all runs

---

### 3. Bar Chart

**Best for:** Comparing individual run scores

**Features:**

- 🟢 Green bars = Bullish sentiment
- 🔴 Red bars = Bearish sentiment
- 🟡 Yellow bars = Neutral sentiment
- Each bar is color-coded by classification

**Use when:** You want to quickly identify which specific runs were bullish/bearish

## 🔄 Switching Charts

**No data loss** - When you switch chart types:

- All your analysis history is preserved
- Same data, different visualization
- Instant switching (no page reload)
- Active button is highlighted in blue

## 💡 Pro Tips

1. **Start with Candlestick** - Great for first impression, very visual
2. **Switch to Line** - See the overall trend direction clearly
3. **Use Bar** - Identify specific bullish/bearish periods quickly

## 🎨 Visual Comparison

```
CANDLESTICK:          LINE:              BAR:
   🟢                   📈                 🟢|
   │█│                 ╱ ╲               ━━━
   🔴                 ╱   ╲              🔴|
                                        ━━

Shows deltas         Shows trends      Shows categories
```

## 🚀 Quick Example Workflow

1. **Run 3-4 analyses** with different Kaggle datasets
2. **Default view**: Candlestick shows you green/red candles
3. **Click "Line"**: See the smooth trend line
4. **Click "Bar"**: Identify which runs were bullish/bearish
5. **Click "Candlestick"**: Back to default stock-market view

All charts update in real-time as you run more analyses!

## 🎯 Perfect for Your Demo

- **Candlestick**: Grabs attention, looks professional
- **Line**: Shows overall direction clearly
- **Bar**: Easy to explain sentiment classification

Switch between them during your presentation to show different perspectives of the same data! 🎉
