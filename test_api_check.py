"""Quick test to check if NewsAPI is returning articles."""
import os
from dotenv import load_dotenv
load_dotenv()
import requests
from datetime import datetime, timedelta

key = os.getenv('NEWS_API_KEY')
print(f"API Key: {key[:8]}...{key[-4:]}" if key else "NO KEY FOUND")

url = "https://newsapi.org/v2/everything"

# Test 1: 24-hour window
from_time_24h = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
params = {
    "q": "crypto OR bitcoin OR ethereum",
    "sortBy": "publishedAt",
    "language": "en",
    "pageSize": 10,
    "from": from_time_24h,
    "apiKey": key
}

print(f"\n=== TEST 1: Last 24 hours ===")
print(f"from: {from_time_24h}")
r = requests.get(url, params=params, timeout=15)
data = r.json()
print(f"HTTP Status: {r.status_code}")
print(f"API Status: {data.get('status')}")
print(f"Total Results: {data.get('totalResults')}")
print(f"Message: {data.get('message', 'none')}")
print(f"Code: {data.get('code', 'none')}")

articles = data.get("articles", [])
print(f"Articles returned: {len(articles)}")
for i, a in enumerate(articles[:5]):
    title = a.get("title", "N/A")
    pub = a.get("publishedAt", "N/A")
    print(f"  [{i+1}] {pub} | {title[:90]}")

# Test 2: 1-hour window (what live mode uses)
from_time_1h = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
params["from"] = from_time_1h
print(f"\n=== TEST 2: Last 1 hour ===")
print(f"from: {from_time_1h}")
r2 = requests.get(url, params=params, timeout=15)
data2 = r2.json()
print(f"HTTP Status: {r2.status_code}")
print(f"API Status: {data2.get('status')}")
print(f"Total Results: {data2.get('totalResults')}")
print(f"Message: {data2.get('message', 'none')}")
articles2 = data2.get("articles", [])
print(f"Articles returned: {len(articles2)}")

# Test 3: 15-second window (what the background task fetches)
from_time_15s = (datetime.utcnow() - timedelta(seconds=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
params["from"] = from_time_15s
print(f"\n=== TEST 3: Last 15 seconds ===")
print(f"from: {from_time_15s}")
r3 = requests.get(url, params=params, timeout=15)
data3 = r3.json()
print(f"HTTP Status: {r3.status_code}")
print(f"API Status: {data3.get('status')}")
print(f"Total Results: {data3.get('totalResults')}")
print(f"Message: {data3.get('message', 'none')}")
articles3 = data3.get("articles", [])
print(f"Articles returned: {len(articles3)}")

# Test 4: No 'from' parameter at all
params_no_from = {
    "q": "crypto OR bitcoin OR ethereum",
    "sortBy": "publishedAt",
    "language": "en",
    "pageSize": 10,
    "apiKey": key
}
print(f"\n=== TEST 4: No 'from' filter (default) ===")
r4 = requests.get(url, params=params_no_from, timeout=15)
data4 = r4.json()
print(f"HTTP Status: {r4.status_code}")
print(f"API Status: {data4.get('status')}")
print(f"Total Results: {data4.get('totalResults')}")
print(f"Message: {data4.get('message', 'none')}")
articles4 = data4.get("articles", [])
print(f"Articles returned: {len(articles4)}")
for i, a in enumerate(articles4[:3]):
    title = a.get("title", "N/A")
    pub = a.get("publishedAt", "N/A")
    print(f"  [{i+1}] {pub} | {title[:90]}")

print("\n=== DIAGNOSIS ===")
if data.get("code") == "rateLimited":
    print("!! API IS RATE LIMITED - you've hit the daily limit")
elif data.get("code") == "apiKeyInvalid":
    print("!! API KEY IS INVALID")
elif data.get("status") == "ok" and data.get("totalResults", 0) > 0:
    print("API is working fine, articles are available")
elif data.get("status") == "ok" and data.get("totalResults", 0) == 0:
    print("API works but no articles match the query")
else:
    print(f"Unknown issue: {data}")
