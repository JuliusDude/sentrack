"""
SenTrack — FastAPI Server
Triple-mode sentiment oracle: Live (Farcaster), News (NewsAPI), & Test (CSV datasets)
Pipeline: data → NLP → vibe score → API → dashboard
"""

import os
import logging
import asyncio
import random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone as dt_timezone

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from data_loader import load_tweets, load_test_tweets, load_kaggle_sample
from live_data import fetch_live_casts, is_configured as neynar_configured
from news_data import fetch_crypto_news, is_configured as news_configured, get_available_intervals, get_interval_seconds
from sentiment import analyze_batch, get_mode
from vibe_score import calculate_vibe

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not found. using manual .env loader.")
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    os.environ[key.strip()] = val.strip()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── In-memory state ──────────────────────────────────────────────
live_history: list[dict] = []
test_history: list[dict] = []

# Live mode automation state
live_automation_active = False
live_automation_interval = "1min"  # default interval
live_collection_buffer: list[dict] = []  # Buffer: [{"text": str, "sentiment": dict, "timestamp": str}]
live_realtime_news: list[dict] = []  # Real-time news feed for Latest News section
live_collection_start: datetime | None = None
live_automation_task: asyncio.Task | None = None
live_last_fetch_time: datetime | None = None

# Contribute scan state
contribute_scan_active = False
contribute_scan_task: asyncio.Task | None = None
contribute_scan_result: dict | None = None
contribute_scan_progress: dict = {"phase": "idle", "articles": 0, "elapsed": 0, "message": ""}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Available test datasets
TEST_DATASETS = {
    "sample": {
        "path": os.path.join(DATA_DIR, "sample_tweets.csv"),
        "label": "Sample Tweets",
        "description": "52 curated crypto tweets (bundled)",
        "type": "file",
    },
    "kaggle_sentiment140": {
        "handle": "kazanova/sentiment140",
        "label": "Sentiment140 (Kaggle)",
        "description": "Random 128 sample from 1.6M tweets",
        "type": "kaggle",
    },
    "kaggle_bitcoin": {
        "handle": "gautamchettiar/bitcoin-sentiment-analysis-twitter-data",
        "label": "Bitcoin Sentiment (Kaggle)",
        "description": "Random 128 sample from Bitcoin tweets",
        "type": "kaggle",
    },
}


# ── Analysis functions ───────────────────────────────────────────

def _run_analysis(texts: list[str], history: list[dict], source: str) -> dict:
    """Run sentiment analysis on texts and store result in history."""
    if not texts:
        raise HTTPException(
            status_code=404, 
            detail="No texts found for analysis. Live mode: Check Neynar API key/status. Test mode: Check dataset."
        )


    logger.info("Analyzing %d texts from '%s'...", len(texts), source)
    sentiments = analyze_batch(texts)
    
    # User requested debug output: Log head of 5 processed tweets with sentiment
    logger.info("--- Batch Preview: %d of %d tweets ---", min(5, len(texts)), len(texts))
    
    if not texts:
         logger.warning("(!) No tweets found. If using Kaggle modes, ensure 'kagglehub' and 'pandas' are installed.")
         
    for i, (txt, sent) in enumerate(zip(texts[:5], sentiments[:5])):
        # Truncate text for cleaner display
        preview = (txt[:75] + '..') if len(txt) > 75 else txt
        logger.info("[%d] %s (%.2f): %s", i+1, sent['label'].upper(), sent['confidence'], preview)
    
    logger.info("-" * 60)

    logger.info("Analyzed %d texts via %s.", len(sentiments), get_mode())
    
    # Find highest and lowest sentiment tweets
    highest_tweet = None
    lowest_tweet = None
    
    if sentiments and texts:
        # Create list of tuples (text, sentiment_score)
        tweet_scores = []
        for txt, sent in zip(texts, sentiments):
            # Convert sentiment to a numeric score (0-100)
            if sent['label'] == 'positive':
                score = 50 + (sent['confidence'] * 50)  # 50-100
            elif sent['label'] == 'negative':
                score = 50 - (sent['confidence'] * 50)  # 0-50
            else:  # neutral
                score = 50
            tweet_scores.append((txt, score, sent))
        
        if tweet_scores:
            # Find max and min
            highest = max(tweet_scores, key=lambda x: x[1])
            lowest = min(tweet_scores, key=lambda x: x[1])
            
            highest_tweet = {
                "text": highest[0],
                "score": round(highest[1], 2),
                "label": highest[2]['label'],
                "confidence": round(highest[2]['confidence'], 2)
            }
            
            lowest_tweet = {
                "text": lowest[0],
                "score": round(lowest[1], 2),
                "label": lowest[2]['label'],
                "confidence": round(lowest[2]['confidence'], 2)
            }

    prev = history[-1]["score"] if history else None
    result = calculate_vibe(sentiments, previous_score=prev)
    result["source"] = source
    
    # Add highest and lowest tweets to result
    result["highest_tweet"] = highest_tweet
    result["lowest_tweet"] = lowest_tweet

    history.append(result)
    logger.info("Vibe score: %.2f (%s)", result["score"], result["classification"])
    return result



