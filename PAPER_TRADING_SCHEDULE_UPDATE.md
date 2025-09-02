# Paper Trading Schedule Update - ASX Correct Trading Hours

**Updated**: September 3, 2025  
**Purpose**: Correct paper trading automation to match actual ASX trading hours

---

## 🕐 **Schedule Changes Summary**

### **ASX Trading Hours Correction:**
- **Correct ASX Hours**: 10:30 AM - 3:30 PM AEST (Sydney time)
- **UTC Conversion**: 00:30 - 05:30 UTC (during AEST/UTC+10)

### **Old Schedule (INCORRECT):**
```bash
# Start Paper Trading: 09:45 AEST (23:45 UTC previous day)
# Health Checks: Every hour 00:00-06:00 UTC  
# Daily Summary: 16:30 AEST (06:30 UTC)
# Main Predictions: Every 30 min 00:00-06:00 UTC
```

### **New Schedule (CORRECT):**
```bash
# Start Paper Trading: 10:15 AEST (00:15 UTC)
# Health Checks: Every hour 00:30-05:30 UTC  
# Daily Summary: 15:45 AEST (05:45 UTC)
# Main Predictions: Every 30 min 00:30-05:30 UTC
```

---

## 📋 **Updated Cron Job Schedule**

### **Paper Trading Automation:**
```bash
# Start service 15 minutes before market open
15 0 * * 1-5 cd /root/test/paper-trading-app && source ./paper_trading_venv/bin/activate && python run_paper_trading_ig.py service >> /root/test/logs/paper_trading_ig_service.log 2>&1 &

# Health checks every hour during trading hours (10:30-15:30 AEST)
30 0-5 * * 1-5 cd /root/test/paper-trading-app && source ./paper_trading_venv/bin/activate && python -c "
from enhanced_paper_trading_service_with_ig import EnhancedPaperTradingServiceWithIG
service = EnhancedPaperTradingServiceWithIG()
summary = service.get_enhanced_portfolio_summary()
print(f'Portfolio: {summary.get(\"active_positions\", 0)} positions, P&L: ${summary.get(\"total_profit\", 0):.2f}')
" >> /root/test/logs/paper_trading_health.log 2>&1

# Daily summary 15 minutes after market close
45 5 * * 1-5 cd /root/test/paper-trading-app && source ./paper_trading_venv/bin/activate && python -c "
from enhanced_paper_trading_service_with_ig import EnhancedPaperTradingServiceWithIG
import json
service = EnhancedPaperTradingServiceWithIG()
summary = service.get_enhanced_portfolio_summary()
print(json.dumps(summary, indent=2, default=str))
" >> /root/test/logs/paper_trading_daily_summary.log 2>&1

# Stop service after market close
50 5 * * 1-5 pkill -f "run_paper_trading_ig.py service" && echo "$(date): Paper trading service stopped for end of day" >> /root/test/logs/paper_trading_lifecycle.log 2>&1
```

### **Main Application Predictions:**
```bash
# Predictions every 30 minutes during correct trading hours
*/30 0-5 * * 1-5 cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python enhanced_efficient_system.py >> /root/test/logs/predictions_ig_markets.log 2>&1
```

---

## ⏰ **Complete Daily Schedule (AEST/Sydney Time)**

| Time (AEST) | Time (UTC) | Operation | Description |
|-------------|------------|-----------|-------------|
| **09:30** | 23:30 | Morning Routine | Daily market preparation |
| **10:15** | 00:15 | Start Paper Trading | 15 min before market open |
| **10:30** | 00:30 | **MARKET OPENS** | ASX trading begins |
| **10:30-15:30** | 00:30-05:30 | Active Trading | Predictions every 30 min, health checks hourly |
| **15:30** | 05:30 | **MARKET CLOSES** | ASX trading ends |
| **15:45** | 05:45 | Paper Trading Summary | Daily portfolio report |
| **15:50** | 05:50 | Stop Paper Trading | Service shutdown |
| **18:00** | 08:00 | Evening Routine | ML training and analysis |

---

## 📊 **Benefits of Correct Timing**

### **Paper Trading Accuracy:**
- ✅ **Precise Market Hours**: Matches actual ASX trading 10:30-15:30 AEST
- ✅ **Realistic Operations**: No trading activity outside market hours
- ✅ **Accurate Performance**: True-to-market trading simulation
- ✅ **Resource Efficiency**: No unnecessary processing outside trading hours

### **Improved Automation:**
- ✅ **Synchronized Predictions**: Main app and paper trading aligned
- ✅ **Optimized Health Checks**: Only during active trading hours
- ✅ **Better Logging**: Clear separation of trading vs non-trading periods
- ✅ **Reduced System Load**: Focused resource usage

---

## 🔧 **Files Updated**

### **Cron Job Configuration:**
- ✅ `updated_cron_jobs.txt` - Complete automation with corrected times
- ✅ `simple_cron_jobs.txt` - Simplified version with corrected times

### **Documentation:**
- ✅ `documentation/README.md` - Updated automation guide with correct schedule
- ✅ `PAPER_TRADING_SCHEDULE_UPDATE.md` - This summary document

### **Schedule Components Updated:**
- ✅ Paper trading service start time
- ✅ Paper trading health check schedule  
- ✅ Paper trading daily summary time
- ✅ Main application prediction schedule
- ✅ Documentation automation schedule table
- ✅ All UTC time conversions

---

## 🚀 **Deployment Instructions**

### **Install Updated Schedule:**
```bash
# Option 1: Use automated deployment
cd /root/test
chmod +x deploy_updated_cron.sh
./deploy_updated_cron.sh

# Option 2: Manual installation
crontab simple_cron_jobs.txt

# Verify installation
crontab -l | grep -E "(paper|00:15|00:30|05:45)"
```

### **Verify Correct Operation:**
```bash
# Check paper trading starts correctly at 10:15 AEST
# Check predictions run every 30 min from 10:30-15:30 AEST
# Check daily summary at 15:45 AEST
# Check service stops at 15:50 AEST

# Monitor logs
tail -f /root/test/logs/paper_trading_ig_service.log
tail -f /root/test/logs/paper_trading_health.log
tail -f /root/test/logs/predictions_ig_markets.log
```

---

## ✅ **Validation Checklist**

- [ ] Paper trading starts at 10:15 AEST (00:15 UTC)
- [ ] Health checks run hourly 10:30-15:30 AEST (00:30-05:30 UTC)
- [ ] Predictions run every 30 min during market hours
- [ ] Daily summary generated at 15:45 AEST (05:45 UTC)
- [ ] Service stops at 15:50 AEST (05:50 UTC)
- [ ] No trading activity outside 10:30-15:30 AEST
- [ ] IG Markets integration works during correct hours
- [ ] Log files show correct timestamps

**🎯 The paper trading system now operates during the correct ASX trading hours: 10:30 AM - 3:30 PM AEST!**
