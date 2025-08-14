# 🚀 Quick Start Guide - ML Trading System

## LATEST UPDATE: ML Trading System Now Operational! ✅

### Essential Setup
```bash
# Activate environment
source .venv312/bin/activate
cd /Users/toddsutherland/Repos/trading_analysis

# Set Python path (REQUIRED for imports to work)
export PYTHONPATH=/Users/toddsutherland/Repos/trading_analysis
```

### 🎯 NEW ML Trading Commands
```bash
# Set Python path first (run once per terminal session)
export PYTHONPATH=/Users/toddsutherland/Repos/trading_analysis

# Get ML scores for all banks
python app/main.py ml-scores

# Analyze specific bank before trading
python app/main.py pre-trade --symbol QBE.AX

# Launch enhanced trading dashboard
python app/main.py enhanced-dashboard

# Run complete ML analysis
python app/main.py analyze

# Other useful commands
python app/main.py news              # News sentiment analysis
python app/main.py economic          # Economic regime analysis
python app/main.py divergence        # Sector divergence analysis
python app/main.py dashboard         # Basic dashboard
```

## 🎯 What Was Fixed

### ✅ Major Error Fixes (Just Completed)
1. **'get_all_news' method missing** ➜ Added news aggregation from multiple sources
2. **'transformer_models' attribute error** ➜ Fixed reference to use 'transformer_pipelines'
3. **'reddit_sentiment' undefined** ➜ Added Reddit sentiment analysis call
4. **'feature_engineer' missing** ➜ Added ML trading component initialization

### ✅ System Status: FULLY OPERATIONAL

## 📊 Example ML Analysis Output

```
🔍 Pre-Trade ML Analysis for QBE.AX
ML Score: 42.9/100
Recommendation: HOLD
Risk Level: MEDIUM
Position Size: 4.5%

📊 Component Scores:
   Sentiment Strength: 0.7
   Sentiment Confidence: 59.0
   Economic Context: 81.3
   Divergence Score: 50.0
   Technical Momentum: 50.0
   ML Prediction Confidence: 25.0
```

## 🏦 Supported Banks
- CBA.AX (Commonwealth Bank)
- WBC.AX (Westpac)
- ANZ.AX (ANZ Bank)
- NAB.AX (National Australia Bank)
- MQG.AX (Macquarie Group)
- SUN.AX (Suncorp)
- QBE.AX (QBE Insurance)

## ⚡ Performance Tips
- Set `SKIP_TRANSFORMERS=1` to reduce memory usage
- System caches results for 30 minutes
- Use Python 3.11/3.12 for best transformer support

## 🔧 Environment Variables (Optional)
```bash
export SKIP_TRANSFORMERS=1          # Skip AI models (faster startup)
export ALPACA_API_KEY=your_key      # For paper trading
export ALPACA_SECRET_KEY=your_secret
```

## 📋 Complete Command Reference

**IMPORTANT**: Set Python path first: `export PYTHONPATH=/Users/toddsutherland/Repos/trading_analysis`

| Command | Purpose | Example |
|---------|---------|---------|
| `ml-scores` | Get ML scores for all banks | `python app/main.py ml-scores` |
| `pre-trade` | Pre-trade analysis for symbol | `python app/main.py pre-trade --symbol QBE.AX` |
| `enhanced-dashboard` | Launch enhanced ML dashboard | `python app/main.py enhanced-dashboard` |
| `dashboard` | Launch basic dashboard | `python app/main.py dashboard` |
| `news` | News sentiment analysis | `python app/main.py news` |
| `economic` | Economic regime analysis | `python app/main.py economic` |
| `divergence` | Sector divergence analysis | `python app/main.py divergence` |
| `morning` | Morning trading routine | `python app/main.py morning` |
| `evening` | Evening trading summary | `python app/main.py evening` |
| `status` | System health check | `python app/main.py status` |

