#!/usr/bin/env python3

from app import app, download_dir, is_safe_path
import os
import zipfile
import io
import urllib.parse

def test_backend_directly():
    print("🔧 Testing ZIP Functionality Directly")
    print("=" * 40)
    
    # Test the is_safe_path function
    print("\n🔒 Test 1: Path Security Check")
    print("-" * 30)
    
    test_folder = "Ballerina (2025) [1080p] [WEBRip] [x265] [10bit] [5.1] [YTS.MX]"
    print(f"Testing path: {test_folder}")
    print(f"is_safe_path result: {is_safe_path(test_folder)}")
    
    # Test folder existence
    print("\n📁 Test 2: Folder Existence")
    print("-" * 30)
    
    folder_path = os.path.join(download_dir, test_folder)
    print(f"Download dir: {download_dir}")
    print(f"Full folder path: {folder_path}")
    print(f"Folder exists: {os.path.exists(folder_path)}")
    print(f"Is directory: {os.path.isdir(folder_path)}")
    
    if os.path.exists(folder_path):
        print("📄 Files in folder:")
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                print(f"  - {file} ({file_size} bytes)")
    
    # Test ZIP creation manually
    print("\n📦 Test 3: ZIP Creation")
    print("-" * 25)
    
    try:
        # Create ZIP file in memory
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            file_count = 0
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    print(f"  Adding: {file_path} as {arcname}")
                    zipf.write(file_path, arcname)
                    file_count += 1
        
        memory_file.seek(0)
        zip_content = memory_file.getvalue()
        
        print(f"✅ ZIP created successfully!")
        print(f"📊 Files added: {file_count}")
        print(f"📊 ZIP size: {len(zip_content)} bytes")
        
        # Save and verify
        test_zip_path = "test_direct.zip"
        with open(test_zip_path, 'wb') as f:
            f.write(zip_content)
        
        print(f"💾 ZIP saved as: {test_zip_path}")
        
        # Verify ZIP contents
        with zipfile.ZipFile(test_zip_path, 'r') as zf:
            zip_files = zf.namelist()
            print(f"📋 ZIP contents: {zip_files}")
        
        os.remove(test_zip_path)
        print(f"🗑️  Cleaned up: {test_zip_path}")
        
    except Exception as e:
        print(f"❌ Error creating ZIP: {e}")
        import traceback
        traceback.print_exc()
    
    # Test URL encoding
    print("\n🔗 Test 4: URL Encoding")
    print("-" * 25)
    
    encoded = urllib.parse.quote(test_folder)
    decoded = urllib.parse.unquote(encoded)
    print(f"Original: {test_folder}")
    print(f"Encoded: {encoded}")
    print(f"Decoded: {decoded}")
    print(f"Roundtrip OK: {decoded == test_folder}")
    
    # Test Flask route simulation
    print("\n🌐 Test 5: Flask Route Simulation")
    print("-" * 35)
    
    with app.test_client() as client:
        # Test folder download
        encoded_folder = urllib.parse.quote(test_folder)
        response = client.get(f'/api/folder/download/{encoded_folder}')
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Content Type: {response.content_type}")
        print(f"📊 Content Length: {len(response.data)} bytes")
        
        if response.status_code == 200:
            print("✅ Folder download endpoint working!")
            
            # Verify it's a valid ZIP
            zip_data = io.BytesIO(response.data)
            try:
                with zipfile.ZipFile(zip_data, 'r') as zf:
                    files_in_zip = zf.namelist()
                    print(f"📦 Files in response ZIP: {files_in_zip}")
                print("✅ ZIP file is valid!")
            except Exception as e:
                print(f"❌ Invalid ZIP file: {e}")
        else:
            print(f"❌ Request failed: {response.get_data(as_text=True)}")
    
    print("\n🏁 Direct Test Complete!")

if __name__ == "__main__":
    test_backend_directly()
