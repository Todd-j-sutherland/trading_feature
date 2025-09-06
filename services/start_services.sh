#!/bin/bash

# Start Services Script - Phase 1 Services Architecture
# This script starts all services in the correct order with proper health checks

set -e  # Exit on any error

# Configuration
SERVICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SERVICES_DIR")"
LOG_DIR="$PROJECT_ROOT/logs/services"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Wait for a service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local timeout=${3:-30}
    local count=0
    
    log "Waiting for $service_name to be ready on port $port..."
    
    while [ $count -lt $timeout ]; do
        if curl -s "http://localhost:$port/health" >/dev/null 2>&1; then
            success "$service_name is ready!"
            return 0
        fi
        
        sleep 1
        count=$((count + 1))
    done
    
    error "$service_name failed to start within $timeout seconds"
    return 1
}

# Stop any existing services
stop_services() {
    log "Stopping any existing services..."
    
    # Kill processes by port
    for port in 8000 8001 8002; do
        if ! check_port $port; then
            warning "Port $port is in use, attempting to stop service..."
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
            sleep 2
        fi
    done
    
    # Kill any python services in the background
    pkill -f "trading_service.py" 2>/dev/null || true
    pkill -f "sentiment_service.py" 2>/dev/null || true
    pkill -f "orchestrator_service.py" 2>/dev/null || true
    
    sleep 2
    success "Existing services stopped"
}

# Check Python environment
check_environment() {
    log "Checking Python environment..."
    
    if ! command -v python3 &> /dev/null; then
        error "Python3 is not installed or not in PATH"
        exit 1
    fi
    
    success "Python3 is available: $(python3 --version)"
    
    # Check if we're in a virtual environment
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        success "Virtual environment active: $VIRTUAL_ENV"
    else
        warning "No virtual environment detected - some dependencies may be missing"
    fi
}

# Start a service
start_service() {
    local service_name=$1
    local service_file=$2
    local port=$3
    
    log "Starting $service_name on port $port..."
    
    # Check if port is available
    if ! check_port $port; then
        error "Port $port is already in use for $service_name"
        return 1
    fi
    
    # Start the service in the background
    cd "$PROJECT_ROOT"
    nohup python3 "$service_file" > "$LOG_DIR/${service_name}.log" 2>&1 &
    local pid=$!
    
    # Store PID for later cleanup
    echo $pid > "$LOG_DIR/${service_name}.pid"
    
    log "$service_name started with PID $pid"
    
    # Wait for service to be ready (but don't fail if it doesn't respond immediately)
    if command -v curl &> /dev/null; then
        if wait_for_service "$service_name" "$port" 15; then
            success "$service_name is responding on port $port"
        else
            warning "$service_name may not be fully ready yet (check logs)"
        fi
    else
        warning "curl not available - cannot verify service health"
        sleep 3
    fi
}

# Check service status
check_service_status() {
    local service_name=$1
    local port=$2
    
    if command -v curl &> /dev/null; then
        if curl -s "http://localhost:$port/health" >/dev/null 2>&1; then
            success "$service_name: ✓ Healthy"
        else
            error "$service_name: ✗ Not responding"
        fi
    else
        # Check if process is running
        if [ -f "$LOG_DIR/${service_name}.pid" ]; then
            local pid=$(cat "$LOG_DIR/${service_name}.pid")
            if ps -p $pid > /dev/null 2>&1; then
                success "$service_name: ✓ Running (PID $pid)"
            else
                error "$service_name: ✗ Process not found"
            fi
        else
            error "$service_name: ✗ No PID file found"
        fi
    fi
}

# Main execution
main() {
    log "Starting Phase 1 Services Architecture..."
    
    # Check environment
    check_environment
    
    # Stop any existing services
    stop_services
    
    # Start services in order
    log "Starting services..."
    
    # 1. Trading Service (Port 8001)
    start_service "trading" "services/trading_service.py" 8001
    
    # 2. Sentiment Service (Port 8002)  
    start_service "sentiment" "services/sentiment_service.py" 8002
    
    # 3. Orchestrator Service (Port 8000)
    start_service "orchestrator" "services/orchestrator_service.py" 8000
    
    # Wait a bit for all services to settle
    sleep 5
    
    # Check status of all services
    log "Checking service status..."
    check_service_status "trading" 8001
    check_service_status "sentiment" 8002
    check_service_status "orchestrator" 8000
    
    # Display service information
    echo ""
    success "Phase 1 Services Started Successfully!"
    echo ""
    echo "Service Endpoints:"
    echo "  • Orchestrator Service: http://localhost:8000"
    echo "  • Trading Service:      http://localhost:8001"
    echo "  • Sentiment Service:    http://localhost:8002"
    echo ""
    echo "Health Check URLs:"
    echo "  • Orchestrator Health:  http://localhost:8000/health"
    echo "  • Trading Health:       http://localhost:8001/health"
    echo "  • Sentiment Health:     http://localhost:8002/health"
    echo ""
    echo "System Status:"
    echo "  • System Status:        http://localhost:8000/system/status"
    echo ""
    echo "Log Files:"
    echo "  • Trading Service:      $LOG_DIR/trading.log"
    echo "  • Sentiment Service:    $LOG_DIR/sentiment.log"
    echo "  • Orchestrator Service: $LOG_DIR/orchestrator.log"
    echo ""
    
    if command -v curl &> /dev/null; then
        log "Testing system integration..."
        if curl -s "http://localhost:8000/system/status" >/dev/null 2>&1; then
            success "System integration test passed!"
        else
            warning "System integration test failed - check logs"
        fi
    fi
    
    echo "To stop services: ./services/stop_services.sh"
    echo "To view logs: tail -f $LOG_DIR/*.log"
}

# Handle script arguments
case "${1:-start}" in
    "start")
        main
        ;;
    "stop")
        stop_services
        ;;
    "status")
        check_service_status "trading" 8001
        check_service_status "sentiment" 8002
        check_service_status "orchestrator" 8000
        ;;
    "restart")
        stop_services
        sleep 3
        main
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all services (default)"
        echo "  stop    - Stop all services"
        echo "  status  - Check service status"
        echo "  restart - Restart all services"
        exit 1
        ;;
esac
