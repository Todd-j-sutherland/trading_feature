#!/bin/bash
# Daily Data Quality Monitor
# Run this script daily to monitor data quality

cd "$(dirname "$0")"
cd ..

echo "🔍 Running Daily Data Quality Check..."
echo "Date: $(date)"

# Run comprehensive analysis
python3 data_quality_manager.py --mode standard

# Check if critical issues found
if [ -f "../data/quality_reports/latest_critical_issues.txt" ]; then
    echo "🚨 CRITICAL ISSUES DETECTED - Check reports immediately!"
    # Could send email alert here
fi

echo "✅ Daily quality check complete"
