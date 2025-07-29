#!/bin/bash

# Remote ML Metrics Dashboard Launcher
# Starts the enhanced dashboard with ML performance metrics

SERVER="root@170.64.199.151"
SSH_KEY="~/.ssh/id_rsa"

echo "🚀 Starting Enhanced ML Dashboard on Remote Server"
echo "=================================================="

# Start the dashboard
ssh -i "$SSH_KEY" "$SERVER" '
cd /root/test
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test

echo "📊 Enhanced Dashboard with ML Performance Metrics"
echo "Access URL: http://170.64.199.151:8501"
echo "Dashboard Features:"
echo "  ✅ Real-time ML performance tracking"
echo "  ✅ Accuracy & confidence progression charts"
echo "  ✅ Model training progress visualization"
echo "  ✅ Trading performance analysis"
echo "  ✅ Detailed performance logs"
echo ""
echo "Navigate to the \"Learning Metrics\" tab for ML analysis"
echo ""
echo "🎯 Starting Streamlit dashboard..."

# Kill any existing streamlit processes
pkill -f streamlit 2>/dev/null

# Start streamlit in background
nohup streamlit run app/dashboard/enhanced_main.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    > streamlit.log 2>&1 &

# Wait a moment for startup
sleep 5

# Check if it started successfully
if pgrep -f streamlit > /dev/null; then
    echo "✅ Dashboard started successfully"
    echo "📊 Access at: http://170.64.199.151:8501"
    echo "📋 Log file: /root/test/streamlit.log"
else
    echo "❌ Dashboard failed to start"
    echo "📋 Check log: /root/test/streamlit.log"
fi
'

echo ""
echo "=================================================="
echo "✅ Remote ML Dashboard Setup Complete"
echo "🌐 Access your dashboard at: http://170.64.199.151:8501"
echo "📊 Navigate to 'Learning Metrics' tab for ML performance"
echo "=================================================="
