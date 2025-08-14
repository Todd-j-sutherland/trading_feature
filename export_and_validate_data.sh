#!/bin/bash

# 📊 Data Export and Validation Script
# This script exports all database tables and creates validation documentation

set -e

# Configuration
REMOTE_HOST="root@170.64.199.151"
REMOTE_DIR="/root/test"
LOCAL_EXPORT_DIR="./data_exports"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log "📊 Starting Data Export and Validation"
echo

# Create local export directory
mkdir -p "$LOCAL_EXPORT_DIR"

# Step 1: Export all database tables
log "📤 Step 1: Exporting Database Tables"
echo

# Export from trading_predictions.db
log "Exporting predictions table..."
ssh "$REMOTE_HOST" "cd $REMOTE_DIR && source ../trading_venv/bin/activate  && sqlite3 -header -csv data/trading_predictions.db 'SELECT * FROM predictions ORDER BY prediction_timestamp DESC;'" > "$LOCAL_EXPORT_DIR/predictions.csv"

log "Exporting outcomes table..."
ssh "$REMOTE_HOST" "cd $REMOTE_DIR && source ../trading_venv/bin/activate  && sqlite3 -header -csv data/trading_predictions.db 'SELECT * FROM outcomes ORDER BY entry_timestamp DESC;'" > "$LOCAL_EXPORT_DIR/outcomes.csv" 2>/dev/null || echo "No outcomes table found"

# Export from trading_unified.db
log "Exporting enhanced_features table..."
ssh "$REMOTE_HOST" "cd $REMOTE_DIR && source ../trading_venv/bin/activate  && sqlite3 -header -csv data/trading_unified.db 'SELECT * FROM enhanced_features ORDER BY timestamp DESC LIMIT 100;'" > "$LOCAL_EXPORT_DIR/enhanced_features.csv" 2>/dev/null || echo "No enhanced_features table found"

log "Exporting enhanced_outcomes table..."
ssh "$REMOTE_HOST" "cd $REMOTE_DIR && source ../trading_venv/bin/activate  && sqlite3 -header -csv data/trading_unified.db 'SELECT * FROM enhanced_outcomes ORDER BY prediction_timestamp DESC LIMIT 100;'" > "$LOCAL_EXPORT_DIR/enhanced_outcomes.csv" 2>/dev/null || echo "No enhanced_outcomes table found"

success "Database tables exported to $LOCAL_EXPORT_DIR/"
echo

# Step 2: Create data expectations document
log "📋 Step 2: Creating Data Expectations Documentation"
echo

cat > "$LOCAL_EXPORT_DIR/DATA_EXPECTATIONS.md" << 'EOF'
# 📊 Trading System Data Expectations

## Overview
This document defines the expected ranges and characteristics for all data in our trading system.

## 1. Predictions Table

### Expected Columns:
- `prediction_id`: UUID format (e.g., "a1b2c3d4-e5f6-...")
- `symbol`: Stock symbol format (e.g., "ANZ.AX", "CBA.AX")
- `predicted_action`: ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
- `action_confidence`: Float [0.0 - 1.0]
- `predicted_direction`: Integer [-1, 0, 1] (-1=DOWN, 0=NEUTRAL, 1=UP)
- `predicted_magnitude`: Float [0.0 - 10.0] (percentage expected change)
- `feature_vector`: JSON array with 20 features
- `prediction_timestamp`: ISO datetime format

### Expected Value Ranges:

#### Feature Vector (JSON Array Index):
0. **sentiment_score**: [-1.0 to 1.0] - Overall sentiment
1. **confidence**: [0.0 to 1.0] - Analysis confidence
2. **news_count**: [0 to 100] - Number of news articles
3. **reddit_sentiment**: [-1.0 to 1.0] - Reddit sentiment
4. **rsi**: [0.0 to 100.0] - Relative Strength Index
5. **macd_line**: [-5.0 to 5.0] - MACD line value
6. **macd_signal**: [-5.0 to 5.0] - MACD signal line
7. **macd_histogram**: [-3.0 to 3.0] - MACD histogram
8. **price_vs_sma20**: [-20.0 to 20.0] - Price vs 20-day SMA (%)
9. **price_vs_sma50**: [-30.0 to 30.0] - Price vs 50-day SMA (%)
10. **price_vs_sma200**: [-50.0 to 50.0] - Price vs 200-day SMA (%)
11. **bollinger_width**: [0.01 to 0.10] - Bollinger band width
12. **volume_ratio**: [0.1 to 10.0] - Volume vs average
13. **atr_14**: [0.01 to 5.0] - Average True Range
14. **volatility_20d**: [0.005 to 0.50] - 20-day volatility
15. **current_price**: [1.0 to 500.0] - Current stock price (AUD)
16. **asx200_change**: [-10.0 to 10.0] - ASX200 daily change (%)
17. **vix_level**: [5.0 to 80.0] - VIX level
18. **asx_market_hours**: [0, 1] - Boolean (0=closed, 1=open)
19. **market_day_effects**: Various boolean flags

