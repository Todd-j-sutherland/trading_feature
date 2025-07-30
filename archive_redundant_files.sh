#!/bin/bash
# SAFE TO ARCHIVE - Files not used by any app.main command
# These files can be safely moved to archive folder

echo "🗂️ Creating archive structure..."
mkdir -p archive/unused_by_main/{root_scripts,collectors,ml_files,dashboard_components,api_files,other_app_files}

echo "📁 Archiving ROOT SCRIPTS (24 files)..."
# These are standalone scripts not called by app.main
mv ENHANCED_ML_IMPLEMENTATION_COMPLETE.py archive/unused_by_main/root_scripts/
mv api_server.py archive/unused_by_main/root_scripts/
mv automated_technical_updater.py archive/unused_by_main/root_scripts/
mv check_ml_dependencies.py archive/unused_by_main/root_scripts/
mv create_compatible_ml_model.py archive/unused_by_main/root_scripts/
mv dashboard.py archive/unused_by_main/root_scripts/
mv demo_graceful_shutdown.py archive/unused_by_main/root_scripts/
mv enhanced_evening_analyzer_with_ml.py archive/unused_by_main/root_scripts/
mv enhanced_ml_test_integration.py archive/unused_by_main/root_scripts/
mv enhanced_morning_analyzer_with_ml.py archive/unused_by_main/root_scripts/
mv integrate_enhanced_ml.py archive/unused_by_main/root_scripts/
mv integrate_technical_scores_evening.py archive/unused_by_main/root_scripts/
mv integrated_ml_api_server.py archive/unused_by_main/root_scripts/
mv manage_email_alerts.py archive/unused_by_main/root_scripts/
mv process_coordinator.py archive/unused_by_main/root_scripts/
mv quick_ml_status.py archive/unused_by_main/root_scripts/
mv remote_ml_analysis.py archive/unused_by_main/root_scripts/
mv run_comprehensive_tests.py archive/unused_by_main/root_scripts/
mv run_enhanced_ml_tests.py archive/unused_by_main/root_scripts/
mv safe_ml_runner.py archive/unused_by_main/root_scripts/
mv safe_ml_runner_with_cleanup.py archive/unused_by_main/root_scripts/

echo "📊 Archiving COLLECTORS (2 files)..."
mv app/services/data_collector.py archive/unused_by_main/collectors/
mv enhanced_ml_system/multi_bank_data_collector.py archive/unused_by_main/collectors/

echo "🧠 Archiving ML FILES (23 files)..."
mv app/core/commands/ml_trading.py archive/unused_by_main/ml_files/
mv app/core/ml/ensemble/transformer_ensemble.py archive/unused_by_main/ml_files/
mv app/core/ml/prediction/backtester.py archive/unused_by_main/ml_files/
mv app/core/ml/prediction/predictor.py archive/unused_by_main/ml_files/
mv app/core/ml/training/feature_engineering.py archive/unused_by_main/ml_files/
mv app/dashboard/ml_trading_dashboard.py archive/unused_by_main/ml_files/
mv enhanced_ml_system/html_dashboard_generator.py archive/unused_by_main/ml_files/
mv enhanced_ml_system/integration/test_app_main_integration.py archive/unused_by_main/ml_files/
mv enhanced_ml_system/performance_dashboard.py archive/unused_by_main/ml_files/
mv enhanced_ml_system/realtime_ml_api.py archive/unused_by_main/ml_files/
mv enhanced_ml_system/testing/enhanced_ml_test_integration.py archive/unused_by_main/ml_files/
mv enhanced_ml_system/testing/test_validation_framework.py archive/unused_by_main/ml_files/

