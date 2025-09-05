# Remote Droplet Restart Recovery Procedure
**Date**: September 3, 2025  
**Purpose**: Restore full automation after droplet restart

---

## 🚀 **IMMEDIATE RECOVERY STEPS**

### **Step 1: Connect to Remote Droplet**
```bash
# SSH into your droplet (replace with your details)
ssh root@your-droplet-ip
# OR
ssh your-username@your-droplet-ip
```

### **Step 2: Navigate to Project Directory**
```bash
cd /root/test
pwd  # Should show /root/test
ls -la  # Verify files are present
```

### **Step 3: Activate Virtual Environment**
```bash
# Activate main trading environment
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test
echo "Virtual env activated: $VIRTUAL_ENV"
```

### **Step 4: Install/Restore Cron Jobs**
```bash
# Option A: Use automated deployment script
chmod +x deploy_updated_cron.sh
./deploy_updated_cron.sh

# Option B: Manual installation (if script doesn't exist)
crontab simple_cron_jobs.txt

# Verify cron jobs are installed
crontab -l | head -20
```

### **Step 5: Start Cron Service**
```bash
# Ensure cron service is running
sudo service cron start
sudo service cron status

# Enable cron to start on boot
sudo systemctl enable cron
```

---

## 🔍 **VERIFICATION STEPS**

### **Step 6: Test Main Application**
```bash
# Test morning routine manually
cd /root/test
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test
python -m app.main morning

# Expected output: Should see morning routine executing with IG Markets integration
```

### **Step 7: Test Paper Trading App**
```bash
# Navigate to paper trading directory
cd /root/test/paper-trading-app

# Activate paper trading environment
source ./paper_trading_venv/bin/activate

# Test paper trading initialization
python run_paper_trading_ig.py init

# Start paper trading service
python run_paper_trading_ig.py service &

# Test paper trading status
python run_paper_trading_ig.py test

# Expected output: Should show IG Markets integration and service status
```

### **Step 8: Verify Cron Jobs Are Working**
```bash
# Check if cron jobs are scheduled correctly
crontab -l | grep -E "(morning|evening|paper_trading)"

# Check cron service logs
grep CRON /var/log/syslog | tail -10

# Check if processes will start at correct times
# Morning routine: 23:30 UTC (09:30 AEST)
# Paper trading: 00:15 UTC (10:15 AEST)
# Evening routine: 08:00 UTC (18:00 AEST)
```

---

## 📊 **MONITORING COMMANDS**

### **Real-time Status Monitoring**
```bash
# Overall system status
python -m app.main status

# Check IG Markets integration
python -m app.main ig-markets-test

# View running processes
ps aux | grep -E "(python|trading)"

# Monitor log files
tail -f /root/test/logs/morning_ig_markets.log &
tail -f /root/test/logs/paper_trading_ig_service.log &
tail -f /root/test/logs/predictions_ig_markets.log &

# Stop monitoring (Ctrl+C)
```

### **Paper Trading Specific Checks**
```bash
cd /root/test/paper-trading-app
source ./paper_trading_venv/bin/activate

# Check paper trading health
python -c "
from enhanced_paper_trading_service_with_ig import EnhancedPaperTradingServiceWithIG
try:
    service = EnhancedPaperTradingServiceWithIG()
    summary = service.get_enhanced_portfolio_summary()
    print(f'Portfolio: {summary.get(\"active_positions\", 0)} positions')
    print(f'Total P&L: ${summary.get(\"total_profit\", 0):.2f}')
    print(f'IG Markets enabled: {service.ig_markets_enabled}')
    if hasattr(service, 'enhanced_price_source'):
        print(f'IG Markets healthy: {service.enhanced_price_source.is_ig_markets_healthy()}')
except Exception as e:
    print(f'Error: {e}')
"
```

---

## 🕐 **TIMING VERIFICATION**

### **Current Time and Next Scheduled Runs**
```bash
# Check current time in different timezones
date
date -u  # UTC time
TZ='Australia/Sydney' date  # Sydney time

# Calculate next scheduled runs:
echo "Next morning routine: Tomorrow 09:30 AEST (23:30 UTC today)"
echo "Next paper trading start: Tomorrow 10:15 AEST (00:15 UTC tomorrow)"
echo "Next evening routine: Today 18:00 AEST (08:00 UTC today)"

# If it's currently during market hours (10:30-15:30 AEST), verify:
echo "If market is open, predictions should run every 30 minutes"
echo "Paper trading should be active now"
```

---

## 🚨 **TROUBLESHOOTING**

### **If Morning Routine Fails:**
```bash
# Check for errors
tail -50 /root/test/logs/morning_ig_markets.log

# Test dependencies
python -c "
try:
    from app.main import main
    print('✅ Main app imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
"

# Check IG Markets connectivity
python -c "
try:
    from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector
    collector = EnhancedMarketDataCollector()
    health = collector.is_ig_markets_healthy()
    print(f'IG Markets health: {\"OK\" if health else \"FAIL\"}')
except Exception as e:
    print(f'IG Markets test error: {e}')
"
```

### **If Paper Trading Fails:**
```bash
# Check paper trading logs
tail -50 /root/test/logs/paper_trading_ig_service.log

# Test paper trading dependencies
cd /root/test/paper-trading-app
python -c "
try:
    from enhanced_paper_trading_service_with_ig import EnhancedPaperTradingServiceWithIG
    print('✅ Paper trading imports successfully')
except Exception as e:
    print(f'❌ Paper trading import error: {e}')
"

# Check if paper trading virtual environment is working
source ./paper_trading_venv/bin/activate
pip list | grep -E "(yfinance|pandas|requests)"
```

### **If Cron Jobs Don't Run:**
```bash
# Restart cron service
sudo service cron restart
sudo service cron status

# Check cron permissions
ls -la /var/spool/cron/crontabs/
sudo cat /var/spool/cron/crontabs/root

# Test cron job syntax
crontab -l | head -10

# Manual test of a cron command
cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -m app.main status
```

---

## ✅ **SUCCESS INDICATORS**

### **System is Working Correctly When:**
- ✅ `crontab -l` shows all scheduled jobs
- ✅ `python -m app.main status` shows IG Markets integration healthy
- ✅ Paper trading service responds to health checks
- ✅ Log files show recent activity (if during scheduled times)
- ✅ `ps aux | grep trading` shows active processes (during market hours)
- ✅ IG Markets connectivity test passes
- ✅ No error messages in recent log entries

### **Expected Log File Locations:**
```bash
ls -la /root/test/logs/
# Should show:
# - morning_ig_markets.log
# - evening_ig_markets.log  
# - predictions_ig_markets.log
# - paper_trading_ig_service.log
# - paper_trading_health.log
# - paper_trading_daily_summary.log
# - ig_markets_test.log
# - daily_status.log
```

---

## 🎯 **IMMEDIATE ACTION CHECKLIST**

Run these commands in order on your remote droplet:

```bash
# 1. Navigate and activate
cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test

# 2. Install cron jobs
crontab simple_cron_jobs.txt

# 3. Start cron service
sudo service cron start && sudo systemctl enable cron

# 4. Test main app
python -m app.main status

# 5. Test paper trading
cd /root/test/paper-trading-app && source ./paper_trading_venv/bin/activate && python run_paper_trading_ig.py test

# 6. Verify scheduling
crontab -l | grep -E "(morning|evening|paper)"

# 7. Check logs
ls -la /root/test/logs/ && tail -5 /root/test/logs/*.log
```

**🚀 After running these commands, your system should be fully operational with automated morning routines, evening routines, and paper trading!**
