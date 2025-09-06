#!/usr/bin/env python3
"""
Performance Report Generator
Generates detailed performance reports for paper trading
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
import sqlite3

# Add the parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.position_manager import PositionManager

def generate_performance_report(days: int = 30) -> dict:
    """Generate comprehensive performance report"""
    
    # Initialize position manager
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    position_manager = PositionManager(db_path=os.path.join(data_dir, "paper_trading.db"))
    
    # Get basic performance summary
    performance = position_manager.get_performance_summary()
    account_balance = position_manager.get_account_balance()
    
    # Get detailed trade history
    conn = sqlite3.connect(position_manager.db_path)
    cursor = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days)).date()
    
    # Daily performance
    cursor.execute("""
        SELECT DATE(entry_time) as trade_date,
               COUNT(*) as trades_count,
               SUM(profit_loss) as daily_pnl,
               AVG(profit_loss_pct) as avg_return_pct
        FROM positions 
        WHERE status = 'CLOSED' 
        AND DATE(entry_time) >= ?
        GROUP BY DATE(entry_time)
        ORDER BY trade_date
    """, (start_date,))
    
    daily_performance = []
    for row in cursor.fetchall():
        daily_performance.append({
            'date': row[0],
            'trades': row[1],
            'pnl': row[2] or 0,
            'avg_return_pct': row[3] or 0
        })
    
    # Symbol performance
    cursor.execute("""
        SELECT symbol,
               COUNT(*) as trades_count,
               SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
               SUM(profit_loss) as total_pnl,
               AVG(profit_loss) as avg_pnl,
               AVG(profit_loss_pct) as avg_return_pct,
               MAX(profit_loss_pct) as best_trade_pct,
               MIN(profit_loss_pct) as worst_trade_pct
        FROM positions 
        WHERE status = 'CLOSED'
        AND DATE(entry_time) >= ?
        GROUP BY symbol
        ORDER BY total_pnl DESC
    """, (start_date,))
    
    symbol_performance = []
    for row in cursor.fetchall():
        win_rate = (row[2] / row[1]) * 100 if row[1] > 0 else 0
        symbol_performance.append({
            'symbol': row[0],
            'trades': row[1],
            'winning_trades': row[2],
            'win_rate': win_rate,
            'total_pnl': row[3] or 0,
            'avg_pnl': row[4] or 0,
            'avg_return_pct': row[5] or 0,
            'best_trade_pct': row[6] or 0,
            'worst_trade_pct': row[7] or 0
        })
    
    # Recent trades
    cursor.execute("""
        SELECT symbol, action, quantity, entry_price, exit_price, 
               profit_loss, profit_loss_pct, exit_reason, entry_time, exit_time
        FROM positions 
        WHERE status = 'CLOSED'
        ORDER BY exit_time DESC
        LIMIT 20
    """)
    
    recent_trades = []
    for row in cursor.fetchall():
        recent_trades.append({
            'symbol': row[0],
            'action': row[1],
            'quantity': row[2],
            'entry_price': row[3],
            'exit_price': row[4],
            'profit_loss': row[5] or 0,
            'profit_loss_pct': row[6] or 0,
            'exit_reason': row[7],
            'entry_time': row[8],
            'exit_time': row[9]
        })
    
    conn.close()
    
    # Compile comprehensive report
    report = {
        'generated_at': datetime.now().isoformat(),
        'report_period_days': days,
        'account_summary': {
            'total_balance': account_balance.total_balance,
            'available_funds': account_balance.available_funds,
            'used_funds': account_balance.used_funds,
            'unrealized_pnl': account_balance.unrealized_pnl,
            'realized_pnl': account_balance.realized_pnl
        },
        'overall_performance': performance,
        'daily_performance': daily_performance,
        'symbol_performance': symbol_performance,
        'recent_trades': recent_trades,
        'risk_metrics': {
            'max_drawdown': performance.get('max_drawdown', 0),
            'max_gain': performance.get('max_gain', 0),
            'avg_trade_size': performance.get('avg_profit_per_trade', 0),
            'profit_factor': calculate_profit_factor(symbol_performance),
            'sharpe_ratio': calculate_sharpe_ratio(daily_performance)
        }
    }
    
    return report

def calculate_profit_factor(symbol_performance: list) -> float:
    """Calculate profit factor (gross profit / gross loss)"""
    total_profit = sum(s['total_pnl'] for s in symbol_performance if s['total_pnl'] > 0)
    total_loss = abs(sum(s['total_pnl'] for s in symbol_performance if s['total_pnl'] < 0))
    
    return total_profit / total_loss if total_loss > 0 else float('inf')

def calculate_sharpe_ratio(daily_performance: list) -> float:
    """Calculate Sharpe ratio (simplified)"""
    if not daily_performance:
        return 0.0
    
    returns = [d['avg_return_pct'] for d in daily_performance]
    if not returns:
        return 0.0
    
    avg_return = sum(returns) / len(returns)
    
    # Calculate standard deviation
    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5
    
    return avg_return / std_dev if std_dev > 0 else 0.0

def print_performance_report(report: dict):
    """Print formatted performance report"""
    
    print("📈 IG Markets Paper Trading Performance Report")
    print("=" * 60)
    print(f"Report Period: {report['report_period_days']} days")
    print(f"Generated: {report['generated_at']}")
    print()
    
    # Account Summary
    account = report['account_summary']
    print("💰 Account Summary:")
    print(f"   Total Balance: ${account['total_balance']:,.2f}")
    print(f"   Available Funds: ${account['available_funds']:,.2f}")
    print(f"   Used Funds: ${account['used_funds']:,.2f}")
    print(f"   Realized P&L: ${account['realized_pnl']:,.2f}")
    print()
    
    # Overall Performance
    perf = report['overall_performance']
    print("📊 Overall Performance:")
    print(f"   Total Trades: {perf['total_trades']}")
    print(f"   Winning Trades: {perf['winning_trades']}")
    print(f"   Win Rate: {perf['win_rate']:.1f}%")
    print(f"   Total P&L: ${perf['total_profit_loss']:,.2f}")
    print(f"   Average per Trade: ${perf['avg_profit_per_trade']:,.2f}")
    print(f"   Average Return: {perf['avg_return_pct']:.2f}%")
    print()
    
    # Risk Metrics
    risk = report['risk_metrics']
    print("⚠️ Risk Metrics:")
    print(f"   Max Drawdown: {risk['max_drawdown']:.2f}%")
    print(f"   Max Gain: {risk['max_gain']:.2f}%")
    print(f"   Profit Factor: {risk['profit_factor']:.2f}")
    print(f"   Sharpe Ratio: {risk['sharpe_ratio']:.2f}")
    print()
    
    # Top Performing Symbols
    print("🎯 Top Performing Symbols:")
    top_symbols = sorted(report['symbol_performance'], key=lambda x: x['total_pnl'], reverse=True)[:5]
    for symbol in top_symbols:
        print(f"   {symbol['symbol']}: ${symbol['total_pnl']:,.2f} ({symbol['trades']} trades, {symbol['win_rate']:.1f}% win rate)")
    print()
    
    # Recent Trades
    print("📋 Recent Trades:")
    for trade in report['recent_trades'][:10]:
        pnl_symbol = "📈" if trade['profit_loss'] > 0 else "📉"
        print(f"   {pnl_symbol} {trade['symbol']} {trade['action']}: ${trade['profit_loss']:,.2f} ({trade['profit_loss_pct']:.2f}%) - {trade['exit_reason']}")

def main():
    """Main function"""
    print("🎯 Generating Performance Report...")
    
    try:
        # Generate report
        report = generate_performance_report()
        
        # Print to console
        print_performance_report(report)
        
        # Save to file
        report_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = os.path.join(report_dir, f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Error generating performance report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
