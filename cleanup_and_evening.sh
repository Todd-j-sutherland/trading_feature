#!/bin/bash

# Memory Cleanup Script - Run before evening analysis
# Frees up memory by stopping non-essential processes

SERVER="root@170.64.199.151"
SSH_KEY="~/.ssh/id_rsa"

echo "🧹 Cleaning up memory before evening analysis..."
echo "==============================================="

ssh -i "$SSH_KEY" "$SERVER" '
echo "Memory before cleanup:"
free -h

# Stop smart collector temporarily
echo "Stopping smart collector..."
pkill -f "news_collector --interval" || echo "Smart collector not running"

# Clear system caches
echo "Clearing system caches..."
sync
echo 3 > /proc/sys/vm/drop_caches

# Force garbage collection in any running Python processes
echo "Forcing garbage collection..."
python3 -c "import gc; gc.collect(); print(\"GC complete\")" 2>/dev/null || true

echo "Memory after cleanup:"
free -h

# Now run evening analysis with memory check
cd /root/test
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test

AVAILABLE_MB=$(free -m | awk "NR==2{printf \"%.0f\", \$7}")
echo "Available memory: ${AVAILABLE_MB}MB"

if [ $AVAILABLE_MB -gt 800 ]; then
    echo "✅ Sufficient memory for evening analysis"
    export USE_TWO_STAGE_ANALYSIS=1
    export SKIP_TRANSFORMERS=1  # Safe mode
    python -m app.main evening
    
    # Restart smart collector after analysis
    echo "Restarting smart collector..."
    nohup python -m app.core.data.collectors.news_collector --interval 30 > /dev/null 2>&1 &
else
    echo "⚠️ Insufficient memory (${AVAILABLE_MB}MB). Skipping evening analysis."
fi
'
