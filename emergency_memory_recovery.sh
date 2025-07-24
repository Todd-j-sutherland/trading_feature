#!/bin/bash

# Emergency Memory Recovery Script
# Use this when the system is experiencing severe memory pressure

SERVER="root@170.64.199.151"
SSH_KEY="~/.ssh/id_rsa"

echo "🚨 EMERGENCY MEMORY RECOVERY"
echo "============================="
echo "📅 $(date)"
echo ""

# Function to run remote commands
run_remote() {
    echo "🔧 $1"
    ssh -i "$SSH_KEY" "$SERVER" "$1"
}

echo "📊 Current memory crisis status:"
run_remote "free -h"

echo ""
echo "🛑 Step 1: Stopping all non-essential processes..."
run_remote "
# Stop smart collector
pkill -f 'news_collector --interval' || echo 'Smart collector not running'

# Stop any Python processes from trading system
pkill -f 'python.*app.main' || echo 'No main trading processes running'

# Stop any dashboard processes
pkill -f 'streamlit' || echo 'No dashboard processes running'

echo 'Processes stopped'
"

echo ""
echo "🧹 Step 2: Aggressive memory cleanup..."
run_remote "
# Clear all caches aggressively
sync
echo 3 > /proc/sys/vm/drop_caches

# Clear temporary files
rm -rf /tmp/* 2>/dev/null || true
rm -rf /var/tmp/* 2>/dev/null || true

# Clear Python cache
find /root -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find /root -name '*.pyc' -delete 2>/dev/null || true

# Force garbage collection
python3 -c 'import gc; gc.collect()' 2>/dev/null || true

echo 'Aggressive cleanup complete'
"

echo ""
echo "💾 Step 3: Checking swap utilization..."
run_remote "
if [ -f /swapfile ]; then
    echo 'Swap file exists, checking utilization:'
    swapon --show
    
    # If swap is not being used, try to activate
    if ! swapon --show | grep -q '/swapfile'; then
        echo 'Activating swap...'
        swapon /swapfile || echo 'Failed to activate swap'
    fi
else
    echo 'No swap file found - this is a problem!'
    echo 'Run: ./setup_swap_remote.sh'
fi
"

echo ""
echo "⚡ Step 4: Memory status after recovery:"
run_remote "
free -h
echo ''
echo 'Available memory:'
free -m | awk 'NR==2{printf \"%.0f MB\\n\", \$7}'
"

echo ""
echo "🔄 Step 5: Restart only essential services..."
run_remote "
cd /root/test
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test

# Only restart smart collector in minimal mode
echo 'Restarting smart collector in memory-safe mode...'
export SKIP_TRANSFORMERS=1
nohup python -m app.core.data.collectors.news_collector --interval 60 > /dev/null 2>&1 &

sleep 2
if pgrep -f 'news_collector' > /dev/null; then
    echo '✅ Smart collector restarted successfully'
else
    echo '❌ Failed to restart smart collector'
fi
"

echo ""
echo "📊 Final system status:"
run_remote "
echo 'Memory:'
free -h
echo ''
echo 'Running processes:'
ps aux | grep -E '(python|streamlit)' | grep -v grep | wc -l | awk '{print \$1 \" Python processes\"}'
echo ''
echo 'Smart collector status:'
if pgrep -f 'news_collector' > /dev/null; then
    echo '✅ Running'
else
    echo '❌ Not running'
fi
"

echo ""
echo "✅ Emergency recovery complete!"
echo ""
echo "💡 Next steps:"
echo "  1. Monitor memory: ./advanced_memory_monitor.sh"
echo "  2. If stable, run: ./run_safe_evening.sh"
echo "  3. Consider upgrading droplet if issues persist"
echo ""
echo "⚠️ Prevention:"
echo "  • Use ./run_safe_evening.sh instead of direct evening commands"
echo "  • Monitor memory regularly with automated cron jobs"
echo "  • Consider upgrading to 4GB droplet for better headroom"
