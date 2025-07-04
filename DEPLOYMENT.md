# Torrent Downloader - Docker Deployment Guide

## 🚀 Quick Speed Fix for Oracle Cloud

If you're experiencing slow speeds, follow these steps:

1. **Stop current container:**
   ```bash
   docker stop torrent-downloader
   docker rm torrent-downloader
   ```

2. **Configure Oracle Cloud Security Lists (CRITICAL):**
   - Go to Oracle Cloud Console → Networking → Virtual Cloud Networks
   - Select your VCN → Security Lists → Default Security List
   - Add these **Ingress Rules**:
     - **Source**: 0.0.0.0/0, **Protocol**: TCP, **Port Range**: 6881-6891
     - **Source**: 0.0.0.0/0, **Protocol**: UDP, **Port Range**: 6881-6891

3. **Run optimized container:**
   ```bash
   docker run -d -p 80:80 -p 6881-6891:6881-6891/tcp -p 6881-6891:6881-6891/udp \
     --name torrent-downloader \
     -v $(pwd)/downloads:/app/downloads \
     --restart unless-stopped \
     --memory=2g --cpus=2 \
     torrent-downloader
   ```

4. **Configure firewall:**
   ```bash
   sudo ufw allow 6881:6891/tcp
   sudo ufw allow 6881:6891/udp
   sudo ufw reload
   ```

**Expected Result**: Download speeds should improve significantly within 5-10 minutes.

---

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
   
   # Run Oracle Cloud optimization first
   chmod +x optimize-oracle-cloud.sh
   sudo ./optimize-oracle-cloud.sh
   
   # Reboot to apply system optimizations
   sudo reboot
   ```

4. **After reboot, complete deployment:**
   ```bash
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

For Oracle Cloud, you need to configure both the instance firewall and Oracle Cloud Security Lists for optimal BitTorrent performance:

1. **Instance firewall:**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 6881:6891/tcp
   sudo ufw allow 6881:6891/udp
   sudo ufw enable
   ```

2. **Oracle Cloud Console Security Rules:**
   - Go to Networking > Virtual Cloud Networks
   - Select your VCN > Security Lists
   - Add these Ingress Rules:
     - **HTTP Access**: Source 0.0.0.0/0, Protocol TCP, Port 80
     - **BitTorrent TCP**: Source 0.0.0.0/0, Protocol TCP, Port Range 6881-6891
     - **BitTorrent UDP**: Source 0.0.0.0/0, Protocol UDP, Port Range 6881-6891

## Performance Optimization for Oracle Cloud

To improve download speeds on Oracle Cloud:

1. **System-level optimizations:**
   ```bash
   # Increase network buffer sizes
   echo 'net.core.rmem_default = 262144' | sudo tee -a /etc/sysctl.conf
   echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
   echo 'net.core.wmem_default = 262144' | sudo tee -a /etc/sysctl.conf
   echo 'net.core.wmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
   echo 'net.ipv4.tcp_rmem = 4096 87380 16777216' | sudo tee -a /etc/sysctl.conf
   echo 'net.ipv4.tcp_wmem = 4096 65536 16777216' | sudo tee -a /etc/sysctl.conf
   
   # Apply changes
   sudo sysctl -p
   ```

2. **Docker optimizations:**
   ```bash
   # Stop the container if running
   docker stop torrent-downloader
   
   # Run with optimized settings
   docker run -d -p 80:80 -p 6881-6891:6881-6891/tcp -p 6881-6891:6881-6891/udp \
     --name torrent-downloader \
     -v $(pwd)/downloads:/app/downloads \
     --restart unless-stopped \
     --memory=2g --cpus=2 \
     torrent-downloader
   ```

3. **Oracle Cloud Instance optimizations:**
   - Use a **VM.Standard.E4.Flex** instance with at least 2 CPUs and 8GB RAM
   - Ensure your instance has sufficient network bandwidth
   - Consider using Oracle Cloud's high-performance network if available

## Monitoring

- **Check container status:** `docker ps`
- **View logs:** `docker logs torrent-downloader`
- **Container stats:** `docker stats torrent-downloader`

## Troubleshooting

### General Issues
- **If port 80 requires sudo:** Run with `sudo docker-compose up -d`
- **Permission issues:** Check downloads folder permissions: `chmod 755 downloads`
- **Container won't start:** Check logs with `docker-compose logs`

### Speed and Performance Issues

If you're experiencing slow download speeds:

1. **Check Oracle Cloud Security Lists:**
   ```bash
   # Verify ports are open
   sudo netstat -tulpn | grep :6881
   sudo ufw status
   ```

2. **Monitor network traffic:**
   ```bash
   # Install monitoring tools
   sudo apt install nethogs iotop
   
   # Monitor network usage
   sudo nethogs
   ```

3. **Check torrent health:**
   - Ensure the torrent has sufficient seeders (seeds > 0)
   - Try different torrents to test if it's content-specific
   - Check if the torrent is properly connected to trackers

4. **Verify Oracle Cloud configuration:**
   - Ensure BitTorrent ports (6881-6891) are open in Security Lists
   - Check if your Oracle Cloud instance has bandwidth limitations
   - Consider upgrading to a higher performance instance shape

5. **Test connectivity:**
   ```bash
   # Test external connectivity
   curl -I http://httpbin.org/ip
   
   # Check DNS resolution
   nslookup tracker.openbittorrent.com
   ```

6. **Restart with verbose logging:**
   ```bash
   docker-compose down
   docker-compose up -d
   docker-compose logs -f
   ```

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
