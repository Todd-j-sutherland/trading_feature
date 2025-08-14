#!/bin/bash
# Protected Morning Routine Cron Job
# Add this to your crontab: 0 9 * * 1-5 /path/to/protected_morning_cron.sh

echo "🌅 Starting Protected Morning Routine at $(date)"

cd /root/test  # Adjust to your trading directory

# Run protected morning routine
python3 protected_morning_routine.py enhanced_morning_analyzer_with_ml.py

if [ $? -eq 0 ]; then
    echo "✅ Morning routine completed successfully"
else
    echo "❌ Morning routine failed - check logs"
    # Send alert email/notification here if needed
fi
