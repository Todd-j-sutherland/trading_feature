#!/bin/bash
# Market-Aware Paper Trading Startup Script

echo "🚀 Starting Market-Aware Paper Trading System..."

cd /root/test/market-aware-paper-trading

# Activate virtual environment if it exists
if [ -d "/root/trading_venv" ]; then
    source /root/trading_venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Set Python path
export PYTHONPATH="/root/test:/root/test/paper-trading-app:$PYTHONPATH"

# Run the system
python main.py "$@"
