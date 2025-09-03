#!/usr/bin/env python3
"""
Deploy Market-Aware Paper Trading System
Copies the enhanced system to remote server and integrates with existing setup
"""

echo "🚀 DEPLOYING MARKET-AWARE PAPER TRADING SYSTEM"
echo "================================================"

# Remote server details
REMOTE_SERVER="root@170.64.199.151"
REMOTE_BASE_DIR="/root/test"
REMOTE_APP_DIR="/root/test/paper-trading-app"

echo "📋 Deployment Plan:"
echo "   • Copy market-aware system to remote server"
echo "   • Create integrated paper trading setup"
echo "   • Test market context analysis"
echo "   • Provide usage instructions"

# Create remote directory for market-aware system
echo -e "\n🔧 Setting up remote directories..."
ssh $REMOTE_SERVER "mkdir -p $REMOTE_BASE_DIR/market-aware-paper-trading"

# Copy market-aware system files
echo -e "\n📁 Copying market-aware system files..."
scp "market-aware-paper-trading/main.py" \
    "$REMOTE_SERVER:$REMOTE_BASE_DIR/market-aware-paper-trading/"

scp "market-aware-paper-trading/market_aware_prediction_system.py" \
    "$REMOTE_SERVER:$REMOTE_BASE_DIR/market-aware-paper-trading/"

# Copy supporting files
echo -e "\n📁 Copying supporting files..."
scp "enhanced_efficient_system_market_aware.py" \
    "$REMOTE_SERVER:$REMOTE_BASE_DIR/"

# Create requirements file
echo -e "\n📝 Creating requirements file..."
cat > requirements_market_aware.txt << 'EOF'
yfinance>=0.1.87
numpy>=1.21.0
pandas>=1.3.0
sqlite3
logging
datetime
pathlib
EOF

scp "requirements_market_aware.txt" \
    "$REMOTE_SERVER:$REMOTE_BASE_DIR/market-aware-paper-trading/"

# Create startup script
echo -e "\n🔧 Creating startup script..."
cat > start_market_aware.sh << 'EOF'
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
EOF

chmod +x start_market_aware.sh
scp "start_market_aware.sh" "$REMOTE_SERVER:$REMOTE_BASE_DIR/"

# Create cron integration script
echo -e "\n⏰ Creating cron integration..."
cat > cron_market_aware.txt << 'EOF'
# Market-Aware Paper Trading Cron Jobs

# Morning routine (7:00 AM weekdays) - Generate signals
0 7 * * 1-5 cd /root/test && ./start_market_aware.sh morning >> /root/test/logs/market_aware_morning.log 2>&1

# Continuous monitoring during market hours (every 30 minutes, 10 AM - 4 PM weekdays)  
*/30 10-16 * * 1-5 cd /root/test && ./start_market_aware.sh test >> /root/test/logs/market_aware_signals.log 2>&1

# Status check (6:00 PM weekdays)
0 18 * * 1-5 cd /root/test && ./start_market_aware.sh status >> /root/test/logs/market_aware_status.log 2>&1
EOF

scp "cron_market_aware.txt" "$REMOTE_SERVER:$REMOTE_BASE_DIR/"

# Create usage guide
echo -e "\n📖 Creating usage guide..."
cat > MARKET_AWARE_USAGE.md << 'EOF'
# Market-Aware Paper Trading System - Usage Guide

## Commands

### Basic Commands
```bash
# Morning routine with market analysis
cd /root/test && ./start_market_aware.sh morning

# Generate trading signals  
cd /root/test && ./start_market_aware.sh test

# Check system status
cd /root/test && ./start_market_aware.sh status

# Continuous monitoring (runs until stopped)
cd /root/test && ./start_market_aware.sh monitor
```

### Direct Python Commands
```bash
cd /root/test/market-aware-paper-trading

# Morning routine
python main.py morning

# Test signal generation
python main.py test

# Status check
python main.py status

# Continuous monitoring
python main.py monitor
```

## Expected Output

### During BEARISH Market:
- Fewer BUY signals (40-60% reduction expected)
- Higher confidence thresholds applied
- Market stress warnings
- Stricter news sentiment requirements

### During BULLISH Market:
- More opportunities identified
- Lower confidence thresholds
- Enhanced signal generation

### During NEUTRAL Market:
- Standard criteria applied
- Balanced approach

## Log Files
- `/root/test/logs/market_aware_morning.log` - Morning routine logs
- `/root/test/logs/market_aware_signals.log` - Signal generation logs  
- `/root/test/logs/market_aware_status.log` - Status check logs
- `/root/test/market-aware-paper-trading/market_aware_paper_trading.log` - Main application log

## Integration with Existing Paper Trading

The system is designed to work alongside your existing paper trading setup:
- Uses existing `enhanced_paper_trading_service.py`
- Integrates with `enhanced_ig_markets_integration.py`
- Maintains compatibility with current database structure

## Cron Job Integration

Add to crontab for automated operation:
```bash
crontab -e
# Then add contents from cron_market_aware.txt
```
EOF

scp "MARKET_AWARE_USAGE.md" "$REMOTE_SERVER:$REMOTE_BASE_DIR/"

# Ensure log directory exists
echo -e "\n💾 Setting up logging..."
ssh $REMOTE_SERVER "mkdir -p $REMOTE_BASE_DIR/logs"

# Test deployment
echo -e "\n🧪 Testing deployment..."

# Test Python imports
echo -e "\n📊 Testing Python imports..."
ssh $REMOTE_SERVER "cd $REMOTE_BASE_DIR/market-aware-paper-trading && python -c \"
try:
    from market_aware_prediction_system import MarketAwarePredictionSystem
    print('✅ Market-aware prediction system imported successfully')
    
    import yfinance as yf
    print('✅ yfinance available')
    
    import numpy as np
    print('✅ numpy available')
    
except Exception as e:
    print(f'❌ Import error: {e}')
\"" || echo "⚠️ Some imports may not be available"

# Test market context analysis
echo -e "\n🌐 Testing market context analysis..."
ssh $REMOTE_SERVER "cd $REMOTE_BASE_DIR && timeout 30 ./start_market_aware.sh status" || {
    echo "⚠️ Market context test timed out or failed"
}

# Show file structure
echo -e "\n📂 Remote file structure:"
ssh $REMOTE_SERVER "find $REMOTE_BASE_DIR -name '*market*' -type f"

echo -e "\n✅ DEPLOYMENT COMPLETED"

echo -e "\n🎯 QUICK START COMMANDS:"
echo "   # Test market context:"
echo "   ssh $REMOTE_SERVER 'cd /root/test && ./start_market_aware.sh status'"
echo ""
echo "   # Run morning analysis:"  
echo "   ssh $REMOTE_SERVER 'cd /root/test && ./start_market_aware.sh morning'"
echo ""
echo "   # Generate signals:"
echo "   ssh $REMOTE_SERVER 'cd /root/test && ./start_market_aware.sh test'"

echo -e "\n💡 INTEGRATION OPTIONS:"
echo "   1. Run parallel with existing system for comparison"
echo "   2. Replace existing prediction system in cron"
echo "   3. Use for manual trading decisions"
echo "   4. Integrate with existing paper trading service"

echo -e "\n📊 MONITORING:"
echo "   • Check market context detection accuracy"
echo "   • Monitor BUY signal reduction during bearish markets"
echo "   • Compare signal quality with original system"
echo "   • Validate paper trading integration"

# Clean up local files
rm -f requirements_market_aware.txt
rm -f start_market_aware.sh  
rm -f cron_market_aware.txt
rm -f MARKET_AWARE_USAGE.md
