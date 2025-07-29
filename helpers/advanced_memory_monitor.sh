#!/bin/bash

# Advanced Memory Monitoring for Trading System
# Tracks memory usage and warns before OOM conditions

SERVER="root@170.64.199.151"
SSH_KEY="~/.ssh/id_rsa"

echo "📊 Advanced Memory Monitoring"
echo "============================"

ssh -i "$SSH_KEY" "$SERVER" '
echo "📅 $(date)"
echo ""

# Detailed memory analysis
echo "💾 DETAILED MEMORY ANALYSIS:"
echo "----------------------------"
free -m | awk "
    NR==1{print \"                 Total    Used    Free   Shared  Buff/Cache   Available\"}
    NR==2{
        total=\$2; used=\$3; free=\$4; shared=\$5; buffcache=\$6; available=\$7
        used_percent = used/total*100
        available_percent = available/total*100
        
        printf \"%-10s %7dMB %7dMB %7dMB %7dMB %10dMB %10dMB\n\", \"Memory:\", total, used, free, shared, buffcache, available
        printf \"%-10s %7s %6.1f%% %6.1f%% %7s %10s %9.1f%%\n\", \"Percent:\", \"\", used_percent, free/total*100, \"\", \"\", available_percent
        
        if (available_percent < 20) print \"⚠️  WARNING: Low available memory!\"
        if (available_percent < 10) print \"🚨 CRITICAL: OOM risk imminent!\"
    }
"

echo ""
echo "🔄 PROCESS MEMORY USAGE:"
echo "------------------------"
ps aux --sort=-%mem | awk "
    NR==1 {print \"PID     %MEM  COMMAND\"}
    NR<=6 && \$4>1.0 {printf \"%-8s %4.1f%%  %s\n\", \$2, \$4, \$11}
"

echo ""
echo "📈 SWAP USAGE:"
echo "--------------"
if [ -f /proc/swaps ] && [ -s /proc/swaps ]; then
    cat /proc/swaps
    swapon --show
else
    echo "No swap configured"
fi

echo ""
echo "🏥 SYSTEM HEALTH:"
echo "-----------------"
# Check for recent OOM kills
if dmesg | grep -i "out of memory\|killed process" | tail -3 | grep -q .; then
    echo "⚠️  Recent OOM events detected:"
    dmesg | grep -i "out of memory\|killed process" | tail -3
else
    echo "✅ No recent OOM kills detected"
fi

# Check load average
load=$(uptime | awk -F"load average:" "{print \$2}" | awk "{print \$1}" | sed "s/,//")
echo "📊 Load Average: $load"

# Trading system status
echo ""
echo "🤖 TRADING SYSTEM STATUS:"
echo "-------------------------"
smart_collector=$(ps aux | grep "news_collector --interval" | grep -v grep || echo "")
if [ -n "$smart_collector" ]; then
    echo "✅ Smart Collector: Running"
    echo "$smart_collector" | awk "{print \"   PID: \"\$2\", Memory: \"\$4\"%\"}"
else
    echo "❌ Smart Collector: Not Running"
fi

# Check Python processes
python_procs=$(ps aux | grep python | grep -v grep | wc -l)
echo "🐍 Python Processes: $python_procs"

# Check ML performance data availability
echo ""
echo "🧠 ML PERFORMANCE DATA STATUS:"
echo "-------------------------------"
if [ -f "/root/test/data_v2/data/ml_performance/ml_performance_history.json" ]; then
    file_size=$(stat -c%s "/root/test/data_v2/data/ml_performance/ml_performance_history.json" 2>/dev/null || echo "0")
        if [ "$file_size" -gt 100 ]; then
            echo "✅ ML Performance History: Available ${file_size} bytes"        # Get latest performance metrics from the correct location
        latest_record=$(tail -20 /root/test/data_v2/data/ml_performance/ml_performance_history.json | grep -A 20 '"date"' | tail -20)
        
        if echo "$latest_record" | grep -q '"total_trades"'; then
            latest_trades=$(echo "$latest_record" | grep '"total_trades"' | head -1 | sed 's/.*"total_trades": *\([0-9]*\).*/\1/')
            latest_successful=$(echo "$latest_record" | grep '"successful_trades"' | head -1 | sed 's/.*"successful_trades": *\([0-9]*\).*/\1/')
            latest_date=$(echo "$latest_record" | grep '"date"' | head -1 | sed 's/.*"date": *"\([^"]*\)".*/\1/')
            
            if [ "$latest_trades" -gt 0 ] && [ -n "$latest_trades" ]; then
                success_rate=$(echo "scale=1; $latest_successful * 100 / $latest_trades" | bc -l 2>/dev/null || echo "0.0")
                echo "📊 Latest Success Rate: ${success_rate}% - ${latest_successful}/${latest_trades} trades"
                echo "📅 Latest Analysis: $latest_date"
            fi
        fi
        
        # Check model training metrics
        if [ -f "/root/test/data_v2/data/ml_performance/model_metrics_history.json" ]; then
            model_size=$(stat -c%s "/root/test/data_v2/data/ml_performance/model_metrics_history.json" 2>/dev/null || echo "0")
            echo "✅ Model Training History: Available ${model_size} bytes"
            
            training_sessions=$(grep -c '"timestamp"' /root/test/data_v2/data/ml_performance/model_metrics_history.json 2>/dev/null || echo "0")
            echo "🔄 Training Sessions: $training_sessions"
            
            # Get latest model accuracy
            latest_accuracy=$(tail -50 /root/test/data_v2/data/ml_performance/model_metrics_history.json | grep '"validation_accuracy"' | tail -1 | sed 's/.*"validation_accuracy": *\([0-9.]*\).*/\1/' | head -1)
            if [ -n "$latest_accuracy" ] && [ "$latest_accuracy" != "0" ]; then
                accuracy_percent=$(echo "scale=1; $latest_accuracy * 100" | bc -l 2>/dev/null || echo "0.0")
                echo "🎯 Latest Model Accuracy: ${accuracy_percent}%"
            fi
        fi
        
        echo "🧠 ML Commands Available:"
        echo "   • python -m app.main ml-scores    - Current ML analysis"
        echo "   • python -m app.main ml-trading   - Trading signals"
        echo "   • python remote_ml_analysis.py   - Performance report"
        
    else
        echo "⚠️  ML Performance History: Empty or corrupted"
    fi
else
    echo "❌ ML Performance History: Not found"
    echo "📍 Checking alternative locations..."
    find /root/test -name "ml_performance_history.json" -type f 2>/dev/null | head -3
fi

echo ""
echo "💡 MEMORY RECOMMENDATIONS:"
echo "-------------------------"
available_mb=$(free -m | awk "NR==2{print \$7}")
if [ $available_mb -gt 1200 ]; then
    echo "✅ Safe to run: Full evening analysis (Stage 2)"
elif [ $available_mb -gt 800 ]; then
    echo "⚖️  Safe to run: FinBERT-only evening analysis"
elif [ $available_mb -gt 400 ]; then
    echo "💡 Safe to run: Stage 1 evening analysis only"
else
    echo "⚠️  WARNING: Memory too low for evening analysis"
    echo "   Recommendation: Restart system or add swap"
fi
