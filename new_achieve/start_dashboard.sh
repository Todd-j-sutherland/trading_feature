#!/bin/bash
# Startup script for the ASX Banks Trading Sentiment Dashboard
# This script activates the virtual environment and starts the dashboard

set -e

echo "🚀 Starting ASX Banks Trading Sentiment Dashboard"
echo "================================================="

# Check if virtual environment exists
if [ ! -d "dashboard_env" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv dashboard_env
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source dashboard_env/bin/activate

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python -c "import streamlit, pandas, plotly" 2>/dev/null; then
    echo "📥 Installing required dependencies..."
    pip install streamlit pandas plotly
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Test dashboard components first
echo "🧪 Testing dashboard components..."
if python test_dashboard_components.py; then
    echo "✅ All component tests passed"
else
    echo "❌ Component tests failed. Please check the database and configuration."
    exit 1
fi

# Start the dashboard
echo "🌐 Starting Streamlit dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8501"
echo "🔄 Press Ctrl+C to stop the dashboard"
echo ""

# Start with headless mode to skip email prompt
streamlit run dashboard.py --server.headless true
