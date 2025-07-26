#!/bin/bash
echo "🏦 Starting Complete ML Trading System"
echo "====================================="

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down all services..."
    kill $(jobs -p) 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT

# Ensure virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📦 Setting up Python environment..."
source venv/bin/activate
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

# Start frontend
echo "🎨 Starting Frontend Dashboard..."
./start_ml_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "🎯 SYSTEM READY!"
echo "==============="
echo "🔗 Frontend Dashboard: http://localhost:3002"
echo "🏦 Main Backend API: http://localhost:8000"
echo "🤖 ML Backend API: http://localhost:8001/docs"
echo "📊 Real-time WebSocket: ws://localhost:8001/ws/live-updates"
echo "📈 HTML Dashboard: file://$(pwd)/enhanced_ml_system/bank_performance_dashboard.html"
echo ""
echo "💡 The system provides:"
echo "   • Main backend with chart data & original ML (Port 8000)"
echo "   • Enhanced ML backend with 11 Australian banks (Port 8001)"
echo "   • Real-time sentiment analysis from news"
echo "   • WebSocket updates every 5 minutes"
echo "   • REST API endpoints for all data"
echo "   • Integrated frontend with existing charts"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for all background jobs
wait
