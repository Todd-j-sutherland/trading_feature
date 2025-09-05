#!/usr/bin/env python3
"""
Paper Trading Dashboard - Streamlit Interface
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import *
from trading.engine import PaperTradingEngine, StrategyInterface, TradeResult
from config import TRADING_CONFIG, SUPPORTED_SYMBOLS

# Page config
st.set_page_config(
    page_title="Paper Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and engine
@st.cache_resource
def init_database():
    """Initialize database connection"""
    engine = create_database()
    session = get_session(engine)
    account = init_default_account(session, TRADING_CONFIG['initial_balance'])
    return engine, session, account.id

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_portfolio_data(account_id):
    """Get portfolio data with caching"""
    engine, session, _ = init_database()
    trading_engine = PaperTradingEngine(session, account_id)
    return trading_engine.get_portfolio_summary()

def main():
    st.title("📈 Paper Trading Dashboard")
    st.markdown("---")
    
    # Initialize
    engine, session, account_id = init_database()
    trading_engine = PaperTradingEngine(session, account_id)
    strategy_interface = StrategyInterface(trading_engine)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Navigation")
        page = st.selectbox(
            "Select Page",
            ["Portfolio Overview", "Trading", "Performance Analytics", "Strategy Testing", "Trade History"]
        )
        
        st.markdown("---")
        
        # Quick stats
        portfolio_data = get_portfolio_data(account_id)
        if portfolio_data:
            account_data = portfolio_data.get('account', {})
            st.metric(
                "Portfolio Value",
                f"${account_data.get('portfolio_value', 0):,.2f}",
                f"{account_data.get('total_pnl_pct', 0):+.2f}%"
            )
            st.metric(
                "Cash Balance",
                f"${account_data.get('cash_balance', 0):,.2f}"
            )
            st.metric(
                "Total P&L",
                f"${account_data.get('total_pnl', 0):+,.2f}"
            )
    
    # Main content
    if page == "Portfolio Overview":
        show_portfolio_overview(trading_engine, portfolio_data)
    elif page == "Trading":
        show_trading_interface(trading_engine, strategy_interface)
    elif page == "Performance Analytics":
        show_performance_analytics(session, account_id)
    elif page == "Strategy Testing":
        show_strategy_testing(strategy_interface)
    elif page == "Trade History":
        show_trade_history(session, account_id)

def show_portfolio_overview(trading_engine, portfolio_data):
    """Display portfolio overview page"""
    st.header("Portfolio Overview")
    
    if not portfolio_data:
        st.error("Unable to load portfolio data")
        return
    
    account_data = portfolio_data.get('account', {})
    positions = portfolio_data.get('positions', [])
    summary = portfolio_data.get('summary', {})
    
    # Account summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Portfolio Value",
            f"${account_data.get('portfolio_value', 0):,.2f}",
            f"{account_data.get('total_pnl_pct', 0):+.2f}%"
        )
    
    with col2:
        st.metric(
            "Cash Balance",
            f"${account_data.get('cash_balance', 0):,.2f}"
        )
    
    with col3:
        st.metric(
            "Total P&L",
            f"${account_data.get('total_pnl', 0):+,.2f}"
        )
    
    with col4:
        st.metric(
            "Positions",
            summary.get('total_positions', 0)
        )
    
    st.markdown("---")
    
    # Portfolio allocation chart
    if positions:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Portfolio Allocation")
            
            # Create pie chart
            symbols = [pos['symbol'] for pos in positions]
            values = [pos['market_value'] for pos in positions]
            
            # Add cash as separate slice
            symbols.append('CASH')
            values.append(account_data.get('cash_balance', 0))
            
            fig = px.pie(
                values=values,
                names=symbols,
                title="Portfolio Allocation",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Position Performance")
            
            # Position performance chart
            symbols = [pos['symbol'] for pos in positions]
            pnl_pcts = [pos['unrealized_pnl_pct'] for pos in positions]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=symbols,
                    y=pnl_pcts,
                    marker_color=['green' if x >= 0 else 'red' for x in pnl_pcts]
                )
            ])
            fig.update_layout(
                title="Unrealized P&L %",
                xaxis_title="Symbol",
                yaxis_title="P&L %",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Positions table
    if positions:
        st.subheader("Current Positions")
        
        df = pd.DataFrame(positions)
        df['avg_cost'] = df['avg_cost'].apply(lambda x: f"${x:.2f}")
        df['current_price'] = df['current_price'].apply(lambda x: f"${x:.2f}")
        df['market_value'] = df['market_value'].apply(lambda x: f"${x:,.2f}")
        df['unrealized_pnl'] = df['unrealized_pnl'].apply(lambda x: f"${x:+,.2f}")
        df['unrealized_pnl_pct'] = df['unrealized_pnl_pct'].apply(lambda x: f"{x:+.2f}%")
        
        st.dataframe(
            df[['symbol', 'quantity', 'avg_cost', 'current_price', 'market_value', 'unrealized_pnl', 'unrealized_pnl_pct']],
            use_container_width=True
        )
    else:
        st.info("No positions currently held")

def show_trading_interface(trading_engine, strategy_interface):
    """Display trading interface"""
    st.header("Trading Interface")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Manual Trading")
        
        # Trading form
        with st.form("manual_trade"):
            symbol = st.selectbox("Symbol", SUPPORTED_SYMBOLS['ASX'] + SUPPORTED_SYMBOLS['US'])
            action = st.selectbox("Action", ["BUY", "SELL"])
            quantity = st.number_input("Quantity", min_value=1, value=100, step=1)
            notes = st.text_area("Notes (optional)")
            
            submitted = st.form_submit_button("Execute Trade")
            
            if submitted:
                if action == "BUY":
                    result = trading_engine.execute_market_buy(
                        symbol=symbol,
                        quantity=quantity,
                        strategy_source="Manual",
                        notes=notes
                    )
                else:
                    result = trading_engine.execute_market_sell(
                        symbol=symbol,
                        quantity=quantity,
                        strategy_source="Manual",
                        notes=notes
                    )
                
                if result.success:
                    st.success(result.message)
                    st.rerun()
                else:
                    st.error(result.message)
    
    with col2:
        st.subheader("Quick Actions")
        
        # Get current positions for quick sell
        portfolio_data = get_portfolio_data(trading_engine.account_id)
        positions = portfolio_data.get('positions', [])
        
        if positions:
            st.write("**Quick Sell Positions:**")
            for pos in positions[:5]:  # Show top 5 positions
                col_a, col_b, col_c = st.columns([2, 1, 1])
                with col_a:
                    st.write(f"{pos['symbol']} ({pos['quantity']} shares)")
                with col_b:
                    st.write(f"${pos['unrealized_pnl']:+,.2f}")
                with col_c:
                    if st.button(f"Sell All", key=f"sell_{pos['symbol']}"):
                        result = trading_engine.execute_market_sell(
                            symbol=pos['symbol'],
                            quantity=pos['quantity'],
                            strategy_source="Quick_Sell"
                        )
                        if result.success:
                            st.success(f"Sold {pos['symbol']}")
                            st.rerun()
                        else:
                            st.error(result.message)
        
        st.markdown("---")
        
        # Market data
        st.subheader("Live Prices")
        selected_symbols = st.multiselect(
            "Select symbols to monitor",
            SUPPORTED_SYMBOLS['ASX'][:10] + SUPPORTED_SYMBOLS['US'][:10],
            default=['AAPL', 'CBA.AX']
        )
        
        if selected_symbols:
            price_data = []
            for symbol in selected_symbols:
                price = trading_engine.get_current_price(symbol)
                if price:
                    price_data.append({'Symbol': symbol, 'Price': f"${price:.2f}"})
            
            if price_data:
                st.dataframe(pd.DataFrame(price_data), use_container_width=True)

def show_performance_analytics(session, account_id):
    """Display performance analytics"""
    st.header("Performance Analytics")
    
    # Get trade data
    trades = session.query(Trade).filter_by(account_id=account_id).order_by(Trade.timestamp.desc()).all()
    
    if not trades:
        st.info("No trades yet to analyze")
        return
    
    # Convert to DataFrame
    trade_data = []
    for trade in trades:
        trade_data.append({
            'timestamp': trade.timestamp,
            'symbol': trade.symbol,
            'side': trade.side,
            'quantity': trade.quantity,
            'price': trade.price,
            'pnl': trade.pnl or 0,
            'commission': trade.commission,
            'strategy': trade.strategy_source
        })
    
    df = pd.DataFrame(trade_data)
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_trades = len(df)
    winning_trades = len(df[df['pnl'] > 0])
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    total_pnl = df['pnl'].sum()
    
    with col1:
        st.metric("Total Trades", total_trades)
    with col2:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col3:
        st.metric("Total P&L", f"${total_pnl:+,.2f}")
    with col4:
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        st.metric("Avg P&L", f"${avg_pnl:+.2f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("P&L Over Time")
        df['cumulative_pnl'] = df['pnl'].cumsum()
        
        fig = px.line(
            df,
            x='timestamp',
            y='cumulative_pnl',
            title="Cumulative P&L"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Strategy Performance")
        strategy_performance = df.groupby('strategy').agg({
            'pnl': 'sum',
            'symbol': 'count'
        }).rename(columns={'symbol': 'trades'})
        
        fig = px.bar(
            strategy_performance,
            x=strategy_performance.index,
            y='pnl',
            title="P&L by Strategy"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_strategy_testing(strategy_interface):
    """Display strategy testing interface"""
    st.header("Strategy Testing")
    
    st.subheader("Test Trading Signal")
    
    with st.form("strategy_signal"):
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.selectbox("Symbol", SUPPORTED_SYMBOLS['ASX'] + SUPPORTED_SYMBOLS['US'])
            action = st.selectbox("Action", ["BUY", "SELL"])
            quantity = st.number_input("Quantity", min_value=1, value=100)
        
        with col2:
            strategy_name = st.text_input("Strategy Name", value="Test_Strategy")
            confidence = st.slider("Confidence", 0.0, 1.0, 0.5, 0.01)
            reasoning = st.text_area("Reasoning")
        
        submitted = st.form_submit_button("Execute Strategy Signal")
        
        if submitted:
            signal = {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'strategy': strategy_name,
                'confidence': confidence,
                'reasoning': reasoning
            }
            
            result = strategy_interface.execute_strategy_signal(signal)
            
            if result.success:
                st.success(result.message)
            else:
                st.error(result.message)
    
    st.markdown("---")
    
    # Strategy performance comparison
    st.subheader("Strategy Performance Comparison")
    
    # Get available strategies
    engine, session, account_id = init_database()
    strategies = session.query(Trade.strategy_source).filter_by(account_id=account_id).distinct().all()
    strategy_names = [s[0] for s in strategies if s[0]]
    
    if strategy_names:
        performance_data = []
        for strategy in strategy_names:
            perf = strategy_interface.get_strategy_performance(strategy)
            if 'error' not in perf:
                performance_data.append(perf)
        
        if performance_data:
            df = pd.DataFrame(performance_data)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No strategy data available yet")

def show_trade_history(session, account_id):
    """Display trade history"""
    st.header("Trade History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_back = st.selectbox("Time Period", [7, 30, 90, 365], index=1)
    with col2:
        side_filter = st.selectbox("Side", ["All", "BUY", "SELL"])
    with col3:
        strategy_filter = st.selectbox("Strategy", ["All"] + ["Manual", "Test_Strategy", "Quick_Sell"])
    
    # Query trades
    query = session.query(Trade).filter_by(account_id=account_id)
    
    # Apply filters
    start_date = datetime.now() - timedelta(days=days_back)
    query = query.filter(Trade.timestamp >= start_date)
    
    if side_filter != "All":
        query = query.filter(Trade.side == side_filter)
    
    if strategy_filter != "All":
        query = query.filter(Trade.strategy_source == strategy_filter)
    
    trades = query.order_by(Trade.timestamp.desc()).all()
    
    if trades:
        # Convert to DataFrame
        trade_data = []
        for trade in trades:
            trade_data.append({
                'Timestamp': trade.timestamp.strftime('%Y-%m-%d %H:%M'),
                'Symbol': trade.symbol,
                'Side': trade.side,
                'Quantity': trade.quantity,
                'Price': f"${trade.price:.2f}",
                'Total Value': f"${trade.total_value:,.2f}",
                'Commission': f"${trade.commission:.2f}",
                'P&L': f"${trade.pnl or 0:+.2f}",
                'Strategy': trade.strategy_source or 'N/A',
                'Confidence': f"{trade.confidence:.2%}" if trade.confidence else 'N/A'
            })
        
        df = pd.DataFrame(trade_data)
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No trades found for the selected criteria")

if __name__ == "__main__":
    main()
