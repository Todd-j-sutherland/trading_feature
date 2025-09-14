#!/bin/bash
"""
Production Deployment Guide for Trading Microservices

This script provides automated production deployment procedures with 
comprehensive validation, rollback capabilities, and operational excellence.

Author: Trading System DevOps Team
Date: September 14, 2025
"""

set -euo pipefail

# Configuration
TRADING_HOME="${TRADING_HOME:-/opt/trading_services}"
TRADING_USER="${TRADING_USER:-trading}"
TRADING_GROUP="${TRADING_GROUP:-trading}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/trading}"
LOG_DIR="${LOG_DIR:-/var/log/trading}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_DIR/deployment.log"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_DIR/deployment.log"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_DIR/deployment.log"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_DIR/deployment.log"
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Deployment failed with exit code $exit_code"
        log "Starting rollback procedure..."
        rollback_deployment
    fi
    exit $exit_code
}

trap cleanup EXIT

# Pre-deployment validation
validate_prerequisites() {
    log "🔍 Validating deployment prerequisites..."
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ] && [ -z "${SUDO_USER:-}" ]; then
        log_error "This script must be run with sudo privileges"
        exit 1
    fi
    
    # Check if trading user exists
    if ! id "$TRADING_USER" >/dev/null 2>&1; then
        log "Creating trading user..."
        useradd -r -s /bin/bash -d "$TRADING_HOME" "$TRADING_USER"
        usermod -a -G redis "$TRADING_USER"
    fi
    
    # Check required directories
    for dir in "$TRADING_HOME" "$BACKUP_DIR" "$LOG_DIR" "/tmp/trading_sockets"; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
            chown "$TRADING_USER:$TRADING_GROUP" "$dir"
        fi
    done
    
    # Check Python virtual environment
    if [ ! -f "$TRADING_HOME/trading_venv/bin/python" ]; then
        log "Creating Python virtual environment..."
        python3 -m venv "$TRADING_HOME/trading_venv"
        chown -R "$TRADING_USER:$TRADING_GROUP" "$TRADING_HOME/trading_venv"
    fi
    
    # Check Redis
    if ! systemctl is-active redis-server >/dev/null 2>&1; then
        log "Starting Redis server..."
        systemctl start redis-server
        systemctl enable redis-server
    fi
    
    # Check available disk space (minimum 5GB)
    available_space=$(df "$TRADING_HOME" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 5242880 ]; then  # 5GB in KB
        log_error "Insufficient disk space. Need at least 5GB available."
        exit 1
    fi
    
    # Check memory (minimum 2GB)
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$available_memory" -lt 2048 ]; then
        log_warning "Low available memory: ${available_memory}MB. Deployment may be slow."
    fi
    
    log_success "Prerequisites validation completed"
}

# Install Python dependencies
install_dependencies() {
    log "📦 Installing Python dependencies..."
    
    cd "$TRADING_HOME"
    
    # Activate virtual environment
    source trading_venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # Install core dependencies
        pip install \
            redis==4.5.4 \
            flask==2.3.2 \
            psutil==5.9.5 \
            aiofiles==23.1.0 \
            requests==2.31.0 \
            pyyaml==6.0 \
            sqlite3
    fi
    
    # Install additional monitoring dependencies
    pip install \
        prometheus-client==0.16.0 \
        grafana-api==1.0.3 \
        alertmanager-api==0.1.0
    
    log_success "Dependencies installation completed"
}

# Create system backup
create_deployment_backup() {
    log "📦 Creating deployment backup..."
    
    local timestamp=$(date +'%Y%m%d_%H%M%S')
    local backup_path="$BACKUP_DIR/deployment_backup_$timestamp"
    
    mkdir -p "$backup_path"
    
    # Backup databases
    mkdir -p "$backup_path/databases"
    find "$TRADING_HOME" -name "*.db" -exec cp {} "$backup_path/databases/" \;
    
    # Backup configuration
    if [ -d "$TRADING_HOME/config" ]; then
        cp -r "$TRADING_HOME/config" "$backup_path/"
    fi
    
    # Backup current services (if they exist)
    if [ -d "$TRADING_HOME/services" ]; then
        cp -r "$TRADING_HOME/services" "$backup_path/"
    fi
    
    # Backup systemd files
    mkdir -p "$backup_path/systemd"
    cp /etc/systemd/system/trading-*.service "$backup_path/systemd/" 2>/dev/null || true
    
    # Create backup manifest
    cat > "$backup_path/manifest.json" << EOF
{
    "backup_type": "deployment",
    "timestamp": "$timestamp",
    "created_at": "$(date -Is)",
    "backup_path": "$backup_path",
    "includes": ["databases", "config", "services", "systemd"]
}
EOF
    
    chown -R "$TRADING_USER:$TRADING_GROUP" "$backup_path"
    
    echo "$backup_path" > "/tmp/last_backup_path"
    
    log_success "Backup created: $backup_path"
}

