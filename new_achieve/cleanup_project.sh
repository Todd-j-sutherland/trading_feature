#!/bin/bash

# 🧹 COMPREHENSIVE PROJECT CLEANUP SCRIPT
# This script archives redundant files identified in the analysis
# All files are MOVED (not deleted) to preserve them for potential future use

set -e  # Exit on any error

echo "🔍 Starting Comprehensive Project Cleanup..."
echo "📍 Working directory: $(pwd)"

# Create archive directory structure
echo "📁 Creating archive structure..."
mkdir -p archive/unused_by_main/{root_scripts,dashboard_files,ml_files,test_files,helper_files,duplicates}

# Phase 1: Handle Duplicate Files
echo "🚨 Phase 1: Archiving duplicate files..."

# Archive root duplicates in favor of organized app/ versions
if [ -f "enhanced_evening_analyzer_with_ml.py" ]; then
    mv enhanced_evening_analyzer_with_ml.py archive/duplicates/
    echo "✅ Archived duplicate: enhanced_evening_analyzer_with_ml.py"
fi

if [ -f "enhanced_morning_analyzer_with_ml.py" ]; then
    mv enhanced_morning_analyzer_with_ml.py archive/duplicates/
    echo "✅ Archived duplicate: enhanced_morning_analyzer_with_ml.py"
fi

if [ -f "dashboard.py" ]; then
    mv dashboard.py archive/duplicates/
    echo "✅ Archived duplicate: dashboard.py"
fi

# Phase 2: Archive Root Scripts (54 files)
echo "📜 Phase 2: Archiving redundant root scripts..."

# Legacy/Alternative API servers
if [ -f "api_server.py" ]; then mv api_server.py archive/unused_by_main/root_scripts/; echo "✅ Archived: api_server.py"; fi
if [ -f "integrated_ml_api_server.py" ]; then mv integrated_ml_api_server.py archive/unused_by_main/root_scripts/; echo "✅ Archived: integrated_ml_api_server.py"; fi

# Standalone tools not used by app.main
if [ -f "automated_technical_updater.py" ]; then mv automated_technical_updater.py archive/unused_by_main/root_scripts/; echo "✅ Archived: automated_technical_updater.py"; fi
if [ -f "process_coordinator.py" ]; then mv process_coordinator.py archive/unused_by_main/root_scripts/; echo "✅ Archived: process_coordinator.py"; fi
if [ -f "manage_email_alerts.py" ]; then mv manage_email_alerts.py archive/unused_by_main/root_scripts/; echo "✅ Archived: manage_email_alerts.py"; fi
if [ -f "technical_analysis_engine.py" ]; then mv technical_analysis_engine.py archive/unused_by_main/root_scripts/; echo "✅ Archived: technical_analysis_engine.py"; fi
if [ -f "remote_ml_analysis.py" ]; then mv remote_ml_analysis.py archive/unused_by_main/root_scripts/; echo "✅ Archived: remote_ml_analysis.py"; fi

# Test scripts
if [ -f "run_comprehensive_tests.py" ]; then mv run_comprehensive_tests.py archive/unused_by_main/root_scripts/; echo "✅ Archived: run_comprehensive_tests.py"; fi
if [ -f "run_enhanced_ml_tests.py" ]; then mv run_enhanced_ml_tests.py archive/unused_by_main/root_scripts/; echo "✅ Archived: run_enhanced_ml_tests.py"; fi
if [ -f "enhanced_ml_test_integration.py" ]; then mv enhanced_ml_test_integration.py archive/unused_by_main/root_scripts/; echo "✅ Archived: enhanced_ml_test_integration.py"; fi
if [ -f "test_reddit_sentiment.py" ]; then mv test_reddit_sentiment.py archive/unused_by_main/root_scripts/; echo "✅ Archived: test_reddit_sentiment.py"; fi
if [ -f "quick_ml_status.py" ]; then mv quick_ml_status.py archive/unused_by_main/root_scripts/; echo "✅ Archived: quick_ml_status.py"; fi

