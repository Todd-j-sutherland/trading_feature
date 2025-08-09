#!/bin/bash
# Simple SCP Push - No password required

echo "🚀 Simple SCP Push for Dashboard Fix"

# Get remote details
if [ $# -eq 2 ]; then
    REMOTE="$1"
    PATH="$2"
else
    read -p "Remote (user@host): " REMOTE
    read -p "Remote path: " PATH
fi

echo "📡 Pushing to: $REMOTE:$PATH"
echo ""

# Push files directly
echo "📤 Transferring files..."
scp fix_dashboard_ml_status.py "$REMOTE:$PATH/" && echo "✅ fix_dashboard_ml_status.py"
scp diagnose_ml_training.py "$REMOTE:$PATH/" && echo "✅ diagnose_ml_training.py" 
scp trigger_ml_training.py "$REMOTE:$PATH/" && echo "✅ trigger_ml_training.py"

echo ""
echo "✅ Files transferred!"
echo ""
echo "🎯 Now run on remote:"
echo "   ssh $REMOTE"
echo "   cd $PATH"
echo "   python fix_dashboard_ml_status.py"