def run_live_analysis(interval: str = "1min", query: str | None = None) -> dict:
    """Fetch crypto news and analyze (Live mode uses NewsAPI)."""
    interval_seconds = get_interval_seconds(interval)
    from_time = datetime.utcnow() - timedelta(seconds=interval_seconds)
    
    news = fetch_crypto_news(query=query or "crypto OR bitcoin OR ethereum", from_time=from_time, limit=50)
    
    if not news:
        logger.warning("No news articles found for live mode.")
        prev = live_history[-1]["score"] if live_history else None
        result = calculate_vibe([], previous_score=prev)
        result["source"] = f"Live News ({interval})"
        result["interval"] = interval
        result["message"] = "No news articles found"
        live_history.append(result)
        return result
    
    return _run_analysis(news, live_history, f"Live News ({interval})")


def run_test_analysis(dataset: str = "sample") -> dict:
    """Load test dataset and analyze."""
    ds = TEST_DATASETS.get(dataset)
    if not ds:
        return {"error": f"Unknown dataset: {dataset}"}

    # Handle Kaggle datasets
    if ds.get("type") == "kaggle":
        texts = load_kaggle_sample(ds["handle"], limit=128)
    # Use format-aware loader for non-sample file datasets
    elif dataset == "sample":
        texts = load_tweets(ds["path"])
    else:
        # Fallback for other file-based datasets in the list if any remain
        texts = load_test_tweets(ds["path"])

    return _run_analysis(texts, test_history, ds["label"])


def run_news_analysis(interval: str = "1min", query: str | None = None) -> dict:
    """Fetch news and analyze immediately (single fetch)."""
    interval_seconds = get_interval_seconds(interval)
    from_time = datetime.utcnow() - timedelta(seconds=interval_seconds)
    
    news = fetch_crypto_news(query=query, from_time=from_time) if query else fetch_crypto_news(from_time=from_time)
    
    if not news:
        logger.warning("No news articles found for the given interval.")
        # Return a neutral result instead of error
        prev = news_history[-1]["score"] if news_history else None
        result = calculate_vibe([], previous_score=prev)
        result["source"] = f"News ({interval})"
        result["interval"] = interval
        result["message"] = "No news articles found in this interval"
        news_history.append(result)
        return result
    
    return _run_analysis(news, news_history, f"News ({interval})")


# ── Live Mode Automation Background Task ────────────────────────────────────

