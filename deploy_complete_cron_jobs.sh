#!/bin/bash
# Complete Cron Job Deployment Script
# Deploys all necessary cron jobs for the trading system

echo "🚀 Deploying Trading System Cron Jobs..."

# Backup current crontab
echo "📋 Backing up current crontab..."
crontab -l > /root/test/cron_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null

# Create new crontab with all jobs
echo "⚙️ Installing new cron jobs..."

cat << 'EOF' | crontab -
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
PYTHONPATH=/root/test

# Market predictions every 30 minutes during 00:00-05:59 UTC (10:00-15:59 AEST)
*/30 0-5 * * 1-5 cd /root/test && python3 production/cron/fixed_price_mapping_system.py >> logs/prediction_fixed.log 2>&1

# Hourly outcome evaluation (FIXED VERSION)
0 * * * * cd /root/test && bash evaluate_predictions_fixed.sh >> logs/evaluation_fixed.log 2>&1

# Daily ML training at 08:00 UTC (18:00 AEST)
0 8 * * * cd /root/test && python3 enhanced_evening_analyzer_with_ml.py >> logs/evening_ml_training.log 2>&1

# Dashboard updates every 4 hours
0 */4 * * * cd /root/test && python3 comprehensive_table_dashboard.py >> logs/dashboard_updates.log 2>&1

# System health monitoring every 2 hours
0 */2 * * * cd /root/test && python3 -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent:.1f}%, CPU: {psutil.cpu_percent():.1f}%')" >> logs/system_health.log 2>&1

# Database maintenance daily at 02:00 UTC
0 2 * * * cd /root/test && sqlite3 data/trading_predictions.db "PRAGMA journal_mode=WAL; VACUUM; REINDEX;" >> logs/db_maintenance.log 2>&1

# Weekly model backup (Sunday at 04:00 UTC)
0 4 * * 0 cd /root/test && cp -r data/ml_models/ data/backups/ml_models_$(date +\%Y\%m\%d)/ >> logs/backup.log 2>&1

EOF

echo "✅ Cron jobs deployed successfully!"

# Verify installation
echo "📊 Current cron jobs:"
crontab -l

echo ""
echo "🔍 Job Schedule Summary:"
echo "  - Predictions: Every 30 minutes during market hours (00:00-05:59 UTC)"
echo "  - Evaluations: Every hour (FIXED VERSION)"
echo "  - ML Training: Daily at 08:00 UTC"
echo "  - Dashboard: Every 4 hours"
echo "  - Health Check: Every 2 hours"
echo "  - DB Maintenance: Daily at 02:00 UTC"
echo "  - Model Backup: Weekly on Sunday"
echo ""
echo "📝 Log files will be in /root/test/logs/"
echo "🎯 System is now fully automated!"
