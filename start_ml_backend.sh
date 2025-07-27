#!/bin/bash
echo "🚀 Starting Enhanced ML Backend System"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install required packages
echo "📦 Installing Python dependencies..."
pip install fastapi uvicorn websockets pydantic pandas numpy sqlite3 yfinance scikit-learn

# Start the ML data collection in background
echo "🔄 Starting ML data collection..."
python enhanced_ml_system/multi_bank_data_collector.py &
ML_COLLECTOR_PID=$!

# Start the real-time API server
echo "🌐 Starting Real-time ML API server on port 8001..."
python enhanced_ml_system/realtime_ml_api.py &
API_SERVER_PID=$!

echo "✅ Backend services started!"
echo "🔗 API Documentation: http://localhost:8001/docs"
echo "📊 WebSocket: ws://localhost:8001/ws/live-updates"
echo "📈 API Endpoints: http://localhost:8001/api/"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down backend services..."
    kill $ML_COLLECTOR_PID 2>/dev/null
    kill $API_SERVER_PID 2>/dev/null
    echo "✅ Backend services stopped"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Wait for user to stop
echo "Press Ctrl+C to stop all services..."
wait