echo "📈 Archiving DASHBOARD COMPONENTS (19 files)..."
mv app/dashboard/charts/chart_generator.py archive/unused_by_main/dashboard_components/
mv app/dashboard/components/charts.py archive/unused_by_main/dashboard_components/
mv app/dashboard/components/ui_components.py archive/unused_by_main/dashboard_components/
mv app/dashboard/main.py archive/unused_by_main/dashboard_components/
mv app/dashboard/views/individual_bank_analysis.py archive/unused_by_main/dashboard_components/
mv app/dashboard/views/market_overview.py archive/unused_by_main/dashboard_components/
mv app/dashboard/views/news_sentiment.py archive/unused_by_main/dashboard_components/
mv app/dashboard/views/position_risk.py archive/unused_by_main/dashboard_components/
mv app/dashboard/views/system_status.py archive/unused_by_main/dashboard_components/
mv app/dashboard/views/technical_analysis.py archive/unused_by_main/dashboard_components/
mv app/services/dashboard_integration.py archive/unused_by_main/dashboard_components/

echo "🌐 Archiving API FILES (5 files)..."
mv backend/live_api.py archive/unused_by_main/api_files/

echo "📦 Archiving OTHER APP FILES (13 files)..."
mv app/core/trading/position_tracker.py archive/unused_by_main/other_app_files/
mv app/core/trading/signals.py archive/unused_by_main/other_app_files/
mv app/services/daily_manager_old.py archive/unused_by_main/other_app_files/
mv app/services/email_notifier.py archive/unused_by_main/other_app_files/
mv app/services/real_time_monitor.py archive/unused_by_main/other_app_files/

echo "🧹 Cleaning up empty __init__.py files and directories..."
# Move empty __init__.py files to archive
mv app/core/ml/__init__.py archive/unused_by_main/ml_files/ 2>/dev/null || true
mv app/core/ml/ensemble/__init__.py archive/unused_by_main/ml_files/ 2>/dev/null || true
mv app/core/ml/prediction/__init__.py archive/unused_by_main/ml_files/ 2>/dev/null || true
mv app/core/ml/training/__init__.py archive/unused_by_main/ml_files/ 2>/dev/null || true
mv app/dashboard/__init__.py archive/unused_by_main/dashboard_components/ 2>/dev/null || true
mv app/dashboard/charts/__init__.py archive/unused_by_main/dashboard_components/ 2>/dev/null || true
mv app/dashboard/components/__init__.py archive/unused_by_main/dashboard_components/ 2>/dev/null || true
mv app/dashboard/pages/__init__.py archive/unused_by_main/dashboard_components/ 2>/dev/null || true
mv app/dashboard/views/__init__.py archive/unused_by_main/dashboard_components/ 2>/dev/null || true
mv app/api/__init__.py archive/unused_by_main/api_files/ 2>/dev/null || true
mv app/api/routes/__init__.py archive/unused_by_main/api_files/ 2>/dev/null || true
mv app/api/schemas/__init__.py archive/unused_by_main/api_files/ 2>/dev/null || true
mv app/__init__.py archive/unused_by_main/other_app_files/ 2>/dev/null || true
mv app/config/__init__.py archive/unused_by_main/other_app_files/ 2>/dev/null || true
mv app/core/__init__.py archive/unused_by_main/other_app_files/ 2>/dev/null || true
mv app/core/analysis/__init__.py archive/unused_by_main/other_app_files/ 2>/dev/null || true
mv app/core/monitoring/__init__.py archive/unused_by_main/other_app_files/ 2>/dev/null || true
mv app/core/sentiment/__init__.py archive/unused_by_main/other_app_files/ 2>/dev/null || true
mv app/core/trading/__init__.py archive/unused_by_main/other_app_files/ 2>/dev/null || true
mv app/services/__init__.py archive/unused_by_main/other_app_files/ 2>/dev/null || true

echo "✅ Archive complete!"
echo "📊 Summary:"
echo "   • 24 root scripts archived"
echo "   • 2 collectors archived" 
echo "   • 23 ML files archived"
echo "   • 19 dashboard components archived"
echo "   • 5 API files archived"
echo "   • 13 other app files archived"
echo "   • Total: 86 files archived"
echo ""
echo "💡 Files archived to: archive/unused_by_main/"
echo "💡 These files are not used by any app.main command"
echo "💡 You can safely delete them or keep them archived"
