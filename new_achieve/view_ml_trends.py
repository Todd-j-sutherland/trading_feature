#!/usr/bin/env python3
"""
ML Performance Trends Viewer
Analyzes historical ML performance data stored in JSON format.

Usage:
    python3 view_ml_trends.py [options]
    
Options:
    --days N        Show last N days (default: 7)
    --action NAME   Filter by specific action (BUY, SELL, HOLD, etc.)
    --export        Export trends to CSV
    --summary       Show summary statistics only
    
Examples:
    python3 view_ml_trends.py --days 14
    python3 view_ml_trends.py --action SELL
    python3 view_ml_trends.py --summary
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import csv

# Configuration
RESULTS_DIR = Path("data/ml_performance_history")
RESULTS_FILE = RESULTS_DIR / "daily_performance.json"

def load_historical_results():
    """Load historical results from JSON file"""
    if not RESULTS_FILE.exists():
        print(f"❌ No historical data found at {RESULTS_FILE}")
        print("Run evening_ml_check_with_history.py first to collect data.")
        return {}
    
    try:
        with open(RESULTS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading historical data: {e}")
        return {}

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'-'*50}")
    print(f" {title}")
    print(f"{'-'*50}")

def filter_data_by_days(data, days):
    """Filter data to last N days"""
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    return {date: results for date, results in data.items() if date >= cutoff_date}

def show_health_trends(data):
    """Show health score trends over time"""
    print_section("SYSTEM HEALTH TRENDS")
    
    if not data:
        print("No data available")
        return
    
    print("Date       Health Score  Status      Database Records")
    print("-" * 55)
    
    health_scores = []
    for date in sorted(data.keys(), reverse=True):
        day_data = data[date]
        health = day_data.get('health_summary', {})
        
        score = health.get('health_score', 0)
        max_score = health.get('max_score', 6)
        percentage = health.get('health_percentage', 0)
        status = health.get('status', 'Unknown')
        db_records = day_data.get('database_records', 0)
        
        health_scores.append(percentage)
        
        # Status icon
        if percentage >= 80:
            icon = "🟢"
        elif percentage >= 60:
            icon = "🟡"
        elif percentage >= 40:
            icon = "🟠"
        else:
            icon = "🔴"
        
        print(f"{date}  {score}/{max_score} ({percentage:3.0f}%)  {icon} {status:<8}  {db_records:,}")
    
    # Trend analysis
    if len(health_scores) > 1:
        recent_avg = sum(health_scores[:3]) / min(len(health_scores), 3)
        older_avg = sum(health_scores[3:6]) / max(1, min(len(health_scores[3:]), 3))
        
        print(f"\nTrend Analysis:")
        print(f"Recent average (last 3 days): {recent_avg:.1f}%")
        if len(health_scores) > 3:
            print(f"Previous average: {older_avg:.1f}%")
            trend = "📈 Improving" if recent_avg > older_avg else "📉 Declining" if recent_avg < older_avg else "➡️ Stable"
            print(f"Trend: {trend}")

def show_performance_trends(data, action_filter=None):
    """Show performance trends over time"""
    section_title = f"PERFORMANCE TRENDS"
    if action_filter:
        section_title += f" - {action_filter} ACTION"
    print_section(section_title)
    
    if not data:
        print("No data available")
        return
    
    print("Date       Total Trades  Win Rate  Avg Return  Top Action")
    print("-" * 55)
    
    win_rates = []
    for date in sorted(data.keys(), reverse=True):
        day_data = data[date]
        today_perf = day_data.get('todays_performance', {})
        
        if action_filter:
            # Show specific action performance
            action_data = today_perf.get('actions', {}).get(action_filter, {})
            trades = action_data.get('trades', 0)
            win_rate = action_data.get('win_rate', 0)
            avg_return = action_data.get('avg_return', 0)
            top_action = action_filter
            
            if trades == 0:
                print(f"{date}  No {action_filter} trades")
                continue
        else:
            # Show overall performance
            trades = today_perf.get('total_trades', 0)
            win_rate = today_perf.get('overall_win_rate', 0)
            avg_return = today_perf.get('overall_avg_return', 0)
            
            # Find top action by trades
            actions = today_perf.get('actions', {})
            if actions:
                top_action = max(actions.keys(), key=lambda k: actions[k].get('trades', 0))
            else:
                top_action = "None"
        
        if trades > 0:
            win_rates.append(win_rate)
            
            # Status indicators
            win_icon = "✅" if win_rate > 55 else "⚠️" if win_rate > 45 else "❌"
            return_icon = "📈" if avg_return > 0 else "📉" if avg_return < 0 else "➡️"
            
            print(f"{date}  {trades:>11}  {win_icon} {win_rate:>6.1f}%  {return_icon} {avg_return:>7.3f}%  {top_action}")
        else:
            print(f"{date}  No trades")
    
    # Performance trend analysis
    if len(win_rates) > 1:
        recent_avg = sum(win_rates[:3]) / min(len(win_rates), 3)
        print(f"\nPerformance Analysis:")
        print(f"Recent win rate average: {recent_avg:.1f}%")
        
        if len(win_rates) > 3:
            older_avg = sum(win_rates[3:6]) / max(1, min(len(win_rates[3:]), 3))
            print(f"Previous win rate average: {older_avg:.1f}%")
            
            improvement = recent_avg - older_avg
            if improvement > 5:
                trend = f"📈 Significantly improving (+{improvement:.1f}%)"
            elif improvement > 1:
                trend = f"📈 Improving (+{improvement:.1f}%)"
            elif improvement < -5:
                trend = f"📉 Significantly declining ({improvement:.1f}%)"
            elif improvement < -1:
                trend = f"📉 Declining ({improvement:.1f}%)"
            else:
                trend = f"➡️ Stable ({improvement:+.1f}%)"
            
            print(f"Trend: {trend}")

def show_action_breakdown(data):
    """Show breakdown by action type"""
    print_section("ACTION PERFORMANCE BREAKDOWN")
    
    if not data:
        print("No data available")
        return
    
    # Aggregate action performance across all days
    action_stats = {}
    
    for date, day_data in data.items():
        today_perf = day_data.get('todays_performance', {})
        actions = today_perf.get('actions', {})
        
        for action, stats in actions.items():
            if action not in action_stats:
                action_stats[action] = {
                    'total_trades': 0,
                    'total_wins': 0,
                    'total_return': 0,
                    'confidence_sum': 0,
                    'days_active': 0
                }
            
            trades = stats.get('trades', 0)
            win_rate = stats.get('win_rate', 0)
            avg_return = stats.get('avg_return', 0)
            confidence = stats.get('confidence', 0)
            
            action_stats[action]['total_trades'] += trades
            action_stats[action]['total_wins'] += int(trades * win_rate / 100)
            action_stats[action]['total_return'] += avg_return * trades
            action_stats[action]['confidence_sum'] += confidence * trades
            action_stats[action]['days_active'] += 1 if trades > 0 else 0
    
    # Display results
    print("Action      Total Trades  Win Rate  Avg Return  Avg Confidence  Days Active")
    print("-" * 75)
    
    for action in sorted(action_stats.keys()):
        stats = action_stats[action]
        total_trades = stats['total_trades']
        
        if total_trades > 0:
            win_rate = (stats['total_wins'] / total_trades) * 100
            avg_return = stats['total_return'] / total_trades
            avg_confidence = stats['confidence_sum'] / total_trades
            days_active = stats['days_active']
            
            # Status indicators
            win_icon = "✅" if win_rate > 55 else "⚠️" if win_rate > 45 else "❌"
            return_icon = "📈" if avg_return > 0 else "📉" if avg_return < 0 else "➡️"
            
            print(f"{action:<10}  {total_trades:>11}  {win_icon} {win_rate:>6.1f}%  {return_icon} {avg_return:>7.3f}%  {avg_confidence:>12.3f}  {days_active:>10}")

def show_data_quality_trends(data):
    """Show data quality trends"""
    print_section("DATA QUALITY TRENDS")
    
    if not data:
        print("No data available")
        return
    
    print("Date       New Samples  Bias 1h  Bias 4h  Bias 1d  Warnings")
    print("-" * 60)
    
    for date in sorted(data.keys(), reverse=True):
        day_data = data[date]
        quality = day_data.get('data_quality', {})
        
        samples = quality.get('new_samples_24h', 0)
        bias_1h = quality.get('bias_1h', 0)
        bias_4h = quality.get('bias_4h', 0)
        bias_1d = quality.get('bias_1d', 0)
        warnings = len(quality.get('bias_warnings', []))
        
        # Bias status indicators
        def bias_status(bias):
            if 40 <= bias <= 60:
                return "✅"
            elif 30 <= bias <= 70:
                return "⚠️"
            else:
                return "❌"
        
        print(f"{date}  {samples:>10}  {bias_status(bias_1h)} {bias_1h:>5.1f}%  {bias_status(bias_4h)} {bias_4h:>5.1f}%  {bias_status(bias_1d)} {bias_1d:>5.1f}%  {warnings:>8}")

def export_to_csv(data, filename="ml_performance_export.csv"):
    """Export performance data to CSV"""
    print_section(f"EXPORTING TO {filename}")
    
    if not data:
        print("No data to export")
        return
    
    # Prepare CSV data
    csv_data = []
    for date, day_data in sorted(data.items()):
        base_row = {
            'date': date,
            'timestamp': day_data.get('timestamp', ''),
            'health_score': day_data.get('health_summary', {}).get('health_score', 0),
            'health_percentage': day_data.get('health_summary', {}).get('health_percentage', 0),
            'database_records': day_data.get('database_records', 0),
        }
        
        # Add today's performance
        today_perf = day_data.get('todays_performance', {})
        base_row.update({
            'total_trades': today_perf.get('total_trades', 0),
            'overall_win_rate': today_perf.get('overall_win_rate', 0),
            'overall_avg_return': today_perf.get('overall_avg_return', 0),
        })
        
        # Add data quality metrics
        quality = day_data.get('data_quality', {})
        base_row.update({
            'new_samples_24h': quality.get('new_samples_24h', 0),
            'bias_1h': quality.get('bias_1h', 0),
            'bias_4h': quality.get('bias_4h', 0),
            'bias_1d': quality.get('bias_1d', 0),
            'bias_warnings_count': len(quality.get('bias_warnings', [])),
        })
        
        # Add action-specific data
        actions = today_perf.get('actions', {})
        for action in ['BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL']:
            if action in actions:
                base_row.update({
                    f'{action.lower()}_trades': actions[action].get('trades', 0),
                    f'{action.lower()}_win_rate': actions[action].get('win_rate', 0),
                    f'{action.lower()}_avg_return': actions[action].get('avg_return', 0),
                    f'{action.lower()}_confidence': actions[action].get('confidence', 0),
                })
            else:
                base_row.update({
                    f'{action.lower()}_trades': 0,
                    f'{action.lower()}_win_rate': 0,
                    f'{action.lower()}_avg_return': 0,
                    f'{action.lower()}_confidence': 0,
                })
        
        csv_data.append(base_row)
    
    # Write CSV
    if csv_data:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = csv_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"✅ Exported {len(csv_data)} days of data to {filename}")
        print(f"Columns: {len(fieldnames)} metrics per day")
    else:
        print("❌ No data to export")

def show_summary_statistics(data):
    """Show summary statistics"""
    print_section("SUMMARY STATISTICS")
    
    if not data:
        print("No data available")
        return
    
    # Calculate overall statistics
    all_trades = []
    all_win_rates = []
    all_returns = []
    all_health_scores = []
    
    action_totals = {}
    
    for date, day_data in data.items():
        # Health scores
        health = day_data.get('health_summary', {})
        health_percentage = health.get('health_percentage', 0)
        all_health_scores.append(health_percentage)
        
        # Performance data
        today_perf = day_data.get('todays_performance', {})
        trades = today_perf.get('total_trades', 0)
        win_rate = today_perf.get('overall_win_rate', 0)
        avg_return = today_perf.get('overall_avg_return', 0)
        
        if trades > 0:
            all_trades.append(trades)
            all_win_rates.append(win_rate)
            all_returns.append(avg_return)
        
        # Action breakdown
        actions = today_perf.get('actions', {})
        for action, stats in actions.items():
            if action not in action_totals:
                action_totals[action] = []
            action_totals[action].append(stats.get('win_rate', 0))
    
    # Display summary
    print(f"Analysis Period: {len(data)} days")
    print(f"Data Range: {min(data.keys())} to {max(data.keys())}")
    
    if all_health_scores:
        avg_health = sum(all_health_scores) / len(all_health_scores)
        print(f"\nSystem Health:")
        print(f"  Average health score: {avg_health:.1f}%")
        print(f"  Best day: {max(all_health_scores):.0f}%")
        print(f"  Worst day: {min(all_health_scores):.0f}%")
    
    if all_win_rates:
        avg_win_rate = sum(all_win_rates) / len(all_win_rates)
        avg_return = sum(all_returns) / len(all_returns)
        total_trades = sum(all_trades)
        
        print(f"\nTrading Performance:")
        print(f"  Average win rate: {avg_win_rate:.1f}%")
        print(f"  Average return: {avg_return:.3f}%")
        print(f"  Total trades: {total_trades}")
        print(f"  Average trades per day: {total_trades / len(all_trades):.1f}")
        
        # Best and worst days
        best_day_idx = all_win_rates.index(max(all_win_rates))
        worst_day_idx = all_win_rates.index(min(all_win_rates))
        dates = sorted(data.keys())
        
        print(f"  Best win rate: {max(all_win_rates):.1f}% on {dates[best_day_idx] if best_day_idx < len(dates) else 'unknown'}")
        print(f"  Worst win rate: {min(all_win_rates):.1f}% on {dates[worst_day_idx] if worst_day_idx < len(dates) else 'unknown'}")
    
    # Action performance summary
    if action_totals:
        print(f"\nAction Performance Summary:")
        for action, win_rates in action_totals.items():
            if win_rates:
                avg_win_rate = sum(win_rates) / len(win_rates)
                print(f"  {action}: {avg_win_rate:.1f}% avg win rate ({len(win_rates)} days)")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="View ML performance trends")
    parser.add_argument('--days', type=int, default=7, help='Show last N days (default: 7)')
    parser.add_argument('--action', type=str, help='Filter by specific action (BUY, SELL, HOLD, etc.)')
    parser.add_argument('--export', action='store_true', help='Export trends to CSV')
    parser.add_argument('--summary', action='store_true', help='Show summary statistics only')
    
    args = parser.parse_args()
    
    # Load data
    data = load_historical_results()
    if not data:
        return
    
    # Filter by days
    if args.days:
        data = filter_data_by_days(data, args.days)
    
    # Display header
    print_header(f"ML PERFORMANCE TRENDS ANALYSIS")
    print(f"Period: Last {args.days} days")
    print(f"Data points: {len(data)} days")
    
    if args.summary:
        show_summary_statistics(data)
    elif args.export:
        export_to_csv(data)
    else:
        show_health_trends(data)
        show_performance_trends(data, args.action)
        
        if not args.action:  # Only show these if not filtering by action
            show_action_breakdown(data)
            show_data_quality_trends(data)
    
    print(f"\nFor more options: python3 {sys.argv[0]} --help")

if __name__ == "__main__":
    main()
