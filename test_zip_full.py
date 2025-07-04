#!/usr/bin/env python3

import requests
import time
import urllib.parse
import os

# Test configuration
BASE_URL = "http://localhost:5001"
TEST_FOLDER = "Ballerina (2025) [1080p] [WEBRip] [x265] [10bit] [5.1] [YTS.MX]"

def test_zip_functionality():
    print("🔧 Testing Download as ZIP Functionality")
    print("=" * 50)
    
    # Test 1: Folder Download as ZIP
    print("\n📁 Test 1: Folder Download as ZIP")
    print("-" * 30)
    
    try:
        # URL encode the folder name
        encoded_folder = urllib.parse.quote(TEST_FOLDER)
        url = f"{BASE_URL}/api/folder/download/{encoded_folder}"
        
        print(f"📤 Requesting: {url}")
        response = requests.get(url, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Content Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"📊 Content Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Save the ZIP file
            zip_filename = f"test_folder_{int(time.time())}.zip"
            with open(zip_filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Success: ZIP file saved as {zip_filename}")
            
            # Verify the ZIP file
            import zipfile
            with zipfile.ZipFile(zip_filename, 'r') as zf:
                files_in_zip = zf.namelist()
                print(f"📦 Files in ZIP: {files_in_zip}")
                
            os.remove(zip_filename)
            print(f"🗑️  Cleaned up: {zip_filename}")
            
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get Files List
    print("\n📄 Test 2: Get Files List")
    print("-" * 25)
    
    try:
        url = f"{BASE_URL}/api/files"
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                files = data.get('files', [])
                print(f"✅ Found {len(files)} files")
                
                # Test selected files download
                if files:
                    print("\n📁 Test 3: Selected Files Download as ZIP")
                    print("-" * 40)
                    
                    # Select first file for testing
                    selected_files = [files[0]['path']]
                    
                    url = f"{BASE_URL}/api/files/download/selected"
                    payload = {"files": selected_files}
                    
                    print(f"📤 Requesting: {url}")
                    print(f"📦 Payload: {payload}")
                    
                    response = requests.post(url, json=payload, timeout=30)
                    
                    print(f"📊 Status Code: {response.status_code}")
                    print(f"📊 Content Type: {response.headers.get('Content-Type', 'Unknown')}")
                    print(f"📊 Content Length: {len(response.content)} bytes")
                    
                    if response.status_code == 200:
                        zip_filename = f"test_selected_{int(time.time())}.zip"
                        with open(zip_filename, 'wb') as f:
                            f.write(response.content)
                        
                        print(f"✅ Success: ZIP file saved as {zip_filename}")
                        
                        # Verify the ZIP file
                        import zipfile
                        with zipfile.ZipFile(zip_filename, 'r') as zf:
                            files_in_zip = zf.namelist()
                            print(f"📦 Files in ZIP: {files_in_zip}")
                            
                        os.remove(zip_filename)
                        print(f"🗑️  Cleaned up: {zip_filename}")
                        
                    else:
                        print(f"❌ Failed: {response.text}")
                else:
                    print("⚠️  No files found to test selected download")
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🏁 Test Complete!")

if __name__ == "__main__":
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    test_zip_functionality()
