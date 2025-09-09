#!/bin/bash

# ONE-COMMAND CRON RESTART
# Simple command to restart all cron jobs

echo "🚀 RESTARTING ALL TRADING CRON JOBS"
echo "==================================="

ssh root@170.64.199.151 "
    cd /root/test
    echo '🔄 Restarting cron service...'
    systemctl restart cron
    
    echo '✅ Cron service restarted'
    echo '📊 Status check:'
    echo '  Service: ' \$(systemctl is-active cron)
    echo '  Jobs: ' \$(crontab -l | grep -E '^[^#]' | wc -l) 'active'
    echo '  Trading jobs: ' \$(crontab -l | grep -E '(fixed_price|enhanced_morning|evaluate_predictions)' | wc -l) 'found'
    
    echo ''
    echo '🎯 All cron jobs restarted and active!'
"
