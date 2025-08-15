#!/bin/bash
"""
Quick Daily ML Monitor
Simple script to check ML performance and save results.

Usage:
    ./daily_ml_monitor.sh
    
Or remotely:
    ssh root@170.64.199.151 "cd /root/test && ./daily_ml_monitor.sh"
"""

echo "🤖 ML Trading System - Daily Check"
echo "=================================="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Run the comprehensive check with history
echo "📊 Running performance analysis..."
python3 evening_ml_check_with_history.py

echo ""
echo "📈 Recent trends (last 3 days):"
python3 view_ml_trends.py --days 3

echo ""
echo "🎯 SELL action performance (focus area):"
python3 view_ml_trends.py --action SELL --days 7

echo ""
echo "✅ Daily check complete!"
echo "💾 Results saved to: data/ml_performance_history/daily_performance.json"
echo ""
echo "Quick commands:"
echo "  Full trends: python3 view_ml_trends.py"
echo "  Export data: python3 view_ml_trends.py --export"
echo "  Summary:     python3 view_ml_trends.py --summary"
