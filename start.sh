#!/bin/bash

# Navigate to project directory
cd /home/abisek/Documents/Skandaenterpriese-main

# Activate virtual environment
source venv/bin/activate

# Kill any existing Flask or cloudflared processes
echo "Stopping existing processes..."
pkill -f "python app.py" 2>/dev/null
pkill cloudflared 2>/dev/null
sleep 2

# Start Flask application in background
echo "Starting Flask application..."
python app.py > /tmp/flask.log 2>&1 &
FLASK_PID=$!
echo "Flask started with PID: $FLASK_PID"

# Wait for Flask to be ready
echo "Waiting for Flask to start..."
sleep 5

# Check if Flask is running
if curl -s http://localhost:5000 > /dev/null; then
    echo "✓ Flask is running on port 5000"
else
    echo "✗ Flask failed to start. Check /tmp/flask.log"
    exit 1
fi

# Start Cloudflare Tunnel
echo "Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://localhost:5000 > /tmp/cloudflared.log 2>&1 &
TUNNEL_PID=$!
echo "Tunnel started with PID: $TUNNEL_PID"

# Wait for tunnel to establish
echo "Waiting for tunnel to establish..."
sleep 8

# Extract and display the public URL
TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cloudflared.log | head -1)

if [ -n "$TUNNEL_URL" ]; then
    echo ""
    echo "=========================================="
    echo "✓ Tunnel is active!"
    echo "Public URL: $TUNNEL_URL"
    echo "=========================================="
    echo ""
    echo "To view logs:"
    echo "  Flask: tail -f /tmp/flask.log"
    echo "  Tunnel: tail -f /tmp/cloudflared.log"
    echo ""
    echo "To stop everything:"
    echo "  pkill -f 'python app.py' && pkill cloudflared"
    echo ""
else
    echo "Tunnel URL not found. Check /tmp/cloudflared.log"
    echo "Tunnel may still be starting. Wait a few seconds and check:"
    echo "  tail -f /tmp/cloudflared.log"
fi

