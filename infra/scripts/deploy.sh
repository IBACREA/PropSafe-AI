#!/bin/bash
# Deployment script for PropSafe AI

set -e

echo "=========================================="
echo "PropSafe AI - Deployment Script"
echo "=========================================="

# Variables
APP_DIR="/opt/propsafe"
REPO_URL="https://github.com/yourusername/propsafe-ai.git" # Update with actual repo
DOMAIN="propsafeai.ibacrea.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    print_error "This script must be run as ubuntu user"
    exit 1
fi

# Step 1: Clone or update repository
print_status "Setting up application directory..."
if [ ! -d "$APP_DIR" ]; then
    print_status "Creating application directory..."
    sudo mkdir -p $APP_DIR
    sudo chown ubuntu:ubuntu $APP_DIR
fi

cd $APP_DIR

# Step 2: Copy files from local (assuming uploaded via SCP)
print_status "Files should be uploaded to $APP_DIR"
print_status "Run from local machine: scp -r -i ~/.ssh/propsafe_key . ubuntu@SERVER_IP:/opt/propsafe/"

# Step 3: Create necessary directories
print_status "Creating directories..."
mkdir -p logs data/clean ml/models

# Step 4: Set up environment variables
print_status "Setting up environment variables..."
if [ ! -f .env ]; then
    cat > .env << EOF
# Database Configuration
DB_PASSWORD=$(openssl rand -base64 32)
DATABASE_URL=postgresql://propsafe_user:\${DB_PASSWORD}@localhost:5432/propsafe_db

# Server Configuration
SERVER_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
DOMAIN=$DOMAIN

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# ML Model Configuration
MODEL_PATH=/app/models
ANOMALY_THRESHOLD=0.7

# Data Processing
DATA_PATH=/app/data
CHUNK_SIZE=10000

# Security
SECRET_KEY=$(openssl rand -base64 32)

# Feature Flags
ENABLE_CADASTRAL_LOOKUP=false
ENABLE_MARKET_VALUATION=false
EOF
    print_status "Environment file created"
else
    print_warning "Environment file already exists, skipping..."
fi

# Step 5: Build and start Docker containers
print_status "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

print_status "Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Step 6: Wait for database to be ready
print_status "Waiting for database to be ready..."
sleep 10

# Step 7: Run database migrations/initial load
print_status "Loading data into database..."
# This will be done after we create the load script

# Step 8: Configure Nginx (if not using Docker)
print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/propsafe << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/propsafe /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Step 9: Display status
print_status "Checking container status..."
docker-compose -f docker-compose.prod.yml ps

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo "Public IP: $PUBLIC_IP"
echo "Application URL: http://$PUBLIC_IP"
echo "Domain: http://$DOMAIN (configure DNS to point to $PUBLIC_IP)"
echo ""
echo "Next steps:"
echo "1. Point DNS record for $DOMAIN to $PUBLIC_IP"
echo "2. Upload ML models to $APP_DIR/ml/models/"
echo "3. Upload processed data to $APP_DIR/data/clean/"
echo "4. Run data load script: docker exec -it propsafe-backend python /app/scripts/load_data.py"
echo ""
echo "Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Restart: docker-compose -f docker-compose.prod.yml restart"
echo "  Stop: docker-compose -f docker-compose.prod.yml down"
echo "=========================================="
