"""
Data loader with noise filtering for crypto tweet CSVs.
"""

import re

# Patterns that indicate spam/noise
_SPAM_PATTERNS = [
    re.compile(r"(.)\1{5,}"),           # repeated characters (aaaaaa)
    re.compile(r"[!?]{4,}"),            # excessive punctuation
    re.compile(r"(?:https?://\S+\s*){3,}"),  # 3+ URLs in one text
]


def _is_spam(text: str) -> bool:
    """Check if text matches spam heuristics."""
    # All caps (>80% uppercase letters)
    alpha = [c for c in text if c.isalpha()]
    if alpha and sum(1 for c in alpha if c.isupper()) / len(alpha) > 0.8:
        return True
    return any(p.search(text) for p in _SPAM_PATTERNS)


def load_tweets(csv_path: str, text_column: str = "text", limit: int = 200) -> list[str]:
    """
    Load and clean tweets from a CSV file.

    Args:
        csv_path: Path to the CSV file.
        text_column: Name of the column containing tweet text.
        limit: Max number of tweets to return.

    Returns:
        Cleaned list of tweet strings.
    """
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Skip header row if it matches the expected column name
    if lines and lines[0].strip().lower() == text_column:
        lines = lines[1:]

    texts = [line.strip() for line in lines if line.strip()]

    # Deduplicate
    seen = set()
    unique = []
    for t in texts:
        normalized = t.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(t.strip())
    texts = unique

    # Filter short texts (< 10 chars)
    texts = [t for t in texts if len(t) >= 10]

    # Filter spam
    texts = [t for t in texts if not _is_spam(t)]

    return texts[:limit]
