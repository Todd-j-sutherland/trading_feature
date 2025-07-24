#!/bin/bash
"""
Enhanced Dashboard Startup Script with Cache Clearing
Usage: ./start_dashboard_fresh.sh
"""

echo "🚀 STARTING ENHANCED DASHBOARD WITH FRESH CACHE"
echo "================================================"

cd /root/test

# Activate virtual environment
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test

echo "🧹 Clearing caches..."
python clear_dashboard_cache.py

echo ""
echo "🌐 Starting Streamlit dashboard..."
echo "📊 Dashboard will be available at: http://170.64.199.151:8501"
echo "⏹️  To stop: pkill -f streamlit"
echo ""

# Start dashboard
nohup streamlit run app/dashboard/enhanced_main.py --server.port 8501 --server.headless true > dashboard.log 2>&1 &

echo "✅ Dashboard started successfully!"
echo "📋 Check logs with: tail -f /root/test/dashboard.log"
echo "🔍 Check status with: ps aux | grep streamlit"
