#!/usr/bin/env python3
"""
Backtesting Dashboard

Streamlit interface for the comprehensive backtesting system.
Provides interactive visualization of all trading strategies and their performance.
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import pandas as pd
import json

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.backtesting.comprehensive_backtester import ComprehensiveBacktester

st.set_page_config(
    page_title="Trading Strategy Backtesting Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the backtester
@st.cache_resource
def get_backtester():
    return ComprehensiveBacktester()

def main():
    st.title("📈 Comprehensive Trading Strategy Backtesting")
    st.markdown("**Analyze historical performance across multiple data sources and strategies**")
    
    backtester = get_backtester()
    
    # Sidebar controls
    st.sidebar.header("Analysis Configuration")
    
    # Symbol selection
    all_symbols = backtester.bank_symbols
    selected_symbols = st.sidebar.multiselect(
        "Select Symbols to Analyze",
        all_symbols,
        default=['CBA.AX', 'WBC.AX', 'ANZ.AX']
    )
    
    # Analysis type selection
    analysis_types = st.sidebar.multiselect(
        "Select Analysis Types",
        [
            "Individual Symbol Analysis",
            "Strategy Comparison", 
            "Performance Metrics",
            "Combined Strategy Signals"
        ],
        default=["Individual Symbol Analysis", "Strategy Comparison"]
    )
    
    # Time period selection
    time_periods = {
        "1 Month": "1mo",
        "3 Months": "3mo", 
        "6 Months": "6mo",
        "1 Year": "1y"
    }
    
    selected_period = st.sidebar.selectbox(
        "Analysis Time Period",
        list(time_periods.keys()),
        index=1
    )
    
    if st.sidebar.button("🚀 Run Backtesting Analysis", type="primary"):
        if not selected_symbols:
            st.error("Please select at least one symbol to analyze.")
            return
        
        with st.spinner("Running comprehensive backtesting analysis..."):
            
            # Individual Symbol Analysis
            if "Individual Symbol Analysis" in analysis_types:
                st.header("📊 Individual Symbol Analysis")
                
                for symbol in selected_symbols:
                    with st.expander(f"📈 {symbol} Detailed Analysis", expanded=True):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # Create and display the comprehensive chart
                            fig = backtester.create_price_visualization(symbol)
                            if fig.data:  # Check if chart has data
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning(f"No data available for {symbol}")
                        
                        with col2:
                            # Display key metrics
                            try:
                                price_data = backtester.fetch_historical_prices(
                                    symbol, 
                                    period=time_periods[selected_period]
                                )
                                
                                if not price_data.empty:
                                    latest_price = price_data['Close'].iloc[-1]
                                    price_change = ((latest_price - price_data['Close'].iloc[0]) / price_data['Close'].iloc[0]) * 100
                                    volatility = price_data['Close'].pct_change().std() * 100
                                    
                                    st.metric(
                                        "Current Price",
                                        f"${latest_price:.2f}",
                                        f"{price_change:+.2f}%"
                                    )
                                    
                                    st.metric(
                                        "Volatility",
                                        f"{volatility:.2f}%"
                                    )
                                    
                                    st.metric(
                                        "Price Range",
                                        f"${price_data['Low'].min():.2f} - ${price_data['High'].max():.2f}"
                                    )
                                else:
                                    st.warning("No price data available")
                            except Exception as e:
                                st.error(f"Error loading metrics: {e}")
            
            # Strategy Comparison
            if "Strategy Comparison" in analysis_types:
                st.header("🔄 Strategy Comparison")
                
                try:
                    comparison_fig = backtester.create_strategy_comparison()
                    if comparison_fig.data:
                        st.plotly_chart(comparison_fig, use_container_width=True)
                        
                        # Additional strategy insights
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.subheader("📈 Traditional Analysis")
                            st.write("Based on technical indicators and sentiment")
                            st.write("• RSI-based signals")
                            st.write("• Moving average crossovers") 
                            st.write("• News sentiment integration")
                        
                        with col2:
                            st.subheader("🤖 ML Predictions")
                            st.write("Machine learning-based forecasting")
                            st.write("• Multi-timeframe predictions")
                            st.write("• Ensemble model confidence")
                            st.write("• Feature importance analysis")
                        
                        with col3:
                            st.subheader("🎯 Combined Strategy")
                            st.write("Smoothed composite signals")
                            st.write("• Weighted signal averaging")
                            st.write("• Confidence-based filtering")
                            st.write("• Risk-adjusted recommendations")
                    else:
                        st.warning("No strategy comparison data available")
                except Exception as e:
                    st.error(f"Error creating strategy comparison: {e}")
            
            # Performance Metrics
            if "Performance Metrics" in analysis_types:
                st.header("📋 Performance Metrics Summary")
                
                try:
                    performance_report = backtester.generate_performance_report()
                    
                    if performance_report['summary']:
                        summary = performance_report['summary']
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "Total Signals",
                                summary.get('total_signals_generated', 0)
                            )
                        
                        with col2:
                            st.metric(
                                "Data Sources",
                                summary.get('data_sources', 0)
                            )
                        
                        with col3:
                            st.metric(
                                "Symbols Covered",
                                summary.get('symbols_covered', 0)
                            )
                        
                        with col4:
                            st.metric(
                                "Analysis Period",
                                summary.get('analysis_period', 'N/A')
                            )
                        
                        # Strategy-specific metrics
                        if performance_report['strategy_metrics']:
                            st.subheader("Strategy-Specific Performance")
                            
                            for strategy, metrics in performance_report['strategy_metrics'].items():
                                with st.expander(f"📊 {strategy.replace('_', ' ').title()} Strategy"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write(f"**Total Signals:** {metrics.get('total_signals', 0)}")
                                        st.write(f"**Average Confidence:** {metrics.get('average_confidence', 0):.3f}")
                                        st.write(f"**Confidence Std Dev:** {metrics.get('confidence_std', 0):.3f}")
                                    
                                    with col2:
                                        signal_dist = metrics.get('signal_distribution', {})
                                        if signal_dist:
                                            st.write("**Signal Distribution:**")
                                            for signal, count in signal_dist.items():
                                                st.write(f"• {signal}: {count}")
                    else:
                        st.warning("No performance metrics available")
                except Exception as e:
                    st.error(f"Error generating performance report: {e}")
            
            # Combined Strategy Signals
            if "Combined Strategy Signals" in analysis_types:
                st.header("🎯 Combined Strategy Signals")
                
                st.info("**Smoothed Composite Strategy**: This combines all available signals (traditional technical analysis, sentiment analysis, and ML predictions) into a single smoothed line that represents the overall trading recommendation strength.")
                
                # Create a simplified combined view
                try:
                    sentiment_data = backtester.load_sentiment_data()
                    
                    if sentiment_data:
                        # Process all signals into a unified format
                        all_signals = []
                        for data_type, df in sentiment_data:
                            signals = backtester.extract_signals_from_data(data_type, df)
                            all_signals.append(signals)
                        
                        if all_signals:
                            combined_df = pd.concat(all_signals, ignore_index=True)
                            combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                            
                            # Create smoothed signals for selected symbols
                            fig = go.Figure()
                            
                            for symbol in selected_symbols:
                                symbol_data = combined_df[combined_df['symbol'] == symbol]
                                
                                if not symbol_data.empty:
                                    # Group by date and calculate composite score
                                    daily_data = symbol_data.groupby(symbol_data['timestamp'].dt.date).agg({
                                        'confidence': 'mean',
                                        'sentiment_score': 'mean'
                                    }).reset_index()
                                    
                                    # Calculate composite score (weighted combination)
                                    daily_data['composite_score'] = (
                                        daily_data['confidence'] * 0.7 + 
                                        abs(daily_data['sentiment_score']) * 0.3
                                    )
                                    
                                    # Apply smoothing
                                    daily_data = daily_data.sort_values('timestamp')
                                    daily_data['smoothed_score'] = daily_data['composite_score'].rolling(
                                        window=3, center=True, min_periods=1
                                    ).mean()
                                    
                                    # Add to chart
                                    fig.add_trace(go.Scatter(
                                        x=daily_data['timestamp'],
                                        y=daily_data['smoothed_score'],
                                        mode='lines+markers',
                                        name=f"{symbol} Combined Signal",
                                        line=dict(width=3)
                                    ))
                            
                            # Add reference lines
                            fig.add_hline(y=0.7, line_dash="dash", line_color="green", 
                                         annotation_text="Strong Buy Threshold")
                            fig.add_hline(y=0.3, line_dash="dash", line_color="red", 
                                         annotation_text="Strong Sell Threshold")
                            fig.add_hline(y=0.5, line_dash="dot", line_color="gray", 
                                         annotation_text="Neutral")
                            
                            fig.update_layout(
                                title="Smoothed Combined Strategy Signals",
                                xaxis_title="Date",
                                yaxis_title="Combined Signal Strength",
                                height=500,
                                hovermode='x unified'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Signal interpretation guide
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("📖 Signal Interpretation")
                                st.write("**Above 0.7**: Strong bullish signal")
                                st.write("**0.5 - 0.7**: Moderate bullish signal")
                                st.write("**0.3 - 0.5**: Neutral/Hold signal")
                                st.write("**Below 0.3**: Bearish signal")
                            
                            with col2:
                                st.subheader("🔧 Methodology")
                                st.write("• **70%** ML/Traditional confidence")
                                st.write("• **30%** Sentiment analysis")
                                st.write("• **3-day** rolling average smoothing")
                                st.write("• **Multi-source** signal aggregation")
                        else:
                            st.warning("No signal data available for combination")
                    else:
                        st.warning("No sentiment data available")
                except Exception as e:
                    st.error(f"Error creating combined signals: {e}")
        
        st.success("✅ Backtesting analysis completed!")
    
    # Additional information
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 About This Dashboard")
    st.sidebar.markdown("""
    This dashboard provides comprehensive backtesting analysis using:
    
    **Data Sources:**
    - 📊 Yahoo Finance historical prices  
    - 📰 News sentiment analysis
    - 📱 Social media sentiment
    - 📈 Technical analysis indicators
    - 🤖 Machine learning predictions
    
    **Features:**
    - Individual symbol performance
    - Strategy comparison and validation
    - Smoothed combined signals
    - Risk and performance metrics
    """)

if __name__ == "__main__":
    main()