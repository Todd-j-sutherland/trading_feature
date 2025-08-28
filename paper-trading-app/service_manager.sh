#!/bin/bash
# Paper Trading Service Manager
# Usage: ./service_manager.sh [start|stop|status|logs]

SERVICE_NAME="final_service.py"
SERVICE_DIR="/root/test/paper-trading-app"
VENV_PATH="$SERVICE_DIR/paper_trading_venv"
LOG_FILE="$SERVICE_DIR/paper_trading_service.log"

cd "$SERVICE_DIR"

case "$1" in
    start)
        echo "🚀 Starting Paper Trading Service..."
        if pgrep -f "$SERVICE_NAME" > /dev/null; then
            echo "⚠️  Service is already running!"
            exit 1
        fi
        nohup $VENV_PATH/bin/python3 $SERVICE_NAME > /dev/null 2>&1 &
        sleep 2
        if pgrep -f "$SERVICE_NAME" > /dev/null; then
            echo "✅ Service started successfully!"
            echo "📝 Logs: tail -f $LOG_FILE"
        else
            echo "❌ Failed to start service"
            exit 1
        fi
        ;;
    stop)
        echo "🛑 Stopping Paper Trading Service..."
        pkill -f "$SERVICE_NAME"
        if pgrep -f "$SERVICE_NAME" > /dev/null; then
            echo "⚠️  Force killing service..."
            pkill -9 -f "$SERVICE_NAME"
        fi
        echo "✅ Service stopped"
        ;;
    status)
        if pgrep -f "$SERVICE_NAME" > /dev/null; then
            echo "✅ Service is running"
            echo "📊 Process: $(pgrep -f "$SERVICE_NAME")"
            echo "📈 Recent trades:"
            sqlite3 "$SERVICE_DIR/paper_trading.db" ".headers on" ".mode column" "SELECT symbol, action, shares, price, execution_timestamp FROM paper_trades ORDER BY execution_timestamp DESC LIMIT 3;"
        else
            echo "❌ Service is not running"
        fi
        ;;
    logs)
        echo "📝 Showing recent logs (Ctrl+C to exit):"
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Usage: $0 {start|stop|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start  - Start the paper trading service"
        echo "  stop   - Stop the paper trading service"
        echo "  status - Check service status and recent trades"
        echo "  logs   - Show live service logs"
        exit 1
        ;;
esac
