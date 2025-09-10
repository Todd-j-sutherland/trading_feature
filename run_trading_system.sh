#!/bin/bash

# Simple Trading System Runner
# Run all required trading processes manually or setup cron jobs

echo "🚀 TRADING SYSTEM RUNNER"
echo "========================"
echo "Date: $(date)"
echo ""

# Configuration
REMOTE_HOST="root@170.64.199.151"
REMOTE_PATH="/root/test"
VENV_PATH="/root/trading_venv"

# Function to run remote command
run_remote() {
    local cmd="$1"
    local description="$2"
    
    echo "🔄 $description..."
    ssh $REMOTE_HOST "cd $REMOTE_PATH && source $VENV_PATH/bin/activate && export PYTHONPATH=$REMOTE_PATH && $cmd"
    
    if [ $? -eq 0 ]; then
        echo "✅ $description completed successfully"
    else
        echo "❌ $description failed"
    fi
    echo ""
}

# Function to setup cron jobs
setup_cron() {
    echo "🔧 Setting up cron jobs on remote server..."
    ssh $REMOTE_HOST "cd $REMOTE_PATH && bash setup_market_aware_cron.sh"
    echo "✅ Cron jobs setup completed"
    echo ""
}

# Function to run single prediction cycle
run_predictions() {
    echo "🎯 Running single prediction cycle..."
    run_remote "python production/cron/fixed_price_mapping_system.py" "Market Predictions"
}

# Function to run morning analysis
run_morning_analysis() {
    echo "🌅 Running morning analysis..."
    run_remote "python enhanced_morning_analyzer_with_ml.py" "Morning Analysis with ML"
}

# Function to run outcome evaluation
run_evaluation() {
    echo "📊 Running outcome evaluation..."
    run_remote "bash evaluate_predictions_comprehensive.sh" "Prediction Evaluation"
}

# Function to check system status
check_status() {
    echo "📋 Checking system status..."
    ssh $REMOTE_HOST "cd $REMOTE_PATH && echo 'Cron service:' && systemctl is-active cron && echo 'Active cron jobs:' && crontab -l | grep -E '^[^#]' | wc -l && echo 'Today predictions:' && sqlite3 data/trading_predictions.db \"SELECT COUNT(*) FROM predictions WHERE date(prediction_timestamp) = date('now', 'localtime')\""
    echo ""
}

# Main menu
echo "Select an option:"
echo "1) Setup cron jobs (automatic scheduling)"
echo "2) Run single prediction cycle"
echo "3) Run morning analysis"
echo "4) Run outcome evaluation"
echo "5) Run all processes once"
echo "6) Check system status"
echo "0) Exit"
echo ""

read -p "Enter choice [0-6]: " choice

case $choice in
    1)
        setup_cron
        ;;
    2)
        run_predictions
        ;;
    3)
        run_morning_analysis
        ;;
    4)
        run_evaluation
        ;;
    5)
        echo "🚀 Running all processes..."
        run_morning_analysis
        run_predictions
        run_evaluation
        ;;
    6)
        check_status
        ;;
    0)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo "🎯 Trading system runner completed!"
