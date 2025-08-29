#!/usr/bin/env python3
"""
Live positions viewer with current prices and profit calculations
"""
import sqlite3
import yfinance as yf
import sys
from datetime import datetime, timezone, timedelta
import pytz

def is_asx_trading_hours(dt):
    """Check if given datetime is during ASX trading hours"""
    if dt is None:
        return False
    
    # Convert to Sydney timezone
    sydney_tz = pytz.timezone('Australia/Sydney')
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    sydney_time = dt.astimezone(sydney_tz)
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    if sydney_time.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # ASX trading hours: 10:00 AM to 4:00 PM AEST/AEDT
    trading_start = sydney_time.replace(hour=11, minute=15, second=0, microsecond=0)
    trading_end = sydney_time.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return trading_start <= sydney_time <= trading_end

def calculate_trading_time_minutes(entry_time_str, current_time=None):
    """Calculate the actual trading time in minutes between entry and current time"""
    try:
        # Parse entry time - handle both formats
        if 'T' in entry_time_str:
            entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
        else:
            entry_time = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M:%S')
            entry_time = entry_time.replace(tzinfo=timezone.utc)
            
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        elif isinstance(current_time, str):
            if 'T' in current_time:
                current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            else:
                current_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
                current_time = current_time.replace(tzinfo=timezone.utc)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        
        # Ensure entry_time has timezone
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=timezone.utc)
        
        if entry_time >= current_time:
            return 0.0
        
        # Sydney timezone
        sydney_tz = pytz.timezone('Australia/Sydney')
        
        total_trading_minutes = 0.0
        current_check = entry_time
        
        # Process each day between entry and current time
        while current_check.date() <= current_time.date():
            sydney_check = current_check.astimezone(sydney_tz)
            
            # Skip weekends
            if sydney_check.weekday() >= 5:
                current_check = current_check.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                continue
            
            # Define trading hours for this day
            trading_start = sydney_check.replace(hour=11, minute=15, second=0, microsecond=0)
            trading_end = sydney_check.replace(hour=16, minute=0, second=0, microsecond=0)
            
            # Convert back to UTC for comparison
            trading_start_utc = trading_start.astimezone(timezone.utc)
            trading_end_utc = trading_end.astimezone(timezone.utc)
            
            # Determine the start and end times for this day
            day_start = max(current_check, trading_start_utc)
            day_end = min(current_time, trading_end_utc)
            
            # If there's overlap with trading hours on this day
            if day_start <= day_end and day_start <= trading_end_utc and day_end >= trading_start_utc:
                # Calculate trading minutes for this day
                day_trading_minutes = max(0, (day_end - day_start).total_seconds() / 60)
                total_trading_minutes += day_trading_minutes
            
            # Move to next day
            current_check = current_check.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        return round(total_trading_minutes, 1)
        
    except Exception as e:
        print(f"Error calculating trading time: {e}")
        return 0.0

def get_live_positions(db_path="/root/test/paper-trading-app/paper_trading.db"):
    """Get active positions with live prices and current profit"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get active positions
        cursor.execute("""
            SELECT symbol, entry_price, shares, investment, commission_paid, entry_time
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
            symbol, entry_price, shares, investment, commission_paid, entry_time = position
            
            # Calculate trading time minutes (not total time)
            hold_minutes = calculate_trading_time_minutes(entry_time)
            
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