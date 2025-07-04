from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import libtorrent as lt
import threading
import time
import os
import tempfile
import json
from datetime import datetime
import hashlib
import shutil
import urllib.parse
import mimetypes
from werkzeug.utils import secure_filename
import zipfile
import io

app = Flask(__name__)
CORS(app)

# Global session and torrents storage
session = lt.session()
torrents = {}
download_dir = os.path.join(os.getcwd(), 'downloads')

# Create downloads directory if it doesn't exist
os.makedirs(download_dir, exist_ok=True)

# Configure session with optimized settings for cloud deployment
session.listen_on(6881, 6891)

# Apply high-performance settings for better speeds
settings = lt.session_settings()

# Connection settings
settings.connections_limit = 500
settings.connections_limit_per_torrent = 100
settings.max_failcount = 3
settings.max_peer_recv_buffer_size = 1024 * 1024  # 1MB
settings.max_peer_send_buffer_size = 1024 * 1024  # 1MB

# Upload/Download rate limits (0 = unlimited, adjust as needed)
settings.download_rate_limit = 0  # Unlimited download
settings.upload_rate_limit = 0    # Unlimited upload (be careful with this)

# DHT and peer exchange settings
settings.enable_dht = True
settings.enable_lsd = True  # Local Service Discovery
settings.enable_upnp = False  # Disable UPnP on cloud servers
settings.enable_natpmp = False  # Disable NAT-PMP on cloud servers

# Choking algorithm (for better performance)
settings.choking_algorithm = lt.choking_algorithm_t.rate_based_choker

# Disk cache settings
settings.cache_size = 512  # 512 MB cache
settings.cache_expiry = 60

# Tracker settings
settings.tracker_completion_timeout = 30
settings.tracker_receive_timeout = 10
settings.stop_tracker_timeout = 5
settings.announce_to_all_trackers = True
settings.announce_to_all_tiers = True

# Apply settings
session.set_settings(settings)

# Add DHT router nodes for better peer discovery
session.add_dht_router("router.bittorrent.com", 6881)
session.add_dht_router("dht.transmissionbt.com", 6881)
session.add_dht_router("router.utorrent.com", 6881)

