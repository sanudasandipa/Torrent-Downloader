#!/usr/bin/env python3

import zipfile
import io
import os
from datetime import datetime

# Test folder path
download_dir = '/workspaces/Torrent-Downloader/downloads'
folder_name = 'Ballerina (2025) [1080p] [WEBRip] [x265] [10bit] [5.1] [YTS.MX]'
folder_path = os.path.join(download_dir, folder_name)

print(f"Testing ZIP creation for folder: {folder_path}")
print(f"Folder exists: {os.path.exists(folder_path)}")

if os.path.exists(folder_path):
    print("Files in folder:")
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            print(f"  - {file_path}")

    print("\nCreating ZIP file...")
    
    try:
        # Create ZIP file in memory
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the folder and add all files
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Get relative path within the folder
                    arcname = os.path.relpath(file_path, folder_path)
                    print(f"Adding to ZIP: {file_path} as {arcname}")
                    zipf.write(file_path, arcname)
        
        memory_file.seek(0)
        zip_content = memory_file.getvalue()
        
        print(f"✓ ZIP file created successfully!")
        print(f"✓ ZIP size: {len(zip_content)} bytes")
        
        # Save to disk for testing
        with open('test_folder_direct.zip', 'wb') as f:
            f.write(zip_content)
        print(f"✓ Test ZIP saved as test_folder_direct.zip")
        
    except Exception as e:
        print(f"✗ Error creating ZIP: {e}")
        import traceback
        traceback.print_exc()

else:
    print("✗ Folder does not exist!")
