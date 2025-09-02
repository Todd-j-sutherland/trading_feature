# Quick Cron Jobs Restart Guide - IG Markets Integration

## 🚀 **IMMEDIATE SETUP** (Choose one method)

### **Method 1: Automated Deployment (Recommended)**
```bash
# Upload and run the automated deployment script
cd /root/test
chmod +x deploy_updated_cron.sh
./deploy_updated_cron.sh
```

### **Method 2: Manual Installation**
```bash
# Backup current cron jobs
crontab -l > /root/crontab_backup_$(date +%Y%m%d).txt

# Install new cron jobs
cat > /tmp/new_cron.txt << 'EOF'
# Main Application with IG Markets
30 23 * * 0-4 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -m app.main morning >> /root/test/logs/morning_ig_markets.log 2>&1
*/30 0-5 * * 1-5 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python enhanced_efficient_system.py >> /root/test/logs/predictions_ig_markets.log 2>&1
0 8 * * 1-5 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -m app.main evening >> /root/test/logs/evening_ig_markets.log 2>&1
0 21 * * 0-4 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -m app.main ig-markets-test >> /root/test/logs/ig_markets_test.log 2>&1

# Paper Trading (if you have it setup)
*/30 0-5 * * 1-5 cd /root/test/paper-trading-app && if ! pgrep -f "run_paper_trading_ig.py service" > /dev/null; then source ./paper_trading_venv/bin/activate 2>/dev/null || source /root/trading_venv/bin/activate; python run_paper_trading_ig.py service >> /root/test/logs/paper_trading.log 2>&1 & fi

# Shared maintenance
0 * * * * cd /root/test && source /root/trading_venv/bin/activate && ./evaluate_predictions.sh >> /root/test/logs/prediction_evaluation.log 2>&1
0 10 * * 0 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -m app.main weekly >> /root/test/logs/weekly_maintenance.log 2>&1
0 16 * * * cd /root/test && mkdir -p backups && tar -czf "backups/trading_backup_$(date +\%Y\%m\%d).tar.gz" data/ logs/ 2>/dev/null
EOF

# Install the new crontab
crontab /tmp/new_cron.txt
rm /tmp/new_cron.txt
```

---

## ✅ **VERIFICATION**

### Check Installation
```bash
# Verify cron jobs are active
crontab -l | grep -E "(morning|ig-markets|paper_trading)"

# Check cron service
systemctl status cron

# Create logs directory
mkdir -p /root/test/logs
```

### Test Key Components
```bash
# Test main app with IG Markets
cd /root/test
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test
python -m app.main ig-markets-test

# Test status command
python -m app.main status
```

---

## 📊 **NEW SCHEDULE OVERVIEW**

### **Main Application**
- **Morning Routine**: 09:30 AEST daily (with IG Markets health checks)
- **Predictions**: Every 30 minutes during market hours (10:00-16:00 AEST) 
- **Evening Analysis**: 18:00 AEST daily (enhanced with IG Markets data)
- **IG Markets Test**: 07:00 AEST daily (connectivity and health check)
- **Status Check**: 08:00 AEST daily
- **Weekly Maintenance**: Sunday 20:00 AEST

### **Paper Trading (if enabled)**
- **Service**: Continuous during market hours
- **Health Checks**: Every 2 hours during market hours
- **Daily Summary**: 16:30 AEST (end of trading day)

### **Monitoring & Maintenance**
- **Prediction Evaluation**: Every hour
- **IG Markets Health**: Every 4 hours on weekdays
- **System Health**: Every 6 hours
- **Backups**: Daily at 02:00 AEST
- **Log Rotation**: Weekly on Sunday
- **Cleanup**: Monthly on 1st day

---

## 🔍 **MONITORING COMMANDS**

### Quick Status Check
```bash
# Overall system status
/root/test/check_trading_status.sh

# IG Markets specific
tail -f /root/test/logs/ig_markets_test.log
tail -f /root/test/logs/ig_markets_health.log

# Paper trading
tail -f /root/test/logs/paper_trading.log
```

### Database Status
```bash
# Check today's predictions
sqlite3 /root/test/data/trading_predictions.db "SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = DATE('now');"

# Check paper trading positions (if applicable)
sqlite3 /root/test/paper-trading-app/paper_trading.db "SELECT COUNT(*) FROM enhanced_positions WHERE status='OPEN';" 2>/dev/null || echo "No paper trading DB"
```

### Cron Job Logs
```bash
# View recent cron activity
grep CRON /var/log/syslog | tail -20

# Check specific log files
ls -la /root/test/logs/
```

---

## 🚨 **TROUBLESHOOTING**

### If Cron Jobs Don't Run
```bash
# Restart cron service
systemctl restart cron
systemctl enable cron

# Check cron service status
systemctl status cron

# Check for syntax errors
crontab -l | head -5
```

### If IG Markets Tests Fail
```bash
# Check environment variables
cd /root/test
source /root/trading_venv/bin/activate
python -c "import os; print('IG_USERNAME:', bool(os.getenv('IG_USERNAME'))); print('IG_API_KEY:', bool(os.getenv('IG_API_KEY')))"

# Test basic connectivity
python -c "import requests; print('Internet OK' if requests.get('https://api.github.com').status_code == 200 else 'Internet Issue')"
```

### If Paper Trading Fails
```bash
# Check if paper trading directory exists
ls -la /root/test/paper-trading-app/

# Check if files are present
ls -la /root/test/paper-trading-app/run_paper_trading_ig.py

# Test paper trading initialization
cd /root/test/paper-trading-app
python run_paper_trading_ig.py init
```

---

## 🔄 **ROLLBACK PLAN**

### If You Need to Restore Previous Cron Jobs
```bash
# Find your backup
ls -la /root/crontab_backup_*.txt

# Restore the most recent backup
crontab /root/crontab_backup_YYYYMMDD.txt

# Or restore to basic working state
crontab << 'EOF'
0 * * * * /root/test/evaluate_predictions.sh
*/30 0-5 * * 1-5 /root/trading_venv/bin/python3 /root/test/enhanced_efficient_system.py >> /root/test/cron_prediction.log 2>&1
0 8 * * 1-5 cd /root/test && export PYTHONPATH=/root/test && /root/trading_venv/bin/python3 ./enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py >> /root/test/logs/evening_ml_training.log 2>&1
EOF
```

---

## 💡 **KEY DIFFERENCES FROM OLD CRON**

### **What's New:**
✅ IG Markets integration in all main routines  
✅ Paper trading automation  
✅ Enhanced health monitoring  
✅ Better error handling and logging  
✅ IG Markets specific health checks  
✅ Improved backup and maintenance  

### **What's Maintained:**
✅ Same timing for core market activities  
✅ Same prediction frequency (every 30 minutes)  
✅ Same evening analysis schedule  
✅ All existing database operations  

### **What's Enhanced:**
🚀 Real-time IG Markets data instead of yfinance only  
🚀 Paper trading runs parallel to main system  
🚀 Comprehensive monitoring and health checks  
🚀 Better backup and log management  

---

## 🎯 **SUCCESS INDICATORS**

After deployment, you should see:
- ✅ Daily IG Markets test logs showing "HEALTHY" status
- ✅ Predictions logged with IG Markets data source info
- ✅ Paper trading service running during market hours
- ✅ Enhanced system status reports
- ✅ No error messages in main log files

**🚀 Your system is now ready with IG Markets integration!**
