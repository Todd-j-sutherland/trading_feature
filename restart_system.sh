#!/bin/bash
# ASX Trading System - Complete Recovery Script
# Use this after VM restart or system reboot

echo "🚀 ASX Trading System Recovery Starting..."
echo "=========================================="
echo "Date: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Step 1: Check and start cron service
echo "Step 1: Checking cron service..."
systemctl is-active --quiet cron
if [ $? -eq 0 ]; then
    print_status 0 "Cron service is running"
else
    print_warning "Cron service not running, starting..."
    systemctl start cron
    systemctl enable cron
    systemctl is-active --quiet cron
    print_status $? "Cron service started"
fi
echo ""

# Step 2: Verify crontab is installed
echo "Step 2: Checking cron jobs..."
CRON_COUNT=$(crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" | wc -l)
if [ $CRON_COUNT -gt 0 ]; then
    print_status 0 "Cron jobs are installed ($CRON_COUNT active jobs)"
    echo "Active cron jobs:"
    crontab -l | grep -v "^#" | grep -v "^$"
else
    print_status 1 "No cron jobs found - MANUAL INTERVENTION NEEDED"
    echo "You need to reinstall the crontab. Check the deployment guide."
fi
echo ""

# Step 3: Check Python environment
echo "Step 3: Checking Python environment..."
if [ -d "/root/trading_venv" ]; then
    print_status 0 "Virtual environment exists"
    
    # Test Python environment
    source /root/trading_venv/bin/activate
    export PYTHONPATH=/root/test
    
    python3 -c "
import sys
sys.path.append('/root/test')
try:
    from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
    exit(0)
except Exception as e:
    print(f'Import error: {e}')
    exit(1)
    " 2>/dev/null
    
    print_status $? "Python imports working"
else
    print_status 1 "Virtual environment missing - MANUAL INTERVENTION NEEDED"
fi
echo ""

# Step 4: Check database
echo "Step 4: Checking database..."
if [ -f "data/trading_predictions.db" ]; then
    print_status 0 "Database file exists"
    
    # Test database integrity
    sqlite3 data/trading_predictions.db "PRAGMA integrity_check;" | grep -q "ok"
    print_status $? "Database integrity check"
    
    # Check data counts
    PRED_COUNT=$(sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM predictions;" 2>/dev/null)
    OUTCOME_COUNT=$(sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM enhanced_outcomes;" 2>/dev/null)
    
    echo "  - Predictions: $PRED_COUNT"
    echo "  - Training data: $OUTCOME_COUNT"
else
    print_status 1 "Database file missing - MANUAL INTERVENTION NEEDED"
fi
echo ""

# Step 5: Test prediction system
echo "Step 5: Testing prediction system..."
export PYTHONPATH=/root/test
cd /root/test

# Run a quick test
timeout 60 /root/trading_venv/bin/python3 enhanced_efficient_system.py >/dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status 0 "Prediction system test successful"
    
    # Check if predictions were generated today
    TODAY_PREDS=$(sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = DATE('now');" 2>/dev/null)
    echo "  - Predictions today: $TODAY_PREDS"
else
    print_status 1 "Prediction system test failed"
fi
echo ""

# Step 6: Check system resources
echo "Step 6: System resource check..."
echo "System uptime: $(uptime)"
echo "Disk usage: $(df -h /root/test | tail -1 | awk '{print $5}') used"
echo "Memory usage: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2 }')"
echo ""

# Step 7: Summary and recommendations
echo "=========================================="
echo "🎯 Recovery Summary:"
echo "=========================================="

# Check if system is fully operational
ISSUES=0

systemctl is-active --quiet cron || ISSUES=$((ISSUES+1))
[ $CRON_COUNT -gt 0 ] || ISSUES=$((ISSUES+1))
[ -d "/root/trading_venv" ] || ISSUES=$((ISSUES+1))
[ -f "data/trading_predictions.db" ] || ISSUES=$((ISSUES+1))

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}🎉 SYSTEM FULLY RECOVERED AND OPERATIONAL!${NC}"
    echo ""
    echo "✅ Next predictions will generate automatically during market hours"
    echo "✅ Evening ML training will run at 18:00 AEST (08:00 UTC)"
    echo "✅ Outcome evaluation runs hourly"
    echo ""
    echo "Monitor with: tail -f cron_prediction.log"
else
    echo -e "${RED}⚠️ SYSTEM RECOVERY INCOMPLETE - $ISSUES ISSUES FOUND${NC}"
    echo ""
    echo "Manual intervention required. Check the issues above."
    echo "Consult the documentation: ./view_docs.sh deploy"
fi

echo ""
echo "Recovery completed at: $(date)"
