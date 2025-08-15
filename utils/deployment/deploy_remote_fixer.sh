#!/bin/bash
"""
Deploy Remote Database Fixer

This script copies the remote database fixer to your server and runs it.
"""

echo "🚀 DEPLOYING REMOTE DATABASE TIMESTAMP FIXER"
echo "=============================================="

# Remote server details
REMOTE_HOST="147.185.221.19"
REMOTE_USER="root"
REMOTE_PATH="/root/test"

echo "📤 Copying remote database fixer to server..."

# Copy the fixer script to remote server
scp -o StrictHostKeyChecking=no remote_database_fixer.py ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

if [ $? -eq 0 ]; then
    echo "✅ Successfully copied remote_database_fixer.py"
    
    echo "🌐 Running timestamp fix on remote server..."
    
    # Execute the fixer on remote server
    ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && python3 remote_database_fixer.py"
    
    if [ $? -eq 0 ]; then
        echo "✅ Remote timestamp fix completed"
        
        echo "📥 Downloading fix report..."
        
        # Download the report
        scp -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/remote_timestamp_fix_report.json ./
        
        if [ $? -eq 0 ]; then
            echo "✅ Downloaded remote fix report"
            echo "📄 Report available at: ./remote_timestamp_fix_report.json"
        else
            echo "⚠️  Could not download report (fix may have still succeeded)"
        fi
        
    else
        echo "❌ Remote timestamp fix failed"
        exit 1
    fi
    
else
    echo "❌ Failed to copy fixer to remote server"
    echo "💡 You may need to:"
    echo "   1. Check SSH key authentication"
    echo "   2. Manually copy remote_database_fixer.py to your server"
    echo "   3. Run it manually: python3 remote_database_fixer.py"
    exit 1
fi

echo ""
echo "🏆 REMOTE DATABASE SYNCHRONIZATION COMPLETE!"
echo "=============================================="
