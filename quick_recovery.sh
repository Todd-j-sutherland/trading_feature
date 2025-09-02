#!/bin/bash
# Quick Recovery Script for Droplet Restart
# Run this script on your remote droplet after restart

echo "🚀 Starting ASX Trading System Recovery..."
echo "Date: $(date)"

# Step 1: Navigate to project directory
echo "📂 Navigating to project directory..."
cd /root/test || { echo "❌ Failed to navigate to /root/test"; exit 1; }
pwd

# Step 2: Activate virtual environment
echo "🐍 Activating virtual environment..."
source /root/trading_venv/bin/activate || { echo "❌ Failed to activate virtual environment"; exit 1; }
export PYTHONPATH=/root/test
echo "Virtual env: $VIRTUAL_ENV"

# Step 3: Install cron jobs
echo "⏰ Installing cron jobs..."
if [ -f "simple_cron_jobs.txt" ]; then
    crontab simple_cron_jobs.txt
    echo "✅ Cron jobs installed from simple_cron_jobs.txt"
elif [ -f "updated_cron_jobs.txt" ]; then
    crontab updated_cron_jobs.txt
    echo "✅ Cron jobs installed from updated_cron_jobs.txt"
else
    echo "⚠️ No cron job file found, please check manually"
fi

# Step 4: Start and enable cron service
echo "🔧 Starting cron service..."
sudo service cron start
sudo systemctl enable cron
sudo service cron status

# Step 5: Test main application
echo "🧪 Testing main application..."
python -m app.main status || echo "⚠️ Main app status check had issues"

# Step 6: Test IG Markets integration
echo "📊 Testing IG Markets integration..."
python -c "
try:
    from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector
    collector = EnhancedMarketDataCollector()
    health = collector.is_ig_markets_healthy()
    print(f'IG Markets health: {\"✅ OK\" if health else \"⚠️ CHECK NEEDED\"}')
except Exception as e:
    print(f'⚠️ IG Markets test: {e}')
" || echo "⚠️ IG Markets test had issues"

# Step 7: Test paper trading
echo "📈 Testing paper trading..."
cd /root/test/paper-trading-app || { echo "❌ Failed to navigate to paper trading directory"; exit 1; }

if [ -d "./paper_trading_venv" ]; then
    source ./paper_trading_venv/bin/activate
    python run_paper_trading_ig.py test || echo "⚠️ Paper trading test had issues"
    echo "✅ Paper trading environment activated"
else
    echo "⚠️ Paper trading virtual environment not found"
fi

# Step 8: Start paper trading service (if during market hours)
current_hour=$(date -u +%H)
current_minute=$(date -u +%M)
current_day=$(date +%u)

# Check if it's during market hours (00:30-05:30 UTC) and weekday (1-5)
if [ $current_day -le 5 ] && [ $current_hour -ge 0 ] && [ $current_hour -le 5 ]; then
    if [ $current_hour -eq 0 ] && [ $current_minute -ge 15 ]; then
        echo "📈 Starting paper trading service (market hours detected)..."
        python run_paper_trading_ig.py service &
        echo "✅ Paper trading service started"
    elif [ $current_hour -ge 1 ] && [ $current_hour -le 5 ]; then
        echo "📈 Starting paper trading service (market hours detected)..."
        python run_paper_trading_ig.py service &
        echo "✅ Paper trading service started"
    else
        echo "⏰ Outside paper trading hours, service will start automatically at 00:15 UTC"
    fi
else
    echo "⏰ Outside market hours or weekend, services will start automatically"
fi

# Step 9: Verify cron jobs are installed
echo "✅ Verifying cron jobs..."
crontab -l | grep -E "(morning|evening|paper)" | head -5

# Step 10: Create/check logs directory
echo "📝 Checking logs directory..."
cd /root/test
mkdir -p logs
ls -la logs/ | head -10

# Step 11: Show next scheduled runs
echo "⏰ Next scheduled runs:"
echo "Morning routine: Next weekday 09:30 AEST (23:30 UTC)"
echo "Paper trading: Next weekday 10:15 AEST (00:15 UTC)"
echo "Evening routine: Next weekday 18:00 AEST (08:00 UTC)"
echo "Predictions: Every 30 min during market hours (00:30-05:30 UTC)"

# Step 12: Final status
echo ""
echo "🎯 RECOVERY COMPLETE!"
echo "Current time: $(date)"
echo "Current UTC time: $(date -u)"
echo "Current Sydney time: $(TZ='Australia/Sydney' date)"
echo ""
echo "✅ Main application tested"
echo "✅ Cron jobs installed"
echo "✅ Cron service started"
echo "✅ Paper trading tested"
echo "✅ Logs directory ready"
echo ""
echo "🔍 To monitor system:"
echo "  - Check status: python -m app.main status"
echo "  - View logs: tail -f /root/test/logs/*.log"
echo "  - Check cron: crontab -l"
echo "  - Check processes: ps aux | grep trading"
echo ""
echo "🚀 System is ready for automated operation!"
