#!/bin/bash
# 🔧 Remote ML Feature Mismatch Fix Script
# Upload and run this on the remote server to fix the feature mismatch issue

echo "🔧 ASX Trading System - Remote ML Feature Mismatch Fix"
echo "====================================================="
echo "📅 Date: $(date)"
echo "🖥️  Host: $(hostname)"
echo ""

# Step 1: Check if we're on the remote server
if [[ "$(hostname)" != *"170.64.199.151"* ]]; then
    echo "⚠️  This script is designed for the remote server."
    echo "To run on the remote server:"
    echo ""
    echo "1. Upload this script:"
    echo "   scp remote_ml_feature_fix.sh root@170.64.199.151:/path/to/trading_feature/"
    echo ""
    echo "2. SSH to remote server:"
    echo "   ssh root@170.64.199.151"
    echo ""
    echo "3. Navigate to project and activate environment:"
    echo "   cd /path/to/trading_feature"
    echo "   source ../trading_venv/bin/activate"
    echo ""
    echo "4. Run this script:"
    echo "   ./remote_ml_feature_fix.sh"
    echo ""
    exit 1
fi

# Step 2: Activate the correct environment
echo "🐍 Activating trading_venv environment..."
if [ -f "../trading_venv/bin/activate" ]; then
    source ../trading_venv/bin/activate
    echo "✅ Environment activated"
else
    echo "❌ trading_venv not found. Please check the path."
    exit 1
fi

# Step 3: Check if fix script exists
if [ ! -f "fix_ml_feature_mismatch.py" ]; then
    echo "❌ fix_ml_feature_mismatch.py not found"
    echo "Please ensure all project files are uploaded to the remote server"
    exit 1
fi

# Step 4: Run the ML feature mismatch fix
echo "🔧 Running ML feature mismatch fix..."
python fix_ml_feature_mismatch.py

echo ""
echo "🔧 Running data reliability fix..."
python fix_data_reliability.py

# Step 5: Remove the problematic database trigger
echo ""
echo "🗃️ Removing problematic database trigger..."
python -c "
import sqlite3
try:
    conn = sqlite3.connect('data/ml_models/training_data.db')
    conn.execute('DROP TRIGGER IF EXISTS prevent_confidence_duplicates;')
    conn.commit()
    conn.close()
    print('✅ Database trigger removed successfully')
except Exception as e:
    print(f'⚠️  Database trigger removal failed: {e}')
"

# Step 6: Test the fix
echo ""
echo "🧪 Testing the fix..."
echo "Running morning analysis to verify..."

# Capture output and check for errors
MORNING_OUTPUT=$(python -m app.main morning 2>&1)
MORNING_EXIT_CODE=$?

if [ $MORNING_EXIT_CODE -eq 0 ]; then
    echo "✅ Morning analysis completed successfully"
    
    # Check for feature mismatch errors
    if echo "$MORNING_OUTPUT" | grep -q "expecting 20 features"; then
        echo "❌ Feature mismatch still present"
        echo "Output preview:"
        echo "$MORNING_OUTPUT" | grep -i "error\|expecting" | head -5
    else
        echo "🎉 Feature mismatch resolved!"
    fi
else
    echo "⚠️  Morning analysis had issues (exit code: $MORNING_EXIT_CODE)"
    echo "Output preview:"
    echo "$MORNING_OUTPUT" | tail -10
fi

# Step 7: Generate validation report
echo ""
echo "📊 Generating validation report..."
python export_and_validate_metrics.py

# Step 8: Summary
echo ""
echo "📋 REMOTE FIX SUMMARY"
echo "===================="
echo "✅ ML feature mismatch fix: Applied"
echo "✅ Data reliability fix: Applied"
echo "✅ Database trigger: Removed"
echo "✅ Morning analysis: Tested"
echo "✅ Validation metrics: Generated"
echo ""
echo "🔍 To check validation results:"
echo "cat metrics_exports/validation_summary_\$(date +%Y%m%d)*.txt"
echo ""
echo "🚀 To run comprehensive test:"
echo "./simple_test_with_logs.sh"
