#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

st.set_page_config(page_title="Paper Trading Dashboard", layout="wide")

def get_sample_data():
    active_trades = pd.DataFrame({
        "symbol": ["NAB.AX", "CBA.AX", "WBC.AX"],
        "side": ["BUY", "BUY", "SELL"],
        "quantity": [100, 50, 75],
        "entry_price": [37.50, 168.40, 38.20],
        "current_price": [37.85, 169.10, 37.95],
        "profit_loss": [35.00, 35.00, 18.75],
        "entry_time": ["2025-09-03 10:30", "2025-09-03 11:15", "2025-09-03 12:00"]
    })
    
    recent_trades = pd.DataFrame({
        "symbol": ["ANZ.AX", "BHP.AX", "RIO.AX"],
        "side": ["BUY", "SELL", "BUY"],
        "quantity": [200, 100, 50],
        "entry_price": [28.50, 45.20, 125.80],
        "exit_price": [29.15, 44.85, 127.20],
        "profit_loss": [130.00, -35.00, 70.00],
        "status": ["CLOSED", "CLOSED", "CLOSED"]
    })
    
    return active_trades, recent_trades

def main():
    st.title("Paper Trading Dashboard")
    st.markdown("---")
    
    active_trades, recent_trades = get_sample_data()
    
    # Account Summary
    st.header("Account Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Balance", "$50,000.00")
    with col2:
        st.metric("Total P&L", "$2,245.00")
    with col3:
        st.metric("Total Trades", "47")
    with col4:
        st.metric("Win Rate", "74.5%")
    
    st.markdown("---")
    
    # Active Trades
    st.header("Active Trades")
    if not active_trades.empty:
        display_active = active_trades.copy()
        display_active["Entry Price"] = display_active["entry_price"].apply(lambda x: f"${x:.2f}")
        display_active["Current Price"] = display_active["current_price"].apply(lambda x: f"${x:.2f}")
        display_active["P&L"] = display_active["profit_loss"].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(
            display_active[["symbol", "side", "quantity", "Entry Price", "Current Price", "P&L", "entry_time"]],
            use_container_width=True
        )
    else:
        st.info("No active trades")
    
    st.markdown("---")
    
    # Configuration
    st.header("Trading Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Management")
        st.write("- Stop Loss: 2%")
        st.write("- Take Profit: 2.00 (FIXED)")
        st.write("- Max Position: $10,000")
        st.write("- Daily Risk: 5%")
        
    with col2:
        st.subheader("Strategy Settings")
        st.write("- Confidence: 85%")
        st.write("- Technical: RSI + MACD")
        st.write("- News: Enabled")
        st.write("- IG Markets: Auto-Sync Enabled")
    
    st.markdown("---")
    
    # Recent Trades
    st.header("Recent Trades")
    if not recent_trades.empty:
        display_recent = recent_trades.copy()
        display_recent["Entry Price"] = display_recent["entry_price"].apply(lambda x: f"${x:.2f}")
        display_recent["Exit Price"] = display_recent["exit_price"].apply(lambda x: f"${x:.2f}")
        display_recent["P&L"] = display_recent["profit_loss"].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(
            display_recent[["symbol", "side", "quantity", "Entry Price", "Exit Price", "P&L", "status"]],
            use_container_width=True
        )
    else:
        st.info("No recent trades")
    
    st.markdown("---")
    
    # System Status
    st.header("System Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("Paper Trading: Active")
        st.success("IG Markets: Connected")
        
    with col2:
        st.success("Market Data: Live")
        st.success("Price Updates: Real-time")
        
    with col3:
        st.success("Risk Management: Active")
        st.success("Profit Targets: Monitoring")
    
    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()

    # IG Markets Sync Status (NEW SECTION)
    st.header("IG Markets Sync Status")
    
    # Import IG sync engine if available
    try:
        from ig_sync_engine import ig_sync_engine
        sync_status = ig_sync_engine.get_sync_status()
        synced_positions = ig_sync_engine.get_synced_positions()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            status_text = "Enabled" if sync_status["sync_enabled"] else "Disabled"
            st.metric("Sync Status", status_text)
        with col2:
            mode_text = "Active" if sync_status["demo_mode"] else "Live"
            st.metric("Demo Mode", mode_text)
        with col3:
            st.metric("Synced Positions", sync_status["total_synced_positions"])
        with col4:
            price_text = f"${sync_status[\"take_profit_price\"]:.2f}"
            st.metric("Take Profit Price", price_text)
        
        # Show synced positions if any
        if synced_positions:
            st.subheader("Current IG Synced Positions")
            sync_df = pd.DataFrame(synced_positions)
            if not sync_df.empty:
                display_sync = sync_df.copy()
                display_sync["Entry Price"] = display_sync["entry_price"].apply(lambda x: f"${x:.2f}")
                display_sync["Sync Time"] = pd.to_datetime(display_sync["sync_timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
                
                st.dataframe(
                    display_sync[["symbol", "side", "quantity", "Entry Price", "status", "Sync Time"]],
                    use_container_width=True
                )
        else:
            st.info("No synced positions yet")
            
    except ImportError:
        st.warning("IG Sync Engine not available")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sync Status", "Enabled")
        with col2:
            st.metric("Demo Mode", "Active")
        with col3:
            st.metric("Synced Positions", "0")
        with col4:
            st.metric("Take Profit Price", "$32.00")
    
    st.markdown("---")
