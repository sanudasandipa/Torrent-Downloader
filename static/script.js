// Global variables
let refreshInterval;

// Utility function to escape HTML characters
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Utility function to format bytes into human readable format
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Utility function to format speed (bytes per second) into human readable format
function formatSpeed(bytesPerSecond) {
    if (bytesPerSecond === 0) return '0 B/s';
    
    const k = 1024;
    const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k));
    
    return parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    refreshTorrents();
    refreshStorage();
    initializeFileBrowser();
    startAutoRefresh();
});

// Refresh storage information
async function refreshStorage() {
    try {
        const response = await fetch('/api/storage');
        const result = await response.json();
        
        if (result.success) {
            displayStorageInfo(result.storage);
        } else {
            console.error('Failed to fetch storage info:', result.message);
        }
    } catch (error) {
        console.error('Error fetching storage info:', error.message);
    }
}

// Display storage information
function displayStorageInfo(storage) {
    // Update storage statistics
    document.getElementById('totalStorage').textContent = storage.total_storage_gb + ' GB';
    document.getElementById('usedStorage').textContent = storage.used_storage_gb + ' GB';
    document.getElementById('freeStorage').textContent = storage.free_storage_gb + ' GB';
    document.getElementById('downloadedContent').textContent = storage.downloaded_content_gb + ' GB';
    
    // Update storage percentage
    document.getElementById('storagePercentage').textContent = storage.usage_percentage + '%';
    
    // Update storage bar
    const storageBarFill = document.getElementById('storageBarFill');
    const storageBarDownloaded = document.getElementById('storageBarDownloaded');
    
    // Set the overall usage bar
    storageBarFill.style.width = storage.usage_percentage + '%';
    
    // Set the downloaded content bar (as a portion of total storage)
    const downloadedPercentage = (storage.downloaded_content / storage.total_storage) * 100;
    storageBarDownloaded.style.width = downloadedPercentage + '%';
    
    // Change color based on usage
    if (storage.usage_percentage > 90) {
        storageBarFill.style.background = '#dc3545'; // Red for critical
    } else if (storage.usage_percentage > 70) {
        storageBarFill.style.background = 'linear-gradient(90deg, #ffc107, #dc3545)'; // Yellow to red
    } else {
        storageBarFill.style.background = 'linear-gradient(90deg, #28a745, #ffc107)'; // Green to yellow
    }
}

// Toast notification system
function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    toast.innerHTML = `
        <div class="toast-header">
            <span class="toast-title">${title}</span>
            <button class="toast-close" onclick="removeToast(this)">&times;</button>
        </div>
        <div class="toast-message">${message}</div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            removeToast(toast.querySelector('.toast-close'));
        }
    }, 5000);
}

function removeToast(closeBtn) {
    const toast = closeBtn.closest('.toast');
    toast.style.animation = 'slideIn 0.3s ease reverse';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

// Add magnet link
async function addMagnetLink() {
    const magnetInput = document.getElementById('magnetLink');
    const magnetLink = magnetInput.value.trim();
    
    if (!magnetLink) {
        showToast('Error', 'Please enter a magnet link', 'error');
        return;
    }
    
    if (!magnetLink.startsWith('magnet:')) {
        showToast('Error', 'Invalid magnet link format', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/add_torrent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                magnet_link: magnetLink
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Success', 'Torrent added successfully!', 'success');
            magnetInput.value = '';
            refreshTorrents();
            refreshStorage();
        } else {
            showToast('Error', result.message, 'error');
        }
    } catch (error) {
        showToast('Error', 'Failed to add torrent: ' + error.message, 'error');
    }
}

// Add torrent file
async function addTorrentFile() {
    const fileInput = document.getElementById('torrentFile');
    const file = fileInput.files[0];
    
    if (!file) {
        return;
    }
    
    if (!file.name.endsWith('.torrent')) {
        showToast('Error', 'Please select a valid .torrent file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('torrent_file', file);
    
    try {
        const response = await fetch('/api/add_torrent', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Success', 'Torrent file added successfully!', 'success');
            fileInput.value = '';
            refreshTorrents();
            refreshStorage();
        } else {
            showToast('Error', result.message, 'error');
        }
    } catch (error) {
        showToast('Error', 'Failed to add torrent file: ' + error.message, 'error');
    }
}

// Refresh torrents list
async function refreshTorrents() {
    const container = document.getElementById('torrentsContainer');
    
    try {
        const response = await fetch('/api/torrents');
        const result = await response.json();
        
        if (result.success) {
            displayTorrents(result.torrents);
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error</h3>
                    <p>${result.message}</p>
                </div>
            `;
        }
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Connection Error</h3>
                <p>Failed to fetch torrents: ${error.message}</p>
            </div>
        `;
    }
}

// Display torrents
function displayTorrents(torrents) {
    const container = document.getElementById('torrentsContainer');
    
    if (!torrents || Object.keys(torrents).length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-cloud-download-alt"></i>
                <h3>No Active Torrents</h3>
                <p>Add a magnet link or upload a .torrent file to get started</p>
            </div>
        `;
        return;
    }
    
    const torrentsArray = Object.values(torrents);
    container.innerHTML = torrentsArray.map(torrent => createTorrentHTML(torrent)).join('');
}

