#!/bin/bash

# CRON MANAGEMENT COMMAND
# Restart, setup, and manage all trading system cron jobs

echo "🔧 TRADING SYSTEM CRON MANAGER"
echo "==============================="
echo "Date: $(date)"
echo ""

# Configuration
REMOTE_HOST="root@170.64.199.151"
REMOTE_PATH="/root/test"

# Function to run remote cron management
manage_cron() {
    local action="$1"
    
    case $action in
        "restart")
            echo "🔄 Restarting cron service and reloading jobs..."
            ssh $REMOTE_HOST "
                cd $REMOTE_PATH
                echo '1. Stopping cron service...'
                systemctl stop cron
                echo '2. Starting cron service...'
                systemctl start cron
                echo '3. Reloading crontab...'
                crontab -l > /tmp/current_cron.txt
                crontab /tmp/current_cron.txt
                echo '4. Verifying service...'
                systemctl is-active cron
                echo '5. Current job count:'
                crontab -l | grep -E '^[^#]' | wc -l
                echo '✅ Cron service restarted successfully'
            "
            ;;
            
        "setup")
            echo "🔧 Setting up fresh cron jobs from scratch..."
            ssh $REMOTE_HOST "
                cd $REMOTE_PATH
                echo 'Running market-aware cron setup...'
                bash setup_market_aware_cron.sh
                echo '✅ Fresh cron setup completed'
            "
            ;;
            
        "status")
            echo "📊 Checking cron status..."
            ssh $REMOTE_HOST "
                cd $REMOTE_PATH
                echo 'Cron service status:'
                systemctl is-active cron
                echo ''
                echo 'Active cron jobs:'
                crontab -l | grep -E '^[^#]' | wc -l
                echo ''
                echo 'Recent cron activity:'
                tail -10 /var/log/syslog | grep CRON | tail -5
                echo ''
                echo 'Trading-specific cron jobs:'
                crontab -l | grep -E '(fixed_price|enhanced_morning|evaluate_predictions)' | wc -l
                echo 'trading jobs found'
            "
            ;;
            
        "backup")
            echo "💾 Backing up current cron configuration..."
            ssh $REMOTE_HOST "
                cd $REMOTE_PATH
                crontab -l > crontab_backup_\$(date +%Y%m%d_%H%M%S).txt
                echo '✅ Cron backup created'
                ls -la crontab_backup_*.txt | tail -1
            "
            ;;
            
        "list")
            echo "📋 Current cron jobs:"
            ssh $REMOTE_HOST "crontab -l"
            ;;
            
        "force-run")
            echo "⚡ Force running all trading processes manually..."
            ssh $REMOTE_HOST "
                cd $REMOTE_PATH
                source /root/trading_venv/bin/activate
                export PYTHONPATH=$REMOTE_PATH
                
                echo '1. Running morning analysis...'
                python enhanced_morning_analyzer_with_ml.py >> logs/manual_run.log 2>&1 &
                
                echo '2. Running predictions...'
                python production/cron/fixed_price_mapping_system.py >> logs/manual_run.log 2>&1 &
                
                echo '3. Running evaluation...'
                bash evaluate_predictions_comprehensive.sh >> logs/manual_run.log 2>&1 &
                
                echo '✅ All processes started in background'
                echo 'Check logs/manual_run.log for output'
            "
            ;;
            
        *)
            echo "❌ Unknown action: $action"
            show_usage
            exit 1
            ;;
    esac
}

# Show usage information
show_usage() {
    echo "Usage: $0 {restart|setup|status|backup|list|force-run}"
    echo ""
    echo "Actions:"
    echo "  restart    - Restart cron service and reload all jobs"
    echo "  setup      - Fresh setup of all market-aware cron jobs"
    echo "  status     - Check cron service and job status"
    echo "  backup     - Backup current cron configuration"
    echo "  list       - List all current cron jobs"
    echo "  force-run  - Manually run all trading processes now"
    echo ""
    echo "Examples:"
    echo "  $0 restart     # Restart everything"
    echo "  $0 status      # Check status"
    echo "  $0 force-run   # Run all processes manually"
}

# Main execution
if [ $# -eq 0 ]; then
    echo "🚀 No action specified. Showing status and options..."
    echo ""
    manage_cron "status"
    echo ""
    show_usage
else
    manage_cron "$1"
fi

echo ""
echo "🎯 Cron management completed!"
