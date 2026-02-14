"""Quick test of news mode API endpoints."""

import requests
import time

BASE_URL = "http://localhost:8000"

print("Testing News Mode Integration...\n")

# Wait for server to be ready
time.sleep(2)

# 1. Check settings
print("1. Checking settings...")
try:
    response = requests.get(f"{BASE_URL}/api/settings", timeout=5)
    settings = response.json()
    print(f"   ✓ Available modes: {settings['available_modes']}")
    print(f"   ✓ News configured: {settings.get('news_configured', False)}")
    if settings.get('news_intervals'):
        print(f"   ✓ Intervals: {list(settings['news_intervals'].keys())}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# 2. Single news analysis
print("\n2. Running single news analysis (1min interval)...")
try:
    response = requests.post(f"{BASE_URL}/api/analyze", json={
        "mode": "news",
        "interval": "1min"
    }, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Score: {result.get('score', 'N/A')}")
        print(f"   ✓ Classification: {result.get('classification', 'N/A')}")
        print(f"   ✓ Interval: {result.get('interval', 'N/A')}")
    else:
        print(f"   ❌ Status: {response.status_code}")
        print(f"   ❌ Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Get news score
print("\n3. Getting latest news score...")
try:
    response = requests.get(f"{BASE_URL}/api/score?mode=news", timeout=5)
    if response.status_code == 200:
        score = response.json()
        print(f"   ✓ Score: {score.get('score', 'N/A')}")
        print(f"   ✓ Sample size: {score.get('sample_size', 0)} articles")
    else:
        print(f"   ℹ️ Status: {response.status_code} (may not have data yet)")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ News Mode API Integration Complete!")
print("\nAvailable intervals: 30s, 1min, 2min, 5min, 10min, 30min, 1hr")
print("\nTo start continuous mode:")
print("  POST /api/news/control with {\"action\": \"start\", \"interval\": \"1min\"}")
print("\nTo stop:")
print("  POST /api/news/control with {\"action\": \"stop\"}")