async def live_automation_background_task(interval: str, query: str | None = None):
    """
    Background task for Live mode automation.
    1. Continuously fetch news during the interval and store RAW text (no analysis).
    2. When the interval ends, randomly sample 9 articles (8:1 ratio).
    3. Analyse ONLY those 9 articles with FinBERT/VADER.
    4. Average their scores → that becomes the Vibe Score for this interval.
    """
    global live_automation_active, live_collection_buffer, live_realtime_news
    global live_collection_start, live_last_fetch_time

    interval_seconds = get_interval_seconds(interval)
    fetch_frequency = 15  # Fetch new articles every 15 seconds
    SAMPLE_SIZE = 25      # Sample 20-30 articles (target ~25)
    MIN_ARTICLES = 30     # Minimum articles before sampling
    MAX_ARTICLES = 120    # Cap the buffer at this size

    logger.info("═" * 60)
    logger.info(f"LIVE AUTOMATION STARTED  interval={interval} ({interval_seconds}s)")
    logger.info(f"Strategy: collect {MIN_ARTICLES}-{MAX_ARTICLES} news → sample {SAMPLE_SIZE} → analyse → avg score")
    logger.info("═" * 60)

    live_collection_start = datetime.utcnow()
    live_collection_buffer = []   # Raw text buffer (no sentiment yet)
    live_realtime_news = []
    live_last_fetch_time = datetime.utcnow()
    seen_texts: set[str] = set()  # Deduplicate across fetches

    while live_automation_active:
        try:
            current_time = datetime.utcnow()

            # ── Phase 1: Continuously collect raw news ──────────────────
            time_since_last_fetch = (current_time - live_last_fetch_time).total_seconds()
            if time_since_last_fetch >= fetch_frequency:
                logger.info("Fetching latest crypto news...")
                # Don't pass from_time — fetch latest articles and deduplicate
                news_texts = fetch_crypto_news(
                    query=query or "crypto OR bitcoin OR ethereum",
                    limit=100
                )

                new_count = 0
                if news_texts:
                    for text in news_texts:
                        if not text:
                            continue
                        # Stop if buffer is at max
                        if len(live_collection_buffer) >= MAX_ARTICLES:
                            break
                        # Deduplicate
                        text_key = text.strip().lower()[:100]
                        if text_key in seen_texts:
                            continue
                        seen_texts.add(text_key)
                        new_count += 1

                        article_entry = {
                            "text": text,
                            "timestamp": datetime.utcnow().isoformat(),
                            "analyzed": False,   # NOT yet analysed
                            "sampled": False,
                        }

                        # Store in buffer for end-of-interval sampling
                        live_collection_buffer.append(article_entry)

                        # Also push to the real-time news feed (keep last 50)
                        live_realtime_news.append(article_entry)
                        if len(live_realtime_news) > 50:
                            live_realtime_news.pop(0)

                logger.info(f"  +{new_count} new articles  (buffer: {len(live_collection_buffer)}/{MAX_ARTICLES})")
                live_last_fetch_time = current_time

            # ── Phase 2: Interval completed → Sample & Analyse ──────────
            time_in_interval = (current_time - live_collection_start).total_seconds()
            if time_in_interval >= interval_seconds:
                buffer_size = len(live_collection_buffer)

                # If we haven't reached the minimum, keep collecting
                if buffer_size < MIN_ARTICLES:
                    logger.info(f"  Interval ended but only {buffer_size}/{MIN_ARTICLES} articles — still collecting...")
                    await asyncio.sleep(2)
                    continue

                logger.info("─" * 60)
                logger.info(f"INTERVAL COMPLETE  collected {buffer_size} articles (min={MIN_ARTICLES}, max={MAX_ARTICLES})")

                if buffer_size > 0:
                    # Randomly sample min(SAMPLE_SIZE, buffer_size) articles
                    pick_count = min(SAMPLE_SIZE, buffer_size)
                    sampled = random.sample(live_collection_buffer, pick_count)
                    sampled_texts = [a["text"] for a in sampled]

                    logger.info(f"  Randomly sampled {pick_count} / {buffer_size} articles (8:1 ratio)")

                    # Analyse ONLY the sampled articles
                    sentiments = analyze_batch(sampled_texts)

                    scores = []
                    analyzed_articles = []
                    for text, sent in zip(sampled_texts, sentiments):
                        if sent["label"] == "positive":
                            score = 50 + (sent["confidence"] * 50)
                        elif sent["label"] == "negative":
                            score = 50 - (sent["confidence"] * 50)
                        else:
                            score = 50
                        scores.append(score)
                        analyzed_articles.append({
                            "text": text,
                            "sentiment": sent,
                            "score": round(score, 2),
                            "timestamp": datetime.utcnow().isoformat(),
                            "analyzed": True,
                            "sampled": True,
                        })

                    # Average the sampled scores
                    avg_score = sum(scores) / len(scores)

                    # Most bullish / bearish from the sample
                    most_bullish = max(analyzed_articles, key=lambda x: x["score"])
                    most_bearish = min(analyzed_articles, key=lambda x: x["score"])

                    classification = (
                        "Bullish" if avg_score >= 60 else
                        "Bearish" if avg_score <= 40 else
                        "Neutral"
                    )

                    result = {
                        "score": round(avg_score, 2),
                        "raw_score": round(avg_score, 2),
                        "classification": classification,
                        "timestamp": current_time.isoformat(),
                        "sample_size": pick_count,
                        "total_collected": buffer_size,
                        "source": f"Live News ({interval})",
                        "interval": interval,
                        "highest_tweet": {
                            "text": most_bullish["text"],
                            "score": most_bullish["score"],
                            "label": most_bullish["sentiment"]["label"],
                            "confidence": most_bullish["sentiment"]["confidence"],
                        },
                        "lowest_tweet": {
                            "text": most_bearish["text"],
                            "score": most_bearish["score"],
                            "label": most_bearish["sentiment"]["label"],
                            "confidence": most_bearish["sentiment"]["confidence"],
                        },
                        "sampled_articles": analyzed_articles,
                    }

                    live_history.append(result)
                    logger.info(f"  ★ Score: {avg_score:.2f} ({classification})  [{pick_count} sampled / {buffer_size} total]")

                    # Mark sampled articles in the realtime feed so the UI can highlight them
                    sampled_set = set(t.strip().lower()[:100] for t in sampled_texts if t)
                    for article in live_realtime_news:
                        art_text = article.get("text") or ""
                        if not art_text:
                            continue
                        key = art_text.strip().lower()[:100]
                        if key in sampled_set:
                            match = next((a for a in analyzed_articles if a["text"] == article["text"]), None)
                            if match:
                                article["sentiment"] = match["sentiment"]
                                article["score"] = match["score"]
                                article["analyzed"] = True
                                article["sampled"] = True
                else:
                    logger.info("  No articles collected in this interval")
                    prev = live_history[-1]["score"] if live_history else 50
                    result = {
                        "score": prev,
                        "raw_score": prev,
                        "classification": "Neutral",
                        "timestamp": current_time.isoformat(),
                        "sample_size": 0,
                        "total_collected": 0,
                        "source": f"Live News ({interval})",
                        "interval": interval,
                        "message": "No articles in this interval",
                    }
                    live_history.append(result)

                logger.info("─" * 60)

                # Reset buffer for next interval
                live_collection_buffer = []
                live_collection_start = current_time
                seen_texts.clear()

            # Sleep briefly before next check
            await asyncio.sleep(2)

        except asyncio.CancelledError:
            logger.info("Live automation task cancelled")
            break
        except Exception as e:
            import traceback
            logger.error(f"Error in live automation task: {e}")
            logger.error(traceback.format_exc())
            await asyncio.sleep(5)

    # Always reset state when exiting the loop (crash, cancel, or flag turned off)
    live_automation_active = False
    live_automation_task = None
    logger.info("Live automation task exited — state reset")


