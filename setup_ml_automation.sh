#!/bin/bash
"""
Complete ML Training Automation Setup
"""

echo "🚀 Setting Up ML Training Automation"
echo "=" * 50

# Current directory
SCRIPT_DIR=$(pwd)
echo "📍 Working directory: $SCRIPT_DIR"

# Setup morning routine (includes ML training)
echo -e "\n1️⃣ Setting up morning routine automation..."
if [ -f "helpers/setup_morning_cron.sh" ]; then
    bash helpers/setup_morning_cron.sh
    echo "✅ Morning routine will run every 30 minutes"
else
    echo "❌ Morning cron setup not found"
fi

# Create evening routine cron
echo -e "\n2️⃣ Setting up evening routine automation..."

# Detect virtual environment
if [ -f "venv/bin/activate" ]; then
    VENV_PATH="$SCRIPT_DIR/venv"
elif [ -f ".venv/bin/activate" ]; then
    VENV_PATH="$SCRIPT_DIR/.venv"
else
    echo "⚠️ No virtual environment found, using system Python"
    VENV_PATH=""
fi

# Create evening cron job
if [ -n "$VENV_PATH" ]; then
    EVENING_CRON="0 18 * * * cd $SCRIPT_DIR && source $VENV_PATH/bin/activate && export PYTHONPATH=$SCRIPT_DIR && python -m app.main evening >> logs/evening_cron.log 2>&1"
else
    EVENING_CRON="0 18 * * * cd $SCRIPT_DIR && export PYTHONPATH=$SCRIPT_DIR && python -m app.main evening >> logs/evening_cron.log 2>&1"
fi

# Remove existing evening entries
crontab -l 2>/dev/null | grep -v 'app.main evening' | crontab - 2>/dev/null || true

# Add evening routine
(crontab -l 2>/dev/null; echo "# Automated Evening Routine - Daily at 6 PM"; echo "$EVENING_CRON") | crontab -

echo "✅ Evening routine will run daily at 6 PM"

# Create logs directory
mkdir -p logs

echo -e "\n3️⃣ Current automation schedule:"
echo "📋 Active cron jobs:"
crontab -l | grep -E 'morning|evening|app.main' || echo "No trading automation found"

echo -e "\n4️⃣ Manual commands:"
echo "🌅 Morning routine: python -m app.main morning"
echo "🌅 Evening routine: python -m app.main evening"
echo "🧠 Force training: python diagnose_ml_training.py --force"

echo -e "\n5️⃣ Monitoring:"
echo "📊 Check logs: tail -f logs/morning_cron.log"
echo "📊 Check logs: tail -f logs/evening_cron.log"
echo "📊 Check cron: crontab -l"

echo -e "\n✅ ML Training automation setup complete!"
echo "🎯 Training will now happen automatically:"
echo "   - Every 30 minutes (morning routine)"
echo "   - Daily at 6 PM (evening routine)"
echo "   - When 5+ new samples are available"
echo "   - When 12+ hours since last training"
