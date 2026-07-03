#!/bin/bash
# =============================================================================
# KORRA AI - 502 Bad Gateway Fix Script for EC2
# =============================================================================
# This script diagnoses and fixes the 502 Bad Gateway error on EC2 deployment
# 
# Usage: chmod +x fix_502_on_ec2.sh && ./fix_502_on_ec2.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}KORRA AI - 502 Fix Script for EC2${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# =============================================================================
# PHASE 1: DIAGNOSIS
# =============================================================================
echo -e "${YELLOW}[1/6] DIAGNOSIS PHASE${NC}"
echo -e "${YELLOW}============================${NC}"

echo -e "${YELLOW}Checking Docker container status...${NC}"
if docker ps -a | grep -q korra-ai; then
    echo -e "${GREEN}✓ KORRA container exists${NC}"
    if docker ps | grep -q korra-ai; then
        echo -e "${GREEN}✓ KORRA container is RUNNING${NC}"
    else
        echo -e "${RED}✗ KORRA container is STOPPED${NC}"
    fi
else
    echo -e "${RED}✗ KORRA container does NOT exist${NC}"
fi
echo ""

echo -e "${YELLOW}Checking container logs...${NC}"
docker logs korra-ai --tail 20 || echo "No logs available"
echo ""

echo -e "${YELLOW}Testing local backend connection (port 8080)...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✓ Backend is responding on port 8080${NC}"
else
    echo -e "${RED}✗ Backend NOT responding on port 8080${NC}"
    echo -e "${RED}  This is likely the cause of the 502 error!${NC}"
fi
echo ""

echo -e "${YELLOW}Testing /dashboard endpoint...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/dashboard 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✓ /dashboard endpoint responds${NC}"
else
    echo -e "${RED}✗ /dashboard endpoint NOT responding${NC}"
fi
echo ""

echo -e "${YELLOW}Checking nginx status...${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx is NOT running${NC}"
    echo -e "${YELLOW}  Starting nginx...${NC}"
    sudo systemctl start nginx || sudo systemctl start nginx
fi
echo ""

# =============================================================================
# PHASE 2: FIX DOCKER CONTAINER
# =============================================================================
echo -e "${YELLOW}[2/6] FIXING DOCKER CONTAINER${NC}"
echo -e "${YELLOW}=============================${NC}"

# Check if container needs to be recreated
CONTAINER_NEEDS_RESTART=false

if ! docker ps | grep -q korra-ai; then
    echo -e "${YELLOW}Container exists but is not running. Attempting to start...${NC}"
    docker start korra-ai 2>/dev/null || CONTAINER_NEEDS_RESTART=true
fi

if [ "$CONTAINER_NEEDS_RESTART" = true ] || ! docker ps -a | grep -q korra-ai; then
    echo -e "${YELLOW}Recreating Docker container...${NC}"
    
    # Stop and remove old container if exists
    docker stop korra-ai 2>/dev/null || true
    docker rm korra-ai 2>/dev/null || true
    
    # Get environment variables
    SUPABASE_URL="${SUPABASE_URL:-https://blsettabymllulsxtziw.supabase.co}"
    SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-}"
    SUPABASE_SERVICE_ROLE_KEY="${SUPABASE_SERVICE_ROLE_KEY:-}"
    
    if [ -z "$SUPABASE_ANON_KEY" ]; then
        echo -e "${RED}Error: SUPABASE_ANON_KEY not set${NC}"
        echo -e "${YELLOW}Please set the environment variables and try again:${NC}"
        echo '  export SUPABASE_URL="https://yourproject.supabase.co"'
        echo '  export SUPABASE_ANON_KEY="your_anon_key"'
        echo '  export SUPABASE_SERVICE_ROLE_KEY="your_service_key"'
        exit 1
    fi
    
    # Run new container
    echo -e "${GREEN}Starting new container...${NC}"
    docker run -d \
        --name korra-ai \
        -p 127.0.0.1:8080:8080 \
        -e SUPABASE_URL="$SUPABASE_URL" \
        -e SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
        -e SUPABASE_SERVICE_ROLE_KEY="$SUPABASE_SERVICE_ROLE_KEY" \
        -e PORT=8080 \
        -e PYTHONUNBUFFERED=1 \
        -e ENVIRONMENT=production \
        --restart unless-stopped \
        korra-ai:latest || echo "Using local image. If this fails, build with: docker build -t korra-ai:latest ."
fi

# Wait for container to start
echo -e "${YELLOW}Waiting for backend to initialize...${NC}"
sleep 5

