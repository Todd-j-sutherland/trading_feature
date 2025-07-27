#!/bin/bash
echo "🚀 Starting Production Frontend Server"
echo "====================================="

cd frontend

# Build the app if dist doesn't exist
if [ ! -d "dist" ]; then
    echo "📦 Building React app for production..."
    npm run build
fi

# Install serve if not available
if ! command -v serve &> /dev/null; then
    echo "📦 Installing 'serve' package..."
    npm install -g serve
fi

echo "🌐 Starting production server on port 3002..."
cd dist
python3 -m http.server 3002 --bind 0.0.0.0

echo "✅ Frontend production server started!"
echo "🔗 Dashboard: http://0.0.0.0:3002 (or http://YOUR_SERVER_IP:3002)"
