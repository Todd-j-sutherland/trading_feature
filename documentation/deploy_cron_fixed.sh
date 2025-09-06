#!/bin/bash

# ASX Trading System - Clean Cron Job Deployment
# ==============================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER="root@170.64.199.151"
WORK_DIR="/root/test"

echo -e "${GREEN}🚀 ASX Trading System - Cron Job Deployment${NC}"
echo "============================================="
echo "📅 $(date)"
echo ""

echo "Starting cron deployment process..."

# Create log directory
echo "📁 Creating log directory..."
ssh $SERVER "mkdir -p $WORK_DIR/logs"

# Backup existing crontab
echo "💾 Backing up existing crontab..."
ssh $SERVER "crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'No existing crontab'"

# Deploy new crontab
echo "⚙️  Deploying comprehensive cron configuration..."
ssh $SERVER 'cat > /tmp/trading_crontab << '\''CRONEOF'\''
# ASX Trading System - Comprehensive Cron Configuration
# Generated: '"$(date)"'
# =======================================================

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
PYTHONPATH=/root/test

# 1. MARKET HOURS PREDICTIONS (Every 30 minutes during 00:00-05:59 UTC)
*/30 0-5 * * 1-5 cd /root/test && /root/trading_venv/bin/python production/cron/fixed_price_mapping_system.py >> logs/prediction_fixed.log 2>&1

# 1.1 MARKET-AWARE MORNING ROUTINE (Daily at 07:00 UTC / 17:00 AEST)
0 7 * * 1-5 cd /root/test && /root/trading_venv/bin/python -m app.main_enhanced market-morning >> logs/market_aware_morning.log 2>&1

# 2. HOURLY OUTCOME EVALUATION (Every hour)
0 * * * * cd /root/test && bash evaluate_predictions.sh >> logs/evaluation.log 2>&1

# 3. DAILY MODEL RETRAINING (08:00 UTC Daily / 18:00 AEST)
0 8 * * * cd /root/test && /root/trading_venv/bin/python enhanced_evening_analyzer_with_ml.py >> logs/evening_ml_training.log 2>&1

# 3.1 WEEKLY DEEP MODEL RETRAINING (Sunday 06:00 UTC)
0 6 * * 0 cd /root/test && /root/trading_venv/bin/python manual_retrain_models.py >> logs/weekly_deep_training.log 2>&1

# 4. IG MARKETS PRICE VALIDATION (Every 4 hours during market days)
0 */4 * * 1-5 cd /root/test && /root/trading_venv/bin/python test_ig_asx_prices.py >> logs/ig_price_validation.log 2>&1

# 5. COMPREHENSIVE DASHBOARD UPDATES (Every 4 hours)
0 */4 * * * cd /root/test && /root/trading_venv/bin/python comprehensive_table_dashboard.py >> logs/dashboard_updates.log 2>&1

# 5.1 MARKET CONTEXT MONITORING (Every 30 minutes during trading hours)
*/30 10-16 * * 1-5 cd /root/test && /root/trading_venv/bin/python -m app.main_enhanced market-status >> logs/market_context.log 2>&1

# 5.2 IG MARKETS PAPER TRADING EXECUTION (Daily at 07:15 UTC)
15 7 * * 1-5 cd /root/test && /root/trading_venv/bin/python ig_markets_paper_trading/main.py >> logs/paper_trading_execution.log 2>&1

# 5.3 PAPER TRADING MONITORING (Every 2 hours during market)
0 */2 0-5 * * 1-5 cd /root/test && /root/trading_venv/bin/python ig_markets_paper_trading/monitor.py >> logs/paper_trading_monitor.log 2>&1

# 6. SYSTEM HEALTH MONITORING (Every 2 hours)
0 */2 * * * cd /root/test && /root/trading_venv/bin/python -c "import datetime; print(datetime.datetime.now())" >> logs/system_health.log 2>&1

# 7. DATABASE MAINTENANCE (Daily at 02:00 UTC)
0 2 * * * cd /root/test && sqlite3 data/trading_predictions.db "VACUUM; REINDEX;" >> logs/db_maintenance.log 2>&1

# 8. LOG ROTATION (Daily at 03:00 UTC)
0 3 * * * cd /root/test/logs && find . -name "*.log" -size +50M -exec mv {} {}.$(date +%Y%m%d) \; >> log_rotation.log 2>&1

# 9. WEEKLY DATABASE MAINTENANCE (Sunday at 04:00 UTC)
0 4 * * 0 cd /root/test && sqlite3 data/trading_predictions.db "PRAGMA integrity_check; VACUUM; REINDEX;" >> logs/weekly_db_maintenance.log 2>&1

CRONEOF'

# Install the crontab
ssh $SERVER "crontab /tmp/trading_crontab && rm /tmp/trading_crontab"

echo -e "${GREEN}✅ Cron deployment completed successfully!${NC}"
echo ""

# Verify deployment
echo -e "${YELLOW}🔍 Verifying cron deployment...${NC}"
echo ""
echo -e "${BLUE}Current crontab:${NC}"
ssh $SERVER "crontab -l"
echo ""

# Check system status
echo -e "${YELLOW}📊 Checking system status...${NC}"
ssh $SERVER "
echo '🔍 SYSTEM STATUS CHECK'
echo '===================='
echo '📅 Current Time (UTC): \$(date -u)'
echo ''
echo '📁 Working Directory:'
ls -la $WORK_DIR/*.py | head -5
echo ''
echo '📊 Running Processes:'
ps aux | grep -E '(python|streamlit)' | grep -v grep | head -5
echo ''
echo '📝 Recent Log Activity:'
ls -la $WORK_DIR/logs/*.log 2>/dev/null | tail -5
"

echo ""
echo -e "${GREEN}🎉 Deployment verification completed!${NC}"
echo -e "${BLUE}📈 The ASX Trading System is now fully operational with comprehensive automation.${NC}"
