#!/bin/bash
echo "🏎️  ASX Trading System Performance Monitor"
echo "=========================================="
echo ""

# Test all backend endpoints
echo "📊 Testing Backend Performance:"
echo ""

echo "🔍 Main Backend (Port 8000):"
echo "  /api/status:"
time_result=$(curl -w "%{time_total}s" -s -o /dev/null http://localhost:8000/api/status)
echo "    Response Time: ${time_result}"

echo "  /api/banks/CBA.AX/ohlcv:"
time_result=$(curl -w "%{time_total}s" -s -o /dev/null "http://localhost:8000/api/banks/CBA.AX/ohlcv?period=1D")
echo "    Response Time: ${time_result}"

echo "  /api/banks/CBA.AX/ml-indicators:"
time_result=$(curl -w "%{time_total}s" -s -o /dev/null "http://localhost:8000/api/banks/CBA.AX/ml-indicators")
echo "    Response Time: ${time_result}"

echo ""
echo "🤖 ML Backend (Port 8001):"
echo "  /api/market-summary:"
time_result=$(curl -w "%{time_total}s" -s -o /dev/null http://localhost:8001/api/market-summary)
echo "    Response Time: ${time_result}"

echo ""
echo "🎨 Frontend (Port 3002):"
echo "  Main page:"
time_result=$(curl -w "%{time_total}s" -s -o /dev/null http://localhost:3002)
echo "    Response Time: ${time_result}"

echo ""
echo "📈 System Resources:"
echo "  Memory Usage:"
ps aux | grep -E "(api_server|uvicorn|vite)" | grep -v grep | awk '{print "    " $11 ": " $4 "% memory, " $3 "% CPU"}'

echo ""
echo "✅ Performance test completed!"
