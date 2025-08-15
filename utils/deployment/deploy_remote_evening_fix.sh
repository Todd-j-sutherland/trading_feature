#!/bin/bash
"""
Deploy Evening Data Quality Fix to Remote Server

This script copies the necessary files to your remote server and runs the comprehensive fix.
"""

# Remote server details
REMOTE_HOST="root@170.64.199.151"
REMOTE_PATH="/root/test"

echo "🚀 DEPLOYING EVENING DATA QUALITY FIX TO REMOTE SERVER"
echo "=========================================================="

# Step 1: Copy the fixer script to remote server
echo "📦 Copying evening data fixer to remote server..."
scp remote_evening_data_fixer.py $REMOTE_HOST:$REMOTE_PATH/
if [ $? -eq 0 ]; then
    echo "✅ Evening data fixer copied successfully"
else
    echo "❌ Failed to copy evening data fixer"
    exit 1
fi

# Step 2: Copy the evening temporal guard and fixer
echo "📦 Copying temporal protection files..."
scp evening_temporal_guard.py $REMOTE_HOST:$REMOTE_PATH/
scp evening_temporal_fixer.py $REMOTE_HOST:$REMOTE_PATH/
if [ $? -eq 0 ]; then
    echo "✅ Temporal protection files copied successfully"
else
    echo "❌ Failed to copy temporal protection files"
    exit 1
fi

# Step 3: Copy enhanced outcomes evaluator
echo "📦 Copying enhanced outcomes evaluator..."
scp enhanced_outcomes_evaluator.py $REMOTE_HOST:$REMOTE_PATH/
if [ $? -eq 0 ]; then
    echo "✅ Enhanced outcomes evaluator copied successfully"
else
    echo "❌ Failed to copy enhanced outcomes evaluator"
    exit 1
fi

# Step 4: Copy technical analysis engine
echo "📦 Copying technical analysis engine..."
scp technical_analysis_engine.py $REMOTE_HOST:$REMOTE_PATH/
if [ $? -eq 0 ]; then
    echo "✅ Technical analysis engine copied successfully"
else
    echo "❌ Failed to copy technical analysis engine"
    exit 1
fi

echo ""
echo "🔧 RUNNING REMOTE EVENING DATA QUALITY FIX"
echo "=========================================================="

# Step 5: Run the comprehensive fix on remote server
echo "🚀 Executing evening data quality fix on remote server..."
ssh $REMOTE_HOST "cd $REMOTE_PATH && python3 remote_evening_data_fixer.py"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Remote evening data quality fix completed successfully!"
    echo ""
    echo "📊 NEXT STEPS:"
    echo "1. Check the remote fix report: $REMOTE_PATH/remote_evening_fix_report.json"
    echo "2. Run evening temporal guard: ssh $REMOTE_HOST 'cd $REMOTE_PATH && python3 evening_temporal_guard.py'"
    echo "3. Test evening routine: ssh $REMOTE_HOST 'cd $REMOTE_PATH && python3 -m app.main evening'"
    echo ""
else
    echo "❌ Remote evening data quality fix failed"
    echo "Check the remote server logs for details"
    exit 1
fi

echo "=========================================================="
echo "🏆 REMOTE DEPLOYMENT COMPLETED"
echo "🌐 Server: $REMOTE_HOST"
echo "📁 Path: $REMOTE_PATH"
echo "🔧 All evening data quality tools deployed and executed"
echo "=========================================================="
