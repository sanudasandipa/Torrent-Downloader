#!/usr/bin/env python3
"""
Test script for the torrent file upload fix
"""

import requests
import io

def test_file_upload():
    """Test the file upload functionality"""
    BASE_URL = "http://localhost:5001"
    
    # Create a mock .torrent file content (this won't be a real torrent)
    # In a real scenario, you'd use an actual .torrent file
    mock_torrent_content = b"d8:announce27:http://tracker.example.com/e"
    
    # Test file upload
    print("🧪 Testing torrent file upload...")
    
    try:
        # Create a file-like object
        file_data = {'torrent_file': ('test.torrent', io.BytesIO(mock_torrent_content), 'application/x-bittorrent')}
        
        response = requests.post(f"{BASE_URL}/api/add_torrent", files=file_data)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ File upload endpoint is working properly!")
            else:
                print(f"⚠️  Upload failed: {data.get('message')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_magnet_link():
    """Test the magnet link functionality"""
    BASE_URL = "http://localhost:5001"
    
    print("\n🧪 Testing magnet link...")
    
    # Test with a dummy magnet link (this won't actually download)
    magnet_data = {
        "magnet_link": "magnet:?xt=urn:btih:C9E15763F722F23E98A29DECDFAE341B98D53056&dn=Test&tr=http://tracker.example.com/announce"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/add_torrent", 
                               json=magnet_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Magnet link endpoint is working properly!")
            else:
                print(f"⚠️  Magnet link failed: {data.get('message')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing Torrent Downloader Upload Fix")
    print("=" * 50)
    
    test_file_upload()
    test_magnet_link()
    
    print("\n" + "=" * 50)
    print("✨ Test completed! The 415 error should be fixed.")
    print("🌐 You can now test the web interface at http://localhost:5001")
