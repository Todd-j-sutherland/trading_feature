#!/bin/bash
echo "🧪 Frontend API Compatibility Test"
echo "=================================="
echo ""

# Test all endpoints that the frontend uses
SYMBOL="CBA.AX"
BASE_URL="http://localhost:8000"

echo "Testing endpoints for symbol: $SYMBOL"
echo ""

echo "1. 📊 OHLCV Data:"
result=$(curl -s -w "%{http_code}" "$BASE_URL/api/banks/$SYMBOL/ohlcv?period=1D")
http_code="${result: -3}"
if [ "$http_code" = "200" ]; then
    echo "   ✅ /api/banks/$SYMBOL/ohlcv - OK"
else
    echo "   ❌ /api/banks/$SYMBOL/ohlcv - HTTP $http_code"
fi

echo ""
echo "2. 🤖 ML Indicators:"
result=$(curl -s -w "%{http_code}" "$BASE_URL/api/banks/$SYMBOL/ml-indicators")
http_code="${result: -3}"
if [ "$http_code" = "200" ]; then
    echo "   ✅ /api/banks/$SYMBOL/ml-indicators - OK"
else
    echo "   ❌ /api/banks/$SYMBOL/ml-indicators - HTTP $http_code"
fi

echo ""
echo "3. 💰 Live Price:"
result=$(curl -s -w "%{http_code}" "$BASE_URL/api/live/price/$SYMBOL")
http_code="${result: -3}"
if [ "$http_code" = "200" ]; then
    echo "   ✅ /api/live/price/$SYMBOL - OK"
else
    echo "   ❌ /api/live/price/$SYMBOL - HTTP $http_code"
fi

echo ""
echo "4. 📈 Live Technical:"
result=$(curl -s -w "%{http_code}" "$BASE_URL/api/live/technical/$SYMBOL")
http_code="${result: -3}"
if [ "$http_code" = "200" ]; then
    echo "   ✅ /api/live/technical/$SYMBOL - OK"
else
    echo "   ❌ /api/live/technical/$SYMBOL - HTTP $http_code"
fi

echo ""
echo "5. 😊 Sentiment:"
result=$(curl -s -w "%{http_code}" "$BASE_URL/api/sentiment/current")
http_code="${result: -3}"
if [ "$http_code" = "200" ]; then
    echo "   ✅ /api/sentiment/current - OK"
else
    echo "   ❌ /api/sentiment/current - HTTP $http_code"
fi

echo ""
echo "6. ⚡ Status:"
result=$(curl -s -w "%{http_code}" "$BASE_URL/api/status")
http_code="${result: -3}"
if [ "$http_code" = "200" ]; then
    echo "   ✅ /api/status - OK"
else
    echo "   ❌ /api/status - HTTP $http_code"
fi

echo ""
echo "🎯 Performance Test:"
echo "   OHLCV Response Time:"
time_result=$(curl -w "   %{time_total}s" -s -o /dev/null "$BASE_URL/api/banks/$SYMBOL/ohlcv?period=1D")
echo "$time_result"

echo "   Live Price Response Time:"
time_result=$(curl -w "   %{time_total}s" -s -o /dev/null "$BASE_URL/api/live/price/$SYMBOL")
echo "$time_result"

echo ""
echo "✅ Frontend API compatibility test completed!"
