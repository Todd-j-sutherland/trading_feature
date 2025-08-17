#!/bin/bash
# Deploy dashboard fix to remote server

REMOTE_HOST="your-remote-server"
REMOTE_USER="root"
REMOTE_PATH="/root/test"
LOCAL_FILE="comprehensive_table_dashboard.py"

echo "🚀 Deploying dashboard fixes to remote server..."

# Backup the remote file first
echo "📋 Creating backup of remote file..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cp ${REMOTE_PATH}/${LOCAL_FILE} ${REMOTE_PATH}/${LOCAL_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# Copy the fixed file
echo "📂 Copying fixed dashboard file..."
scp ${LOCAL_FILE} ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

# Verify the copy
echo "✅ Verifying deployment..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && python3 -c 'from comprehensive_table_dashboard import TradingDataDashboard; print(\"Import successful!\")'"

echo "🎉 Deployment complete!"
echo "💡 To test: ssh to remote and run 'streamlit run comprehensive_table_dashboard.py'"
