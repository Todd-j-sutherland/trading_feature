#!/bin/bash

# Remote Server Monitoring Script for Trading Analysis System

SERVER="root@170.64.199.151"
SSH_KEY="~/.ssh/id_rsa"

# Function to run remote commands
run_remote() {
    ssh -i "$SSH_KEY" "$SERVER" "$1"
}

echo "🖥️  Trading Analysis System - Remote Server Status"
echo "=================================================="
echo "📅 $(date)"
echo ""

# System resources
echo "💾 Memory Usage:"
run_remote "free -h"
echo ""

echo "💽 Disk Usage:"
run_remote "df -h | grep -E '(Filesystem|/dev/root)'"
echo ""

# Process status
echo "🔄 Background Processes:"
smart_collector=$(run_remote "ps aux | grep 'news_collector --interval' | grep -v grep" || echo "")
if [ -n "$smart_collector" ]; then
    echo "✅ Smart Collector: RUNNING"
    echo "   $smart_collector"
    
    # Get process memory usage
    memory_usage=$(echo "$smart_collector" | awk '{print $4}')
    echo "   Memory: ${memory_usage}% of total RAM"
else
    echo "❌ Smart Collector: NOT RUNNING"
fi
echo ""

# Recent logs
echo "📊 Recent Activity (last 10 lines):"
run_remote "tail -10 /root/test/logs/dashboard.log 2>/dev/null || echo 'No logs found'"
echo ""

# Data collection stats
echo "📈 Data Collection Status:"
run_remote "cd /root/test && find data/sentiment_history -name '*.json' -mtime -1 2>/dev/null | wc -l | xargs echo 'Recent sentiment files:'" || echo "No recent data"
echo ""

# Quick system health check
echo "🔍 System Health:"
run_remote "uptime"
run_remote "python3 --version"
echo ""

echo "🎯 Quick Commands:"
echo "   Monitor logs: ssh -i $SSH_KEY $SERVER 'tail -f /root/test/logs/dashboard.log'"
echo "   Restart collector: ssh -i $SSH_KEY $SERVER 'cd /root/test && SKIP_TRANSFORMERS=1 python -m app.main morning'"
echo "   Check news: ssh -i $SSH_KEY $SERVER 'cd /root/test && SKIP_TRANSFORMERS=1 python -m app.main news'"
