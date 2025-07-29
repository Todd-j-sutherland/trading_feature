#!/bin/bash

# Smart Collector Startup Script
echo "🚀 Smart Collector Management"
echo "============================="

# Check if already running
if pgrep -f news_collector > /dev/null; then
    echo "⚠️  Smart collector is already running"
    echo "📋 Current process:"
    ps aux | grep news_collector | grep -v grep
    echo ""
    echo "📊 Recent activity:"
    tail -5 logs/smart_collector.log 2>/dev/null || echo "No log file found"
    exit 0
fi

# Start smart collector
echo "🔄 Starting smart collector..."
mkdir -p logs
nohup python app/core/data/collectors/news_collector.py --interval 30 > logs/smart_collector.log 2>&1 &

sleep 2

# Verify it started
if pgrep -f news_collector > /dev/null; then
    echo "✅ Smart collector started successfully!"
    echo "📋 Process ID: $(pgrep -f news_collector)"
    echo "📊 Log file: logs/smart_collector.log"
    echo "⏰ Collection interval: 30 minutes"
else
    echo "❌ Failed to start smart collector"
    echo "📋 Check logs/smart_collector.log for errors"
fi
