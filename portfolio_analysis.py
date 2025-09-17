#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import os

def calculate_portfolio_returns():
    print("📊 Portfolio Return Analysis Since September 10th, 2025")
    print("=" * 70)
    
    # Portfolio parameters
    total_capital = 100000  # $100k
    position_size = 15000   # $15k per position
    max_positions = total_capital // position_size  # ~6 positions max
    
    print(f"💰 Portfolio Setup:")
    print(f"  Total Capital: ${total_capital:,}")
    print(f"  Position Size: ${position_size:,}")
    print(f"  Max Positions: {max_positions}")
    print(f"  Analysis Period: September 10th, 2025 onwards")
    
    # Connect to database
    db_path = "trading_predictions.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get BUY signals with outcomes since September 10th
    query = """
    SELECT 
        date(p.prediction_timestamp) as trade_date,
        p.symbol,
        p.predicted_action,
        o.entry_price,
        o.exit_price,
        o.actual_return,
        p.prediction_timestamp,
        p.action_confidence
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE p.predicted_action = 'BUY' 
      AND date(p.prediction_timestamp) >= '2025-09-10'
    ORDER BY p.prediction_timestamp ASC
    """
    
    try:
        cursor.execute(query)
        trades = cursor.fetchall()
        
        if not trades:
            print("❌ No BUY signals found since September 10th")
            return
            
        print(f"\n📈 Found {len(trades)} BUY signals since September 10th")
        print("\n" + "=" * 70)
        print("INDIVIDUAL TRADE ANALYSIS")
        print("=" * 70)
        
        # Track portfolio performance
        portfolio_value = total_capital
        total_return_dollars = 0
        total_return_percentage = 0
        successful_trades = 0
        
        # Track positions per symbol (one at a time)
        symbol_positions = defaultdict(list)
        daily_returns = defaultdict(float)
        
        for i, trade in enumerate(trades, 1):
            trade_date, symbol, action, entry_price, exit_price, return_pct, timestamp, confidence = trade
            
            # Calculate trade return in dollars
            if return_pct is not None and entry_price is not None:
                trade_return_dollars = position_size * (return_pct / 100)
                total_return_dollars += trade_return_dollars
                daily_returns[trade_date] += trade_return_dollars
                
                if return_pct > 0:
                    successful_trades += 1
                
                print(f"\n#{i:2d} {symbol} - {trade_date}")
                print(f"    Entry: ${entry_price:.4f}")
                print(f"    Exit:  ${exit_price:.4f} ")
                print(f"    Return: {return_pct:.2f}% = ${trade_return_dollars:+,.2f}")
                print(f"    Confidence: {confidence:.1%}")
                
                # Track symbol positions
                symbol_positions[symbol].append({
                    'date': trade_date,
                    'return_pct': return_pct,
                    'return_dollars': trade_return_dollars,
                    'confidence': confidence
                })
        
        # Calculate overall performance
        total_return_percentage = (total_return_dollars / total_capital) * 100
        final_portfolio_value = total_capital + total_return_dollars
        win_rate = (successful_trades / len(trades)) * 100 if trades else 0
        
        print("\n" + "=" * 70)
        print("PORTFOLIO PERFORMANCE SUMMARY")
        print("=" * 70)
        
        print(f"📊 Trading Statistics:")
        print(f"  Total Trades: {len(trades)}")
        print(f"  Successful Trades: {successful_trades}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Average Return per Trade: {(total_return_percentage/len(trades)):.2f}%")
        
        print(f"\n💰 Financial Performance:")
        print(f"  Starting Capital: ${total_capital:,}")
        print(f"  Total Return (Dollars): ${total_return_dollars:+,.2f}")
        print(f"  Total Return (Percentage): {total_return_percentage:+.2f}%")
        print(f"  Final Portfolio Value: ${final_portfolio_value:,.2f}")
        
        # Daily performance breakdown
        if daily_returns:
            print(f"\n📅 Daily Performance Breakdown:")
            running_total = 0
            for date in sorted(daily_returns.keys()):
                daily_profit = daily_returns[date]
                running_total += daily_profit
                print(f"  {date}: ${daily_profit:+8.2f} (Running Total: ${running_total:+,.2f})")
        
        # Symbol performance analysis
        print(f"\n🎯 Performance by Symbol:")
        symbol_stats = {}
        for symbol, positions in symbol_positions.items():
            symbol_return_dollars = sum(p['return_dollars'] for p in positions)
            symbol_return_pct = sum(p['return_pct'] for p in positions)
            avg_confidence = sum(p['confidence'] for p in positions) / len(positions)
            trade_count = len(positions)
            wins = sum(1 for p in positions if p['return_pct'] > 0)
            
            symbol_stats[symbol] = {
                'return_dollars': symbol_return_dollars,
                'return_pct': symbol_return_pct,
                'trade_count': trade_count,
                'win_rate': (wins / trade_count) * 100,
                'avg_confidence': avg_confidence
            }
            
            print(f"  {symbol:8s}: {trade_count} trades, ${symbol_return_dollars:+8.2f} ({symbol_return_pct:+5.2f}%), {wins}/{trade_count} wins ({(wins/trade_count)*100:.0f}%)")
        
        # Risk analysis
        print(f"\n⚠️  Risk Analysis:")
        losing_trades = len(trades) - successful_trades
        if losing_trades > 0:
            avg_loss = sum(r for r in [t[5] for t in trades] if r < 0) / losing_trades if losing_trades > 0 else 0
            max_loss = min([t[5] for t in trades])
            print(f"  Losing Trades: {losing_trades}")
            print(f"  Average Loss: {avg_loss:.2f}%")
            print(f"  Maximum Loss: {max_loss:.2f}%")
        else:
            print(f"  🎉 No losing trades!")
        
        if successful_trades > 0:
            avg_win = sum(r for r in [t[5] for t in trades] if r > 0) / successful_trades
            max_win = max([t[5] for t in trades])
            print(f"  Average Win: {avg_win:.2f}%")
            print(f"  Maximum Win: {max_win:.2f}%")
        
        # Performance verdict
        print(f"\n🏆 PERFORMANCE VERDICT:")
        if total_return_percentage > 10:
            verdict = "🌟 OUTSTANDING"
        elif total_return_percentage > 5:
            verdict = "✨ EXCELLENT"
        elif total_return_percentage > 2:
            verdict = "✅ VERY GOOD"
        elif total_return_percentage > 0:
            verdict = "✓ POSITIVE"
        else:
            verdict = "⚠️ NEEDS REVIEW"
            
        days_trading = len(set(t[0] for t in trades))
        daily_avg_return = total_return_percentage / days_trading if days_trading > 0 else 0
        
        print(f"  {verdict}")
        print(f"  Daily Average Return: {daily_avg_return:.2f}%")
        print(f"  Trading Days: {days_trading}")
        
        if total_return_percentage > 0:
            annualized = (1 + total_return_percentage/100) ** (365/days_trading) - 1 if days_trading > 0 else 0
            print(f"  Annualized Return (projected): {annualized*100:.1f}%")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    calculate_portfolio_returns()
