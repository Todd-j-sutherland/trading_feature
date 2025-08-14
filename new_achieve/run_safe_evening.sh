#!/bin/bash

# Local Script to Run Memory-Safe Evening Analysis on Remote Server
# This script intelligently manages memory and prevents OOM kills

SERVER="root@170.64.199.151"
SSH_KEY="~/.ssh/id_rsa"

echo "🌙 Running Memory-Safe Evening Analysis"
echo "======================================"
echo "📅 $(date)"
echo ""

# Function to run remote commands
run_remote() {
    ssh -i "$SSH_KEY" "$SERVER" "$1"
}

echo "📊 Checking remote server memory status..."
run_remote "bash /root/test/memory_monitor.sh | grep -A 10 'MEMORY RECOMMENDATIONS'"

echo ""
echo "🧹 Running pre-analysis memory cleanup..."
if run_remote "bash /root/test/memory_cleanup.sh"; then
    echo "✅ Memory cleanup successful"
else
    echo "⚠️ Memory cleanup had issues, but continuing..."
fi

echo ""
echo "🚀 Starting smart evening analysis..."
run_remote "bash /root/test/smart_evening.sh"

echo ""
echo "📊 Final memory status:"
run_remote "free -h"

echo ""
echo "✅ Memory-safe evening analysis complete!"
echo ""
echo "💡 To monitor ongoing status:"
echo "   ./advanced_memory_monitor.sh"
echo ""
echo "📊 To view analysis logs:"
echo "   ssh -i ~/.ssh/id_rsa root@170.64.199.151 'tail -20 /root/test/logs/evening_analysis.log'"
