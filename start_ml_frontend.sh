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
echo "🌐 Starting React development server..."
npm run dev

echo "✅ Frontend started!"
echo "🔗 Dashboard: http://localhost:5173"
echo "🤖 ML Integration active!"
