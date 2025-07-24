#!/bin/bash

# Comprehensive Memory Management Deployment for Trading Analysis System
# Handles memory optimization, swap setup, and monitoring

SERVER="root@170.64.199.151"
SSH_KEY="~/.ssh/id_rsa"
REMOTE_DIR="/root/test"

echo "🚀 Deploying Advanced Memory Management Solution"
echo "==============================================="
echo "📅 $(date)"
echo ""

# Function to run remote commands with error handling
run_remote() {
    echo "🔧 Executing: $1"
    if ssh -i "$SSH_KEY" "$SERVER" "$1"; then
        echo "✅ Success"
    else
        echo "❌ Failed: $1"
        return 1
    fi
}

# 1. SWAP SPACE SETUP
echo "💾 Setting up swap space..."
echo "---------------------------"
run_remote '
# Check current swap
echo "Current swap status:"
swapon --show
free -h

# Only create swap if none exists
if [ $(swapon --show | wc -l) -eq 0 ]; then
    echo "No swap detected. Creating 2GB swap file..."
    
    # Create swap file
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # Make it persistent
    if ! grep -q "/swapfile" /etc/fstab; then
        echo "/swapfile none swap sw 0 0" >> /etc/fstab
    fi
    
    # Optimize swappiness
    sysctl vm.swappiness=10
    if ! grep -q "vm.swappiness" /etc/sysctl.conf; then
        echo "vm.swappiness = 10" >> /etc/sysctl.conf
    fi
    
    echo "✅ Swap file created and configured"
else
    echo "✅ Swap already configured"
fi

echo "Final swap status:"
swapon --show
free -h
'

# 2. INSTALL MEMORY MONITORING DEPENDENCIES
echo ""
echo "📦 Installing memory monitoring dependencies..."
echo "----------------------------------------------"
run_remote "cd $REMOTE_DIR && source /root/trading_venv/bin/activate && pip install psutil==6.1.1"

# 3. DEPLOY MEMORY MONITORING SCRIPTS
echo ""
echo "📊 Deploying memory monitoring scripts..."
echo "----------------------------------------"

# Memory cleanup script
run_remote "cat > $REMOTE_DIR/memory_cleanup.sh << 'EOF'
#!/bin/bash
# Memory Cleanup Script - Free up memory before analysis

echo \"🧹 Cleaning up memory...\"
echo \"========================\"

# Stop smart collector temporarily
echo \"Stopping smart collector...\"
pkill -f \"news_collector --interval\" || echo \"Smart collector not running\"

# Clear system caches
echo \"Clearing system caches...\"
sync
echo 3 > /proc/sys/vm/drop_caches

# Force Python garbage collection
echo \"Forcing garbage collection...\"
python3 -c \"import gc; gc.collect(); print('GC complete')\" 2>/dev/null || true

echo \"Memory status after cleanup:\"
free -h