def start_live_automation(interval: str = "1min", query: str | None = None):
    """Start the live automation background task."""
    global live_automation_active, live_automation_task, live_automation_interval
    
    # If already active, stop the old one first so the toggle always works
    if live_automation_active:
        logger.info("Stopping previous automation before restarting")
        stop_live_automation()
    
    live_automation_active = True
    live_automation_interval = interval
    live_automation_task = asyncio.create_task(live_automation_background_task(interval, query))
    logger.info(f"Live automation started with {interval} interval")
    return {"status": "started", "interval": interval}


def stop_live_automation():
    """Stop the live automation background task."""
    global live_automation_active, live_automation_task
    
    if not live_automation_active and live_automation_task is None:
        # Already stopped — not an error, just a no-op
        return {"status": "stopped", "message": "Was not running"}
    
    live_automation_active = False
    if live_automation_task:
        live_automation_task.cancel()
        live_automation_task = None
    
    logger.info("Live automation stopped")
    return {"status": "stopped"}


# ── App lifecycle ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run initial test analysis on startup."""
    logger.info("Running initial sentiment analysis (test mode)...")
    try:
        run_test_analysis("sample")
    except Exception as e:
        logger.warning(f"Initial analysis failed (non-fatal): {e}")
    yield
    
    # Cleanup on shutdown
    stop_live_automation()