### 🚨 Red Flags (Values that indicate problems):
- RSI exactly 50.0 (neutral default - should vary)
- MACD exactly 0.0 (neutral default - should vary)
- Sentiment exactly 0.0 (neutral default - should vary)
- Multiple symbols with identical feature vectors
- Current price exactly 0.0 or 25.50 (test values)
- All timestamps clustered within seconds (bulk inserts)

## 2. Outcomes Table

### Expected Columns:
- `outcome_id`: UUID format
- `prediction_id`: UUID matching predictions table
- `actual_direction`: Integer [-1, 0, 1]
- `actual_magnitude`: Float [0.0 - 20.0]
- `actual_return`: Float [-50.0 to 50.0] (percentage)
- `entry_price`: Float [1.0 to 500.0]
- `exit_price`: Float [1.0 to 500.0]
- `entry_timestamp`: ISO datetime
- `exit_timestamp`: ISO datetime

### 🚨 Red Flags:
- Return percentages outside [-50%, +50%] range
- Entry/exit prices exactly the same
- Timestamps that don't make logical sense (exit before entry)

## 3. Enhanced Features Table

### Expected Columns:
- `id`: Integer primary key
- `symbol`: Stock symbol
- `timestamp`: ISO datetime
- `sentiment_score`: [-1.0 to 1.0]
- `news_count`: [0 to 100]
- `technical_rsi`: [0.0 to 100.0]
- `technical_macd`: [-5.0 to 5.0]
- Various other technical and sentiment features

### 🚨 Red Flags:
- All RSI values exactly 50.0
- All MACD values exactly 0.0
- Identical feature sets across different symbols
- Missing or null critical technical indicators

## 4. Data Quality Checks

### Manual Validation Steps:
1. Check for static/default values across multiple records
2. Verify realistic ranges for all numerical features
3. Ensure timestamps are logical and recent
4. Confirm feature vectors have 20 elements each
5. Validate that different symbols have different characteristics
6. Check that sentiment scores correlate with news events
7. Ensure technical indicators show realistic market patterns

### Automated Red Flag Detection:
- Count records with RSI = 50.0
- Count records with MACD = 0.0
- Count records with sentiment = 0.0
- Identify duplicate feature vectors
- Find unrealistic price movements
- Detect timestamp anomalies

EOF

success "Data expectations documentation created: $LOCAL_EXPORT_DIR/DATA_EXPECTATIONS.md"
echo

# Step 3: Run quick data validation
log "🔍 Step 3: Running Quick Data Validation"
echo

# Create Python validation script
cat > "$LOCAL_EXPORT_DIR/validate_data.py" << 'EOF'
#!/usr/bin/env python3
"""
Quick data validation script to check for red flags
"""
import csv
import json
from collections import defaultdict, Counter
from datetime import datetime

def analyze_csv_file(filename, analysis_name):
    """Analyze a CSV file for red flags"""
    print(f"\n🔍 Analyzing {analysis_name}")
    print("=" * 50)
    
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        if not rows:
            print("❌ No data found")
            return
            
        print(f"📊 Total records: {len(rows)}")
        
        # Analyze based on file type
        if 'predictions' in filename:
            analyze_predictions(rows)
        elif 'enhanced_features' in filename:
            analyze_enhanced_features(rows)
        elif 'outcomes' in filename:
            analyze_outcomes(rows)
            
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
    except Exception as e:
        print(f"❌ Error analyzing {filename}: {e}")

