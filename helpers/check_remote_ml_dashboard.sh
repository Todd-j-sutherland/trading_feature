#!/bin/bash

# Enhanced ML Metrics Dashboard Status Check
echo "🧠 ENHANCED DASHBOARD ML METRICS STATUS"
echo "======================================="

# Check if dashboard is running
dashboard_pid=$(ssh -i ~/.ssh/id_rsa root@170.64.199.151 'pgrep -f "streamlit run app/dashboard/enhanced_main.py"')

if [ -n "$dashboard_pid" ]; then
    echo "✅ Enhanced Dashboard: Running (PID: $dashboard_pid)"
    echo "🌐 URL: http://170.64.199.151:8501"
    echo ""
    
    # Get current ML metrics from remote server
    echo "📊 CURRENT ML PERFORMANCE METRICS:"
    echo "-----------------------------------"
    
    ssh -i ~/.ssh/id_rsa root@170.64.199.151 'cd /root/test && source /root/trading_venv/bin/activate && export PYTHONPATH=/root/test && python -c "
import json
from pathlib import Path

# Load latest ML data
perf_file = Path(\"data_v2/data/ml_performance/ml_performance_history.json\")
model_file = Path(\"data_v2/data/ml_performance/model_metrics_history.json\")

if perf_file.exists():
    with open(perf_file, \"r\") as f:
        performance_data = json.load(f)
    
    latest = performance_data[-1]
    recent_7days = performance_data[-7:]
    
    print(f\"📈 Latest Performance ({latest['date']}):\")
    print(f\"   Success Rate: {(latest['successful_trades'] / latest['total_trades'] * 100) if latest['total_trades'] > 0 else 0:.1f}%\")
    print(f\"   Model Confidence: {latest.get('model_confidence', 0) * 100:.1f}%\")
    print(f\"   Trades: {latest['successful_trades']}/{latest['total_trades']}\")
    
    # Recent week performance
    week_trades = sum(e['total_trades'] for e in recent_7days)
    week_success = sum(e['successful_trades'] for e in recent_7days)
    week_rate = (week_success / week_trades * 100) if week_trades > 0 else 0
    
    print(f\"\\n📊 7-Day Performance:\")
    print(f\"   Success Rate: {week_rate:.1f}%\")
    print(f\"   Total Trades: {week_trades}\")
    print(f\"   Successful: {week_success}\")
    
    # Overall stats
    total_trades = sum(e['total_trades'] for e in performance_data)
    total_success = sum(e['successful_trades'] for e in performance_data)
    overall_rate = (total_success / total_trades * 100) if total_trades > 0 else 0
    
    print(f\"\\n💹 Overall Performance:\")
    print(f\"   Success Rate: {overall_rate:.1f}%\")
    print(f\"   Total Trades: {total_trades:,}\")
    print(f\"   Data Points: {len(performance_data)} days\")

if model_file.exists():
    with open(model_file, \"r\") as f:
        model_metrics = json.load(f)
    
    latest_model = model_metrics[-1]
    
    print(f\"\\n🎯 Latest Model Training:\")
    print(f\"   Validation Accuracy: {latest_model.get('validation_accuracy', 0) * 100:.2f}%\")
    print(f\"   Cross-Validation: {latest_model.get('cross_validation_score', 0) * 100:.2f}%\")
    print(f\"   Training Samples: {latest_model.get('training_samples', 0):,}\")
    print(f\"   Model Version: {latest_model.get('model_version', 'N/A')}\")
    print(f\"   Training Sessions: {len(model_metrics)}\")
"'
    
    echo ""
    echo "🎨 DASHBOARD FEATURES AVAILABLE:"
    echo "--------------------------------"
    echo "✅ Accuracy & Confidence Progression Charts"
    echo "✅ Model Training Progress Visualization"
    echo "✅ Trading Performance Analysis"
    echo "✅ Detailed Performance Logs"
    echo "✅ Real-time Metrics Cards"
    echo "✅ Interactive Plotly Charts"
    echo "✅ Memory-Optimized Analysis"
    
    echo ""
    echo "📋 NAVIGATION INSTRUCTIONS:"
    echo "--------------------------"
    echo "1. Open: http://170.64.199.151:8501"
    echo "2. Click on 'Learning Metrics' tab"
    echo "3. View comprehensive ML performance data"
    echo "4. Explore interactive charts and metrics"
    
else
    echo "❌ Enhanced Dashboard: Not Running"
    echo "💡 To start: Run enhanced dashboard startup script"
fi

echo ""
echo "🔧 SYSTEM STATUS:"
echo "----------------"
ssh -i ~/.ssh/id_rsa root@170.64.199.151 'echo "Memory: $(free -m | awk "NR==2{printf \"%.1f%%\", \$3/\$2*100}")" && echo "Load: $(uptime | awk -F"load average:" "{print \$2}" | awk "{print \$1}" | sed "s/,//")" && echo "Processes: $(ps aux | grep -c python)"'
