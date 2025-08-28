#!/bin/bash
# Enhanced Paper Trading Service Manager
# Usage: ./enhanced_service_manager.sh [start|stop|status|logs|config]

SERVICE_NAME="enhanced_paper_trading_service.py"
SERVICE_DIR="/root/test/paper-trading-app"
VENV_PATH="$SERVICE_DIR/paper_trading_venv"
LOG_FILE="$SERVICE_DIR/enhanced_paper_trading_service.log"
DB_FILE="$SERVICE_DIR/paper_trading.db"

cd "$SERVICE_DIR"

case "$1" in
    start)
        echo "🚀 Starting Enhanced Paper Trading Service..."
        if pgrep -f "$SERVICE_NAME" > /dev/null; then
            echo "⚠️  Service is already running!"
            exit 1
        fi
        nohup $VENV_PATH/bin/python3 $SERVICE_NAME > /dev/null 2>&1 &
        sleep 3
        if pgrep -f "$SERVICE_NAME" > /dev/null; then
            echo "✅ Enhanced service started successfully!"
            echo "🎯 Strategy: One position per symbol, profit target monitoring"
            echo "📝 Logs: tail -f $LOG_FILE"
        else
            echo "❌ Failed to start service"
            echo "📋 Check logs: tail $LOG_FILE"
            exit 1
        fi
        ;;
    stop)
        echo "🛑 Stopping Enhanced Paper Trading Service..."
        pkill -f "$SERVICE_NAME"
        sleep 2
        if pgrep -f "$SERVICE_NAME" > /dev/null; then
            echo "⚠️  Force killing service..."
            pkill -9 -f "$SERVICE_NAME"
        fi
        echo "✅ Service stopped"
        ;;
    status)
        if pgrep -f "$SERVICE_NAME" > /dev/null; then
            echo "✅ Enhanced service is running"
            echo "📊 Process: $(pgrep -f "$SERVICE_NAME")"
            
            # Enhanced status with active positions
            echo ""
            echo "💼 Active Positions:"
            if command -v python3 >/dev/null 2>&1 && [ -f "get_live_positions.py" ]; then
                python3 get_live_positions.py "$DB_FILE" 2>/dev/null || {
                    echo "   Falling back to basic view..."
                    sqlite3 "$DB_FILE" ".headers on" ".mode column" "SELECT symbol, entry_price, shares, investment, 
                        ROUND((julianday('now') - julianday(entry_time)) * 24 * 60, 0) as hold_minutes,
                        'LONG' as position_type
                        FROM enhanced_positions WHERE status = 'OPEN' ORDER BY entry_time DESC LIMIT 5;" 2>/dev/null || echo "   No active positions"
                }
            else
                sqlite3 "$DB_FILE" ".headers on" ".mode column" "SELECT symbol, entry_price, shares, investment, 
                    ROUND((julianday('now') - julianday(entry_time)) * 24 * 60, 0) as hold_minutes,
                    'LONG' as position_type
                    FROM enhanced_positions WHERE status = 'OPEN' ORDER BY entry_time DESC LIMIT 5;" 2>/dev/null || echo "   No active positions"
            fi
            
            echo ""
            echo "📈 Recent Trades:"
            sqlite3 "$DB_FILE" ".headers on" ".mode column" "SELECT symbol, 
                ROUND(profit, 2) as profit, 
                ROUND(hold_time_minutes, 0) as hold_min, 
                exit_reason
                FROM enhanced_trades ORDER BY exit_time DESC LIMIT 3;" 2>/dev/null || echo "   No trades yet"
            
            echo ""
            echo "🎯 Current Configuration:"
            sqlite3 "$DB_FILE" ".headers on" ".mode column" "SELECT key, value FROM trading_config ORDER BY key;" 2>/dev/null || echo "   Using default config"
            
        else
            echo "❌ Service is not running"
        fi
        ;;
    logs)
        echo "📝 Showing recent logs (Ctrl+C to exit):"
        tail -f "$LOG_FILE"
        ;;
    config)
        echo "⚙️ Current Configuration:"
        sqlite3 "$DB_FILE" ".headers on" ".mode column" "SELECT key, value, updated_at FROM trading_config ORDER BY key;" 2>/dev/null || echo "No configuration found"
        echo ""
        echo "📝 To update configuration:"
        echo "   Use the Streamlit dashboard or update directly in database"
        echo "   sqlite3 $DB_FILE \"UPDATE trading_config SET value = 10.0 WHERE key = 'profit_target';\""
        ;;
    portfolio)
        echo "💼 Portfolio Summary:"
        echo ""
        
        # Active positions
        echo "🔄 Active Positions:"
        if command -v python3 >/dev/null 2>&1 && [ -f "get_live_positions.py" ]; then
            python3 get_live_positions.py "$DB_FILE" 2>/dev/null || {
                echo "   Falling back to basic view..."
                sqlite3 "$DB_FILE" ".headers on" ".mode column" "SELECT 
                    symbol, 
                    ROUND(entry_price, 2) as entry_price,
                    shares,
                    ROUND(investment, 2) as investment,
                    ROUND(target_profit, 2) as target,
                    ROUND((julianday('now') - julianday(entry_time)) * 24 * 60, 0) as hold_min,
                    'LONG' as position_type
                    FROM enhanced_positions WHERE status = 'OPEN';" 2>/dev/null || echo "   No active positions"
            }
        else
            sqlite3 "$DB_FILE" ".headers on" ".mode column" "SELECT 
                symbol, 
                ROUND(entry_price, 2) as entry_price,
                shares,
                ROUND(investment, 2) as investment,
                ROUND(target_profit, 2) as target,
                ROUND((julianday('now') - julianday(entry_time)) * 24 * 60, 0) as hold_min,
                'LONG' as position_type
                FROM enhanced_positions WHERE status = 'OPEN';" 2>/dev/null || echo "   No active positions"
        fi
        
        echo ""
        echo "📊 Trade Statistics:"
        sqlite3 "$DB_FILE" ".headers on" ".mode column" "SELECT 
            COUNT(*) as total_trades,
            COUNT(CASE WHEN profit > 0 THEN 1 END) as winning_trades,
            ROUND(AVG(profit), 2) as avg_profit,
            ROUND(SUM(profit), 2) as total_profit,
            ROUND(AVG(hold_time_minutes), 0) as avg_hold_min
            FROM enhanced_trades;" 2>/dev/null || echo "   No trades yet"
        ;;
    *)
        echo "Usage: $0 {start|stop|status|logs|config|portfolio}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the enhanced paper trading service"
        echo "  stop      - Stop the enhanced paper trading service"  
        echo "  status    - Check service status and recent activity"
        echo "  logs      - Show live service logs"
        echo "  config    - Show current configuration"
        echo "  portfolio - Show detailed portfolio summary"
        echo ""
        echo "Enhanced Features:"
        echo "  • One position per symbol maximum"
        echo "  • Configurable profit targets (default \$5)"
        echo "  • Continuous monitoring every minute"
        echo "  • Real-time Yahoo Finance pricing"
        echo "  • Maximum hold time limits"
        exit 1
        ;;
esac