def analyze_predictions(rows):
    """Analyze predictions table data"""
    # Count actions
    actions = Counter(row.get('predicted_action', 'UNKNOWN') for row in rows)
    print(f"📈 Action distribution: {dict(actions)}")
    
    # Check confidence ranges
    confidences = [float(row.get('action_confidence', 0)) for row in rows if row.get('action_confidence')]
    if confidences:
        print(f"🎯 Confidence range: {min(confidences):.3f} - {max(confidences):.3f}")
    
    # Analyze feature vectors for red flags
    red_flags = defaultdict(int)
    symbols_analyzed = set()
    
    for row in rows:
        symbol = row.get('symbol', 'UNKNOWN')
        symbols_analyzed.add(symbol)
        
        feature_vector = row.get('feature_vector', '')
        if feature_vector:
            try:
                features = json.loads(feature_vector)
                if len(features) >= 6:
                    # Check for red flag values
                    sentiment = features[0] if len(features) > 0 else None
                    rsi = features[4] if len(features) > 4 else None
                    macd = features[5] if len(features) > 5 else None
                    
                    if sentiment == 0.0:
                        red_flags['sentiment_zero'] += 1
                    if rsi == 50.0:
                        red_flags['rsi_50'] += 1
                    if macd == 0.0:
                        red_flags['macd_zero'] += 1
                        
            except json.JSONDecodeError:
                red_flags['invalid_json'] += 1
    
    print(f"🏦 Symbols analyzed: {sorted(symbols_analyzed)}")
    
    if red_flags:
        print("🚨 RED FLAGS DETECTED:")
        for flag, count in red_flags.items():
            percentage = (count / len(rows)) * 100
            print(f"   {flag}: {count} records ({percentage:.1f}%)")
    else:
        print("✅ No obvious red flags detected")

def analyze_enhanced_features(rows):
    """Analyze enhanced features table data"""
    symbols = Counter(row.get('symbol', 'UNKNOWN') for row in rows)
    print(f"🏦 Symbol distribution: {dict(symbols)}")
    
    # Check for static values
    rsi_values = [float(row.get('technical_rsi', 50)) for row in rows if row.get('technical_rsi')]
    sentiment_values = [float(row.get('sentiment_score', 0)) for row in rows if row.get('sentiment_score')]
    
    if rsi_values:
        unique_rsi = len(set(rsi_values))
        print(f"📊 RSI diversity: {unique_rsi} unique values from {len(rsi_values)} records")
        if unique_rsi == 1:
            print(f"🚨 RED FLAG: All RSI values are identical: {rsi_values[0]}")
    
    if sentiment_values:
        unique_sentiment = len(set(sentiment_values))
        print(f"📊 Sentiment diversity: {unique_sentiment} unique values")
        zero_sentiment = sum(1 for v in sentiment_values if v == 0.0)
        if zero_sentiment > len(sentiment_values) * 0.8:
            print(f"🚨 RED FLAG: {zero_sentiment} records have zero sentiment ({zero_sentiment/len(sentiment_values)*100:.1f}%)")

def analyze_outcomes(rows):
    """Analyze outcomes table data"""
    if not rows:
        print("ℹ️  No outcomes data (normal for new system)")
        return
        
    returns = [float(row.get('actual_return', 0)) for row in rows if row.get('actual_return')]
    if returns:
        print(f"💰 Return range: {min(returns):.2f}% to {max(returns):.2f}%")
        
        # Check for unrealistic returns
        extreme_returns = [r for r in returns if abs(r) > 20]
        if extreme_returns:
            print(f"🚨 RED FLAG: {len(extreme_returns)} extreme returns (>20%): {extreme_returns}")

if __name__ == "__main__":
    print("🔍 TRADING SYSTEM DATA VALIDATION")
    print("=" * 60)
    
    # Analyze all exported files
    files_to_analyze = [
        ("predictions.csv", "Predictions Table"),
        ("outcomes.csv", "Outcomes Table"),
        ("enhanced_features.csv", "Enhanced Features Table"),
        ("enhanced_outcomes.csv", "Enhanced Outcomes Table")
    ]
    
    for filename, analysis_name in files_to_analyze:
        analyze_csv_file(filename, analysis_name)
    
    print("\n" + "=" * 60)
    print("✅ Data validation complete!")
    print("\nReview the red flags above and check DATA_EXPECTATIONS.md for details.")
EOF

# Run the validation
log "Running data validation analysis..."
cd "$LOCAL_EXPORT_DIR"
python3 validate_data.py
cd - > /dev/null

echo
success "✅ Data Export and Validation Complete!"
echo
echo "📁 Files created in $LOCAL_EXPORT_DIR/:"
echo "   • predictions.csv - Latest predictions data"
echo "   • outcomes.csv - Outcomes data (if available)"
echo "   • enhanced_features.csv - Enhanced features data"
echo "   • enhanced_outcomes.csv - Enhanced outcomes data"
echo "   • DATA_EXPECTATIONS.md - Detailed expectations documentation"
echo "   • validate_data.py - Python validation script"
echo
echo "🔍 Next steps:"
echo "   1. Review the validation output above for red flags"
echo "   2. Open the CSV files in Excel/Numbers for manual inspection"
echo "   3. Check DATA_EXPECTATIONS.md for detailed value ranges"
echo "   4. Run the validation script again after any fixes"
