#!/bin/bash

echo "========================================="
echo "🔍 AI Voice Server Diagnostics"
echo "========================================="
echo ""

echo "1️⃣ Docker containers status:"
docker compose ps
echo ""

echo "2️⃣ Frontend container logs (last 30 lines):"
docker compose logs --tail=30 frontend
echo ""

echo "3️⃣ Backend container logs (last 20 lines):"
docker compose logs --tail=20 backend
echo ""

echo "4️⃣ Check if frontend is built correctly:"
echo "   Inspecting built files in frontend container..."
docker compose exec frontend ls -la /usr/share/nginx/html/assets/*.js | head -5
echo ""

echo "5️⃣ Check nginx configuration:"
docker compose exec frontend cat /etc/nginx/conf.d/default.conf | grep -A 5 "location /api"
echo ""

echo "6️⃣ Test API endpoint from backend:"
docker compose exec backend curl -s http://localhost:8000/api/health
echo ""

echo "7️⃣ Test API endpoint through nginx (from frontend container):"
docker compose exec frontend wget -qO- http://backend:8000/api/health
echo ""

echo "8️⃣ Check environment variables in frontend build:"
echo "   (This will show if VITE_API_URL was set during build)"
docker compose exec frontend sh -c 'cat /usr/share/nginx/html/index.html | grep -o "VITE_API_URL" || echo "Not found in HTML"'
echo ""

echo "9️⃣ Network connectivity:"
echo "   Can frontend reach backend?"
docker compose exec frontend ping -c 2 backend
echo ""

echo "========================================="
echo "✅ Diagnostics complete!"
echo "========================================="
echo ""
echo "📋 Please share this output for analysis"
