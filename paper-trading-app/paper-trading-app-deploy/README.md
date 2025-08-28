# Paper Trading Application

A comprehensive paper trading application for testing trading strategies without risking real money. Built with Streamlit for the dashboard interface and SQLAlchemy for data management.

## Features

### 📊 Portfolio Management
- Real-time portfolio tracking with live market data
- Position management with P&L calculations
- Cash balance monitoring
- Portfolio allocation visualization

### 🎯 Trading Interface
- Manual trade execution (Market Buy/Sell orders)
- Quick actions for position management
- Live price monitoring for selected symbols
- Commission and slippage simulation

### 📈 Performance Analytics
- Comprehensive trade history analysis
- Win rate and P&L tracking
- Strategy performance comparison
- Cumulative performance charts

### 🤖 Strategy Integration
- Interface for automated trading strategies
- Strategy signal testing
- Performance tracking by strategy
- Confidence scoring system

### 🛡️ Risk Management
- Position size limits (20% max per position)
- Daily loss limits (5% of portfolio)
- Cash availability validation
- Commission and slippage calculations

## Supported Markets

### ASX (Australian Securities Exchange)
- Major banks: CBA.AX, ANZ.AX, WBC.AX, NAB.AX
- Resources: BHP.AX, RIO.AX, FMG.AX
- Technology: XRO.AX, APT.AX
- REITs: SCG.AX, GMG.AX

### US Markets
- Technology: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA
- Finance: JPM, BAC, GS, MS
- Healthcare: JNJ, PFE, UNH
- And more...

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Internet connection for market data

### Quick Start
1. Navigate to the paper-trading-app directory
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python run.py
   ```

### Manual Setup
1. Install required packages:
   ```bash
   pip install streamlit>=1.28.0 sqlalchemy>=2.0.0 pandas>=2.0.0 yfinance>=0.2.0 plotly>=5.15.0
   ```

2. Initialize the database:
   ```bash
   python database/init_db.py
   ```

3. Start the dashboard:
   ```bash
   streamlit run dashboard.py
   ```

## Configuration

Edit `config.py` to customize:

### Trading Parameters
- Initial balance: $100,000 (default)
- Commission rate: 0.25%
- Minimum commission: $5.00
- Maximum commission: $25.00
- Slippage simulation: 0.1%

### Risk Management
- Maximum position size: 20% of portfolio
- Daily loss limit: 5% of portfolio
- Concentration limits: Prevent over-exposure

### Market Configuration
- Trading hours simulation
- Supported symbols
- Data refresh intervals

## Database Schema

### Tables
- **accounts**: Portfolio balances and summary data
- **trades**: Individual trade records with P&L
- **positions**: Current holdings and market values
- **metrics**: Daily performance analytics
- **strategies**: Strategy configurations and performance
- **price_data**: Historical price data cache
- **order_history**: Order tracking and management

## Usage Guide

### 1. Portfolio Overview
- View current positions and cash balance
- Monitor real-time portfolio performance
- Analyze portfolio allocation with interactive charts

### 2. Manual Trading
- Select symbol from supported markets
- Choose BUY or SELL action
- Specify quantity and optional notes
- Execute trades with realistic commission/slippage

### 3. Strategy Testing
- Test trading signals programmatically
- Compare strategy performance
- Track confidence levels and reasoning

### 4. Performance Analysis
- Review historical trade performance
- Analyze win rates and profit factors
- Export trade data for external analysis

## Strategy Integration

### Signal Format
```python
signal = {
    'symbol': 'AAPL',
    'action': 'BUY',  # or 'SELL'
    'quantity': 100,
    'strategy': 'ML_Strategy_v1',
    'confidence': 0.85,  # 0.0 to 1.0
    'reasoning': 'Strong buy signal from ML model'
}
```

### Integration Example
```python
from trading.engine import PaperTradingEngine, StrategyInterface
from database.models import get_session, create_database

# Initialize
engine = create_database()
session = get_session(engine)
trading_engine = PaperTradingEngine(session, account_id=1)
strategy_interface = StrategyInterface(trading_engine)

# Execute signal
result = strategy_interface.execute_strategy_signal(signal)
if result.success:
    print(f"Trade executed: {result.message}")
else:
    print(f"Trade failed: {result.message}")
```

## Market Data

- **Source**: Yahoo Finance (yfinance)
- **Update Frequency**: 5-minute cache for performance
- **Coverage**: ASX and US major exchanges
- **Data Points**: Current price, volume, historical data

## Risk Controls

### Position Limits
- Maximum 20% of portfolio in single position
- Automatic validation before trade execution
- Cash availability checks

### Daily Limits
- 5% daily loss limit
- Automatic trading halt if exceeded
- Reset at market open

### Execution Controls
- Commission simulation (0.25% + min/max)
- Slippage simulation (0.1% base rate)
- Market hours validation

## Performance Metrics

### Portfolio Level
- Total return (absolute and percentage)
- Sharpe ratio calculation
- Maximum drawdown tracking
- Volatility measurement

### Trade Level
- Win rate calculation
- Average win/loss amounts
- Profit factor analysis
- Strategy attribution

## Data Export

### Trade History
- CSV export functionality
- Customizable date ranges
- Filter by strategy or symbol
- Include all trade details and P&L

### Portfolio Analytics
- Performance charts (PNG/HTML)
- Position summaries
- Risk metrics reports

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   python database/init_db.py
   ```

2. **Market Data Issues**
   - Check internet connection
   - Verify symbol format (e.g., CBA.AX for ASX)
   - Some symbols may have trading halts

3. **Performance Issues**
   - Clear price cache: restart application
   - Reduce number of monitored symbols
   - Check system resources

### Logs and Debugging
- Application logs in console output
- Database queries logged at debug level
- Network errors captured and displayed

## Extending the Application

### Adding New Markets
1. Update `SUPPORTED_SYMBOLS` in config.py
2. Ensure symbol format compatible with yfinance
3. Test price data availability

### Custom Strategies
1. Implement strategy logic
2. Use StrategyInterface for execution
3. Track performance in database

### Additional Analytics
1. Extend Metrics model for new calculations
2. Add visualization in dashboard.py
3. Update performance analytics functions

## Security Notes

- This is a paper trading application - no real money involved
- Market data is for simulation purposes only
- No authentication system (suitable for local use)
- Database contains only simulated trading data

## Support

For issues or questions:
1. Check this README for common solutions
2. Review configuration settings
3. Verify all dependencies are installed
4. Check console output for error messages
