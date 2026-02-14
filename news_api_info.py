"""
NEWS API Testing & Information Script
=====================================

The NEWS_API_KEY found in your .env file appears to be invalid or expired.

API Key: c92a411efa4f44dba2ef570d3d260b20
Status: ❌ Invalid (401 Unauthorized)

News API Information:
---------------------
- Provider: NewsAPI.org
- Purpose: Fetch latest news articles about cryptocurrency, bitcoin, ethereum, etc.
- Free Tier: 100 requests/day, 1 month article history
- Paid Plans: Higher limits and more features

How to Get a New API Key:
--------------------------
1. Visit https://newsapi.org
2. Sign up for a free account
3. Get your API key from the dashboard
4. Replace the old key in your .env file

Endpoints Available:
--------------------
1. /v2/top-headlines - Get breaking news headlines
2. /v2/everything - Search through millions of articles
3. /v2/sources - Get available news sources

Test with curl:
curl 'https://newsapi.org/v2/everything?q=bitcoin&apiKey=YOUR_API_KEY'

Integration with SenTrack:
--------------------------
This API could be used to:
- Fetch real-time crypto news
- Analyze news sentiment alongside social media
- Correlate news events with sentiment scores
- Provide context for sudden sentiment changes
"""

import requests

def test_news_api(api_key):
    """Test the News API with a given key."""
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': 'cryptocurrency',
        'sortBy': 'publishedAt',
        'pageSize': 5,
        'apiKey': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Key is valid!")
            print(f"   Total Results: {data.get('totalResults', 0)}")
            print(f"   Articles fetched: {len(data.get('articles', []))}")
            return True
        elif response.status_code == 401:
            print(f"❌ API Key is invalid or expired")
            print(f"   Error: {response.json().get('message')}")
            return False
        elif response.status_code == 429:
            print(f"⚠️  Rate limit exceeded")
            return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print(__doc__)
    
    print("\n" + "="*60)
    print("Testing Current API Key...")
    print("="*60)
    
    current_key = "c92a411efa4f44dba2ef570d3d260b20"
    test_news_api(current_key)
    
    print("\n" + "="*60)
    print("To test with a new key, run:")
    print("  python test_news_api.py YOUR_NEW_KEY")
    print("="*60)
