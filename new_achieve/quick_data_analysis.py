#!/usr/bin/env python3
"""
Quick Data Analysis Script
Quickly analyze database contents to identify potential issues
"""

import subprocess
import json
import os
from datetime import datetime

def run_remote_analysis():
    """Run analysis on remote database"""
    print("🌐 Analyzing Remote Database")
    print("=" * 40)
    
    # Quick remote analysis script
    analysis_script = '''
import sqlite3
import json
import pandas as pd
from collections import Counter

conn = sqlite3.connect("data/trading_predictions.db")

print("📊 DATABASE OVERVIEW")
print("-" * 30)

# Get table info
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print(f"Tables: {', '.join(tables)}")

# Predictions analysis
if 'predictions' in tables:
    print("\\n🎯 PREDICTIONS TABLE ANALYSIS")
    print("-" * 30)
    
    # Basic stats
    cursor.execute("SELECT COUNT(*) FROM predictions")
    total_predictions = cursor.fetchone()[0]
    print(f"Total predictions: {total_predictions}")
    
    # Action distribution
    cursor.execute("SELECT predicted_action, COUNT(*) FROM predictions GROUP BY predicted_action")
    actions = cursor.fetchall()
    print("Action distribution:")
    for action, count in actions:
        pct = (count / total_predictions) * 100
        print(f"  {action}: {count} ({pct:.1f}%)")
    
    # Confidence stats
    cursor.execute("SELECT AVG(action_confidence), MIN(action_confidence), MAX(action_confidence) FROM predictions")
    conf_avg, conf_min, conf_max = cursor.fetchone()
    print(f"Confidence: avg={conf_avg:.3f}, min={conf_min:.3f}, max={conf_max:.3f}")
    
    # Recent predictions
    cursor.execute("SELECT symbol, predicted_action, ROUND(action_confidence, 3), prediction_timestamp FROM predictions ORDER BY prediction_timestamp DESC LIMIT 5")
    recent = cursor.fetchall()
    print("\\nRecent predictions:")
    for symbol, action, conf, timestamp in recent:
        print(f"  {symbol}: {action} (conf: {conf}) at {timestamp}")
    
    # Feature vector analysis
    print("\\n🔍 FEATURE VECTOR ANALYSIS")
    print("-" * 30)
    
    cursor.execute("SELECT feature_vector FROM predictions WHERE feature_vector IS NOT NULL LIMIT 10")
    feature_vectors = cursor.fetchall()
    
    if feature_vectors:
        # Parse feature vectors
        parsed_features = []
        for (fv_str,) in feature_vectors:
            try:
                features = json.loads(fv_str)
                if isinstance(features, list) and len(features) >= 16:
                    parsed_features.append({
                        'sentiment': features[0],
                        'rsi': features[4], 
                        'macd': features[5],
                        'price': features[15] if len(features) > 15 else 0
                    })
            except:
                continue
        
        if parsed_features:
            # Calculate statistics
            sentiments = [f['sentiment'] for f in parsed_features]
            rsis = [f['rsi'] for f in parsed_features]
            macds = [f['macd'] for f in parsed_features]
            prices = [f['price'] for f in parsed_features]
            
            print(f"Sample size: {len(parsed_features)} feature vectors")
            print(f"Sentiment range: {min(sentiments):.3f} to {max(sentiments):.3f}")
            print(f"RSI range: {min(rsis):.1f} to {max(rsis):.1f}")
            print(f"MACD range: {min(macds):.3f} to {max(macds):.3f}")
            print(f"Price range: ${min(prices):.2f} to ${max(prices):.2f}")
            
            # Check for static values
            rsi_50_count = sum(1 for r in rsis if r == 50.0)
            macd_0_count = sum(1 for m in macds if m == 0.0)
            price_0_count = sum(1 for p in prices if p == 0.0)
            
            print(f"\\n🚨 STATIC VALUE CHECK:")
            print(f"RSI = 50.0: {rsi_50_count}/{len(rsis)} ({100*rsi_50_count/len(rsis):.1f}%)")
            print(f"MACD = 0.0: {macd_0_count}/{len(macds)} ({100*macd_0_count/len(macds):.1f}%)")
            print(f"Price = 0.0: {price_0_count}/{len(prices)} ({100*price_0_count/len(prices):.1f}%)")
            
            # Show sample values
            print(f"\\n📋 SAMPLE VALUES:")
            for i in range(min(3, len(parsed_features))):
                f = parsed_features[i]
                print(f"  Sample {i+1}: sentiment={f['sentiment']:.3f}, RSI={f['rsi']:.1f}, MACD={f['macd']:.3f}, price=${f['price']:.2f}")
        else:
            print("❌ No valid feature vectors found")
    else:
        print("❌ No feature vectors found")

# Outcomes analysis
if 'outcomes' in tables:
    print("\\n📈 OUTCOMES TABLE ANALYSIS")
    print("-" * 30)
    
    cursor.execute("SELECT COUNT(*) FROM outcomes")
    total_outcomes = cursor.fetchone()[0]
    print(f"Total outcomes: {total_outcomes}")
    
    if total_outcomes > 0:
        cursor.execute("SELECT AVG(actual_return), MIN(actual_return), MAX(actual_return) FROM outcomes WHERE actual_return IS NOT NULL")
        result = cursor.fetchone()
        if result[0] is not None:
            avg_return, min_return, max_return = result
            print(f"Returns: avg={avg_return:.3f}%, min={min_return:.3f}%, max={max_return:.3f}%")

conn.close()
'''
    
    # Write analysis script to remote
    print("📝 Running comprehensive analysis on remote server...")
    
    cmd = f'''ssh root@170.64.199.151 "cd /root/test && python3 -c '{analysis_script}'"'''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ Remote analysis completed:")
            print(result.stdout)
        else:
            print(f"❌ Remote analysis failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("⏱️ Analysis timed out")
    except Exception as e:
        print(f"❌ Error running remote analysis: {e}")

def export_sample_data():
    """Export sample data for manual inspection"""
    print("\n📋 Exporting Sample Data for Manual Review")
    print("=" * 45)
    
    # Create exports directory
    os.makedirs("quick_exports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export recent predictions
    export_cmd = f'''ssh root@170.64.199.151 "cd /root/test && sqlite3 -header -csv data/trading_predictions.db \\"
    SELECT 
        symbol,
        predicted_action,
        ROUND(action_confidence, 3) as confidence,
        prediction_timestamp,
        feature_vector
    FROM predictions 
    ORDER BY prediction_timestamp DESC 
    LIMIT 20
    \\"" > quick_exports/recent_predictions_{timestamp}.csv'''
    
    try:
        subprocess.run(export_cmd, shell=True, check=True)
        print(f"✅ Recent predictions exported to: quick_exports/recent_predictions_{timestamp}.csv")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to export predictions: {e}")
    
    # Export feature vector analysis
    feature_analysis_cmd = f'''ssh root@170.64.199.151 "cd /root/test && python3 -c \\"
import sqlite3
import json
import csv

conn = sqlite3.connect('data/trading_predictions.db')
cursor = conn.cursor()

cursor.execute('SELECT symbol, prediction_timestamp, feature_vector FROM predictions WHERE feature_vector IS NOT NULL ORDER BY prediction_timestamp DESC LIMIT 20')
rows = cursor.fetchall()

with open('feature_analysis_temp.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['symbol', 'timestamp', 'sentiment', 'rsi', 'macd_line', 'current_price', 'full_vector'])
    
    for symbol, timestamp, fv_str in rows:
        try:
            features = json.loads(fv_str)
            if len(features) >= 16:
                sentiment = features[0]
                rsi = features[4]
                macd = features[5]
                price = features[15] if len(features) > 15 else 0
                writer.writerow([symbol, timestamp, sentiment, rsi, macd, price, fv_str[:100] + '...'])
        except:
            writer.writerow([symbol, timestamp, 'ERROR', 'ERROR', 'ERROR', 'ERROR', 'PARSE_ERROR'])

conn.close()
\\" && cat feature_analysis_temp.csv && rm feature_analysis_temp.csv" > quick_exports/feature_analysis_{timestamp}.csv'''
    
    try:
        subprocess.run(feature_analysis_cmd, shell=True, check=True)
        print(f"✅ Feature analysis exported to: quick_exports/feature_analysis_{timestamp}.csv")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to export feature analysis: {e}")

def create_manual_checklist():
    """Create a checklist for manual data validation"""
    
    checklist = """
# 📋 MANUAL DATA VALIDATION CHECKLIST

## 🎯 PREDICTIONS TABLE VALIDATION

### Action Distribution Check
- [ ] BUY signals: Should be 20-40% of total
- [ ] SELL signals: Should be 10-30% of total  
- [ ] HOLD signals: Should be 30-70% of total
- [ ] No unknown/invalid actions

### Confidence Distribution Check
- [ ] Average confidence: Should be 0.4-0.7
- [ ] Not all values exactly 0.5
- [ ] Reasonable spread (std > 0.05)
- [ ] No values outside 0.0-1.0 range

### Feature Vector Validation
- [ ] Sentiment scores: Range -1.0 to 1.0, not all 0.0
- [ ] RSI values: Range 0-100, NOT mostly 50.0
- [ ] MACD values: Realistic range, NOT mostly 0.0
- [ ] Current prices: $15-$150 for ASX stocks, NOT 0.0
- [ ] No completely identical feature vectors

### Symbol Validation
- [ ] Only valid ASX symbols (*.AX format)
- [ ] Focus on: ANZ.AX, CBA.AX, WBC.AX, NAB.AX
- [ ] No invalid/test symbols

### Timestamp Validation
- [ ] Recent predictions (within last 7 days)
- [ ] No future timestamps
- [ ] Logical sequence

## 📈 OUTCOMES TABLE VALIDATION (if exists)

### Return Values
- [ ] Realistic returns: -10% to +10% typical
- [ ] Not all 0.0% returns
- [ ] Entry/exit prices make sense

### Reference Integrity
- [ ] All outcome prediction_ids exist in predictions table
- [ ] No orphaned outcomes

## 🚨 RED FLAGS TO WATCH FOR

### Data Quality Issues
- [ ] More than 50% of RSI values = 50.0 (static default)
- [ ] More than 50% of MACD values = 0.0 (static default)
- [ ] More than 80% of one action type
- [ ] All confidence values clustered around 0.5
- [ ] Many 0.0 prices
- [ ] Identical feature vectors

### System Issues
- [ ] No new predictions in 24+ hours
- [ ] Error patterns in feature vectors
- [ ] Missing data for major symbols

## ✅ VALIDATION STEPS

1. **Export Data**: Run data_export_validator.py
2. **Review CSVs**: Check exported CSV files manually
3. **Spot Check**: Verify 10-20 random predictions
4. **Cross Reference**: Compare with expected value ranges
5. **Flag Issues**: Document any concerning patterns

## 📊 EXPECTED VALUE RANGES

### Technical Indicators
- RSI: 20-80 (30-70 typical), NOT consistently 50
- MACD: -2.0 to +2.0 typical, NOT consistently 0
- Prices: $15-$150 for major banks
- Sentiment: -0.5 to +0.5 typical

### Prediction Patterns
- Confidence: 0.3-0.8 typical
- Actions: Mixed distribution, not >90% one type
- Timestamps: Recent and sequential

---
Generated: {datetime.now().isoformat()}
"""
    
    checklist_path = f"quick_exports/manual_validation_checklist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(checklist_path, 'w') as f:
        f.write(checklist)
    
    print(f"📋 Manual validation checklist created: {checklist_path}")
    return checklist_path

def main():
    """Main execution"""
    print("🔍 Quick Data Analysis and Export Tool")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Run remote analysis
    run_remote_analysis()
    
    # Export sample data
    export_sample_data()
    
    # Create manual checklist
    checklist_path = create_manual_checklist()
    
    print("\n🎉 Quick Analysis Complete!")
    print("\n📋 Next Steps:")
    print("1. Review the analysis output above")
    print("2. Check exported CSV files in quick_exports/")
    print(f"3. Follow manual checklist: {checklist_path}")
    print("4. Flag any concerning patterns")
    print("\n💡 Look especially for:")
    print("   - RSI values stuck at 50.0")
    print("   - MACD values stuck at 0.0") 
    print("   - Unrealistic price ranges")
    print("   - Static confidence values")

if __name__ == "__main__":
    main()
