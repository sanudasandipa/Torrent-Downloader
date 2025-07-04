#!/bin/bash

# Torrent Downloader Deployment Script
# For Oracle Ubuntu Server

set -e

echo "🚀 Starting Torrent Downloader deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up the repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    echo "✅ Docker installed successfully!"
    echo "⚠️  Please logout and login again for Docker permissions to take effect."
    echo "    Or run: newgrp docker"
else
    echo "✅ Docker is already installed"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed successfully!"
else
    echo "✅ Docker Compose is already installed"
fi

# Create downloads directory with proper permissions
echo "📁 Creating downloads directory..."
mkdir -p downloads
chmod 755 downloads

# Stop any existing container
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true
docker stop torrent-downloader 2>/dev/null || true
docker rm torrent-downloader 2>/dev/null || true

# Build and run the application
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting the application..."
docker-compose up -d

# Wait for the container to be ready
echo "⏳ Waiting for application to start..."
sleep 10

# Check if the container is running
if docker ps | grep -q torrent-downloader; then
    echo "✅ Torrent Downloader is running successfully!"
    echo "🌐 Access your application at: http://140.245.238.153"
    echo "📊 Container status:"
    docker ps | grep torrent-downloader
    echo ""
    echo "📋 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
    echo "🔄 To restart: docker-compose restart"
else
    echo "❌ Something went wrong. Checking logs..."
    docker-compose logs
fi

# Configure firewall if ufw is active
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    echo "🔥 Configuring firewall..."
    sudo ufw allow 80/tcp
    echo "✅ Port 80 opened in firewall"
fi

echo "🎉 Deployment completed!"
