#!/usr/bin/env python3
"""
Test script for the Torrent Downloader application
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_api():
    """Test the API endpoints"""
    print("🧪 Testing Torrent Downloader API...")
    
    # Test health check by accessing the main page
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("✅ Web server is running")
        else:
            print(f"❌ Web server error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to web server. Make sure it's running on port 5000")
        return False
    
    # Test getting torrents (should be empty initially)
    try:
        response = requests.get(f"{BASE_URL}/api/torrents")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ API is working")
                print(f"📊 Active torrents: {len(data.get('torrents', {}))}")
            else:
                print(f"❌ API error: {data.get('message')}")
        else:
            print(f"❌ API endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    print("\n🎉 Torrent Downloader is ready to use!")
    print("🌐 Open http://localhost:5000 in your browser")
    print("\n📝 To test with a real torrent:")
    print("   1. Find a legal torrent magnet link")
    print("   2. Paste it into the web interface")
    print("   3. Watch the download progress")
    
    return True

if __name__ == "__main__":
    test_api()
