#!/bin/bash

# Safe cleanup script for root directory files
# Removes debug, test, and temporary files that are no longer needed

echo "🧹 Starting root directory cleanup..."

# Debug files
echo "Removing debug files..."
rm -f debug_dashboard_ml.py
rm -f debug_dashboard_performance.py  
rm -f debug_enhanced_performance.py
rm -f debug_ml_display.py
rm -f demo_ml_metrics.py

# Test files
echo "Removing test files..."
rm -f test_confidence_fix.py
rm -f test_dashboard_components.py
rm -f test_dashboard_exact.py
rm -f test_fixed_components.py
rm -f test_ml_models.py
rm -f test_ml_progression_component.py
rm -f test_performance_component.py
rm -f test_performance_metrics.py
rm -f test_restored_system.py
rm -f test_technical_isolated.py
rm -f test_training_count.py

# Verification files (keeping these for diagnostics)
echo "Keeping verification files for future diagnostics..."
# rm -f verify_complete_flow.py
# rm -f verify_dashboard.py  
# rm -f verify_dashboard_data.py

# Validation files
echo "Removing validation files..."
rm -f validate_dashboard_data.py
rm -f validate_ml_data_with_env.py

# Cleanup scripts (one-time use)
echo "Removing cleanup scripts..."
rm -f cleanup_duplicate_predictions.py
rm -f cleanup_duplicates.py

# Fix scripts (completed their purpose)
echo "Removing fix scripts..."
rm -f fix_dashboard_data.py
rm -f fix_data_reliability.py
rm -f fix_ml_system.py
rm -f fix_progression_tracker.py
rm -f fix_timestamps.py

# Emergency scripts
echo "Removing emergency scripts..."
rm -f emergency_memory_recovery.sh
rm -f emergency_ml_fix.py

# Analysis scripts
echo "Removing analysis scripts..."
rm -f analyze_data_quality.py
rm -f export_and_validate_metrics.py
rm -f run_data_validation.py

# Old documentation
echo "Removing outdated documentation..."
rm -f COMPLETE_FLOW_VERIFICATION.md
rm -f DASHBOARD_FIXES_SUMMARY.md
rm -f DASHBOARD_IMPLEMENTATION_SUMMARY.md
rm -f DATA_RELIABILITY_SUCCESS.md
rm -f MEMORY_MANAGEMENT_SOLUTION.md
rm -f MIGRATION_ACTION_PLAN.md
rm -f REMOTE_CLEANUP_PLAN.md
rm -f TECHNICAL_ANALYSIS_FIX_SUMMARY.md
rm -f TECHNICAL_SCORES_FIX_COMPLETE.md
rm -f TESTING_IMPLEMENTATION_SUMMARY.md
rm -f asx_bank_analyzer_readme.md
rm -f chat-data-issue.md
rm -f improvements_needed.md
rm -f raw_data.md
rm -f testing_readme.md

# Temporary JSON files
echo "Removing temporary JSON files..."
rm -f pre_migration_validation_*.json
rm -f production_data_validation_*.json

# Old reports
echo "Removing old reports..."
rm -f ml_system_report_*.md

# Temporary directories (be careful with data)
echo "Removing temporary directories..."
rm -rf __pycache__
rm -f .DS_Store

# Optional: Remove data_temp if you're sure it's not needed
# rm -rf data_temp/

echo "✅ Root directory cleanup complete!"
echo "📊 Kept essential files: dashboard.py, app/, data/, requirements.txt, setup scripts"
echo "� Kept verification files: verify_*.py for future diagnostics"
echo "�🗑️ Removed: debug, test, validation, fix, and outdated documentation files"