# Integration scripts (one-time use)
if [ -f "integrate_enhanced_ml.py" ]; then mv integrate_enhanced_ml.py archive/unused_by_main/root_scripts/; echo "✅ Archived: integrate_enhanced_ml.py"; fi
if [ -f "integrate_technical_scores_evening.py" ]; then mv integrate_technical_scores_evening.py archive/unused_by_main/root_scripts/; echo "✅ Archived: integrate_technical_scores_evening.py"; fi

# Safety/compatibility scripts
if [ -f "safe_ml_runner.py" ]; then mv safe_ml_runner.py archive/unused_by_main/root_scripts/; echo "✅ Archived: safe_ml_runner.py"; fi
if [ -f "safe_ml_runner_with_cleanup.py" ]; then mv safe_ml_runner_with_cleanup.py archive/unused_by_main/root_scripts/; echo "✅ Archived: safe_ml_runner_with_cleanup.py"; fi
if [ -f "create_compatible_ml_model.py" ]; then mv create_compatible_ml_model.py archive/unused_by_main/root_scripts/; echo "✅ Archived: create_compatible_ml_model.py"; fi
if [ -f "check_ml_dependencies.py" ]; then mv check_ml_dependencies.py archive/unused_by_main/root_scripts/; echo "✅ Archived: check_ml_dependencies.py"; fi

# Start scripts (redundant - use app.main commands instead)
if [ -f "start_complete_ml_system.sh" ]; then mv start_complete_ml_system.sh archive/unused_by_main/root_scripts/; echo "✅ Archived: start_complete_ml_system.sh"; fi
if [ -f "start_complete_ml_system_dev.sh" ]; then mv start_complete_ml_system_dev.sh archive/unused_by_main/root_scripts/; echo "✅ Archived: start_complete_ml_system_dev.sh"; fi
if [ -f "start_integrated_ml_system.sh" ]; then mv start_integrated_ml_system.sh archive/unused_by_main/root_scripts/; echo "✅ Archived: start_integrated_ml_system.sh"; fi
if [ -f "start_dashboard.sh" ]; then mv start_dashboard.sh archive/unused_by_main/root_scripts/; echo "✅ Archived: start_dashboard.sh"; fi
if [ -f "run_safe_evening.sh" ]; then mv run_safe_evening.sh archive/unused_by_main/root_scripts/; echo "✅ Archived: run_safe_evening.sh"; fi
if [ -f "setup.sh" ]; then mv setup.sh archive/unused_by_main/root_scripts/; echo "✅ Archived: setup.sh"; fi
if [ -f "organize_project.sh" ]; then mv organize_project.sh archive/unused_by_main/root_scripts/; echo "✅ Archived: organize_project.sh"; fi
if [ -f "fix_remote_metadata.sh" ]; then mv fix_remote_metadata.sh archive/unused_by_main/root_scripts/; echo "✅ Archived: fix_remote_metadata.sh"; fi

# Documentation files that are outdated or redundant
if [ -f "comprehensive_analysis.py" ]; then mv comprehensive_analysis.py archive/unused_by_main/root_scripts/; echo "✅ Archived: comprehensive_analysis.py"; fi

# Phase 3: Archive Unused Dashboard Files
echo "📊 Phase 3: Archiving unused dashboard files..."

# Old dashboard main file
if [ -d "app/dashboard/views" ]; then
    mv app/dashboard/views archive/unused_by_main/dashboard_files/
    echo "✅ Archived: app/dashboard/views/"
fi

if [ -f "app/dashboard/main.py" ]; then
    mv app/dashboard/main.py archive/unused_by_main/dashboard_files/
    echo "✅ Archived: app/dashboard/main.py"
fi

if [ -f "app/dashboard/ml_trading_dashboard.py" ]; then
    mv app/dashboard/ml_trading_dashboard.py archive/unused_by_main/dashboard_files/
    echo "✅ Archived: app/dashboard/ml_trading_dashboard.py"
fi

# Unused components
if [ -f "app/dashboard/components/charts.py" ]; then
    mv app/dashboard/components/charts.py archive/unused_by_main/dashboard_files/
    echo "✅ Archived: app/dashboard/components/charts.py"
fi

