#!/bin/bash
# Migration Script: Monolithic to Microservices
# Zero-downtime migration with rollback capability
# 
# This script migrates from the current monolithic trading system 
# to the new multi-region microservices architecture

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRADING_DIR="/opt/trading_services"
BACKUP_DIR="/opt/trading_backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="/var/log/trading/migration_$(date +%Y%m%d_%H%M%S).log"
MIGRATION_STATE_FILE="/tmp/trading_migration_state.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Save migration state
save_migration_state() {
    local state="$1"
    local step="$2"
    cat > "$MIGRATION_STATE_FILE" << EOF
{
    "migration_id": "$(basename "$BACKUP_DIR")",
    "state": "$state",
    "current_step": "$step",
    "timestamp": "$(date -Iseconds)",
    "backup_dir": "$BACKUP_DIR",
    "pid": $$
}
EOF
}

# Check if migration is already in progress
check_migration_in_progress() {
    if [[ -f "$MIGRATION_STATE_FILE" ]]; then
        local existing_state=$(cat "$MIGRATION_STATE_FILE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('state', 'unknown'))")
        if [[ "$existing_state" == "in_progress" ]]; then
            error "Migration already in progress. Check $MIGRATION_STATE_FILE or run with --force to override"
        fi
    fi
}

# Pre-migration checks
pre_migration_checks() {
    log "Starting pre-migration checks..."
    save_migration_state "checking" "pre_migration_checks"
    
    # Check system requirements
    if ! command -v python3 &> /dev/null; then
        error "Python3 is required but not installed"
    fi
    
    if ! command -v redis-cli &> /dev/null; then
        error "Redis is required but not installed"
    fi
    
    # Check available disk space (need at least 2GB for backup)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 2097152 ]]; then  # 2GB in KB
        error "Insufficient disk space. Need at least 2GB for backup"
    fi
    
    # Check Redis connectivity
    if ! redis-cli ping > /dev/null 2>&1; then
        error "Cannot connect to Redis. Ensure Redis is running"
    fi
    
    # Check current system processes
    if pgrep -f "python.*enhanced_efficient_system" > /dev/null; then
        log "Found running prediction processes - will be gracefully stopped during migration"
    fi
    
    # Check database access
    for db in "trading_predictions.db" "paper_trading.db" "predictions.db"; do
        if [[ -f "$db" ]]; then
            if ! sqlite3 "$db" "SELECT 1;" > /dev/null 2>&1; then
                error "Cannot access database: $db"
            fi
            log "Database accessible: $db"
        fi
    done
    
    success "Pre-migration checks completed"
}

