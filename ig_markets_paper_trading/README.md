# IG Markets Paper Trading System

## Overview

This is a self-contained paper trading system that integrates with IG Markets demo API to execute virtual trades based on predictions from the main trading system. It includes position management, fund tracking, and Phase 4 exit strategy integration.

## Features

- **OAuth Authentication**: Secure connection to IG Markets demo API
- **Position Management**: Maximum 1 position per symbol at any time
- **Fund Management**: Available funds checking before trade execution
- **Exit Strategy Integration**: Phase 4 exit strategy for intelligent position exits
- **Performance Tracking**: Comprehensive P&L and performance metrics
- **Data Consistency**: Uses IG Markets data for both execution and evaluation

## Architecture

```
ig_markets_paper_trading/
├── README.md                           # This documentation
├── config/
│   ├── ig_markets_config.json         # IG Markets API configuration
│   └── trading_parameters.json        # Trading rules and limits
├── src/
│   ├── __init__.py
│   ├── paper_trader.py                # Main paper trading engine
│   ├── position_manager.py            # Position and fund management
│   ├── ig_markets_client.py           # IG Markets API client
│   └── performance_tracker.py         # Performance analysis
├── data/
│   └── paper_trading.db               # SQLite database for trades
├── logs/
│   └── paper_trading.log              # Trading activity logs
├── tests/
│   ├── test_paper_trader.py           # Unit tests
│   └── test_position_manager.py       # Position management tests
├── scripts/
│   ├── deploy.sh                      # Deployment script
│   ├── run_paper_trader.py            # Main execution script
│   └── performance_report.py          # Generate performance reports
└── docs/
    ├── api_integration.md              # IG Markets API documentation
    ├── position_management.md          # Position management rules
    └── removal_guide.md                # How to remove the system
```

## Key Components

### 1. Position Manager
- Enforces 1 position per symbol rule
- Checks available funds before trades
- Manages position sizing based on account balance
- Prevents over-leverage

### 2. IG Markets Client
- OAuth authentication with token management
- Real-time market data retrieval
- Trade execution simulation
- Error handling and rate limiting

### 3. Paper Trader Engine
- Processes new predictions from main system
- Executes paper trades based on available funds
- Applies exit strategy using Phase 4 engine
- Logs all trading activity

### 4. Performance Tracker
- Real-time P&L calculation
- Win rate and drawdown metrics
- Performance reporting
- Risk analysis

## Installation and Setup

### 1. Configuration
Update `config/ig_markets_config.json` with your IG Markets demo credentials:

```json
{
  "api_key": "YOUR_IG_API_KEY",
  "username": "YOUR_DEMO_USERNAME",
  "password": "YOUR_DEMO_PASSWORD",
  "account_id": "YOUR_DEMO_ACCOUNT_ID",
  "base_url": "https://demo-api.ig.com"
}
```

### 2. Trading Parameters
Adjust `config/trading_parameters.json` for your risk preferences:

```json
{
  "starting_balance": 10000.0,
  "max_position_size": 1000.0,
  "max_risk_per_trade": 0.02,
  "max_positions": 10,
  "max_positions_per_symbol": 1,
  "min_confidence_threshold": 0.6
}
```

### 3. Deploy
```bash
cd ig_markets_paper_trading
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## Integration with Main System

The paper trading system integrates with your existing prediction system through:

1. **Database Connection**: Reads predictions from `data/trading_predictions.db`
2. **Symbol Mapping**: Maps ASX symbols to IG Markets EPICs
3. **Exit Strategy**: Uses Phase 4 exit strategy engine
4. **Performance Feedback**: Writes results back to main performance database

## Position Management Rules

### 1. One Position Per Symbol
- Only one open position allowed per symbol (e.g., CBA.AX)
- New signals for symbols with open positions are ignored
- Positions must be closed before new trades can be opened

### 2. Fund Management
- Checks available balance before each trade
- Position size calculated based on confidence and available funds
- Maximum risk per trade enforced (default: 2% of account)
- Total position exposure limited to account balance

### 3. Risk Controls
- Stop loss at -2% per position
- Profit target at configurable percentage
- Maximum drawdown protection
- Position timeout after configurable days

## Usage

### Manual Execution
```bash
# Run paper trading cycle
python scripts/run_paper_trader.py

# Generate performance report
python scripts/performance_report.py

# Run tests
python -m pytest tests/
```

### Automated Execution (Cron)
```bash
# Add to crontab for automated execution every 2 hours during market hours
0 */2 9-16 * 1-5 cd /path/to/ig_markets_paper_trading && python scripts/run_paper_trader.py
```

## Monitoring and Logging

### Log Files
- `logs/paper_trading.log`: All trading activity
- `logs/ig_markets_api.log`: API calls and responses
- `logs/performance.log`: Daily performance summaries

### Performance Metrics
- Total P&L
- Win rate percentage
- Average return per trade
- Maximum drawdown
- Sharpe ratio
- Number of trades per symbol

## Database Schema

The system uses SQLite with the following tables:

```sql
-- Account balance tracking
CREATE TABLE account_balance (
    date TEXT PRIMARY KEY,
    balance REAL NOT NULL,
    available_funds REAL NOT NULL,
    used_funds REAL NOT NULL
);