AVAILABLE_MB=\\\$(free -m | awk \"NR==2{printf \\\"%.0f\\\", \\\$7}\")
echo \"Available memory: \${AVAILABLE_MB}MB\"

if [ \$AVAILABLE_MB -gt 800 ]; then
    echo \"✅ Memory cleanup successful - safe for analysis\"
    exit 0
else
    echo \"⚠️ Memory still constrained after cleanup\"
    exit 1
fi
EOF"

# Advanced memory monitor
run_remote "cat > $REMOTE_DIR/memory_monitor.sh << 'EOF'
#!/bin/bash
# Advanced Memory Monitor for Trading System

echo \"📊 ADVANCED MEMORY ANALYSIS\"
echo \"============================\"
echo \"📅 \$(date)\"
echo \"\"

# System memory analysis
echo \"💾 MEMORY BREAKDOWN:\"
echo \"--------------------\"
free -m | awk '
    NR==1{print \"                 Total    Used    Free   Shared  Buff/Cache   Available\"}
    NR==2{
        total=\$2; used=\$3; free=\$4; shared=\$5; buffcache=\$6; available=\$7
        used_percent = used/total*100
        available_percent = available/total*100
        
        printf \"%-10s %7dMB %7dMB %7dMB %7dMB %10dMB %10dMB\\n\", \"Memory:\", total, used, free, shared, buffcache, available
        printf \"%-10s %7s %6.1f%% %6.1f%% %7s %10s %9.1f%%\\n\", \"Percent:\", \"\", used_percent, free/total*100, \"\", \"\", available_percent
        
        if (available_percent < 20) print \"⚠️  WARNING: Low available memory!\"
        if (available_percent < 10) print \"🚨 CRITICAL: OOM risk imminent!\"
    }
'

echo \"\"
echo \"🔄 TOP MEMORY CONSUMERS:\"
echo \"------------------------\"
ps aux --sort=-%mem | head -6 | awk 'NR==1 {print \"PID     %MEM  COMMAND\"} NR>1 && \$4>1.0 {printf \"%-8s %4.1f%%  %s\\n\", \$2, \$4, \$11}'

echo \"\"
echo \"📈 SWAP STATUS:\"
echo \"---------------\"
if [ -f /proc/swaps ] && [ -s /proc/swaps ]; then
    cat /proc/swaps
    echo \"Swap usage details:\"
    swapon --show
else
    echo \"No swap configured\"
fi

echo \"\"
echo \"🤖 TRADING SYSTEM STATUS:\"
echo \"-------------------------\"
smart_collector=\$(ps aux | grep \"news_collector --interval\" | grep -v grep || echo \"\")
if [ -n \"\$smart_collector\" ]; then
    echo \"✅ Smart Collector: Running\"
    echo \"\$smart_collector\" | awk \"{print \\\"   PID: \\\"\\\$2\\\", Memory: \\\"\\\$4\\\"%\\\"}\"
else
    echo \"❌ Smart Collector: Not Running\"
fi

python_procs=\$(ps aux | grep python | grep -v grep | wc -l)
echo \"🐍 Python Processes: \$python_procs\"

echo \"\"
echo \"💡 MEMORY RECOMMENDATIONS:\"
echo \"--------------------------\"
available_mb=\$(free -m | awk \"NR==2{print \\\$7}\")
if [ \$available_mb -gt 1200 ]; then
    echo \"✅ Safe to run: Full evening analysis (Stage 2)\"
elif [ \$available_mb -gt 800 ]; then
    echo \"⚖️  Safe to run: FinBERT-only evening analysis\"
elif [ \$available_mb -gt 400 ]; then
    echo \"💡 Safe to run: Stage 1 evening analysis only\"
else
    echo \"⚠️  WARNING: Memory too low for evening analysis\"
    echo \"   Recommendation: Run memory cleanup first\"
fi

# Check for recent OOM kills
echo \"\"
echo \"🏥 OOM KILLER STATUS:\"
echo \"--------------------\"
if dmesg | grep -i \"out of memory\\|killed process\" | tail -3 | grep -q .; then
    echo \"⚠️  Recent OOM events detected:\"
    dmesg | grep -i \"out of memory\\|killed process\" | tail -3
else
    echo \"✅ No recent OOM kills detected\"
fi
EOF"

# Smart evening routine with memory management
run_remote "cat > $REMOTE_DIR/smart_evening.sh << 'EOF'
#!/bin/bash
# Smart Evening Analysis with Memory Management

cd /root/test
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test

echo \"🌙 SMART EVENING ANALYSIS\"
echo \"==========================\"
echo \"📅 \$(date)\"
echo \"\"

# Check memory before starting
echo \"📊 Pre-analysis memory check:\"
AVAILABLE_MB=\$(free -m | awk \"NR==2{printf \\\"%.0f\\\", \\\$7}\")
TOTAL_MB=\$(free -m | awk \"NR==2{printf \\\"%.0f\\\", \\\$2}\")
USED_PERCENT=\$(free | awk \"NR==2{printf \\\"%.0f\\\", \\\$3/\\\$2 * 100}\")

echo \"   Total: \${TOTAL_MB}MB\"
echo \"   Available: \${AVAILABLE_MB}MB\"
echo \"   Used: \${USED_PERCENT}%\"

# Run memory cleanup if needed
if [ \$AVAILABLE_MB -lt 600 ]; then
    echo \"⚠️ Low memory detected - running cleanup...\"
    bash /root/test/memory_cleanup.sh
    
    # Recheck after cleanup
    AVAILABLE_MB=\$(free -m | awk \"NR==2{printf \\\"%.0f\\\", \\\$7}\")
    echo \"Available after cleanup: \${AVAILABLE_MB}MB\"
fi

# Choose analysis mode based on available memory
export USE_TWO_STAGE_ANALYSIS=1

if [ \$AVAILABLE_MB -gt 1200 ]; then
    echo \"🚀 HIGH MEMORY MODE: Running Stage 2 Enhanced Analysis\"
    export SKIP_TRANSFORMERS=0
    python -m app.main evening
    
elif [ \$AVAILABLE_MB -gt 800 ]; then
    echo \"⚖️ BALANCED MODE: Running FinBERT-only Analysis\"
    export FINBERT_ONLY=1
    python -m app.main evening
    
elif [ \$AVAILABLE_MB -gt 400 ]; then
    echo \"💡 SAFE MODE: Running Stage 1 Enhanced Analysis\"
    export SKIP_TRANSFORMERS=1
    python -m app.main evening
    
else
    echo \"⚠️ CRITICAL: Insufficient memory for evening analysis\"
    echo \"   Available: \${AVAILABLE_MB}MB (minimum: 400MB)\"
    echo \"   Recommendation: Add swap space or upgrade droplet\"
    exit 1
fi

# Post-analysis memory check
echo \"\"
echo \"📊 Post-analysis memory status:\"
free -h

# Restart smart collector if it's not running
if ! pgrep -f \"news_collector --interval\" > /dev/null; then
    echo \"🔄 Restarting smart collector...\"
    nohup python -m app.core.data.collectors.news_collector --interval 30 > /dev/null 2>&1 &
    echo \"✅ Smart collector restarted\"
fi

echo \"\"
echo \"✅ Smart evening analysis complete\"
EOF"

# Make scripts executable
run_remote "chmod +x $REMOTE_DIR/memory_cleanup.sh"
run_remote "chmod +x $REMOTE_DIR/memory_monitor.sh"
run_remote "chmod +x $REMOTE_DIR/smart_evening.sh"

# 4. UPDATE REMOTE DEPLOY SCRIPT WITH MEMORY SETTINGS
echo ""
echo "⚙️ Updating remote deployment configuration..."
echo "---------------------------------------------"
run_remote "cat > $REMOTE_DIR/.env << 'EOF'
# Memory optimization for remote server (2GB RAM + 2GB swap)
SKIP_TRANSFORMERS=1
USE_TWO_STAGE_ANALYSIS=1
PYTHONPATH=/root/test
LOG_LEVEL=INFO

# Memory management settings
MAX_MEMORY_MB=1800
MEMORY_CHECK_INTERVAL=300
AUTO_CLEANUP_THRESHOLD=85

# Data directories
DATA_DIR=/root/test/data
MODELS_DIR=/root/test/data/ml_models

# Performance settings (memory optimized)
MAX_WORKERS=1
BATCH_SIZE=5
CACHE_SIZE=50

# News collection settings (reduced for memory)
NEWS_INTERVAL=30
MAX_NEWS_ARTICLES=5
NEWS_CACHE_SIZE=20

# Database settings
DB_PATH=/root/test/data/trading.db
EOF"

# 5. CREATE MONITORING CRON JOB
echo ""
echo "⏰ Setting up automated monitoring..."
echo "-----------------------------------"
run_remote "
# Add memory monitoring to crontab (every 15 minutes)
(crontab -l 2>/dev/null | grep -v 'memory_monitor'; echo '*/15 * * * * /root/test/memory_monitor.sh >> /root/test/logs/memory_monitor.log 2>&1') | crontab -

# Add evening analysis to crontab (6 PM daily)
(crontab -l 2>/dev/null | grep -v 'smart_evening'; echo '0 18 * * * /root/test/smart_evening.sh >> /root/test/logs/evening_analysis.log 2>&1') | crontab -

echo 'Cron jobs configured:'
crontab -l
"

# 6. TEST THE SYSTEM
echo ""
echo "🧪 Testing memory management system..."
echo "------------------------------------"
echo "Running initial memory analysis..."
run_remote "bash $REMOTE_DIR/memory_monitor.sh"

echo ""
echo "Testing memory cleanup..."
run_remote "bash $REMOTE_DIR/memory_cleanup.sh"

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "📋 Summary:"
echo "  • Swap space: 2GB configured"
echo "  • Memory monitoring: Active"
echo "  • Smart evening analysis: Scheduled at 6 PM"
echo "  • Memory cleanup: Available on-demand"
echo "  • Dependencies: psutil installed"
echo ""
echo "🎯 Available Commands:"
echo "  ssh -i ~/.ssh/id_rsa root@170.64.199.151 'bash /root/test/memory_monitor.sh'"
echo "  ssh -i ~/.ssh/id_rsa root@170.64.199.151 'bash /root/test/memory_cleanup.sh'"
echo "  ssh -i ~/.ssh/id_rsa root@170.64.199.151 'bash /root/test/smart_evening.sh'"
echo ""
echo "📊 Monitor logs:"
echo "  tail -f /root/test/logs/memory_monitor.log"
echo "  tail -f /root/test/logs/evening_analysis.log"
echo ""
