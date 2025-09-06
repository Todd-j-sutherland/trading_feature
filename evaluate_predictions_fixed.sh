#!/bin/bash
# Fixed Outcome Evaluation Script
# Uses the new fixed evaluator to prevent database locking issues

cd /root/test

# Ensure logs directory exists
mkdir -p logs

# Run the fixed outcome evaluator
python3 fixed_outcome_evaluator.py >> logs/evaluation_fixed.log 2>&1

# Also log to the original evaluation log for compatibility
echo "$(date): Fixed evaluator completed" >> logs/evaluation.log

# Optional: Quick status check
echo "$(date): Evaluation job completed" >> logs/cron_status.log
