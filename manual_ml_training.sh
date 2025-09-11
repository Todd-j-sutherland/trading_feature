#!/bin/bash
"""
Manual ML Training Command
Use this script to manually retrain ML models anytime
"""

echo "🚀 Starting Manual ML Training..."
echo "📅 $(date)"

# Navigate to trading system directory
cd /root/test

# Run the ML training
echo "🎯 Running ML training..."
/root/trading_venv/bin/python simple_ml_training.py

# Check if training was successful
if [ $? -eq 0 ]; then
    echo "✅ ML training completed successfully!"
    echo "📊 Check the dashboard to see updated models"
else
    echo "❌ ML training failed!"
    echo "📋 Check logs/evening_ml_training.log for details"
fi

echo "🎯 Training session completed at $(date)"
