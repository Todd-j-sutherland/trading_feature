#!/bin/bash
"""
Complete Dashboard Suite Launcher
Runs comprehensive table dashboard, enhanced dashboard, and live metrics dashboard
"""

# Dashboard configuration
ORIGINAL_DASHBOARD="comprehensive_table_dashboard.py"
ENHANCED_DASHBOARD="enhanced_comprehensive_dashboard.py" 
LIVE_METRICS_DASHBOARD="live_trading_metrics_dashboard.py"
ORIGINAL_PORT="8502"
ENHANCED_PORT="8503"
LIVE_METRICS_PORT="8504"

echo "🚀 LAUNCHING COMPLETE DASHBOARD SUITE"
echo "====================================="
echo "📊 Original Dashboard: $ORIGINAL_DASHBOARD on port $ORIGINAL_PORT"
echo "🎯 Enhanced Dashboard: $ENHANCED_DASHBOARD on port $ENHANCED_PORT"
echo "🔴 Live Metrics Dashboard: $LIVE_METRICS_DASHBOARD on port $LIVE_METRICS_PORT"

# Stop any existing streamlit processes
echo "🛑 Stopping existing streamlit processes..."
pkill -f streamlit
sleep 3

# Verify working directory
cd /root/test
echo "📂 Working directory: $(pwd)"

# Check if files exist
for dashboard in "$ORIGINAL_DASHBOARD" "$ENHANCED_DASHBOARD" "$LIVE_METRICS_DASHBOARD"; do
    if [ ! -f "$dashboard" ]; then
        echo "❌ Dashboard file not found: $dashboard"
        exit 1
    fi
done

echo "✅ All dashboard files verified"

# Create log directories
mkdir -p logs

# Start original dashboard
echo "🚀 Starting original dashboard on port $ORIGINAL_PORT..."
nohup /root/trading_venv/bin/streamlit run $ORIGINAL_DASHBOARD \
    --server.headless=true \
    --server.port=$ORIGINAL_PORT \
    --server.address=0.0.0.0 \
    > logs/original_dashboard.log 2>&1 &

ORIGINAL_PID=$!
echo "Original dashboard PID: $ORIGINAL_PID"

# Wait for startup
sleep 5

# Start enhanced dashboard
echo "🚀 Starting enhanced dashboard on port $ENHANCED_PORT..."
nohup /root/trading_venv/bin/streamlit run $ENHANCED_DASHBOARD \
    --server.headless=true \
    --server.port=$ENHANCED_PORT \
    --server.address=0.0.0.0 \
    > logs/enhanced_dashboard.log 2>&1 &

ENHANCED_PID=$!
echo "Enhanced dashboard PID: $ENHANCED_PID"

# Wait for startup
sleep 5

# Start live metrics dashboard
echo "🚀 Starting live metrics dashboard on port $LIVE_METRICS_PORT..."
nohup /root/trading_venv/bin/streamlit run $LIVE_METRICS_DASHBOARD \
    --server.headless=true \
    --server.port=$LIVE_METRICS_PORT \
    --server.address=0.0.0.0 \
    > logs/live_metrics_dashboard.log 2>&1 &

LIVE_METRICS_PID=$!
echo "Live metrics dashboard PID: $LIVE_METRICS_PID"

# Wait for startup
sleep 10

# Verify all processes are running
echo "🔍 Verifying dashboard processes..."
ps aux | grep streamlit | grep -v grep

# Check if ports are listening
echo "🔍 Checking port status..."
netstat -tulpn | grep :$ORIGINAL_PORT || echo "⚠️ Original port $ORIGINAL_PORT not listening"
netstat -tulpn | grep :$ENHANCED_PORT || echo "⚠️ Enhanced port $ENHANCED_PORT not listening"
netstat -tulpn | grep :$LIVE_METRICS_PORT || echo "⚠️ Live metrics port $LIVE_METRICS_PORT not listening"

# Display access URLs
echo ""
echo "🎯 COMPLETE DASHBOARD SUITE ACCESS URLS:"
echo "=========================================="
echo "📊 Original Dashboard (Comprehensive Tables): http://170.64.199.151:$ORIGINAL_PORT"
echo "🎯 Enhanced Dashboard (Advanced Metrics):     http://170.64.199.151:$ENHANCED_PORT"
echo "🔴 Live Metrics Dashboard (Real-time):        http://170.64.199.151:$LIVE_METRICS_PORT"
echo ""
echo "📝 Log files:"
echo "   Original:    /root/test/logs/original_dashboard.log"
echo "   Enhanced:    /root/test/logs/enhanced_dashboard.log"
echo "   Live Metrics: /root/test/logs/live_metrics_dashboard.log"
echo ""
echo "🔄 Dashboard Purposes:"
echo "   📊 Original (8502):  Historical data, outcomes, traditional tables"
echo "   🎯 Enhanced (8503):  Success rates, trends, profit tracking" 
echo "   🔴 Live (8504):     Real-time sentiment, technical, ML confidence"
echo ""
echo "✅ Complete dashboard suite deployed successfully!"
echo "💡 All three dashboards complement each other for complete market coverage"
