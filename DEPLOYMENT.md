# Torrent Downloader - Docker Deployment Guide

## Quick Deployment on Oracle Ubuntu Server (140.245.238.153)

### Option 1: Automated Deployment

1. **Upload files to your server:**
   ```bash
   # On your local machine, compress and upload
   tar -czf torrent-downloader.tar.gz --exclude=downloads --exclude=__pycache__ .
   scp torrent-downloader.tar.gz ubuntu@140.245.238.153:~/
   ```

2. **SSH into your server:**
   ```bash
   ssh ubuntu@140.245.238.153
   ```

3. **Extract and deploy:**
   ```bash
   tar -xzf torrent-downloader.tar.gz
   cd torrent-downloader
   chmod +x deploy.sh
   ./deploy.sh
   ```

### Option 2: Manual Deployment

1. **SSH into your server:**
   ```bash
   ssh ubuntu@140.245.238.153
   ```

2. **Install Docker (if not installed):**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Upload your project files and build:**
   ```bash
   # After uploading your files
   docker build -t torrent-downloader .
   docker run -d -p 80:80 --name torrent-downloader \
     -v $(pwd)/downloads:/app/downloads \
     --restart unless-stopped \
     torrent-downloader
   ```

### Using Docker Compose (Recommended)

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart
docker-compose restart
```

## Access Your Application

- **Web Interface:** http://140.245.238.153
- **API Endpoint:** http://140.245.238.153/api/

## Firewall Configuration

For Oracle Cloud, you may need to configure both the instance firewall and Oracle Cloud Security Lists:

1. **Instance firewall:**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw enable
   ```

2. **Oracle Cloud Console:**
   - Go to Networking > Virtual Cloud Networks
   - Select your VCN > Security Lists
   - Add Ingress Rule: Source 0.0.0.0/0, Protocol TCP, Port 80

## Monitoring

- **Check container status:** `docker ps`
- **View logs:** `docker logs torrent-downloader`
- **Container stats:** `docker stats torrent-downloader`

## Troubleshooting

- **If port 80 requires sudo:** Run with `sudo docker-compose up -d`
- **Permission issues:** Check downloads folder permissions: `chmod 755 downloads`
- **Container won't start:** Check logs with `docker-compose logs`

## API Endpoints

Your deployed application will have these endpoints:

- `GET /` - Web interface
- `POST /api/add_torrent` - Add torrent (magnet link or file)
- `GET /api/torrents` - List all torrents
- `GET /api/files` - List downloaded files
- `GET /api/download/<filename>` - Download specific file
- `DELETE /api/torrent/<id>/remove` - Remove torrent

## Production Considerations

- Use a reverse proxy (nginx) for SSL/HTTPS
- Set up regular backups of the downloads folder
- Monitor disk space usage
- Consider using Docker volumes for persistent data