## 📈 NEW ML System Features
- ✅ Multi-source news aggregation
- ✅ AI-powered sentiment analysis
- ✅ ML trading score calculation
- ✅ Economic regime detection
- ✅ Sector divergence analysis
- ✅ Pre-trade risk assessment
- ✅ Alpaca paper trading integration
- ✅ Enhanced trading dashboard
- ✅ **NEW: Buy Positions Deep Analysis**
  - Entry and exit reasoning for all BUY signals
  - Real-time performance tracking for open positions
  - Technical indicator analysis at entry point
  - Performance breakdown by RSI and sentiment ranges

## 🚨 Troubleshooting

### "No module named 'app'" Error
**Solution**: Set the Python path in your terminal:
```bash
source .venv312/bin/activate
export PYTHONPATH=/Users/toddsutherland/Repos/trading_analysis
python app/main.py status  # Test it works
```

### "delta_color only accepts: 'normal', 'inverse', or 'off'" Error
**Status**: ✅ FIXED in enhanced dashboard
- Fixed Streamlit delta_color parameter usage in economic analysis section
- Dashboard now uses correct color values for metrics

### Quick Setup Script
Create this one-time setup script:
```bash
# Create a setup.sh file
cat > setup.sh << 'EOF'
#!/bin/bash
source .venv312/bin/activate
export PYTHONPATH=/Users/toddsutherland/Repos/trading_analysis
echo "✅ Environment ready for ML trading!"
echo "Now run: python app/main.py [command]"
EOF

chmod +x setup.sh
```

Then just run: `./setup.sh` before using any commands.

### Other Issues
- **Memory issues**: Add `SKIP_TRANSFORMERS=1`
- **Slow startup**: Transformer models download ~268MB first time
- **Network errors**: News scraping may occasionally fail (system continues)
- **Port 8501 in use**: Dashboard is already running in another terminal

Ready to trade with ML! 🚀

## 💰 NEW: Buy Positions Deep Analysis

The enhanced ML dashboard now includes comprehensive analysis of BUY positions:

### 🎯 Key Features

**📊 Position Performance Tracking**
- Real-time unrealized gains/losses for open positions
- Entry and exit price analysis
- Win rate and average return calculations

**🧠 Entry Decision Reasoning**
- Why each BUY signal was generated:
  - Sentiment analysis scores and confidence levels
  - Technical indicators (RSI, MACD) at time of entry
  - News volume and market activity
  - ML model confidence scores
- Example reasoning: "Strong positive sentiment (0.156); Oversold RSI (28.4) - potential bounce; High news activity (45 articles)"

**🎯 Exit Analysis**
- For closed positions: Actual profit/loss and exit reasoning
- For open positions: Current unrealized P&L with live price updates
- Performance breakdown by technical indicator ranges

**📈 Performance Analytics**
- Best and worst performing BUY signals
- Success rates by RSI ranges (Oversold, Normal, Overbought)
- Performance by sentiment levels (Negative, Neutral, Positive)

### 🖥️ Dashboard Access

Navigate to **"Buy Positions Analysis"** page in the ML dashboard for:
- Complete position history with entry/exit reasoning
- Live tracking of open positions
- Performance analysis by technical indicators
- Position-by-position detailed breakdown

**Dashboard URL:** `http://localhost:8502` (or your server IP:8502)

---

## 📋 Legacy Prerequisites (For Reference)

- **Python 3.8+** installed on your system
- **Git** for cloning the repository
- **Virtual environment** support (recommended)

## ⚡ 5-Minute Setup

### 1. Clone & Setup
```bash
# Clone the repository
git clone https://github.com/your-username/trading_analysis.git
cd trading_analysis

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
```

### 2. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### 3. Test Installation
```bash
# Check if everything is working
python -m app.main status
```

You should see output like:
```
📊 QUICK STATUS CHECK
Trading Analysis System Status: ✅ Operational
✅ Enhanced Sentiment Integration: Available
✅ Core modules: Loaded successfully
✅ Dashboard: Ready to launch
```

## 🎯 First Commands

### Check System Status
```bash
python -m app.main status
```
- Validates all components are working
- Shows system health
- Confirms data availability

### Morning Analysis
```bash
python -m app.main morning --dry-run
```
- Runs morning market analysis
- Collects latest news sentiment
- Generates trading insights
- `--dry-run` flag shows what would happen without making changes

