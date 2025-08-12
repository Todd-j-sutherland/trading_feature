#!/bin/bash
# Weekly Deep Data Quality Analysis
# Run this script weekly for comprehensive analysis with ML training

cd "$(dirname "$0")"
cd ..

echo "🧠 Running Weekly Deep Analysis..."
echo "Date: $(date)"

# Run full analysis with ML training
python3 data_quality_manager.py --mode full

echo "✅ Weekly deep analysis complete"
