#!/usr/bin/env python3
"""
SQL-Based Trading Dashboard

Unified dashboard that reads all data directly from SQL database.
Replaces JSON-based dashboard with proper SQL data access.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import our SQL manager
from app.core.data.sql_manager import TradingDataManager, get_trading_dashboard_data, get_latest_sentiment_all_banks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="ASX Trading Analysis - SQL Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_dashboard_data():
    """Load all dashboard data from SQL database"""
    try:
        return get_trading_dashboard_data()
    except Exception as e:
        logger.error(f"Error loading dashboard data: {e}")
        return {}

@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_sentiment_history(symbol: str, days: int = 7):
    """Load sentiment history for a specific bank"""
    try:
        data_manager = TradingDataManager()
        df = data_manager.get_sentiment_history(symbol, days_back=days)
        return df
    except Exception as e:
        logger.error(f"Error loading sentiment history for {symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_performance_metrics():
    """Load trading performance metrics"""
    try:
        data_manager = TradingDataManager()
        return data_manager.get_performance_summary()
    except Exception as e:
        logger.error(f"Error loading performance metrics: {e}")
        return {}

def create_sentiment_gauge(sentiment_score: float, confidence: float) -> go.Figure:
    """Create gauge chart for sentiment"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = sentiment_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Sentiment (Confidence: {confidence:.1%})"},
        delta = {'reference': 0},
        gauge = {
            'axis': {'range': [None, 1]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [-1, -0.3], 'color': "lightred"},
                {'range': [-0.3, 0.3], 'color': "lightyellow"},
                {'range': [0.3, 1], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0.5
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_sentiment_timeline(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Create sentiment timeline chart"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    fig = go.Figure()
    
    # Add sentiment score line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['sentiment_score'],
        mode='lines+markers',
        name='Sentiment Score',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))
    
    # Add confidence as fill area
    if 'confidence' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['confidence'],
            mode='lines',
            name='Confidence',
            line=dict(color='gray', width=1, dash='dash'),
            yaxis='y2'
        ))
    
    fig.update_layout(
        title=f"{symbol} Sentiment Timeline",
        xaxis_title="Date",
        yaxis_title="Sentiment Score",
        yaxis2=dict(
            title="Confidence",
            overlaying='y',
            side='right'
        ),
        height=400,
        hovermode='x unified'
    )
    
    return fig

def display_trading_signals(signals: list):
    """Display active trading signals"""
    if not signals:
        st.info("No active trading signals")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(signals)
    
    # Color code by signal type
    def get_signal_color(signal_type):
        colors = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}
        return colors.get(signal_type, '⚪')
    
    df['Signal'] = df['signal_type'].apply(lambda x: f"{get_signal_color(x)} {x}")
    
    # Display in columns
    for i, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
        
        with col1:
            st.metric("Symbol", row['symbol'])
        
        with col2:
            st.metric("Signal", row['Signal'])
        
        with col3:
            st.metric("Strength", f"{row['strength']:.2f}")
        
        with col4:
            st.write(f"**ML Confidence:** {row['ml_confidence']:.1%}")
            st.write(f"**Economic Regime:** {row['economic_regime']}")
            if row['reasoning']:
                with st.expander("Reasoning"):
                    st.write(row['reasoning'])
        
        st.divider()

def display_positions_table(positions: list):
    """Display positions in a formatted table"""
    if not positions:
        st.info("No open positions")
        return
    
    df = pd.DataFrame(positions)
    
    # Format columns for display
    display_columns = ['symbol', 'entry_date', 'position_type', 'entry_price', 
                      'position_size', 'ml_confidence']
    
    if 'profit_loss' in df.columns:
        display_columns.extend(['profit_loss', 'return_percentage'])
    
    # Format numeric columns
    if 'entry_price' in df.columns:
        df['entry_price'] = df['entry_price'].apply(lambda x: f"${x:.2f}")
    if 'profit_loss' in df.columns:
        df['profit_loss'] = df['profit_loss'].apply(lambda x: f"${x:+.2f}" if pd.notna(x) else "Open")
    if 'return_percentage' in df.columns:
        df['return_percentage'] = df['return_percentage'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "Open")
    if 'ml_confidence' in df.columns:
        df['ml_confidence'] = df['ml_confidence'].apply(lambda x: f"{x:.1%}")
    
    # Display table
    st.dataframe(
        df[display_columns].rename(columns={
            'symbol': 'Symbol',
            'entry_date': 'Entry Date',
            'position_type': 'Type',
            'entry_price': 'Entry Price',
            'position_size': 'Size',
            'ml_confidence': 'ML Confidence',
            'profit_loss': 'P&L',
            'return_percentage': 'Return %'
        }),
        use_container_width=True
    )

