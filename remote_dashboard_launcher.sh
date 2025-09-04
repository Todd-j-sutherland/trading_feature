#!/bin/bash
"""
Remote Dashboard Launcher
Runs both comprehensive_table_dashboard.py and enhanced_comprehensive_dashboard.py on remote server
"""

# Dashboard configuration
ORIGINAL_DASHBOARD="comprehensive_table_dashboard.py"
ENHANCED_DASHBOARD="enhanced_comprehensive_dashboard.py"
ORIGINAL_PORT="8502"
ENHANCED_PORT="8503"

echo "🚀 Starting Remote Dashboard Deployment..."
echo "Original Dashboard: $ORIGINAL_DASHBOARD on port $ORIGINAL_PORT"
echo "Enhanced Dashboard: $ENHANCED_DASHBOARD on port $ENHANCED_PORT"

# Stop any existing streamlit processes
echo "🛑 Stopping existing streamlit processes..."
pkill -f streamlit
sleep 3

# Verify working directory
cd /root/test
echo "📂 Working directory: $(pwd)"

# Check if files exist
if [ ! -f "$ORIGINAL_DASHBOARD" ]; then
    echo "❌ Original dashboard file not found: $ORIGINAL_DASHBOARD"
    exit 1
fi

if [ ! -f "$ENHANCED_DASHBOARD" ]; then
    echo "❌ Enhanced dashboard file not found: $ENHANCED_DASHBOARD"
    exit 1
fi

echo "✅ Both dashboard files verified"

# Create log directories
mkdir -p logs

# Start original dashboard
echo "🚀 Starting original comprehensive_table_dashboard.py on port $ORIGINAL_PORT..."
nohup /root/trading_venv/bin/streamlit run $ORIGINAL_DASHBOARD \
    --server.headless=true \
    --server.port=$ORIGINAL_PORT \
    --server.address=0.0.0.0 \
    > logs/original_dashboard.log 2>&1 &

ORIGINAL_PID=$!
echo "Original dashboard PID: $ORIGINAL_PID"

# Wait a moment for startup
sleep 5

# Start enhanced dashboard
echo "🚀 Starting enhanced_comprehensive_dashboard.py on port $ENHANCED_PORT..."
nohup /root/trading_venv/bin/streamlit run $ENHANCED_DASHBOARD \
    --server.headless=true \
    --server.port=$ENHANCED_PORT \
    --server.address=0.0.0.0 \
    > logs/enhanced_dashboard.log 2>&1 &

ENHANCED_PID=$!
echo "Enhanced dashboard PID: $ENHANCED_PID"

# Wait for startup
sleep 10

# Verify both processes are running
echo "🔍 Verifying dashboard processes..."
ps aux | grep streamlit | grep -v grep

# Check if ports are listening
echo "🔍 Checking port status..."
netstat -tulpn | grep :$ORIGINAL_PORT || echo "⚠️ Original port $ORIGINAL_PORT not listening"
netstat -tulpn | grep :$ENHANCED_PORT || echo "⚠️ Enhanced port $ENHANCED_PORT not listening"

# Display access URLs
echo ""
echo "🎯 DASHBOARD ACCESS URLS:"
echo "📊 Original Dashboard: http://170.64.199.151:$ORIGINAL_PORT"
echo "🎯 Enhanced Dashboard: http://170.64.199.151:$ENHANCED_PORT"
echo ""
echo "📝 Log files:"
echo "   Original: /root/test/logs/original_dashboard.log"
echo "   Enhanced: /root/test/logs/enhanced_dashboard.log"
echo ""
echo "✅ Both dashboards deployed successfully!"
