#!/bin/bash
# Quick SCP Push for Dashboard Fix
# Usage: ./quick_scp_push.sh username@hostname /remote/path

echo "🚀 Quick SCP Push for ML Dashboard Fix"

if [ $# -ne 2 ]; then
    echo "Usage: $0 username@hostname /remote/path"
    echo "Example: $0 todd@192.168.1.100 /home/todd/trading_feature"
    exit 1
fi

REMOTE="$1"
REMOTE_PATH="$2"

echo "📡 Target: $REMOTE:$REMOTE_PATH"
echo ""

# Push the essential files
echo "📤 Transferring essential fix files..."

scp fix_dashboard_ml_status.py "$REMOTE:$REMOTE_PATH/"
scp diagnose_ml_training.py "$REMOTE:$REMOTE_PATH/"
scp trigger_ml_training.py "$REMOTE:$REMOTE_PATH/"

echo ""
echo "✅ Essential files transferred!"
echo ""
echo "🎯 Run on remote server:"
echo "   ssh $REMOTE"
echo "   cd $REMOTE_PATH"
echo "   python fix_dashboard_ml_status.py"
echo ""
