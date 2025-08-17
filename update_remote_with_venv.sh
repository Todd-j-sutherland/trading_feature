#!/bin/bash
# Update remote server data with virtual environment activation

REMOTE_HOST="170.64.199.151"
REMOTE_USER="root"
REMOTE_PATH="/root/test"

echo "🚀 Updating remote server data with virtual environment..."
echo "Server: ${REMOTE_USER}@${REMOTE_HOST}"
echo "Path: ${REMOTE_PATH}"
echo ""

# Function to run commands with venv activated
run_with_venv() {
    local cmd="$1"
    ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && source dashboard_venv/bin/activate && ${cmd}"
}

# 1. Copy the fixed dashboard file and enhanced analytics trigger
echo "📂 Copying dashboard and analytics files..."
scp comprehensive_table_dashboard.py ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
scp trigger_enhanced_analytics.py ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
scp cleanup_stale_data.py ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
scp TRADING_DATABASE_ARCHITECTURE.md ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

# 2. Backup remote database before any updates
echo "💾 Creating backup of remote database..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && cp data/trading_predictions.db data/trading_predictions.db.backup_$(date +%Y%m%d_%H%M%S)"

# 2b. Only copy database if explicitly requested (commented out by default)
# if [ -f "data/trading_predictions.db" ]; then
#     echo "🗄️ Copying local database..."
#     scp data/trading_predictions.db ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/data/
# else
#     echo "ℹ️ Local database not found, skipping database copy"
# fi
echo "⚠️  Database copy disabled to preserve remote trading history"

# 3. Install missing dependencies in venv
echo "📦 Installing/updating dependencies in virtual environment..."
run_with_venv "pip install streamlit pandas pathlib2"

# 4. Test dashboard import
echo "🧪 Testing dashboard import with virtual environment..."
if run_with_venv "python3 -c 'from comprehensive_table_dashboard import TradingDataDashboard; print(\"✅ Dashboard import successful!\")'" ; then
    echo "✅ Dashboard import test passed!"
else
    echo "❌ Dashboard import test failed!"
    exit 1
fi

# 5. Check database status
echo "🗄️ Checking database status..."
run_with_venv "python3 -c 'import sqlite3; conn=sqlite3.connect(\"data/trading_predictions.db\"); print(f\"Tables: {[t[0] for t in conn.execute(\\\"SELECT name FROM sqlite_master WHERE type=\\\"table\\\"\\\").fetchall()]}\"); conn.close()'"

# 6. Test streamlit availability and show enhanced analytics status
echo "🌐 Testing Streamlit availability..."
if run_with_venv "streamlit --version" ; then
    echo "✅ Streamlit is available in virtual environment!"
    
    # Check enhanced analytics status
    echo ""
    echo "📊 Checking enhanced analytics status..."
    run_with_venv "python3 -c 'import sqlite3; conn=sqlite3.connect(\"data/trading_predictions.db\"); enhanced_count=conn.execute(\"SELECT COUNT(*) FROM enhanced_outcomes\").fetchone()[0]; perf_count=conn.execute(\"SELECT COUNT(*) FROM model_performance\").fetchone()[0]; print(f\"🎯 Enhanced Outcomes: {enhanced_count}\"); print(f\"📈 Model Performance: {perf_count}\"); conn.close()'"
    
    echo ""
    echo "🎉 Ready to run dashboard with enhanced analytics:"
    echo "   ssh ${REMOTE_USER}@${REMOTE_HOST}"
    echo "   cd ${REMOTE_PATH}"
    echo "   source dashboard_venv/bin/activate"
    echo "   streamlit run comprehensive_table_dashboard.py"
    echo ""
    echo "💡 Data management commands:"
    echo "   🧹 Clean stale data: python3 cleanup_stale_data.py --days 7"
    echo "   📊 Show data age: python3 cleanup_stale_data.py --summary"
    echo "   🎯 Trigger enhanced analytics: python3 trigger_enhanced_analytics.py"
    echo "   📖 View documentation: cat TRADING_DATABASE_ARCHITECTURE.md"
else
    echo "❌ Streamlit not available - installing..."
    run_with_venv "pip install streamlit"
fi

echo ""
echo "✅ Remote update completed!"
