"""Test NEWS_API_KEY and fetch crypto news."""

import requests
import os
from dotenv import load_dotenv

# Load from .env file in current directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

NEWS_API_KEY = os.getenv('NEWS_API_KEY')

# Fallback: read manually if dotenv fails
if not NEWS_API_KEY:
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('NEWS_API_KEY'):
                    NEWS_API_KEY = line.split('=', 1)[1].strip()
                    break
    except:
        pass

if not NEWS_API_KEY:
    print("❌ NEWS_API_KEY not found in .env file!")
    exit(1)

# Test News API - Get top crypto news headlines
url = 'https://newsapi.org/v2/everything'
params = {
    'q': 'cryptocurrency OR bitcoin OR ethereum',
    'sortBy': 'publishedAt',
    'language': 'en',
    'pageSize': 5,
    'apiKey': NEWS_API_KEY
}

print(f"Testing News API Key: {NEWS_API_KEY[:10]}...")
print("=" * 60)

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    print(f"Status: {data.get('status', 'unknown')}")
    print(f"Total Results: {data.get('totalResults', 0)}")
    print("\n📰 Latest Crypto News:\n")
    
    articles = data.get('articles', [])
    for i, article in enumerate(articles[:5], 1):
        print(f"{i}. {article.get('title', 'N/A')}")
        print(f"   Source: {article.get('source', {}).get('name', 'Unknown')}")
        print(f"   Published: {article.get('publishedAt', 'N/A')}")
        print(f"   URL: {article.get('url', 'N/A')[:60]}...")
        print()
    
    print("=" * 60)
    print(f"✅ News API Key is valid and working!")
    print(f"\nAPI Info:")
    print(f"  - Endpoint: {url}")
    print(f"  - Rate Limits: Check response headers")
    print(f"  - Available Articles: {data.get('totalResults', 0)}")
    
except requests.exceptions.HTTPError as e:
    print(f"❌ HTTP Error: {e}")
    if hasattr(e, 'response'):
        print(f"Response: {e.response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
