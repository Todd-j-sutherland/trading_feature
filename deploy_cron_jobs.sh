#!/bin/bash

# =============================================================================
# ASX Trading System - Cron Job Deployment Script
# =============================================================================
# This script deploys all necessary cron jobs for the trading system
# Based on SYSTEM_ARCHITECTURE.md specifications
# 
# Components:
# 1. Market Hours Predictions (Every 30 minutes, 00:00-06:00 UTC)
# 2. Hourly Outcome Evaluation 
# 3. Daily Evening ML Training (08:00 UTC)
# 4. Comprehensive Dashboard Updates
# =============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER="root@170.64.199.151"
WORK_DIR="/root/test"
LOG_DIR="/root/test/logs"

echo -e "${BLUE}🚀 ASX Trading System - Cron Job Deployment${NC}"
echo -e "${BLUE}=============================================${NC}"
echo "📅 $(date)"
echo ""

# Function to create log directory
create_log_directory() {
    echo -e "${YELLOW}📁 Creating log directory...${NC}"
    ssh $SERVER "mkdir -p $LOG_DIR"
}

# Function to backup existing crontab
backup_crontab() {
    echo -e "${YELLOW}💾 Backing up existing crontab...${NC}"
    ssh $SERVER "crontab -l > $WORK_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo 'No existing crontab'"
}

