#!/usr/bin/env python3
"""
Live positions viewer with current prices and profit calculations
"""
import sqlite3
import yfinance as yf
import sys
from datetime import datetime

def get_live_positions(db_path="/root/test/paper-trading-app/paper_trading.db"):
    """Get active positions with live prices and current profit"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get active positions
        cursor.execute("""
            SELECT symbol, entry_price, shares, investment, commission_paid, entry_time,
                   ROUND((julianday('now') - julianday(entry_time)) * 24 * 60, 0) as hold_minutes
            FROM enhanced_positions 
            WHERE status = 'OPEN' 
            ORDER BY entry_time DESC
        """)
        
        positions = cursor.fetchall()
        
        if not positions:
            print("No active positions")
            return
        
        # Print header
        print(f"{'symbol':<8} {'entry_price':<11} {'current_price':<13} {'shares':<6} {'investment':<10} {'current_profit':<13} {'hold_min':<8} {'position_type':<13}")
        print(f"{'------':<8} {'-----------':<11} {'-------------':<13} {'------':<6} {'----------':<10} {'-------------':<13} {'--------':<8} {'-------------':<13}")
        
        for position in positions:
            symbol, entry_price, shares, investment, commission_paid, entry_time, hold_minutes = position
            
            try:
                # Get current price from Yahoo Finance
                ticker = yf.Ticker(symbol)
                current_price = ticker.history(period="1d")['Close'].iloc[-1]
                
                # Calculate current profit
                current_value = current_price * shares
                current_profit = current_value - investment - commission_paid
                
                # Format values
                entry_price_str = f"{entry_price:.2f}"
                current_price_str = f"{current_price:.2f}"
                investment_str = f"{investment:.0f}"
                current_profit_str = f"{current_profit:+.2f}"
                
                print(f"{symbol:<8} {entry_price_str:<11} {current_price_str:<13} {shares:<6} {investment_str:<10} {current_profit_str:<13} {hold_minutes:<8.0f} {'LONG':<13}")
                
            except Exception as e:
                # Fallback if price fetch fails
                entry_price_str = f"{entry_price:.2f}"
                investment_str = f"{investment:.0f}"
                print(f"{symbol:<8} {entry_price_str:<11} {'N/A':<13} {shares:<6} {investment_str:<10} {'N/A':<13} {hold_minutes:<8.0f} {'LONG':<13}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error getting positions: {e}")

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "/root/test/paper-trading-app/paper_trading.db"
    get_live_positions(db_path)
