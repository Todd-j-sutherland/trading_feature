#!/bin/bash

# Stop all trading system services

echo "🛑 Stopping Trading System Services..."

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="logs/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "   🛑 Stopping $service_name (PID: $pid)..."
            kill "$pid"
            sleep 2
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "   💀 Force killing $service_name..."
                kill -9 "$pid"
            fi
        else
            echo "   ⚠️  $service_name was not running"
        fi
        rm -f "$pid_file"
    else
        echo "   ⚠️  No PID file found for $service_name"
    fi
}

# Stop all services
stop_service "orchestrator"
stop_service "trading-service"
stop_service "sentiment-service"

# Clean up any remaining processes
echo "🧹 Cleaning up any remaining processes..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "python.*orchestrator.py" 2>/dev/null || true

echo "✅ All services stopped"