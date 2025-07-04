#!/usr/bin/env python3

from app import app, download_dir, is_safe_path
import os
import zipfile
import io
import urllib.parse

def test_with_small_folder():
    print("🔧 Testing ZIP Functionality with Small Test Folder")
    print("=" * 50)
    
    test_folder = "test-folder"
    
    # Test the path security
    print(f"\n🔒 Path Security: is_safe_path('{test_folder}') = {is_safe_path(test_folder)}")
    
    folder_path = os.path.join(download_dir, test_folder)
    print(f"📁 Folder path: {folder_path}")
    print(f"📁 Folder exists: {os.path.exists(folder_path)}")
    
    if os.path.exists(folder_path):
        print("📄 Files in test folder:")
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                print(f"  - {file} ({file_size} bytes)")
    
    # Test Flask route with small folder
    print(f"\n🌐 Testing Flask route with small folder")
    
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
            try:
                zip_data = io.BytesIO(response.data)
                with zipfile.ZipFile(zip_data, 'r') as zf:
                    files_in_zip = zf.namelist()
                    print(f"📦 Files in response ZIP: {files_in_zip}")
                    
                    # Extract and verify content
                    for file_name in files_in_zip:
                        content = zf.read(file_name).decode('utf-8')
                        print(f"  📄 {file_name}: '{content.strip()}'")
                        
                print("✅ ZIP file is valid and contains expected content!")
            except Exception as e:
                print(f"❌ Invalid ZIP file: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ Request failed: {response.get_data(as_text=True)}")
    
    # Test files API
    print(f"\n📄 Testing Files API")
    
    with app.test_client() as client:
        response = client.get('/api/files')
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            if data.get('success'):
                files = data.get('files', [])
                test_files = [f for f in files if f['folder'] == 'test-folder']
                print(f"✅ Found {len(test_files)} test files")
                
                if test_files:
                    # Test selected files download
                    selected_files = [f['path'] for f in test_files]
                    
                    response = client.post('/api/files/download/selected', 
                                         json={'files': selected_files})
                    
                    print(f"📊 Selected download status: {response.status_code}")
                    print(f"📊 Selected download size: {len(response.data)} bytes")
                    
                    if response.status_code == 200:
                        try:
                            zip_data = io.BytesIO(response.data)
                            with zipfile.ZipFile(zip_data, 'r') as zf:
                                files_in_zip = zf.namelist()
                                print(f"📦 Selected files ZIP contents: {files_in_zip}")
                            print("✅ Selected files download working!")
                        except Exception as e:
                            print(f"❌ Invalid selected files ZIP: {e}")
                    else:
                        print(f"❌ Selected files download failed: {response.get_data(as_text=True)}")
            else:
                print(f"❌ Files API error: {data.get('message')}")
        else:
            print(f"❌ Files API failed: {response.get_data(as_text=True)}")
    
    print("\n🏁 Test Complete!")

if __name__ == "__main__":
    test_with_small_folder()
