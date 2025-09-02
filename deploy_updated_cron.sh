#!/bin/bash
# Update Cron Jobs for ASX Trading System with IG Markets + Paper Trading
# Safe deployment script with backup and verification

set -e  # Exit on any error

echo "🚀 Updating Cron Jobs for ASX Trading System with IG Markets Integration"
echo "============================================================================"

# Configuration
BACKUP_DIR="/root/test/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CRON_BACKUP_FILE="$BACKUP_DIR/crontab_backup_$TIMESTAMP.txt"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "📋 Step 1: Backing up current crontab..."
crontab -l > "$CRON_BACKUP_FILE" 2>/dev/null || echo "# No existing crontab found" > "$CRON_BACKUP_FILE"
echo "✅ Current crontab backed up to: $CRON_BACKUP_FILE"

echo "📋 Step 2: Checking system requirements..."

# Check if main application directory exists
if [ ! -d "/root/test" ]; then
    echo "❌ Main application directory /root/test not found!"
    exit 1
fi

# Check if paper trading directory exists
if [ ! -d "/root/test/paper-trading-app" ]; then
    echo "⚠️ Paper trading directory not found - creating it..."
    mkdir -p "/root/test/paper-trading-app"
fi

# Check virtual environments
if [ ! -d "/root/trading_venv" ]; then
    echo "❌ Main trading virtual environment not found at /root/trading_venv!"
    exit 1
fi

if [ ! -d "/root/test/paper-trading-app/paper_trading_venv" ]; then
    echo "⚠️ Paper trading virtual environment not found - will note in cron setup"
fi

# Check required log directory
mkdir -p "/root/test/logs"

echo "✅ System requirements checked"

echo "📋 Step 3: Installing new crontab..."

# Create the new crontab
cat > "/tmp/new_crontab.txt" << 'EOF'
# Updated Cron Jobs for ASX Trading System with IG Markets + Paper Trading
# Generated: September 2025 - Auto-deployed

# =============================================================================
# MAIN APPLICATION - ASX Trading System with IG Markets Integration
# =============================================================================

# Morning routine with IG Markets integration - 09:30 AEST (23:30 UTC previous day)
30 23 * * 0-4 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -m app.main morning >> /root/test/logs/morning_ig_markets.log 2>&1

# Enhanced predictions with IG Markets - Every 30 minutes during ASX market hours
# ASX Hours: 10:00-16:00 AEST = 00:00-06:00 UTC (UTC+10 timezone)
*/30 0-5 * * 1-5 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python enhanced_efficient_system.py >> /root/test/logs/predictions_ig_markets.log 2>&1

# Enhanced evening analysis with IG Markets data - 18:00 AEST (08:00 UTC) weekdays
0 8 * * 1-5 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -m app.main evening >> /root/test/logs/evening_ig_markets.log 2>&1

# Daily status check with IG Markets health - 08:00 AEST (22:00 UTC previous day)
0 22 * * 0-4 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -m app.main status >> /root/test/logs/daily_status_ig_markets.log 2>&1

# IG Markets integration test - Daily at 07:00 AEST (21:00 UTC previous day)
0 21 * * 0-4 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -m app.main ig-markets-test >> /root/test/logs/ig_markets_test.log 2>&1

# =============================================================================
# PAPER TRADING APPLICATION with IG Markets Integration
# =============================================================================

# Paper trading service startup check - Every 30 minutes during market hours
# Only starts if not already running
*/30 0-5 * * 1-5 cd /root/test/paper-trading-app && if ! pgrep -f "run_paper_trading_ig.py service" > /dev/null; then source ./paper_trading_venv/bin/activate 2>/dev/null || source /root/trading_venv/bin/activate; python run_paper_trading_ig.py service >> /root/test/logs/paper_trading_ig_service.log 2>&1 & fi

# Paper trading health check - Every 2 hours during market hours
0 */2 * * 1-5 cd /root/test/paper-trading-app && (source ./paper_trading_venv/bin/activate 2>/dev/null || source /root/trading_venv/bin/activate) && python -c "import sys; sys.path.append('.'); from enhanced_paper_trading_service_with_ig import EnhancedPaperTradingServiceWithIG; service = EnhancedPaperTradingServiceWithIG(); summary = service.get_enhanced_portfolio_summary(); print(f'Portfolio: {summary.get(\"active_positions\", 0)} positions, P&L: \${summary.get(\"total_profit\", 0):.2f}')" >> /root/test/logs/paper_trading_health.log 2>&1

# Paper trading daily summary - End of trading day 16:30 AEST (06:30 UTC)
30 6 * * 1-5 cd /root/test/paper-trading-app && (source ./paper_trading_venv/bin/activate 2>/dev/null || source /root/trading_venv/bin/activate) && python -c "import sys; sys.path.append('.'); from enhanced_paper_trading_service_with_ig import EnhancedPaperTradingServiceWithIG; import json; from datetime import datetime; service = EnhancedPaperTradingServiceWithIG(); summary = service.get_enhanced_portfolio_summary(); print(f'=== Paper Trading Daily Summary - {datetime.now().strftime(\"%Y-%m-%d\")} ==='); print(json.dumps(summary, indent=2, default=str))" >> /root/test/logs/paper_trading_daily_summary.log 2>&1

