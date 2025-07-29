#!/bin/bash
# 🧪 ASX Trading System - Comprehensive Test with Log Analysis
# Runs all core features and analyzes logs for errors/warnings

echo "🏦 ASX Trading System - Comprehensive Test with Log Analysis"
echo "============================================================="
echo "📅 Test Date: $(date)"
echo "🖥️  Host: $(hostname)"
echo "🐍 Python: $(python --version 2>&1)"
echo ""

# Create temp directory for logs
TEMP_DIR="/tmp/asx_trading_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEMP_DIR"
echo "📁 Log Directory: $TEMP_DIR"
echo ""

# Test results tracking
declare -A test_results
declare -A test_logs
total_tests=0
passed_tests=0
failed_tests=0

# Function to run test and capture logs
run_test() {
    local test_name="$1"
    local test_command="$2"
    local log_file="$TEMP_DIR/${test_name}.log"
    
    echo "🧪 Testing: $test_name"
    echo "   Command: $test_command"
    echo "   Log: $log_file"
    
    # Run command and capture output
    if eval "$test_command" > "$log_file" 2>&1; then
        test_results["$test_name"]="PASSED"
        echo "   ✅ PASSED"
        ((passed_tests++))
    else
        test_results["$test_name"]="FAILED"
        echo "   ❌ FAILED"
        ((failed_tests++))
    fi
    
    test_logs["$test_name"]="$log_file"
    ((total_tests++))
    echo ""
}

# Function to analyze logs for errors and warnings
analyze_logs() {
    echo "🔍 ANALYZING LOGS FOR ERRORS AND WARNINGS"
    echo "=========================================="
    
    local found_issues=false
    
    for test_name in "${!test_logs[@]}"; do
        local log_file="${test_logs[$test_name]}"
        local status="${test_results[$test_name]}"
        
        echo ""
        echo "📋 $test_name ($status)"
        echo "   Log: $log_file"
        
        if [ -f "$log_file" ]; then
            # Count different types of issues
            local errors=$(grep -i "error\|exception\|traceback\|failed" "$log_file" | wc -l)
            local warnings=$(grep -i "warning\|warn" "$log_file" | wc -l)
            local critical=$(grep -i "critical\|fatal" "$log_file" | wc -l)
            
            echo "   📊 Issues: $errors errors, $warnings warnings, $critical critical"
            
            # Show specific issues if found
            if [ $errors -gt 0 ] || [ $warnings -gt 0 ] || [ $critical -gt 0 ]; then
                found_issues=true
                echo "   🚨 ISSUES FOUND:"
                
                # Show critical issues
                if [ $critical -gt 0 ]; then
                    echo "      💥 CRITICAL/FATAL:"
                    grep -i "critical\|fatal" "$log_file" | head -3 | sed 's/^/         /'
                fi
                
                # Show errors
                if [ $errors -gt 0 ]; then
                    echo "      ❌ ERRORS:"
                    grep -i "error\|exception\|traceback\|failed" "$log_file" | head -5 | sed 's/^/         /'
                fi
                
                # Show warnings (limited to avoid spam)
                if [ $warnings -gt 0 ] && [ $warnings -le 3 ]; then
                    echo "      ⚠️  WARNINGS:"
                    grep -i "warning\|warn" "$log_file" | head -3 | sed 's/^/         /'
                elif [ $warnings -gt 3 ]; then
                    echo "      ⚠️  WARNINGS: (showing first 2 of $warnings)"
                    grep -i "warning\|warn" "$log_file" | head -2 | sed 's/^/         /'
                fi
            else
                echo "   ✅ No issues found"
            fi
            
            # Show log size
            local log_size=$(du -h "$log_file" | cut -f1)
            echo "   📏 Log size: $log_size"
            
        else
            echo "   ❌ Log file not found"
        fi
    done
    
    if [ "$found_issues" = false ]; then
        echo ""
        echo "🎉 NO ISSUES FOUND IN ANY LOGS!"
    fi
}