-- Position tracking
CREATE TABLE positions (
    position_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    epic TEXT NOT NULL,
    action TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    entry_time DATETIME NOT NULL,
    confidence REAL NOT NULL,
    status TEXT DEFAULT 'OPEN',
    exit_price REAL,
    exit_time DATETIME,
    exit_reason TEXT,
    profit_loss REAL,
    profit_loss_pct REAL
);

-- Trading activity log
CREATE TABLE trade_log (
    log_id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    action TEXT NOT NULL,
    symbol TEXT,
    details TEXT,
    result TEXT
);
```

## API Integration Details

### IG Markets API Endpoints Used
- `POST /gateway/deal/session` - Authentication
- `GET /gateway/deal/markets/{epic}` - Market data
- `GET /gateway/deal/accounts` - Account information
- `POST /gateway/deal/positions/otc` - Position management (demo only)

### Rate Limiting
- Demo account: ~30 requests per hour
- Automatic backoff on 403 errors
- Request queuing to prevent overload

## Testing

### Unit Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Test specific components
python -m pytest tests/test_position_manager.py -v
python -m pytest tests/test_paper_trader.py -v
```

### Integration Tests
```bash
# Test IG Markets connection
python tests/test_ig_connection.py

# Test end-to-end workflow
python tests/test_full_workflow.py
```

## Performance Expectations

### Typical Metrics
- **Execution Time**: ~2-5 seconds per trading cycle
- **Memory Usage**: ~50-100MB during operation
- **API Calls**: ~10-20 per execution cycle
- **Database Size**: ~1MB per 1000 trades

### Expected Performance
- **Win Rate**: Dependent on prediction accuracy
- **Maximum Drawdown**: Limited by risk controls (~10-15%)
- **Position Turnover**: ~2-5 trades per day
- **Risk per Trade**: Limited to 2% of account balance

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check IG Markets credentials in config
   - Verify demo account is active
   - Check API key permissions

2. **Position Limits**
   - Review position management rules
   - Check available funds
   - Verify symbol mappings

3. **Performance Issues**
   - Monitor API rate limits
   - Check database connection
   - Review log files for errors

### Debug Mode
```bash
# Enable debug logging
export IG_PAPER_TRADING_DEBUG=1
python scripts/run_paper_trader.py
```

## Removal Guide

If you want to remove the IG Markets paper trading system:

### 1. Stop Automated Execution
```bash
# Remove from crontab
crontab -e
# Delete the IG Markets paper trading line
```

### 2. Remove Integration Points
```bash
# Remove any imports in main system
grep -r "ig_markets_paper_trading" /path/to/main/system/
# Remove or comment out the imports
```

### 3. Clean Up Files
```bash
# Remove the entire directory
rm -rf ig_markets_paper_trading/

# Remove any symlinks or references
find /path/to/main/system/ -name "*ig_markets*" -type l -delete
```

### 4. Database Cleanup
```bash
# Remove paper trading database (optional)
rm -f data/paper_trading.db

# Remove references from main database (if any)
sqlite3 data/trading_predictions.db "DELETE FROM config WHERE key LIKE '%ig_markets%';"
```

### 5. Configuration Cleanup
```bash
# Remove environment variables
unset IG_MARKETS_API_KEY
unset IG_MARKETS_USERNAME
unset IG_MARKETS_PASSWORD

# Remove from .env file
sed -i '/IG_MARKETS/d' .env
```

## Support and Maintenance

### Regular Maintenance
- Monitor log files weekly
- Review performance metrics monthly
- Update IG Markets credentials as needed
- Archive old trade data quarterly

### Updates
- Check for IG Markets API changes
- Update symbol mappings as needed
- Review and adjust risk parameters
- Backup trade history before updates

## Security Considerations

- Uses demo account only (no real money at risk)
- API credentials stored in local config files
- No sensitive data transmitted unencrypted
- All trades are paper trades only
- Regular credential rotation recommended

## Integration Points with Main System

### Input Sources
- Reads predictions from: `data/trading_predictions.db`
- Uses Phase 4 exit strategy: `phase4_development/exit_strategy/`
- Symbol mappings: `config/symbol_mappings.json`

### Output Destinations
- Writes trades to: `data/paper_trading.db`
- Performance metrics: `data/performance_summary.json`
- Activity logs: `logs/paper_trading.log`

This self-contained system can be easily integrated, monitored, and removed without affecting the main trading system.
