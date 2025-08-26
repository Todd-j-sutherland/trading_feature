# Quick Troubleshooting Checklist - Trading System
**For Monday Morning Use - August 26, 2025**

## 🚨 **IMMEDIATE STATUS CHECK** (2 minutes)

### **Step 1: Basic System Health**
```bash
# Check if predictions were generated today
ssh root@170.64.199.151 'cd /root/test && sqlite3 /root/test/data/trading_predictions.db "SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = DATE(\"now\");"'

# Expected: 7 predictions (one per bank symbol)
# If 0: System didn't run
# If < 7: Partial failure
```

### **Step 2: Data Quality Check**
```bash
# Check for corruption (-9999 values)
ssh root@170.64.199.151 'cd /root/test && sqlite3 /root/test/data/trading_predictions.db "SELECT action_confidence FROM predictions WHERE DATE(prediction_timestamp) = DATE(\"now\") AND action_confidence < 0;"'

# Expected: No results (empty)
# If results: CORRUPTION DETECTED - need to rerun
```

### **Step 3: Prediction Diversity**
```bash
# Check action variety
ssh root@170.64.199.151 'cd /root/test && sqlite3 /root/test/data/trading_predictions.db "SELECT predicted_action, COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = DATE(\"now\") GROUP BY predicted_action;"'

# Expected: Mix of SELL and HOLD (BUY rare)
# If all HOLD: System using fallback analyzer
```

---

## ⚡ **QUICK FIXES** (5 minutes)

### **Problem: No Predictions Today**
```bash
# Solution: Run fixed morning routine
ssh root@170.64.199.151 'cd /root/test && /root/trading_venv/bin/python fix_remote_prediction_system.py'
```

### **Problem: Corrupted Data (-9999 values)**
```bash
# Solution: Kill processes and restart
ssh root@170.64.199.151 'pkill -f python && cd /root/test && /root/trading_venv/bin/python fix_remote_prediction_system.py'
```

### **Problem: All HOLD Actions**
```bash
# Solution: Force NewsTradingAnalyzer
ssh root@170.64.199.151 'cd /root/test && /root/trading_venv/bin/python -c "
import sys
sys.path.insert(0, \"/root/test\")
from app.core.data.processors.news_processor import NewsTradingAnalyzer
analyzer = NewsTradingAnalyzer()
print(\"NewsTradingAnalyzer loaded successfully\")
"'

# If this fails, check logs and use fallback
```

---

## 📊 **EXPECTED HEALTHY OUTPUT**

### **Normal Prediction Pattern:**
```
Symbol   Action Confidence Price    
CBA.AX   HOLD   0.747     $172.84  
WBC.AX   HOLD   0.740     $38.98   
ANZ.AX   SELL   0.747     $33.87   
NAB.AX   HOLD   0.733     $42.47   
MQG.AX   HOLD   0.746     $223.78  
SUN.AX   HOLD   0.698     $21.82   
QBE.AX   SELL   0.599     $21.58   
```

### **Healthy Indicators:**
- ✅ **7 predictions total**
- ✅ **Confidence: 0.5-1.0 range**
- ✅ **Actions: Mix of SELL/HOLD**
- ✅ **Prices: Real dollar values**
- ✅ **Model: NewsTradingAnalyzer_v1.0**

---

## 🔥 **EMERGENCY COMMANDS**

### **If Everything is Broken:**
```bash
# 1. Nuclear reset
ssh root@170.64.199.151 'pkill -f python; cd /root/test && rm -f *.pyc && /root/trading_venv/bin/python fix_remote_prediction_system.py'

# 2. Verify fix worked
ssh root@170.64.199.151 'cd /root/test && sqlite3 /root/test/data/trading_predictions.db "SELECT symbol, predicted_action, action_confidence FROM predictions ORDER BY prediction_timestamp DESC LIMIT 7;"'
```

### **Database Field Validation:**
```bash
# Check all critical fields are populated
ssh root@170.64.199.151 'cd /root/test && sqlite3 /root/test/data/trading_predictions.db "SELECT 
  CASE WHEN prediction_id IS NULL THEN \"MISSING\" ELSE \"OK\" END as prediction_id_status,
  CASE WHEN entry_price = 0.0 THEN \"MISSING\" ELSE \"OK\" END as price_status,
  symbol, predicted_action
FROM predictions 
WHERE DATE(prediction_timestamp) = DATE(\"now\");"'
```

---

## 📞 **ESCALATION POINTS**

### **Call for Help If:**
1. **Repeated crashes** after multiple restart attempts
2. **Network connectivity issues** to remote server
3. **Database corruption** that won't clear
4. **yfinance API failures** (all prices showing 0.0)

### **Working Backup Strategy:**
- Last known good database state: Check predictions from August 22, 2025
- Working script: `/root/test/fix_remote_prediction_system.py`
- Reference output patterns documented in main architecture document

---

## 💡 **PRO TIPS**

### **Time Savers:**
- Run status check first - saves time if system is already working
- Use prediction diversity as primary health indicator
- Price data validates yfinance connectivity

### **Warning Signs:**
- All predictions with same confidence (0.5) = Fallback system active
- Missing prediction_id = Database insertion problems  
- Negative confidence = Data corruption

### **Success Metrics:**
- 2 SELL signals normal (ANZ, QBE typically bearish)
- 5 HOLD signals normal (conservative market)
- 0 BUY signals normal (current market conditions)

---

**🎯 Total time for full health check and fix: < 10 minutes**
