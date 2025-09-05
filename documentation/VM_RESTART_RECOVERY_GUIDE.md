# 🔄 VM Restart & Recovery Guide

**Complete system recovery after virtual machine restart/reboot**

---

## 🚨 **Emergency Situations**

This guide covers:
- ✅ Virtual machine was turned off and on again
- ✅ Server rebooted unexpectedly  
- ✅ System appears to have stopped generating predictions
- ✅ Cron jobs are not running
- ✅ Need to restart all automated processes

---

## ⚡ **QUICK START (30 seconds)**

### **Emergency One-Command Recovery**
```bash
# Single command to recover everything
ssh root@170.64.199.151 'cd /root/test && ./restart_system.sh'
```

**That's it!** The script will automatically:
- ✅ Check and restart cron service
- ✅ Verify all scheduled jobs
- ✅ Test Python environment
- ✅ Validate database integrity
- ✅ Test prediction system
- ✅ Report system status

---

## 🔧 **Manual Step-by-Step Recovery**

*Use this if the automated script fails or you want to understand each step.*

### **Step 1: Connect and Check Services**
```bash
# Connect to the server
ssh root@170.64.199.151

# Navigate to project directory
cd /root/test

# Check if cron service is running
systemctl status cron

# If cron is not running, start it
sudo systemctl start cron
sudo systemctl enable cron
```

### **Step 2: Verify Cron Jobs**
```bash
# Check if your cron jobs are still scheduled
crontab -l

# You should see something like:
# */30 0-6 * * 1-5 cd /root/test && /root/trading_venv/bin/python3 enhanced_efficient_system.py >> cron_prediction.log 2>&1
# 0 8 * * * cd /root/test && timeout 300 /root/trading_venv/bin/python3 ./enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py >> cron_evening.log 2>&1
```

### **Step 3: Test Python Environment**
```bash
# Test if virtual environment works
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test

# Quick import test
python3 -c "
import sys
sys.path.append('/root/test')
from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
print('✅ Python environment working')
"
```

### **Step 4: Test Prediction System**
```bash
# Run prediction system manually once to test
cd /root/test
export PYTHONPATH=/root/test
/root/trading_venv/bin/python3 enhanced_efficient_system.py

# Check if it worked - should see new predictions
sqlite3 data/trading_predictions.db "
SELECT COUNT(*) as predictions_today 
FROM predictions 
WHERE DATE(prediction_timestamp) = DATE('now');
"
```

### **Step 5: Test Database**
```bash
# Verify database is intact
sqlite3 data/trading_predictions.db "
PRAGMA integrity_check;
SELECT 'Total predictions: ' || COUNT(*) FROM predictions;
SELECT 'Enhanced outcomes: ' || COUNT(*) FROM enhanced_outcomes;
"
```

---

## 🩺 **Troubleshooting Common Issues**

### **Problem: Cron jobs disappeared**
```bash
# Reinstall crontab (this should never happen, but just in case)
crontab -e

# Add these lines:
# Predictions every 30 minutes during ASX hours (00:00-06:00 UTC = 10:00-16:00 AEST)
*/30 0-6 * * 1-5 cd /root/test && /root/trading_venv/bin/python3 enhanced_efficient_system.py >> cron_prediction.log 2>&1

# Evening ML training at 08:00 UTC (18:00 AEST)
0 8 * * * cd /root/test && timeout 300 /root/trading_venv/bin/python3 ./enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py >> cron_evening.log 2>&1

# Hourly outcome evaluation during market hours
0 0-6 * * 1-5 cd /root/test && /root/trading_venv/bin/python3 outcome_evaluator.py >> cron_outcomes.log 2>&1
```

### **Problem: Python environment issues**
```bash
# Recreate virtual environment if needed
rm -rf /root/trading_venv
python3 -m venv /root/trading_venv
source /root/trading_venv/bin/activate

# Reinstall packages
pip install scikit-learn pandas numpy yfinance requests beautifulsoup4 lxml python-crontab anthropic
```

### **Problem: Database corruption**
```bash
# Check if database is corrupted
sqlite3 data/trading_predictions.db "PRAGMA integrity_check;"

# If corrupted, you may need to restore from backup
# (Check if you have backups in the data/ directory)
ls -la data/*.db*
```

### **Problem: Disk space full**
```bash
# Check disk usage
df -h

# Clean up old log files if needed
cd /root/test
find . -name "*.log" -mtime +7 -delete
```

---

## 📊 **Verification Checklist**

After recovery, verify these items:

### **✅ System Status**
- [ ] Cron service is active: `systemctl is-active cron`
- [ ] Cron jobs are scheduled: `crontab -l | wc -l` (should be > 0)
- [ ] Virtual environment exists: `ls /root/trading_venv/`
- [ ] Database is accessible: `sqlite3 data/trading_predictions.db "SELECT 1;"`

### **✅ Prediction System**
- [ ] Enhanced system runs: `python3 enhanced_efficient_system.py`
- [ ] Predictions are generated: `sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = DATE('now');"`
- [ ] Features are calculated: Check prediction logs for feature vectors

### **✅ ML Training**
- [ ] Evening analyzer runs: `python3 ./enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py`
- [ ] Models exist: `ls -la models/`
- [ ] Training data populated: `sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM enhanced_outcomes;"`

---

## 🔍 **Monitoring Commands**

```bash
# Watch live prediction logs
tail -f cron_prediction.log

# Watch evening training logs  
tail -f cron_evening.log

# Check recent predictions
sqlite3 data/trading_predictions.db "
SELECT symbol, prediction_direction, confidence_score, prediction_timestamp 
FROM predictions 
ORDER BY prediction_timestamp DESC 
LIMIT 10;
"

# Check system resource usage
htop
# or
ps aux | grep python
```

---

## 🎯 **Success Indicators**

**System is fully recovered when you see:**

1. **Cron service active**: `systemctl is-active cron` → `active`
2. **Jobs scheduled**: `crontab -l` shows 3+ active jobs
3. **Predictions flowing**: New predictions every 30 minutes during market hours
4. **ML training working**: Models updated daily at 18:00 AEST
5. **No errors in logs**: `tail cron_prediction.log` shows successful runs

---

## 📞 **Getting Help**

If recovery fails:

1. **Check the deployment guide**: `./view_docs.sh deploy`
2. **Review system architecture**: `./view_docs.sh arch`
3. **Check the complete fix documentation**: `./view_docs.sh fixes`
4. **Review Monday morning checklist**: `./view_docs.sh monday`

---

## 🔄 **Automation Setup**

**Want this to happen automatically after reboot?**

Add the recovery script to system startup:

```bash
# Add to root's crontab for automatic recovery on reboot
crontab -e

# Add this line:
@reboot sleep 60 && cd /root/test && ./restart_system.sh >> restart_recovery.log 2>&1
```

This will automatically run the recovery script 60 seconds after every reboot.
