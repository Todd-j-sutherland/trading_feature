#!/usr/bin/env python3
"""
Simple Trading Analysis Tool
Analyze BUY predictions and outcomes with filtering (no external dependencies)
"""

import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import sys

# Database path
DB_PATH = "data/trading_predictions.db"

def load_trading_data():
    """Load predictions and outcomes data"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Get predictions with outcomes
            query = """
            SELECT 
                p.prediction_id,
                p.symbol,
                p.prediction_timestamp,
                p.predicted_action,
                p.action_confidence,
                p.entry_price as predicted_entry_price,
                p.model_version,
                o.entry_price as actual_entry_price,
                o.exit_price,
                o.actual_return,
                o.actual_direction,
                o.evaluation_timestamp,
                o.outcome_details
            FROM predictions p
            LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE p.predicted_action = 'BUY'
            AND p.model_version = 'fixed_price_mapping_v4.0'
            ORDER BY p.prediction_timestamp DESC
            """
            
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                # Parse timestamps
                df['prediction_timestamp'] = pd.to_datetime(df['prediction_timestamp'])
                df['evaluation_timestamp'] = pd.to_datetime(df['evaluation_timestamp'])
                
                # Add time-based columns for filtering
                df['prediction_hour'] = df['prediction_timestamp'].dt.hour
                df['prediction_date'] = df['prediction_timestamp'].dt.date
                
                # Calculate returns percentage and success
                df['return_pct'] = (df['actual_return'] * 100).round(3)
                df['successful'] = df['actual_direction'] > 0  # Positive direction = successful for BUY
                
                # Calculate P&L (assuming $15k position size for consistency)
                df['position_size'] = 15000
                df['pnl'] = (df['actual_return'] * df['position_size']).round(2)
                
                # Add day of week
                df['day_of_week'] = df['prediction_timestamp'].dt.day_name()
                
                # Convert times to AEST for display
                df['prediction_time_aest'] = df['prediction_timestamp'] + pd.Timedelta(hours=10)
                df['evaluation_time_aest'] = df['evaluation_timestamp'] + pd.Timedelta(hours=10)
                
                # Add exit reason (simplified)
                df['exit_reason'] = 'Price Evaluation'
                
            return df
            
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def filter_data(df, filters):
    """Apply filters to the dataframe"""
    filtered_df = df.copy()
    
    # Date range filter
    if 'date_start' in filters and 'date_end' in filters:
        start_date = pd.to_datetime(filters['date_start']).date()
        end_date = pd.to_datetime(filters['date_end']).date()
        filtered_df = filtered_df[
            (filtered_df['prediction_date'] >= start_date) & 
            (filtered_df['prediction_date'] <= end_date)
        ]
    
    # Confidence filter
    if 'min_confidence' in filters:
        filtered_df = filtered_df[filtered_df['action_confidence'] >= filters['min_confidence']]
    
    if 'max_confidence' in filters:
        filtered_df = filtered_df[filtered_df['action_confidence'] <= filters['max_confidence']]
    
    # Symbol filter
    if 'symbols' in filters and filters['symbols']:
        filtered_df = filtered_df[filtered_df['symbol'].isin(filters['symbols'])]
    
    # Time range filter (AEST hours)
    if 'start_hour' in filters and 'end_hour' in filters:
        start_hour = filters['start_hour']
        end_hour = filters['end_hour']
        # Convert AEST to UTC for filtering
        utc_start = start_hour - 10 if start_hour >= 10 else start_hour + 14
        utc_end = end_hour - 10 if end_hour >= 10 else end_hour + 14
        
        if utc_start <= utc_end:
            filtered_df = filtered_df[
                (filtered_df['prediction_hour'] >= utc_start) & 
                (filtered_df['prediction_hour'] <= utc_end)
            ]
        else:  # Handle overnight range
            filtered_df = filtered_df[
                (filtered_df['prediction_hour'] >= utc_start) | 
                (filtered_df['prediction_hour'] <= utc_end)
            ]
    
    # Only completed trades
    if filters.get('only_completed', True):
        filtered_df = filtered_df[filtered_df['actual_return'].notna()]
    
    # One trade per symbol (most recent)
    if filters.get('one_per_symbol', False):
        filtered_df = filtered_df.sort_values('prediction_timestamp', ascending=False)
        filtered_df = filtered_df.drop_duplicates(subset=['symbol'], keep='first')
    
    # Success filter
    if 'success_only' in filters and filters['success_only'] is not None:
        filtered_df = filtered_df[filtered_df['successful'] == filters['success_only']]
    
    return filtered_df

def print_summary(df):
    """Print summary statistics"""
    print("\n" + "="*80)
    print("🏦 TRADING ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"📊 BASIC METRICS:")
    print(f"   Total Records: {len(df):,}")
    
    if df.empty:
        print("   No data to analyze.")
        return
    
    completed = df[df['successful'].notna()]
    print(f"   Completed Trades: {len(completed):,}")
    
    if len(completed) > 0:
        win_rate = completed['successful'].mean()
        total_pnl = completed['pnl'].sum()
        avg_return = completed['return_pct'].mean()
        avg_confidence = completed['action_confidence'].mean()
        
        print(f"\n💰 PERFORMANCE METRICS:")
        print(f"   Win Rate: {win_rate:.1%}")
        print(f"   Average Return: {avg_return:+.2f}%")
        print(f"   Total P&L: ${total_pnl:+,.2f}")
        print(f"   Average Confidence: {avg_confidence:.1%}")
        
        # Best and worst trades
        best_trade = completed.loc[completed['return_pct'].idxmax()]
        worst_trade = completed.loc[completed['return_pct'].idxmin()]
        
        print(f"\n🏆 BEST/WORST TRADES:")
        print(f"   Best: {best_trade['symbol']} ({best_trade['return_pct']:+.2f}%, ${best_trade['pnl']:+.2f})")
        print(f"   Worst: {worst_trade['symbol']} ({worst_trade['return_pct']:+.2f}%, ${worst_trade['pnl']:+.2f})")
        
        # Performance by symbol
        symbol_stats = completed.groupby('symbol').agg({
            'return_pct': ['mean', 'count'],
            'successful': 'mean',
            'pnl': 'sum',
            'action_confidence': 'mean'
        }).round(3)
        
        print(f"\n📈 PERFORMANCE BY SYMBOL:")
        print(f"{'Symbol':<8} {'Count':<6} {'Win Rate':<9} {'Avg Return':<11} {'Total P&L':<10} {'Avg Conf':<8}")
        print("-" * 65)
        
        for symbol in symbol_stats.index:
            count = int(symbol_stats.loc[symbol, ('return_pct', 'count')])
            win_rate = symbol_stats.loc[symbol, ('successful', 'mean')]
            avg_return = symbol_stats.loc[symbol, ('return_pct', 'mean')]
            total_pnl = symbol_stats.loc[symbol, ('pnl', 'sum')]
            avg_conf = symbol_stats.loc[symbol, ('action_confidence', 'mean')]
            
            print(f"{symbol:<8} {count:<6} {win_rate:<9.1%} {avg_return:<+11.2f} ${total_pnl:<9.2f} {avg_conf:<8.1%}")
        
        # Time analysis
        print(f"\n🕐 TIME ANALYSIS:")
        hour_stats = completed.groupby(completed['prediction_time_aest'].dt.hour).agg({
            'successful': 'mean',
            'return_pct': 'mean',
            'prediction_id': 'count'
        }).round(3)
        
        for hour in sorted(hour_stats.index):
            count = int(hour_stats.loc[hour, 'prediction_id'])
            win_rate = hour_stats.loc[hour, 'successful']
            avg_return = hour_stats.loc[hour, 'return_pct']
            print(f"   {hour:02d}:00 AEST: {count:3d} trades, {win_rate:.1%} win rate, {avg_return:+.2f}% avg return")

def print_detailed_table(df, limit=20):
    """Print detailed trading table"""
    if df.empty:
        return
    
    print(f"\n📋 DETAILED RESULTS (showing top {limit}):")
    print("="*120)
    
    # Prepare display data
    display_cols = ['symbol', 'prediction_time_aest', 'action_confidence', 'actual_entry_price', 
                   'exit_price', 'return_pct', 'pnl', 'successful', 'exit_reason']
    
    display_df = df[display_cols].head(limit).copy()
    
    # Format for display
    display_df['prediction_time_aest'] = display_df['prediction_time_aest'].dt.strftime('%Y-%m-%d %H:%M')
    display_df['action_confidence'] = (display_df['action_confidence'] * 100).round(1)
    display_df['actual_entry_price'] = display_df['actual_entry_price'].round(2)
    display_df['exit_price'] = display_df['exit_price'].round(2)
    display_df['pnl'] = display_df['pnl'].round(2)
    
    # Print header
    print(f"{'Symbol':<8} {'Time (AEST)':<17} {'Conf%':<6} {'Entry$':<7} {'Exit$':<7} {'Return%':<8} {'P&L$':<8} {'Win':<4} {'Exit Reason':<15}")
    print("-" * 120)
    
    # Print rows
    for _, row in display_df.iterrows():
        symbol = str(row['symbol'])[:7]
        time_str = str(row['prediction_time_aest'])[:16]
        conf = f"{row['action_confidence']:.1f}"
        entry = f"{row['actual_entry_price']:.2f}"
        exit_p = f"{row['exit_price']:.2f}"
        ret = f"{row['return_pct']:+.2f}"
        pnl = f"{row['pnl']:+.2f}"
        win = "✅" if row['successful'] else "❌"
        reason = str(row['exit_reason'])[:14]
        
        print(f"{symbol:<8} {time_str:<17} {conf:<6} {entry:<7} {exit_p:<7} {ret:<8} {pnl:<8} {win:<4} {reason:<15}")

def main():
    """Main analysis function"""
    print("🔄 Loading trading data...")
    df = load_trading_data()
    
    if df.empty:
        print("❌ No data found. Check database connection and data availability.")
        return
    
    print(f"✅ Loaded {len(df):,} BUY predictions")
    
    # Example filters - customize these as needed
    filters = {
        'date_start': '2025-09-01',  # Start date
        'date_end': '2025-09-12',    # End date
        'min_confidence': 0.75,      # Minimum 75% confidence
        'max_confidence': 1.0,       # Maximum 100% confidence
        'start_hour': 11,            # 11 AM AEST
        'end_hour': 15,              # 3 PM AEST
        'only_completed': True,      # Only completed trades
        'one_per_symbol': False,     # Allow multiple trades per symbol
        'success_only': None,        # None = all, True = winners only, False = losers only
        # 'symbols': ['NAB.AX', 'CBA.AX']  # Specific symbols (uncomment to use)
    }
    
    print(f"\n🎛️ Applying filters:")
    for key, value in filters.items():
        if value is not None:
            print(f"   {key}: {value}")
    
    filtered_df = filter_data(df, filters)
    
    print_summary(filtered_df)
    print_detailed_table(filtered_df)
    
    print(f"\n💾 Analysis complete. Filtered {len(df):,} records down to {len(filtered_df):,} records.")

if __name__ == "__main__":
    main()
