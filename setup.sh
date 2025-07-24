#!/bin/bash

# ML Trading System Setup Script
# This script sets up the environment for the trading analysis system

echo "🚀 Setting up ML Trading System Environment..."

# Activate virtual environment
source .venv312/bin/activate

# Set Python path (required for imports to work)
export PYTHONPATH=/Users/toddsutherland/Repos/trading_analysis

echo "✅ Environment ready for ML trading!"
echo ""
echo "📋 Available Commands:"
echo "  python app/main.py status           # System health check"
echo "  python app/main.py ml-scores        # Get ML scores for all banks"
echo "  python app/main.py pre-trade --symbol QBE.AX  # Pre-trade analysis"
echo "  python app/main.py enhanced-dashboard  # Launch ML dashboard (port 8501)"
echo "  streamlit run app/dashboard/enhanced_main.py --server.port 8502  # Alt port"
echo "  python app/main.py news             # News sentiment analysis"
echo ""
echo "💡 Tip: For faster startup, use: SKIP_TRANSFORMERS=1 python app/main.py [command]"
echo "🌐 Dashboard: If port 8501 is busy, use port 8502 or 8503"
echo ""
echo "🎯 Test the system with: python app/main.py status"