### Evening Summary
```bash
python -m app.main evening --dry-run
```
- Daily performance summary
- Market closure analysis
- Sentiment trend analysis

### Launch Dashboard
```bash
python -m app.main dashboard
```
- Opens interactive web interface
- Real-time market visualization
- Professional trading dashboard
- Access at `http://localhost:8501`

## 📊 Dashboard Tour

When you launch the dashboard, you'll see:

1. **📈 Market Overview**
   - Real-time sentiment scores for major ASX banks
   - Confidence metrics and trend indicators
   - Market regime analysis

2. **🏦 Bank Analysis**
   - Detailed analysis for CBA, WBC, ANZ, NAB, MQG
   - Historical sentiment trends
   - Technical indicator integration

3. **📰 News Sentiment**
   - Real-time news analysis
   - Sentiment scoring with confidence levels
   - Source attribution and timestamps

4. **📊 Technical Charts**
   - Interactive Plotly visualizations
   - Sentiment correlation analysis
   - Historical trend analysis

## 🧪 Validate Installation

Run the test suite to ensure everything is working:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v        # Unit tests (19 tests)
python -m pytest tests/integration/ -v # Integration tests (44 tests)
```

Expected output:
```
======================== 63 passed in 2.45s ========================
```

## 🔧 Configuration

### Environment Setup (Optional)
Create a `.env` file for custom configuration:
```bash
# Copy example configuration
cp .env.example .env

# Edit with your preferences
nano .env
```

Common settings:
```env
# Logging level
LOG_LEVEL=INFO

# Data directory
DATA_DIR=data

# Dashboard port
DASHBOARD_PORT=8501
```

### Data Initialization
The system will automatically create necessary directories:
- `data/` - Market and sentiment data storage
- `logs/` - Application logging
- `reports/` - Generated analysis reports

## 💡 Common Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `status` | System health check | `python -m app.main status` |
| `morning` | Morning briefing | `python -m app.main morning` |
| `evening` | Evening summary | `python -m app.main evening` |
| `dashboard` | Web interface | `python -m app.main dashboard` |

## 🎯 Next Steps

### Explore the Dashboard
1. Launch dashboard: `python -m app.main dashboard`
2. Navigate to different sections
3. Interact with charts and visualizations
4. Review sentiment analysis results

### Customize Analysis
1. Check `app/config/settings.py` for configuration options
2. Modify sentiment analysis parameters in `app/config/ml_config.yaml`
3. Add new data sources in `app/core/data/collectors/`

### Scheduled Operations
Set up daily automation:
```bash
# Add to crontab for daily automation
# Morning analysis at 9:00 AM
0 9 * * * cd /path/to/trading_analysis && source venv/bin/activate && python -m app.main morning

# Evening summary at 6:00 PM
0 18 * * * cd /path/to/trading_analysis && source venv/bin/activate && python -m app.main evening
```

## 🆘 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Port Already in Use (Dashboard)**
```bash
# Use different port
python -m streamlit run app/dashboard/main.py --server.port 8502
```

**Missing Data Directories**
```bash
# The system creates these automatically, but you can create manually:
mkdir -p data logs reports
```

**Permission Issues**
```bash
# Ensure proper permissions
chmod +x venv/bin/activate
```

### Getting Help

1. **Check logs**: Look in `logs/` directory for error details
2. **Run tests**: `python -m pytest tests/ -v` to identify issues
3. **Verbose mode**: Add `--verbose` flag to commands for detailed output
4. **System status**: Always start with `python -m app.main status`

## 🔗 Key Files

- **Main Entry**: `app/main.py` - CLI interface
- **Configuration**: `app/config/settings.py` - System settings
- **Dashboard**: `app/dashboard/main.py` - Web interface
- **Core Logic**: `app/core/sentiment/` - Analysis engine
- **Tests**: `tests/` - Validation suite

## ✅ Success Indicators

You'll know everything is working when:
- ✅ `python -m app.main status` shows all green checkmarks
- ✅ Dashboard loads without errors at `http://localhost:8501`
- ✅ Morning/evening commands complete successfully
- ✅ Test suite passes: `python -m pytest tests/ -v`

**🎉 You're ready to start trading with AI-powered insights!**
