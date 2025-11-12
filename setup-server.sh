#!/bin/bash

# AI Voice Hostess Bot - Automated Server Setup Script
# Usage: curl -sSL https://raw.githubusercontent.com/Vovanwotkd/ai-voice/main/setup-server.sh | bash

set -e

echo "=========================================="
echo "🚀 AI Voice Hostess Bot - Server Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="voice.matrixcontrol.ru"
EMAIL="admin@matrixcontrol.ru"  # Change this to your email for SSL
PROJECT_DIR="/root/ai-voice"

echo -e "${YELLOW}Domain:${NC} $DOMAIN"
echo -e "${YELLOW}Email:${NC} $EMAIL"
echo -e "${YELLOW}Project Directory:${NC} $PROJECT_DIR"
echo ""

# Step 1: Update system
echo -e "${YELLOW}[1/10]${NC} Updating system packages..."
apt update && apt upgrade -y
echo -e "${GREEN}✓${NC} System updated"
echo ""

# Step 2: Install dependencies
echo -e "${YELLOW}[2/10]${NC} Installing dependencies..."
apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    git \
    ufw
echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Step 3: Install Docker
echo -e "${YELLOW}[3/10]${NC} Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed"
fi
echo -e "${GREEN}✓${NC} Docker installed: $(docker --version)"
echo ""

# Step 4: Install Docker Compose
echo -e "${YELLOW}[4/10]${NC} Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi
echo -e "${GREEN}✓${NC} Docker Compose installed: $(docker-compose --version)"
echo ""

# Step 5: Install Nginx
echo -e "${YELLOW}[5/10]${NC} Installing Nginx..."
if ! command -v nginx &> /dev/null; then
    apt install -y nginx
    systemctl enable nginx
else
    echo "Nginx already installed"
fi
echo -e "${GREEN}✓${NC} Nginx installed"
echo ""

# Step 6: Install Certbot for SSL
echo -e "${YELLOW}[6/10]${NC} Installing Certbot..."
if ! command -v certbot &> /dev/null; then
    apt install -y certbot python3-certbot-nginx
else
    echo "Certbot already installed"
fi
echo -e "${GREEN}✓${NC} Certbot installed"
echo ""

# Step 7: Configure Nginx
echo -e "${YELLOW}[7/10]${NC} Configuring Nginx..."
cat > /etc/nginx/sites-available/$DOMAIN <<'NGINX_EOF'
server {
    listen 80;
    server_name voice.matrixcontrol.ru;

    # Redirect to HTTPS (will be configured by certbot)
    location / {
        return 301 https://$server_name$request_uri;
    }

    # Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}

server {
    listen 443 ssl http2;
    server_name voice.matrixcontrol.ru;

    # SSL certificates (will be configured by certbot)
    # ssl_certificate /etc/letsencrypt/live/voice.matrixcontrol.ru/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/voice.matrixcontrol.ru/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend (React)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for LLM requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support (if needed)
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX_EOF

# Enable site
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/$DOMAIN
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

echo -e "${GREEN}✓${NC} Nginx configured"
echo ""

# Step 8: Setup SSL with Let's Encrypt
echo -e "${YELLOW}[8/10]${NC} Setting up SSL certificate..."
echo -e "${YELLOW}Note:${NC} Make sure DNS for $DOMAIN points to this server!"
read -p "Press Enter to continue with SSL setup (or Ctrl+C to skip)..."

systemctl restart nginx

# Get SSL certificate
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect || {
    echo -e "${RED}⚠️  SSL setup failed. You can run it manually later:${NC}"
    echo "certbot --nginx -d $DOMAIN --email $EMAIL"
}

echo -e "${GREEN}✓${NC} SSL configured"
echo ""

# Step 9: Configure firewall
echo -e "${YELLOW}[9/10]${NC} Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
echo -e "${GREEN}✓${NC} Firewall configured"
echo ""

# Step 10: Clone repository and create .env
echo -e "${YELLOW}[10/10]${NC} Setting up application..."

if [ ! -d "$PROJECT_DIR" ]; then
    git clone https://github.com/Vovanwotkd/ai-voice.git $PROJECT_DIR
fi

cd $PROJECT_DIR

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}===========================================\n"
    echo -e "Creating .env file...\n"
    echo -e "You need to provide the following information:\n"
    echo -e "===========================================${NC}\n"

    # Read API key
    read -p "Enter your Anthropic API key (or press Enter to skip): " ANTHROPIC_KEY
    if [ -z "$ANTHROPIC_KEY" ]; then
        ANTHROPIC_KEY="sk-ant-api03-REPLACE-WITH-YOUR-KEY"
    fi

    # Generate random password and secret
    DB_PASSWORD=$(openssl rand -hex 16)
    SECRET_KEY=$(openssl rand -hex 32)

    cat > .env <<ENV_EOF
# ==========================================
# Database Configuration
# ==========================================
DB_USER=postgres
DB_PASSWORD=$DB_PASSWORD
DATABASE_URL=postgresql://postgres:$DB_PASSWORD@postgres:5432/hostess_db

# ==========================================
# Redis Configuration
# ==========================================
REDIS_URL=redis://redis:6379/0

# ==========================================
# LLM Provider Configuration
# ==========================================
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=$ANTHROPIC_KEY

# OpenAI (optional)
OPENAI_API_KEY=

# Yandex (optional)
YANDEX_API_KEY=
YANDEX_FOLDER_ID=

# ==========================================
# Restaurant Information
# ==========================================
RESTAURANT_NAME=Гастрономия
RESTAURANT_PHONE=+7-495-123-45-67
RESTAURANT_ADDRESS=Москва, ул. Примерная, д. 1

# ==========================================
# Application Configuration
# ==========================================
SECRET_KEY=$SECRET_KEY
DEBUG=false
CORS_ORIGINS=https://$DOMAIN,http://$DOMAIN,http://localhost:3000

# ==========================================
# Frontend Configuration
# ==========================================
VITE_API_URL=https://$DOMAIN
ENV_EOF

    chmod 600 .env

    echo -e "${GREEN}✓${NC} .env file created"
    echo ""

    if [ "$ANTHROPIC_KEY" = "sk-ant-api03-REPLACE-WITH-YOUR-KEY" ]; then
        echo -e "${RED}⚠️  WARNING: You need to add your real Anthropic API key!${NC}"
        echo "Edit the .env file: nano $PROJECT_DIR/.env"
        echo ""
    fi
fi

echo -e "${GREEN}✓${NC} Application setup complete"
echo ""

# Final message
echo "=========================================="
echo -e "${GREEN}✅ Server Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file if needed:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Deploy the application:"
echo "   cd $PROJECT_DIR"
echo "   docker-compose up -d --build"
echo ""
echo "3. Check status:"
echo "   docker-compose ps"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "Your site will be available at:"
echo "  🌐 https://$DOMAIN"
echo ""
echo "API Documentation:"
echo "  📚 https://$DOMAIN/api/docs"
echo ""
echo "Server info:"
echo "  • Nginx: $(nginx -v 2>&1 | grep -oP 'nginx/\K[0-9.]+')"
echo "  • Docker: $(docker --version | grep -oP 'version \K[0-9.]+')"
echo "  • Docker Compose: $(docker-compose --version | grep -oP 'version \K[0-9.]+')"
echo ""
