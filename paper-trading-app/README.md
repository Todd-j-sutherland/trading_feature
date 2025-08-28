# Paper Trading Application

A comprehensive paper trading application for testing trading strategies without risking real money. Features multiple dashboards, automated trading services, and advanced backtesting capabilities using real historical data.

## 🎯 System Overview

The Paper Trading Application consists of three main components:

1. **📊 Interactive Dashboards** - Real-time portfolio management and analytics
2. **🤖 Automated Trading Services** - Background services that execute trades based on ML predictions
3. **🔬 Backtesting Engine** - Historical strategy validation using actual timing data

## 📊 Dashboard Components

### Main Dashboard (`dashboard.py`)
The primary Streamlit interface for portfolio management and manual trading.

**Features:**
- Real-time portfolio tracking with live market data
- Manual trade execution (Market Buy/Sell orders)
- Position management with P&L calculations
- Cash balance monitoring and allocation visualization
- Live price monitoring for supported symbols
- Commission and slippage simulation

**Usage:**
```bash
streamlit run dashboard.py
```

**Note:** For automated ASX trading with ML integration, use the Enhanced Dashboard Component instead (see below).

### Enhanced Dashboard Component (`paper_trading_dashboard_component.py`)
Advanced dashboard integration for automated trading management.

**Features:**
- 🤖 Live Paper Trading System controls
- ⚙️ Real-time configuration updates
- 🚦 Service status monitoring and controls
- 💼 Portfolio overview with active positions
- 📈 Recent trades analysis
- 📊 Active positions with current P&L
- 📚 Strategy explanation and documentation

**Key Capabilities:**
- **Configuration Management**: Update profit targets, hold times, position sizes in real-time
- **Service Control**: Start/stop/monitor automated trading services
- **Live Monitoring**: Track active positions and their current profit/loss
- **Performance Analytics**: View win rates, trade statistics, and cumulative profits

**Integration:**
```python
# Add to your main dashboard
from paper_trading_dashboard_component import paper_trading_dashboard_section
paper_trading_dashboard_section()
```

## 🤖 Automated Trading Services

### Enhanced Paper Trading Service (`enhanced_paper_trading_service.py`)
Advanced automated trading service implementing the backtesting strategy.

**Strategy Features:**
- ✅ **Long Positions Only**: Processes BUY signals only (no short selling)
- ✅ **One Position Per Symbol**: Maximum one open position per stock symbol
- 🎯 **Profit Target Monitoring**: Configurable profit target (default $5)
- ⏰ **Continuous Monitoring**: Check positions every minute for exit conditions
- 📡 **Real-time Data**: Yahoo Finance integration for live pricing
- 🛡️ **Risk Management**: Maximum hold time limits (default 24 hours)
- 🔄 **Live Configuration**: Update settings without restarting service

**Exit Conditions:**
1. **Profit Target Reached**: Exit when profit ≥ configured target
2. **Maximum Hold Time**: Exit after configured time limit
3. **Real-time Monitoring**: Continuous price checking every minute

### Legacy Services
- `paper_trading_background_service.py` - Original background service
- `start_paper_trading_service.py` - Service launcher with test commands

## 🛠️ Service Management

### Enhanced Service Manager (`enhanced_service_manager.sh`)
Comprehensive service management with enhanced monitoring.

**Commands:**
```bash
./enhanced_service_manager.sh start      # Start enhanced service
./enhanced_service_manager.sh stop       # Stop service
./enhanced_service_manager.sh status     # Check status & positions with live prices
./enhanced_service_manager.sh portfolio  # Detailed portfolio view with current P&L
./enhanced_service_manager.sh config     # View/update configuration
./enhanced_service_manager.sh logs       # Live service logs
```

**Enhanced Position Display:**
The status and portfolio commands now show real-time market data:
- **Current Price**: Live market price from Yahoo Finance
- **Current Profit**: Real-time P&L calculation based on current prices
- **Entry vs Current**: Easy comparison of entry price vs current market price
- **Auto-fallback**: Gracefully falls back to basic view if live data unavailable

**Status Example:**
```
✅ Enhanced service is running
📊 Process: 79320

💼 Active Positions:
symbol   entry_price current_price shares investment current_profit hold_min position_type
------   ----------- ------------- ------ ---------- -------------- -------- -------------
MQG.AX   224.91      226.45        44     9896.04    +67.76         44       LONG         
CBA.AX   118.23      117.85        84     9896.32    -31.88         12       LONG         

🎯 Current Configuration:
profit_target           5.0
max_hold_time_minutes   1440.0
position_size           10000.0
check_interval_seconds  60.0
commission_rate         0.0
```

