#!/bin/bash
# 🔍 VIRTUAL ENVIRONMENT ANALYSIS SCRIPT
# Run this to determine if we can safely consolidate virtual environments

REMOTE="root@170.64.199.151"
LOG_FILE="/tmp/venv_analysis_$(date +%Y%m%d_%H%M%S).log"

echo "🔍 VIRTUAL ENVIRONMENT ANALYSIS"
echo "==============================="
echo "Time: $(date)"
echo "Target: $REMOTE"
echo "Log: $LOG_FILE"
echo ""

# Function to log and execute
log_and_run() {
    echo "CHECKING: $1" | tee -a $LOG_FILE
    ssh $REMOTE "$1" 2>&1 | tee -a $LOG_FILE
    echo "---" | tee -a $LOG_FILE
}

# 1. COMPARE VIRTUAL ENVIRONMENTS
echo "📦 STEP 1: COMPARE VIRTUAL ENVIRONMENTS"
echo "Size comparison:"
log_and_run "du -sh /root/trading_venv /root/test/.venv 2>/dev/null"

echo ""
echo "Python versions:"
log_and_run "echo 'TRADING_VENV:' && /root/trading_venv/bin/python --version"
log_and_run "echo 'TEST_VENV:' && /root/test/.venv/bin/python --version"

echo ""
echo "Package comparison (first 20 packages):"
log_and_run "echo 'TRADING_VENV packages:' && /root/trading_venv/bin/pip list | head -20"  
log_and_run "echo 'TEST_VENV packages:' && /root/test/.venv/bin/pip list | head -20"

# 2. TEST CRITICAL IMPORTS
echo ""
echo "🧪 STEP 2: TEST CRITICAL IMPORTS"
echo "Testing trading_venv:"
log_and_run "cd /root && source trading_venv/bin/activate && python -c 'import yfinance; import pandas; import numpy; import sklearn; print(\"TRADING_VENV: All critical imports successful\")' || echo 'TRADING_VENV: Import errors detected'"

echo ""
echo "Testing test/.venv:"
log_and_run "cd /root/test && source .venv/bin/activate && python -c 'import yfinance; import pandas; import numpy; import sklearn; print(\"TEST_VENV: All critical imports successful\")' || echo 'TEST_VENV: Import errors detected'"

# 3. TEST APPLICATION STARTUP
echo ""
echo "🚀 STEP 3: TEST APPLICATION STARTUP"
echo "Testing enhanced_morning_analyzer with trading_venv:"
log_and_run "cd /root && source trading_venv/bin/activate && timeout 10 python enhanced_morning_analyzer.py --test 2>&1 | head -5 || echo 'TRADING_VENV: Enhanced analyzer test completed/timed out'"

echo ""
echo "Testing app framework with test/.venv:"
log_and_run "cd /root/test && source .venv/bin/activate && timeout 10 python -c 'import app; print(\"TEST_VENV: App framework imports successfully\")' || echo 'TEST_VENV: App framework test failed'"

# 4. MEMORY USAGE ANALYSIS
echo ""
echo "💻 STEP 4: MEMORY USAGE ANALYSIS"
log_and_run "free -m"
log_and_run "echo 'Current Python processes:' && ps aux | grep python | grep -v grep"

# 5. DISK SPACE BREAKDOWN
echo ""
echo "💾 STEP 5: DETAILED DISK SPACE BREAKDOWN"
log_and_run "echo 'Virtual environment sizes:'"
log_and_run "du -sh /root/trading_venv/* 2>/dev/null | sort -hr | head -10"
log_and_run "du -sh /root/test/.venv/* 2>/dev/null | sort -hr | head -10"

log_and_run "echo 'Largest directories in trading_venv:'"
log_and_run "find /root/trading_venv -type d -exec du -sh {} + 2>/dev/null | sort -hr | head -10"

# 6. PACKAGE DEPENDENCY ANALYSIS
echo ""
echo "📋 STEP 6: PACKAGE DEPENDENCY ANALYSIS"
log_and_run "echo 'Critical package versions in trading_venv:'"
log_and_run "/root/trading_venv/bin/pip show yfinance pandas numpy scikit-learn 2>/dev/null | grep -E '^(Name|Version):' || echo 'Some packages not found'"

log_and_run "echo 'Critical package versions in test/.venv:'"
log_and_run "/root/test/.venv/bin/pip show yfinance pandas numpy scikit-learn 2>/dev/null | grep -E '^(Name|Version):' || echo 'Some packages not found'"

# 7. RECOMMENDATIONS
echo ""
echo "💡 STEP 7: CONSOLIDATION RECOMMENDATIONS"
echo "========================================"

# Determine which venv is better
ssh $REMOTE "
if [ -d /root/test/.venv ] && [ -d /root/trading_venv ]; then
    TEST_SIZE=\$(du -sb /root/test/.venv 2>/dev/null | cut -f1)
    TRADING_SIZE=\$(du -sb /root/trading_venv 2>/dev/null | cut -f1)
    
    echo 'SIZE COMPARISON:'
    echo \"  /root/test/.venv: \$(du -sh /root/test/.venv 2>/dev/null | cut -f1)\"
    echo \"  /root/trading_venv: \$(du -sh /root/trading_venv 2>/dev/null | cut -f1)\"
    echo ''
    
    if [ \$TEST_SIZE -lt \$TRADING_SIZE ]; then
        echo '🎯 RECOMMENDATION: Use /root/test/.venv (smaller)'
        echo '   • Move enhanced_morning_analyzer.py to /root/test/'
        echo '   • Update cron jobs to use /root/test/.venv'
        echo '   • Delete /root/trading_venv to save 2.6GB'
    else
        echo '🎯 RECOMMENDATION: Keep /root/trading_venv (better established)'
        echo '   • Delete /root/test/.venv to save space'
        echo '   • Continue using trading_venv for cron jobs'
    fi
else
    echo 'ERROR: Could not compare virtual environments'
fi
" | tee -a $LOG_FILE

echo ""
echo "✅ VIRTUAL ENVIRONMENT ANALYSIS COMPLETE!"
echo "========================================"
echo "Time: $(date)"
echo "Log saved to: $LOG_FILE"
echo ""
echo "📋 NEXT STEPS:"
echo "  1. Review the analysis results above"
echo "  2. Test both environments with actual workloads"
echo "  3. Choose consolidation strategy based on results"
echo "  4. Run phase2_cleanup.sh when ready"

# Show the log file
echo ""
echo "📄 FULL LOG OUTPUT:"
echo "==================="
cat $LOG_FILE
