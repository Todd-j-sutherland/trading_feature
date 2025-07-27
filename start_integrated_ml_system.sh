#!/bin/bash

# Start Integrated ML Trading System
# Connects morning data collection → evening ML training → real-time dashboard

echo "🚀 Starting Integrated ML Trading System"
echo "=========================================="

# Check if required directories exist
echo "📁 Checking directories..."
mkdir -p data/ml_models/models
mkdir -p logs
mkdir -p metrics_exports

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -i :$port | grep LISTEN >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use"
        lsof -i :$port | grep LISTEN
        return 1
    else
        echo "✅ Port $port is available"
        return 0
    fi
}

# Function to start a background process with logging
start_bg_process() {
    local name=$1
    local command=$2
    local port=$3
    
    echo "🔄 Starting $name on port $port..."
    
    if check_port $port; then
        # Ensure logs directory exists
        mkdir -p logs
        
        local log_name=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
        nohup $command > logs/${log_name}_$(date +%Y%m%d_%H%M%S).log 2>&1 &
        local pid=$!
        echo "✅ $name started (PID: $pid)"
        sleep 3
        
        # Check if process is still running
        if kill -0 $pid 2>/dev/null; then
            echo "✅ $name is running successfully"
        else
            echo "❌ $name failed to start - check logs/${log_name}_*.log"
            return 1
        fi
    else
        echo "❌ Cannot start $name - port $port is busy"
        return 1
    fi
}

# Check Python environment and activate virtual environment
echo "🐍 Checking Python environment..."
if [ -f "dashboard_env/bin/activate" ]; then
    echo "✅ Found dashboard_env virtual environment"
    source dashboard_env/bin/activate
    echo "✅ Activated virtual environment: $(which python3)"
    
    # Check if required packages are installed
    python3 -c "import fastapi, uvicorn" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ FastAPI and uvicorn are available"
    else
        echo "⚠️  Installing required packages in virtual environment..."
        pip install fastapi uvicorn
        if [ $? -ne 0 ]; then
            echo "❌ Failed to install required packages"
            exit 1
        fi
    fi
elif command -v python3 &> /dev/null; then
    echo "⚠️  No virtual environment found, using system Python3: $(python3 --version)"
    # Try to install with --user flag as fallback
    python3 -c "import fastapi, uvicorn" 2>/dev/null || {
        echo "⚠️  Installing FastAPI with --user flag..."
        pip3 install --user fastapi uvicorn
    }
else
    echo "❌ Python3 not found"
    exit 1
fi

# Check Node.js environment
echo "📦 Checking Node.js environment..."
if command -v node &> /dev/null; then
    echo "✅ Node.js found: $(node --version)"
else
    echo "❌ Node.js not found"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    echo "✅ npm found: $(npm --version)"
else
    echo "❌ npm not found"
    exit 1
fi

echo ""
echo "🧠 INTEGRATED ML SYSTEM STARTUP"
echo "================================"

# 1. Start Main Backend (Port 8000)
start_bg_process "Main Backend" "python3 api_server.py" 8000

# 2. Start Enhanced ML Backend (Port 8001) 
start_bg_process "Enhanced ML Backend" "python3 enhanced_ml_system/realtime_ml_api.py" 8001

# 3. Start Frontend (Port 3000)
echo "🔄 Starting Frontend on port 3000..."
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found"
    exit 1
fi

cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install frontend dependencies"
        exit 1
    fi
fi

# Start frontend in background
start_bg_process "Frontend" "npm run dev" 3000
cd ..

# Wait for all services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Test endpoints
echo ""
echo "🔍 Testing service endpoints..."

# Test Main Backend
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Main Backend (8000) - Healthy"
else
    echo "⚠️  Main Backend (8000) - Not responding"
fi

# Test Enhanced ML Backend
if curl -s http://localhost:8001/api/health > /dev/null; then
    echo "✅ Enhanced ML Backend (8001) - Healthy"
else
    echo "⚠️  Enhanced ML Backend (8001) - Not responding"
fi

# Test Frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend (3000) - Healthy"
else
    echo "⚠️  Frontend (3000) - Not responding"
fi

echo ""
echo "🎯 INTEGRATED ML SYSTEM STATUS"
echo "=============================="
echo "📊 Main Dashboard:      http://localhost:3000"
echo "🧠 Integrated ML:       http://localhost:3000 (click 'Integrated ML' tab)"
echo "🤖 Simple ML Test:      http://localhost:3000 (click 'ML Test' tab)"
echo "🔧 Main API:            http://localhost:8000/docs"
echo "⚡ Enhanced ML API:     http://localhost:8001/docs"
echo ""
echo "📝 USAGE GUIDE:"
echo "==============="
echo "1. 🌅 Morning Analysis:  python -m app.main morning"
echo "2. 🌆 Evening Training:  python -m app.main evening"
echo "3. 📊 View Dashboard:    Open browser to http://localhost:3000"
echo "4. 🧠 Integrated ML:     Click 'Integrated ML' tab for real ML training results"
echo ""
echo "📋 LOG FILES:"
echo "============="
ls -la logs/*.log 2>/dev/null | tail -5
echo ""
echo "🎉 Integrated ML Trading System is ready!"
echo ""
echo "💡 TIP: The 'Integrated ML' dashboard shows real predictions from your"
echo "    morning data collection and evening ML training pipeline!"
echo ""
echo "🛑 To stop all services: ./stop_complete_ml_system.sh"