### Legacy Service Manager (`service_manager.sh`)
Original service manager for basic operations.

### Enhanced Position Monitoring

The system now provides **live position monitoring** with real-time market data:

**Live Status Display:**
```bash
./enhanced_service_manager.sh status
```
Shows active positions with:
- **Current Price**: Live market price from Yahoo Finance
- **Current Profit**: Real-time P&L (+$67.76 or -$31.88)
- **Entry Price**: Original purchase price for comparison
- **Hold Time**: Minutes since position opened

**Example Output:**
```
� Active Positions:
symbol   entry_price current_price shares investment current_profit hold_min position_type
------   ----------- ------------- ------ ---------- -------------- -------- -------------
MQG.AX   224.91      226.45        44     9896.04    +67.76         44       LONG         
CBA.AX   118.23      117.85        84     9896.32    -31.88         12       LONG         
```

**Features:**
- ✅ **Real-time Updates**: Live prices fetched from Yahoo Finance
- ✅ **Instant P&L**: Current profit/loss calculated in real-time
- ✅ **Color Coding**: Positive profits shown with + prefix
- ✅ **Fallback Protection**: Gracefully handles network issues
- ✅ **Multi-symbol**: Supports all ASX and US symbols

**Dashboard Integration:**
The Streamlit dashboard also includes live position monitoring with the same real-time calculations.

## 🔬 Configuration Management

### Real-time Configuration Updates

**Via Dashboard:**
Use the Enhanced Dashboard Component to update settings through the web interface.

**Via Database:**
```sql
-- Update profit target to $10
UPDATE trading_config SET value = 10.0 WHERE key = 'profit_target';

-- Update check interval to 30 seconds  
UPDATE trading_config SET value = 30 WHERE key = 'check_interval_seconds';

-- Update position size to $15,000
UPDATE trading_config SET value = 15000 WHERE key = 'position_size';

-- Update max hold time to 2 hours (120 minutes)
UPDATE trading_config SET value = 120 WHERE key = 'max_hold_time_minutes';

-- Set commission to 0.1% (0.001)
UPDATE trading_config SET value = 0.001 WHERE key = 'commission_rate';

-- Set flat $3 commission
UPDATE trading_config SET value = 3.0 WHERE key = 'min_commission';
UPDATE trading_config SET value = 3.0 WHERE key = 'max_commission';
```

**Configuration Parameters:**
- `profit_target`: Target profit per trade (default: $5.00)
- `max_hold_time_minutes`: Maximum hold time (default: 1440 = 24 hours)
- `position_size`: Dollar amount per position (default: $10,000)
- `check_interval_seconds`: Position monitoring frequency (default: 60 seconds)
- `commission_rate`: Commission percentage (default: 0% - configurable via dashboard)
- `min_commission`: Minimum commission per trade (default: $0)
- `max_commission`: Maximum commission per trade (default: $100)

## 📊 Portfolio Management Features

### Real-time Monitoring
- Live position tracking with current market prices
- Continuous P&L calculation and display
- Active position status and hold times
- Portfolio allocation and risk metrics
- Real-time profit/loss updates with live pricing
- Current price vs entry price comparison

### Trade Execution
- Automated BUY signal processing from ML predictions (LONG positions only)
- One position per symbol rule enforcement
- Realistic commission and slippage simulation
- Comprehensive trade logging and history
- **Note**: Currently supports LONG positions only - no short selling

### Performance Analytics
- Trade statistics (win rate, average profit, total return)
- Position-level analytics (hold times, exit reasons)
- Symbol performance comparison
- Cumulative profit tracking

### Risk Management
- Position size limits and validation
- Maximum hold time enforcement
- Cash availability checks
- Commission calculation (configurable: 0% default, adjustable via dashboard)

## Supported Markets

### ASX (Australian Securities Exchange) - Primary Focus
- Major banks: CBA.AX, ANZ.AX, WBC.AX, NAB.AX, MQG.AX
- Resources: BHP.AX, RIO.AX, FMG.AX
- Technology: XRO.AX, APT.AX
- REITs: SCG.AX, GMG.AX

### US Markets (Manual Trading Only)
- Technology: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA
- Finance: JPM, BAC, GS, MS
- Healthcare: JNJ, PFE, UNH
- **Note:** Automated trading service focuses on ASX stocks

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
3. Initialize the database:
   ```bash
   python database/init_db.py
   ```
