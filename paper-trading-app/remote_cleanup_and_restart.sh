#!/bin/bash

# Remote Paper Trading Cleanup and Restart Script
# Handles cleanup and restart for both local and remote environments

echo "🧹 Paper Trading System - Remote Cleanup & Restart"
echo "=================================================="

# Auto-detect environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$SCRIPT_DIR" == *"/root/test/"* ]]; then
    ENV_TYPE="REMOTE"
    WORK_DIR="/root/test/paper-trading-app"
else
    ENV_TYPE="LOCAL"
    WORK_DIR="$SCRIPT_DIR"
fi

echo "🔧 Environment: $ENV_TYPE"
echo "🔧 Working directory: $WORK_DIR"

# Change to correct directory
cd "$WORK_DIR" || {
    echo "❌ Failed to change to working directory: $WORK_DIR"
    exit 1
}

echo ""
echo "📍 Step 1: Stopping all running paper trading services..."

# Kill any running enhanced paper trading services
PIDS=$(pgrep -f "enhanced_paper_trading_service.py" 2>/dev/null)
if [ -n "$PIDS" ]; then
    echo "🔪 Killing enhanced paper trading service processes: $PIDS"
    echo "$PIDS" | xargs kill -TERM 2>/dev/null
    sleep 3
    
    # Force kill if still running
    REMAINING_PIDS=$(pgrep -f "enhanced_paper_trading_service.py" 2>/dev/null)
    if [ -n "$REMAINING_PIDS" ]; then
        echo "🔪 Force killing remaining processes: $REMAINING_PIDS"
        echo "$REMAINING_PIDS" | xargs kill -KILL 2>/dev/null
    fi
else
    echo "✅ No enhanced paper trading services running"
fi

# Kill any other paper trading services
OTHER_PIDS=$(pgrep -f "paper_trading.*service" 2>/dev/null)
if [ -n "$OTHER_PIDS" ]; then
    echo "🔪 Killing other paper trading processes: $OTHER_PIDS"
    echo "$OTHER_PIDS" | xargs kill -TERM 2>/dev/null
    sleep 2
fi

# Remove lock files
echo "🔓 Removing lock files..."
rm -f /tmp/enhanced_paper_trading_service.lock
rm -f /tmp/paper_trading_service.lock

echo ""
echo "📍 Step 2: Cleaning up stuck positions in database..."

# Check if database exists
if [ -f "paper_trading.db" ]; then
    # Get count of stuck positions
    STUCK_COUNT=$(sqlite3 paper_trading.db "SELECT COUNT(*) FROM enhanced_positions WHERE status = 'OPEN';" 2>/dev/null || echo "0")
    
    if [ "$STUCK_COUNT" -gt 0 ]; then
        echo "🗑️  Found $STUCK_COUNT stuck positions - cleaning up..."
        
        # Show what we're deleting
        echo "Positions to be deleted:"
        sqlite3 paper_trading.db -header -column "SELECT symbol, entry_time, shares, investment FROM enhanced_positions WHERE status = 'OPEN';" 2>/dev/null || echo "Could not display positions"
        
        # Delete stuck positions
        sqlite3 paper_trading.db "DELETE FROM enhanced_positions WHERE status = 'OPEN';" 2>/dev/null
        
        # Verify deletion
        REMAINING_COUNT=$(sqlite3 paper_trading.db "SELECT COUNT(*) FROM enhanced_positions WHERE status = 'OPEN';" 2>/dev/null || echo "0")
        if [ "$REMAINING_COUNT" -eq 0 ]; then
            echo "✅ All stuck positions cleaned up successfully"
        else
            echo "⚠️  Warning: $REMAINING_COUNT positions still remain"
        fi
    else
        echo "✅ No stuck positions found"
    fi
else
    echo "⚠️  Database file paper_trading.db not found"
fi

echo ""
echo "📍 Step 3: Checking virtual environment..."

# Check if virtual environment exists 
VENV_DIR="$WORK_DIR/../trading_venv"
if [ -d "$VENV_DIR" ]; then
    echo "✅ Using existing virtual environment: $VENV_DIR"
    RECREATE_VENV=false
else
    echo "❌ Virtual environment not found at: $VENV_DIR"
    echo "🔧 Creating new virtual environment..."
    python3 -m venv "$VENV_DIR"
    RECREATE_VENV=true
fi

if [ "$RECREATE_VENV" = true ]; then
    echo "📦 Installing required packages..."
    source "$VENV_DIR/bin/activate"
    pip install --quiet yfinance pandas numpy sqlalchemy pytz streamlit plotly
    deactivate
    
    echo "✅ Virtual environment created successfully"
fi

echo ""
echo "📍 Step 4: Verifying predictions database connectivity..."

# Check predictions database - try multiple locations
PRED_DB_FOUND=false

if [ "$ENV_TYPE" = "REMOTE" ]; then
    PRED_DB_PATH="/root/test/data/trading_predictions.db"
else
    PRED_DB_PATH="../data/trading_predictions.db"
fi

if [ -f "$PRED_DB_PATH" ]; then
    echo "✅ Predictions database found: $PRED_DB_PATH"
    PRED_DB_FOUND=true
    
    # Test database connectivity
    PRED_COUNT=$(sqlite3 "$PRED_DB_PATH" "SELECT COUNT(*) FROM predictions;" 2>/dev/null || echo "0")
    echo "📊 Predictions in database: $PRED_COUNT"
else
    echo "❌ Predictions database not found at: $PRED_DB_PATH"
    
    # Try alternative locations
    ALT_PATHS=(
        "/root/test/trading_predictions.db"
        "../trading_predictions.db"
        "../../data/trading_predictions.db"
    )
    
    for alt_path in "${ALT_PATHS[@]}"; do
        if [ -f "$alt_path" ]; then
            echo "✅ Found predictions database at alternative location: $alt_path"
            PRED_DB_FOUND=true
            break
        fi
    done
fi

if [ "$PRED_DB_FOUND" = false ]; then
    echo "⚠️  Warning: No predictions database found. Service may not work properly."
fi

echo ""
echo "📍 Step 5: Starting enhanced paper trading service..."

# Make sure service manager is executable
chmod +x enhanced_service_manager.sh

# Start the service
if ./enhanced_service_manager.sh start; then
    echo "✅ Service start command executed"
    
    # Wait a moment and check if it's actually running
    sleep 3
    
    if ./enhanced_service_manager.sh status; then
        echo ""
        echo "🎉 SUCCESS: Paper trading service is now running!"
        echo ""
        echo "📊 You can monitor the service with:"
        echo "   ./enhanced_service_manager.sh status    # Check status"
        echo "   ./enhanced_service_manager.sh logs      # View logs"
        echo "   ./enhanced_service_manager.sh portfolio # View portfolio"
    else
        echo ""
        echo "❌ Service failed to start properly. Check logs:"
        echo "   tail -50 enhanced_paper_trading_service.log"
    fi
else
    echo "❌ Failed to start service"
    exit 1
fi

echo ""
echo "=================================================="
echo "🧹 Remote cleanup and restart completed"
echo "=================================================="
