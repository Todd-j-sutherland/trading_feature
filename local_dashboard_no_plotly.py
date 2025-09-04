#!/usr/bin/env python3
"""
Enhanced Paper Trading Dashboard Component
Integrates with the enhanced paper trading service
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import time
import pytz

# Database path constant
db_path = '/root/test/paper-trading-app/paper_trading.db'

def calculate_trading_time_minutes(entry_time_str, current_time=None):
    """Calculate only the minutes during market trading hours (10 AM - 4 PM Sydney)"""
    try:
        sydney_tz = pytz.timezone('Australia/Sydney')
        
        # Parse entry time
        if 'T' in entry_time_str:
            if '+' in entry_time_str:
                entry_time = datetime.fromisoformat(entry_time_str)
            else:
                entry_time = datetime.fromisoformat(entry_time_str).replace(tzinfo=sydney_tz)
        else:
            entry_time = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=sydney_tz)
        
        # Current time
        if current_time is None:
            current_time = datetime.now(sydney_tz)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=sydney_tz)
        
        total_minutes = 0
        current_date = entry_time.date()
        end_date = current_time.date()
        
        while current_date <= end_date:
            day_start = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=sydney_tz)
            market_open = day_start.replace(hour=10, minute=0)  # 10:00 AM
            market_close = day_start.replace(hour=16, minute=0)  # 4:00 PM
            
            # Skip weekends
            if day_start.weekday() >= 5:
                current_date = datetime.combine(current_date + timedelta(days=1), datetime.min.time()).date()
                continue
            
            # Determine the effective start and end times for this day
            day_entry = max(entry_time, market_open) if current_date == entry_time.date() else market_open
            day_exit = min(current_time, market_close) if current_date == current_time.date() else market_close
            
            # Only count time if it falls within market hours
            if day_entry < market_close and day_exit > market_open:
                effective_start = max(day_entry, market_open)
                effective_end = min(day_exit, market_close)
                if effective_start < effective_end:
                    day_minutes = int((effective_end - effective_start).total_seconds() // 60)
                    total_minutes += day_minutes
            
            current_date = datetime.combine(current_date + timedelta(days=1), datetime.min.time()).date()
        
        return total_minutes
        
    except Exception as e:
        print(f"Error calculating trading time: {e}")
        return 0.0

def get_current_config():
    """Get current trading configuration from database"""
    default_config = {
        'profit_target': 5.0,
        'max_hold_time_minutes': 1440.0,
        'position_size': 10000.0
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM trading_config")
        rows = cursor.fetchall()
        
        config = default_config.copy()
        for key, value in rows:
            config[key] = float(value)
        
        conn.close()
        return config
        
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return default_config

def paper_trading_dashboard_section():
    """Enhanced paper trading dashboard section"""
    
    st.markdown("## 🤖 Live Paper Trading System")
    st.markdown("Real-time automated trading based on ML predictions")
    
    # Load current configuration from database
    current_config = get_current_config()
    
    # Configuration section
    st.markdown("### ⚙️ Trading Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        profit_target = st.number_input(
            "Profit Target ($)",
            min_value=1.0,
            max_value=100.0,
            value=current_config.get('profit_target', 5.0),
            step=0.5,
            help="Target profit per trade before exit"
        )
        
        max_hold_time = st.selectbox(
            "Max Hold Time (minutes)",
            [60, 240, 480, 720, 1440, 2880],
            index=[60, 240, 480, 720, 1440, 2880].index(int(current_config.get('max_hold_time_minutes', 1440.0))),
            help="Maximum time to hold a position"
        )
    
    with col2:
        position_size = st.number_input(
            "Position Size ($)",
            min_value=1000,
            max_value=50000,
            value=int(current_config.get('position_size', 10000.0)),
            step=1000,
            help="Dollar amount per position"
        )
        
        stop_loss = st.number_input(
            "Stop Loss ($)",
            min_value=10.0,
            max_value=200.0,
            value=current_config.get('stop_loss', 40.0),
            step=5.0,
            help="Maximum loss per trade before exit"
        )
        
        check_interval = st.selectbox(
            "Check Interval (seconds)",
            [30, 60, 120, 300],
            index=[30, 60, 120, 300].index(int(current_config.get('check_interval_seconds', 60.0))),
            help="How often to check positions"
        )
    
    with col3:
        commission_rate = st.number_input(
            "Commission Rate (%)",
            min_value=0.0,
            max_value=1.0,
            value=current_config.get('commission_rate', 0.0) * 100.0,  # Convert to percentage
            step=0.05,
            format="%.3f",
            help="Commission as percentage of trade value (0% = no commission)"
        )
        
        min_commission = st.number_input(
            "Min Commission ($)",
            min_value=0.0,
            max_value=50.0,
            value=current_config.get('min_commission', 0.0),
            step=1.0,
            help="Minimum commission per trade"
        )
        
        max_commission = st.number_input(
            "Max Commission ($)",
            min_value=0.0,
            max_value=200.0,
            value=current_config.get('max_commission', 100.0),
            step=5.0,
            help="Maximum commission per trade"
        )
    
    # Update configuration button
    if st.button("🔄 Update Configuration", type="primary"):
        if update_trading_config(profit_target, stop_loss, max_hold_time, position_size, check_interval, 
                                commission_rate, min_commission, max_commission):
            st.success("✅ Configuration updated successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Failed to update configuration")
    
    # Service status and controls
    display_service_status()
    
    # Portfolio overview
    display_portfolio_overview()
    
    # Recent trades
    display_recent_trades()
    
    # Active positions
    display_active_positions()

def update_config(profit_target, max_hold_time, position_size):
    """Update trading configuration in database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_config (
                key TEXT PRIMARY KEY,
                value REAL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Update configuration
        cursor.execute("INSERT OR REPLACE INTO trading_config (key, value) VALUES (?, ?)", 
                      ('profit_target', profit_target))
        cursor.execute("INSERT OR REPLACE INTO trading_config (key, value) VALUES (?, ?)", 
                      ('max_hold_time_minutes', max_hold_time))
        cursor.execute("INSERT OR REPLACE INTO trading_config (key, value) VALUES (?, ?)", 
                      ('position_size', position_size))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Error updating config: {e}")
        return False

def display_service_status():
    """Display current service status"""
    st.markdown("### 🚦 Service Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Service"):
            st.info("Starting enhanced paper trading service...")
            # You would SSH to start the service here
    
    with col2:
        if st.button("⏸️ Stop Service"):
            st.info("Stopping paper trading service...")
            # You would SSH to stop the service here
    
    with col3:
        if st.button("📊 View Logs"):
            st.info("Opening service logs...")
            # You would display logs here

def display_portfolio_overview():
    """Display portfolio overview"""
    st.markdown("### 💼 Portfolio Overview")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Get active positions
        active_df = pd.read_sql_query("""
            SELECT symbol, entry_price, shares, investment, entry_time
            FROM enhanced_positions 
            WHERE status = 'OPEN'
        """, conn)
        
        # Calculate trading time for each position
        if not active_df.empty:
            active_df['hold_time_minutes'] = active_df['entry_time'].apply(
                lambda x: calculate_trading_time_minutes(x)
            )
        
        # Get trade statistics
        stats_query = """
            SELECT 
                COUNT(*) as total_trades,
                SUM(profit) as total_profit,
                AVG(profit) as avg_profit,
                COUNT(CASE WHEN profit > 0 THEN 1 END) as winning_trades,
                AVG(hold_time_minutes) as avg_hold_time
            FROM enhanced_trades
        """
        stats_df = pd.read_sql_query(stats_query, conn)
        conn.close()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        if not stats_df.empty and stats_df.iloc[0]['total_trades'] > 0:
            stats = stats_df.iloc[0]
            
            with col1:
                st.metric("Total Trades", int(stats['total_trades']))
            
            with col2:
                st.metric("Total Profit", f"${stats['total_profit']:.2f}")
            
            with col3:
                win_rate = (stats['winning_trades'] / stats['total_trades']) * 100 if stats['total_trades'] > 0 else 0
                st.metric("Win Rate", f"{win_rate:.1f}%")
            
            with col4:
                st.metric("Avg Hold Time", f"{stats['avg_hold_time']:.0f} min")
        
        # Active positions summary
        if not active_df.empty:
            st.markdown(f"**Active Positions:** {len(active_df)}")
            total_invested = active_df['investment'].sum()
            st.markdown(f"**Total Invested:** ${total_invested:,.2f}")
        else:
            st.info("No active positions")
            
    except Exception as e:
        st.error(f"Error loading portfolio data: {e}")

def display_recent_trades():
    """Display recent trades"""
    st.markdown("### 📈 Recent Trades")
    
    try:
        conn = sqlite3.connect('/root/test/paper-trading-app/paper_trading.db')
        
        trades_df = pd.read_sql_query("""
            SELECT symbol, 
                   datetime(entry_time) as entry_time, 
                   datetime(exit_time) as exit_time, 
                   entry_price, exit_price,
                   shares, profit, hold_time_minutes, exit_reason
            FROM enhanced_trades
            ORDER BY exit_time DESC
            LIMIT 10
        """, conn)
        
        conn.close()
        
        if not trades_df.empty:
            # Format dates with proper type conversion
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time']).dt.strftime('%m-%d %H:%M')
            trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time']).dt.strftime('%m-%d %H:%M')
            trades_df['profit'] = pd.to_numeric(trades_df['profit'], errors='coerce').round(2)
            trades_df['hold_time_minutes'] = pd.to_numeric(trades_df['hold_time_minutes'], errors='coerce').round(0)
            
            st.dataframe(trades_df, use_container_width=True)
            
            # Profit chart
            if len(trades_df) > 1:
                # Create cumulative profit data
                cumulative_profit = trades_df['profit'].cumsum()
                chart_data = pd.DataFrame({
                    'Trade Number': range(len(trades_df)),
                    'Cumulative Profit': cumulative_profit
                })
                st.subheader("Cumulative Profit")
                st.line_chart(chart_data.set_index('Trade Number'), height=300)
        else:
            st.info("No trades executed yet")
            
    except Exception as e:
        st.error(f"Error loading trades: {e}")

def delete_position(position_id, symbol):
    """Delete a position from the database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update position status to DELETED instead of removing entirely
        cursor.execute("""
            UPDATE enhanced_positions 
            SET status = 'DELETED'
            WHERE id = ? AND symbol = ?
        """, (position_id, symbol))
        
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        
        return rows_affected > 0
        
    except Exception as e:
        st.error(f"Error deleting position: {e}")
        return False

def display_active_positions():
    """Display active positions with current P&L"""
    st.markdown("### 📊 Active Positions")
    
    try:
        conn = sqlite3.connect('/root/test/paper-trading-app/paper_trading.db')
        
        positions_df = pd.read_sql_query("""
            SELECT id, symbol, 
                   datetime(entry_time) as entry_time, 
                   entry_price, shares, investment, commission_paid,
                   target_profit, confidence
            FROM enhanced_positions 
            WHERE status = 'OPEN'
            ORDER BY entry_time DESC
        """, conn)
        
        conn.close()
        
        if not positions_df.empty:
            # Calculate trading time for each position
            positions_df['hold_time_minutes'] = positions_df['entry_time'].apply(
                lambda x: calculate_trading_time_minutes(x)
            )
            # Add current price and profit columns using IG Markets integration
            current_prices = []
            current_profits = []
            
            # Try to use IG Markets data source first
            try:
                # Import the enhanced trading engine with IG Markets support
                import sys
                sys.path.append('/root/test/paper-trading-app')
                from ig_sync_engine import ig_sync_engine
                
                ig_available = True
                st.info("🎯 Using IG Markets real-time pricing data")
                
                for idx, row in positions_df.iterrows():
                    try:
                        # Get current price from IG Markets
                        current_price = ig_sync_engine.get_current_price(row['symbol'])
                        if current_price is None:
                            raise Exception("IG Markets price not available")
                        
                        # Calculate current profit
                        current_value = current_price * row['shares']
                        current_profit = current_value - row['investment'] - row['commission_paid']
                        
                        current_prices.append(current_price)
                        current_profits.append(current_profit)
                        
                    except Exception as e:
                        # Fallback to yfinance if IG Markets fails
                        try:
                            import yfinance as yf
                            ticker = yf.Ticker(row['symbol'])
                            fallback_price = ticker.history(period="1d")['Close'].iloc[-1]
                            
                            current_value = fallback_price * row['shares']
                            current_profit = current_value - row['investment'] - row['commission_paid']
                            
                            current_prices.append(fallback_price)
                            current_profits.append(current_profit)
                        except:
                            current_prices.append(row['entry_price'])  # fallback to entry price
                            current_profits.append(0.0)  # fallback to zero profit
                
                positions_df['current_price'] = current_prices
                positions_df['current_profit'] = current_profits
                
            except ImportError as e:
                # Fallback to yfinance if IG integration not available
                st.warning("⚠️ IG Markets integration not available - using yfinance fallback")
                try:
                    import yfinance as yf
                    
                    for idx, row in positions_df.iterrows():
                        try:
                            ticker = yf.Ticker(row['symbol'])
                            current_price = ticker.history(period="1d")['Close'].iloc[-1]
                            
                            current_value = current_price * row['shares']
                            current_profit = current_value - row['investment'] - row['commission_paid']
                            
                            current_prices.append(current_price)
                            current_profits.append(current_profit)
                            
                        except Exception:
                            current_prices.append(row['entry_price'])
                            current_profits.append(0.0)
                    
                    positions_df['current_price'] = current_prices
                    positions_df['current_profit'] = current_profits
                    
                except ImportError:
                    st.warning("⚠️ No pricing data source available - showing positions without current prices")
                    positions_df['current_price'] = positions_df['entry_price']
                    positions_df['current_profit'] = 0.0
            
            # Format data with proper type conversion
            positions_df['entry_time'] = pd.to_datetime(positions_df['entry_time']).dt.strftime('%m-%d %H:%M')
            positions_df['entry_price'] = pd.to_numeric(positions_df['entry_price'], errors='coerce').round(2)
            positions_df['current_price'] = pd.to_numeric(positions_df['current_price'], errors='coerce').round(2)
            positions_df['investment'] = pd.to_numeric(positions_df['investment'], errors='coerce').round(2)
            positions_df['current_profit'] = pd.to_numeric(positions_df['current_profit'], errors='coerce').round(2)
            positions_df['target_profit'] = pd.to_numeric(positions_df['target_profit'], errors='coerce').round(2)
            positions_df['confidence'] = pd.to_numeric(positions_df['confidence'], errors='coerce').round(3)
            positions_df['hold_time_minutes'] = pd.to_numeric(positions_df['hold_time_minutes'], errors='coerce').round(0)
            
            # Display positions with delete buttons
            st.markdown("**Active Positions:**")
            for idx, row in positions_df.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 1])
                    
                    with col1:
                        st.write(f"**{row['symbol']}**")
                        st.write(f"Entry: {row['entry_time']}")
                    
                    with col2:
                        st.write(f"Entry Price: ${row['entry_price']:.2f}")
                        st.write(f"Current: ${row['current_price']:.2f}")
                    
                    with col3:
                        st.write(f"Shares: {row['shares']}")
                        st.write(f"Investment: ${row['investment']:.2f}")
                    
                    with col4:
                        profit_color = "green" if row['current_profit'] >= 0 else "red"
                        st.write(f"Current P&L: ::{profit_color}[${row['current_profit']:.2f}]")
                        st.write(f"Target: ${row['target_profit']:.2f}")
                    
                    with col5:
                        st.write(f"Confidence: {row['confidence']:.3f}")
                        st.write(f"Hold Time: {row['hold_time_minutes']:.0f} min")
                    
                    with col6:
                        # Delete button for each position
                        if st.button(f"🗑️", key=f"delete_{row['id']}", 
                                   help=f"Delete position {row['symbol']}", 
                                   type="secondary"):
                            if delete_position(row['id'], row['symbol']):
                                st.success(f"✅ Position {row['symbol']} deleted successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to delete position {row['symbol']}")
                    
                    st.divider()
            
            # Display summary dataframe
            st.markdown("**Position Summary:**")
            # Reorder columns for better display (remove id from display)
            display_columns = ['symbol', 'entry_time', 'entry_price', 'current_price', 'shares', 
                             'investment', 'current_profit', 'target_profit', 'hold_time_minutes']
            display_df = positions_df[display_columns]
            
            st.dataframe(display_df, use_container_width=True)
            
            # Position timeline
            if len(positions_df) > 0:
                # Create hold time chart data
                chart_data = pd.DataFrame({
                    'Symbol': positions_df['symbol'],
                    'Hold Time (minutes)': positions_df['hold_time_minutes']
                })
                st.subheader("Position Hold Times")
                st.bar_chart(chart_data.set_index('Symbol'), height=300)
        else:
            st.info("No active positions")
            
    except Exception as e:
        st.error(f"Error loading positions: {e}")

def trading_history_section():
    """Display complete trading history"""
    st.markdown("### 📈 Complete Trading History")
    
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        
        # Create tabs for different history views
        hist_tab1, hist_tab2 = st.tabs(["📋 All Trades", "💰 Closed Positions"])
        
        with hist_tab1:
            st.markdown("#### Enhanced Trades (Complete Records)")
            
            # Query enhanced_trades table
            trades_query = """
            SELECT 
                symbol,
                action,
                entry_time,
                exit_time,
                entry_price,
                exit_price,
                shares,
                investment,
                proceeds,
                profit,
                commission_total,
                hold_time_minutes,
                exit_reason,
                created_at
            FROM enhanced_trades 
            ORDER BY exit_time DESC
            """
            
            trades_df = pd.read_sql_query(trades_query, conn)
            
            if len(trades_df) > 0:
                # Format currency columns
                currency_cols = ['entry_price', 'exit_price', 'investment', 'proceeds', 'profit', 'commission_total']
                for col in currency_cols:
                    if col in trades_df.columns:
                        trades_df[col] = trades_df[col].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "$0.00")
                
                # Format time columns
                if 'hold_time_minutes' in trades_df.columns:
                    trades_df['hold_time_minutes'] = trades_df['hold_time_minutes'].apply(
                        lambda x: f"{x:.0f}min" if pd.notnull(x) else "0min"
                    )
                
                st.dataframe(trades_df, use_container_width=True, height=400)
                
                # Summary statistics
                col1, col2, col3, col4 = st.columns(4)
                
                # Convert profit back to float for calculations
                profit_values = pd.to_numeric(trades_df['profit'].str.replace('$', ''), errors='coerce')
                
                with col1:
                    st.metric("Total Trades", len(trades_df))
                with col2:
                    total_profit = profit_values.sum()
                    st.metric("Total P&L", f"${total_profit:.2f}")
                with col3:
                    winning_trades = len(profit_values[profit_values > 0])
                    win_rate = (winning_trades / len(trades_df)) * 100 if len(trades_df) > 0 else 0
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                with col4:
                    avg_profit = profit_values.mean()
                    st.metric("Avg P&L", f"${avg_profit:.2f}")
                    
            else:
                st.info("No completed trades found")
        
        with hist_tab2:
            st.markdown("#### All Positions (Open & Closed)")
            
            # Query enhanced_positions table
            positions_query = """
            SELECT 
                symbol,
                entry_time,
                entry_price,
                shares,
                investment,
                target_profit,
                status,
                created_at,
                id
            FROM enhanced_positions 
            ORDER BY created_at DESC
            """
            
            all_positions_df = pd.read_sql_query(positions_query, conn)
            
            if len(all_positions_df) > 0:
                # Format currency columns
                currency_cols = ['entry_price', 'investment', 'target_profit']
                for col in currency_cols:
                    if col in all_positions_df.columns:
                        all_positions_df[col] = all_positions_df[col].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "$0.00")
                
                # Add status badges
                all_positions_df['status_badge'] = all_positions_df['status'].apply(
                    lambda x: f"🟢 {x}" if x == 'OPEN' else f"🔴 {x}" if x == 'CLOSED' else f"❌ {x}"
                )
                
                # Display without id column
                display_df = all_positions_df.drop(columns=['id'])
                st.dataframe(display_df, use_container_width=True, height=400)
                
                # Position status summary
                status_counts = all_positions_df['status'].value_counts()
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    open_count = status_counts.get('OPEN', 0)
                    st.metric("Open Positions", open_count)
                with col2:
                    closed_count = status_counts.get('CLOSED', 0)
                    st.metric("Closed Positions", closed_count)
                with col3:
                    total_count = len(all_positions_df)
                    st.metric("Total Positions", total_count)
                    
            else:
                st.info("No position history found")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading trading history: {e}")

def cleanup_tools_section():
    """Tools for cleaning up trading data"""
    st.markdown("### 🧹 Data Cleanup Tools")
    
    st.warning("⚠️ **Warning**: These operations will permanently delete data. Use with caution!")
    
    # Create columns for different cleanup options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Delete Closed Positions")
        st.info("Remove closed positions from enhanced_positions table (keeps trade records in enhanced_trades)")
        
        if st.button("🗑️ Delete All Closed Positions", type="secondary"):
            if delete_closed_positions():
                st.success("✅ Closed positions deleted successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to delete closed positions")
    
    with col2:
        st.markdown("#### Delete Trade History")
        st.info("Remove completed trades from enhanced_trades table")
        
        if st.button("🗑️ Delete All Trade History", type="secondary"):
            if delete_trade_history():
                st.success("✅ Trade history deleted successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to delete trade history")
    
    st.markdown("---")
    
    # Advanced cleanup options
    st.markdown("#### Advanced Cleanup")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("**Delete by Date Range**")
        start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
        end_date = st.date_input("End Date", value=datetime.now().date())
        
        if st.button("🗑️ Delete Trades in Date Range", type="secondary"):
            if delete_trades_by_date(start_date, end_date):
                st.success(f"✅ Trades from {start_date} to {end_date} deleted!")
                st.rerun()
            else:
                st.error("❌ Failed to delete trades by date range")
    
    with col4:
        st.markdown("**Delete by Symbol**")
        
        # Get available symbols
        try:
            conn = sqlite3.connect(db_path, timeout=10.0)
            symbols_df = pd.read_sql_query("SELECT DISTINCT symbol FROM enhanced_positions ORDER BY symbol", conn)
            conn.close()
            
            if len(symbols_df) > 0:
                selected_symbol = st.selectbox("Select Symbol", symbols_df['symbol'].tolist())
                
                if st.button(f"🗑️ Delete All {selected_symbol} Records", type="secondary"):
                    if delete_symbol_records(selected_symbol):
                        st.success(f"✅ All {selected_symbol} records deleted!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to delete {selected_symbol} records")
            else:
                st.info("No symbols found in database")
                
        except Exception as e:
            st.error(f"Error loading symbols: {e}")

def delete_closed_positions():
    """Delete all closed positions from enhanced_positions table"""
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM enhanced_positions WHERE status = 'CLOSED'")
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted_count > 0
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def delete_trade_history():
    """Delete all records from enhanced_trades table"""
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM enhanced_trades")
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted_count > 0
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def delete_trades_by_date(start_date, end_date):
    """Delete trades within a specific date range"""
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # Delete from both tables
        cursor.execute("""
            DELETE FROM enhanced_trades 
            WHERE date(exit_time) BETWEEN ? AND ?
        """, (start_date, end_date))
        
        cursor.execute("""
            DELETE FROM enhanced_positions 
            WHERE status = 'CLOSED' AND date(created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def delete_symbol_records(symbol):
    """Delete all records for a specific symbol"""
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # Delete from both tables
        cursor.execute("DELETE FROM enhanced_trades WHERE symbol = ?", (symbol,))
        cursor.execute("DELETE FROM enhanced_positions WHERE symbol = ?", (symbol,))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def update_trading_config(profit_target, stop_loss, max_hold_time, position_size, check_interval, 
                         commission_rate, min_commission, max_commission):
    """Update trading configuration in database"""
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # Create config table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_config (
                key TEXT PRIMARY KEY,
                value REAL,
                updated_at TEXT
            )
        """)
        
        # Update configuration
        config_updates = [
            ('profit_target', profit_target),
            ('stop_loss', stop_loss),
            ('max_hold_time_minutes', max_hold_time),
            ('position_size', position_size),
            ('check_interval_seconds', check_interval),
            ('commission_rate', commission_rate / 100.0),  # Convert percentage to decimal
            ('min_commission', min_commission),
            ('max_commission', max_commission)
        ]
        
        for key, value in config_updates:
            cursor.execute("""
                INSERT OR REPLACE INTO trading_config (key, value, updated_at) 
                VALUES (?, ?, ?)
            """, (key, value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def trading_strategy_explanation():
    """Explain the trading strategy"""
    st.markdown("### 📚 Trading Strategy")
    
    st.markdown("""
    **Enhanced Backtesting Strategy Implementation:**
    
    1. **One Position Per Symbol**: Maximum one open position per stock symbol
    2. **Profit Target**: Exit when position reaches configured profit target (default $5)
    3. **Time Limit**: Exit after maximum hold time (default 24 hours)
    4. **Continuous Monitoring**: Check positions every minute for exit conditions
    5. **Real-time Pricing**: Use Yahoo Finance for current market prices
    6. **ML Integration**: Monitor predictions database for new BUY signals
    
    **Risk Management:**
    - Position sizing based on configured amount
    - Commission calculation (0.25% with min/max)
    - Stop monitoring prevents unlimited losses
    - Comprehensive trade logging
    """)

# Example usage in main dashboard
if __name__ == "__main__":
    st.set_page_config(page_title="Enhanced Paper Trading", layout="wide")
    st.title("🤖 Enhanced Paper Trading Dashboard")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Active Positions", "📈 Trading History", "🧹 Cleanup Tools", "📚 Strategy"])
    
    with tab1:
        paper_trading_dashboard_section()
    
    with tab2:
        trading_history_section()
    
    with tab3:
        cleanup_tools_section()
    
    with tab4:
        trading_strategy_explanation()
