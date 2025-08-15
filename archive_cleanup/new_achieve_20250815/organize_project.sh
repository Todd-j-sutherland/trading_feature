#!/usr/bin/env bash

# Project Organization Script
# Based on PROJECT_ORGANIZATION_PLAN.md

set -e

echo "🗂️ ASX Trading System - Project Organization"
echo "============================================"

# Create directories if they don't exist
mkdir -p archive helpers

echo "📋 This script will organize your project files according to the analysis:"
echo ""
echo "📁 ARCHIVE (~50 files): Legacy documentation and superseded scripts"
echo "🛠️ HELPERS (~40 files): Utility scripts for monitoring, testing, management"
echo "🎯 CORE (~25 files): Essential system files remain in root"
echo ""

read -p "🤔 Do you want to see the file categorization plan? (y/n): " show_plan

if [[ $show_plan == "y" || $show_plan == "Y" ]]; then
    echo ""
    echo "📚 Files to ARCHIVE (Legacy/Historical):"
    echo "   • BACKEND_CONNECTION_FIXED.md"
    echo "   • CHART_ERROR_FIXES.md" 
    echo "   • CHART_FIXES_SUMMARY.md"
    echo "   • api_server_minimal.py"
    echo "   • old_useMLPredicitions.ts"
    echo "   • debug_chart_rendering.html"
    echo "   • phase1_cleanup.sh"
    echo "   • And ~40 more legacy files..."
    echo ""
    echo "🛠️ Files to move to HELPERS:"
    echo "   • advanced_memory_monitor.sh"
    echo "   • check_frontend_requirements.sh"
    echo "   • analyze_data_quality.py"
    echo "   • test_*.py scripts"
    echo "   • monitoring and validation scripts"
    echo "   • And ~35 more utility files..."
    echo ""
    echo "🎯 Files to KEEP in root:"
    echo "   • dashboard.py (PRIMARY DASHBOARD)"
    echo "   • api_server.py"
    echo "   • start_complete_ml_system.sh"
    echo "   • GOLDEN_STANDARD_DOCUMENTATION.md"
    echo "   • README.md"
    echo "   • And ~20 more core files..."
    echo ""
fi

read -p "🚀 Ready to organize files? This will move files according to the plan (y/n): " proceed

if [[ $proceed != "y" && $proceed != "Y" ]]; then
    echo "❌ Organization cancelled. No files moved."
    exit 0
fi

echo ""
echo "🗂️ Starting file organization..."

# Archive legacy documentation
echo "📚 Moving legacy documentation to archive/..."
mv BACKEND_CONNECTION_FIXED.md archive/ 2>/dev/null || true
mv CHART_ERROR_FIXES.md archive/ 2>/dev/null || true
mv CHART_FIXES_SUMMARY.md archive/ 2>/dev/null || true
mv COMPLETE_FLOW_VERIFICATION.md archive/ 2>/dev/null || true
mv DASHBOARD_FIXES_SUMMARY.md archive/ 2>/dev/null || true
mv DASHBOARD_IMPLEMENTATION_SUMMARY.md archive/ 2>/dev/null || true
mv DATABASE_CONSTRAINT_FIX_SUMMARY.md archive/ 2>/dev/null || true
mv DATA_RELIABILITY_SUCCESS.md archive/ 2>/dev/null || true
mv DEPLOYMENT_READY.md archive/ 2>/dev/null || true
mv DUAL_ML_BACKEND_SOLUTION.md archive/ 2>/dev/null || true
mv FRONTEND_IMPROVEMENTS_COMPLETE.md archive/ 2>/dev/null || true
mv HTML_DASHBOARD_DOCUMENTATION.md archive/ 2>/dev/null || true
mv REMOTE_DEPLOYMENT_SUCCESS.md archive/ 2>/dev/null || true
mv REMOTE_ML_SYSTEM_FIX_COMPLETE.md archive/ 2>/dev/null || true
mv SIMPLE_ML_DASHBOARD_GUIDE.md archive/ 2>/dev/null || true
mv SIMPLE_ML_INTEGRATION.md archive/ 2>/dev/null || true
mv TECHNICAL_ANALYSIS_FIX_SUMMARY.md archive/ 2>/dev/null || true
mv TECHNICAL_SCORES_FIX_COMPLETE.md archive/ 2>/dev/null || true
mv TECHNICAL_SCORES_SOLUTION_COMPLETE.md archive/ 2>/dev/null || true
mv TRADING_CHART_CONTAINER_FIXES.md archive/ 2>/dev/null || true
mv TRADING_CHART_ML_FIX.md archive/ 2>/dev/null || true
mv WEBSOCKET_FIX_SUMMARY.md archive/ 2>/dev/null || true

