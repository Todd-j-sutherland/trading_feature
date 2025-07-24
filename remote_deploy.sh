#!/bin/bash

# Remote Server Deployment Script for Trading Analysis System
# Optimized for memory-constrained environments

set -e

SERVER="root@170.64.199.151"
SSH_KEY="~/.ssh/id_rsa"
REMOTE_DIR="/root/test"
VENV_DIR="/root/trading_venv"

echo "🚀 Deploying Trading Analysis System to Remote Server..."
echo "📍 Server: $SERVER"
echo "📁 Remote Directory: $REMOTE_DIR"

# Function to run remote commands
run_remote() {
    ssh -i "$SSH_KEY" "$SERVER" "$1"
}

# Check server resources
echo "📊 Checking server resources..."
run_remote "free -h && df -h"

# Create environment configuration for memory-constrained server
echo "⚙️ Setting up environment configuration..."
run_remote "cat > $REMOTE_DIR/.env << 'EOF'
# Memory optimization for remote server (2GB RAM limit)
SKIP_TRANSFORMERS=1
USE_TWO_STAGE_ANALYSIS=1
PYTHONPATH=$REMOTE_DIR
LOG_LEVEL=INFO

# Data directories
DATA_DIR=$REMOTE_DIR/data
MODELS_DIR=$REMOTE_DIR/data/ml_models

# Performance settings
MAX_WORKERS=2
BATCH_SIZE=10
CACHE_SIZE=100

# News collection settings
NEWS_INTERVAL=30
MAX_NEWS_ARTICLES=10

# Database settings
DB_PATH=$REMOTE_DIR/data/trading.db

# Two-stage analysis settings
SENTIMENT_CACHE_DIR=$REMOTE_DIR/data/sentiment_cache
FINBERT_SCHEDULE_HOUR=18
EOF"

# Run morning routine with optimized settings
echo "🌅 Running morning routine on remote server..."
run_remote "cd $REMOTE_DIR && source $VENV_DIR/bin/activate && export SKIP_TRANSFORMERS=1 && export PYTHONPATH=$REMOTE_DIR && python -m app.main morning"

# Check if smart collector is running
echo "🔍 Checking background processes..."
run_remote "ps aux | grep news_collector | grep -v grep || echo 'Smart collector not running'"

# Show system status
echo "📈 System status:"
run_remote "cd $REMOTE_DIR && source $VENV_DIR/bin/activate && export SKIP_TRANSFORMERS=1 && export PYTHONPATH=$REMOTE_DIR && python -c 'import app; print(\"✅ System operational\")'"

echo "✅ Remote deployment complete!"
echo ""
echo "🎯 Next steps:"
echo "   • Monitor: ssh -i $SSH_KEY $SERVER 'ps aux | grep news_collector'"
echo "   • News update: ssh -i $SSH_KEY $SERVER 'cd $REMOTE_DIR && python -m app.main news'"
echo "   • Dashboard: ssh -i $SSH_KEY $SERVER 'cd $REMOTE_DIR && python -m app.main dashboard'"
echo "   • Logs: ssh -i $SSH_KEY $SERVER 'tail -f $REMOTE_DIR/logs/dashboard.log'"
