"""
SenTrack — FastAPI Server
Dual-mode sentiment oracle: Live (Farcaster) & Test (CSV datasets)
Pipeline: data → NLP → vibe score → API → dashboard
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from data_loader import load_tweets, load_test_tweets, load_kaggle_sample
from live_data import fetch_live_casts, is_configured as neynar_configured
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
        return {
            "score": 50.0,
            "classification": "Neutral",
            "timestamp": "",
            "sample_size": 0,
            "raw_score": 50.0,
            "source": source,
            "error": "No texts to analyze.",
        }


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



def run_live_analysis(query: str | None = None) -> dict:
    """Fetch casts from Farcaster and analyze."""
    casts = fetch_live_casts(query=query) if query else fetch_live_casts()
    return _run_analysis(casts, live_history, "farcaster")


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


# ── App lifecycle ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run initial test analysis on startup."""
    logger.info("Running initial sentiment analysis (test mode)...")
    run_test_analysis("sample")
    yield


app = FastAPI(title="SenTrack", lifespan=lifespan)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ── Request model ────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    mode: str = "test"       # "live" or "test"
    dataset: str = "sample"  # test dataset key (ignored for live)
    query: str | None = None # custom search query (live mode only)


# ── API Endpoints ────────────────────────────────────────────────

@app.get("/")
async def dashboard():
    """Serve the web dashboard."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/settings")
async def get_settings():
    """Return configuration status for the frontend."""
    return {
        "neynar_configured": neynar_configured(),
        "available_modes": ["test", "live"] if neynar_configured() else ["test"],
        "test_datasets": {
            key: {"label": ds["label"], "description": ds["description"]}
            for key, ds in TEST_DATASETS.items()
        },
        "nlp_engine": get_mode(),
    }


@app.get("/api/score")
async def get_score(mode: str = Query("test")):
    """Get the latest Community Vibe Score for a given mode."""
    history = live_history if mode == "live" else test_history

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
        "nlp_engine": get_mode(),
        "mode": mode,
    }


@app.get("/api/history")
async def get_history(mode: str = Query("test")):
    """Get the score history for charting."""
    history = live_history if mode == "live" else test_history
    return {"history": history, "mode": mode}


@app.post("/api/analyze")
async def trigger_analysis(req: AnalyzeRequest):
    """Trigger a new analysis batch."""

    if req.mode == "live":
        if not neynar_configured():
            return JSONResponse(
                {"error": "Neynar API key not configured. Add NEYNAR_API_KEY to your .env file."},
                status_code=400,
            )
        result = run_live_analysis(query=req.query)
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
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
