#!/usr/bin/env python3
"""
Trading Analysis Tool
Interactive tool to analyze BUY predictions and their outcomes with comprehensive filtering
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, time
import numpy as np

# Database path
DB_PATH = "data/trading_predictions.db"

@st.cache_data
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
                o.actual_action,
                o.entry_price as actual_entry_price,
                o.exit_price,
                o.entry_time,
                o.exit_time,
                o.pnl,
                o.successful,
                o.position_size,
                o.holding_time_minutes,
                o.exit_reason
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
                df['entry_time'] = pd.to_datetime(df['entry_time'])
                df['exit_time'] = pd.to_datetime(df['exit_time'])
                
                # Add time-based columns for filtering
                df['prediction_hour'] = df['prediction_timestamp'].dt.hour
                df['prediction_date'] = df['prediction_timestamp'].dt.date
                df['entry_hour'] = df['entry_time'].dt.hour
                
                # Calculate returns
                df['return_pct'] = ((df['exit_price'] - df['actual_entry_price']) / df['actual_entry_price'] * 100).round(3)
                
                # Add day of week
                df['day_of_week'] = df['prediction_timestamp'].dt.day_name()
                
                # Convert times to AEST for display
                df['prediction_time_aest'] = df['prediction_timestamp'] + pd.Timedelta(hours=10)
                df['entry_time_aest'] = df['entry_time'] + pd.Timedelta(hours=10)
                df['exit_time_aest'] = df['exit_time'] + pd.Timedelta(hours=10)
                
            return df
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def apply_filters(df, filters):
    """Apply all selected filters to the dataframe"""
    filtered_df = df.copy()
    
    # Date range filter
    if filters['date_range']:
        start_date, end_date = filters['date_range']
        filtered_df = filtered_df[
            (filtered_df['prediction_date'] >= start_date) & 
            (filtered_df['prediction_date'] <= end_date)
        ]
    
    # Time range filter (AEST hours)
    if filters['time_range']:
        start_hour, end_hour = filters['time_range']
        # Convert AEST back to UTC for filtering
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
    
    # Confidence filter
    if filters['confidence_range']:
        min_conf, max_conf = filters['confidence_range']
        filtered_df = filtered_df[
            (filtered_df['action_confidence'] >= min_conf/100) & 
            (filtered_df['action_confidence'] <= max_conf/100)
        ]
    
    # Symbol filter
    if filters['symbols']:
        filtered_df = filtered_df[filtered_df['symbol'].isin(filters['symbols'])]
    
    # Day of week filter
    if filters['days_of_week']:
        filtered_df = filtered_df[filtered_df['day_of_week'].isin(filters['days_of_week'])]
    
    # Outcome filter (only completed trades)
    if filters['only_completed']:
        filtered_df = filtered_df[filtered_df['actual_action'].notna()]
    
    # Success filter
    if filters['success_filter'] != 'All':
        if filters['success_filter'] == 'Winning Only':
            filtered_df = filtered_df[filtered_df['successful'] == True]
        elif filters['success_filter'] == 'Losing Only':
            filtered_df = filtered_df[filtered_df['successful'] == False]
    
    # One trade per symbol filter
    if filters['one_per_symbol']:
        # Keep the most recent trade per symbol
        filtered_df = filtered_df.sort_values('prediction_timestamp', ascending=False)
        filtered_df = filtered_df.drop_duplicates(subset=['symbol'], keep='first')
    
    # Return range filter
    if filters['return_range'] and not filtered_df.empty:
        min_return, max_return = filters['return_range']
        filtered_df = filtered_df[
            (filtered_df['return_pct'] >= min_return) & 
            (filtered_df['return_pct'] <= max_return)
        ]
    
    # Holding time filter
    if filters['holding_time_range'] and not filtered_df.empty:
        min_time, max_time = filters['holding_time_range']
        filtered_df = filtered_df[
            (filtered_df['holding_time_minutes'] >= min_time) & 
            (filtered_df['holding_time_minutes'] <= max_time)
        ]
    
    return filtered_df

def create_performance_charts(df):
    """Create performance visualization charts"""
    if df.empty:
        return None, None, None
    
    # Returns distribution
    fig1 = px.histogram(
        df, 
        x='return_pct', 
        nbins=20,
        title='Return Distribution (%)',
        labels={'return_pct': 'Return (%)', 'count': 'Frequency'},
        color_discrete_sequence=['lightblue']
    )
    fig1.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break Even")
    
    # Performance by symbol
    symbol_stats = df.groupby('symbol').agg({
        'return_pct': ['mean', 'count'],
        'successful': 'mean',
        'pnl': 'sum'
    }).round(3)
    symbol_stats.columns = ['Avg_Return', 'Trade_Count', 'Win_Rate', 'Total_PnL']
    symbol_stats = symbol_stats.reset_index()
    
    fig2 = px.scatter(
        symbol_stats,
        x='Avg_Return',
        y='Win_Rate',
        size='Trade_Count',
        color='Total_PnL',
        hover_data=['symbol'],
        title='Performance by Symbol (Bubble Size = Trade Count)',
        labels={
            'Avg_Return': 'Average Return (%)',
            'Win_Rate': 'Win Rate',
            'Total_PnL': 'Total P&L ($)'
        }
    )
    
    # Time series performance
    if len(df) > 1:
        df_sorted = df.sort_values('prediction_timestamp')
        df_sorted['cumulative_pnl'] = df_sorted['pnl'].cumsum()
        
        fig3 = px.line(
            df_sorted,
            x='prediction_timestamp',
            y='cumulative_pnl',
            title='Cumulative P&L Over Time',
            labels={'prediction_timestamp': 'Date', 'cumulative_pnl': 'Cumulative P&L ($)'}
        )
    else:
        fig3 = go.Figure().add_annotation(text="Need more data for time series", 
                                         xref="paper", yref="paper", x=0.5, y=0.5)
    
    return fig1, fig2, fig3

def main():
    st.set_page_config(
        page_title="Trading Analysis Tool", 
        page_icon="📊", 
        layout="wide"
    )
    
    st.title("📊 Trading Analysis Tool")
    st.markdown("### Analyze BUY predictions and outcomes with advanced filtering")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading trading data..."):
        df = load_trading_data()
    
    if df.empty:
        st.error("No trading data found. Check database connection and data availability.")
        return
    
    # Sidebar filters
    st.sidebar.header("🎛️ Filters")
    
    # Date range filter
    st.sidebar.subheader("📅 Date Range")
    date_range = st.sidebar.date_input(
        "Select date range",
        value=(df['prediction_date'].min(), df['prediction_date'].max()),
        min_value=df['prediction_date'].min(),
        max_value=df['prediction_date'].max()
    )
    
    # Time range filter (AEST)
    st.sidebar.subheader("🕐 Time Range (AEST)")
    time_range = st.sidebar.slider(
        "Trading hours",
        min_value=0,
        max_value=23,
        value=(10, 16),  # Default to 10 AM - 4 PM AEST
        format="%d:00"
    )
    
    # Confidence filter
    st.sidebar.subheader("🎯 Confidence Level")
    confidence_range = st.sidebar.slider(
        "Confidence range (%)",
        min_value=0,
        max_value=100,
        value=(70, 100),
        step=5
    )
    
    # Symbol filter
    st.sidebar.subheader("📈 Symbols")
    available_symbols = sorted(df['symbol'].unique())
    symbols = st.sidebar.multiselect(
        "Select symbols (empty = all)",
        options=available_symbols,
        default=[]
    )
    
    # Day of week filter
    st.sidebar.subheader("📆 Days of Week")
    days_of_week = st.sidebar.multiselect(
        "Select days",
        options=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        default=[]
    )
    
    # Advanced filters
    st.sidebar.subheader("⚙️ Advanced Filters")
    
    only_completed = st.sidebar.checkbox("Only completed trades", value=True)
    one_per_symbol = st.sidebar.checkbox("One trade per symbol (most recent)", value=False)
    
    success_filter = st.sidebar.selectbox(
        "Trade outcome",
        options=['All', 'Winning Only', 'Losing Only'],
        index=0
    )
    
    # Return range filter
    if not df.empty and 'return_pct' in df.columns:
        return_range = st.sidebar.slider(
            "Return range (%)",
            min_value=float(df['return_pct'].min()),
            max_value=float(df['return_pct'].max()),
            value=(float(df['return_pct'].min()), float(df['return_pct'].max())),
            step=0.1
        )
    else:
        return_range = None
    
    # Holding time filter
    if not df.empty and 'holding_time_minutes' in df.columns:
        holding_time_range = st.sidebar.slider(
            "Holding time (minutes)",
            min_value=int(df['holding_time_minutes'].min()),
            max_value=int(df['holding_time_minutes'].max()),
            value=(int(df['holding_time_minutes'].min()), int(df['holding_time_minutes'].max())),
            step=10
        )
    else:
        holding_time_range = None
    
    # Collect all filters
    filters = {
        'date_range': date_range if len(date_range) == 2 else None,
        'time_range': time_range,
        'confidence_range': confidence_range,
        'symbols': symbols if symbols else None,
        'days_of_week': days_of_week if days_of_week else None,
        'only_completed': only_completed,
        'one_per_symbol': one_per_symbol,
        'success_filter': success_filter,
        'return_range': return_range,
        'holding_time_range': holding_time_range
    }
    
    # Apply filters
    filtered_df = apply_filters(df, filters)
    
    # Display summary metrics
    st.subheader("📊 Summary Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Trades", len(filtered_df))
    
    if not filtered_df.empty and 'successful' in filtered_df.columns:
        completed_trades = filtered_df[filtered_df['successful'].notna()]
        
        with col2:
            if len(completed_trades) > 0:
                win_rate = completed_trades['successful'].mean()
                st.metric("Win Rate", f"{win_rate:.1%}")
            else:
                st.metric("Win Rate", "N/A")
        
        with col3:
            if len(completed_trades) > 0:
                avg_return = completed_trades['return_pct'].mean()
                st.metric("Avg Return", f"{avg_return:+.2f}%")
            else:
                st.metric("Avg Return", "N/A")
        
        with col4:
            if len(completed_trades) > 0:
                total_pnl = completed_trades['pnl'].sum()
                st.metric("Total P&L", f"${total_pnl:+,.2f}")
            else:
                st.metric("Total P&L", "N/A")
        
        with col5:
            if len(completed_trades) > 0:
                avg_confidence = completed_trades['action_confidence'].mean()
                st.metric("Avg Confidence", f"{avg_confidence:.1%}")
            else:
                st.metric("Avg Confidence", "N/A")
    
    # Performance charts
    if not filtered_df.empty and 'return_pct' in filtered_df.columns:
        st.subheader("📈 Performance Analysis")
        
        fig1, fig2, fig3 = create_performance_charts(filtered_df)
        
        if fig1:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                st.plotly_chart(fig2, use_container_width=True)
            
            st.plotly_chart(fig3, use_container_width=True)
    
    # Detailed table
    st.subheader("📋 Detailed Results")
    
    if not filtered_df.empty:
        # Prepare display columns
        display_df = filtered_df.copy()
        
        # Format columns for display
        display_cols = [
            'symbol', 'prediction_time_aest', 'action_confidence', 
            'actual_entry_price', 'exit_price', 'return_pct', 'pnl', 
            'successful', 'holding_time_minutes', 'exit_reason'
        ]
        
        # Keep only existing columns
        display_cols = [col for col in display_cols if col in display_df.columns]
        
        # Format the dataframe
        if 'prediction_time_aest' in display_df.columns:
            display_df['prediction_time_aest'] = display_df['prediction_time_aest'].dt.strftime('%Y-%m-%d %H:%M AEST')
        
        if 'action_confidence' in display_df.columns:
            display_df['action_confidence'] = (display_df['action_confidence'] * 100).round(1)
        
        if 'actual_entry_price' in display_df.columns:
            display_df['actual_entry_price'] = display_df['actual_entry_price'].round(2)
        
        if 'exit_price' in display_df.columns:
            display_df['exit_price'] = display_df['exit_price'].round(2)
        
        if 'pnl' in display_df.columns:
            display_df['pnl'] = display_df['pnl'].round(2)
        
        # Rename columns for display
        column_names = {
            'symbol': 'Symbol',
            'prediction_time_aest': 'Prediction Time',
            'action_confidence': 'Confidence (%)',
            'actual_entry_price': 'Entry Price ($)',
            'exit_price': 'Exit Price ($)',
            'return_pct': 'Return (%)',
            'pnl': 'P&L ($)',
            'successful': 'Success',
            'holding_time_minutes': 'Hold Time (min)',
            'exit_reason': 'Exit Reason'
        }
        
        display_df = display_df[display_cols].rename(columns=column_names)
        
        # Color code the success column
        def style_success(val):
            if pd.isna(val):
                return 'background-color: lightgray'
            elif val:
                return 'background-color: lightgreen'
            else:
                return 'background-color: lightcoral'
        
        if 'Success' in display_df.columns:
            styled_df = display_df.style.applymap(style_success, subset=['Success'])
            st.dataframe(styled_df, use_container_width=True, height=400)
        else:
            st.dataframe(display_df, use_container_width=True, height=400)
        
        # Export option
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"trading_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    else:
        st.warning("No data matches the selected filters.")
    
    # Filter summary
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Filter Summary")
    st.sidebar.write(f"**Showing:** {len(filtered_df):,} trades")
    st.sidebar.write(f"**From total:** {len(df):,} trades")
    if len(df) > 0:
        st.sidebar.write(f"**Filtered:** {((len(df) - len(filtered_df)) / len(df) * 100):.1f}%")

if __name__ == "__main__":
    main()