4. Choose your interface:

**Option A: Main Dashboard (Manual Trading - All Markets)**
```bash
streamlit run dashboard.py
```

**Option B: Enhanced Dashboard (Automated ASX Trading Management)**
```bash
streamlit run paper_trading_dashboard_component.py
```

**Option C: Automated ASX Service Only**
```bash
./enhanced_service_manager.sh start
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

3. Start your preferred interface (see Quick Start options above)

## 🚀 Usage Guide

### Dashboard Usage

#### 1. Main Dashboard Interface
**Access:** `streamlit run dashboard.py`

**Portfolio Overview:**
- View current positions and cash balance
- Monitor real-time portfolio performance  
- Analyze portfolio allocation with interactive charts

**Manual Trading:**
- Select symbol from supported markets
- Choose BUY or SELL action
- Specify quantity and optional notes
- Execute trades with realistic commission/slippage

**Performance Analysis:**
- Review historical trade performance
- Analyze win rates and profit factors
- Export trade data for external analysis

#### 2. Enhanced Dashboard (Automated Trading)
**Access:** `streamlit run paper_trading_dashboard_component.py`

**Trading Configuration:**
- Set profit targets (default $5)
- Configure maximum hold times (default 24 hours)
- Adjust position sizes (default $10,000)
- Update monitoring intervals (default 1 minute)
- Set commission structure (default 0% - fully configurable)
  - Commission rate (percentage of trade value)
  - Minimum commission per trade
  - Maximum commission per trade

**Service Management:**
- Start/stop automated trading services
- Monitor service status and logs
- View real-time portfolio updates

**Live Monitoring:**
- Track active positions with current P&L
- Monitor profit progress toward targets
- View hold times and exit conditions
- Real-time price updates and profit calculations
- Live current price display for all positions

### Automated Trading Service

#### Starting the Enhanced Service
```bash
# Start the service
./enhanced_service_manager.sh start

# Check status
./enhanced_service_manager.sh status

# View portfolio
./enhanced_service_manager.sh portfolio

# Monitor logs
./enhanced_service_manager.sh logs
```

#### Service Behavior
1. **Monitors ML predictions** every 5 minutes for new BUY signals
2. **Checks positions** every 1 minute for exit conditions
3. **Enforces one position per symbol** rule
4. **Exits when profit target reached** or max hold time exceeded
5. **Uses real-time Yahoo Finance** pricing for accurate P&L

#### Configuration Updates
Update settings while service is running:
```bash
# Via database
sqlite3 paper_trading.db "UPDATE trading_config SET value = 10.0 WHERE key = 'profit_target';"

# Via dashboard (recommended)
# Use the Enhanced Dashboard web interface
```

### Strategy Testing

#### Signal Integration
The service automatically processes ML prediction signals:

```python
# Prediction format expected
prediction = {
    'prediction_id': 'MQG.AX_20250828_043624',
    'symbol': 'MQG.AX',
    'predicted_action': 'BUY',
    'action_confidence': 0.846,
    'prediction_timestamp': '2025-08-28T04:36:24.752809',
    'entry_price': 225.45
}
```

#### Manual Strategy Testing
Use the StrategyInterface for programmatic testing:

```python
from trading.engine import PaperTradingEngine, StrategyInterface
from database.models import get_session, create_database

# Initialize
engine = create_database()
session = get_session(engine)
trading_engine = PaperTradingEngine(session, account_id=1)
strategy_interface = StrategyInterface(trading_engine)

# Execute signal
signal = {
    'symbol': 'AAPL',
    'action': 'BUY',
    'quantity': 100,
    'strategy': 'ML_Strategy_v1',
    'confidence': 0.85,
    'reasoning': 'Strong buy signal from ML model'
}

