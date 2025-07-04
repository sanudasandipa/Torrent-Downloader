#!/bin/bash

# Oracle Cloud BitTorrent Performance Optimization Script
# Run this script as root or with sudo privileges

echo "🚀 Optimizing Oracle Cloud instance for BitTorrent performance..."

# Update system
echo "📦 Updating system packages..."
apt-get update

# Install required packages
echo "📦 Installing optimization tools..."
apt-get install -y htop iotop nethogs sysstat

# Network optimizations
echo "🌐 Applying network optimizations..."

# Backup original sysctl.conf
cp /etc/sysctl.conf /etc/sysctl.conf.backup

# Apply network optimizations
cat >> /etc/sysctl.conf << EOF

# BitTorrent Performance Optimizations
# Increase network buffer sizes
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Increase maximum connections
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000

# TCP optimizations
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_sack = 1
net.ipv4.tcp_congestion_control = bbr

# Increase file descriptor limits
fs.file-max = 65535

EOF

# Apply changes
sysctl -p

# Configure systemd limits
echo "📁 Configuring file descriptor limits..."
cat > /etc/systemd/system.conf.d/limits.conf << EOF
[Manager]
DefaultLimitNOFILE=65535
EOF

# Configure user limits
cat >> /etc/security/limits.conf << EOF
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOF

# Configure firewall for BitTorrent
echo "🔥 Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 6881:6891/tcp
ufw allow 6881:6891/udp
ufw --force reload

# Oracle Cloud iptables rules (backup for Security Lists)
echo "🔒 Adding iptables rules for Oracle Cloud..."
iptables -I INPUT -p tcp --dport 80 -j ACCEPT
iptables -I INPUT -p tcp --dport 6881:6891 -j ACCEPT
iptables -I INPUT -p udp --dport 6881:6891 -j ACCEPT
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true

# Optimize Docker if installed
if command -v docker &> /dev/null; then
    echo "🐳 Optimizing Docker configuration..."
    
    # Create Docker daemon configuration
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "default-ulimits": {
        "nofile": {
            "name": "nofile",
            "hard": 65535,
            "soft": 65535
        }
    }
}
EOF
    
    systemctl restart docker
fi

echo "✅ Oracle Cloud optimization complete!"
echo ""
echo "🔄 Please reboot your instance for all changes to take effect:"
echo "   sudo reboot"
echo ""
echo "📋 After reboot, redeploy your torrent downloader with:"
echo "   docker-compose down && docker-compose up -d"
echo ""
echo "🌐 Don't forget to configure Oracle Cloud Security Lists:"
echo "   - TCP ports 6881-6891"
echo "   - UDP ports 6881-6891"
