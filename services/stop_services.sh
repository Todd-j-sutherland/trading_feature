#!/bin/bash

# Stop Services Script - Phase 1 Services Architecture
# This script stops all running services gracefully

set -e  # Exit on any error

# Configuration
SERVICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SERVICES_DIR")"
LOG_DIR="$PROJECT_ROOT/logs/services"

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

# Stop a specific service
stop_service() {
    local service_name=$1
    local port=$2
    
    log "Stopping $service_name..."
    
    # Try to stop via PID file first
    if [ -f "$LOG_DIR/${service_name}.pid" ]; then
        local pid=$(cat "$LOG_DIR/${service_name}.pid")
        if ps -p $pid > /dev/null 2>&1; then
            log "Stopping $service_name (PID $pid)..."
            kill $pid 2>/dev/null || true
            
            # Wait for graceful shutdown
            local count=0
            while [ $count -lt 10 ] && ps -p $pid > /dev/null 2>&1; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                warning "Force killing $service_name (PID $pid)..."
                kill -9 $pid 2>/dev/null || true
            fi
            
            success "$service_name stopped"
        else
            warning "$service_name PID file exists but process not found"
        fi
        
        # Remove PID file
        rm -f "$LOG_DIR/${service_name}.pid"
    fi
    
    # Stop by port if still running
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        warning "Service still running on port $port, killing by port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    # Verify service is stopped
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        error "Failed to stop service on port $port"
    else
        success "$service_name on port $port is stopped"
    fi
}

# Stop all services
stop_all_services() {
    log "Stopping all Phase 1 services..."
    
    # Stop services in reverse order
    stop_service "orchestrator" 8000
    stop_service "sentiment" 8002
    stop_service "trading" 8001
    
    # Kill any remaining python service processes
    log "Cleaning up any remaining processes..."
    pkill -f "trading_service.py" 2>/dev/null || true
    pkill -f "sentiment_service.py" 2>/dev/null || true
    pkill -f "orchestrator_service.py" 2>/dev/null || true
    
    sleep 2
    
    # Final verification
    local ports_in_use=0
    for port in 8000 8001 8002; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            error "Port $port is still in use"
            ports_in_use=$((ports_in_use + 1))
        fi
    done
    
    if [ $ports_in_use -eq 0 ]; then
        success "All services stopped successfully!"
    else
        error "$ports_in_use ports are still in use"
        return 1
    fi
}

# Show service status
show_status() {
    log "Checking service status..."
    
    echo ""
    echo "Service Status:"
    
    for service_port in "trading:8001" "sentiment:8002" "orchestrator:8000"; do
        local service=$(echo $service_port | cut -d: -f1)
        local port=$(echo $service_port | cut -d: -f2)
        
        printf "  %-12s: " "$service"
        
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${RED}Running${NC} (port $port)"
        else
            echo -e "${GREEN}Stopped${NC}"
        fi
    done
    
    echo ""
    
    # Check for any remaining python service processes
    local service_processes=$(ps aux | grep -E "(trading_service|sentiment_service|orchestrator_service)\.py" | grep -v grep | wc -l)
    if [ $service_processes -gt 0 ]; then
        warning "$service_processes service processes still running"
        ps aux | grep -E "(trading_service|sentiment_service|orchestrator_service)\.py" | grep -v grep
    fi
}

# Clean up log files and PID files
cleanup() {
    log "Cleaning up service files..."
    
    # Remove PID files
    rm -f "$LOG_DIR"/*.pid
    
    # Optionally archive log files
    if [ "${1:-}" = "clean-logs" ]; then
        if [ -d "$LOG_DIR" ] && [ "$(ls -A $LOG_DIR)" ]; then
            local archive_dir="$LOG_DIR/archive/$(date +%Y%m%d_%H%M%S)"
            mkdir -p "$archive_dir"
            mv "$LOG_DIR"/*.log "$archive_dir/" 2>/dev/null || true
            success "Log files archived to $archive_dir"
        fi
    fi
    
    success "Cleanup completed"
}

# Main execution
main() {
    case "${1:-stop}" in
        "stop")
            stop_all_services
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "clean-all")
            stop_all_services
            cleanup "clean-logs"
            ;;
        *)
            echo "Usage: $0 {stop|status|cleanup|clean-all}"
            echo ""
            echo "Commands:"
            echo "  stop      - Stop all services (default)"
            echo "  status    - Show service status"
            echo "  cleanup   - Remove PID files"
            echo "  clean-all - Stop services and archive logs"
            exit 1
            ;;
    esac
}

# Handle script arguments
main "$@"