# =============================================================================
# SHARED MAINTENANCE & MONITORING
# =============================================================================

# Hourly prediction outcome evaluation (shared between both systems)
0 * * * * cd /root/test && source /root/trading_venv/bin/activate && ./evaluate_predictions.sh >> /root/test/logs/prediction_evaluation.log 2>&1

# Weekly maintenance - Sunday 20:00 AEST (10:00 UTC)
0 10 * * 0 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -m app.main weekly >> /root/test/logs/weekly_maintenance.log 2>&1

# Database backup - Daily at 02:00 AEST (16:00 UTC previous day)
0 16 * * * cd /root/test && mkdir -p backups && tar -czf "backups/trading_data_backup_$(date +\%Y\%m\%d).tar.gz" data/ paper-trading-app/*.db logs/ 2>/dev/null >> /root/test/logs/backup.log 2>&1

# IG Markets health monitoring - Every 4 hours during business days
0 */4 * * 1-5 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -c "from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector; import datetime; collector = EnhancedMarketDataCollector(); health = collector.is_ig_markets_healthy(); stats = collector.get_data_source_stats(); print(f'{datetime.datetime.now()}: IG Markets Health: {\"OK\" if health else \"FAIL\"}, Requests: IG={stats.get(\"ig_markets\", 0)} yfinance={stats.get(\"yfinance\", 0)}')" >> /root/test/logs/ig_markets_health.log 2>&1 || echo "$(date): IG Markets health check failed" >> /root/test/logs/ig_markets_health.log 2>&1

# System health check - Every 6 hours
0 */6 * * * echo "=== System Health $(date) ===" >> /root/test/logs/system_health.log && df -h /root/test >> /root/test/logs/system_health.log && uptime >> /root/test/logs/system_health.log && ps aux | grep -E "(python|trading)" | grep -v grep >> /root/test/logs/system_health.log && echo "" >> /root/test/logs/system_health.log

# Log rotation - Weekly on Sunday at 01:00 AEST (15:00 UTC Saturday)
0 15 * * 6 cd /root/test/logs && for log in *.log; do [ -f "$log" ] && [ $(stat -c%s "$log") -gt 10485760 ] && mv "$log" "${log}.$(date +\%Y\%m\%d)" && touch "$log"; done && echo "$(date): Log rotation completed" >> /root/test/logs/maintenance.log 2>&1

# =============================================================================
# CLEANUP & OPTIMIZATION
# =============================================================================

# Clean old backup files - Monthly on 1st at 03:00 AEST (17:00 UTC previous day)
0 17 1 * * find /root/test/backups -name "*.tar.gz" -mtime +30 -delete 2>/dev/null && echo "$(date): Old backups cleaned" >> /root/test/logs/cleanup.log 2>&1

# Clean old log files - Monthly on 1st at 03:30 AEST (17:30 UTC previous day)
30 17 1 * * find /root/test/logs -name "*.log.*" -mtime +7 -delete 2>/dev/null && echo "$(date): Old logs cleaned" >> /root/test/logs/cleanup.log 2>&1

# Database optimization - Weekly on Sunday at 03:00 AEST (17:00 UTC Saturday)
0 17 * * 6 cd /root/test && sqlite3 data/trading_predictions.db "VACUUM;" 2>/dev/null && [ -f paper-trading-app/paper_trading.db ] && sqlite3 paper-trading-app/paper_trading.db "VACUUM;" 2>/dev/null; echo "$(date): Database optimization completed" >> /root/test/logs/maintenance.log 2>&1
EOF

# Install the new crontab
crontab "/tmp/new_crontab.txt"

echo "✅ New crontab installed successfully"

echo "📋 Step 4: Verifying installation..."

# Show the installed crontab
echo ""
echo "📋 Currently active cron jobs:"
echo "============================================================================"
crontab -l | grep -v "^#" | grep -v "^$" | head -10
echo "... (showing first 10 active jobs, see full list with 'crontab -l')"
echo ""

# Check cron service status
if systemctl is-active --quiet cron; then
    echo "✅ Cron service is running"
else
    echo "⚠️ Starting cron service..."
    systemctl start cron
    systemctl enable cron
    echo "✅ Cron service started and enabled"
fi

echo "📋 Step 5: Creating monitoring scripts..."

# Create a simple status check script
cat > "/root/test/check_trading_status.sh" << 'EOF'
#!/bin/bash
# Quick status check for both trading systems

echo "🔍 ASX Trading System Status - $(date)"
echo "=============================================="

echo "📊 Main Application:"
if cd /root/test && source /root/trading_venv/bin/activate 2>/dev/null; then
    export PYTHONPATH=/root/test
    python -m app.main status 2>/dev/null | tail -5 || echo "  ❌ Main app status check failed"
