#!/bin/bash

# ==============================================================================
# AUTOMATED MORNING ROUTINE CRON SETUP
# ==============================================================================
# Sets up continuous main.py morning execution every 30 minutes
# Author: Trading Analysis System
# Created: July 24, 2025
# ==============================================================================

echo '🕐 SETTING UP AUTOMATED MORNING ROUTINE'
echo '======================================'

# Configuration
SCRIPT_DIR='/root/trading_analysis'
VENV_PATH='/root/trading_venv'
LOG_DIR='$SCRIPT_DIR/logs'
CRON_LOG='$LOG_DIR/morning_cron.log'

# Ensure log directory exists
mkdir -p $LOG_DIR

# Create the cron command
CRON_COMMAND="*/30 * * * * cd $SCRIPT_DIR && source $VENV_PATH/bin/activate && export PYTHONPATH=$SCRIPT_DIR && python -m app.main morning >> $CRON_LOG 2>&1"

echo '📋 Cron command to be added:'
echo "$CRON_COMMAND"
echo ''

# Backup existing crontab
echo '💾 Backing up existing crontab...'
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'No existing crontab found'

# Remove any existing morning routine cron jobs
echo '🧹 Removing existing morning routine cron jobs...'
crontab -l 2>/dev/null | grep -v 'app.main morning' | crontab - 2>/dev/null || true

# Add new cron job
echo '➕ Adding new morning routine cron job...'
(crontab -l 2>/dev/null; echo "# Automated Morning Routine - Every 30 minutes"; echo "$CRON_COMMAND") | crontab -

# Verify installation
echo ''
echo '✅ CRON JOB SETUP COMPLETE!'
echo '=========================='
echo '📋 Current crontab:'
crontab -l | grep -E 'morning|app.main'

echo ''
echo '📊 System Information:'
echo "   🕐 Runs every: 30 minutes"
echo "   📁 Working directory: $SCRIPT_DIR"
echo "   📋 Log file: $CRON_LOG"
echo "   🔄 Next run: $(date -d '+30 minutes' '+%H:%M')"

echo ''
echo '🎯 Management Commands:'
echo "   📊 View logs: tail -f $CRON_LOG"
echo "   🛑 Stop cron: crontab -e (remove the morning line)"
echo "   📋 List cron: crontab -l"

echo ''
echo '✅ Automated morning routine is now active!'
