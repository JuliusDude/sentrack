"""Fetch and display latest crypto news using NEWS API."""

import requests
import os

# Directly use the API key
NEWS_API_KEY = "c92a411efa4f44dba2ef570d3d260b20"

url = 'https://newsapi.org/v2/everything'
params = {
    'q': 'cryptocurrency OR bitcoin OR ethereum',
    'sortBy': 'publishedAt',
    'language': 'en',
    'pageSize': 10,
    'apiKey': NEWS_API_KEY
}

print("🔑 Testing NEWS API Key")
print("=" * 70)

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    print(f"✅ Status: {data.get('status').upper()}")
    print(f"📊 Total Results Available: {data.get('totalResults', 0):,}")
    print(f"📄 Fetched: {len(data.get('articles', []))} articles")
    print("\n" + "=" * 70)
    print("📰 LATEST CRYPTOCURRENCY NEWS")
    print("=" * 70 + "\n")
    
    articles = data.get('articles', [])
    for i, article in enumerate(articles, 1):
        title = article.get('title', 'N/A')
        source = article.get('source', {}).get('name', 'Unknown')
        published = article.get('publishedAt', 'N/A')[:10]  # Just the date
        url_link = article.get('url', 'N/A')
        description = article.get('description', '')
        
        print(f"{i}. {title}")
        print(f"   📍 Source: {source}")
        print(f"   📅 Published: {published}")
        if description and len(description) > 10:
            desc_short = description[:150] + '...' if len(description) > 150 else description
            print(f"   💬 {desc_short}")
        print(f"   🔗 {url_link}")
        print()
    
    print("=" * 70)
    print("✅ NEWS API KEY IS VALID AND WORKING!")
    print("\nAPI Capabilities:")
    print("  • 100 requests/day (free tier)")
    print("  • Access to 3,600+ articles on crypto topics")
    print("  • Real-time news from multiple sources")
    print("  • Can filter by source, date, language, etc.")
    print("\nPossible Integration with SenTrack:")
    print("  • Add news sentiment analysis")
    print("  • Correlate news with social sentiment")
    print("  • Display breaking news on dashboard")
    print("  • Alert on major crypto news events")
    
except requests.exceptions.HTTPError as e:
    print(f"❌ HTTP Error: {e}")
    print(f"Response: {e.response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