else
    echo "  ❌ Failed to activate main trading environment"
fi

echo ""
echo "📈 Paper Trading:"
if cd /root/test/paper-trading-app 2>/dev/null; then
    if pgrep -f "run_paper_trading_ig.py service" > /dev/null; then
        echo "  ✅ Paper trading service is running"
    else
        echo "  ⚠️ Paper trading service is not running"
    fi
    
    if [ -f "paper_trading.db" ]; then
        positions=$(sqlite3 paper_trading.db "SELECT COUNT(*) FROM enhanced_positions WHERE status='OPEN';" 2>/dev/null || echo "0")
        echo "  📊 Active positions: $positions"
    else
        echo "  ⚠️ Paper trading database not found"
    fi
else
    echo "  ❌ Paper trading directory not accessible"
fi

echo ""
echo "🗄️ Database Status:"
if [ -f "/root/test/data/trading_predictions.db" ]; then
    predictions_today=$(sqlite3 /root/test/data/trading_predictions.db "SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = DATE('now');" 2>/dev/null || echo "0")
    echo "  📈 Predictions today: $predictions_today"
else
    echo "  ❌ Main predictions database not found"
fi

echo ""
echo "💾 Disk Usage:"
df -h /root/test | tail -1

echo ""
echo "⚙️ Recent Log Activity:"
if [ -d "/root/test/logs" ]; then
    echo "  Last IG Markets test: $([ -f /root/test/logs/ig_markets_test.log ] && tail -1 /root/test/logs/ig_markets_test.log | cut -d' ' -f1-2 || echo 'Never')"
    echo "  Last prediction: $([ -f /root/test/logs/predictions_ig_markets.log ] && tail -1 /root/test/logs/predictions_ig_markets.log | cut -d' ' -f1-2 || echo 'Never')"
else
    echo "  ❌ Logs directory not found"
fi
EOF

chmod +x "/root/test/check_trading_status.sh"

echo "✅ Status check script created: /root/test/check_trading_status.sh"

echo "📋 Step 6: Testing key components..."

# Test main application
echo "🧪 Testing main application..."
if cd /root/test && source /root/trading_venv/bin/activate 2>/dev/null; then
    export PYTHONPATH=/root/test
    if timeout 30 python -c "import app.main; print('✅ Main app imports successfully')" 2>/dev/null; then
        echo "✅ Main application test passed"
    else
        echo "⚠️ Main application test failed - check imports and dependencies"
    fi
else
    echo "⚠️ Could not activate main trading environment"
fi

# Test paper trading if directory exists
if [ -d "/root/test/paper-trading-app" ]; then
    echo "🧪 Testing paper trading application..."
    if cd /root/test/paper-trading-app; then
        if [ -f "run_paper_trading_ig.py" ]; then
            echo "✅ Paper trading app files found"
        else
            echo "⚠️ Paper trading IG integration files not found"
        fi
    fi
else
    echo "⚠️ Paper trading directory not found - will be created when needed"
fi

echo "📋 Step 7: Final recommendations..."

echo ""
echo "🎉 Cron jobs update completed successfully!"
echo "=============================================="
echo ""
echo "📋 Next Steps:"
echo "1. ✅ Cron jobs updated with IG Markets integration"
echo "2. ✅ Backup created: $CRON_BACKUP_FILE"
echo "3. ✅ Status monitoring script created"
echo ""
echo "💡 Immediate Actions:"
echo "• Run status check: /root/test/check_trading_status.sh"
echo "• Monitor logs: tail -f /root/test/logs/ig_markets_test.log"
echo "• Test IG Markets: cd /root/test && python -m app.main ig-markets-test"
echo ""
echo "📊 Monitoring Commands:"
echo "• View all cron jobs: crontab -l"
echo "• Check cron logs: grep CRON /var/log/syslog | tail -20"
echo "• System status: /root/test/check_trading_status.sh"
echo ""
echo "🔄 Rollback (if needed):"
echo "• Restore previous cron: crontab $CRON_BACKUP_FILE"
echo ""
echo "⏰ Schedule Summary:"
echo "• Main app morning routine: 09:30 AEST daily"
echo "• Predictions with IG Markets: Every 30 min during market hours"
echo "• Paper trading: Continuous during market hours"
echo "• IG Markets health checks: Every 4 hours"
echo "• Daily summaries: 16:30 AEST"
echo ""

# Final verification
echo "📋 Final Verification:"
if crontab -l | grep -q "ig-markets-test"; then
    echo "✅ IG Markets integration cron jobs are active"
else
    echo "❌ IG Markets cron jobs may not be properly installed"
fi

if crontab -l | grep -q "paper_trading"; then
    echo "✅ Paper trading cron jobs are active"
else
    echo "⚠️ Paper trading cron jobs not found (may need paper trading setup)"
fi

echo ""
echo "🚀 System is ready for IG Markets integrated trading!"

# Clean up
rm -f "/tmp/new_crontab.txt"
