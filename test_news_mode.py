"""
Test News Mode Integration
===========================
This script demonstrates the news mode functionality with different time intervals.
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_news_mode():
    print("=" * 70)
    print("SENTRACK NEWS MODE TEST")
    print("=" * 70)
    
    # 1. Check settings
    print("\n1. Checking API settings...")
    response = requests.get(f"{BASE_URL}/api/settings")
    settings = response.json()
    
    print(f"   ✓ Available modes: {settings['available_modes']}")
    print(f"   ✓ News configured: {settings['news_configured']}")
    print(f"   ✓ Available intervals: {list(settings.get('news_intervals', {}).keys())}")
    
    if not settings['news_configured']:
        print("\n❌ News API not configured. Please add NEWS_API_KEY to .env file.")
        return
    
    # 2. Test single news analysis (manual trigger)
    print("\n2. Testing single news analysis (1min interval)...")
    response = requests.post(f"{BASE_URL}/api/analyze", json={
        "mode": "news",
        "interval": "1min"
    })
    result = response.json()
    
    if response.status_code == 200:
        print(f"   ✓ Score: {result['score']}")
        print(f"   ✓ Classification: {result['classification']}")
        print(f"   ✓ Source: {result['source']}")
        print(f"   ✓ Interval: {result.get('interval', 'N/A')}")
    else:
        print(f"   ❌ Error: {result.get('error', 'Unknown')}")
        return
    
    # 3. Start continuous news mode with 30s interval
    print("\n3. Starting continuous news mode (30s interval)...")
    response = requests.post(f"{BASE_URL}/api/news/control", json={
        "action": "start",
        "interval": "30s"
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ {result['message']}")
        print(f"   ✓ Interval: {result['interval']} ({result['interval_seconds']}s)")
        print(f"   ✓ Active: {result['active']}")
    else:
        print(f"   ❌ Error: {response.json().get('error', 'Unknown')}")
        return
    
    # 4. Monitor for 2 minutes (4 cycles of 30s)
    print("\n4. Monitoring news sentiment (will run for ~2 minutes)...")
    print("   Press Ctrl+C to stop early\n")
    
    try:
        for i in range(4):
            time.sleep(35)  # Wait slightly longer than interval
            
            # Get latest score
            response = requests.get(f"{BASE_URL}/api/score?mode=news")
            if response.status_code == 200:
                score_data = response.json()
                print(f"   Cycle {i+1}:")
                print(f"      Score: {score_data['score']:.2f} ({score_data['classification']})")
                print(f"      Sample size: {score_data['sample_size']} articles")
                print(f"      Timestamp: {score_data['timestamp'][:19]}")
                if score_data.get('message'):
                    print(f"      Message: {score_data['message']}")
            
    except KeyboardInterrupt:
        print("\n   Interrupted by user")
    
    # 5. Stop news mode
    print("\n5. Stopping news mode...")
    response = requests.post(f"{BASE_URL}/api/news/control", json={
        "action": "stop"
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ {result['message']}")
    
    # 6. Get history
    print("\n6. Retrieving news history...")
    response = requests.get(f"{BASE_URL}/api/history?mode=news")
    history_data = response.json()
    history = history_data.get('history', [])
    
    print(f"   ✓ Total analyses: {len(history)}")
    if history:
        print("\n   Recent scores:")
        for entry in history[-5:]:  # Last 5 entries
            print(f"      {entry['timestamp'][:19]}: {entry['score']:.2f} ({entry['classification']}) - {entry.get('sample_size', 0)} articles")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nNews Mode Features:")
    print("  ✓ Fetches crypto news from NewsAPI")
    print("  ✓ Analyzes sentiment at configurable intervals")
    print("  ✓ Averages sentiment over collection period")
    print("  ✓ Tracks history with timestamps")
    print("  ✓ Supports 7 intervals: 30s, 1min, 2min, 5min, 10min, 30min, 1hr")
    print("\nAPI Endpoints:")
    print("  POST /api/news/control - Start/stop news mode")
    print("  POST /api/analyze (mode=news) - Single news analysis")
    print("  GET /api/score?mode=news - Get latest news sentiment")
    print("  GET /api/history?mode=news - Get news history")


if __name__ == "__main__":
    try:
        test_news_mode()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to SenTrack server.")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