# =============================================================================
# PHASE 3: VERIFY BACKEND
# =============================================================================
echo -e "${YELLOW}[3/6] VERIFYING BACKEND${NC}"
echo -e "${YELLOW}======================${NC}"

# Test health endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Backend health check PASSED${NC}"
else
    echo -e "${RED}✗ Backend health check FAILED (HTTP $HTTP_CODE)${NC}"
    echo -e "${YELLOW}Checking container logs...${NC}"
    docker logs korra-ai --tail 30
    exit 1
fi

# Test dashboard endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/dashboard 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ /dashboard endpoint PASSED${NC}"
else
    echo -e "${RED}✗ /dashboard endpoint FAILED (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# =============================================================================
# PHASE 4: FIX NGINX CONFIGURATION
# =============================================================================
echo -e "${YELLOW}[4/6] FIXING NGINX CONFIGURATION${NC}"
echo -e "${YELLOW}=============================${NC}"

# Create nginx configuration for KORRA
KORRA_NGINX_CONFIG="/etc/nginx/sites-available/korra"
KORRA_NGINX_ENABLED="/etc/nginx/sites-enabled/korra"

echo -e "${YELLOW}Creating/updating nginx configuration...${NC}"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: Run with sudo for nginx configuration changes${NC}"
fi

# Create nginx config (use sudo if needed)
sudo tee "$KORRA_NGINX_CONFIG" > /dev/null << 'NGINX_CONFIG'
server {
    listen 80;
    listen [::]:80;
    server_name korra.work www.korra.work _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client max body size for file uploads
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for file uploads and ML processing
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        
        # CORS headers
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Freesewing pattern service — routes to Node.js on port 3002
    location ~ ^/(api/pattern|api/patterns|api/measurements) {
        proxy_pass http://127.0.0.1:3002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API routes - extended timeout for ML processing
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Longer timeouts for ML processing (5 minutes)
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }

    # Static assets - serve directly for performance
    location /assets/ {
        alias /app/public/assets/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_CONFIG

echo -e "${GREEN}Nginx config created${NC}"

# Enable the site
if [ ! -L "$KORRA_NGINX_ENABLED" ]; then
    echo -e "${YELLOW}Enabling KORRA nginx site...${NC}"
    sudo ln -sf "$KORRA_NGINX_CONFIG" "$KORRA_NGINX_ENABLED"
fi

# Disable default site if exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo -e "${YELLOW}Disabling default nginx site...${NC}"
    sudo rm -f /etc/nginx/sites-enabled/default
fi

# Test nginx configuration
echo -e "${YELLOW}Testing nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}✗ Nginx configuration has errors${NC}"
    exit 1
fi

# Reload nginx
echo -e "${YELLOW}Reloading nginx...${NC}"
sudo systemctl reload nginx || sudo nginx -s reload
echo -e "${GREEN}✓ Nginx reloaded${NC}"
echo ""

# =============================================================================
# PHASE 5: TEST END-TO-END
# =============================================================================
echo -e "${YELLOW}[5/6] TESTING END-TO-END${NC}"
echo -e "${YELLOW}======================${NC}"

# Test through nginx (simulate external request)
echo -e "${YELLOW}Testing / through nginx...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Root endpoint PASSED (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ Root endpoint FAILED (HTTP $HTTP_CODE)${NC}"
fi

echo -e "${YELLOW}Testing /dashboard through nginx...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/dashboard 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ /dashboard endpoint PASSED (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ /dashboard endpoint FAILED (HTTP $HTTP_CODE)${NC}"
fi

echo -e "${YELLOW}Testing /api/v2/health...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v2/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ /api/v2/health PASSED (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ /api/v2/health FAILED (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# =============================================================================
# PHASE 6: FINAL STATUS
# =============================================================================
echo -e "${YELLOW}[6/6] FINAL STATUS${NC}"
echo -e "${YELLOW}=============${NC}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}502 Fix Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Container Status:${NC}"
docker ps | grep korra-ai || echo "Container not running"
echo ""
echo -e "${BLUE}Nginx Status:${NC}"
systemctl status nginx --no-pager | head -3 || sudo systemctl status nginx --no-pager | head -3
echo ""
echo -e "${BLUE}Quick Commands:${NC}"
echo "  docker logs -f korra-ai     # View container logs"
echo "  docker restart korra-ai    # Restart container"
echo "  sudo nginx -s reload     # Reload nginx"
echo "  curl http://localhost/      # Test root"
echo ""

exit 0
