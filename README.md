# Torrent Downloader

A modern web-based torrent downloader built with Python Flask backend and HTML/CSS/JavaScript frontend.

## Features

- **Modern Web Interface**: Beautiful, responsive design that works on desktop and mobile
- **Magnet Link Support**: Add torrents using magnet links
- **File Upload**: Upload .torrent files directly
- **Real-time Progress**: Live updates of download progress, speeds, and status
- **Torrent Management**: Pause, resume, and remove torrents
- **Detailed Information**: View file sizes, download/upload speeds, peer counts, and more

## Technology Stack

### Backend
- **Python Flask**: Web framework
- **libtorrent**: BitTorrent protocol implementation
- **Flask-CORS**: Cross-origin resource sharing

### Frontend
- **HTML5**: Modern semantic markup
- **CSS3**: Responsive design with gradients and animations
- **JavaScript**: Interactive functionality with async/await
- **Font Awesome**: Icons

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Quick Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Torrent-Downloader
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

3. **Start the application:**
   ```bash
   source venv/bin/activate
   python app.py
   ```

4. **Open your browser:**
   Navigate to `http://localhost:5000`

### Manual Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create downloads directory:**
   ```bash
   mkdir downloads
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

## Usage

### Adding Torrents

1. **Magnet Links:**
   - Paste a magnet link into the text field
   - Click "Add" button

2. **Torrent Files:**
   - Click "Choose File" button
   - Select a .torrent file from your computer
   - File will be automatically added

### Managing Torrents

- **View Progress**: Real-time progress bars and statistics
- **Pause/Resume**: Control download state
- **Remove**: Delete torrents from the list
- **Auto-refresh**: Interface updates every 2 seconds

## API Endpoints

### Add Torrent
- **POST** `/api/add_torrent`
- Body: `{"magnet_link": "magnet:?xt=urn:btih:..."}`
- Or form-data with `torrent_file`

### Get All Torrents
- **GET** `/api/torrents`
- Returns list of all active torrents

### Get Specific Torrent
- **GET** `/api/torrent/<torrent_id>`
- Returns details for specific torrent

### Pause Torrent
- **POST** `/api/torrent/<torrent_id>/pause`

### Resume Torrent
- **POST** `/api/torrent/<torrent_id>/resume`

### Remove Torrent
- **DELETE** `/api/torrent/<torrent_id>/remove`

## File Structure

```
Torrent-Downloader/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── setup.sh              # Setup script
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── style.css         # CSS styles
│   └── script.js         # JavaScript functionality
├── downloads/            # Downloaded files (created automatically)
└── README.md
```

## Configuration

### Download Location
Downloads are saved to the `downloads/` directory by default. You can modify this in `app.py`:

```python
download_dir = os.path.join(os.getcwd(), 'downloads')
```

### Port Configuration
The application runs on port 5000 by default. Change it in `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Security Considerations

⚠️ **Important**: This application is designed for local use and development purposes.

- The Flask app runs in debug mode by default
- No authentication is implemented
- CORS is enabled for all origins
- For production use, implement proper security measures

## Troubleshooting

### Common Issues

1. **libtorrent installation fails:**
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install python3-libtorrent
   
   # On macOS with Homebrew
   brew install libtorrent-rasterbar
   ```

2. **Permission errors:**
   - Ensure the downloads directory is writable
   - Run with appropriate permissions

3. **Port already in use:**
   - Change the port in `app.py`
   - Or kill the process using the port

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- **libtorrent**: For the BitTorrent protocol implementation
- **Flask**: For the lightweight web framework
- **Font Awesome**: For the beautiful icons

---

**Disclaimer**: This tool is for downloading legal content only. Users are responsible for ensuring they have the right to download any content through this application.