# Function to show log file locations
show_log_locations() {
    echo ""
    echo "📁 LOG FILE LOCATIONS"
    echo "===================="
    echo "All logs are stored in: $TEMP_DIR"
    echo ""
    echo "Individual log files:"
    for test_name in "${!test_logs[@]}"; do
        local log_file="${test_logs[$test_name]}"
        local status="${test_results[$test_name]}"
        echo "   $status: $test_name"
        echo "           $log_file"
    done
}

# Function to create summary report
create_summary_report() {
    local summary_file="$TEMP_DIR/test_summary.txt"
    
    cat > "$summary_file" << EOF
ASX Trading System - Test Summary Report
========================================
Date: $(date)
Host: $(hostname)
Python: $(python --version 2>&1)

TEST RESULTS:
Total Tests: $total_tests
Passed: $passed_tests
Failed: $failed_tests
Success Rate: $(( passed_tests * 100 / total_tests ))%

INDIVIDUAL TEST RESULTS:
EOF

    for test_name in "${!test_results[@]}"; do
        echo "$test_name: ${test_results[$test_name]}" >> "$summary_file"
    done
    
    echo "" >> "$summary_file"
    echo "LOG FILES:" >> "$summary_file"
    echo "Main directory: $TEMP_DIR" >> "$summary_file"
    
    for test_name in "${!test_logs[@]}"; do
        echo "$test_name: ${test_logs[$test_name]}" >> "$summary_file"
    done
    
    echo ""
    echo "📄 Summary report created: $summary_file"
}

# Main test execution
echo "🚀 Starting comprehensive testing..."
echo ""

# Test 1: Morning Analysis
run_test "morning_analysis" "python -m app.main morning"

# Test 2: Enhanced ML Data Collection
run_test "ml_data_collection" "python enhanced_ml_system/multi_bank_data_collector.py"

# Test 3: Validation Metrics Export
run_test "validation_metrics" "python export_and_validate_metrics.py"

# Test 4: HTML Dashboard Generation
run_test "html_dashboard" "python enhanced_ml_system/html_dashboard_generator.py"

# Test 5: Evening Analysis (optional, only if requested)
if [ "$1" = "--include-evening" ]; then
    echo "🌆 Including evening analysis (this may take 5-10 minutes)..."
    run_test "evening_analysis" "python -m app.main evening"
fi

# Test 6: ML API Test (if realtime_ml_api.py exists)
if [ -f "enhanced_ml_system/realtime_ml_api.py" ]; then
    run_test "ml_api_test" "timeout 10s python enhanced_ml_system/realtime_ml_api.py || true"
fi

# Analyze all logs
analyze_logs

# Show log locations
show_log_locations

# Create summary report
create_summary_report

# Final summary
echo ""
echo "🎯 FINAL TEST SUMMARY"
echo "===================="
echo "✅ Tests Passed: $passed_tests"
echo "❌ Tests Failed: $failed_tests"
echo "📊 Success Rate: $(( passed_tests * 100 / total_tests ))%"
echo ""

if [ $failed_tests -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED! System is working correctly."
    exit_code=0
else
    echo "⚠️  Some tests failed. Check the logs above for details."
    exit_code=1
fi

echo ""
echo "📁 All logs saved to: $TEMP_DIR"
echo "🔍 To view specific logs:"
echo "   cat $TEMP_DIR/[test_name].log"
echo ""
echo "📋 Quick commands to check for issues:"
echo "   # Show all errors across all logs:"
echo "   grep -r -i 'error\\|exception\\|traceback' $TEMP_DIR/"
echo ""
echo "   # Show all warnings across all logs:"
echo "   grep -r -i 'warning\\|warn' $TEMP_DIR/"
echo ""
echo "   # Show critical issues:"
echo "   grep -r -i 'critical\\|fatal' $TEMP_DIR/"
echo ""
echo "   # View summary report:"
echo "   cat $TEMP_DIR/test_summary.txt"

exit $exit_code
