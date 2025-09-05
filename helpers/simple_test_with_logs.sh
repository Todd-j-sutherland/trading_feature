#!/bin/bash
# 🧪 Simple Test Script with Log Export (matches your exact command)
# Runs the exact commands you specified and exports logs for analysis

echo "🏦 ASX Trading System - Simple Test with Log Analysis"
echo "====================================================="
echo "📅 Test Date: $(date)"
echo ""

# Create temp directory for logs
TEMP_DIR="/tmp/asx_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEMP_DIR"
echo "📁 Log Directory: $TEMP_DIR"
echo ""

# Combined log file for all commands
COMBINED_LOG="$TEMP_DIR/combined_output.log"
ERRORS_LOG="$TEMP_DIR/errors_and_warnings.log"

echo "🚀 Running your exact command sequence..."
echo "=========================================="

# Your exact command with log capture
{
    echo "=== STARTING MORNING ANALYSIS ==="
    python -m app.main morning
    echo ""
    
    echo "=== STARTING ML DATA COLLECTION ==="
    python enhanced_ml_system/multi_bank_data_collector.py
    echo ""
    
    echo "=== STARTING VALIDATION METRICS EXPORT ==="
    python export_and_validate_metrics.py
    echo ""
    
    echo "=== STARTING HTML DASHBOARD GENERATION ==="
    python enhanced_ml_system/html_dashboard_generator.py
    echo ""
    
    echo "✅ All core features tested successfully!"
    
} 2>&1 | tee "$COMBINED_LOG"

# Extract errors and warnings
echo ""
echo "🔍 ANALYZING OUTPUT FOR ERRORS AND WARNINGS"
echo "============================================"

# Search for issues and save to separate file
{
    echo "ASX Trading System - Error and Warning Analysis"
    echo "==============================================="
    echo "Generated: $(date)"
    echo ""
    
    echo "🚨 ERRORS FOUND:"
    echo "================"
    grep -i "error\|exception\|traceback\|failed" "$COMBINED_LOG" || echo "No errors found."
    echo ""
    
    echo "⚠️  WARNINGS FOUND:"
    echo "=================="
    grep -i "warning\|warn" "$COMBINED_LOG" || echo "No warnings found."
    echo ""
    
    echo "💥 CRITICAL ISSUES:"
    echo "=================="
    grep -i "critical\|fatal" "$COMBINED_LOG" || echo "No critical issues found."
    echo ""
    
} > "$ERRORS_LOG"

# Display the analysis
cat "$ERRORS_LOG"

# Count issues
ERROR_COUNT=$(grep -i "error\|exception\|traceback\|failed" "$COMBINED_LOG" | wc -l)
WARNING_COUNT=$(grep -i "warning\|warn" "$COMBINED_LOG" | wc -l)
CRITICAL_COUNT=$(grep -i "critical\|fatal" "$COMBINED_LOG" | wc -l)

echo "📊 ISSUE SUMMARY"
echo "================"
echo "Errors: $ERROR_COUNT"
echo "Warnings: $WARNING_COUNT"
echo "Critical: $CRITICAL_COUNT"
echo ""

if [ $ERROR_COUNT -eq 0 ] && [ $CRITICAL_COUNT -eq 0 ]; then
    echo "🎉 SUCCESS: No errors or critical issues found!"
    if [ $WARNING_COUNT -gt 0 ]; then
        echo "⚠️  Note: $WARNING_COUNT warnings found (may be normal)"
    fi
else
    echo "⚠️  ISSUES DETECTED: Review the logs above"
fi

echo ""
echo "📁 LOG FILES CREATED:"
echo "===================="
echo "Complete output: $COMBINED_LOG"
echo "Errors/Warnings: $ERRORS_LOG"
echo ""
echo "🔍 QUICK COMMANDS TO VIEW LOGS:"
echo "==============================="
echo "# View complete output:"
echo "cat $COMBINED_LOG"
echo ""
echo "# View only errors/warnings:"
echo "cat $ERRORS_LOG"
echo ""
echo "# Search for specific term:"
echo "grep -i 'your_search_term' $COMBINED_LOG"
echo ""
echo "# View last 20 lines of output:"
echo "tail -20 $COMBINED_LOG"
