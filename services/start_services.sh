#!/bin/bash

# Trading System Services Startup Script
# Starts all services in the correct order

set -e  # Exit on error

echo "🚀 Starting Trading System Services..."

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r services/requirements.txt
else
    echo "📦 Activating existing virtual environment..."
    source venv/bin/activate
fi

# Create necessary directories
mkdir -p logs
mkdir -p data/services

# Function to start a service in background
start_service() {
    local service_name=$1
    local service_path=$2
    local port=$3
    
    echo "🌟 Starting $service_name on port $port..."
    
    cd "$service_path"
    python main.py > "../../logs/${service_name}.log" 2>&1 &
    local pid=$!
    echo $pid > "../../logs/${service_name}.pid"
    cd - > /dev/null
    
    echo "   ✅ $service_name started (PID: $pid)"
    
    # Wait a moment for service to start
    sleep 2
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $port is already in use"
        return 1
    fi
    return 0
}

# Check required ports
echo "🔍 Checking required ports..."
check_port 8001 || exit 1
check_port 8002 || exit 1
check_port 8000 || exit 1

# Start services in order
start_service "trading-service" "services/trading-service" 8001
start_service "sentiment-service" "services/sentiment-service" 8002

# Start orchestrator last
echo "🎯 Starting orchestrator on port 8000..."
cd services
python orchestrator.py > "../logs/orchestrator.log" 2>&1 &
orchestrator_pid=$!
echo $orchestrator_pid > "../logs/orchestrator.pid"
cd - > /dev/null
echo "   ✅ Orchestrator started (PID: $orchestrator_pid)"

# Wait for all services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Health check
echo "🏥 Performing health checks..."

health_check() {
    local service_name=$1
    local url=$2
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        echo "   ✅ $service_name is healthy"
        return 0
    else
        echo "   ❌ $service_name is not responding (HTTP $response)"
        return 1
    fi
}

all_healthy=true

health_check "Trading Service" "http://localhost:8001/health" || all_healthy=false
health_check "Sentiment Service" "http://localhost:8002/health" || all_healthy=false
health_check "Orchestrator" "http://localhost:8000/health" || all_healthy=false

if $all_healthy; then
    echo ""
    echo "🎉 All services are running and healthy!"
    echo ""
    echo "📊 Service URLs:"
    echo "   🎯 Orchestrator:      http://localhost:8000"
    echo "   💰 Trading Service:   http://localhost:8001"
    echo "   📰 Sentiment Service: http://localhost:8002"
    echo ""
    echo "📖 API Documentation:"
    echo "   🎯 Orchestrator Docs: http://localhost:8000/docs"
    echo "   💰 Trading Docs:      http://localhost:8001/docs"
    echo "   📰 Sentiment Docs:    http://localhost:8002/docs"
    echo ""
    echo "🔍 To view logs:"
    echo "   tail -f logs/orchestrator.log"
    echo "   tail -f logs/trading-service.log"
    echo "   tail -f logs/sentiment-service.log"
    echo ""
    echo "🛑 To stop all services:"
    echo "   ./services/stop_services.sh"
else
    echo ""
    echo "❌ Some services failed to start. Check logs in the logs/ directory."
    exit 1
fi