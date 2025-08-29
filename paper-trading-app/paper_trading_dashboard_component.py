#!/usr/bin/env python3
"""
Enhanced Paper Trading Dashboard Component
Integrates with the enhanced paper trading service
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
import time

def get_current_config():
    """Load current configuration from database"""
    try:
        conn = sqlite3.connect('/root/test/paper-trading-app/paper_trading.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM trading_config")
        config_rows = cursor.fetchall()
        conn.close()
        
        config = {}
        for key, value in config_rows:
            config[key] = float(value)
        
        return config
    except Exception as e:
        # Return defaults if database doesn't exist or error occurs
        return {
            'profit_target': 5.0,
            'stop_loss': 40.0,
            'position_size': 10000.0,
            'max_hold_time_minutes': 1440.0,
            'check_interval_seconds': 60.0,
            'commission_rate': 0.0,
            'min_commission': 0.0,
            'max_commission': 100.0
        }

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

def update_trading_config(profit_target, stop_loss, max_hold_time, position_size, check_interval, 
                         commission_rate, min_commission, max_commission):
    """Update trading configuration in database"""
    try:
        conn = sqlite3.connect('/root/test/paper-trading-app/paper_trading.db')
        cursor = conn.cursor()
        
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
        conn = sqlite3.connect('/root/test/paper-trading-app/paper_trading.db')
        
        # Get active positions
        active_df = pd.read_sql_query("""
            SELECT symbol, entry_price, shares, investment, 
                   (julianday('now') - julianday(entry_time)) * 24 * 60 as hold_time_minutes
            FROM enhanced_positions 
            WHERE status = 'OPEN'
        """, conn)
        
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
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(len(trades_df))),
                    y=trades_df['profit'].cumsum(),
                    mode='lines+markers',
                    name='Cumulative Profit',
                    line=dict(color='green')
                ))
                fig.update_layout(
                    title="Cumulative Profit",
                    xaxis_title="Trade Number",
                    yaxis_title="Cumulative Profit ($)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trades executed yet")
            
    except Exception as e:
        st.error(f"Error loading trades: {e}")

def display_active_positions():
    """Display active positions with current P&L"""
    st.markdown("### 📊 Active Positions")
    
    try:
        conn = sqlite3.connect('/root/test/paper-trading-app/paper_trading.db')
        
        positions_df = pd.read_sql_query("""
            SELECT symbol, 
                   datetime(entry_time) as entry_time, 
                   entry_price, shares, investment, commission_paid,
                   target_profit, confidence,
                   (julianday('now') - julianday(entry_time)) * 24 * 60 as hold_time_minutes
            FROM enhanced_positions 
            WHERE status = 'OPEN'
            ORDER BY entry_time DESC
        """, conn)
        
        conn.close()
        
        if not positions_df.empty:
            # Add current price and profit columns
            try:
                import yfinance as yf
                yfinance_available = True
            except ImportError:
                st.warning("⚠️ yfinance not available - showing positions without current prices")
                yfinance_available = False
            
            current_prices = []
            current_profits = []
            
            if yfinance_available:
                for idx, row in positions_df.iterrows():
                    try:
                        # Get current price
                        ticker = yf.Ticker(row['symbol'])
                        current_price = ticker.history(period="1d")['Close'].iloc[-1]
                        
                        # Calculate current profit
                        current_value = current_price * row['shares']
                        current_profit = current_value - row['investment'] - row['commission_paid']
                        
                        current_prices.append(current_price)
                        current_profits.append(current_profit)
                        
                    except Exception as e:
                        current_prices.append(row['entry_price'])  # fallback to entry price
                        current_profits.append(0.0)  # fallback to zero profit
                
                positions_df['current_price'] = current_prices
                positions_df['current_profit'] = current_profits
            else:
                # If yfinance not available, use entry price and zero profit
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
            
            # Reorder columns for better display
            display_columns = ['symbol', 'entry_time', 'entry_price', 'current_price', 'shares', 
                             'investment', 'current_profit', 'target_profit', 'hold_time_minutes']
            positions_df = positions_df[display_columns]
            
            st.dataframe(positions_df, use_container_width=True)
            
            # Position timeline
            if len(positions_df) > 0:
                fig = go.Figure()
                
                for idx, row in positions_df.iterrows():
                    fig.add_trace(go.Bar(
                        x=[row['symbol']],
                        y=[row['hold_time_minutes']],
                        name=row['symbol'],
                        text=f"${row['target_profit']:.2f}",
                        textposition="auto"
                    ))
                
                fig.update_layout(
                    title="Position Hold Times",
                    xaxis_title="Symbol",
                    yaxis_title="Hold Time (minutes)",
                    height=300,
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No active positions")
            
    except Exception as e:
        st.error(f"Error loading positions: {e}")

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
    
    paper_trading_dashboard_section()
    trading_strategy_explanation()
