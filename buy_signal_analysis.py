#!/usr/bin/env python3
import sqlite3
from datetime import datetime

def analyze_buy_signals():
    print("BUY Signal Portfolio Analysis Since September 10th, 2025")
    print("="*70)
    
    conn = sqlite3.connect("trading_predictions.db")
    cursor = conn.cursor()
    
    # Portfolio settings
    total_capital = 100000  # $100k
    position_size = 15000   # $15k per position
    
    print(f"Portfolio: ${total_capital:,} total, ${position_size:,} per position")
    print("="*70)
    
    # Get BUY signals with outcomes since Sept 10
    query = """
    SELECT 
        date(p.prediction_timestamp) as trade_date,
        p.symbol,
        o.entry_price,
        o.exit_price,
        o.actual_return,
        p.action_confidence,
        p.prediction_timestamp
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE p.predicted_action = 'BUY' 
      AND date(p.prediction_timestamp) >= '2025-09-10'
    ORDER BY p.prediction_timestamp ASC
    """
    
    cursor.execute(query)
    trades = cursor.fetchall()
    
    if not trades:
        print("No completed BUY trades found since September 10th")
        
        # Check pending BUY signals
        cursor.execute("""
        SELECT COUNT(*) FROM predictions 
        WHERE predicted_action = 'BUY' AND date(prediction_timestamp) >= '2025-09-10'
        """)
        pending_buys = cursor.fetchone()[0]
        print(f"Pending BUY signals (no outcomes yet): {pending_buys}")
        
        if pending_buys > 0:
            cursor.execute("""
            SELECT symbol, date(prediction_timestamp), action_confidence
            FROM predictions 
            WHERE predicted_action = 'BUY' AND date(prediction_timestamp) >= '2025-09-10'
            ORDER BY prediction_timestamp DESC
            LIMIT 10
            """)
            
            recent = cursor.fetchall()
            print("\nRecent BUY signals (awaiting outcomes):")
            for symbol, date, conf in recent:
                print(f"  {symbol} on {date} (confidence: {conf:.1%})")
        
        conn.close()
        return
    
    print(f"Found {len(trades)} completed BUY trades")
    print("\nTrade Details:")
    print("-" * 70)
    
    total_return_dollars = 0
    winning_trades = 0
    daily_totals = {}
    
    for i, trade in enumerate(trades, 1):
        trade_date, symbol, entry_price, exit_price, return_pct, confidence, timestamp = trade
        
        if return_pct is not None:
            trade_return_dollars = position_size * (return_pct / 100)
            total_return_dollars += trade_return_dollars
            
            if return_pct > 0:
                winning_trades += 1
            
            # Track daily performance
            if trade_date not in daily_totals:
                daily_totals[trade_date] = 0
            daily_totals[trade_date] += trade_return_dollars
            
            print(f"{i:2d}. {symbol:8s} {trade_date} | {return_pct:+6.2f}% = ${trade_return_dollars:+8.2f}")
    
    # Calculate performance metrics
    total_return_pct = (total_return_dollars / total_capital) * 100
    win_rate = (winning_trades / len(trades)) * 100
    
    print("\n" + "="*70)
    print("PORTFOLIO PERFORMANCE SUMMARY")
    print("="*70)
    
    print(f"Total Trades: {len(trades)}")
    print(f"Winning Trades: {winning_trades}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"")
    print(f"Starting Capital: ${total_capital:,}")
    print(f"Total Return: ${total_return_dollars:+,.2f}")
    print(f"Portfolio Return: {total_return_pct:+.2f}%")
    print(f"Final Value: ${total_capital + total_return_dollars:,.2f}")
    
    if daily_totals:
        print(f"\nDaily Performance:")
        running_total = 0
        for date in sorted(daily_totals.keys()):
            daily_profit = daily_totals[date]
            running_total += daily_profit
            print(f"  {date}: ${daily_profit:+8.2f} (Total: ${running_total:+,.2f})")
    
    # Performance assessment
    print(f"\nPerformance Assessment:")
    if total_return_pct > 5:
        verdict = "EXCELLENT"
    elif total_return_pct > 2:
        verdict = "VERY GOOD" 
    elif total_return_pct > 0:
        verdict = "POSITIVE"
    else:
        verdict = "NEEDS IMPROVEMENT"
    
    print(f"  Verdict: {verdict}")
    
    # Calculate daily average if multiple days
    trading_days = len(daily_totals)
    if trading_days > 1:
        daily_avg = total_return_pct / trading_days
        print(f"  Average Daily Return: {daily_avg:.2f}%")
        print(f"  Trading Days: {trading_days}")
    
    conn.close()

if __name__ == "__main__":
    analyze_buy_signals()
