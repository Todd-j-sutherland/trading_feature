#!/bin/bash
echo "🔄 Restarting ML Trading System on Remote"
echo "========================================="

# Connect to remote and restart the system
ssh root@170.64.199.151 << 'EOF'
    echo "🛑 Stopping existing processes..."
    pkill -f "api_server.py" 2>/dev/null || echo "No api_server.py processes found"
    pkill -f "realtime_ml_api.py" 2>/dev/null || echo "No realtime_ml_api processes found"
    pkill -f "start_complete_ml_system.sh" 2>/dev/null || echo "No system startup processes found"
    
    # Wait for processes to stop
    sleep 3
    
    echo "🏁 Starting fresh ML system..."
    cd /root/test
    
    # Run the complete system in background
    nohup ./start_complete_ml_system.sh > ml_system.log 2>&1 &
    
    echo "✅ System restart initiated"
    echo "📊 System will be available in ~15 seconds at:"
    echo "   Frontend: http://170.64.199.151:3002"
    echo "   Main API: http://170.64.199.151:8000"
    echo "   ML API: http://170.64.199.151:8001"
    echo ""
    echo "📝 To monitor logs: tail -f /root/test/ml_system.log"
EOF

echo ""
echo "🎉 Remote restart complete!"
echo "💡 The feature mismatch fix is now active"
echo "⏰ Give the system 15-20 seconds to fully initialize"
