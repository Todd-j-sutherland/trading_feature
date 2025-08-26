#!/bin/bash

echo "🚀 SERVER RESTART SETUP SCRIPT"
echo "==============================="
echo

echo "📅 Current Time: $(date)"
echo "🌏 Current Time AEST: $(TZ=Australia/Sydney date)"
echo

# Check if cron job exists
echo "🔍 Checking cron job status..."
CRON_EXISTS=$(crontab -l 2>/dev/null | grep "efficient_prediction_system.py" | wc -l)

if [ "$CRON_EXISTS" -gt 0 ]; then
    echo "✅ Cron job already exists:"
    crontab -l | grep "efficient_prediction"
else
    echo "❌ Cron job missing - reinstalling..."
    # Add the cron job
    (crontab -l 2>/dev/null; echo "*/30 10-15 * * 1-5 /root/trading_venv/bin/python3 /root/test/efficient_prediction_system.py >> /root/test/cron_prediction.log 2>&1") | crontab -
    echo "✅ Cron job installed: */30 10-15 * * 1-5"
fi

echo
echo "🎯 Available commands after restart:"
echo "===================================="
echo
echo "1️⃣  EFFICIENT SYSTEM (Recommended):"
echo "    /root/trading_venv/bin/python3 /root/test/efficient_prediction_system.py"
echo "    • Uses <100MB memory"
echo "    • Validates market hours automatically"
echo "    • Logs to efficient_prediction_log.txt"
echo
echo "2️⃣  LEGACY SYSTEM (if needed):"
echo "    cd /root/test && source /root/trading_venv/bin/activate && python -m app.main morning"
echo "    • Original system"
echo "    • Higher memory usage"
echo "    • May require manual monitoring"
echo
echo "🕐 CURRENT STATUS:"
CURRENT_HOUR=$(TZ=Australia/Sydney date +%H)
if [ "$CURRENT_HOUR" -ge 10 ] && [ "$CURRENT_HOUR" -lt 16 ]; then
    echo "✅ MARKET IS OPEN - You can run predictions now"
else
    echo "⏰ MARKET IS CLOSED - Predictions will wait for market hours"
fi

echo
echo "🚀 QUICK START:"
echo "==============="
echo "Run this command to test the system:"
echo "/root/trading_venv/bin/python3 /root/test/efficient_prediction_system.py"
echo
echo "✅ Setup complete!"
