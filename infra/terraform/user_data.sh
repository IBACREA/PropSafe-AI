#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Install Python 3.11
apt-get install -y python3.11 python3.11-venv python3-pip

# Install Nginx
apt-get install -y nginx

# Install PostgreSQL client tools
apt-get install -y postgresql-client

# Create application directory
mkdir -p /opt/propsafe
chown ubuntu:ubuntu /opt/propsafe

# Enable and start Docker
systemctl enable docker
systemctl start docker

echo "Server setup completed!"
