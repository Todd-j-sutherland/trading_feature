#!/bin/bash
"""
Market-Aware Trading System Cron Setup
Replaces existing cron jobs with market-aware enhanced system
"""

echo "🔧 Setting up Market-Aware Trading System Cron Jobs"
echo "=================================================="

# Backup existing crontab
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt
echo "✅ Existing crontab backed up"

# Create new crontab with market-aware system
cat > new_crontab << 'EOF'
# Market-Aware Trading System Cron Jobs
# Updated: September 3, 2025

# Morning Routine - ENABLED with Market-Aware System
# Runs every 30 minutes during ASX market hours (10:00-16:00 AEST = 00:00-06:00 UTC)
*/30 0-5 * * 1-5 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python3 enhanced_efficient_system_market_aware_integrated.py >> /root/test/logs/market_aware_morning.log 2>&1

# Evening Market Analysis & ML Training - 18:00 AEST (08:00 UTC) weekdays
0 8 * * 1-5 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && timeout 300 python3 ./enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py >> /root/test/logs/evening_ml_training.log 2>&1

# Hourly prediction outcome evaluation
0 * * * * /root/test/evaluate_predictions.sh >> /root/test/logs/evaluation.log 2>&1

# Paper Trading Integration - Every hour during market hours
0 0-5 * * 1-5 cd /root/test/paper-trading-app && source /root/test/paper-trading-app/paper_trading_venv/bin/activate && python3 main.py >> /root/test/logs/paper_trading_integration.log 2>&1

# System Health Check - Every 2 hours
0 */2 * * * cd /root/test && echo "$(date): System check" >> /root/test/logs/system_health.log 2>&1

EOF

# Install new crontab
crontab new_crontab
echo "✅ New market-aware crontab installed"

# Verify installation
echo ""
echo "📊 Current Cron Jobs:"
crontab -l

# Test cron service
echo ""
echo "🔍 Testing Cron Service:"
systemctl status cron

# Create logs directory if it doesn't exist
mkdir -p /root/test/logs
echo "✅ Logs directory created"

# Cleanup
rm new_crontab

echo ""
echo "🎯 Market-Aware Cron Setup Complete!"
echo "✅ Morning routine: Every 30 mins during market hours (with market context)"
echo "✅ Evening analysis: Daily at 6PM AEST (8AM UTC)"  
echo "✅ Paper trading: Hourly integration during market hours"
echo "✅ System monitoring: Continuous evaluation and health checks"