# Archive legacy Python files
echo "🐍 Moving legacy Python files to archive/..."
mv api_server_minimal.py archive/ 2>/dev/null || true
mv automated_data_collection.py archive/ 2>/dev/null || true
mv clear_dashboard_cache.py archive/ 2>/dev/null || true
mv create_enhanced_predictions.py archive/ 2>/dev/null || true
mv dashboard_sql_integration_template.py archive/ 2>/dev/null || true
mv fix_data_reliability.py archive/ 2>/dev/null || true
mv fix_ml_feature_mismatch.py archive/ 2>/dev/null || true
mv fix_technical_scores_integration.py archive/ 2>/dev/null || true
mv migrate_dashboard_to_sql.py archive/ 2>/dev/null || true
mv no_auth_email.py archive/ 2>/dev/null || true
mv no_auth_email_service.py archive/ 2>/dev/null || true
mv old_useMLPredicitions.ts archive/ 2>/dev/null || true
mv phase1_cleanup.py archive/ 2>/dev/null || true
mv pre_migration_validation.py archive/ 2>/dev/null || true
mv simple_email_sender.py archive/ 2>/dev/null || true
mv simple_email_test.py archive/ 2>/dev/null || true
mv sql_dashboard_test.py archive/ 2>/dev/null || true
mv system_email_test.py archive/ 2>/dev/null || true

# Archive legacy shell scripts and HTML files
echo "📜 Moving legacy scripts and test files to archive/..."
mv cleanup_and_evening.sh archive/ 2>/dev/null || true
mv phase1_cleanup.sh archive/ 2>/dev/null || true
mv setup_alpaca.py archive/ 2>/dev/null || true
mv start_dashboard_fresh.sh archive/ 2>/dev/null || true
mv start_ml_backend_improved.sh archive/ 2>/dev/null || true
mv venv_analysis.sh archive/ 2>/dev/null || true
mv debug_chart_rendering.html archive/ 2>/dev/null || true
mv test_chart_data.html archive/ 2>/dev/null || true
mv test_chart_direct.html archive/ 2>/dev/null || true
mv test_signals.html archive/ 2>/dev/null || true

# Move monitoring & system management to helpers
echo "📊 Moving monitoring and system management scripts to helpers/..."
mv advanced_memory_monitor.sh helpers/ 2>/dev/null || true
mv check_frontend_requirements.sh helpers/ 2>/dev/null || true
mv check_remote_ml_dashboard.sh helpers/ 2>/dev/null || true
mv cleanup_ports.sh helpers/ 2>/dev/null || true
mv cleanup_root_files.sh helpers/ 2>/dev/null || true
mv comprehensive_test_with_logs.sh helpers/ 2>/dev/null || true
mv deploy_memory_management.sh helpers/ 2>/dev/null || true
mv frontend_api_test.sh helpers/ 2>/dev/null || true
mv monitor_morning_cron.sh helpers/ 2>/dev/null || true
mv monitor_remote.sh helpers/ 2>/dev/null || true
mv performance_monitor.sh helpers/ 2>/dev/null || true
mv remote_deploy.sh helpers/ 2>/dev/null || true
mv remote_ml_feature_fix.sh helpers/ 2>/dev/null || true
mv restart_remote_ml_system.sh helpers/ 2>/dev/null || true
mv setup_frontend_ml_integration.py helpers/ 2>/dev/null || true
mv setup_morning_cron.sh helpers/ 2>/dev/null || true
mv setup_swap_remote.sh helpers/ 2>/dev/null || true
mv simple_test_with_logs.sh helpers/ 2>/dev/null || true
mv smart_evening_remote.sh helpers/ 2>/dev/null || true
mv sync_ml_models.sh helpers/ 2>/dev/null || true
mv upload_remote_host_fixes.sh helpers/ 2>/dev/null || true

