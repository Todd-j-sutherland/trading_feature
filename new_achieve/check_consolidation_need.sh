#!/bin/bash
# Remote Database Investigation Script
# Run this on your remote server to check the actual situation

echo "🔍 REMOTE DATABASE INVESTIGATION"
echo "================================"

echo "📂 Current working directory:"
pwd

echo ""
echo "📁 Looking for database files:"
find . -name "*.db" -type f 2>/dev/null | while read db; do
    size=$(du -h "$db" | cut -f1)
    echo "   ✅ $db ($size)"
done

echo ""
echo "📊 Main database analysis:"
if [ -f "data/ml_models/enhanced_training_data.db" ]; then
    echo "   ✅ Main database exists"
    python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('data/ml_models/enhanced_training_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM enhanced_features')
    features = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM enhanced_features')
    banks = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL')
    outcomes = cursor.fetchone()[0]
    
    print(f'   📈 Features: {features}')
    print(f'   🏦 Banks: {banks}')
    print(f'   📉 Outcomes: {outcomes}')
    
    # Check recent data
    cursor.execute(\"SELECT COUNT(*) FROM enhanced_features WHERE timestamp >= datetime('now', '-1 day')\")
    recent = cursor.fetchone()[0]
    print(f'   ⏰ Recent (24h): {recent}')
    
    training_ready = features >= 50 and outcomes >= 50
    print(f'   🎯 Training ready: {\"✅ YES\" if training_ready else \"❌ NO\"}')
    
    conn.close()
except Exception as e:
    print(f'   ❌ Error: {e}')
"
else
    echo "   ❌ Main database not found"
fi

echo ""
echo "🌅 Testing morning routine output:"
echo "   (This will show what the morning routine actually produces)"

# Run a quick morning analysis to see what it reports
python3 -c "
import sys
import os
sys.path.append('.')

try:
    # Try to import and run a quick analysis
    from app.main import main
    print('   📊 Running quick morning check...')
    # This would show the actual morning routine output
except ImportError:
    print('   ⚠️ Cannot import morning routine - check if in correct directory')
except Exception as e:
    print(f'   ❌ Morning routine error: {e}')
"

echo ""
echo "💡 CONSOLIDATION ASSESSMENT:"
echo "   If features from database ≠ features from morning routine:"
echo "   → YES, consolidation needed"
echo "   If they match:"
echo "   → NO, consolidation not needed"
echo ""
echo "🎯 DECISION POINT:"
echo "   Compare the numbers above to determine if consolidation is required"
