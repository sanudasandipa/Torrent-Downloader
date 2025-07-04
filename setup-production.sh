#!/bin/bash

# Production deployment script for Oracle Cloud Ubuntu server
# Run this script as root or with sudo privileges

set -e

echo "🔧 Setting up production environment for Torrent Downloader..."

# Update system
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# Install required system packages
echo "📦 Installing system dependencies..."
apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Configure firewall for Oracle Cloud
echo "🔥 Configuring firewall..."
# Oracle Cloud uses iptables, so we'll configure both ufw and iptables
if command -v ufw &> /dev/null; then
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force reload
fi

# Also configure iptables directly for Oracle Cloud
iptables -I INPUT -p tcp --dport 80 -j ACCEPT
iptables -I INPUT -p tcp --dport 443 -j ACCEPT
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker ubuntu
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create application directory
APP_DIR="/opt/torrent-downloader"
echo "📁 Creating application directory at $APP_DIR..."
mkdir -p $APP_DIR
cd $APP_DIR

# Set proper permissions
chown -R ubuntu:ubuntu $APP_DIR

echo "✅ Production environment setup completed!"
echo "📋 Next steps:"
echo "1. Upload your application files to: $APP_DIR"
echo "2. Run: cd $APP_DIR && chmod +x deploy.sh && ./deploy.sh"
echo "3. Your app will be available at: http://140.245.238.153"
