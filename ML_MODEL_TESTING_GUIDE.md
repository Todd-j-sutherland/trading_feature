# ML Model Testing Guide - 1 Week Performance Monitoring

## Overview
This guide outlines how to test and monitor your enhanced ML trading model performance over the next week (August 11-18, 2025). The system has been recently improved with balanced action logic and proper error handling.

## 🚀 QUICK START - Automated Evening Report
**RECOMMENDED**: Use the automated evening script for comprehensive daily monitoring:
```bash
# Copy scripts to remote server (one-time setup)
scp evening_ml_check_with_history.py view_ml_trends.py root@170.64.199.151:/root/test/

# Run daily evening report with historical tracking
ssh root@170.64.199.151 "cd /root/test && python3 evening_ml_check_with_history.py"

# View performance trends
ssh root@170.64.199.151 "cd /root/test && python3 view_ml_trends.py"
```
This saves results to JSON for historical tracking and trend analysis!

### 📊 **Historical Performance Tracking**
```bash
# View trends for different periods
ssh root@170.64.199.151 "cd /root/test && python3 view_ml_trends.py --days 14"

# Focus on specific action performance
ssh root@170.64.199.151 "cd /root/test && python3 view_ml_trends.py --action SELL"

# Get summary statistics
ssh root@170.64.199.151 "cd /root/test && python3 view_ml_trends.py --summary"

# Export data to CSV for analysis
ssh root@170.64.199.151 "cd /root/test && python3 view_ml_trends.py --export"
```

### 📈 **Trend Analysis Features**
- **Health Score Trends**: Track system improvement over time
- **Performance by Action**: Monitor BUY/SELL/HOLD performance separately  
- **Data Quality Tracking**: Monitor training data bias trends
- **Export to CSV**: Analyze data in Excel/other tools
- **Automatic History**: Keeps 30 days of performance data

---

## Quick Status Check Commands

### 1. Check Current Model Status
```bash
# SSH to remote server
ssh root@170.64.199.151

# Check if models exist and are current
cd /root/test/data/ml_models/models
ls -la current_*
stat current_direction_model.pkl current_magnitude_model.pkl

# Check model training dates
cat current_enhanced_metadata.json | grep -E '"training_date"|"version"'
```

### 2. Daily Model Performance Check
```bash
# Check recent predictions and outcomes
cd /root/test
sqlite3 data/trading_unified.db "
SELECT 
    DATE(prediction_timestamp) as date,
    COUNT(*) as total_predictions,
    AVG(CASE WHEN price_direction_1d = 1 THEN 1.0 ELSE 0.0 END) as pct_bullish,
    AVG(return_pct) as avg_return,
    optimal_action,
    COUNT(*) as action_count
FROM enhanced_outcomes 
WHERE prediction_timestamp >= date('now', '-7 days')
GROUP BY DATE(prediction_timestamp), optimal_action
ORDER BY date DESC, optimal_action;
"
```

### 3. Dashboard Quick Check
```bash
# Check if dashboard is showing proper ML confidence values (not 0s)
ssh root@170.64.199.151 "cd /root/test && python3 -c \"
import sqlite3
conn = sqlite3.connect('data/trading_unified.db')
cursor = conn.cursor()
cursor.execute('SELECT symbol, optimal_action, confidence_score FROM enhanced_outcomes ORDER BY created_at DESC LIMIT 5')
print('Recent ML Predictions:')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]} (confidence: {row[2]:.3f})')
conn.close()
\""
```

## Daily Monitoring Routine (5 minutes/day)

### Morning Check (before market open - 9:30 AM)
1. **Verify Model Status**
   ```bash
   ssh root@170.64.199.151 "cd /root/test && python3 check_status.py"
   ```

2. **Check Training Data Quality**
   ```bash
   ssh root@170.64.199.151 "cd /root/test && sqlite3 data/trading_unified.db '
   SELECT 
       COUNT(*) as total_samples,
       AVG(CASE WHEN price_direction_1d = 1 THEN 1.0 ELSE 0.0 END) as bullish_ratio,
       MIN(prediction_timestamp) as oldest_data,
       MAX(prediction_timestamp) as newest_data
   FROM enhanced_outcomes 
   WHERE created_at >= date(\"now\", \"-1 days\");'"
   ```

