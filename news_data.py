"""
Live news fetcher — Crypto news via NewsAPI.
Fetches breaking crypto news in real time with configurable intervals.
"""

import os
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

NEWS_API_BASE = "https://newsapi.org/v2/everything"

# Default search query — covers crypto topics
DEFAULT_QUERY = "cryptocurrency OR bitcoin OR ethereum OR blockchain OR defi"

# Time interval configurations (in seconds)
TIME_INTERVALS = {
    "30s": 30,
    "1min": 60,
    "2min": 120,
    "5min": 300,
    "10min": 600,
    "30min": 1800,
    "1hr": 3600,
}


def _get_api_key() -> str | None:
    """Get News API key from environment."""
    return os.environ.get("NEWS_API_KEY")


def is_configured() -> bool:
    """Check if News API key is available."""
    key = _get_api_key()
    return key is not None and key != "" and key != "your_news_api_key_here"


def fetch_crypto_news(
    query: str = DEFAULT_QUERY,
    limit: int = 50,
    from_time: datetime | None = None,
) -> list[str]:
    """
    Fetch crypto news articles from NewsAPI.

    Args:
        query: Search query string (supports AND/OR operators).
        limit: Max number of articles to fetch (1-100).
        from_time: Fetch articles from this time onwards (default: last 1 hour).

    Returns:
        List of article titles and descriptions combined.
    """
    api_key = _get_api_key()

    if not api_key or api_key == "your_news_api_key_here":
        logger.warning("News API key not configured. News mode unavailable.")
        return []

    params = {
        "q": query,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": min(limit, 100),
        "apiKey": api_key,
    }

    # Only add 'from' if explicitly provided AND reasonable (>= 1 hour window)
    # Short windows (seconds/minutes) return 0 results from NewsAPI
    if from_time is not None:
        delta = datetime.utcnow() - from_time
        if delta.total_seconds() >= 3600:  # Only use from_time for >= 1 hour
            params["from"] = from_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        # For shorter windows, skip the 'from' param and fetch latest articles

    try:
        logger.info("Fetching news articles: query='%s', limit=%d", query, limit)
        response = requests.get(NEWS_API_BASE, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()
        
        if data.get("status") != "ok":
            logger.error("News API error: %s", data.get("message", "Unknown error"))
            return []

        articles = data.get("articles", [])
        
        # Combine title and description for better sentiment analysis
        texts = []
        seen = set()
        
        for article in articles:
            title = (article.get("title") or "").strip()
            description = (article.get("description") or "").strip()
            
            # Combine title and description
            combined = f"{title}. {description}" if description else title
            
            if not combined or len(combined) < 20:
                continue
            
            # Deduplicate
            normalized = combined.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            
            texts.append(combined)

        logger.info("Fetched %d news articles from NewsAPI.", len(texts))
        return texts

    except requests.exceptions.Timeout:
        logger.error("News API request timed out.")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error("News API HTTP error: %s", e)
        if hasattr(e, 'response') and e.response is not None:
            logger.error("Response: %s", e.response.text)
        return []
    except requests.exceptions.RequestException as e:
        logger.error("News API request failed: %s", e)
        return []
    except (KeyError, ValueError) as e:
        logger.error("Failed to parse News API response: %s", e)
        return []


def get_interval_seconds(interval_key: str) -> int:
    """Get the number of seconds for a given interval key."""
    return TIME_INTERVALS.get(interval_key, 60)  # Default to 1 minute


def get_available_intervals() -> dict[str, int]:
    """Get all available time intervals."""
    return TIME_INTERVALS.copy()
