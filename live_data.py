"""
Live data fetcher — Farcaster casts via Neynar API v2.
Searches for crypto/finance-relevant casts in real time.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

NEYNAR_BASE = "https://api.neynar.com/v2/farcaster/cast/search"

# Default search query — covers broad crypto/finance topics
DEFAULT_QUERY = "crypto | bitcoin | ethereum | defi | blockchain"

# Keywords for post-fetch relevance filtering
_CRYPTO_KEYWORDS = {
    "bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain", "defi",
    "nft", "solana", "sol", "cardano", "ada", "polygon", "matic",
    "avalanche", "avax", "arbitrum", "optimism", "layer2", "l2",
    "staking", "yield", "airdrop", "token", "wallet", "dex", "cex",
    "swap", "liquidity", "tvl", "dao", "web3", "metaverse", "mining",
    "halving", "bull", "bear", "altcoin", "hodl", "whale", "pump",
    "dump", "rug", "moon", "fud", "degen", "gm", "wagmi", "ngmi",
    "base", "farcaster", "warpcast", "onchain", "on-chain",
    "market", "trading", "price", "rally", "crash", "dip",
    "regulation", "sec", "etf", "cbdc", "stablecoin", "usdt", "usdc",
}


def _get_api_key() -> str | None:
    """Get Neynar API key from environment."""
    return os.environ.get("NEYNAR_API_KEY")


def _is_crypto_relevant(text: str) -> bool:
    """Check if text contains crypto/finance keywords."""
    lower = text.lower()
    return any(kw in lower for kw in _CRYPTO_KEYWORDS)


def is_configured() -> bool:
    """Check if Neynar API key is available."""
    key = _get_api_key()
    return key is not None and key != "" and key != "your_neynar_api_key_here"


def fetch_live_casts(
    query: str = DEFAULT_QUERY,
    limit: int = 100,
    relevance_filter: bool = True,
) -> list[str]:
    """
    Fetch live casts from Farcaster via Neynar API.

    Args:
        query: Search query string (supports AND/OR operators).
        limit: Max number of casts to fetch (1-100 per API call).
        relevance_filter: If True, filter results for crypto relevance.

    Returns:
        List of cast text strings, cleaned and filtered.
    """
    api_key = _get_api_key()

    if not api_key or api_key == "your_neynar_api_key_here":
        logger.warning("Neynar API key not configured. Live mode unavailable.")
        return []

    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
    }

    params = {
        "q": query,
        "limit": min(limit, 100),
        "mode": "literal",
        "sort_type": "desc_chron",
    }

    try:
        logger.info("Fetching casts from Farcaster: query='%s', limit=%d", query, limit)
        response = requests.get(NEYNAR_BASE, headers=headers, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()
        casts = data.get("result", {}).get("casts", [])

        # Extract text from each cast
        texts = []
        seen = set()
        for cast in casts:
            text = cast.get("text", "").strip()
            if not text or len(text) < 10:
                continue

            # Deduplicate
            normalized = text.lower()
            if normalized in seen:
                continue
            seen.add(normalized)

            texts.append(text)

        # Optional crypto relevance filter
        if relevance_filter:
            before = len(texts)
            texts = [t for t in texts if _is_crypto_relevant(t)]
            logger.info(
                "Relevance filter: %d/%d casts passed crypto keyword check.",
                len(texts), before,
            )

        logger.info("Fetched %d casts from Farcaster.", len(texts))
        return texts

    except requests.exceptions.Timeout:
        logger.error("Neynar API request timed out.")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error("Neynar API HTTP error: %s", e)
        return []
    except requests.exceptions.RequestException as e:
        logger.error("Neynar API request failed: %s", e)
        return []
    except (KeyError, ValueError) as e:
        logger.error("Failed to parse Neynar API response: %s", e)
        return []
