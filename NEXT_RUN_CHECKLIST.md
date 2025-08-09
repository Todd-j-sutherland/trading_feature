# 🚀 Next Trading Cycle Checklist

## ✅ Fixes Applied
- **Evening Analyzer Fixed**: Now records outcomes instead of duplicate features
- **Exit Price Tracking**: Should properly calculate exit prices and returns
- **Data Quality**: Fixed column name inconsistencies for dashboard

## 🌅 Morning Run (Local)
```bash
cd /Users/toddsutherland/Repos/trading_feature
python -m app.main morning
```

## 🌅 Morning Run (Remote)
```bash
ssh -i ~/.ssh/id_rsa root@170.64.199.151
cd /root/test
python3 enhanced_morning_analyzer_with_ml.py
```

**Expected Results:**
- New enhanced_features records for each symbol
- Sentiment analysis, technical indicators, news data
- ~7 new feature records (one per bank symbol)

## 🌙 Evening Run (Local)
```bash
cd /Users/toddsutherland/Repos/trading_feature
python -m app.main evening
```

## 🌙 Evening Run (Remote)  
```bash
ssh -i ~/.ssh/id_rsa root@170.64.199.151
cd /root/test
python3 enhanced_evening_analyzer_with_ml.py
```

**Expected Results:**
- New enhanced_outcomes records with trading actions
- Exit prices calculated from current market data
- Return percentages computed
- ML confidence scores assigned

## 🔍 Validation (Local)
```bash
cd /Users/toddsutherland/Repos/trading_feature
python validate_trading_cycle.py
```

## 🔍 Validation (Remote)
```bash
ssh -i ~/.ssh/id_rsa root@170.64.199.151
cd /root/test
python3 validate_trading_cycle.py
```

**Success Indicators:**
- Exit Price Completion: >80%
- Return Calculation: >95%
- Both morning features and evening outcomes generated
- Trading actions (BUY/HOLD/SELL) with proper confidence scores

## 📊 Dashboard View (Local)
```bash
cd /Users/toddsutherland/Repos/trading_feature
python -m app.main ml-dashboard
# OR
streamlit run ml_dashboard.py --server.port=8504
```

## 📊 Dashboard View (Remote)
```bash
ssh -i ~/.ssh/id_rsa root@170.64.199.151
cd /root/test
streamlit run ml_dashboard.py --server.port=8504
```

**Expected Improvements:**
- Position Win Rates page working correctly
- Clean data without NULL values
- Real trading performance metrics
- No more "winning_trades" column errors

## 🚨 If Issues Occur
1. Check `validate_trading_cycle.py` output
2. Verify database has new records: 
   ```bash
   sqlite3 data/trading_unified.db "SELECT COUNT(*) FROM enhanced_features; SELECT COUNT(*) FROM enhanced_outcomes;"
   ```
3. Check for exit price calculation: 
   ```bash
   sqlite3 data/trading_unified.db "SELECT COUNT(*) FROM enhanced_outcomes WHERE exit_price_1d IS NOT NULL;"
   ```

## 💡 Key Expectations
- **Features**: Should increase by ~7 per morning run
- **Outcomes**: Should increase by ~7 per evening run  
- **Exit Prices**: Should be calculated for all new outcomes
- **Returns**: Should show real trading performance data
- **Dashboard**: Should display complete analytics without errors

## 🔄 Current Status Summary
Based on your remote analysis, you currently have:
- **374 enhanced_features** (working well)
- **178 enhanced_outcomes** (working but 94.4% missing exit prices)
- **Only 10 complete trading records** out of 178
- **BUY signals showing +0.58% avg return** (promising!)
- **System collecting data but exit tracking broken**

## 🎯 What Should Change After Fix
- Exit price completion should jump from ~5% to >80%
- All recent trades should show real returns instead of 0%
- Dashboard analytics should be based on complete data
- Position win rates should reflect actual trading performance

---
*Last Updated: August 9, 2025*
*Status: Ready for next trading cycle* ✅