# Move data management & validation to helpers
echo "📊 Moving data management scripts to helpers/..."
mv analyze_data_quality.py helpers/ 2>/dev/null || true
mv auto_backup_ml_data.sh helpers/ 2>/dev/null || true
mv check_metadata.py helpers/ 2>/dev/null || true
mv collect_reliable_data.py helpers/ 2>/dev/null || true
mv export_and_validate_metrics.py helpers/ 2>/dev/null || true
mv ml_data_validator.py helpers/ 2>/dev/null || true
mv update_ml_performance.py helpers/ 2>/dev/null || true
mv update_pending_predictions.py helpers/ 2>/dev/null || true
mv update_sql_predictions.py helpers/ 2>/dev/null || true
mv validate_system.py helpers/ 2>/dev/null || true

# Move development & testing to helpers
echo "🧪 Moving development and testing scripts to helpers/..."
mv test_api_endpoints.py helpers/ 2>/dev/null || true
mv test_app_main_integration.py helpers/ 2>/dev/null || true
mv test_dashboard.sh helpers/ 2>/dev/null || true
mv test_dashboard_components.py helpers/ 2>/dev/null || true
mv test_enhanced_ml_pipeline.py helpers/ 2>/dev/null || true
mv test_enhanced_simple.py helpers/ 2>/dev/null || true
mv test_evening_technical_integration.py helpers/ 2>/dev/null || true
mv test_performance_metrics.py helpers/ 2>/dev/null || true
mv test_quick_enhanced.py helpers/ 2>/dev/null || true
mv test_technical_isolated.py helpers/ 2>/dev/null || true
mv test_timestamps.py helpers/ 2>/dev/null || true
mv test_validation_framework.py helpers/ 2>/dev/null || true
mv verify_app_main_integration.py helpers/ 2>/dev/null || true
mv verify_complete_flow.py helpers/ 2>/dev/null || true
mv verify_dashboard.py helpers/ 2>/dev/null || true
mv verify_dashboard_data.py helpers/ 2>/dev/null || true

# Move some startup scripts to helpers
echo "🚀 Moving utility startup scripts to helpers/..."
mv start_ml_backend.sh helpers/ 2>/dev/null || true
mv start_ml_frontend.sh helpers/ 2>/dev/null || true
mv start_ml_frontend_production.sh helpers/ 2>/dev/null || true
mv start_remote_dashboard.sh helpers/ 2>/dev/null || true
mv start_smart_collector.sh helpers/ 2>/dev/null || true
mv stop_ml_backend.sh helpers/ 2>/dev/null || true

echo ""
echo "✅ File organization complete!"
echo ""
echo "📊 Summary:"
echo "   📁 Archive: $(ls archive/ 2>/dev/null | wc -l | tr -d ' ') files"
echo "   🛠️ Helpers: $(ls helpers/ 2>/dev/null | wc -l | tr -d ' ') files"
echo "   🎯 Root: $(ls -1 *.py *.sh *.md 2>/dev/null | wc -l | tr -d ' ') core files"
echo ""
echo "🎯 Key files in root:"
echo "   • dashboard.py (PRIMARY DASHBOARD)"
echo "   • api_server.py & integrated_ml_api_server.py"
echo "   • start_complete_ml_system.sh (MAIN STARTUP)"
echo "   • GOLDEN_STANDARD_DOCUMENTATION.md"
echo "   • README.md"
echo ""
echo "💡 Next steps:"
echo "   1. Test system startup: ./start_complete_ml_system.sh"
echo "   2. Test primary dashboard: streamlit run dashboard.py"
echo "   3. Update documentation references if needed"
echo "   4. Commit organized structure to git"
echo ""
echo "🚀 Your project is now organized and ready for improved maintainability!"
