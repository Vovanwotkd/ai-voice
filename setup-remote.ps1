# PowerShell script to setup remote server
# Run this on your local Windows machine

$PASSWORD = "rvy&YekUkBs6"
$SERVER = "root@217.26.27.210"

Write-Host "=========================================" -ForegroundColor Green
Write-Host "🚀 Setting up AI Voice Bot on server" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Create setup commands
$SETUP_COMMANDS = @"
# Update system
echo '📦 Updating system...'
apt update && apt upgrade -y

# Install Docker
echo '🐳 Installing Docker...'
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
echo '📦 Installing Docker Compose...'
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-`$(uname -s)-`$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Nginx
echo '🌐 Installing Nginx...'
apt install -y nginx git ufw certbot python3-certbot-nginx

# Configure firewall
echo '🔒 Configuring firewall...'
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure Nginx
echo '⚙️  Configuring Nginx...'
cat > /etc/nginx/sites-available/voice.matrixcontrol.ru << 'NGINX_EOF'
server {
    listen 80;
    server_name voice.matrixcontrol.ru;
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    location / {
        return 301 https://`$server_name`$request_uri;
    }
}
server {
    listen 443 ssl http2;
    server_name voice.matrixcontrol.ru;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade `$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host `$host;
        proxy_cache_bypass `$http_upgrade;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
    }
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/voice.matrixcontrol.ru /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Get SSL certificate
echo '🔐 Setting up SSL...'
certbot --nginx -d voice.matrixcontrol.ru --non-interactive --agree-tos --email admin@matrixcontrol.ru --redirect

# Clone repository
echo '📂 Cloning repository...'
cd /root
git clone https://github.com/Vovanwotkd/ai-voice.git || (cd ai-voice && git pull)
cd ai-voice

# Create .env file
echo '⚙️  Creating .env file...'
DB_PASSWORD=`$(openssl rand -hex 16)
SECRET_KEY=`$(openssl rand -hex 32)

cat > .env << ENV_EOF
DB_USER=postgres
DB_PASSWORD=`$DB_PASSWORD
DATABASE_URL=postgresql://postgres:`$DB_PASSWORD@postgres:5432/hostess_db
REDIS_URL=redis://redis:6379/0
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-api03-REPLACE-WITH-YOUR-KEY
OPENAI_API_KEY=
YANDEX_API_KEY=
YANDEX_FOLDER_ID=
RESTAURANT_NAME=Гастрономия
RESTAURANT_PHONE=+7-495-123-45-67
RESTAURANT_ADDRESS=Москва, ул. Примерная, д. 1
SECRET_KEY=`$SECRET_KEY
DEBUG=false
CORS_ORIGINS=https://voice.matrixcontrol.ru,http://voice.matrixcontrol.ru
VITE_API_URL=https://voice.matrixcontrol.ru
ENV_EOF

chmod 600 .env

# Start application
echo '🚀 Starting application...'
docker-compose up -d --build

echo ''
echo '=========================================='
echo '✅ Setup completed!'
echo '=========================================='
echo ''
echo 'Your application is running at:'
echo '  🌐 https://voice.matrixcontrol.ru'
echo ''
echo 'IMPORTANT: Add your Anthropic API key:'
echo '  nano /root/ai-voice/.env'
echo '  docker-compose restart'
echo ''
"@

# Connect to server and run setup
Write-Host "Connecting to server and running setup..." -ForegroundColor Yellow
Write-Host ""

# Use plink if available, otherwise instruct to use PuTTY
$plinkPath = "C:\Program Files\PuTTY\plink.exe"
if (Test-Path $plinkPath) {
    # Execute with plink
    $SETUP_COMMANDS | & $plinkPath -batch -pw $PASSWORD $SERVER /bin/bash
} else {
    Write-Host "PuTTY plink not found. Using alternative method..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please copy and paste this command in a separate terminal:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "ssh $SERVER" -ForegroundColor White
    Write-Host ""
    Write-Host "Then run this script on the server:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host $SETUP_COMMANDS -ForegroundColor Gray
}