### Evening Check (after market close - 5:00 PM)
1. **Check Today's Model Performance**
   ```bash
   ssh root@170.64.199.151 "cd /root/test && python3 -c '
import sqlite3
from datetime import datetime, date

conn = sqlite3.connect(\"data/trading_unified.db\")
cursor = conn.cursor()

# Today performance
cursor.execute(\"\"\"
SELECT 
    optimal_action,
    COUNT(*) as count,
    AVG(return_pct) as avg_return,
    AVG(confidence_score) as avg_confidence
FROM enhanced_outcomes 
WHERE DATE(prediction_timestamp) = DATE(\"now\")
GROUP BY optimal_action
ORDER BY count DESC
\"\"\")

print(\"TODAY PERFORMANCE:\")
for row in cursor.fetchall():
    print(f\"{row[0]}: {row[1]} trades, {row[2]:.3f}% avg return, {row[3]:.3f} confidence\")

conn.close()
'"
   ```

   **OR USE THE AUTOMATED SCRIPT (RECOMMENDED):**
   ```bash
   ssh root@170.64.199.151 "cd /root/test && python3 evening_ml_check.py"
   ```

2. **Verify Evening Training Ran**
   ```bash
   ssh root@170.64.199.151 "cd /root/test && tail -50 logs/app.log | grep -E 'evening|training|Enhanced.*trained'"
   ```

## Weekly Deep Analysis Commands

### Model Performance Metrics
```bash
ssh root@170.64.199.151 "cd /root/test && python3 -c '
import sqlite3

conn = sqlite3.connect(\"data/trading_unified.db\")

# Last 7 days performance by action
query = \"\"\"
SELECT 
    optimal_action,
    COUNT(*) as trades,
    AVG(return_pct) as avg_return,
    SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
    AVG(confidence_score) as avg_confidence
FROM enhanced_outcomes 
WHERE prediction_timestamp >= datetime(\"now\", \"-7 days\")
    AND return_pct IS NOT NULL
GROUP BY optimal_action
ORDER BY trades DESC
\"\"\"

print(\"7-DAY PERFORMANCE BY ACTION:\")
print(\"Action\\t\\tTrades\\tAvg Return\\tWin Rate\\tConfidence\")
print(\"-\" * 60)

for row in conn.execute(query):
    action, trades, avg_ret, win_rate, confidence = row
    print(f\"{action:<12}\\t{trades}\\t{avg_ret:.3f}%\\t\\t{win_rate:.1f}%\\t\\t{confidence:.3f}\")

conn.close()
'"
```

### Data Quality Check
```bash
ssh root@170.64.199.151 "cd /root/test && python3 -c '
import sqlite3

conn = sqlite3.connect(\"data/trading_unified.db\")

# Check for data bias issues
print(\"TRAINING DATA BIAS CHECK:\")
cursor = conn.execute(\"\"\"
SELECT 
    AVG(CASE WHEN price_direction_1h = 1 THEN 1.0 ELSE 0.0 END) * 100 as bullish_1h,
    AVG(CASE WHEN price_direction_4h = 1 THEN 1.0 ELSE 0.0 END) * 100 as bullish_4h, 
    AVG(CASE WHEN price_direction_1d = 1 THEN 1.0 ELSE 0.0 END) * 100 as bullish_1d,
    COUNT(*) as total_samples
FROM enhanced_outcomes 
WHERE created_at >= datetime(\"now\", \"-7 days\")
\"\"\")

row = cursor.fetchone()
print(f\"Bullish bias: 1h={row[0]:.1f}%, 4h={row[1]:.1f}%, 1d={row[2]:.1f}% (samples: {row[3]})\")
print(\"Healthy range: 40-60% bullish\")

if row[0] < 20 or row[0] > 80:
    print(\"⚠️  WARNING: Extreme bias detected in 1h predictions\")
if row[1] < 20 or row[1] > 80:  
    print(\"⚠️  WARNING: Extreme bias detected in 4h predictions\")
if row[2] < 20 or row[2] > 80:
    print(\"⚠️  WARNING: Extreme bias detected in 1d predictions\")

conn.close()
'"
```

## Key Performance Indicators (KPIs) to Track

### 1. Model Accuracy Trends
- **Direction Accuracy**: Should be >55% for profitable trading
- **Magnitude MAE**: Should be <2% for reliable predictions
- **Confidence Calibration**: High confidence predictions should be more accurate

### 2. Action Performance
- **BUY/SELL Win Rates**: Should be >60% for profitable actions
- **HOLD Accuracy**: Should avoid losses during volatile periods
- **Strong Action Performance**: STRONG_BUY/STRONG_SELL should outperform regular actions

