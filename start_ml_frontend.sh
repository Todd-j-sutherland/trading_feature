#!/bin/bash
echo "🎨 Starting Enhanced Frontend with ML Integration"
echo "=============================================="

cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Add TypeScript types for better development
echo "🔧 Adding TypeScript types..."
npm install --save-dev @types/ws || true

# Start the frontend development server
echo "🌐 Starting React development server on all interfaces..."
npm run dev -- --host 0.0.0.0 --port 3002

echo "✅ Frontend started!"
echo "🔗 Dashboard: http://0.0.0.0:3002 (or http://YOUR_SERVER_IP:3002)"
echo "🤖 ML Integration active!"