app = FastAPI(title="SenTrack", lifespan=lifespan)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ── Request models ────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    mode: str = "test"       # "live", "news", or "test"
    dataset: str = "sample"  # test dataset key (ignored for live/news)
    query: str | None = None # custom search query (live/news mode)
    interval: str = "1min"   # time interval for news mode


class NewsControlRequest(BaseModel):
    action: str              # "start" or "stop"
    interval: str = "1min"   # time interval (30s, 1min, 2min, 5min, 10min, 30min, 1hr)
    query: str | None = None # custom search query


# ── API Endpoints ────────────────────────────────────────────────

@app.get("/")
async def dashboard():
    """Serve the web dashboard."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/settings")
async def get_settings():
    """Return configuration status for the frontend."""
    available_modes = ["test"]
    if news_configured():
        available_modes.append("live")  # Live mode now uses NewsAPI
    
    return {
        "news_configured": news_configured(),
        "available_modes": available_modes,
        "test_datasets": {
            key: {"label": ds["label"], "description": ds["description"]}
            for key, ds in TEST_DATASETS.items()
        },
        "news_intervals": get_available_intervals(),
        "nlp_engine": get_mode(),
        "live_automation_active": live_automation_active,
        "live_automation_interval": live_automation_interval if live_automation_active else None,
    }


@app.get("/api/score")
async def get_score(mode: str = Query("test")):
    """Get the latest Community Vibe Score for a given mode."""
    if mode == "live":
        history = live_history
    else:
        history = test_history
    
    logger.info(f"GET /api/score mode={mode}, history_size={len(history)}")

    if not history:
        return JSONResponse(
            {"error": f"No analysis has been run yet for '{mode}' mode."},
            status_code=404,
        )


    latest = history[-1]
    return {
        "score": latest["score"],
        "classification": latest["classification"],
        "timestamp": latest["timestamp"],
        "sample_size": latest["sample_size"],
        "raw_score": latest["raw_score"],
        "source": latest.get("source", "unknown"),
        "interval": latest.get("interval"),
        "nlp_engine": get_mode(),
        "mode": mode,
        "highest_tweet": latest.get("highest_tweet"),
        "lowest_tweet": latest.get("lowest_tweet"),
        "message": latest.get("message"),
    }



@app.get("/api/history")
async def get_history(mode: str = Query("test")):
    """Get the score history for charting."""
    if mode == "live":
        history = live_history
    else:
        history = test_history
    
    logger.info(f"GET /api/history mode={mode}, returning {len(history)} items")
    return {"history": history, "mode": mode}


@app.post("/api/analyze")
async def trigger_analysis(req: AnalyzeRequest):
    """Trigger a new analysis batch."""

    if req.mode == "live":
        if not news_configured():
            return JSONResponse(
                {"error": "News API key not configured. Add NEWS_API_KEY to your .env file."},
                status_code=400,
            )
        result = run_live_analysis(interval=req.interval, query=req.query or "crypto OR bitcoin OR ethereum")
    else:
        result = run_test_analysis(dataset=req.dataset)

    if "error" in result and not result.get("score"):
        return JSONResponse({"error": result["error"]}, status_code=400)

    return {
        "message": "Analysis complete.",
        "score": result["score"],
        "classification": result["classification"],
        "timestamp": result["timestamp"],
        "source": result.get("source", "unknown"),
        "mode": req.mode,
        "interval": result.get("interval"),
    }


@app.post("/api/live/automation")
async def control_live_automation(req: NewsControlRequest):
    """Start or stop live mode automation with continuous news collection."""
    
    if not news_configured():
        return JSONResponse(
            {"error": "News API key not configured. Add NEWS_API_KEY to your .env file."},
            status_code=400,
        )
    
    if req.action == "start":
        # If already active, we'll stop it first and restart (no error)
        
        # Validate interval
        if req.interval not in get_available_intervals():
            return JSONResponse(
                {"error": f"Invalid interval. Available: {list(get_available_intervals().keys())}"},
                status_code=400,
            )
        
        result = start_live_automation(interval=req.interval, query=req.query)
        if "error" in result:
            return JSONResponse(result, status_code=400)
        
        return {
            "message": f"Live automation started with {req.interval} aggregation interval",
            "interval": req.interval,
            "interval_seconds": get_interval_seconds(req.interval),
            "active": True,
        }
    
    elif req.action == "stop":
        result = stop_live_automation()
        if "error" in result:
            return JSONResponse(result, status_code=400)
        
        return {
            "message": "Live automation stopped",
            "active": False,
        }
    
    else:
        return JSONResponse(
            {"error": "Invalid action. Use 'start' or 'stop'."},
            status_code=400,
        )


@app.get("/api/live/realtime-news")
async def get_realtime_news():
    """Get the real-time news feed (last 50 articles with sentiment)."""
    return {
        "news": list(reversed(live_realtime_news)),  # Newest first
        "count": len(live_realtime_news),
        "automation_active": live_automation_active,
        "current_interval": live_automation_interval if live_automation_active else None,
        "collection_start": live_collection_start.isoformat() if live_collection_start else None,
        "buffer_size": len(live_collection_buffer)
    }


@app.get("/api/live/status")
async def get_live_status():
    """Get current live automation status with interval progress."""
    elapsed = 0.0
    remaining = 0.0
    interval_secs = 0
    if live_automation_active and live_collection_start:
        interval_secs = get_interval_seconds(live_automation_interval)
        elapsed = (datetime.utcnow() - live_collection_start).total_seconds()
        remaining = max(0, interval_secs - elapsed)

    return {
        "active": live_automation_active,
        "interval": live_automation_interval if live_automation_active else None,
        "interval_seconds": interval_secs,
        "elapsed_seconds": round(elapsed, 1),
        "remaining_seconds": round(remaining, 1),
        "articles_in_buffer": len(live_collection_buffer),
        "realtime_feed_size": len(live_realtime_news),
        "total_scores": len(live_history),
        "last_fetch": live_last_fetch_time.isoformat() if live_last_fetch_time else None,
        "collection_start": live_collection_start.isoformat() if live_collection_start else None,
    }


# ── Contribute Scan ──────────────────────────────────────────────

async def contribute_scan_task_fn():
    """
    1-minute scan: collect news → sample 25 → analyse → return average score.
    This is independent from the Live automation loop.
    """
    global contribute_scan_active, contribute_scan_result, contribute_scan_progress

    SCAN_DURATION = 60   # seconds
    FETCH_FREQ = 15      # fetch every 15s
    SAMPLE_SIZE = 25
    query = "crypto OR bitcoin OR ethereum"
    buffer: list[dict] = []
    seen: set[str] = set()
    start = datetime.utcnow()
    last_fetch = datetime.utcnow() - timedelta(seconds=FETCH_FREQ)  # trigger immediate first fetch

    contribute_scan_progress = {"phase": "collecting", "articles": 0, "elapsed": 0, "message": "Starting scan..."}

    try:
        while contribute_scan_active:
            now = datetime.utcnow()
            elapsed = (now - start).total_seconds()
            remaining = max(0, SCAN_DURATION - elapsed)
            contribute_scan_progress["elapsed"] = round(elapsed)

            # Fetch
            if (now - last_fetch).total_seconds() >= FETCH_FREQ:
                try:
                    articles = fetch_crypto_news(query=query, limit=100)
                    new_count = 0
                    for art in articles:
                        key = (art.get("title") or "").strip()[:80]
                        if key and key not in seen:
                            seen.add(key)
                            text = f"{(art.get('title') or '').strip()}. {(art.get('description') or '').strip()}"
                            if len(text.strip()) > 5:
                                buffer.append({"text": text, "title": art.get("title", "")})
                                new_count += 1
                    logger.info(f"[Contribute] Fetched {len(articles)} articles, +{new_count} new (buffer: {len(buffer)})")
                except Exception as e:
                    logger.error(f"[Contribute] Fetch error: {e}")
                last_fetch = now

            contribute_scan_progress["articles"] = len(buffer)
            contribute_scan_progress["message"] = f"Collecting... {int(remaining)}s left ({len(buffer)} articles)"

            # Time's up?
            if elapsed >= SCAN_DURATION:
                break

            await asyncio.sleep(2)

        # ── Phase 2: Sample & Analyse ──
        contribute_scan_progress["phase"] = "analyzing"
        contribute_scan_progress["message"] = f"Sampling {SAMPLE_SIZE} of {len(buffer)} articles..."

        if len(buffer) < 5:
            contribute_scan_result = {"error": "Not enough articles collected", "score": None}
            contribute_scan_progress["phase"] = "error"
            contribute_scan_progress["message"] = "Not enough articles"
            return

        pick_count = min(SAMPLE_SIZE, len(buffer))
        sampled = random.sample(buffer, pick_count)
        texts = [s["text"] for s in sampled]

        contribute_scan_progress["message"] = f"Analyzing {pick_count} articles with FinBERT..."

        results = analyze_batch(texts)
        scores = [r["score"] for r in results]
        avg_score = round(sum(scores) / len(scores), 2)
        classification = "Bullish" if avg_score >= 60 else "Bearish" if avg_score <= 40 else "Neutral"

        contribute_scan_result = {
            "score": avg_score,
            "classification": classification,
            "sample_size": pick_count,
            "total_collected": len(buffer),
            "timestamp": datetime.utcnow().isoformat(),
            "engine": get_mode(),
        }
        contribute_scan_progress["phase"] = "done"
        contribute_scan_progress["message"] = f"Score: {avg_score} ({classification})"
        logger.info(f"[Contribute] ★ Score: {avg_score} ({classification}) [{pick_count} sampled / {len(buffer)} total]")

    except asyncio.CancelledError:
        logger.info("[Contribute] Scan cancelled")
        contribute_scan_progress["phase"] = "cancelled"
        contribute_scan_progress["message"] = "Scan cancelled"
    except Exception as e:
        import traceback
        logger.error(f"[Contribute] Error: {e}")
        logger.error(traceback.format_exc())
        contribute_scan_result = {"error": str(e), "score": None}
        contribute_scan_progress["phase"] = "error"
        contribute_scan_progress["message"] = f"Error: {e}"
    finally:
        contribute_scan_active = False
        contribute_scan_task = None


@app.post("/api/contribute/start")
async def start_contribute_scan():
    """Start a 1-minute contribute scan."""
    global contribute_scan_active, contribute_scan_task, contribute_scan_result

    if not news_configured():
        return JSONResponse({"error": "News API key not configured."}, status_code=400)

    if contribute_scan_active:
        return JSONResponse({"error": "Contribute scan already running."}, status_code=400)

    contribute_scan_active = True
    contribute_scan_result = None
    contribute_scan_task = asyncio.create_task(contribute_scan_task_fn())

    return {"message": "Contribute scan started (1 minute)", "active": True}


@app.get("/api/contribute/status")
async def get_contribute_status():
    """Poll contribute scan progress."""
    return {
        "active": contribute_scan_active,
        "phase": contribute_scan_progress.get("phase", "idle"),
        "articles": contribute_scan_progress.get("articles", 0),
        "elapsed": contribute_scan_progress.get("elapsed", 0),
        "message": contribute_scan_progress.get("message", ""),
        "result": contribute_scan_result,
    }


@app.post("/api/contribute/cancel")
async def cancel_contribute_scan():
    """Cancel an in-progress contribute scan."""
    global contribute_scan_active, contribute_scan_task
    if not contribute_scan_active:
        return {"message": "No scan running"}
    contribute_scan_active = False
    if contribute_scan_task:
        contribute_scan_task.cancel()
        contribute_scan_task = None
    return {"message": "Scan cancelled"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