result = strategy_interface.execute_strategy_signal(signal)
```

## 📁 File Structure

### Core Application Files
- `dashboard.py` - Main Streamlit dashboard for manual trading
- `config.py` - Configuration settings and parameters
- `run.py` - Application launcher script
- `requirements.txt` - Python dependencies

### Database Components
- `database/` - Database models and initialization
  - `models.py` - SQLAlchemy ORM models
  - `init_db.py` - Database initialization script
- `paper_trading.db` - SQLite database file

### Trading Engine
- `trading/` - Core trading functionality
  - `engine.py` - Paper trading engine and strategy interface
- `integration/` - External system integrations

### Automated Trading Services
- `enhanced_paper_trading_service.py` - **Enhanced automated service** (recommended)
- `paper_trading_background_service.py` - Legacy background service
- `start_paper_trading_service.py` - Service launcher utility

### Service Management
- `enhanced_service_manager.sh` - **Enhanced service manager** (recommended)
- `service_manager.sh` - Legacy service manager

### Dashboard Components
- `paper_trading_dashboard_component.py` - Enhanced dashboard for automated trading

### Log Files
- `enhanced_paper_trading_service.log` - Enhanced service logs
- `paper_trading_service.log` - Legacy service logs

## 🔧 Configuration

### Main Configuration (`config.py`)
Edit for basic application settings:

```python
# Trading Parameters
DEFAULT_INITIAL_BALANCE = 100000.0  # $100,000 starting capital
DEFAULT_COMMISSION_RATE = 0.0       # 0% commission (configurable via dashboard)
DEFAULT_SLIPPAGE_RATE = 0.001       # 0.1% slippage

# Risk Management  
MAX_POSITION_SIZE_PCT = 0.20        # Maximum 20% per position
DAILY_LOSS_LIMIT_PCT = 0.05         # Maximum 5% daily loss
MAX_PORTFOLIO_CONCENTRATION = 0.30   # Maximum 30% in one sector
```

### Enhanced Service Configuration
Stored in database `trading_config` table, updatable via dashboard or SQL:

```sql
-- View current config
SELECT * FROM trading_config;

-- Update profit target
UPDATE trading_config SET value = 15.0 WHERE key = 'profit_target';
```

**Available Settings:**
- `profit_target` - Target profit per trade ($)
- `max_hold_time_minutes` - Maximum hold time (minutes)
- `position_size` - Dollar amount per position
- `check_interval_seconds` - Position monitoring frequency
- `commission_rate` - Commission percentage (0.0 = 0%, 0.001 = 0.1%, etc.)
- `min_commission` - Minimum commission per trade ($)
- `max_commission` - Maximum commission per trade ($)

## 📊 Database Schema

### Core Tables
- **accounts**: Portfolio balances and summary data
- **trades**: Individual trade records with P&L
- **positions**: Current holdings and market values
- **metrics**: Daily performance analytics
- **strategies**: Strategy configurations and performance

### Enhanced Trading Tables
- **enhanced_positions**: Active positions for automated trading
  - Tracks entry details, target profits, and status
  - One position per symbol enforcement
- **enhanced_trades**: Completed automated trades
  - Detailed P&L, hold times, and exit reasons
  - Commission tracking and performance metrics
- **trading_config**: Live configuration management
  - Real-time updatable settings
  - Dashboard integration support

### Support Tables
- **price_data**: Historical price data cache
- **order_history**: Order tracking and management
- **hold_signals**: Hold signal tracking for analysis

### Database Queries

**View Active Positions:**
```sql
SELECT symbol, entry_price, shares, investment,
       ROUND((julianday('now') - julianday(entry_time)) * 24 * 60, 0) as hold_minutes
FROM enhanced_positions 
WHERE status = 'OPEN';
```

**Trade Performance:**
```sql
SELECT symbol, COUNT(*) as trades, 
       ROUND(AVG(profit), 2) as avg_profit,
       ROUND(SUM(profit), 2) as total_profit,
       ROUND(AVG(hold_time_minutes), 0) as avg_hold_minutes
FROM enhanced_trades 
GROUP BY symbol;
```

**Configuration Management:**
```sql
-- View all settings
SELECT key, value, updated_at FROM trading_config;

-- Update profit target
UPDATE trading_config SET value = 10.0, updated_at = datetime('now') 
WHERE key = 'profit_target';
```

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
- Commission simulation (configurable: 0% default, set via dashboard)
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

4. **Enhanced Service Issues**
   ```bash
   # Check service status
   ./enhanced_service_manager.sh status
   
   # View service logs
   ./enhanced_service_manager.sh logs
   
   # Restart service
   ./enhanced_service_manager.sh stop
   ./enhanced_service_manager.sh start
   ```

5. **Configuration Problems**
   ```bash
   # Check current configuration
   ./enhanced_service_manager.sh config
   
   # Reset to defaults
   sqlite3 paper_trading.db "DELETE FROM trading_config;"
   # Restart service to recreate defaults
   ```

6. **Dashboard Connection Issues**
   - Ensure Streamlit is installed: `pip install streamlit`
   - Check if port 8501 is available
   - Try different browser or incognito mode

### Logs and Debugging

**Enhanced Service Logs:**
```bash
# Real-time logs
tail -f enhanced_paper_trading_service.log