if [ -f "app/dashboard/components/ui_components.py" ]; then
    mv app/dashboard/components/ui_components.py archive/unused_by_main/dashboard_files/
    echo "✅ Archived: app/dashboard/components/ui_components.py"
fi

# Phase 4: Archive Unused ML Files
echo "🧠 Phase 4: Archiving unused ML files..."

# Unused ML components
if [ -d "app/core/ml/ensemble" ]; then
    mv app/core/ml/ensemble archive/unused_by_main/ml_files/
    echo "✅ Archived: app/core/ml/ensemble/"
fi

if [ -f "app/core/ml/prediction/backtester.py" ]; then
    mv app/core/ml/prediction/backtester.py archive/unused_by_main/ml_files/
    echo "✅ Archived: app/core/ml/prediction/backtester.py"
fi

if [ -f "app/core/ml/prediction/predictor.py" ]; then
    mv app/core/ml/prediction/predictor.py archive/unused_by_main/ml_files/
    echo "✅ Archived: app/core/ml/prediction/predictor.py"
fi

if [ -f "app/core/ml/training/feature_engineering.py" ]; then
    mv app/core/ml/training/feature_engineering.py archive/unused_by_main/ml_files/
    echo "✅ Archived: app/core/ml/training/feature_engineering.py"
fi

# Phase 5: Archive Test Files
echo "🧪 Phase 5: Archiving test files..."

# Move entire test directories
if [ -d "tests" ]; then
    mv tests archive/unused_by_main/test_files/
    echo "✅ Archived: tests/ directory"
fi

if [ -d "enhanced_ml_system/testing" ]; then
    mv enhanced_ml_system/testing archive/unused_by_main/test_files/
    echo "✅ Archived: enhanced_ml_system/testing/"
fi

# Individual test files in helpers
if [ -f "helpers/test_models.py" ]; then
    mv helpers/test_models.py archive/unused_by_main/test_files/
    echo "✅ Archived: helpers/test_models.py"
fi

# Phase 6: Archive Helper Files
echo "🔧 Phase 6: Archiving helper files..."

# Data validation and setup helpers (one-time use)
if [ -d "helpers" ]; then
    # Keep helpers directory but move specific unused files
    for file in helpers/data_validation.py helpers/setup_*.py helpers/analysis_*.py; do
        if [ -f "$file" ]; then
            mv "$file" archive/unused_by_main/helper_files/
            echo "✅ Archived: $file"
        fi
    done
fi

# Archive unused trading files
echo "📈 Phase 7: Archiving unused trading files..."
if [ -f "app/core/trading/signals.py" ]; then
    mv app/core/trading/signals.py archive/unused_by_main/root_scripts/
    echo "✅ Archived: app/core/trading/signals.py"
fi

# Phase 8: Test Core Functionality
echo "✅ Phase 8: Testing core functionality..."

echo "🧪 Testing app.main imports..."
python3 -c "from app.main import main; print('✅ app.main imports successfully')" || {
    echo "❌ app.main import failed!"
    exit 1
}

echo "🧪 Testing basic commands..."
python3 -m app.main status || {
    echo "❌ app.main status command failed!"
    exit 1
}

# Summary
echo ""
echo "🎉 CLEANUP COMPLETE!"
echo ""
echo "📊 Summary:"
echo "   ✅ Archived duplicate files to archive/duplicates/"
echo "   ✅ Archived redundant root scripts to archive/unused_by_main/root_scripts/"
echo "   ✅ Archived unused dashboard files to archive/unused_by_main/dashboard_files/"
echo "   ✅ Archived unused ML files to archive/unused_by_main/ml_files/"
echo "   ✅ Archived test files to archive/unused_by_main/test_files/"
echo "   ✅ Archived helper files to archive/unused_by_main/helper_files/"
echo "   ✅ Core functionality verified"
echo ""
echo "🔍 Next Steps:"
echo "   1. Test your regular workflows: morning, evening, dashboard"
echo "   2. If anything is missing, check the archive/ directory"
echo "   3. Update your documentation and README files"
echo "   4. Consider configuring Reddit sentiment (see REDDIT_SENTIMENT_SETUP.md)"
echo ""
echo "📁 Files preserved in archive/ can be restored anytime if needed."