// Create HTML for a single torrent
function createTorrentHTML(torrent) {
    const statusClass = `status-${torrent.status}`;
    const progressWidth = Math.max(0, Math.min(100, torrent.progress));
    
    // Create download files section for completed torrents
    let downloadFilesHtml = '';
    if ((torrent.status === 'completed' || torrent.status === 'seeding') && torrent.download_files && torrent.download_files.length > 0) {
        downloadFilesHtml = `
            <div class="download-files">
                <h4><i class="fas fa-download"></i> Available Downloads:</h4>
                <div class="download-files-list">
                    ${torrent.download_files.map(file => `
                        <div class="download-file-item">
                            <div class="download-file-info">
                                <span class="download-file-name">${escapeHtml(file.name)}</span>
                                <span class="download-file-size">${formatBytes(file.size)}</span>
                            </div>
                            <a href="/api/download/${encodeURIComponent(file.path)}" class="btn-download-small" title="Download ${escapeHtml(file.name)}">
                                <i class="fas fa-download"></i>
                            </a>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    return `
        <div class="torrent-item">
            <div class="torrent-header">
                <h3 class="torrent-name">${escapeHtml(torrent.name)}</h3>
                <span class="torrent-status ${statusClass}">${torrent.status}</span>
            </div>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progressWidth}%"></div>
                </div>
                <div class="progress-text">${progressWidth.toFixed(1)}% complete</div>
            </div>
            
            <div class="torrent-info">
                <div class="info-item">
                    <div class="info-label">Size</div>
                    <div class="info-value">${formatBytes(torrent.size)}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Download Speed</div>
                    <div class="info-value">${formatSpeed(torrent.download_rate)}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Upload Speed</div>
                    <div class="info-value">${formatSpeed(torrent.upload_rate)}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Peers</div>
                    <div class="info-value">${torrent.peers}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Seeds</div>
                    <div class="info-value">${torrent.seeds}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Added</div>
                    <div class="info-value">${torrent.added_time}</div>
                </div>
            </div>
            
            ${downloadFilesHtml}
            
            <div class="torrent-actions">
                ${torrent.status === 'paused' ? 
                    `<button class="action-btn btn-success" onclick="resumeTorrent('${torrent.id}')">
                        <i class="fas fa-play"></i> Resume
                    </button>` :
                    `<button class="action-btn btn-warning" onclick="pauseTorrent('${torrent.id}')">
                        <i class="fas fa-pause"></i> Pause
                    </button>`
                }
                <button class="action-btn btn-danger" onclick="removeTorrent('${torrent.id}')">
                    <i class="fas fa-trash"></i> Remove
                </button>
            </div>
        </div>
    `;
}

// Torrent control functions
async function pauseTorrent(torrentId) {
    try {
        const response = await fetch(`/api/torrent/${torrentId}/pause`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Success', 'Torrent paused', 'success');
            refreshTorrents();
            refreshStorage();
        } else {
            showToast('Error', result.message, 'error');
        }
    } catch (error) {
        showToast('Error', 'Failed to pause torrent: ' + error.message, 'error');
    }
}

async function resumeTorrent(torrentId) {
    try {
        const response = await fetch(`/api/torrent/${torrentId}/resume`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Success', 'Torrent resumed', 'success');
            refreshTorrents();
            refreshStorage();
        } else {
            showToast('Error', result.message, 'error');
        }
    } catch (error) {
        showToast('Error', 'Failed to resume torrent: ' + error.message, 'error');
    }
}

// Global variable to store torrent ID for modal
let currentTorrentIdForRemoval = null;

async function removeTorrent(torrentId) {
    currentTorrentIdForRemoval = torrentId;
    document.getElementById('confirmModal').style.display = 'block';
    
    // Add event listeners for modal buttons
    document.getElementById('removeOnly').onclick = () => performRemoval(false);
    document.getElementById('removeAndDelete').onclick = () => performRemoval(true);
}

async function performRemoval(deleteFiles) {
    if (!currentTorrentIdForRemoval) return;
    
    try {
        const url = `/api/torrent/${currentTorrentIdForRemoval}/remove?delete_files=${deleteFiles}`;
        const response = await fetch(url, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Success', result.message, 'success');
            refreshTorrents();
            refreshStorage();
        } else {
            showToast('Error', result.message, 'error');
        }
    } catch (error) {
        showToast('Error', 'Failed to remove torrent: ' + error.message, 'error');
    }
    
    closeModal();
}

function closeModal() {
    document.getElementById('confirmModal').style.display = 'none';
    currentTorrentIdForRemoval = null;
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('confirmModal');
    if (event.target === modal) {
        closeModal();
    }
}

// File Management Functions

// Initialize file browser
function initializeFileBrowser() {
    refreshFolders();
    refreshFiles();
}

// Show folder view
function showFolderView() {
    document.getElementById('folderTab').classList.add('active');
    document.getElementById('fileTab').classList.remove('active');
    document.getElementById('foldersContainer').classList.add('active');
    document.getElementById('filesContainer').classList.remove('active');
}

// Show file view
function showFileView() {
    document.getElementById('fileTab').classList.add('active');
    document.getElementById('folderTab').classList.remove('active');
    document.getElementById('filesContainer').classList.add('active');
    document.getElementById('foldersContainer').classList.remove('active');
}

// Toggle between list and grid view
function toggleFileView() {
    const toggleBtn = document.getElementById('viewToggle');
    const containers = document.querySelectorAll('.files-container');
    
    containers.forEach(container => {
        if (container.classList.contains('grid-view')) {
            container.classList.remove('grid-view');
            toggleBtn.innerHTML = '<i class="fas fa-th"></i> Grid View';
        } else {
            container.classList.add('grid-view');
            toggleBtn.innerHTML = '<i class="fas fa-th-list"></i> List View';
        }
    });
}

// Refresh folders
async function refreshFolders() {
    const container = document.getElementById('foldersContainer');
    container.innerHTML = '<div class="files-loading"><i class="fas fa-spinner fa-spin"></i> Loading folders...</div>';
    
    try {
        const response = await fetch('/api/folders');
        const result = await response.json();
        
        if (result.success) {
            displayFolders(result.folders);
        } else {
            container.innerHTML = `<div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error loading folders</h3>
                <p>${result.message}</p>
            </div>`;
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Error loading folders</h3>
            <p>${error.message}</p>
        </div>`;
    }
}

// Display folders
function displayFolders(folders) {
    const container = document.getElementById('foldersContainer');
    
    if (folders.length === 0) {
        container.innerHTML = `<div class="empty-state">
            <i class="fas fa-folder-open"></i>
            <h3>No folders found</h3>
            <p>No downloaded folders available yet</p>
        </div>`;
        return;
    }
    
    const foldersHtml = folders.map(folder => `
        <div class="folder-item" onclick="showFolderFiles('${folder.path}')">
            <div class="folder-icon">
                <i class="fas fa-folder"></i>
            </div>
            <div class="folder-info">
                <div class="folder-name">${folder.name}</div>
                <div class="folder-details">
                    ${folder.file_count} files • ${folder.size_mb} MB • Modified: ${folder.modified}
                </div>
            </div>
            <div class="folder-actions">
                <button class="btn-info" onclick="event.stopPropagation(); showFolderDetails('${folder.path}')" title="View details">
                    <i class="fas fa-info-circle"></i>
                </button>
                <button class="btn-primary" onclick="event.stopPropagation(); downloadFolderAsZip('${folder.path}')" title="Download as ZIP">
                    <i class="fas fa-file-archive"></i> ZIP
                </button>
                <button class="btn-danger" onclick="event.stopPropagation(); confirmDeleteFolder('${folder.path}', '${folder.name}')" title="Delete folder">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = foldersHtml;
}

// Refresh files
async function refreshFiles() {
    const container = document.getElementById('filesContainer');
    container.innerHTML = '<div class="files-loading"><i class="fas fa-spinner fa-spin"></i> Loading files...</div>';
    
    try {
        const response = await fetch('/api/files');
        const result = await response.json();
        
        if (result.success) {
            displayFiles(result.files);
        } else {
            container.innerHTML = `<div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error loading files</h3>
                <p>${result.message}</p>
            </div>`;
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Error loading files</h3>
            <p>${error.message}</p>
        </div>`;
    }
}

// Display files
function displayFiles(files) {
    const container = document.getElementById('filesContainer');
    
    if (files.length === 0) {
        container.innerHTML = `<div class="empty-state">
            <i class="fas fa-file"></i>
            <h3>No files found</h3>
            <p>No downloaded files available yet</p>
        </div>`;
        return;
    }
    
    // Add bulk actions header
    const bulkActionsHtml = `
        <div class="bulk-actions-header">
            <div class="bulk-controls">
                <label class="checkbox-container">
                    <input type="checkbox" id="selectAllFiles" onchange="toggleSelectAll()">
                    <span class="checkmark"></span>
                    Select All
                </label>
                <button id="bulkActionsBtn" class="btn-secondary" onclick="showBulkActions()" style="display: none;">
                    <i class="fas fa-cogs"></i> Actions (<span id="selectedCount">0</span>)
                </button>
            </div>
        </div>
    `;
    
    const filesHtml = files.map(file => `
        <div class="file-item">
            <div class="file-selector">
                <label class="checkbox-container">
                    <input type="checkbox" class="file-checkbox" value="${file.path}" onchange="updateBulkActions()">
                    <span class="checkmark"></span>
                </label>
            </div>
            <div class="file-icon ${getFileIconClass(file.extension)}">
                <i class="${getFileIcon(file.extension)}"></i>
            </div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-details">
                    ${file.size_mb} MB • ${file.folder} • Modified: ${file.modified}
                </div>
            </div>
            <div class="file-actions">
                <button class="btn-info" onclick="showFileDetails('${file.path}')" title="View details">
                    <i class="fas fa-info-circle"></i>
                </button>
                <a href="/api/download/${encodeURIComponent(file.path)}" class="btn-download" title="Download file">
                    <i class="fas fa-download"></i>
                </a>
                <button class="btn-danger" onclick="confirmDeleteFile('${file.path}', '${file.name}')" title="Delete file">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = bulkActionsHtml + filesHtml;
}

// Get file icon based on extension
function getFileIcon(extension) {
    const iconMap = {
        // Video
        '.mp4': 'fas fa-file-video',
        '.avi': 'fas fa-file-video',
        '.mkv': 'fas fa-file-video',
        '.mov': 'fas fa-file-video',
        '.wmv': 'fas fa-file-video',
        '.flv': 'fas fa-file-video',
        '.webm': 'fas fa-file-video',
        
        // Audio
        '.mp3': 'fas fa-file-audio',
        '.wav': 'fas fa-file-audio',
        '.flac': 'fas fa-file-audio',
        '.aac': 'fas fa-file-audio',
        '.ogg': 'fas fa-file-audio',
        '.wma': 'fas fa-file-audio',
        
        // Images
        '.jpg': 'fas fa-file-image',
        '.jpeg': 'fas fa-file-image',
        '.png': 'fas fa-file-image',
        '.gif': 'fas fa-file-image',
        '.bmp': 'fas fa-file-image',
        '.webp': 'fas fa-file-image',
        '.svg': 'fas fa-file-image',
        
        // Archives
        '.zip': 'fas fa-file-archive',
        '.rar': 'fas fa-file-archive',
        '.7z': 'fas fa-file-archive',
        '.tar': 'fas fa-file-archive',
        '.gz': 'fas fa-file-archive',
        
        // Documents
        '.pdf': 'fas fa-file-pdf',
        '.doc': 'fas fa-file-word',
        '.docx': 'fas fa-file-word',
        '.txt': 'fas fa-file-alt',
        '.srt': 'fas fa-closed-captioning',
        
        // Executables
        '.exe': 'fas fa-cog',
        '.msi': 'fas fa-cog',
        '.bin': 'fas fa-cog'
    };
    
    return iconMap[extension.toLowerCase()] || 'fas fa-file';
}

// Get file icon class for styling
function getFileIconClass(extension) {
    const ext = extension.toLowerCase();
    if (['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'].includes(ext)) return 'video';
    if (['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'].includes(ext)) return 'audio';
    if (['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'].includes(ext)) return 'image';
    if (['.zip', '.rar', '.7z', '.tar', '.gz'].includes(ext)) return 'archive';
    if (['.pdf', '.doc', '.docx', '.txt'].includes(ext)) return 'document';
    return 'default';
}

// Show folder files
async function showFolderFiles(folderPath) {
    try {
        const response = await fetch('/api/files');
        const result = await response.json();
        
        if (result.success) {
            // Filter files by folder
            const folderFiles = result.files.filter(file => 
                file.folder === folderPath || file.path.startsWith(folderPath + '/')
            );
            
            // Switch to file view and display filtered files
            showFileView();
            displayFiles(folderFiles);
            
            showToast('Success', `Showing ${folderFiles.length} files from ${folderPath}`, 'success');
        }
    } catch (error) {
        showToast('Error', 'Failed to load folder files: ' + error.message, 'error');
    }
}

// Show file details
async function showFileDetails(filePath) {
    try {
        const response = await fetch(`/api/file/info/${encodeURIComponent(filePath)}`);
        const result = await response.json();
        
        if (result.success) {
            const file = result.file;
            const details = `
                <strong>Name:</strong> ${file.name}<br>
                <strong>Size:</strong> ${file.size_mb} MB (${file.size_gb} GB)<br>
                <strong>Type:</strong> ${file.mime_type}<br>
                <strong>Modified:</strong> ${file.modified}<br>
                <strong>Created:</strong> ${file.created}<br>
                <strong>Path:</strong> ${file.path}
            `;
            
            showToast('File Details', details, 'info');
        } else {
            showToast('Error', 'Failed to get file details: ' + result.message, 'error');
        }
    } catch (error) {
        showToast('Error', 'Failed to get file details: ' + error.message, 'error');
    }
}

// Show folder details
function showFolderDetails(folderPath) {
    showToast('Folder Details', `Folder: ${folderPath}<br>Click to view all files in this folder`, 'info');
}

// Update auto refresh to include files
function startAutoRefresh() {
    refreshInterval = setInterval(() => {
        refreshTorrents();
        refreshStorage();
        // Refresh files every 30 seconds instead of every 5 seconds
        if (Date.now() % 30000 < 5000) {
            refreshFolders();
            refreshFiles();
        }
    }, 5000); // 5 second intervals
}

// Global variables for bulk actions
let selectedFiles = new Set();

// Bulk actions functionality
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllFiles');
    const fileCheckboxes = document.querySelectorAll('.file-checkbox');
    
    fileCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
        if (selectAllCheckbox.checked) {
            selectedFiles.add(checkbox.value);
        } else {
            selectedFiles.delete(checkbox.value);
        }
    });
    
    updateBulkActions();
}

function updateBulkActions() {
    const fileCheckboxes = document.querySelectorAll('.file-checkbox');
    const bulkActionsBtn = document.getElementById('bulkActionsBtn');
    const selectedCountSpan = document.getElementById('selectedCount');
    const selectAllCheckbox = document.getElementById('selectAllFiles');
    
    // Update selected files set
    selectedFiles.clear();
    fileCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            selectedFiles.add(checkbox.value);
        }
    });
    
    // Update UI
    const selectedCount = selectedFiles.size;
    if (selectedCount > 0) {
        bulkActionsBtn.style.display = 'inline-flex';
        selectedCountSpan.textContent = selectedCount;
    } else {
        bulkActionsBtn.style.display = 'none';
    }
    
    // Update select all checkbox state
    if (selectedCount === 0) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = false;
    } else if (selectedCount === fileCheckboxes.length) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = true;
    } else {
        selectAllCheckbox.indeterminate = true;
        selectAllCheckbox.checked = false;
    }
}