# Recent activity
tail -50 enhanced_paper_trading_service.log
```

**Database Debugging:**
```bash
# Check active positions
sqlite3 paper_trading.db "SELECT * FROM enhanced_positions WHERE status = 'OPEN';"

# Check recent trades
sqlite3 paper_trading.db "SELECT * FROM enhanced_trades ORDER BY exit_time DESC LIMIT 5;"

# Check configuration
sqlite3 paper_trading.db "SELECT * FROM trading_config;"
```

**Service Debugging:**
```bash
# Check if service is running
ps aux | grep enhanced_paper_trading_service

# Check service process
./enhanced_service_manager.sh status

# Test manual execution
python enhanced_paper_trading_service.py
```

## 🔧 Extending the Application

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

## 💡 Usage Examples

### Example 1: Basic Dashboard Setup
```bash
# Quick start for manual trading
cd paper-trading-app
pip install -r requirements.txt
python database/init_db.py
streamlit run dashboard.py
```

### Example 2: Automated Trading Setup
```bash
# Setup automated trading with $10 profit targets
cd paper-trading-app
pip install -r requirements.txt
python database/init_db.py

# Configure for $10 profit target
sqlite3 paper_trading.db "INSERT OR REPLACE INTO trading_config (key, value) VALUES ('profit_target', 10.0);"

# Start enhanced service
./enhanced_service_manager.sh start

# Monitor in separate terminal
./enhanced_service_manager.sh logs
```

### Example 3: Dashboard Integration
```python
# Add enhanced trading dashboard to existing Streamlit app
import streamlit as st
from paper_trading_dashboard_component import paper_trading_dashboard_section

st.title("My Trading Dashboard")

# Add the paper trading section
paper_trading_dashboard_section()

# Your other dashboard components...
```

### Example 4: Configuration Management
```bash
# Update configuration while service is running
./enhanced_service_manager.sh config  # View current settings

# Update profit target to $15
sqlite3 paper_trading.db "UPDATE trading_config SET value = 15.0 WHERE key = 'profit_target';"

# Update max hold time to 4 hours
sqlite3 paper_trading.db "UPDATE trading_config SET value = 240 WHERE key = 'max_hold_time_minutes';"

# Check that changes took effect (within 5 minutes)
./enhanced_service_manager.sh config
```

### Example 5: Portfolio Monitoring
```bash
# Check service status and positions
./enhanced_service_manager.sh status

# Detailed portfolio view
./enhanced_service_manager.sh portfolio

# Watch real-time logs
./enhanced_service_manager.sh logs
```

### Example 6: Performance Analysis
```sql
-- Connect to database for analysis
sqlite3 paper_trading.db

-- View all completed trades
SELECT symbol, entry_time, exit_time, profit, exit_reason 
FROM enhanced_trades 
ORDER BY exit_time DESC;

-- Calculate win rate
SELECT 
    COUNT(*) as total_trades,
    COUNT(CASE WHEN profit > 0 THEN 1 END) as winning_trades,
    ROUND(COUNT(CASE WHEN profit > 0 THEN 1 END) * 100.0 / COUNT(*), 2) as win_rate_pct
FROM enhanced_trades;

-- Average hold time by exit reason
SELECT exit_reason, 
       COUNT(*) as trades,
       ROUND(AVG(hold_time_minutes), 1) as avg_hold_minutes,
       ROUND(AVG(profit), 2) as avg_profit
FROM enhanced_trades 
GROUP BY exit_reason;
```

## Security Notes

- This is a paper trading application - no real money involved
- Market data is for simulation purposes only
- No authentication system (suitable for local use)
- Database contains only simulated trading data

## Support

For issues or questions:
1. Check this README for common solutions
2. Review service logs: `./enhanced_service_manager.sh logs`
3. Check service status: `./enhanced_service_manager.sh status`
4. Review configuration: `./enhanced_service_manager.sh config`
5. Verify all dependencies are installed: `pip install -r requirements.txt`
6. For dashboard issues, check that Streamlit is running
7. For database issues, ensure SQLite is accessible and database file exists

## File References

Key files in this paper-trading-app directory:
- `enhanced_paper_trading_service.py` - Main automated trading service
- `enhanced_service_manager.sh` - Service management script
- `paper_trading_dashboard_component.py` - Dashboard components
- `paper_trading.db` - SQLite database (created automatically)
- `requirements.txt` - Python dependencies
- `README.md` - This documentation file
