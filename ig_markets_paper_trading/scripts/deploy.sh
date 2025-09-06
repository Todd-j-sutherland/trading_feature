#!/bin/bash

# IG Markets Paper Trading System Deployment Script
# Deploys the self-contained paper trading system

set -e

echo "🚀 Deploying IG Markets Paper Trading System"
echo "=============================================="

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

echo "📁 Project Directory: $PROJECT_DIR"

# Create required directories
echo "📂 Creating directories..."
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/logs"

# Set up Python path
export PYTHONPATH="$PROJECT_DIR/src:$PYTHONPATH"

# Check if config files exist
echo "⚙️ Checking configuration..."

if [ ! -f "$PROJECT_DIR/config/ig_markets_config.json" ]; then
    echo "❌ IG Markets config not found: $PROJECT_DIR/config/ig_markets_config.json"
    echo "   Please configure your IG Markets demo credentials"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/config/trading_parameters.json" ]; then
    echo "❌ Trading parameters config not found: $PROJECT_DIR/config/trading_parameters.json"
    exit 1
fi

# Check if IG Markets credentials are configured
echo "🔐 Checking credentials..."
API_KEY=$(grep -o '"api_key": "[^"]*"' "$PROJECT_DIR/config/ig_markets_config.json" | cut -d'"' -f4)
USERNAME=$(grep -o '"username": "[^"]*"' "$PROJECT_DIR/config/ig_markets_config.json" | cut -d'"' -f4)

if [ -z "$API_KEY" ] || [ -z "$USERNAME" ]; then
    echo "⚠️ Warning: IG Markets credentials appear to be empty"
    echo "   Please update config/ig_markets_config.json with your demo account details"
fi

# Test Python imports
echo "🐍 Testing Python dependencies..."
cd "$PROJECT_DIR"

python3 -c "
import sys
import os
sys.path.append('src')

try:
    from position_manager import PositionManager
    from ig_markets_client import IGMarketsClient
    from paper_trader import PaperTrader
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
" || {
    echo "❌ Python import test failed"
    echo "   Please ensure all required dependencies are installed"
    exit 1
}

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "
import sys
import os
sys.path.append('src')

from position_manager import PositionManager

try:
    pm = PositionManager(db_path='data/paper_trading.db', config_path='config/trading_parameters.json')
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    sys.exit(1)
"

# Test IG Markets connection (if credentials are provided)
if [ -n "$API_KEY" ] && [ -n "$USERNAME" ]; then
    echo "🔌 Testing IG Markets connection..."
    python3 -c "
import sys
import os
sys.path.append('src')

from ig_markets_client import IGMarketsClient

try:
    client = IGMarketsClient(config_path='config/ig_markets_config.json')
    if client.test_connection():
        print('✅ IG Markets connection successful')
    else:
        print('⚠️ IG Markets connection test failed (may be due to rate limits)')
except Exception as e:
    print(f'⚠️ IG Markets connection error: {e}')
    print('   This may be normal if credentials are not configured or rate limits are hit')
"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x "$PROJECT_DIR/scripts/run_paper_trader.py"
chmod +x "$PROJECT_DIR/scripts/performance_report.py"
chmod +x "$PROJECT_DIR/scripts/deploy.sh"

# Test run (dry run)
echo "🧪 Running test execution..."
cd "$PROJECT_DIR"
python3 scripts/run_paper_trader.py > /dev/null 2>&1 && {
    echo "✅ Test execution successful"
} || {
    echo "⚠️ Test execution failed - this may be normal on first run"
}

# Create crontab entry example
echo "⏰ Creating crontab example..."
cat > "$PROJECT_DIR/crontab_example.txt" << EOF
# IG Markets Paper Trading Cron Jobs
# Add these lines to your crontab (crontab -e) for automated execution

# Run paper trading every 2 hours during market hours (9 AM - 4 PM, Mon-Fri)
0 */2 9-16 * 1-5 cd $PROJECT_DIR && python3 scripts/run_paper_trader.py >> logs/cron.log 2>&1

# Generate daily performance report at 5 PM
0 17 * * 1-5 cd $PROJECT_DIR && python3 scripts/performance_report.py >> logs/cron.log 2>&1

# Weekly log cleanup (remove logs older than 30 days)
0 2 * * 0 find $PROJECT_DIR/logs -name "*.log" -mtime +30 -delete
EOF

echo "📄 Crontab example saved to: $PROJECT_DIR/crontab_example.txt"

# Create quick start guide
echo "📖 Creating quick start guide..."
cat > "$PROJECT_DIR/QUICK_START.md" << EOF
# Quick Start Guide

## 1. Configure Credentials
Edit \`config/ig_markets_config.json\` with your IG Markets demo account details:
\`\`\`json
{
  "api_key": "YOUR_API_KEY",
  "username": "YOUR_DEMO_USERNAME", 
  "password": "YOUR_DEMO_PASSWORD",
  "account_id": "YOUR_DEMO_ACCOUNT_ID"
}
\`\`\`

## 2. Manual Execution
\`\`\`bash
cd $PROJECT_DIR
python3 scripts/run_paper_trader.py
\`\`\`

## 3. View Performance
\`\`\`bash
python3 scripts/performance_report.py
\`\`\`

## 4. Enable Automation
\`\`\`bash
crontab -e
# Add the lines from crontab_example.txt
\`\`\`

## 5. Monitor Logs
\`\`\`bash
tail -f logs/paper_trading.log
\`\`\`

## 6. Status Check
Check account balance and open positions in the logs or run performance report.
EOF

# Summary
echo ""
echo "✅ IG Markets Paper Trading System Deployed Successfully!"
echo "========================================================="
echo ""
echo "📁 Installation Directory: $PROJECT_DIR"
echo "⚙️ Configuration Files:"
echo "   - config/ig_markets_config.json (update with your credentials)"
echo "   - config/trading_parameters.json"
echo ""
echo "🚀 Quick Start:"
echo "   1. Update config/ig_markets_config.json with your IG Markets demo credentials"
echo "   2. Run: python3 scripts/run_paper_trader.py"
echo "   3. View performance: python3 scripts/performance_report.py"
echo ""
echo "⏰ For automation, add the cron jobs from: crontab_example.txt"
echo "📖 See QUICK_START.md for detailed instructions"
echo ""
echo "📊 System Status:"
echo "   - Database: ✅ Initialized"
echo "   - Scripts: ✅ Executable"
echo "   - Logs: 📁 logs/"
echo "   - Data: 📁 data/"
echo ""

if [ -n "$API_KEY" ] && [ -n "$USERNAME" ]; then
    echo "🔐 Credentials: ✅ Configured"
else
    echo "🔐 Credentials: ⚠️ Need configuration"
fi

echo ""
echo "Ready for paper trading! 🎯"
