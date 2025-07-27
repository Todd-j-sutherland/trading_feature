#!/bin/bash
echo "🏦 Starting Complete ML Trading System (DEVELOPMENT MODE)"
echo "======================================================="

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down all services..."
    kill $(jobs -p) 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT

# Check if we're using a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Using virtual environment: $VIRTUAL_ENV"
else
    echo "⚠️  Please activate dashboard_env first:"
    echo "   source dashboard_env/bin/activate"
    exit 1
fi

# Ensure we have all dependencies
echo "📦 Installing/updating Python dependencies..."
pip install fastapi uvicorn websockets pydantic pandas numpy yfinance scikit-learn joblib

# Start backend services
echo "🚀 Starting Main Backend (Port 8000)..."
python api_server.py &
MAIN_BACKEND_PID=$!

echo "🤖 Starting ML Backend System (Port 8001)..."
./start_ml_backend.sh &
ML_BACKEND_PID=$!

# Wait a moment for backends to start
echo "⏳ Waiting for backends to initialize..."
sleep 8

# Start frontend in DEVELOPMENT mode
echo "🎨 Starting Frontend in DEVELOPMENT mode with HOT RELOAD..."
echo "📍 Current directory: $(pwd)"
echo "📁 Frontend directory exists: $([ -d "frontend" ] && echo "YES" || echo "NO")"

cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

echo "🔥 Starting Vite dev server with hot reload..."
npm run dev &
FRONTEND_PID=$!

cd ..

# Wait a moment for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 5

echo ""
echo "🎉 Complete ML Trading System is now running in DEVELOPMENT mode!"
echo "=================================================="
echo "🔗 Main Dashboard: http://localhost:5173"
echo "🤖 SimpleML Test: http://localhost:5173 (click 'ML Test' button)"
echo "🔧 Chart Test: http://localhost:5173 (click 'Chart Test' button)"
echo "📊 ML API Docs: http://localhost:8001/docs"
echo "🚀 Main API: http://localhost:8000/api/status"
echo ""
echo "✨ HOT RELOAD ENABLED - Changes will automatically update!"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running and show logs
wait
