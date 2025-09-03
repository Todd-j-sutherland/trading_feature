#!/usr/bin/env python3
"""
Focused Paper Trading Dashboard - Clean Interface
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import json

# Page config
st.set_page_config(
    page_title="Paper Trading Dashboard",
    page_icon="Ì≥à",
    layout="wide"
)

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_database_data():
    """Get all data from database"""
    try:
        conn = sqlite3.connect('/root/test/paper-trading-app/data/paper_trading.db')
        
        # Get active trades
        active_trades = pd.read_sql_query("""
            SELECT symbol, side, quantity, entry_price, current_price, 
                   profit_loss, profit_loss_pct, entry_time
            FROM trades 
            WHERE status = 'OPEN'
            ORDER BY entry_time DESC
        """, conn)
        
        # Get recent trades (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        recent_trades = pd.read_sql_query(f"""
            SELECT symbol, side, quantity, entry_price, exit_price, 
                   profit_loss, profit_loss_pct, entry_time, exit_time, status
            FROM trades 
            WHERE exit_time >= '{thirty_days_ago}' OR status = 'OPEN'
            ORDER BY entry_time DESC
            LIMIT 50
        """, conn)
        
        # Get account info
        account_info = pd.read_sql_query("""
            SELECT balance, total_profit_loss, trade_count, win_rate
            FROM accounts 
            ORDER BY created_at DESC 
            LIMIT 1
        """, conn)
        
        conn.close()
        return active_trades, recent_trades, account_info
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def main():
    st.title("Ì≥à Paper Trading Dashboard")
    st.markdown("---")
    
    # Get data
    active_trades, recent_trades, account_info = get_database_data()
    
    # Account Summary
    st.header("Ì≤∞ Account Summary")
    if not account_info.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Balance", f"${account_info.iloc[0]['balance']:,.2f}")
        with col2:
            st.metric("Total P&L", f"${account_info.iloc[0]['total_profit_loss']:,.2f}")
        with col3:
            st.metric("Total Trades", f"{account_info.iloc[0]['trade_count']}")
        with col4:
            win_rate = account_info.iloc[0]['win_rate'] * 100 if account_info.iloc[0]['win_rate'] else 0
            st.metric("Win Rate", f"{win_rate:.1f}%")
    
    st.markdown("---")
    
    # Active Trades
    st.header("Ì¥• Active Trades")
    if not active_trades.empty:
        # Format the dataframe for display
        display_active = active_trades.copy()
        display_active['Entry Price'] = display_active['entry_price'].apply(lambda x: f"${x:.2f}")
        display_active['Current Price'] = display_active['current_price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
        display_active['P&L'] = display_active['profit_loss'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "$0.00")
        display_active['P&L %'] = display_active['profit_loss_pct'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "0.00%")
        display_active['Entry Time'] = pd.to_datetime(display_active['entry_time']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(
            display_active[['symbol', 'side', 'quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %', 'Entry Time']],
            use_container_width=True
        )
    else:
        st.info("No active trades")
    
    st.markdown("---")
    
    # Configuration Section
    st.header("‚öôÔ∏è Trading Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Management")
        st.write("‚Ä¢ **Stop Loss**: 2%")
        st.write("‚Ä¢ **Take Profit**: 4%")
        st.write("‚Ä¢ **Max Position Size**: $10,000")
        st.write("‚Ä¢ **Max Daily Risk**: 5%")
        
    with col2:
        st.subheader("Strategy Settings")
        st.write("‚Ä¢ **Confidence Threshold**: 85%")
        st.write("‚Ä¢ **Technical Analysis**: RSI + MACD")
        st.write("‚Ä¢ **News Sentiment**: Enabled")
        st.write("‚Ä¢ **IG Markets Integration**: Active")
    
    st.markdown("---")
    
    # Recent Trades
    st.header("Ì≥ä Recent Trades (Last 30 Days)")
    if not recent_trades.empty:
        # Format for display
        display_recent = recent_trades.copy()
        display_recent['Entry Price'] = display_recent['entry_price'].apply(lambda x: f"${x:.2f}")
        display_recent['Exit Price'] = display_recent['exit_price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
        display_recent['P&L'] = display_recent['profit_loss'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "$0.00")
        display_recent['P&L %'] = display_recent['profit_loss_pct'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "0.00%")
        display_recent['Entry Time'] = pd.to_datetime(display_recent['entry_time']).dt.strftime('%Y-%m-%d %H:%M')
        display_recent['Exit Time'] = pd.to_datetime(display_recent['exit_time']).dt.strftime('%Y-%m-%d %H:%M') if 'exit_time' in display_recent.columns else "N/A"
        
        # Color code P&L
        def color_pnl(val):
            if 'N/A' in str(val) or '$0.00' in str(val):
                return ''
            elif '$-' in str(val):
                return 'color: red'
            else:
                return 'color: green'
        
        styled_df = display_recent[['symbol', 'side', 'quantity', 'Entry Price', 'Exit Price', 'P&L', 'P&L %', 'status', 'Entry Time']].style.applymap(color_pnl, subset=['P&L', 'P&L %'])
        
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No recent trades found")
    
    # Auto-refresh
    st.markdown("---")
    st.caption("Dashboard auto-refreshes every 60 seconds ‚Ä¢ Last updated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

if __name__ == "__main__":
    main()
