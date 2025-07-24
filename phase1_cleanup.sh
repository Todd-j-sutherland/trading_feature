#!/bin/bash
# 🧹 PHASE 1: SAFE REMOTE CLEANUP SCRIPT
# Execute this during off-hours (after 7 PM AEST)

REMOTE="root@170.64.199.151"
LOG_FILE="/tmp/remote_cleanup_$(date +%Y%m%d_%H%M%S).log"

echo "🧹 STARTING SAFE REMOTE CLEANUP - PHASE 1"
echo "=========================================="
echo "Time: $(date)"
echo "Target: $REMOTE"
echo "Log: $LOG_FILE"
echo ""

# Function to log and execute
log_and_run() {
    echo "EXECUTING: $1" | tee -a $LOG_FILE
    ssh $REMOTE "$1" 2>&1 | tee -a $LOG_FILE
    echo "RESULT: $?" | tee -a $LOG_FILE
    echo "---" | tee -a $LOG_FILE
}

# 1. BACKUP CRITICAL FILES FIRST (SAFETY)
echo "📋 STEP 1: BACKUP CRITICAL FILES"
log_and_run "cp /root/enhanced_morning_analyzer.py /root/enhanced_morning_analyzer_CLEANUP_BACKUP.py"
log_and_run "cp /root/trading_analysis.db /root/trading_analysis_CLEANUP_BACKUP.db"
log_and_run "cp /root/morning_analysis.db /root/morning_analysis_CLEANUP_BACKUP.db"

# 2. DELETE OBSOLETE PYTHON FILES IN /ROOT
echo "🗑️ STEP 2: DELETE OBSOLETE PYTHON FILES"
OBSOLETE_FILES=(
    "/root/enhanced_morning_analyzer_backup.py"
    "/root/enhanced_morning_analyzer_broken.py"
    "/root/fixed_morning_system.py"
    "/root/fixed_morning_system_backup.py"
    "/root/fixed_morning_system_before_restore.py"
    "/root/morning_analysis_system.py"
    "/root/morning_analysis_system_v2.py"
    "/root/morning_system_final.py"
    "/root/working_morning_system.py"
    "/root/evening_ml_system.py"
    "/root/evening_ml_system_v2.py"
    "/root/optimized_signal_logic.py"
    "/root/simple_sentiment_analyzer.py"
    "/root/test_systems.py"
    "/root/morning_analysis_restored.db"
)

for file in "${OBSOLETE_FILES[@]}"; do
    log_and_run "[ -f \"$file\" ] && rm \"$file\" && echo 'DELETED: $file' || echo 'NOT FOUND: $file'"
done

# 3. DELETE DUPLICATE DATA DIRECTORIES
echo "🗂️ STEP 3: DELETE DUPLICATE DATA DIRECTORIES"
log_and_run "[ -d /root/test/data_temp ] && rm -rf /root/test/data_temp && echo 'DELETED: /root/test/data_temp' || echo 'NOT FOUND: data_temp'"
log_and_run "[ -d /root/test/data_v2 ] && rm -rf /root/test/data_v2 && echo 'DELETED: /root/test/data_v2' || echo 'NOT FOUND: data_v2'"

# 4. CLEAN PYTHON CACHE FILES
echo "🧹 STEP 4: CLEAN PYTHON CACHE FILES"
log_and_run "find /root/test -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null && echo 'CLEANED: Python cache files'"
log_and_run "find /root/.cache -name '*.db' -mtime +7 -delete 2>/dev/null && echo 'CLEANED: Old cache files'"

# 5. VERIFY CRITICAL SYSTEMS STILL WORK
echo "✅ STEP 5: VERIFY SYSTEM INTEGRITY"
log_and_run "[ -f /root/enhanced_morning_analyzer.py ] && echo 'VERIFIED: enhanced_morning_analyzer.py exists' || echo 'ERROR: enhanced_morning_analyzer.py missing!'"
log_and_run "[ -f /root/evening_system_final.py ] && echo 'VERIFIED: evening_system_final.py exists' || echo 'ERROR: evening_system_final.py missing!'"
log_and_run "[ -f /root/trading_analysis.db ] && echo 'VERIFIED: trading_analysis.db exists' || echo 'ERROR: trading_analysis.db missing!'"
log_and_run "ps aux | grep -E '(python.*news_collector|python.*enhanced_morning)' | grep -v grep && echo 'VERIFIED: Python processes running' || echo 'NOTE: No trading processes currently running'"

# 6. DISK SPACE ANALYSIS
echo "💾 STEP 6: DISK SPACE ANALYSIS"
log_and_run "echo 'BEFORE/AFTER DISK USAGE:'"
log_and_run "df -h /"
log_and_run "du -sh /root/test/data* 2>/dev/null || echo 'Data directories cleaned'"
log_and_run "du -sh /root/trading_venv /root/test/.venv 2>/dev/null"

# 7. FINAL SUMMARY
echo ""
echo "✅ PHASE 1 CLEANUP COMPLETE!"
echo "=========================="
echo "Time: $(date)"
echo "Log saved to: $LOG_FILE"
echo ""
echo "🔍 WHAT WAS CLEANED:"
echo "  • 15+ obsolete Python files (~150KB)"
echo "  • 2 duplicate data directories (~20MB)"  
echo "  • Python cache files"
echo "  • Old cache databases"
echo ""
echo "⚠️ WHAT REMAINS (REVIEW FOR PHASE 2):"
echo "  • /root/trading_venv (2.6GB) - virtual environment"
echo "  • Various debug scripts in /root/test/"
echo ""
echo "📋 NEXT STEPS:"
echo "  1. Review the log file: $LOG_FILE"
echo "  2. Test system functionality"
echo "  3. Consider Phase 2 cleanup if needed"

# Show the log file
echo ""
echo "📄 FULL LOG OUTPUT:"
echo "==================="
cat $LOG_FILE
