"""
Data loader with noise filtering and multi-format CSV support.
Handles the original sample_tweets.csv, Kaggle crypto datasets,
and Sentiment140-format CSVs.
"""

import csv
import re
import logging
import os
import random

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import kagglehub
    from kagglehub import KaggleDatasetAdapter
except ImportError:
    kagglehub = None

logger = logging.getLogger(__name__)

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


def _clean_texts(texts: list[str], limit: int = 200) -> list[str]:
    """Deduplicate, filter short/spam texts, and limit results."""
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


def load_tweets(csv_path: str, text_column: str = "text", limit: int = 200) -> list[str]:
    """
    Load and clean tweets from a simple single-column CSV file.

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
    return _clean_texts(texts, limit)


def load_test_tweets(csv_path: str, limit: int = 500) -> list[str]:
    """
    Load tweets from various CSV formats with auto-detection.

    Supports:
        - Simple single-column CSVs (header: 'text')
        - Multi-column CSVs with a 'text', 'tweet', or 'content' column
        - Sentiment140 format (6 columns: polarity,id,date,query,user,text)

    Args:
        csv_path: Path to the CSV file.
        limit: Max number of tweets to return.

    Returns:
        Cleaned list of tweet strings.
    """
    texts = []

    try:
        with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
            # Peek at first line to detect format
            first_line = f.readline().strip()
            f.seek(0)

            # Check if it's a simple single-column file
            if first_line.lower() == "text":
                lines = f.readlines()[1:]  # skip header
                texts = [line.strip() for line in lines if line.strip()]
                logger.info("Detected single-column CSV format.")

            else:
                reader = csv.reader(f)
                header = next(reader, None)

                if header is None:
                    logger.warning("Empty CSV file: %s", csv_path)
                    return []

                # Try to find text column by name
                text_col_idx = None
                text_col_names = ["text", "tweet", "content", "message", "body"]

                for i, col in enumerate(header):
                    if col.strip().lower() in text_col_names:
                        text_col_idx = i
                        logger.info("Found text column '%s' at index %d.", col.strip(), i)
                        break

                # Sentiment140 format: 6 columns, text is last (index 5)
                if text_col_idx is None and len(header) == 6:
                    text_col_idx = 5
                    logger.info("Detected Sentiment140 format (6 columns, text at index 5).")

                # Fallback: use last column
                if text_col_idx is None:
                    text_col_idx = len(header) - 1
                    logger.info("Falling back to last column (index %d) for text.", text_col_idx)

                for row in reader:
                    if len(row) > text_col_idx:
                        text = row[text_col_idx].strip()
                        if text:
                            texts.append(text)

    except FileNotFoundError:
        logger.error("CSV file not found: %s", csv_path)
        return []
    except Exception as e:
        logger.error("Error reading CSV file %s: %s", csv_path, e)
        return []

    logger.info("Loaded %d raw texts from %s.", len(texts), csv_path)
    return _clean_texts(texts, limit)


def load_kaggle_sample(handle: str, limit: int = 128) -> list[str]:
    """
    Load a random sample of tweets from a Kaggle dataset.
    Downloads if not present, auto-detects CSV file and text column.
    """
    if kagglehub is None or pd is None:
        logger.error("kagglehub or pandas not installed. Cannot load Kaggle dataset.")
        return []

    try:
        # Download/Update dataset
        logger.info("Downloading/Verified Kaggle dataset: %s", handle)
        path = kagglehub.dataset_download(handle)
        
        # Find CSV file
        csv_files = [f for f in os.listdir(path) if f.lower().endswith('.csv')]
        if not csv_files:
            logger.error("No CSV files found in dataset %s at %s", handle, path)
            return []
            
        # Prioritize known filenames or just take largest?
        # For simple robustness, take the largest CSV file
        csv_file = max(csv_files, key=lambda f: os.path.getsize(os.path.join(path, f)))
        full_path = os.path.join(path, csv_file)
        logger.info("Loading file: %s", full_path)
        
        # Load with pandas
        # Sentiment140 is known to be latin-1 and headerless
        # Others might be utf-8 with header.
        # We try to detect.
        
        try:
            df = pd.read_csv(full_path, encoding='utf-8', engine='python', on_bad_lines='skip')
        except UnicodeDecodeError:
            df = pd.read_csv(full_path, encoding='latin-1', engine='python', on_bad_lines='skip', header=None)
            
        # If header=None was used (or inferred), columns are ints.
        # If first row looks like header (strings), use it.
        
        # Heuristic to find text column
        text_col = None
        
        # 1. Look for common names
        candidates = ['text', 'tweet', 'content', 'message', 'body', 'review']
        for col in df.columns:
            if str(col).lower() in candidates:
                text_col = col
                break
                
        # 2. If not found, look for column with longest average string length
        if text_col is None:
            max_avg_len = 0
            for col in df.columns:
                # Sample a few values to check type and length
                sample_vals = df[col].dropna().head(10).astype(str)
                avg_len = sample_vals.apply(len).mean()
                if avg_len > max_avg_len and avg_len > 10: # filtering out IDs or short codes
                    max_avg_len = avg_len
                    text_col = col
                    
        if text_col is None:
            # Fallback for Sentiment140 specific known index (last column usually)
            if 'sentiment140' in handle.lower() and len(df.columns) == 6:
                text_col = df.columns[-1]
            else:
                 # Last resort: last column
                 text_col = df.columns[-1]

        logger.info("Selected text column: %s", text_col)

        # Sampling
        if len(df) > limit:
            sample_df = df.sample(n=limit)
        else:
            sample_df = df
        
        # Convert to string and filter out NaN/None values
        texts = []
        for val in sample_df[text_col]:
            # Skip NaN, None, and non-string convertible values
            if pd.isna(val):
                continue
            try:
                text_str = str(val).strip()
                if text_str and text_str.lower() not in ['nan', 'none', '']:
                    texts.append(text_str)
            except:
                continue
                
        return _clean_texts(texts, limit)

    except Exception as e:
        logger.error("Failed to load/sample Kaggle dataset %s: %s", handle, e)
        return []

