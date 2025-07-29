#!/bin/bash
echo "🔍 Port Status Check"
echo "==================="

echo "📊 Checking ports 8000, 8001, 3002:"
netstat -tlnp | grep -E ":8000|:8001|:3002" || echo "All ports available"

echo ""
echo "🔄 Killing any existing processes on these ports:"
pkill -f "api_server.py" 2>/dev/null && echo "Killed api_server.py" || echo "No api_server.py process found"
pkill -f "realtime_ml_api.py" 2>/dev/null && echo "Killed realtime_ml_api.py" || echo "No realtime_ml_api.py process found"
pkill -f "vite" 2>/dev/null && echo "Killed vite process" || echo "No vite process found"

echo ""
echo "✅ Ports should now be available"
