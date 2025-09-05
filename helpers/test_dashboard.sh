#!/bin/bash

echo "🔍 Testing ASX Trading Dashboard..."

# Test API Server
echo "📊 Testing API Server..."
API_RESPONSE=$(curl -s "http://localhost:8000/api/banks/CBA.AX/ml-indicators?period=1D" | head -100)
if [[ $API_RESPONSE == *"success"* ]]; then
    echo "✅ API Server is responding"
    
    # Count signals
    BUY_COUNT=$(echo $API_RESPONSE | grep -o '"signal":"BUY"' | wc -l)
    SELL_COUNT=$(echo $API_RESPONSE | grep -o '"signal":"SELL"' | wc -l)
    HOLD_COUNT=$(echo $API_RESPONSE | grep -o '"signal":"HOLD"' | wc -l)
    
    echo "   📈 BUY signals: $BUY_COUNT"
    echo "   📉 SELL signals: $SELL_COUNT"  
    echo "   ⏸️  HOLD signals: $HOLD_COUNT"
else
    echo "❌ API Server not responding"
fi

# Test Frontend
echo ""
echo "🌐 Testing Frontend..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3002")
if [[ $FRONTEND_RESPONSE == "200" ]]; then
    echo "✅ Frontend is responding"
else
    echo "❌ Frontend not responding (HTTP $FRONTEND_RESPONSE)"
fi

# Check processes
echo ""
echo "🔧 Process Status..."
API_PID=$(pgrep -f "api_server.py")
FRONTEND_PID=$(pgrep -f "vite")

if [[ -n $API_PID ]]; then
    echo "✅ API Server running (PID: $API_PID)"
else
    echo "❌ API Server not running"
fi

if [[ -n $FRONTEND_PID ]]; then
    echo "✅ Frontend running (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend not running"
fi

echo ""
echo "🎯 Dashboard URLs:"
echo "   Frontend: http://localhost:3002"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔧 Quick Commands:"
echo "   Test signals: curl 'http://localhost:8000/api/banks/CBA.AX/ml-indicators?period=1D' | jq '.data[0]'"
echo "   View API docs: open http://localhost:8000/docs"
echo "   Open dashboard: open http://localhost:3002"
