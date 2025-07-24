#!/bin/bash

echo "📊 MORNING ROUTINE CRON MONITOR"
echo "==============================="
echo ""

# Check cron service status
echo "🔧 Cron Service Status:"
if systemctl is-active --quiet cron; then
    echo "  ✅ Cron service is running"
else
    echo "  ❌ Cron service is not running"
    echo "  🔄 Starting cron service..."
    systemctl start cron
fi

echo ""

# Show current cron jobs
echo "📋 Current Cron Jobs:"
crontab -l | grep -E "morning|app.main" || echo "  ❌ No morning routine cron jobs found"

echo ""

# Check log file
echo "📄 Recent Log Activity:"
if [ -f "/root/trading_analysis/logs/morning_cron.log" ]; then
    echo "  📊 Last 5 log entries:"
    tail -5 /root/trading_analysis/logs/morning_cron.log
    echo ""
    echo "  📈 Log file size: $(du -h /root/trading_analysis/logs/morning_cron.log | cut -f1)"
else
    echo "  ⚠️ No log file found yet (first run pending)"
fi

echo ""

# Show next execution time
echo "⏰ Next Execution Times:"
echo "  🕐 Current time: $(date '+%H:%M:%S')"
echo "  🔄 Next 30-min mark: $(date -d 'now + 30 minutes' '+%H:%M') (or sooner if within 30min window)"

echo ""
echo "🎯 Quick Commands:"
echo "  📊 Monitor logs: tail -f /root/trading_analysis/logs/morning_cron.log"
echo "  🛑 Stop cron: crontab -r"
echo "  📋 Edit cron: crontab -e"
echo "  🔄 Manual run: python -m app.main morning"