def main():
    """Main dashboard function"""
    # Header
    st.title("📈 ASX Trading Analysis Dashboard")
    st.markdown("*Real-time sentiment analysis, ML predictions, and trading signals*")
    
    # Sidebar controls
    st.sidebar.title("Dashboard Controls")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (5 min)", value=True)
    if auto_refresh:
        st.sidebar.success("Auto-refresh enabled")
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Time range selector
    time_range = st.sidebar.selectbox(
        "Sentiment History Range",
        ["1 day", "3 days", "7 days", "14 days", "30 days"],
        index=2
    )
    days_back = {"1 day": 1, "3 days": 3, "7 days": 7, "14 days": 14, "30 days": 30}[time_range]
    
    # Load data
    with st.spinner("Loading dashboard data..."):
        dashboard_data = load_dashboard_data()
    
    if not dashboard_data:
        st.error("Failed to load dashboard data. Check database connection.")
        return
    
    # Main dashboard layout
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💭 Sentiment Analysis", "📈 Trading Signals", "💼 Positions"])
    
    with tab1:
        st.header("System Overview")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        performance = dashboard_data.get('performance', {})
        
        with col1:
            st.metric(
                "Total P&L",
                f"${performance.get('total_pnl', 0):+,.2f}",
                delta=f"{performance.get('win_rate', 0):.1f}% win rate"
            )
        
        with col2:
            st.metric(
                "Open Positions",
                performance.get('open_positions', 0),
                delta=f"{performance.get('closed_positions', 0)} closed"
            )
        
        with col3:
            active_signals = len(dashboard_data.get('active_signals', []))
            st.metric(
                "Active Signals",
                active_signals,
                delta="Live analysis"
            )
        
        with col4:
            avg_return = performance.get('avg_return_pct', 0)
            st.metric(
                "Avg Return",
                f"{avg_return:+.1f}%",
                delta=f"PF: {performance.get('profit_factor', 0):.2f}"
            )
        
        # Recent activity
        st.subheader("Recent Activity")
        
        # Show recent predictions
        recent_predictions = dashboard_data.get('recent_predictions', [])
        if recent_predictions:
            st.write("**Pending ML Predictions:**")
            pred_df = pd.DataFrame(recent_predictions)
            st.dataframe(
                pred_df[['symbol', 'prediction_type', 'predicted_value', 'confidence_score', 'timestamp']].head(5),
                use_container_width=True
            )
        else:
            st.info("No pending predictions")
    
    with tab2:
        st.header("Bank Sentiment Analysis")
        
        sentiment_data = dashboard_data.get('sentiment', {})
        
        if sentiment_data:
            # Create sentiment overview
            bank_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'QBE.AX', 'SUN.AX']
            
            # Sentiment gauges
            cols = st.columns(3)
            for i, symbol in enumerate(bank_symbols[:6]):  # Show first 6 banks
                with cols[i % 3]:
                    if symbol in sentiment_data:
                        data = sentiment_data[symbol]
                        sentiment_score = data.get('sentiment_score', 0)
                        confidence = data.get('confidence', 0)
                        
                        # Create gauge
                        fig = create_sentiment_gauge(sentiment_score, confidence)
                        fig.update_layout(title=f"{symbol.replace('.AX', '')}")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show additional metrics
                        stage_1 = data.get('stage_1_score')
                        stage_2 = data.get('stage_2_score')
                        if stage_1 is not None and stage_2 is not None:
                            st.write(f"Stage 1: {stage_1:.3f} | Stage 2: {stage_2:.3f}")
                    else:
                        st.info(f"No data for {symbol}")
            
            # Detailed sentiment history
            st.subheader("Sentiment Timeline")
            
            selected_bank = st.selectbox(
                "Select bank for detailed view:",
                bank_symbols
            )
            
            if selected_bank:
                sentiment_history = load_sentiment_history(selected_bank, days_back)
                if not sentiment_history.empty:
                    fig = create_sentiment_timeline(sentiment_history, selected_bank)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show raw data
                    with st.expander("Raw Data"):
                        st.dataframe(sentiment_history.tail(20))
                else:
                    st.info(f"No sentiment history for {selected_bank}")
        else:
            st.warning("No sentiment data available")
    
    with tab3:
        st.header("Trading Signals")
        
        active_signals = dashboard_data.get('active_signals', [])
        display_trading_signals(active_signals)
        
        # Signal strength distribution
        if active_signals:
            st.subheader("Signal Strength Distribution")
            
            signal_df = pd.DataFrame(active_signals)
            fig = px.histogram(
                signal_df,
                x='strength',
                color='signal_type',
                title="Distribution of Signal Strengths",
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.header("Position Management")
        
        # Open positions
        st.subheader("Open Positions")
        open_positions = dashboard_data.get('open_positions', [])
        display_positions_table(open_positions)
        
        # Performance summary
        st.subheader("Performance Summary")
        performance = dashboard_data.get('performance', {})
        
        if performance:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Trading Statistics:**")
                st.write(f"• Total Positions: {performance.get('total_positions', 0)}")
                st.write(f"• Win Rate: {performance.get('win_rate', 0):.1f}%")
                st.write(f"• Profit Factor: {performance.get('profit_factor', 0):.2f}")
                st.write(f"• Average Return: {performance.get('avg_return_pct', 0):+.1f}%")
            
            with col2:
                st.write("**P&L Breakdown:**")
                st.write(f"• Total P&L: ${performance.get('total_pnl', 0):+,.2f}")
                st.write(f"• Average Win: ${performance.get('avg_win', 0):.2f}")
                st.write(f"• Average Loss: ${performance.get('avg_loss', 0):.2f}")
                st.write(f"• Winning Trades: {performance.get('winning_trades', 0)}")
                st.write(f"• Losing Trades: {performance.get('losing_trades', 0)}")
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        data_manager = TradingDataManager()
        if data_manager.db_path.exists():
            st.write(f"**Database:** Connected ✅")
        else:
            st.write(f"**Database:** Disconnected ❌")
    
    with col3:
        # Quick actions
        if st.button("🧹 Cleanup Cache"):
            try:
                data_manager = TradingDataManager()
                expired_count = data_manager.cleanup_expired_cache()
                st.success(f"Cleaned up {expired_count} expired cache entries")
            except Exception as e:
                st.error(f"Cleanup failed: {e}")

if __name__ == "__main__":
    main()