def get_storage_info():
    """Get storage information for the downloads directory"""
    try:
        # Get disk usage statistics
        total, used, free = shutil.disk_usage(download_dir)
        
        # Calculate downloaded content size
        downloaded_size = 0
        for root, dirs, files in os.walk(download_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    downloaded_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    continue
        
        return {
            'total_storage': total,
            'free_storage': free,
            'used_storage': used,
            'downloaded_content': downloaded_size,
            'total_storage_gb': round(total / (1024**3), 2),
            'free_storage_gb': round(free / (1024**3), 2),
            'used_storage_gb': round(used / (1024**3), 2),
            'downloaded_content_gb': round(downloaded_size / (1024**3), 2),
            'usage_percentage': round((used / total) * 100, 2)
        }
    except Exception as e:
        return {
            'error': str(e),
            'total_storage': 0,
            'free_storage': 0,
            'used_storage': 0,
            'downloaded_content': 0,
            'total_storage_gb': 0,
            'free_storage_gb': 0,
            'used_storage_gb': 0,
            'downloaded_content_gb': 0,
            'usage_percentage': 0
        }

class TorrentManager:
    def __init__(self):
        self.active_torrents = {}
    
    def add_torrent(self, torrent_data, is_magnet=False):
        try:
            if is_magnet:
                # Handle magnet link
                params = {
                    'save_path': download_dir,
                    'storage_mode': lt.storage_mode_t.storage_mode_sparse,
                }
                handle = lt.add_magnet_uri(session, torrent_data, params)
            else:
                # Handle .torrent file
                info = lt.torrent_info(torrent_data)
                params = {
                    'ti': info,
                    'save_path': download_dir,
                    'storage_mode': lt.storage_mode_t.storage_mode_sparse,
                }
                handle = session.add_torrent(params)
            
            # Generate unique ID for this torrent
            torrent_id = hashlib.md5(str(handle.info_hash()).encode()).hexdigest()[:8]
            
            self.active_torrents[torrent_id] = {
                'handle': handle,
                'added_time': datetime.now(),
                'name': '',
                'size': 0,
                'progress': 0,
                'download_rate': 0,
                'upload_rate': 0,
                'status': 'downloading',
                'peers': 0,
                'seeds': 0
            }
            
            return torrent_id, True, "Torrent added successfully"
        except Exception as e:
            return None, False, str(e)
    
    def get_torrent_status(self, torrent_id=None):
        if torrent_id:
            if torrent_id in self.active_torrents:
                return self._get_single_torrent_status(torrent_id)
            return None
        else:
            return {tid: self._get_single_torrent_status(tid) for tid in self.active_torrents}
    
    def _get_single_torrent_status(self, torrent_id):
        torrent_data = self.active_torrents[torrent_id]
        handle = torrent_data['handle']
        status = handle.status()
        
        # Update torrent information
        if handle.has_metadata():
            torrent_data['name'] = handle.name()
            torrent_data['size'] = status.total_wanted
        
        torrent_data['progress'] = status.progress * 100
        torrent_data['download_rate'] = status.download_rate / 1024  # KB/s
        torrent_data['upload_rate'] = status.upload_rate / 1024  # KB/s
        torrent_data['peers'] = status.num_peers
        torrent_data['seeds'] = status.num_seeds
        
        # Determine status
        if status.is_seeding:
            torrent_data['status'] = 'seeding'
        elif status.is_finished:
            torrent_data['status'] = 'completed'
        elif status.paused:
            torrent_data['status'] = 'paused'
        else:
            torrent_data['status'] = 'downloading'
        
        # Get download info for completed torrents
        download_files = []
        if status.is_finished and handle.has_metadata():
            try:
                torrent_info = handle.get_torrent_info()
                save_path = handle.save_path()
                
                if torrent_info.num_files() == 1:
                    # Single file torrent
                    file_path = torrent_info.files().file_path(0)
                    full_path = os.path.join(save_path, file_path)
                    if os.path.exists(full_path):
                        download_files.append({
                            'name': os.path.basename(file_path),
                            'path': file_path,
                            'size': torrent_info.files().file_size(0)
                        })
                else:
                    # Multi-file torrent
                    for i in range(torrent_info.num_files()):
                        file_path = torrent_info.files().file_path(i)
                        full_path = os.path.join(save_path, file_path)
                        if os.path.exists(full_path):
                            download_files.append({
                                'name': os.path.basename(file_path),
                                'path': file_path,
                                'size': torrent_info.files().file_size(i)
                            })
            except Exception as e:
                print(f"Error getting download files for torrent {torrent_id}: {e}")
        
        return {
            'id': torrent_id,
            'name': torrent_data['name'] or f"Torrent {torrent_id}",
            'size': torrent_data['size'],
            'progress': round(torrent_data['progress'], 2),
            'download_rate': round(torrent_data['download_rate'], 2),
            'upload_rate': round(torrent_data['upload_rate'], 2),
            'status': torrent_data['status'],
            'peers': torrent_data['peers'],
            'seeds': torrent_data['seeds'],
            'added_time': torrent_data['added_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'download_files': download_files
        }
    
    def pause_torrent(self, torrent_id):
        if torrent_id in self.active_torrents:
            self.active_torrents[torrent_id]['handle'].pause()
            return True
        return False
    
    def resume_torrent(self, torrent_id):
        if torrent_id in self.active_torrents:
            self.active_torrents[torrent_id]['handle'].resume()
            return True
        return False
    
    def remove_torrent(self, torrent_id, delete_files=False):
        if torrent_id in self.active_torrents:
            handle = self.active_torrents[torrent_id]['handle']
            
            # Get file path before removing torrent
            if delete_files and handle.has_metadata():
                try:
                    # Get the torrent info and save path
                    torrent_info = handle.get_torrent_info()
                    save_path = handle.save_path()
                    
                    # Remove from session first
                    session.remove_torrent(handle)
                    
                    # Delete the actual files
                    if torrent_info.num_files() == 1:
                        # Single file torrent
                        file_path = os.path.join(save_path, torrent_info.files().file_path(0))
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    else:
                        # Multi-file torrent - remove the entire folder
                        folder_path = os.path.join(save_path, torrent_info.name())
                        if os.path.exists(folder_path):
                            shutil.rmtree(folder_path)
                            
                except Exception as e:
                    print(f"Error deleting files for torrent {torrent_id}: {e}")
            else:
                # Just remove from session without deleting files
                session.remove_torrent(handle)
            
            del self.active_torrents[torrent_id]
            return True
        return False

def get_downloaded_files():
    """Get a list of all downloaded files and folders"""
    files_list = []
    
    try:
        for root, dirs, files in os.walk(download_dir):
            # Get relative path from downloads directory
            rel_path = os.path.relpath(root, download_dir)
            if rel_path == '.':
                rel_path = ''
            
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Get file extension and determine type
                _, ext = os.path.splitext(file)
                mime_type, _ = mimetypes.guess_type(file)
                
                file_info = {
                    'name': file,
                    'path': os.path.join(rel_path, file).replace('\\', '/') if rel_path else file,
                    'size': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'modified': file_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'extension': ext.lower(),
                    'mime_type': mime_type or 'application/octet-stream',
                    'folder': rel_path.replace('\\', '/') if rel_path else 'root'
                }
                files_list.append(file_info)
                
    except Exception as e:
        print(f"Error scanning downloads directory: {e}")
    
    return files_list

def is_safe_path(path):
    """Check if the path is safe and doesn't contain directory traversal attempts"""
    # Check for directory traversal patterns
    if '..' in path or path.startswith('/'):
        return False
    
    # Normalize the path and check if it's within the downloads directory
    full_path = os.path.join(download_dir, path)
    real_path = os.path.realpath(full_path)
    real_download_dir = os.path.realpath(download_dir)
    
    return real_path.startswith(real_download_dir)

# Initialize torrent manager
torrent_manager = TorrentManager()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-zip')
def test_zip():
    return render_template('test_zip.html')

@app.route('/api/add_torrent', methods=['POST'])
def add_torrent():
    try:
        # Check if it's a file upload (multipart/form-data)
        if 'torrent_file' in request.files:
            # Handle .torrent file upload
            file = request.files['torrent_file']
            if file and file.filename and file.filename.endswith('.torrent'):
                torrent_data = file.read()
                torrent_id, success, message = torrent_manager.add_torrent(torrent_data, is_magnet=False)
            else:
                return jsonify({'success': False, 'message': 'Invalid file format or no file selected'})
        elif request.is_json:
            # Handle JSON data (magnet link)
            data = request.get_json()
            if 'magnet_link' in data:
                magnet_link = data['magnet_link']
                torrent_id, success, message = torrent_manager.add_torrent(magnet_link, is_magnet=True)
            else:
                return jsonify({'success': False, 'message': 'No magnet link provided'})
        else:
            return jsonify({'success': False, 'message': 'No torrent data provided'})
        
        if success:
            return jsonify({'success': True, 'torrent_id': torrent_id, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/torrents', methods=['GET'])
def get_torrents():
    try:
        torrents = torrent_manager.get_torrent_status()
        return jsonify({'success': True, 'torrents': torrents})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/torrent/<torrent_id>', methods=['GET'])
def get_torrent(torrent_id):
    try:
        torrent = torrent_manager.get_torrent_status(torrent_id)
        if torrent:
            return jsonify({'success': True, 'torrent': torrent})
        else:
            return jsonify({'success': False, 'message': 'Torrent not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/torrent/<torrent_id>/pause', methods=['POST'])
def pause_torrent(torrent_id):
    try:
        success = torrent_manager.pause_torrent(torrent_id)
        if success:
            return jsonify({'success': True, 'message': 'Torrent paused'})
        else:
            return jsonify({'success': False, 'message': 'Torrent not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/torrent/<torrent_id>/resume', methods=['POST'])
def resume_torrent(torrent_id):
    try:
        success = torrent_manager.resume_torrent(torrent_id)
        if success:
            return jsonify({'success': True, 'message': 'Torrent resumed'})
        else:
            return jsonify({'success': False, 'message': 'Torrent not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/torrent/<torrent_id>/remove', methods=['DELETE'])
def remove_torrent(torrent_id):
    try:
        # Check if we should delete files too
        delete_files = request.args.get('delete_files', 'false').lower() == 'true'
        
        success = torrent_manager.remove_torrent(torrent_id, delete_files=delete_files)
        if success:
            message = 'Torrent and files removed' if delete_files else 'Torrent removed (files kept)'
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'Torrent not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/storage', methods=['GET'])
def get_storage():
    try:
        storage_info = get_storage_info()
        return jsonify({'success': True, 'storage': storage_info})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/files', methods=['GET'])
def get_files():
    """Get list of all downloaded files"""
    try:
        files = get_downloaded_files()
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download a specific file"""
    try:
        # Security check: ensure the path is safe
        if not is_safe_path(filename):
            return jsonify({'success': False, 'message': 'Invalid file path'}), 400
        
        file_path = os.path.join(download_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        # Get filename for download
        download_name = os.path.basename(filename)
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/file/info/<path:filename>')
def get_file_info(filename):
    """Get detailed information about a specific file"""
    try:
        # Security check: ensure the path is safe
        if not is_safe_path(filename):
            return jsonify({'success': False, 'message': 'Invalid file path'}), 400
        
        file_path = os.path.join(download_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        # Get file stats
        stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        file_info = {
            'name': os.path.basename(filename),
            'path': filename,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'size_gb': round(stat.st_size / (1024 * 1024 * 1024), 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            'mime_type': mime_type or 'application/octet-stream',
            'extension': os.path.splitext(filename)[1].lower(),
            'is_video': mime_type and mime_type.startswith('video/'),
            'is_audio': mime_type and mime_type.startswith('audio/'),
            'is_image': mime_type and mime_type.startswith('image/'),
            'is_archive': os.path.splitext(filename)[1].lower() in ['.zip', '.rar', '.7z', '.tar', '.gz'],
        }
        
        return jsonify({'success': True, 'file': file_info})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/folders')
def get_folders():
    """Get list of all download folders"""
    try:
        folders = []
        for item in os.listdir(download_dir):
            item_path = os.path.join(download_dir, item)
            if os.path.isdir(item_path):
                # Count files in folder
                file_count = 0
                total_size = 0
                for root, dirs, files in os.walk(item_path):
                    file_count += len(files)
                    for file in files:
                        try:
                            total_size += os.path.getsize(os.path.join(root, file))
                        except (OSError, IOError):
                            continue
                
                folder_info = {
                    'name': item,
                    'path': item,
                    'file_count': file_count,
                    'size': total_size,
                    'size_mb': round(total_size / (1024 * 1024), 2),
                    'size_gb': round(total_size / (1024 * 1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(os.path.getmtime(item_path)).strftime('%Y-%m-%d %H:%M:%S')
                }
                folders.append(folder_info)
        
        return jsonify({'success': True, 'folders': folders})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/file/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a specific file"""
    try:
        # Security check: ensure the path is safe
        if not is_safe_path(filename):
            return jsonify({'success': False, 'message': 'Invalid file path'}), 400
        
        file_path = os.path.join(download_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        # Check if it's a file (not a directory)
        if not os.path.isfile(file_path):
            return jsonify({'success': False, 'message': 'Path is not a file'}), 400
        
        # Delete the file
        os.remove(file_path)
        
        return jsonify({'success': True, 'message': f'File {os.path.basename(filename)} deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/folder/delete/<path:foldername>', methods=['DELETE'])
def delete_folder(foldername):
    """Delete a specific folder and all its contents"""
    try:
        # Security check: ensure the path is safe
        if not is_safe_path(foldername):
            return jsonify({'success': False, 'message': 'Invalid folder path'}), 400
        
        folder_path = os.path.join(download_dir, foldername)
        
        # Check if folder exists
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'message': 'Folder not found'}), 404
        
        # Check if it's a directory
        if not os.path.isdir(folder_path):
            return jsonify({'success': False, 'message': 'Path is not a folder'}), 400
        
        # Delete the folder and all its contents
        shutil.rmtree(folder_path)
        
        return jsonify({'success': True, 'message': f'Folder {foldername} deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/folder/download/<path:foldername>')
def download_folder_as_zip(foldername):
    """Download a folder as a ZIP file"""
    try:
        # URL decode the folder name
        import urllib.parse
        foldername = urllib.parse.unquote(foldername)
        
        # Security check: ensure the path is safe
        if not is_safe_path(foldername):
            return jsonify({'success': False, 'message': 'Invalid folder path'}), 400
        
        folder_path = os.path.join(download_dir, foldername)
        
        # Check if folder exists
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return jsonify({'success': False, 'message': 'Folder not found'}), 404
        
        # Create ZIP file in memory
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            # Walk through the folder and add all files
            file_count = 0
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Get relative path within the folder
                    arcname = os.path.relpath(file_path, folder_path)
                    try:
                        zipf.write(file_path, arcname)
                        file_count += 1
                    except Exception as e:
                        print(f"Warning: Could not add file {file_path} to ZIP: {e}")
        
        memory_file.seek(0)
        
        # Set the filename for download (sanitize the name)
        safe_folder_name = "".join(c for c in foldername if c.isalnum() or c in (' ', '-', '_')).strip()
        zip_filename = f"{safe_folder_name}.zip"
        
        return send_file(
            memory_file,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        print(f"Error in download_folder_as_zip: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to create ZIP file: {str(e)}'}), 500

@app.route('/api/files/download/selected', methods=['POST'])
def download_selected_files():
    """Download multiple selected files as a ZIP"""
    try:
        data = request.get_json()
        if not data or 'files' not in data:
            return jsonify({'success': False, 'message': 'No files specified'}), 400
        
        file_paths = data['files']
        if not file_paths:
            return jsonify({'success': False, 'message': 'No files specified'}), 400
        
        # Validate all file paths
        for file_path in file_paths:
            if not is_safe_path(file_path):
                return jsonify({'success': False, 'message': f'Invalid file path: {file_path}'}), 400
        
        # Create ZIP file in memory
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            file_count = 0
            for file_path in file_paths:
                full_path = os.path.join(download_dir, file_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    # Use just the filename for the archive to avoid deep folder structures
                    arcname = os.path.basename(file_path)
                    # If there are duplicate filenames, add folder prefix
                    if any(os.path.basename(fp) == arcname for fp in file_paths if fp != file_path):
                        arcname = file_path.replace('/', '_').replace('\\', '_')
                    try:
                        zipf.write(full_path, arcname)
                        file_count += 1
                    except Exception as e:
                        print(f"Warning: Could not add file {full_path} to ZIP: {e}")
        
        if file_count == 0:
            return jsonify({'success': False, 'message': 'No valid files found to zip'}), 400
        
        memory_file.seek(0)
        
        # Generate filename based on timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"selected_files_{timestamp}.zip"
        
        return send_file(
            memory_file,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        print(f"Error in download_selected_files: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to create ZIP file: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
