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
