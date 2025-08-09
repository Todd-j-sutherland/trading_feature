#!/bin/bash
# SCP Push Script for ML Training Dashboard Fix
# Usage: ./scp_push_fix.sh username@hostname /remote/path

echo "🚀 SCP Push Script for Dashboard Fix"
echo "=" * 40

# SSH configuration
SSH_KEY="~/.ssh/id_rsa"
REMOTE_USER="root"
REMOTE_HOST="170.64.199.151" 
REMOTE_PATH="/root/test"  # Correct path to trading system

# Allow override via command line
if [ $# -eq 1 ]; then
    REMOTE_PATH="$1"
fi

REMOTE_USER_HOST="${REMOTE_USER}@${REMOTE_HOST}"

echo "📡 Remote target: $REMOTE_USER_HOST:$REMOTE_PATH"
echo "🔑 Using SSH key: $SSH_KEY"
echo ""

# Files to transfer
FILES_TO_PUSH=(
    "fix_dashboard_ml_status.py"
    "comprehensive_dashboard_fix.py"
    "diagnose_ml_training.py"
    "trigger_ml_training.py"
    "ml_training_scheduler.py"
    "setup_ml_automation.sh"
)

echo "📁 Files to transfer:"
for file in "${FILES_TO_PUSH[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (missing)"
    fi
done
echo ""

# Transfer files
echo "🔄 Starting file transfer..."

for file in "${FILES_TO_PUSH[@]}"; do
    if [ -f "$file" ]; then
        echo "📤 Transferring $file..."
        scp -i ~/.ssh/id_rsa "$file" "$REMOTE_USER_HOST:$REMOTE_PATH/"
        
        if [ $? -eq 0 ]; then
            echo "   ✅ $file transferred successfully"
        else
            echo "   ❌ Failed to transfer $file"
        fi
    else
        echo "   ⏭️ Skipping missing file: $file"
    fi
done

echo ""
echo "🔧 Making scripts executable on remote..."
ssh -i ~/.ssh/id_rsa "$REMOTE_USER_HOST" "cd $REMOTE_PATH && chmod +x *.py *.sh"

echo ""
echo "✅ Transfer complete!"
echo ""
echo "🎯 Next steps on your remote server:"
echo "   1. SSH into your server: ssh -i ~/.ssh/id_rsa $REMOTE_USER_HOST"
echo "   2. Navigate to directory: cd $REMOTE_PATH"
echo "   3. Fix dashboard: python fix_dashboard_ml_status.py"
echo "   4. Setup automation: ./setup_ml_automation.sh"
echo "   5. Restart dashboard: source venv/bin/activate && streamlit run dashboard.py"
echo ""
echo "🔍 To diagnose on remote:"
echo "   python diagnose_ml_training.py"
echo ""
echo "🚀 To force training on remote:"
echo "   python diagnose_ml_training.py --force"