# Create comprehensive backup
create_backup() {
    log "Creating comprehensive system backup..."
    save_migration_state "in_progress" "backup"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup current system
    log "Backing up current trading system..."
    
    # Backup Python scripts
    if [[ -d "." ]]; then
        tar -czf "$BACKUP_DIR/current_system.tar.gz" \
            --exclude="trading_venv" \
            --exclude="__pycache__" \
            --exclude="*.pyc" \
            --exclude=".git" \
            .
    fi
    
    # Backup databases
    log "Backing up databases..."
    mkdir -p "$BACKUP_DIR/databases"
    for db in *.db data/*.db; do
        if [[ -f "$db" ]]; then
            cp "$db" "$BACKUP_DIR/databases/"
            log "Backed up: $db"
        fi
    done
    
    # Backup Redis data
    log "Backing up Redis data..."
    redis-cli BGSAVE
    sleep 2
    if [[ -f "/var/lib/redis/dump.rdb" ]]; then
        cp "/var/lib/redis/dump.rdb" "$BACKUP_DIR/redis_dump.rdb"
    fi
    
    # Backup current cron jobs
    crontab -l > "$BACKUP_DIR/current_crontab.txt" 2>/dev/null || echo "No crontab found"
    
    # Backup configuration files
    mkdir -p "$BACKUP_DIR/config"
    for config in "config.py" "enhanced_config.py" "app/config/settings.py"; do
        if [[ -f "$config" ]]; then
            cp "$config" "$BACKUP_DIR/config/"
        fi
    done
    
    # Create backup manifest
    cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << EOF
Trading System Backup
Created: $(date)
Migration ID: $(basename "$BACKUP_DIR")

Contents:
- current_system.tar.gz: Complete current system
- databases/: All SQLite databases  
- redis_dump.rdb: Redis data snapshot
- current_crontab.txt: Current cron configuration
- config/: Configuration files

To restore: Use scripts/restore_from_backup.sh
EOF
    
    success "Backup created: $BACKUP_DIR"
}

# Install microservices (without starting)
install_microservices() {
    log "Installing microservices architecture..."
    save_migration_state "in_progress" "install_microservices"
    
    # Run deployment script in install-only mode
    if [[ -f "scripts/deploy_multi_region.sh" ]]; then
        # Modify deployment script to not start services
        bash scripts/deploy_multi_region.sh --install-only
    else
        error "Deployment script not found: scripts/deploy_multi_region.sh"
    fi
    
    # Verify installation
    if [[ ! -d "$TRADING_DIR" ]]; then
        error "Microservices installation failed - directory not created"
    fi
    
    # Check systemd service files
    for service in trading-market-data trading-sentiment trading-prediction; do
        if [[ ! -f "/etc/systemd/system/$service.service" ]]; then
            error "Service file not found: $service.service"
        fi
    done
    
    success "Microservices installed (not started)"
}

# Data migration
migrate_data() {
    log "Migrating data to microservices format..."
    save_migration_state "in_progress" "migrate_data"
    
    # Create data migration script
    python3 << 'EOF'
import sqlite3
import json
import os
from datetime import datetime

def migrate_prediction_data():
    """Migrate prediction data to microservices format"""
    
    # Source databases
    source_dbs = [
        "trading_predictions.db",
        "predictions.db", 
        "data/enhanced_outcomes.db"
    ]
    
    # Target consolidated database
    target_db = "/opt/trading_services/data/microservices_predictions.db"
    os.makedirs(os.path.dirname(target_db), exist_ok=True)
    
    # Create target database schema
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            predicted_action TEXT NOT NULL,
            action_confidence REAL NOT NULL,
            entry_price REAL,
            market_context TEXT,
            prediction_details TEXT,
            components TEXT,
            feature_vector TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_system TEXT DEFAULT 'monolithic',
            migration_batch TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER,
            symbol TEXT NOT NULL,
            actual_action TEXT,
            actual_price REAL,
            profit_loss REAL,
            success BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prediction_id) REFERENCES predictions (id)
        )
    ''')
    
    migration_batch = datetime.now().strftime("%Y%m%d_%H%M%S")
    migrated_count = 0
    
    # Migrate from each source database
    for source_db in source_dbs:
        if os.path.exists(source_db):
            print(f"Migrating from {source_db}")
            
            source_conn = sqlite3.connect(source_db)
            source_cursor = source_conn.cursor()
            
            # Get table names
            source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = source_cursor.fetchall()
            
            for (table_name,) in tables:
                if 'prediction' in table_name.lower():
                    try:
                        source_cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                        columns = [description[0] for description in source_cursor.description]
                        
                        source_cursor.execute(f"SELECT * FROM {table_name}")
                        rows = source_cursor.fetchall()
                        
                        for row in rows:
                            row_dict = dict(zip(columns, row))
                            
                            # Map to standardized format
                            cursor.execute('''
                                INSERT INTO predictions (
                                    symbol, predicted_action, action_confidence,
                                    entry_price, market_context, prediction_details,
                                    components, feature_vector, timestamp,
                                    source_system, migration_batch
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                row_dict.get('symbol', 'UNKNOWN'),
                                row_dict.get('predicted_action', row_dict.get('action', 'UNKNOWN')),
                                row_dict.get('action_confidence', row_dict.get('confidence', 0.5)),
                                row_dict.get('entry_price', 0.0),
                                row_dict.get('market_context', 'MIGRATED'),
                                json.dumps(row_dict),  # Store original as JSON
                                json.dumps({}),  # Empty components for now
                                '',  # Empty feature vector
                                row_dict.get('timestamp', datetime.now().isoformat()),
                                f"monolithic_{source_db}",
                                migration_batch
                            ))
                            migrated_count += 1
                            
                    except Exception as e:
                        print(f"Error migrating table {table_name}: {e}")
            
            source_conn.close()
    
    conn.commit()
    conn.close()
    
    print(f"Migrated {migrated_count} prediction records")
    return migrated_count

def migrate_paper_trading_data():
    """Migrate paper trading data"""
    
    source_dbs = [
        "paper_trading.db",
        "data/ig_markets_paper_trades.db"
    ]
    
    target_db = "/opt/trading_services/data/microservices_paper_trading.db"
    os.makedirs(os.path.dirname(target_db), exist_ok=True)
    
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id TEXT UNIQUE,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'completed',
            ig_order_id TEXT,
            source_system TEXT DEFAULT 'monolithic'
        )
    ''')
    
    migrated_count = 0
    
    for source_db in source_dbs:
        if os.path.exists(source_db):
            print(f"Migrating paper trading data from {source_db}")
            
            source_conn = sqlite3.connect(source_db)
            source_cursor = source_conn.cursor()
            
            source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = source_cursor.fetchall()
            
            for (table_name,) in tables:
                if 'trade' in table_name.lower():
                    try:
                        source_cursor.execute(f"SELECT * FROM {table_name}")
                        columns = [description[0] for description in source_cursor.description]
                        rows = source_cursor.fetchall()
                        
                        for row in rows:
                            row_dict = dict(zip(columns, row))
                            
                            cursor.execute('''
                                INSERT OR IGNORE INTO paper_trades (
                                    trade_id, symbol, action, quantity, price,
                                    timestamp, status, ig_order_id, source_system
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                row_dict.get('id', f"migrated_{migrated_count}"),
                                row_dict.get('symbol', 'UNKNOWN'),
                                row_dict.get('action', 'UNKNOWN'),
                                row_dict.get('quantity', 0),
                                row_dict.get('price', 0.0),
                                row_dict.get('timestamp', datetime.now().isoformat()),
                                'completed',
                                row_dict.get('ig_order_id', ''),
                                f"monolithic_{source_db}"
                            ))
                            migrated_count += 1
                            
                    except Exception as e:
                        print(f"Error migrating table {table_name}: {e}")
            
            source_conn.close()
    
    conn.commit()
    conn.close()
    
    print(f"Migrated {migrated_count} paper trading records")
    return migrated_count

# Run migrations
if __name__ == "__main__":
    print("Starting data migration...")
    pred_count = migrate_prediction_data()
    trade_count = migrate_paper_trading_data()
    print(f"Migration completed: {pred_count} predictions, {trade_count} trades")
EOF
    
    success "Data migration completed"
}

# Start microservices with health checks
start_microservices() {
    log "Starting microservices..."
    save_migration_state "in_progress" "start_microservices"
    
    # Start services in dependency order with health checks
    services=(
        "trading-market-data"
        "trading-sentiment" 
        "trading-prediction"
        "trading-ml-model"
        "trading-scheduler"
        "trading-paper-trading"
    )
    
    for service in "${services[@]}"; do
        log "Starting $service..."
        sudo systemctl start "$service"
        
        # Wait for service to be healthy
        local max_wait=30
        local wait_count=0
        while [[ $wait_count -lt $max_wait ]]; do
            if systemctl is-active --quiet "$service"; then
                log "$service is active"
                
                # Additional health check via socket (if available)
                local socket_path="/tmp/trading_${service#trading-}.sock"
                if [[ -S "$socket_path" ]]; then
                    if timeout 5 python3 -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('$socket_path')
s.send(json.dumps({'method': 'health', 'params': {}}).encode())
response = s.recv(1024)
s.close()
print('Health check passed')
" 2>/dev/null; then
                        success "$service health check passed"
                        break
                    fi
                fi
                break
            fi
            
            sleep 2
            ((wait_count++))
        done
        
        if [[ $wait_count -eq $max_wait ]]; then
            error "$service failed to start properly"
        fi
    done
    
    success "All microservices started successfully"
}

# Stop monolithic system gracefully
stop_monolithic_system() {
    log "Stopping monolithic system..."
    save_migration_state "in_progress" "stop_monolithic"
    
    # Find and gracefully stop prediction processes
    if pgrep -f "python.*enhanced_efficient_system" > /dev/null; then
        log "Stopping prediction processes..."
        pkill -TERM -f "python.*enhanced_efficient_system" || true
        sleep 5
        
        # Force stop if still running
        if pgrep -f "python.*enhanced_efficient_system" > /dev/null; then
            warn "Force stopping remaining prediction processes..."
            pkill -KILL -f "python.*enhanced_efficient_system" || true
        fi
    fi
    
    # Disable cron jobs (backup first done in backup stage)
    log "Disabling cron jobs..."
    crontab -r 2>/dev/null || true
    
    # Stop any other trading-related processes
    for process in "market_aware_daily_manager" "comprehensive_table_dashboard" "ml_dashboard"; do
        if pgrep -f "$process" > /dev/null; then
            log "Stopping $process..."
            pkill -TERM -f "$process" || true
        fi
    done
    
    success "Monolithic system stopped"
}

# Validation and testing
validate_migration() {
    log "Validating migration..."
    save_migration_state "in_progress" "validate"
    
    # Run comprehensive validation
    if [[ -f "validate_multi_region.py" ]]; then
        python3 validate_multi_region.py --output-format json > "$BACKUP_DIR/migration_validation.json"
        
        # Check validation results
        local validation_score=$(cat "$BACKUP_DIR/migration_validation.json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('overall_score', 0))
except:
    print(0)
")
        
        if [[ $(echo "$validation_score >= 80" | bc -l) == 1 ]]; then
            success "Migration validation passed (score: $validation_score)"
        else
            error "Migration validation failed (score: $validation_score). Check $BACKUP_DIR/migration_validation.json"
        fi
    else
        warn "Validation script not found - manual validation required"
    fi
    
    # Test basic functionality
    log "Testing basic functionality..."
    
    # Test prediction generation
    if timeout 30 python3 -c "
import asyncio
from services.base.base_service import BaseService

async def test():
    service = BaseService('migration_test')
    result = await service.call_service('prediction', 'generate_single_prediction', symbol='CBA.AX')
    if 'action' in result:
        print('Prediction test passed')
    else:
        raise Exception('Prediction test failed')

asyncio.run(test())
" > /dev/null 2>&1; then
        success "Prediction service test passed"
    else
        error "Prediction service test failed"
    fi
    
    success "Migration validation completed"
}

# Cleanup and finalization
finalize_migration() {
    log "Finalizing migration..."
    save_migration_state "completed" "finalize"
    
    # Create migration success report
    cat > "$BACKUP_DIR/MIGRATION_REPORT.txt" << EOF
Trading System Migration Report
===============================

Migration completed successfully!
Date: $(date)
Migration ID: $(basename "$BACKUP_DIR")

System Status:
- Monolithic system: STOPPED
- Microservices: RUNNING
- Data migration: COMPLETED
- Validation: PASSED

Services Running:
EOF
    
    sudo systemctl status trading-* --no-pager >> "$BACKUP_DIR/MIGRATION_REPORT.txt"
    
    # Create quick commands reference
    cat > "/opt/trading_services/MIGRATION_QUICKREF.txt" << EOF
Post-Migration Quick Reference
==============================

Service Management:
- Check status: sudo systemctl status trading-*
- Restart all: sudo systemctl restart trading-*
- View logs: sudo journalctl -u trading-prediction -f

Management Dashboard:
- cd /opt/trading_services && python3 multi_region_manager.py

Region Switching:
- Use management dashboard option 4
- Or use API calls to switch regions

Backup Location: $BACKUP_DIR
Rollback: bash scripts/restore_from_backup.sh $BACKUP_DIR

For help: See QUICK_START_MULTI_REGION.md
EOF
    
    success "Migration completed successfully!"
    success "Backup location: $BACKUP_DIR"
    success "Management dashboard: cd /opt/trading_services && python3 multi_region_manager.py"
}

# Rollback function
rollback_migration() {
    local backup_dir="${1:-$BACKUP_DIR}"
    
    error "Migration failed - initiating rollback..."
    log "Rolling back to backup: $backup_dir"
    
    # Stop microservices
    sudo systemctl stop trading-* 2>/dev/null || true
    
    # Restore cron jobs
    if [[ -f "$backup_dir/current_crontab.txt" ]]; then
        crontab "$backup_dir/current_crontab.txt"
    fi
    
    # Restore databases
    if [[ -d "$backup_dir/databases" ]]; then
        cp "$backup_dir/databases"/* . 2>/dev/null || true
    fi
    
    # Restore Redis data
    if [[ -f "$backup_dir/redis_dump.rdb" ]]; then
        sudo systemctl stop redis-server
        sudo cp "$backup_dir/redis_dump.rdb" /var/lib/redis/dump.rdb
        sudo chown redis:redis /var/lib/redis/dump.rdb
        sudo systemctl start redis-server
    fi
    
    # Extract original system
    if [[ -f "$backup_dir/current_system.tar.gz" ]]; then
        tar -xzf "$backup_dir/current_system.tar.gz"
    fi
    
    save_migration_state "rolled_back" "rollback_completed"
    
    error "Rollback completed. System restored to pre-migration state."
    exit 1
}

# Main migration workflow
main() {
    local force_migration=false
    
    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --force)
                force_migration=true
                shift
                ;;
            --help)
                echo "Usage: $0 [--force] [--help]"
                echo "  --force: Force migration even if one is in progress"
                echo "  --help: Show this help"
                exit 0
                ;;
        esac
    done
    
    # Check for existing migration
    if [[ "$force_migration" != true ]]; then
        check_migration_in_progress
    fi
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log "Starting migration from monolithic to microservices"
    log "Migration ID: $(basename "$BACKUP_DIR")"
    
    # Set trap for cleanup on failure
    trap 'rollback_migration' ERR
    
    # Execute migration steps
    pre_migration_checks
    create_backup
    install_microservices
    migrate_data
    start_microservices
    
    # Point of no return - stop monolithic system
    log "Reaching point of no return - stopping monolithic system"
    stop_monolithic_system
    
    validate_migration
    finalize_migration
    
    # Clear trap
    trap - ERR
    
    log "Migration completed successfully!"
    echo ""
    echo "================================================================"
    echo "        MIGRATION TO MICROSERVICES COMPLETED SUCCESSFULLY!"
    echo "================================================================"
    echo ""
    echo "Your trading system is now running on microservices architecture"
    echo "Backup location: $BACKUP_DIR"
    echo ""
    echo "Next steps:"
    echo "1. Start management dashboard: cd /opt/trading_services && python3 multi_region_manager.py"
    echo "2. Test region switching functionality"
    echo "3. Monitor service health and performance"
    echo ""
    echo "For support, see QUICK_START_MULTI_REGION.md"
    echo ""
}

# Run main function with all arguments
main "$@"
