#!/usr/bin/env python3
"""
Streamlit Dashboard for Realistic Trading Simulation
Shows how ML predictions would perform with real trading constraints
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from realistic_trading_simulator import RealisticTradingSimulator
import json
from pathlib import Path

def load_simulation_results():
    """Load existing simulation results if available"""
    results_file = Path("realistic_trading_simulation_results.json")
    if results_file.exists():
        with open(results_file, 'r') as f:
            return json.load(f)
    return None

def run_new_simulation(days, min_confidence, trade_amount, initial_capital):
    """Run a new simulation with specified parameters"""
    simulator = RealisticTradingSimulator(initial_capital=initial_capital)
    simulator.trade_amount = trade_amount
    simulator.min_confidence = min_confidence / 100  # Convert percentage to decimal
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    with st.spinner("Running realistic trading simulation..."):
        results = simulator.simulate_trading(start_date, end_date)
    
    return results, simulator

def create_performance_chart(trades_df):
    """Create cumulative performance chart"""
    if trades_df.empty:
        return go.Figure()
    
    # Calculate cumulative P&L
    trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
    trades_df['trade_number'] = range(1, len(trades_df) + 1)
    
    fig = go.Figure()
    
    # Cumulative P&L line
    fig.add_trace(go.Scatter(
        x=trades_df['trade_number'],
        y=trades_df['cumulative_pnl'],
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))
    
    # Add individual trade markers
    winning_trades = trades_df[trades_df['pnl'] > 0]
    losing_trades = trades_df[trades_df['pnl'] <= 0]
    
    if not winning_trades.empty:
        fig.add_trace(go.Scatter(
            x=winning_trades['trade_number'],
            y=winning_trades['cumulative_pnl'],
            mode='markers',
            name='Winning Trades',
            marker=dict(color='green', size=12, symbol='triangle-up')
        ))
    
    if not losing_trades.empty:
        fig.add_trace(go.Scatter(
            x=losing_trades['trade_number'],
            y=losing_trades['cumulative_pnl'],
            mode='markers',
            name='Losing Trades',
            marker=dict(color='red', size=12, symbol='triangle-down')
        ))
    
    fig.update_layout(
        title="Cumulative Trading Performance",
        xaxis_title="Trade Number",
        yaxis_title="Cumulative P&L ($)",
        height=400,
        showlegend=True
    )
    
    return fig

def create_trade_distribution_chart(trades_df):
    """Create trade distribution charts"""
    if trades_df.empty:
        return go.Figure()
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Return Distribution', 'Trades by Symbol', 'Trades by Action', 'Exit Reasons'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Return distribution histogram
    fig.add_trace(
        go.Histogram(
            x=trades_df['return_pct'] * 100,
            nbinsx=20,
            name='Returns',
            marker_color='lightblue'
        ),
        row=1, col=1
    )
    
    # Trades by symbol
    symbol_counts = trades_df['symbol'].value_counts()
    fig.add_trace(
        go.Bar(
            x=symbol_counts.index,
            y=symbol_counts.values,
            name='By Symbol',
            marker_color='lightgreen'
        ),
        row=1, col=2
    )
    
    # Trades by action
    action_counts = trades_df['action'].value_counts()
    fig.add_trace(
        go.Bar(
            x=action_counts.index,
            y=action_counts.values,
            name='By Action',
            marker_color='orange'
        ),
        row=2, col=1
    )
    
    # Exit reasons
    reason_counts = trades_df['reason'].value_counts()
    fig.add_trace(
        go.Bar(
            x=reason_counts.index,
            y=reason_counts.values,
            name='Exit Reasons',
            marker_color='purple'
        ),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False)
    fig.update_xaxes(title_text="Return (%)", row=1, col=1)
    fig.update_xaxes(title_text="Symbol", row=1, col=2)
    fig.update_xaxes(title_text="Action", row=2, col=1)
    fig.update_xaxes(title_text="Exit Reason", row=2, col=2)
    fig.update_yaxes(title_text="Frequency", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=2)
    
    return fig

def main():
    st.set_page_config(
        page_title="Realistic Trading Simulator", 
        page_icon="💰", 
        layout="wide"
    )
    
    st.title("💰 Realistic Trading Simulation Dashboard")
    st.markdown("### See how your ML predictions would perform with real trading constraints")
    st.markdown("---")
    
    # Sidebar controls
    st.sidebar.header("🎛️ Simulation Parameters")
    
    # Load existing results
    existing_results = load_simulation_results()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📊 Load Last Results") and existing_results:
            st.session_state['simulation_results'] = existing_results
            st.session_state['last_simulator'] = None
    
    with col2:
        if st.button("🔄 New Simulation"):
            if 'simulation_results' in st.session_state:
                del st.session_state['simulation_results']
    
    # Simulation parameters
    st.sidebar.subheader("📈 Trading Parameters")
    days = st.sidebar.slider("Simulation Period (days)", 7, 90, 30)
    min_confidence = st.sidebar.slider("Minimum Confidence (%)", 50, 95, 75)
    
    st.sidebar.subheader("💰 Capital Parameters")
    initial_capital = st.sidebar.number_input("Initial Capital ($)", 10000, 1000000, 100000, step=10000)
    trade_amount = st.sidebar.number_input("Trade Amount per Position ($)", 1000, 50000, 15000, step=1000)
    
    # Risk management info
    st.sidebar.subheader("⚠️ Risk Management")
    st.sidebar.info("""
    **Automatic Risk Controls:**
    - 5% Stop Loss
    - 10% Take Profit  
    - Max 4 hour holding period
    - One position per symbol
    - Max 7 positions total
    - Only stable trading hours (11:30 AM - 3:30 PM AEST)
    """)
    
    # Run simulation button
    if st.sidebar.button("🚀 Run Simulation"):
        results, simulator = run_new_simulation(days, min_confidence, trade_amount, initial_capital)
        st.session_state['simulation_results'] = results
        st.session_state['last_simulator'] = {
            'initial_capital': initial_capital,
            'trade_amount': trade_amount,
            'min_confidence': min_confidence
        }
        st.success("Simulation completed!")
    
    # Display results
    if 'simulation_results' in st.session_state:
        results = st.session_state['simulation_results']
        simulator_params = st.session_state.get('last_simulator', {})
        
        # Key metrics
        st.subheader("📊 Simulation Results")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Trades",
                results['total_trades'],
                delta=f"{results['winning_trades']} winners"
            )
        
        with col2:
            win_rate = results['win_rate']
            win_delta = "🎯 Excellent" if win_rate > 0.7 else "✅ Good" if win_rate > 0.6 else "⚠️ Needs Work"
            st.metric(
                "Win Rate",
                f"{win_rate:.1%}",
                delta=win_delta
            )
        
        with col3:
            total_return = results['total_return']
            return_delta = "🚀 Great" if total_return > 0.05 else "📈 Positive" if total_return > 0 else "📉 Loss"
            st.metric(
                "Total Return",
                f"{total_return:+.2%}",
                delta=return_delta
            )
        
        with col4:
            st.metric(
                "Total P&L",
                f"${results['total_pnl']:+,.2f}",
                delta="Profit" if results['total_pnl'] > 0 else "Loss"
            )
        
        with col5:
            final_value = results['final_portfolio_value']
            initial_value = simulator_params.get('initial_capital', 100000)
            st.metric(
                "Final Portfolio",
                f"${final_value:,.2f}",
                delta=f"${final_value - initial_value:+,.2f}"
            )
        
        # Performance assessment
        st.subheader("💡 Performance Assessment")
        
        if results['total_trades'] > 0:
            if win_rate > 0.7 and total_return > 0.05:
                st.success("🚀 **EXCELLENT PERFORMANCE!** Your ML predictions show strong profitability with realistic trading constraints. Consider increasing position sizes or trading frequency.")
            elif win_rate > 0.6 and total_return > 0.02:
                st.success("✅ **SOLID PERFORMANCE!** Your predictions are consistently profitable. Fine-tune confidence thresholds for optimization.")
            elif win_rate > 0.5 and total_return > 0:
                st.info("📈 **POSITIVE RESULTS!** Your system is profitable but has room for improvement. Consider adjusting risk management or entry timing.")
            else:
                st.warning("⚠️ **NEEDS OPTIMIZATION!** Results suggest adjusting confidence thresholds, improving entry timing, or refining the ML model.")
            
            # Best/worst trade info
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Best Trade", f"{results['best_trade']:+.2%}")
                st.metric("Average Trade", f"{results['avg_trade_return']:+.2%}")
            with col2:
                st.metric("Worst Trade", f"{results['worst_trade']:+.2%}")
                # Calculate Sharpe-like ratio
                if results['total_trades'] > 1:
                    trades_df = pd.DataFrame(results['trades'])
                    sharpe_approx = trades_df['return_pct'].mean() / trades_df['return_pct'].std() if trades_df['return_pct'].std() > 0 else 0
                    st.metric("Risk-Adjusted Return", f"{sharpe_approx:.2f}")
        else:
            st.warning("📭 **NO QUALIFYING TRADES** found for the simulation period. Try:")
            st.info("""
            - **Longer time period** (60-90 days)
            - **Lower confidence threshold** (60-70%)
            - **Check if predictions exist** in the selected period
            """)
        
        # Charts and detailed analysis
        if results['trades']:
            trades_df = pd.DataFrame(results['trades'])
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
            trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])
            
            # Performance chart
            st.subheader("📈 Cumulative Performance")
            perf_chart = create_performance_chart(trades_df)
            st.plotly_chart(perf_chart, use_container_width=True)
            
            # Distribution charts
            st.subheader("📊 Trade Analysis")
            dist_chart = create_trade_distribution_chart(trades_df)
            st.plotly_chart(dist_chart, use_container_width=True)
            
            # Detailed trades table
            st.subheader("📋 Trade Details")
            
            # Format trades for display
            display_trades = trades_df.copy()
            # Convert UTC to AEST for display (UTC + 10 hours)
            display_trades['Entry Time'] = (display_trades['entry_time'] + pd.Timedelta(hours=10)).dt.strftime('%Y-%m-%d %H:%M AEST')
            display_trades['Exit Time'] = (display_trades['exit_time'] + pd.Timedelta(hours=10)).dt.strftime('%Y-%m-%d %H:%M AEST')
            display_trades['P&L'] = display_trades['pnl'].apply(lambda x: f"${x:+,.2f}")
            display_trades['Return'] = display_trades['return_pct'].apply(lambda x: f"{x:+.2%}")
            display_trades['Confidence'] = display_trades['confidence'].apply(lambda x: f"{x:.1%}")
            display_trades['Entry Price'] = display_trades['entry_price'].apply(lambda x: f"${x:.2f}")
            display_trades['Exit Price'] = display_trades['exit_price'].apply(lambda x: f"${x:.2f}")
            display_trades['Result'] = display_trades['successful'].apply(lambda x: "✅ Win" if x else "❌ Loss")
            
            # Show table
            cols_to_show = ['symbol', 'action', 'Entry Time', 'Exit Time', 'Entry Price', 'Exit Price', 
                           'Confidence', 'P&L', 'Return', 'reason', 'Result']
            
            st.dataframe(
                display_trades[cols_to_show],
                column_config={
                    "symbol": "Symbol",
                    "action": "Action",
                    "Entry Time": "Entry Time",
                    "Exit Time": "Exit Time", 
                    "Entry Price": "Entry Price",
                    "Exit Price": "Exit Price",
                    "Confidence": "Confidence",
                    "P&L": "P&L",
                    "Return": "Return %",
                    "reason": "Exit Reason",
                    "Result": "Result"
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Summary insights
            st.subheader("🔍 Trading Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Symbol Performance:**")
                symbol_perf = trades_df.groupby('symbol').agg({
                    'return_pct': 'mean',
                    'successful': 'mean',
                    'pnl': 'sum'
                }).round(3)
                symbol_perf.columns = ['Avg Return', 'Win Rate', 'Total P&L']
                st.dataframe(symbol_perf)
            
            with col2:
                st.write("**Action Performance:**")
                action_perf = trades_df.groupby('action').agg({
                    'return_pct': 'mean',
                    'successful': 'mean',
                    'pnl': 'sum'
                }).round(3)
                action_perf.columns = ['Avg Return', 'Win Rate', 'Total P&L']
                st.dataframe(action_perf)
            
            # Confidence analysis
            if len(trades_df) >= 5:
                st.write("**Confidence vs Performance:**")
                conf_bins = pd.cut(trades_df['confidence'], bins=5, labels=['Low', 'Med-Low', 'Medium', 'Med-High', 'High'])
                conf_perf = trades_df.groupby(conf_bins).agg({
                    'return_pct': 'mean',
                    'successful': 'mean',
                    'confidence': 'count'
                }).round(3)
                conf_perf.columns = ['Avg Return', 'Win Rate', 'Trade Count']
                st.dataframe(conf_perf)
        
        # Simulation parameters summary
        st.subheader("⚙️ Simulation Parameters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"""
            **Trading Rules:**
            - Min Confidence: {min_confidence}%
            - Trade Amount: ${trade_amount:,}
            - Max Positions: 7
            """)
        
        with col2:
            st.info(f"""
            **Risk Management:**
            - Stop Loss: 5%
            - Take Profit: 10%
            - Max Hold: 4 hours
            """)
        
        with col3:
            st.info(f"""
            **Market Constraints:**
            - Trading Hours: 11:30 AM - 3:30 PM AEST
            - yfinance Delay: 15 minutes
            - One position per symbol
            """)
    
    else:
        # Show introduction
        st.subheader("🎯 What This Simulation Shows")
        st.info("""
        This realistic trading simulator shows how your ML predictions would have performed with **real-world constraints**:
        
        **✅ Realistic Constraints:**
        - Only trades during stable market hours (11:30 AM - 3:30 PM AEST)
        - Accounts for yfinance data delays (15 minutes)
        - Proper risk management (stop loss, take profit)
        - Position sizing ($15,000 default per trade)
        - One position per symbol at a time
        
        **📊 What You'll Learn:**
        - Actual profitability of your predictions
        - Win rate with realistic timing
        - Risk-adjusted returns
        - Best performing symbols and strategies
        - Impact of confidence thresholds
        """)
        
        st.subheader("🚀 Get Started")
        st.success("Configure your simulation parameters in the sidebar and click **'Run Simulation'** to see how your ML predictions would perform in real trading!")

if __name__ == "__main__":
    main()