function showBulkActions() {
    if (selectedFiles.size === 0) return;
    
    const modal = document.getElementById('bulkModal');
    const message = document.getElementById('bulkModalMessage');
    message.textContent = `${selectedFiles.size} files selected. Choose an action:`;
    modal.style.display = 'flex';
}

function closeBulkModal() {
    document.getElementById('bulkModal').style.display = 'none';
}

// Download selected files as ZIP
async function downloadSelectedFiles() {
    if (selectedFiles.size === 0) {
        showToast('Warning', 'No files selected for download', 'warning');
        return;
    }
    
    try {
        showToast('Info', `Creating ZIP file with ${selectedFiles.size} selected files...`, 'info');
        
        const response = await fetch('/api/files/download/selected', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                files: Array.from(selectedFiles)
            })
        });
        
        if (response.ok) {
            // Create a blob from the response and trigger download
            const blob = await response.blob();
            
            // Check if we actually got a ZIP file
            if (blob.size === 0) {
                showToast('Error', 'ZIP file is empty. No valid files found.', 'error');
                return;
            }
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            
            // Get filename from response headers
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'selected_files.zip';
            if (contentDisposition) {
                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            closeBulkModal();
            showToast('Success', `Downloaded ${selectedFiles.size} files as ${filename}`, 'success');
            
            // Clear selection
            selectedFiles.clear();
            updateBulkActions();
            document.getElementById('selectAllFiles').checked = false;
            document.querySelectorAll('.file-checkbox').forEach(cb => cb.checked = false);
        } else {
            let errorMessage = 'Failed to download files';
            try {
                const result = await response.json();
                errorMessage = result.message || errorMessage;
            } catch (e) {
                // If response is not JSON, use default message
            }
            showToast('Error', errorMessage, 'error');
        }
    } catch (error) {
        console.error('Download selected files error:', error);
        showToast('Error', 'Network error while downloading files: ' + error.message, 'error');
    }
}

