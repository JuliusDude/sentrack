"""
Community Vibe Score calculator.
Confidence-weighted aggregation with EMA smoothing.
"""

from datetime import datetime, timezone

# Label → raw sentiment value mapping
_LABEL_VALUE = {
    "positive": 1.0,
    "neutral": 0.5,
    "negative": 0.0,
}

# EMA smoothing factor (0–1). Higher = more reactive, lower = smoother.
_ALPHA = 0.3


def classify(score: float) -> str:
    """Classify a 0–100 score into market sentiment."""
    if score <= 30:
        return "Bearish"
    if score <= 60:
        return "Neutral"
    return "Bullish"


def calculate_vibe(sentiments: list[dict], previous_score: float | None = None) -> dict:
    """
    Calculate the Community Vibe Score from sentiment results.

    Args:
        sentiments: List of {"label": str, "confidence": float}.
        previous_score: Previous vibe score for EMA smoothing (None on first run).

    Returns:
        {"score": float, "classification": str, "timestamp": str,
         "sample_size": int, "raw_score": float}
    """
    if not sentiments:
        return {
            "score": 50.0,
            "classification": "Neutral",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sample_size": 0,
            "raw_score": 50.0,
        }

    # Confidence-weighted average
    weighted_sum = 0.0
    weight_total = 0.0

    for s in sentiments:
        value = _LABEL_VALUE.get(s["label"], 0.5)
        conf = s.get("confidence", 0.5)
        weighted_sum += value * conf
        weight_total += conf

    raw = (weighted_sum / weight_total) * 100 if weight_total > 0 else 50.0

    # EMA smoothing
    if previous_score is not None:
        score = _ALPHA * raw + (1 - _ALPHA) * previous_score
    else:
        score = raw

    score = round(min(100.0, max(0.0, score)), 2)

    return {
        "score": score,
        "classification": classify(score),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sample_size": len(sentiments),
        "raw_score": round(raw, 2),
    }
