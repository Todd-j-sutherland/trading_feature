#!/usr/bin/env python3
"""
ML Trading Dashboard
A simple dashboard for displaying machine learning trading data, combining:
- ML training samples and outcomes
- News, social media, technical analysis, and ML predictions
- Performance metrics and visualizations
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="ML Trading Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
def get_db_connection():
    """Get database connection"""
    return sqlite3.connect('data/trading_unified.db')

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_latest_combined_data():
    """Load the latest combined analysis data for each symbol"""
    query = """
    WITH latest_data AS (
        SELECT 
            ef.symbol,
            ef.timestamp,
            ef.sentiment_score,
            ef.confidence as sentiment_confidence,
            ef.news_count,
            ef.reddit_sentiment,
            ef.rsi,
            ef.macd_line,
            ef.current_price,
            ef.price_change_1d,
            ef.volatility_20d,
            eo.optimal_action,
            eo.confidence_score as ml_confidence,
            eo.return_pct,
            eo.price_direction_1d,
            ROW_NUMBER() OVER (PARTITION BY ef.symbol ORDER BY ef.timestamp DESC) as rn
        FROM enhanced_features ef
        JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
    )
    SELECT 
        symbol,
        timestamp,
        sentiment_score,
        sentiment_confidence,
        news_count,
        reddit_sentiment,
        rsi,
        macd_line,
        current_price,
        price_change_1d,
        volatility_20d,
        optimal_action,
        ml_confidence,
        return_pct,
        price_direction_1d
    FROM latest_data 
    WHERE rn = 1
    ORDER BY symbol
    """
    
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def load_ml_performance_data():
    """Load ML model performance metrics by symbol - filtering out NULL/zero data"""
    query = """
    SELECT 
        symbol,
        COUNT(*) as total_predictions,
        SUM(CASE WHEN optimal_action = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
        SUM(CASE WHEN optimal_action = 'SELL' THEN 1 ELSE 0 END) as sell_signals,
        SUM(CASE WHEN optimal_action = 'HOLD' THEN 1 ELSE 0 END) as hold_signals,
        ROUND(AVG(confidence_score), 3) as avg_ml_confidence,
        ROUND(AVG(return_pct), 3) as avg_return,
        ROUND(SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate_pct,
        ROUND(SUM(CASE WHEN price_direction_1d = 1 AND return_pct > 0 THEN 1 
                       WHEN price_direction_1d = 0 AND return_pct <= 0 THEN 1 
                       ELSE 0 END) * 100.0 / COUNT(*), 1) as direction_accuracy_pct
    FROM enhanced_outcomes 
    WHERE return_pct IS NOT NULL 
      AND entry_price IS NOT NULL 
      AND entry_price > 0
      AND price_magnitude_1d IS NOT NULL
    GROUP BY symbol 
    ORDER BY avg_return DESC
    """
    
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def load_training_overview():
    """Load training data overview"""
    query = """
    SELECT 
        COUNT(*) as total_samples,
        COUNT(DISTINCT symbol) as unique_symbols,
        MIN(date(timestamp)) as earliest_date,
        MAX(date(timestamp)) as latest_date,
        ROUND(AVG(sentiment_score), 3) as avg_sentiment,
        ROUND(AVG(confidence), 3) as avg_confidence,
        ROUND(AVG(rsi), 1) as avg_rsi
    FROM enhanced_features
    """
    
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.iloc[0].to_dict()

@st.cache_data(ttl=300)
def load_action_distribution():
    """Load distribution of trading actions - filtering out NULL/zero data"""
    query = """
    SELECT 
        optimal_action,
        COUNT(*) as count,
        SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) as winning_positions,
        SUM(CASE WHEN return_pct <= 0 THEN 1 ELSE 0 END) as losing_positions,
        ROUND(AVG(confidence_score), 3) as avg_confidence,
        ROUND(AVG(return_pct), 3) as avg_return_pct,
        ROUND(SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate_pct,
        ROUND(MIN(return_pct), 3) as min_return,
        ROUND(MAX(return_pct), 3) as max_return,
        ROUND(MIN(return_pct), 3) as worst_return_pct,
        ROUND(MAX(return_pct), 3) as best_return_pct
    FROM enhanced_outcomes 
    WHERE return_pct IS NOT NULL 
      AND entry_price IS NOT NULL 
      AND entry_price > 0
      AND price_magnitude_1d IS NOT NULL
    GROUP BY optimal_action 
    ORDER BY count DESC
    """
    
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def load_position_win_rates():
    """Load win rates specifically by position type with clean data only"""
    query = """
    SELECT 
        optimal_action as position,
        COUNT(*) as total_trades,
        SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) as winning_positions,
        SUM(CASE WHEN return_pct <= 0 THEN 1 ELSE 0 END) as losing_positions,
        ROUND(AVG(return_pct), 4) as avg_return_pct,
        ROUND(SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_pct,
        ROUND(AVG(CASE WHEN return_pct > 0 THEN return_pct END), 4) as avg_winning_return,
        ROUND(AVG(CASE WHEN return_pct <= 0 THEN return_pct END), 4) as avg_losing_return,
        ROUND(MAX(return_pct), 4) as best_return,
        ROUND(MIN(return_pct), 4) as worst_return
    FROM enhanced_outcomes 
    WHERE return_pct IS NOT NULL 
      AND entry_price IS NOT NULL 
      AND entry_price > 0
      AND price_magnitude_1d IS NOT NULL
    GROUP BY optimal_action 
    ORDER BY win_rate_pct DESC
    """
    
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def load_time_series_data(days=30):
    """Load time series data for charts"""
    query = """
    SELECT 
        ef.symbol,
        ef.timestamp,
        ef.sentiment_score,
        ef.confidence as sentiment_confidence,
        ef.rsi,
        ef.current_price,
        eo.optimal_action,
        eo.confidence_score as ml_confidence,
        eo.return_pct
    FROM enhanced_features ef
    JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
    WHERE ef.timestamp >= datetime('now', '-{} days')
    ORDER BY ef.timestamp DESC
    """.format(days)
    
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def format_action_color(action):
    """Return color for trading action"""
    colors = {
        'STRONG_BUY': '🟢',
        'BUY': '🟢',
        'HOLD': '🟡',
        'SELL': '🔴',
        'STRONG_SELL': '🔴'
    }
    return colors.get(action, '⚪')

def main():
    st.title("🤖 ML Trading Dashboard")
    st.markdown("**Real-time machine learning trading analysis combining news, social media, technical indicators, and ML predictions**")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "Overview", 
        "Latest Analysis", 
        "ML Performance", 
        "Position Win Rates",
        "Training Data", 
        "Time Series Analysis"
    ])
    
    # Filter options
    st.sidebar.title("Filters")
    show_only_buy = st.sidebar.checkbox("Show only BUY signals", value=False)
    if show_only_buy:
        st.sidebar.info("📈 Filtering for BUY/STRONG_BUY signals only")
    
    # Load data
    try:
        latest_data = load_latest_combined_data()
        performance_data = load_ml_performance_data()
        training_overview = load_training_overview()
        action_dist = load_action_distribution()
        position_win_rates = load_position_win_rates()
        
        # Apply BUY filter if selected
        if show_only_buy:
            latest_data = latest_data[latest_data['optimal_action'].isin(['BUY', 'STRONG_BUY'])]
            performance_data = performance_data[performance_data['buy_signals'] > 0]  # Only symbols with buy signals
        
        if page == "Overview":
            show_overview(latest_data, performance_data, training_overview, action_dist, show_only_buy)
        elif page == "Latest Analysis":
            show_latest_analysis(latest_data, show_only_buy)
        elif page == "ML Performance":
            show_ml_performance(performance_data, show_only_buy)
        elif page == "Position Win Rates":
            show_position_win_rates(position_win_rates, show_only_buy)
        elif page == "Training Data":
            show_training_data(training_overview, action_dist, show_only_buy)
        elif page == "Time Series Analysis":
            show_time_series_analysis(show_only_buy)
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Make sure the database file exists at: data/trading_unified.db")

def show_overview(latest_data, performance_data, training_overview, action_dist, show_only_buy=False):
    """Show overview page"""
    st.header("📊 ML Trading System Overview")
    
    if show_only_buy:
        st.info("📈 Showing only BUY/STRONG_BUY signals")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total ML Samples", 
            f"{training_overview['total_samples']:,}",
            delta=f"{training_overview['unique_symbols']} symbols"
        )
    
    with col2:
        avg_return = performance_data['avg_return'].mean()
        st.metric(
            "Avg Return", 
            f"{avg_return:.3f}%",
            delta=f"{performance_data['win_rate_pct'].mean():.1f}% win rate"
        )
    
    with col3:
        st.metric(
            "Avg ML Confidence", 
            f"{performance_data['avg_ml_confidence'].mean():.3f}",
            delta=f"{training_overview['avg_confidence']:.3f} sentiment conf"
        )
    
    with col4:
        total_predictions = performance_data['total_predictions'].sum()
        st.metric(
            "Total Predictions", 
            f"{total_predictions:,}",
            delta=f"Last: {training_overview['latest_date']}"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Trading Action Distribution")
        fig = px.pie(action_dist, values='count', names='optimal_action', 
                    title="ML Trading Recommendations")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Win Rate by Position Type")
        fig = px.bar(action_dist, x='optimal_action', y='win_rate_pct', 
                    color='win_rate_pct', title="Win Rate % by Trading Action",
                    color_continuous_scale='RdYlGn')
        fig.update_layout(xaxis_title="Trading Action", yaxis_title="Win Rate (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    # Win Rate Analysis Table
    st.subheader("📊 Win Rate Analysis by Position")
    win_rate_df = action_dist.copy()
    win_rate_df['Action'] = win_rate_df['optimal_action'].apply(lambda x: f"{format_action_color(x)} {x}")
    win_rate_df['Total Positions'] = win_rate_df['count']
    win_rate_df['Winning'] = win_rate_df['winning_positions']
    win_rate_df['Losing'] = win_rate_df['losing_positions']
    win_rate_df['Win Rate'] = win_rate_df['win_rate_pct'].apply(lambda x: f"{x}%")
    win_rate_df['Avg Return'] = win_rate_df['avg_return_pct'].apply(lambda x: f"{x}%")
    win_rate_df['Best Return'] = win_rate_df['best_return_pct'].apply(lambda x: f"{x}%")
    win_rate_df['Worst Return'] = win_rate_df['worst_return_pct'].apply(lambda x: f"{x}%")
    
    st.dataframe(
        win_rate_df[['Action', 'Total Positions', 'Winning', 'Losing', 'Win Rate', 'Avg Return', 'Best Return', 'Worst Return']],
        use_container_width=True
    )
    
    # Latest signals
    st.subheader("🎯 Latest Trading Signals")
    display_df = latest_data.copy()
    display_df['Action'] = display_df['optimal_action'].apply(lambda x: f"{format_action_color(x)} {x}")
    display_df['Sentiment'] = display_df['sentiment_score'].round(3)
    display_df['ML Conf'] = display_df['ml_confidence'].round(3)
    display_df['Price'] = display_df['current_price'].round(2)
    display_df['RSI'] = display_df['rsi'].round(1)
    
    st.dataframe(
        display_df[['symbol', 'Action', 'Sentiment', 'ML Conf', 'Price', 'RSI']],
        use_container_width=True
    )

def show_latest_analysis(latest_data, show_only_buy=False):
    """Show latest analysis page"""
    st.header("📈 Latest Combined Analysis")
    if show_only_buy:
        st.markdown("**Showing only BUY/STRONG_BUY signals - Real-time view of bullish analysis**")
    else:
        st.markdown("**Real-time view of all analysis sources for each symbol**")
    
    # Detailed table
    st.subheader("Complete Analysis Dashboard")
    
    if show_only_buy and latest_data.empty:
        st.warning("No BUY/STRONG_BUY signals found in current data")
        return
    elif show_only_buy:
        st.success(f"Found {len(latest_data)} BUY/STRONG_BUY signals")
    
    # Format the data for better display
    display_df = latest_data.copy()
    display_df['Symbol'] = display_df['symbol']
    display_df['Action'] = display_df['optimal_action'].apply(lambda x: f"{format_action_color(x)} {x}")
    display_df['Timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Sentiment Analysis columns
    display_df['Sentiment Score'] = display_df['sentiment_score'].round(3)
    display_df['Sent Confidence'] = display_df['sentiment_confidence'].round(3)
    display_df['News Count'] = display_df['news_count']
    display_df['Reddit Sentiment'] = display_df['reddit_sentiment'].round(3)
    
    # Technical Analysis columns  
    display_df['RSI'] = display_df['rsi'].round(1)
    display_df['MACD'] = display_df['macd_line'].round(3)
    display_df['Price'] = display_df['current_price'].round(2)
    display_df['Price Change 1D'] = display_df['price_change_1d'].round(3)
    display_df['Volatility'] = display_df['volatility_20d'].round(3)
    
    # ML Analysis columns
    display_df['ML Confidence'] = display_df['ml_confidence'].round(3)
    display_df['Return %'] = display_df['return_pct'].round(3)
    
    # Select columns for display
    columns_to_show = [
        'Symbol', 'Timestamp', 'Action',
        'Sentiment Score', 'Sent Confidence', 'News Count', 'Reddit Sentiment',
        'RSI', 'MACD', 'Price', 'Price Change 1D', 'Volatility',
        'ML Confidence', 'Return %'
    ]
    
    st.dataframe(display_df[columns_to_show], use_container_width=True)
    
    # Symbol selection for detailed view
    st.subheader("🔍 Detailed Symbol Analysis")
    selected_symbol = st.selectbox("Select a symbol for detailed analysis:", latest_data['symbol'].tolist())
    
    if selected_symbol:
        symbol_data = latest_data[latest_data['symbol'] == selected_symbol].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Sentiment Analysis**")
            st.metric("Sentiment Score", f"{symbol_data['sentiment_score']:.3f}")
            st.metric("Confidence", f"{symbol_data['sentiment_confidence']:.3f}")
            st.metric("News Count", f"{symbol_data['news_count']}")
            st.metric("Reddit Sentiment", f"{symbol_data['reddit_sentiment']:.3f}")
        
        with col2:
            st.write("**Technical Analysis**")
            st.metric("RSI", f"{symbol_data['rsi']:.1f}")
            st.metric("MACD", f"{symbol_data['macd_line']:.3f}")
            st.metric("Current Price", f"${symbol_data['current_price']:.2f}")
            st.metric("1D Price Change", f"{symbol_data['price_change_1d']:.3f}%")
        
        with col3:
            st.write("**ML Analysis**")
            action_color = format_action_color(symbol_data['optimal_action'])
            st.metric("ML Action", f"{action_color} {symbol_data['optimal_action']}")
            st.metric("ML Confidence", f"{symbol_data['ml_confidence']:.3f}")
            st.metric("Return %", f"{symbol_data['return_pct']:.3f}%")
            st.metric("Volatility", f"{symbol_data['volatility_20d']:.3f}%")

def show_ml_performance(performance_data, show_only_buy=False):
    """Show ML performance metrics"""
    st.header("🧠 ML Model Performance")
    
    if show_only_buy:
        st.info("📈 Showing performance for symbols with BUY signals")
    
    # Performance table
    st.subheader("Performance by Symbol")
    
    # Add color coding for returns
    def color_returns(val):
        if val > 0:
            return 'color: green'
        elif val < 0:
            return 'color: red'
        return ''
    
    styled_df = performance_data.style.applymap(color_returns, subset=['avg_return'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Win Rate by Symbol")
        fig = px.bar(performance_data, x='symbol', y='win_rate_pct', 
                    title="Win Rate Percentage", color='win_rate_pct')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Direction Accuracy")
        fig = px.bar(performance_data, x='symbol', y='direction_accuracy_pct', 
                    title="Direction Prediction Accuracy (%)", color='direction_accuracy_pct')
        st.plotly_chart(fig, use_container_width=True)
    
    # Signal distribution
    st.subheader("Signal Distribution by Symbol")
    
    # Reshape data for stacked bar chart
    signal_data = performance_data[['symbol', 'buy_signals', 'sell_signals', 'hold_signals']].melt(
        id_vars=['symbol'], var_name='signal_type', value_name='count'
    )
    
    fig = px.bar(signal_data, x='symbol', y='count', color='signal_type',
                title="Trading Signal Distribution", barmode='stack')
    st.plotly_chart(fig, use_container_width=True)
    
    # Win Rate Analysis by Position Type
    st.subheader("🎯 Win Rate Analysis by Position Type")
    
    # Load action distribution data for detailed analysis
    action_analysis = load_action_distribution()
    if show_only_buy:
        action_analysis = action_analysis[action_analysis['optimal_action'].isin(['BUY', 'STRONG_BUY'])]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Position Performance Metrics")
        for _, row in action_analysis.iterrows():
            action = row['optimal_action']
            action_color = format_action_color(action)
            
            with st.expander(f"{action_color} {action} Positions ({row['count']} total)"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Win Rate", f"{row['win_rate_pct']}%")
                    st.metric("Winning Positions", f"{row['winning_positions']}")
                    st.metric("Losing Positions", f"{row['losing_positions']}")
                with col_b:
                    st.metric("Avg Return", f"{row['avg_return_pct']}%")
                    st.metric("Best Return", f"{row['best_return_pct']}%")
                    st.metric("Worst Return", f"{row['worst_return_pct']}%")
    
    with col2:
        st.subheader("Win Rate Comparison")
        fig = px.bar(action_analysis, x='optimal_action', y='win_rate_pct',
                    title="Win Rate by Position Type (%)",
                    color='win_rate_pct', 
                    color_continuous_scale='RdYlGn',
                    text='win_rate_pct')
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        fig.update_layout(xaxis_title="Position Type", yaxis_title="Win Rate (%)")
        st.plotly_chart(fig, use_container_width=True)

def show_position_win_rates(position_win_rates, show_only_buy=False):
    """Show win rates by position type"""
    st.header("🎯 Position Win Rates Analysis")
    
    if show_only_buy:
        position_win_rates = position_win_rates[position_win_rates['position'].isin(['BUY', 'STRONG_BUY'])]
        st.info("📈 Showing win rates for BUY positions only")
    
    st.markdown("**Performance analysis by trading position (filtered for clean data only)**")
    
    # Main win rates table
    st.subheader("📊 Win Rate Summary by Position")
    
    # Format the display
    display_df = position_win_rates.copy()
    display_df['Win Rate %'] = display_df['win_rate_pct'].astype(str) + '%'
    display_df['Total Trades'] = display_df['total_trades']
    display_df['Winning Trades'] = display_df['winning_positions']
    display_df['Losing Trades'] = display_df['losing_positions']
    display_df['Avg Return %'] = display_df['avg_return_pct'].astype(str) + '%'
    display_df['Best Return %'] = display_df['best_return'].astype(str) + '%'
    display_df['Worst Return %'] = display_df['worst_return'].astype(str) + '%'
    
    # Color-code the win rates
    def color_win_rates(val):
        if '%' in str(val):
            rate = float(val.replace('%', ''))
            if rate >= 70:
                return 'background-color: #d4edda; color: #155724'
            elif rate >= 50:
                return 'background-color: #fff3cd; color: #856404'
            else:
                return 'background-color: #f8d7da; color: #721c24'
        return ''
    
    styled_df = display_df[['position', 'Win Rate %', 'Total Trades', 'Winning Trades', 'Losing Trades', 
                           'Avg Return %', 'Best Return %', 'Worst Return %']].style.applymap(
        color_win_rates, subset=['Win Rate %']
    )
    
    st.dataframe(styled_df, use_container_width=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Win Rate by Position")
        fig = px.bar(position_win_rates, x='position', y='win_rate_pct', 
                    color='win_rate_pct', title="Win Rate Percentage by Position",
                    color_continuous_scale='RdYlGn')
        fig.update_layout(coloraxis_colorbar=dict(title="Win Rate %"))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Average Return by Position")
        fig = px.bar(position_win_rates, x='position', y='avg_return_pct', 
                    color='avg_return_pct', title="Average Return % by Position",
                    color_continuous_scale='RdBu')
        fig.update_layout(coloraxis_colorbar=dict(title="Avg Return %"))
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed breakdown
    st.subheader("📈 Detailed Performance Breakdown")
    
    for _, row in position_win_rates.iterrows():
        with st.expander(f"{row['position']} Position Details"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Trades", f"{row['total_trades']:,}")
                st.metric("Win Rate", f"{row['win_rate_pct']:.2f}%")
            
            with col2:
                st.metric("Winning Trades", f"{row['winning_positions']:,}")
                st.metric("Losing Trades", f"{row['losing_positions']:,}")
            
            with col3:
                st.metric("Average Return", f"{row['avg_return_pct']:.4f}%")
                st.metric("Avg Winning Return", f"{row['avg_winning_return']:.4f}%" if row['avg_winning_return'] else "N/A")
            
            with col4:
                st.metric("Best Return", f"{row['best_return']:.4f}%")
                st.metric("Worst Return", f"{row['worst_return']:.4f}%")
    
    # Overall insights
    st.subheader("💡 Key Insights")
    
    if not position_win_rates.empty:
        best_position = position_win_rates.loc[position_win_rates['win_rate_pct'].idxmax()]
        worst_position = position_win_rates.loc[position_win_rates['win_rate_pct'].idxmin()]
        total_trades = position_win_rates['total_trades'].sum()
        overall_win_rate = (position_win_rates['winning_positions'].sum() / total_trades * 100)
        
        st.info(f"""
        **📊 Performance Summary:**
        - **Best Position:** {best_position['position']} with {best_position['win_rate_pct']:.1f}% win rate
        - **Worst Position:** {worst_position['position']} with {worst_position['win_rate_pct']:.1f}% win rate  
        - **Overall Win Rate:** {overall_win_rate:.1f}% across {total_trades:,} total trades
        - **Most Active:** {position_win_rates.loc[position_win_rates['total_trades'].idxmax(), 'position']} with {position_win_rates['total_trades'].max():,} trades
        """)

def show_training_data(training_overview, action_dist, show_only_buy=False):
    """Show training data information"""
    st.header("📚 Training Data Overview")
    
    if show_only_buy:
        # Filter action distribution to only show BUY actions
        action_dist = action_dist[action_dist['optimal_action'].isin(['BUY', 'STRONG_BUY'])]
        st.info("📈 Showing training data for BUY signals only")
    
    # Training data metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Data Volume")
        st.metric("Total Samples", f"{training_overview['total_samples']:,}")
        st.metric("Unique Symbols", training_overview['unique_symbols'])
        st.metric("Date Range", f"{training_overview['earliest_date']} to {training_overview['latest_date']}")
    
    with col2:
        st.subheader("Sentiment Metrics")
        st.metric("Avg Sentiment", f"{training_overview['avg_sentiment']:.3f}")
        st.metric("Avg Confidence", f"{training_overview['avg_confidence']:.3f}")
        
    with col3:
        st.subheader("Technical Metrics")
        st.metric("Avg RSI", f"{training_overview['avg_rsi']:.1f}")
    
    # Action distribution details
    st.subheader("Trading Action Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(action_dist, x='optimal_action', y='count', 
                    title="Action Frequency", color='optimal_action')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(action_dist, x='avg_confidence', y='win_rate_pct', 
                        size='count', color='optimal_action',
                        title="Confidence vs Win Rate by Action",
                        hover_data=['avg_return_pct'])
        fig.update_layout(xaxis_title="Average Confidence", yaxis_title="Win Rate (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed Win Rate Table
    st.subheader("📊 Detailed Position Performance")
    
    # Format the action distribution data for better display
    display_action_df = action_dist.copy()
    display_action_df['Position Type'] = display_action_df['optimal_action'].apply(lambda x: f"{format_action_color(x)} {x}")
    display_action_df['Total'] = display_action_df['count']
    display_action_df['Winners'] = display_action_df['winning_positions']
    display_action_df['Losers'] = display_action_df['losing_positions']
    display_action_df['Win Rate (%)'] = display_action_df['win_rate_pct']
    display_action_df['Avg Return (%)'] = display_action_df['avg_return_pct']
    display_action_df['ML Confidence'] = display_action_df['avg_confidence']
    display_action_df['Best (%)'] = display_action_df['best_return_pct']
    display_action_df['Worst (%)'] = display_action_df['worst_return_pct']
    
    st.dataframe(
        display_action_df[['Position Type', 'Total', 'Winners', 'Losers', 'Win Rate (%)', 
                          'Avg Return (%)', 'ML Confidence', 'Best (%)', 'Worst (%)']],
        use_container_width=True
    )

def show_time_series_analysis(show_only_buy=False):
    """Show time series analysis"""
    st.header("📊 Time Series Analysis")
    
    if show_only_buy:
        st.info("📈 Time series data filtered for BUY/STRONG_BUY signals")
    
    # Date range selector
    days = st.slider("Select time range (days)", 7, 60, 30)
    time_data = load_time_series_data(days)
    
    # Apply BUY filter if selected
    if show_only_buy and not time_data.empty:
        time_data = time_data[time_data['optimal_action'].isin(['BUY', 'STRONG_BUY'])]
    
    if time_data.empty:
        if show_only_buy:
            st.warning("No BUY/STRONG_BUY signals found for the selected time range")
        else:
            st.warning("No data available for the selected time range")
        return
    
    # Symbol selector
    symbols = time_data['symbol'].unique()
    selected_symbols = st.multiselect("Select symbols to display:", symbols, default=symbols[:3])
    
    if selected_symbols:
        filtered_data = time_data[time_data['symbol'].isin(selected_symbols)]
        
        # Convert timestamp to datetime
        filtered_data['timestamp'] = pd.to_datetime(filtered_data['timestamp'])
        
        # Sentiment over time
        st.subheader("Sentiment Score Over Time")
        fig = px.line(filtered_data, x='timestamp', y='sentiment_score', 
                     color='symbol', title="Sentiment Score Time Series")
        st.plotly_chart(fig, use_container_width=True)
        
        # RSI over time
        st.subheader("RSI Over Time")
        fig = px.line(filtered_data, x='timestamp', y='rsi', 
                     color='symbol', title="RSI Time Series")
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
        st.plotly_chart(fig, use_container_width=True)
        
        # ML Confidence over time
        st.subheader("ML Confidence Over Time")
        fig = px.line(filtered_data, x='timestamp', y='ml_confidence', 
                     color='symbol', title="ML Model Confidence")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