# Function to deploy the comprehensive cron configuration
deploy_cron_jobs() {
    echo -e "${YELLOW}⚙️  Deploying comprehensive cron configuration...${NC}"
    
    ssh $SERVER 'cat > /tmp/trading_crontab << '"'"'EOF'"'"'
# =============================================================================
# ASX Trading System - Complete Cron Configuration
# =============================================================================
# Deployed: $(date)
# System Architecture: Enhanced 3-Component System
# Working Directory: /root/test
# =============================================================================

# Environment Variables
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
PYTHONPATH=/root/test

# =============================================================================
# 1. MARKET HOURS PREDICTIONS (Every 30 minutes during 00:00-06:00 UTC)
# =============================================================================
# Generate enhanced predictions with 53 feature vectors and market context
# Runs: :00 and :30 minutes during market hours
# OPTION 1: Market-Aware Enhanced System (recommended)
0,30 0-5 * * * cd /root/test && /root/trading_venv/bin/python -m app.main_enhanced market-morning >> logs/market_aware_morning.log 2>&1

# OPTION 2: Fallback to original system (if market-aware not available)
# 0,30 0-5 * * * cd /root/test && /root/trading_venv/bin/python enhanced_efficient_system.py >> logs/cron_prediction.log 2>&1

# =============================================================================
# 2. HOURLY OUTCOME EVALUATION (Every hour)
# =============================================================================
# Evaluate predictions against actual market movement
# Store results in outcomes table
0 * * * * cd /root/test && bash evaluate_predictions.sh >> logs/evaluation.log 2>&1

# =============================================================================
# 3. DAILY MODEL RETRAINING (08:00 UTC Daily) - ENHANCED
# =============================================================================
# Automatic model retraining with performance validation
0 8 * * * cd /root/test && /root/trading_venv/bin/python enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py >> logs/evening_ml_training.log 2>&1

# =============================================================================
# 3.1 WEEKLY DEEP MODEL RETRAINING (Sunday 06:00 UTC)
# =============================================================================
# Comprehensive model retraining with extended historical data
0 6 * * 0 cd /root/test && /root/trading_venv/bin/python manual_retrain_models.py >> logs/weekly_deep_training.log 2>&1

# =============================================================================
# 4. IG MARKETS PRICE VALIDATION (Every 4 hours during market days)
# =============================================================================
# Validate IG Markets API and price accuracy
0 */4 * * 1-5 cd /root/test && /root/trading_venv/bin/python test_ig_asx_prices.py >> logs/ig_price_validation.log 2>&1

# =============================================================================
# 5. COMPREHENSIVE DASHBOARD UPDATES (Every 4 hours)
# =============================================================================
# Update dashboard with latest analysis and performance metrics
0 */4 * * * cd /root/test && /root/trading_venv/bin/streamlit run comprehensive_table_dashboard.py --server.headless=true --server.port=8502 >> logs/dashboard_updates.log 2>&1

# =============================================================================
# 5.1 MARKET-AWARE SIGNAL GENERATION (Every 2 hours during market hours)
# =============================================================================
# Generate market-aware trading signals with updated context
0 */2 0-5 * * * cd /root/test && /root/trading_venv/bin/python -m app.main_enhanced market-signals >> logs/market_aware_signals.log 2>&1

# =============================================================================
# 6. SYSTEM HEALTH MONITORING (Every 2 hours)
# =============================================================================
# Monitor system health, memory usage, and process status
0 */2 * * * cd /root/test && /root/trading_venv/bin/python -c "
import psutil
import datetime
print(f\"[{datetime.datetime.now()}] Memory: {psutil.virtual_memory().percent:.1f}%, CPU: {psutil.cpu_percent():.1f}%\")
" >> logs/system_health.log 2>&1

# =============================================================================
# 7. DATABASE MAINTENANCE (Daily at 02:00 UTC)
# =============================================================================
# Optimize database performance and fix locking issues
0 2 * * * cd /root/test && sqlite3 data/trading_predictions.db "VACUUM; REINDEX;" >> logs/db_maintenance.log 2>&1

# =============================================================================
# 8. LOG ROTATION (Daily at 03:00 UTC)
# =============================================================================
# Prevent log files from growing too large
0 3 * * * cd /root/test/logs && find . -name "*.log" -size +50M -exec mv {} {}.$(date +%Y%m%d) \; >> log_rotation.log 2>&1

# =============================================================================
# 9. DATABASE MAINTENANCE (Weekly on Sunday at 04:00 UTC)
# =============================================================================
# Deep database optimization and integrity check
0 4 * * 0 cd /root/test && sqlite3 data/trading_predictions.db "PRAGMA integrity_check; VACUUM; REINDEX;" >> logs/weekly_db_maintenance.log 2>&1

EOF'

    # Install the new crontab
    ssh $SERVER "crontab /tmp/trading_crontab"
    ssh $SERVER "rm /tmp/trading_crontab"
}

# Function to verify cron deployment
verify_deployment() {
    echo -e "${YELLOW}🔍 Verifying cron deployment...${NC}"
    echo ""
    echo -e "${BLUE}Current crontab:${NC}"
    ssh $SERVER "crontab -l"
    echo ""
}

# Function to check system status
check_system_status() {
    echo -e "${YELLOW}📊 Checking system status...${NC}"
    
    ssh $SERVER "
    echo '🔍 SYSTEM STATUS CHECK'
    echo '===================='
    echo '📅 Current Time (UTC): \$(date -u)'
    echo ''
    
    echo '📁 Working Directory:'
    ls -la $WORK_DIR/enhanced_efficient_system.py $WORK_DIR/comprehensive_table_dashboard.py 2>/dev/null || echo 'Files not found'
    echo ''
    
    echo '📁 Log Directory:'
    ls -la $LOG_DIR/ 2>/dev/null || echo 'Log directory not found'
    echo ''
    
    echo '💾 Database Status:'
    ls -la $WORK_DIR/data/trading_predictions.db 2>/dev/null || echo 'Database not found'
    echo ''
    
    echo '🧠 Memory Usage:'
    free -h | head -2
    echo ''
    
    echo '⚡ Process Status:'
    ps aux | grep -E '(enhanced_|comprehensive_|python)' | grep -v grep || echo 'No relevant processes running'
    "
}

# Function to test next cron execution
test_next_execution() {
    echo -e "${YELLOW}⏰ Testing next scheduled execution...${NC}"
    
    ssh $SERVER "
    echo '⏰ NEXT EXECUTION TIMES'
    echo '====================='
    echo '📅 Current UTC Time: \$(date -u)'
    echo ''
    
    # Check if we're in market hours
    current_hour=\$(date -u +%H)
    current_minute=\$(date -u +%M)
    
    if [ \$current_hour -ge 0 ] && [ \$current_hour -le 5 ]; then
        echo '✅ Currently in market hours (00:00-05:59 UTC)'
        
        # Calculate next 30-minute mark
        if [ \$current_minute -lt 30 ]; then
            next_minute=30
            next_hour=\$current_hour
        else
            next_minute=0
            next_hour=\$((current_hour + 1))
            if [ \$next_hour -gt 5 ]; then
                echo '⏰ Next prediction: Tomorrow at 00:00 UTC'
            else
                echo \"⏰ Next prediction: \$(printf '%02d:%02d' \$next_hour \$next_minute) UTC\"
            fi
        fi
    else
        echo '⏸️  Outside market hours (00:00-05:59 UTC)'
        echo '⏰ Next prediction: Tomorrow at 00:00 UTC'
    fi
    
    echo ''
    echo '📅 Daily Schedules:'
    echo '  • Evening ML Training: 08:00 UTC'
    echo '  • Dashboard Updates: Every 4 hours'
    echo '  • Outcome Evaluation: Every hour'
    echo '  • System Health: Every 2 hours'
    "
}

# Main execution
main() {
    echo -e "${GREEN}Starting cron deployment process...${NC}"
    echo ""
    
    create_log_directory
    backup_crontab
    deploy_cron_jobs
    verify_deployment
    check_system_status
    test_next_execution
    
    echo ""
    echo -e "${GREEN}✅ Cron deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Summary:${NC}"
    echo "• Market-aware predictions: Every 30 minutes (00:00-05:59 UTC)"
    echo "• Market-aware signals: Every 2 hours during market hours"
    echo "• Outcome evaluation: Every hour"
    echo "• ML training: Daily at 08:00 UTC"
    echo "• Dashboard updates: Every 4 hours"
    echo "• System monitoring: Every 2 hours"
    echo "• Log rotation: Daily at 02:00 UTC"
    echo "• Database maintenance: Weekly on Sunday"
    echo ""
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo "1. Monitor logs in $LOG_DIR/"
    echo "2. Check market-aware logs: market_aware_morning.log, market_aware_signals.log"
    echo "3. Verify predictions during market hours"
    echo "4. Review ML training results daily"
    echo "5. Test market-aware commands: python -m app.main_enhanced market-status"
}

# Execute main function
main
