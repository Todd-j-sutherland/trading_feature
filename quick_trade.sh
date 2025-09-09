#!/bin/bash

# QUICK TRADING SYSTEM COMMANDS
# Simple commands to run trading processes

echo "🎯 QUICK TRADING COMMANDS"
echo "========================="

# Simple command functions
quick_predictions() {
    echo "🔮 Running predictions..."
    ssh root@170.64.199.151 "cd /root/test && source /root/trading_venv/bin/activate && python production/cron/fixed_price_mapping_system.py"
}

quick_analysis() {
    echo "🧠 Running morning analysis..."
    ssh root@170.64.199.151 "cd /root/test && source /root/trading_venv/bin/activate && python enhanced_morning_analyzer_with_ml.py"
}

quick_evaluation() {
    echo "📊 Running evaluation..."
    ssh root@170.64.199.151 "cd /root/test && bash evaluate_predictions_comprehensive.sh"
}

quick_status() {
    echo "📋 System status..."
    ssh root@170.64.199.151 "cd /root/test && echo 'Predictions today:' && sqlite3 data/trading_predictions.db \"SELECT COUNT(*) FROM predictions WHERE date(prediction_timestamp) = date('now', 'localtime')\" && echo 'Cron active:' && systemctl is-active cron"
}

# Parse command line argument
case "$1" in
    "predictions"|"pred"|"p")
        quick_predictions
        ;;
    "analysis"|"analyze"|"a")
        quick_analysis
        ;;
    "evaluation"|"eval"|"e")
        quick_evaluation
        ;;
    "status"|"stat"|"s")
        quick_status
        ;;
    "all")
        quick_analysis
        quick_predictions
        quick_evaluation
        ;;
    *)
        echo "Usage: $0 {predictions|analysis|evaluation|status|all}"
        echo ""
        echo "Quick commands:"
        echo "  $0 predictions  (or pred, p) - Run market predictions"
        echo "  $0 analysis     (or analyze, a) - Run morning analysis" 
        echo "  $0 evaluation   (or eval, e) - Run outcome evaluation"
        echo "  $0 status       (or stat, s) - Check system status"
        echo "  $0 all          - Run all processes"
        echo ""
        echo "Examples:"
        echo "  $0 p            # Quick predictions"
        echo "  $0 all          # Run everything"
        ;;
esac
