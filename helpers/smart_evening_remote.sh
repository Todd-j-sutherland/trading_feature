#!/bin/bash

# Smart Evening Analysis - Memory-aware processing
# This script automatically chooses the best analysis mode based on available memory

SERVER="root@170.64.199.151"
SSH_KEY="~/.ssh/id_rsa"

echo "🌙 Starting Smart Evening Analysis..."
echo "===================================="

# Check available memory before running
ssh -i "$SSH_KEY" "$SERVER" '
cd /root/test
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test

# Get available memory (not just used %)
AVAILABLE_MB=$(free -m | awk "NR==2{printf \"%.0f\", \$7}")
TOTAL_MB=$(free -m | awk "NR==2{printf \"%.0f\", \$2}")
USED_PERCENT=$(free | awk "NR==2{printf \"%.0f\", \$3/\$2 * 100}")

echo "💾 Memory Status:"
echo "   Total: ${TOTAL_MB}MB"
echo "   Available: ${AVAILABLE_MB}MB" 
echo "   Used: ${USED_PERCENT}%"

# Decision logic based on AVAILABLE memory
if [ $AVAILABLE_MB -gt 1200 ]; then
    echo "🚀 HIGH MEMORY MODE: Running Stage 2 Enhanced Analysis"
    export USE_TWO_STAGE_ANALYSIS=1
    export SKIP_TRANSFORMERS=0
    python -m app.main evening
elif [ $AVAILABLE_MB -gt 800 ]; then
    echo "⚖️ BALANCED MODE: Running FinBERT-only Analysis"
    export USE_TWO_STAGE_ANALYSIS=1
    export FINBERT_ONLY=1
    python -m app.main evening
elif [ $AVAILABLE_MB -gt 400 ]; then
    echo "💡 SAFE MODE: Running Stage 1 Enhanced Analysis"
    export USE_TWO_STAGE_ANALYSIS=1
    export SKIP_TRANSFORMERS=1
    python -m app.main evening
else
    echo "⚠️ LOW MEMORY: Skipping evening analysis - insufficient memory"
    echo "   Consider running: sudo systemctl restart trading_analysis"
    exit 1
fi

echo "✅ Evening analysis complete"
'
