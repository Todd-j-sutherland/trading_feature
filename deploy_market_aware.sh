#!/bin/bash
"""
Market-Aware System Deployment Script
"""

echo "🚀 Deploying Market-Aware Trading System"
echo "========================================"

# Define remote details
REMOTE_HOST="root@170.64.199.151"
REMOTE_DIR="/root/test/paper-trading-app"

echo "📂 Preparing deployment files..."

# Create deployment package
mkdir -p deployment_package
cp enhanced_efficient_system_market_aware.py deployment_package/
cp simple_market_test.py deployment_package/
cp -r market-aware-paper-trading/* deployment_package/ 2>/dev/null || echo "Market-aware folder not found, skipping..."
cp -r app/ deployment_package/ 2>/dev/null || echo "App folder not found, skipping..."

echo "📤 Deploying to remote server..."

# Deploy files
scp -r deployment_package/* $REMOTE_HOST:$REMOTE_DIR/

echo "🔧 Setting up remote environment..."

# Setup remote environment
ssh $REMOTE_HOST "cd $REMOTE_DIR && mkdir -p market-aware-logs app/services app/config app/core/ml"
ssh $REMOTE_HOST "cd $REMOTE_DIR && touch app/__init__.py app/services/__init__.py app/config/__init__.py app/core/__init__.py app/core/ml/__init__.py"

echo "🧪 Running deployment test..."

# Run test
ssh $REMOTE_HOST "cd $REMOTE_DIR && python3 simple_market_test.py"

echo "📊 Checking test results..."

# Get log files
ssh $REMOTE_HOST "cd $REMOTE_DIR && ls -la market_aware_test_*.log | tail -1"
ssh $REMOTE_HOST "cd $REMOTE_DIR && [ -f \$(ls -t market_aware_test_*.log | head -1) ] && cat \$(ls -t market_aware_test_*.log | head -1)"

echo "✅ Deployment complete!"

# Cleanup local deployment package
rm -rf deployment_package

echo "📁 Check remote logs in: $REMOTE_DIR/market_aware_test_*.log"
