"""
SenTrack — FastAPI Server
Sentiment oracle pipeline: data → NLP → vibe score → API → dashboard
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from data_loader import load_tweets
from sentiment import analyze_batch, get_mode
from vibe_score import calculate_vibe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory state
score_history: list[dict] = []
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "sample_tweets.csv")


def run_analysis():
    """Execute one analysis cycle: load → analyze → score → store."""
    tweets = load_tweets(DATA_PATH)
    logger.info("Loaded %d tweets for analysis.", len(tweets))

    sentiments = analyze_batch(tweets)
    logger.info("Analyzed %d tweets via %s.", len(sentiments), get_mode())

    prev = score_history[-1]["score"] if score_history else None
    result = calculate_vibe(sentiments, previous_score=prev)
    score_history.append(result)

    logger.info("Vibe score: %.2f (%s)", result["score"], result["classification"])
    return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run initial analysis on startup."""
    logger.info("Running initial sentiment analysis...")
    run_analysis()
    yield


app = FastAPI(title="SenTrack", lifespan=lifespan)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def dashboard():
    """Serve the web dashboard."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/score")
async def get_score():
    """Get the latest Community Vibe Score."""
    if not score_history:
        return JSONResponse({"error": "No analysis has been run yet."}, status_code=404)
    latest = score_history[-1]
    return {
        "score": latest["score"],
        "classification": latest["classification"],
        "timestamp": latest["timestamp"],
        "sample_size": latest["sample_size"],
        "raw_score": latest["raw_score"],
        "nlp_engine": get_mode(),
    }


@app.get("/api/history")
async def get_history():
    """Get the score history for charting."""
    return {"history": score_history}


@app.post("/api/analyze")
async def trigger_analysis():
    """Trigger a new analysis batch."""
    result = run_analysis()
    return {
        "message": "Analysis complete.",
        "score": result["score"],
        "classification": result["classification"],
        "timestamp": result["timestamp"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
