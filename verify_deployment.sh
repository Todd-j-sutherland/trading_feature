#!/bin/bash
echo "🔍 VERIFYING MARKET-AWARE DEPLOYMENT"
echo "====================================="

# Check if files exist
echo "📁 Checking files..."
if [ -f "/root/test/market-aware-paper-trading/main.py" ]; then
    echo "✅ main.py deployed"
else
    echo "❌ main.py missing"
fi

if [ -f "/root/test/market-aware-paper-trading/market_aware_prediction_system.py" ]; then
    echo "✅ market_aware_prediction_system.py deployed"
else
    echo "❌ market_aware_prediction_system.py missing"
fi

if [ -f "/root/test/enhanced_efficient_system_market_aware.py" ]; then
    echo "✅ enhanced_efficient_system_market_aware.py deployed"
else
    echo "❌ enhanced_efficient_system_market_aware.py missing"
fi

if [ -f "/root/test/start_market_aware.sh" ]; then
    echo "✅ start_market_aware.sh deployed"
else
    echo "❌ start_market_aware.sh missing"
fi

# Test Python imports
echo -e "\n🐍 Testing Python imports..."
cd /root/test/market-aware-paper-trading

python -c "
try:
    import yfinance as yf
    print('✅ yfinance available')
except:
    print('❌ yfinance not available')

try:
    import numpy as np
    print('✅ numpy available') 
except:
    print('❌ numpy not available')

try:
    from market_aware_prediction_system import MarketAwarePredictionSystem
    print('✅ MarketAwarePredictionSystem imported')
except Exception as e:
    print(f'❌ MarketAwarePredictionSystem import failed: {e}')
"

echo -e "\n📊 Testing market context..."
timeout 15 python -c "
try:
    from market_aware_prediction_system import MarketAwarePredictionSystem
    system = MarketAwarePredictionSystem()
    context = system.get_market_context()
    print(f'✅ Market context: {context[\"context\"]} ({context[\"trend_pct\"]:+.2f}%)')
except Exception as e:
    print(f'❌ Market context test failed: {e}')
"

echo -e "\n✅ VERIFICATION COMPLETE"