# Deploy service files
deploy_services() {
    log "🚀 Deploying service files..."
    
    cd "$TRADING_HOME"
    
    # Set proper ownership
    chown -R "$TRADING_USER:$TRADING_GROUP" .
    
    # Make service files executable
    if [ -d "services" ]; then
        find services -name "*.py" -exec chmod +x {} \;
    fi
    
    # Deploy systemd service files
    if [ -d "systemd" ]; then
        cp systemd/*.service /etc/systemd/system/
        systemctl daemon-reload
        
        # Enable services
        for service_file in systemd/*.service; do
            service_name=$(basename "$service_file")
            systemctl enable "$service_name"
            log "Enabled $service_name"
        done
    fi
    
    log_success "Service files deployed"
}

# Start services in dependency order
start_services() {
    log "🔄 Starting services in dependency order..."
    
    local services=(
        "trading-market-data"
        "trading-sentiment" 
        "trading-ml-model"
        "trading-prediction"
        "trading-paper-trading"
        "trading-scheduler"
        "trading-monitoring"
    )
    
    for service in "${services[@]}"; do
        log "Starting $service..."
        
        if systemctl start "$service"; then
            log_success "$service started successfully"
            
            # Wait for service to be ready
            sleep 5
            
            # Health check
            if systemctl is-active "$service" >/dev/null; then
                log_success "$service is active and healthy"
            else
                log_error "$service failed to start properly"
                return 1
            fi
        else
            log_error "Failed to start $service"
            return 1
        fi
    done
    
    log_success "All services started successfully"
}

# Comprehensive health check
run_health_checks() {
    log "🏥 Running comprehensive health checks..."
    
    local failed_checks=0
    
    # Check service status
    local services=(
        "trading-market-data"
        "trading-sentiment"
        "trading-ml-model" 
        "trading-prediction"
        "trading-paper-trading"
        "trading-scheduler"
        "trading-monitoring"
    )
    
    for service in "${services[@]}"; do
        if systemctl is-active "$service" >/dev/null; then
            log_success "$service: Active"
        else
            log_error "$service: Inactive"
            ((failed_checks++))
        fi
    done
    
    # Check socket connectivity
    for service in "${services[@]}"; do
        local socket_name="/tmp/trading_${service#trading-}.sock"
        if [ -S "$socket_name" ]; then
            log_success "Socket $socket_name: Available"
        else
            log_error "Socket $socket_name: Not available"
            ((failed_checks++))
        fi
    done
    
    # Check Redis connectivity
    if redis-cli ping >/dev/null 2>&1; then
        log_success "Redis: Connected"
    else
        log_error "Redis: Connection failed"
        ((failed_checks++))
    fi
    
    # Check database accessibility
    local databases=(
        "$TRADING_HOME/predictions.db"
        "$TRADING_HOME/trading_predictions.db"
        "$TRADING_HOME/paper_trading.db"
    )
    
    for db in "${databases[@]}"; do
        if [ -f "$db" ]; then
            if sqlite3 "$db" "SELECT 1;" >/dev/null 2>&1; then
                log_success "Database $(basename "$db"): Accessible"
            else
                log_error "Database $(basename "$db"): Corrupted or inaccessible"
                ((failed_checks++))
            fi
        else
            log_warning "Database $(basename "$db"): Not found (may be created on first use)"
        fi
    done
    
    # Check system resources
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3/$2*100}')
    local disk_usage=$(df "$TRADING_HOME" | awk 'NR==2{printf "%.0f", $3/$2*100}')
    
    log "Memory usage: ${memory_usage}%"
    log "Disk usage: ${disk_usage}%"
    
    if [ "$memory_usage" -gt 90 ]; then
        log_warning "High memory usage: ${memory_usage}%"
    fi
    
    if [ "$disk_usage" -gt 90 ]; then
        log_warning "High disk usage: ${disk_usage}%"
    fi
    
    if [ $failed_checks -eq 0 ]; then
        log_success "All health checks passed"
        return 0
    else
        log_error "$failed_checks health checks failed"
        return 1
    fi
}

# Production readiness validation
validate_production_readiness() {
    log "🔍 Validating production readiness..."
    
    # Run the Python production readiness validator
    cd "$TRADING_HOME"
    source trading_venv/bin/activate
    
    if [ -f "tools/deployment_manager.py" ]; then
        python tools/deployment_manager.py validate > /tmp/production_validation.json
        
        local overall_ready=$(python -c "
import json
with open('/tmp/production_validation.json', 'r') as f:
    data = json.load(f)
    print('true' if data.get('overall_ready', False) else 'false')
")
        
        if [ "$overall_ready" = "true" ]; then
            log_success "Production readiness validation passed"
            return 0
        else
            log_error "Production readiness validation failed"
            cat /tmp/production_validation.json
            return 1
        fi
    else
        log_warning "Production readiness validator not found, skipping detailed validation"
        return 0
    fi
}

# Rollback deployment
rollback_deployment() {
    log "🔄 Rolling back deployment..."
    
    if [ -f "/tmp/last_backup_path" ]; then
        local backup_path=$(cat /tmp/last_backup_path)
        
        if [ -d "$backup_path" ]; then
            log "Restoring from backup: $backup_path"
            
            # Stop all services
            local services=(
                "trading-monitoring"
                "trading-scheduler"
                "trading-paper-trading"
                "trading-prediction"
                "trading-ml-model"
                "trading-sentiment"
                "trading-market-data"
            )
            
            for service in "${services[@]}"; do
                systemctl stop "$service" 2>/dev/null || true
            done
            
            # Restore files
            if [ -d "$backup_path/services" ]; then
                rm -rf "$TRADING_HOME/services"
                cp -r "$backup_path/services" "$TRADING_HOME/"
            fi
            
            if [ -d "$backup_path/config" ]; then
                rm -rf "$TRADING_HOME/config"
                cp -r "$backup_path/config" "$TRADING_HOME/"
            fi
            
            if [ -d "$backup_path/databases" ]; then
                cp "$backup_path/databases"/*.db "$TRADING_HOME/" 2>/dev/null || true
            fi
            
            if [ -d "$backup_path/systemd" ]; then
                cp "$backup_path/systemd"/*.service /etc/systemd/system/
                systemctl daemon-reload
            fi
            
            # Set ownership
            chown -R "$TRADING_USER:$TRADING_GROUP" "$TRADING_HOME"
            
            # Restart services
            for service in "${services[@]}"; do
                systemctl start "$service" 2>/dev/null || true
            done
            
            log_success "Rollback completed"
        else
            log_error "Backup directory not found: $backup_path"
        fi
    else
        log_error "No backup path found for rollback"
    fi
}

# Setup monitoring
setup_monitoring() {
    log "📊 Setting up monitoring and alerting..."
    
    # Create monitoring configuration if it doesn't exist
    if [ ! -f "$TRADING_HOME/config/monitoring.json" ]; then
        mkdir -p "$TRADING_HOME/config"
        
        cat > "$TRADING_HOME/config/monitoring.json" << EOF
{
    "metrics": {
        "enabled": true,
        "retention_days": 90,
        "collection_interval": 30
    },
    "alerts": {
        "email": {
            "enabled": false,
            "smtp_server": "",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "recipients": []
        },
        "webhook": {
            "enabled": false,
            "url": ""
        },
        "console": {
            "enabled": true
        }
    },
    "thresholds": {
        "memory_usage": 85,
        "cpu_usage": 90,
        "disk_usage": 90,
        "error_rate": 5,
        "response_time": 10000
    }
}
EOF
        
        chown "$TRADING_USER:$TRADING_GROUP" "$TRADING_HOME/config/monitoring.json"
        log_success "Monitoring configuration created"
    fi
    
    # Start monitoring dashboard if available
    if systemctl list-unit-files | grep -q "trading-monitoring-dashboard.service"; then
        systemctl start trading-monitoring-dashboard.service
        systemctl enable trading-monitoring-dashboard.service
        log_success "Monitoring dashboard started"
    fi
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    log "🚀 Starting Trading System Deployment"
    log "Deployment started at: $(date)"
    
    # Pre-deployment steps
    validate_prerequisites
    install_dependencies
    create_deployment_backup
    
    # Deployment steps
    deploy_services
    start_services
    
    # Post-deployment validation
    run_health_checks
    validate_production_readiness
    setup_monitoring
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "Deployment completed successfully in ${duration} seconds"
    log "Deployment finished at: $(date)"
    
    # Display service status
    echo
    log "📊 Final Service Status:"
    systemctl status trading-* --no-pager -l || true
    
    echo
    log "🌐 Access Points:"
    log "  - Monitoring Dashboard: http://localhost:5000"
    log "  - Service Logs: journalctl -u trading-* -f"
    log "  - Health Checks: python tools/deployment_manager.py status"
    
    echo
    log_success "Trading System is now running in production!"
}

# Command line interface
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback_deployment
        ;;
    "health")
        run_health_checks
        ;;
    "validate")
        validate_production_readiness
        ;;
    "backup")
        create_deployment_backup
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|health|validate|backup}"
        echo "  deploy   - Full production deployment"
        echo "  rollback - Rollback to previous version"
        echo "  health   - Run health checks"
        echo "  validate - Validate production readiness"
        echo "  backup   - Create system backup"
        exit 1
        ;;
esac
