"""
Sentiment analysis engine.
Primary: FinBERT (ProsusAI/finbert) for financial-domain NLP.
Fallback: VADER for environments where FinBERT can't load.
"""

import logging

logger = logging.getLogger(__name__)

_analyzer = None
_mode = None


def _init_analyzer():
    """Lazy-load the sentiment model. Try FinBERT first, fall back to VADER."""
    global _analyzer, _mode

    if _analyzer is not None:
        return

    # Try FinBERT
    try:
        from transformers import pipeline
        _analyzer = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            top_k=None,
        )
        _mode = "finbert"
        logger.info("Loaded FinBERT sentiment model.")
        return
    except Exception as e:
        logger.warning("FinBERT unavailable (%s), falling back to VADER.", e)

    # Fallback: VADER
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _analyzer = SentimentIntensityAnalyzer()
    _mode = "vader"
    logger.info("Loaded VADER sentiment analyzer.")


def _finbert_analyze(texts: list[str]) -> list[dict]:
    """Run FinBERT on a batch of texts."""
    results = []
    # FinBERT max token length is 512; truncate long texts
    truncated = [t[:512] for t in texts]
    raw = _analyzer(truncated)

    for scores in raw:
        # scores is a list of {label, score} dicts for each class
        best = max(scores, key=lambda x: x["score"])
        label = best["label"].lower()  # positive / negative / neutral
        results.append({
            "label": label,
            "confidence": round(best["score"], 4),
        })
    return results


def _vader_analyze(texts: list[str]) -> list[dict]:
    """Run VADER on a batch of texts."""
    results = []
    for text in texts:
        scores = _analyzer.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"
        results.append({
            "label": label,
            "confidence": round(abs(compound), 4),
        })
    return results


def analyze_batch(texts: list[str]) -> list[dict]:
    """
    Analyze a batch of texts for sentiment.
    Returns list of {"label": str, "confidence": float}.
    """
    if not texts:
        return []

    _init_analyzer()

    if _mode == "finbert":
        return _finbert_analyze(texts)
    return _vader_analyze(texts)


def get_mode() -> str:
    """Return which NLP backend is active."""
    _init_analyzer()
    return _mode