// Delete confirmation functions
function confirmDeleteFile(filePath, fileName) {
    const modal = document.getElementById('deleteModal');
    const title = document.getElementById('deleteModalTitle');
    const message = document.getElementById('deleteModalMessage');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    
    title.textContent = 'Delete File';
    message.textContent = `Are you sure you want to delete "${fileName}"?`;
    
    confirmBtn.onclick = () => deleteFile(filePath, fileName);
    modal.style.display = 'flex';
}

function confirmDeleteFolder(folderPath, folderName) {
    const modal = document.getElementById('deleteModal');
    const title = document.getElementById('deleteModalTitle');
    const message = document.getElementById('deleteModalMessage');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    
    title.textContent = 'Delete Folder';
    message.textContent = `Are you sure you want to delete the folder "${folderName}" and all its contents?`;
    
    confirmBtn.onclick = () => deleteFolder(folderPath, folderName);
    modal.style.display = 'flex';
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

// Delete file function
async function deleteFile(filePath, fileName) {
    try {
        const response = await fetch(`/api/file/delete/${encodeURIComponent(filePath)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Success', result.message, 'success');
            closeDeleteModal();
            refreshFiles();
            refreshStorage();
        } else {
            showToast('Error', 'Failed to delete file: ' + result.message, 'error');
        }
    } catch (error) {
        showToast('Error', 'Failed to delete file: ' + error.message, 'error');
    }
}

// Delete folder function
async function deleteFolder(folderPath, folderName) {
    try {
        const response = await fetch(`/api/folder/delete/${encodeURIComponent(folderPath)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Success', result.message, 'success');
            closeDeleteModal();
            refreshFolders();
            refreshStorage();
        } else {
            showToast('Error', 'Failed to delete folder: ' + result.message, 'error');
        }
    } catch (error) {
        showToast('Error', 'Failed to delete folder: ' + error.message, 'error');
    }
}

// Delete selected files
async function deleteSelectedFiles() {
    if (selectedFiles.size === 0) return;
    
    // Show confirmation for multiple files
    const modal = document.getElementById('deleteModal');
    const title = document.getElementById('deleteModalTitle');
    const message = document.getElementById('deleteModalMessage');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    
    title.textContent = 'Delete Multiple Files';
    message.textContent = `Are you sure you want to delete ${selectedFiles.size} selected files?`;
    
    confirmBtn.onclick = async () => {
        try {
            const deletePromises = Array.from(selectedFiles).map(filePath => 
                fetch(`/api/file/delete/${encodeURIComponent(filePath)}`, {
                    method: 'DELETE'
                })
            );
            
            const responses = await Promise.all(deletePromises);
            const results = await Promise.all(responses.map(r => r.json()));
            
            const successCount = results.filter(r => r.success).length;
            const failCount = results.length - successCount;
            
            if (successCount > 0) {
                showToast('Success', `${successCount} files deleted successfully`, 'success');
            }
            if (failCount > 0) {
                showToast('Warning', `${failCount} files failed to delete`, 'warning');
            }
            
            closeDeleteModal();
            closeBulkModal();
            refreshFiles();
            refreshStorage();
            
            // Clear selection
            selectedFiles.clear();
            updateBulkActions();
            document.getElementById('selectAllFiles').checked = false;
            document.querySelectorAll('.file-checkbox').forEach(cb => cb.checked = false);
            
        } catch (error) {
            showToast('Error', 'Failed to delete files: ' + error.message, 'error');
        }
    };
    
    closeBulkModal();
    modal.style.display = 'flex';
}

// Download folder as ZIP
async function downloadFolderAsZip(folderPath) {
    try {
        showToast('Info', 'Creating ZIP file...', 'info');
        
        const response = await fetch(`/api/folder/download/${encodeURIComponent(folderPath)}`);
        
        if (response.ok) {
            // Create a blob from the response and trigger download
            const blob = await response.blob();
            
            // Check if we actually got a ZIP file
            if (blob.size === 0) {
                showToast('Error', 'ZIP file is empty. No files found in folder.', 'error');
                return;
            }
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            
            // Get filename from response headers or create one
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `${folderPath}.zip`;
            if (contentDisposition) {
                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showToast('Success', `Folder downloaded as ${filename}`, 'success');
        } else {
            let errorMessage = 'Failed to download folder';
            try {
                const result = await response.json();
                errorMessage = result.message || errorMessage;
            } catch (e) {
                // If response is not JSON, use default message
            }
            showToast('Error', errorMessage, 'error');
        }
    } catch (error) {
        console.error('Download folder error:', error);
        showToast('Error', 'Network error while downloading folder: ' + error.message, 'error');
    }
}