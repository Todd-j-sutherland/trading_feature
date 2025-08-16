#!/bin/bash
# Update remote server with fixed dashboard and data

REMOTE_HOST="170.64.199.151"
REMOTE_USER="root"
REMOTE_PATH="/root/test"

echo "🚀 UPDATING REMOTE SERVER DATA AND DASHBOARD"
echo "=" * 60
echo "🌐 Remote: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"
echo "⏰ Time: $(date)"
echo

# 1. Backup remote files first
echo "📋 Creating backups on remote server..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && \
    cp comprehensive_table_dashboard.py comprehensive_table_dashboard.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'No existing dashboard to backup'"

# 2. Copy fixed dashboard file
echo "📂 Copying fixed dashboard file..."
scp comprehensive_table_dashboard.py ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
if [ $? -eq 0 ]; then
    echo "✅ Dashboard file copied successfully"
else
    echo "❌ Failed to copy dashboard file"
    exit 1
fi

# 3. Copy database if it exists locally
if [ -f "data/trading_predictions.db" ]; then
    echo "📊 Copying database..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_PATH}/data"
    scp data/trading_predictions.db ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/data/
    if [ $? -eq 0 ]; then
        echo "✅ Database copied successfully"
    else
        echo "⚠️ Database copy failed, but continuing..."
    fi
else
    echo "ℹ️ No local database found to copy"
fi

# 4. Verify the dashboard import works
echo "🔍 Testing dashboard import on remote..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && python3 -c 'from comprehensive_table_dashboard import TradingDataDashboard; print(\"✅ Import successful!\")'"
if [ $? -eq 0 ]; then
    echo "✅ Dashboard import test passed"
else
    echo "❌ Dashboard import test failed"
    exit 1
fi

# 5. Check database status
echo "📊 Checking database status on remote..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && \
    if [ -f data/trading_predictions.db ]; then \
        echo '✅ Database file exists'; \
        sqlite3 data/trading_predictions.db 'SELECT COUNT(*) as table_count FROM sqlite_master WHERE type=\"table\";' | sed 's/^/📋 Tables: /'; \
        sqlite3 data/trading_predictions.db 'SELECT COUNT(*) as prediction_count FROM predictions;' 2>/dev/null | sed 's/^/🔮 Predictions: /' || echo '🔮 Predictions: 0 (table may not exist yet)'; \
        sqlite3 data/trading_predictions.db 'SELECT COUNT(*) as feature_count FROM enhanced_features;' 2>/dev/null | sed 's/^/🎯 Features: /' || echo '🎯 Features: 0 (table may not exist yet)'; \
    else \
        echo '⚠️ Database file not found'; \
    fi"

# 6. Test dashboard startup
echo "🧪 Testing dashboard startup (5 second test)..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && timeout 5 python3 -c '
import streamlit as st
from comprehensive_table_dashboard import TradingDataDashboard
import sys

try:
    dashboard = TradingDataDashboard(\"/root/test\")
    print(\"✅ Dashboard initialization successful\")
    print(f\"✅ analysis_results initialized: {hasattr(dashboard, \\\"analysis_results\\\")}\")
    print(f\"✅ Database path: {dashboard.main_db_path}\")
    print(f\"✅ Database exists: {dashboard.main_db_path.exists()}\")
except Exception as e:
    print(f\"❌ Dashboard initialization failed: {e}\")
    sys.exit(1)
' 2>&1"

if [ $? -eq 0 ]; then
    echo "✅ Dashboard startup test passed"
else
    echo "❌ Dashboard startup test failed"
fi

# 7. Show remote directory status
echo "📁 Remote directory status:"
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && \
    echo 'Files in /root/test:' && \
    ls -la *.py | head -5 && \
    echo && \
    echo 'Data directory:' && \
    ls -la data/ 2>/dev/null || echo 'No data directory'"

echo
echo "🎉 UPDATE COMPLETE!"
echo "=" * 60
echo "💡 To run dashboard: ssh ${REMOTE_USER}@${REMOTE_HOST} 'cd ${REMOTE_PATH} && streamlit run comprehensive_table_dashboard.py'"
echo "💡 To check logs: ssh ${REMOTE_USER}@${REMOTE_HOST} 'cd ${REMOTE_PATH} && tail -f *.log'"