### 3. Data Quality Metrics
- **Training Sample Growth**: Should add 20-50 samples per day
- **Bias Detection**: Bullish/bearish ratio should be 40-60%
- **Feature Coverage**: All required features should have <5% missing values

## Automated Monitoring Script

Create this script for daily automated checks:

```bash
# Save as /root/test/daily_ml_check.sh
#!/bin/bash
echo "=== Daily ML Model Check - $(date) ==="

# Check model files exist
echo "1. Model Status:"
if [ -f "data/ml_models/models/current_direction_model.pkl" ]; then
    echo "✅ Direction model: OK"
else
    echo "❌ Direction model: MISSING"
fi

if [ -f "data/ml_models/models/current_magnitude_model.pkl" ]; then
    echo "✅ Magnitude model: OK"  
else
    echo "❌ Magnitude model: MISSING"
fi

# Check recent performance
echo -e "\n2. Today's Performance:"
sqlite3 data/trading_unified.db "
SELECT 
    optimal_action,
    COUNT(*) as trades,
    ROUND(AVG(return_pct), 3) as avg_return,
    ROUND(AVG(confidence_score), 3) as confidence
FROM enhanced_outcomes 
WHERE DATE(prediction_timestamp) = DATE('now')
GROUP BY optimal_action
ORDER BY trades DESC
"

# Check training data growth
echo -e "\n3. Training Data Growth:"
sqlite3 data/trading_unified.db "
SELECT 
    DATE(created_at) as date,
    COUNT(*) as new_samples
FROM enhanced_outcomes 
WHERE created_at >= date('now', '-3 days')
GROUP BY DATE(created_at)
ORDER BY date DESC
"

echo -e "\n=== Check Complete ==="
```

## Warning Signs to Watch For

### 🚨 Critical Issues
- **All confidence scores = 0**: Models not loading properly
- **Win rate <30%**: Models performing worse than random
- **No new training data**: Data collection pipeline broken
- **Extreme bias (>90% bullish/bearish)**: Data quality issues

### ⚠️ Performance Issues  
- **Declining win rates**: Model degradation over time
- **High magnitude errors**: Price prediction inaccuracy
- **Low confidence on strong actions**: Model uncertainty

### 📊 Data Quality Issues
- **Missing features**: Feature extraction problems
- **Stale model dates**: Training not running automatically
- **Inconsistent sample counts**: Data collection gaps

## Troubleshooting Commands

### Reset Models if Performance is Poor
```bash
ssh root@170.64.199.151 "cd /root/test && python3 -c '
from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline

pipeline = EnhancedMLTrainingPipeline()
X, y = pipeline.prepare_enhanced_training_dataset()
if X is not None:
    results = pipeline.train_enhanced_models(X, y)
    print(f\"Retrained models with {len(X)} samples\")
else:
    print(\"Insufficient training data for retraining\")
'"
```

### Force Manual Training Run
```bash
ssh root@170.64.199.151 "cd /root/test && python3 app/main.py evening"
```

### Check Dashboard Issues
```bash
ssh root@170.64.199.151 "cd /root/test && python3 dashboard.py --test-mode"
```

## Expected Results After 1 Week

### Good Performance Indicators:
- **Model Stability**: Confidence scores consistently >0.4
- **Balanced Actions**: Not >70% of any single action type
- **Profitable Trades**: Overall positive returns on BUY/SELL actions
- **Growing Dataset**: 150-350 new training samples collected

### Success Metrics:
- **Direction Accuracy**: >55% on 4h and 1d predictions
- **SELL Action Improvement**: Win rate >40% (vs previous 11%)
- **Strong Action Premium**: STRONG_BUY/STRONG_SELL outperform regular actions
- **Error Reduction**: No "fallback prediction" errors in logs

## Next Steps Based on Results

### If Performance is Good (Win Rate >55%):
1. Gradually increase position sizes
2. Add more stocks to monitoring
3. Implement paper trading validation

### If Performance is Poor (Win Rate <45%):
1. Investigate training data bias
2. Review feature engineering
3. Consider model architecture changes
4. Increase training data collection period

### If Data Quality Issues:
1. Check feature extraction pipeline
2. Validate market data sources  
3. Review sentiment analysis accuracy
4. Ensure proper temporal alignment

---

**Remember**: ML models need time to learn from new market conditions. One week provides initial validation, but 2-4 weeks of data gives more reliable performance assessment.
