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
import json

# Try to import yfinance for price data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Import enhanced confidence metrics
try:
    from enhanced_confidence_metrics import compute_enhanced_confidence_metrics
except ImportError:
    def compute_enhanced_confidence_metrics():
        return {
            'overall_integration': {'confidence': 0.5, 'status': 'UNKNOWN'},
            'component_summary': {'total_features': 0, 'completed_outcomes': 0}
        }

# Page configuration
st.set_page_config(
    page_title="ML Trading Dashboard - Fresh Data",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
def get_database_connection():
    """Get database connection with retry logic"""
    try:
        return sqlite3.connect('data/trading_predictions.db')
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Remove caching to ensure fresh data
def load_latest_combined_data():
    """Load the latest combined analysis data from enhanced tables"""
    query = """
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
        eo.entry_price,
        eo.return_pct,
        eo.price_direction_1d,
        ef.created_at
    FROM enhanced_features ef
    LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
    ORDER BY ef.timestamp DESC
    """
    
    conn = get_database_connection()
    if conn is None:
        return pd.DataFrame()
        
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Enhance data with real-time price information if needed
        df = enhance_with_current_prices(df)
        
        # Ensure all numeric columns are properly typed
        numeric_columns = ['sentiment_score', 'sentiment_confidence', 'news_count', 'reddit_sentiment',
                          'rsi', 'macd_line', 'current_price', 'price_change_1d', 'volatility_20d',
                          'ml_confidence', 'return_pct', 'price_direction_1d', 'entry_price']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        return df
    except Exception as e:
        st.error(f"Error loading enhanced data: {e}")
        # Fallback to old method
        return load_latest_combined_data_fallback()

def load_latest_combined_data_fallback():
    """Fallback to load data from old prediction/outcomes tables"""
    query = """
    WITH latest_predictions AS (
        SELECT 
            p.symbol,
            p.prediction_timestamp as timestamp,
            p.predicted_action as optimal_action,
            p.action_confidence as ml_confidence,
            p.predicted_direction,
            p.predicted_magnitude,
            p.feature_vector,
            o.actual_return as return_pct,
            o.entry_price,
            ROW_NUMBER() OVER (PARTITION BY p.symbol ORDER BY p.prediction_timestamp DESC) as rn
        FROM predictions p
        LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
    )
    SELECT 
        symbol,
        timestamp,
        feature_vector,
        COALESCE(entry_price, 0.0) as current_price,
        optimal_action,
        ml_confidence,
        COALESCE(return_pct, 0.0) as return_pct,
        COALESCE(predicted_direction, 0) as price_direction_1d
    FROM latest_predictions 
    WHERE rn = 1
    ORDER BY symbol
    """
    
    conn = get_database_connection()
    if conn is None:
        return pd.DataFrame()
        
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Process feature vectors in Python
        if not df.empty and 'feature_vector' in df.columns:
            df = process_feature_vectors(df)
        
        return df
    except Exception as e:
        st.error(f"Error loading fallback data: {e}")
        return pd.DataFrame()

def process_feature_vectors(df):
    """Process feature vectors from JSON arrays into individual columns"""
    import json
    
    # Initialize new columns with default values
    df['sentiment_score'] = 0.0
    df['sentiment_confidence'] = 0.0
    df['news_count'] = 0
    df['reddit_sentiment'] = 0.0
    df['rsi'] = 50.0
    df['macd_line'] = 0.0
    df['volatility_20d'] = 0.015
    df['price_change_1d'] = 0.0
    
    # Process each row
    for idx, row in df.iterrows():
        feature_vector = row.get('feature_vector')
        if feature_vector:
            try:
                features = json.loads(feature_vector)
                if len(features) >= 20:  # Expected feature vector length
                    df.at[idx, 'sentiment_score'] = float(features[0])
                    df.at[idx, 'sentiment_confidence'] = float(features[1])
                    df.at[idx, 'news_count'] = int(features[2])
                    df.at[idx, 'reddit_sentiment'] = float(features[3])
                    df.at[idx, 'rsi'] = float(features[4])
                    df.at[idx, 'macd_line'] = float(features[5])
                    df.at[idx, 'volatility_20d'] = float(features[14])
                    # Try to get current price from features if available
                    if len(features) > 15 and features[15] > 0:
                        df.at[idx, 'current_price'] = float(features[15])
            except (json.JSONDecodeError, ValueError, IndexError) as e:
                # Keep default values if parsing fails
                continue
    
    return df

def enhance_with_current_prices(df):
    """Enhance dataframe with current prices from Yahoo Finance"""
    if not YFINANCE_AVAILABLE:
        return df
        
    try:        
        for idx, row in df.iterrows():
            symbol = row['symbol']
            try:
                # Get current price from Yahoo Finance
                ticker = yf.Ticker(symbol)
                info = ticker.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
                
                if current_price and current_price > 0:
                    df.at[idx, 'current_price'] = current_price
                    
                    # Calculate price change if we have previous data
                    previous_close = info.get('previousClose', 0)
                    if previous_close and previous_close > 0:
                        price_change = ((current_price - previous_close) / previous_close) * 100
                        df.at[idx, 'price_change_1d'] = price_change
                        
            except Exception as e:
                # If price fetch fails, keep existing values
                continue
                
        return df
    except Exception as e:
        # If any error occurs, return original dataframe
        return df

# Remove caching to ensure fresh data
def load_ml_performance_data():
    """Load ML model performance metrics by symbol from new prediction system"""
    query = """
    SELECT 
        p.symbol,
        COUNT(*) as total_predictions,
        SUM(CASE WHEN p.predicted_action = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
        SUM(CASE WHEN p.predicted_action = 'SELL' THEN 1 ELSE 0 END) as sell_signals,
        SUM(CASE WHEN p.predicted_action = 'HOLD' THEN 1 ELSE 0 END) as hold_signals,
        ROUND(AVG(p.action_confidence), 3) as avg_ml_confidence,
        ROUND(AVG(o.actual_return), 3) as avg_return,
        ROUND(SUM(CASE WHEN o.actual_return > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(o.outcome_id), 1) as win_rate_pct,
        ROUND(SUM(CASE WHEN p.predicted_direction = 1 AND o.actual_return > 0 THEN 1 
                       WHEN p.predicted_direction = -1 AND o.actual_return <= 0 THEN 1 
                       ELSE 0 END) * 100.0 / COUNT(o.outcome_id), 1) as direction_accuracy_pct
    FROM predictions p
    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE o.actual_return IS NOT NULL
    GROUP BY p.symbol 
    ORDER BY avg_return DESC
    """
    
    conn = get_database_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

#@st.cache_data(ttl=300) - REMOVED FOR FRESH DATA
def load_training_overview():
    """Load training data overview from new prediction system"""
    query = """
    SELECT 
        COUNT(*) as total_samples,
        COUNT(DISTINCT symbol) as unique_symbols,
        MIN(date(prediction_timestamp)) as earliest_date,
        MAX(date(prediction_timestamp)) as latest_date,
        0.0 as avg_sentiment,
        ROUND(AVG(action_confidence), 3) as avg_confidence,
        0.0 as avg_rsi
    FROM predictions
    """
    
    conn = get_database_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.iloc[0].to_dict()

#@st.cache_data(ttl=300) - REMOVED FOR FRESH DATA
def load_action_distribution():
    """Load distribution of trading actions from new prediction system"""
    # First try to get data with outcomes
    query_with_outcomes = """
    SELECT 
        p.predicted_action as optimal_action,
        COUNT(*) as count,
        SUM(CASE WHEN o.actual_return > 0 THEN 1 ELSE 0 END) as winning_positions,
        SUM(CASE WHEN o.actual_return <= 0 THEN 1 ELSE 0 END) as losing_positions,
        ROUND(AVG(p.action_confidence), 3) as avg_confidence,
        ROUND(AVG(o.actual_return), 3) as avg_return_pct,
        ROUND(SUM(CASE WHEN o.actual_return > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(o.outcome_id), 1) as win_rate_pct,
        ROUND(MIN(o.actual_return), 3) as min_return,
        ROUND(MAX(o.actual_return), 3) as max_return,
        ROUND(MIN(o.actual_return), 3) as worst_return_pct,
        ROUND(MAX(o.actual_return), 3) as best_return_pct
    FROM predictions p
    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE o.actual_return IS NOT NULL
    GROUP BY p.predicted_action 
    ORDER BY count DESC
    """
    
    # If no outcomes yet, get prediction distribution only
    query_predictions_only = """
    SELECT 
        predicted_action as optimal_action,
        COUNT(*) as count,
        0 as winning_positions,
        0 as losing_positions,
        ROUND(AVG(action_confidence), 3) as avg_confidence,
        0.0 as avg_return_pct,
        0.0 as win_rate_pct,
        0.0 as min_return,
        0.0 as max_return,
        0.0 as worst_return_pct,
        0.0 as best_return_pct
    FROM predictions
    GROUP BY predicted_action 
    ORDER BY count DESC
    """
    
    conn = get_database_connection()
    df = pd.read_sql_query(query_with_outcomes, conn)
    
    # If no data with outcomes, fall back to predictions only
    if df.empty:
        df = pd.read_sql_query(query_predictions_only, conn)
        
    conn.close()
    return df

#@st.cache_data(ttl=300) - REMOVED FOR FRESH DATA
def load_position_win_rates():
    """Load win rates specifically by position type from new prediction system"""
    query = """
    SELECT 
        p.predicted_action as position,
        COUNT(o.outcome_id) as total_trades,
        SUM(CASE WHEN o.actual_return > 0 THEN 1 ELSE 0 END) as winning_positions,
        SUM(CASE WHEN o.actual_return <= 0 THEN 1 ELSE 0 END) as losing_positions,
        ROUND(AVG(o.actual_return), 4) as avg_return_pct,
        ROUND(SUM(CASE WHEN o.actual_return > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(o.outcome_id), 2) as win_rate_pct,
        ROUND(AVG(CASE WHEN o.actual_return > 0 THEN o.actual_return END), 4) as avg_winning_return,
        ROUND(AVG(CASE WHEN o.actual_return <= 0 THEN o.actual_return END), 4) as avg_losing_return,
        ROUND(MAX(o.actual_return), 4) as best_return,
        ROUND(MIN(o.actual_return), 4) as worst_return
    FROM predictions p
    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE o.actual_return IS NOT NULL
    GROUP BY p.predicted_action 
    ORDER BY win_rate_pct DESC
    """
    
    conn = get_database_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

#@st.cache_data(ttl=300) - REMOVED FOR FRESH DATA
def load_time_series_data(days=30):
    """Load time series data for charts from TruePredictionEngine system"""
    query = """
    SELECT 
        p.symbol,
        p.prediction_timestamp as timestamp,
        CASE WHEN p.feature_vector IS NOT NULL THEN
            COALESCE(CAST(json_extract(p.feature_vector, '$.sentiment_score') AS REAL), 0.0)
        ELSE 0.0 END as sentiment_score,
        0.0 as sentiment_confidence,
        CASE WHEN p.feature_vector IS NOT NULL THEN
            COALESCE(CAST(json_extract(p.feature_vector, '$.rsi') AS REAL), 50.0)
        ELSE 50.0 END as rsi,
        COALESCE(
            CASE 
                WHEN p.feature_vector IS NOT NULL AND CAST(json_extract(p.feature_vector, '$.current_price') AS REAL) > 0 
                THEN CAST(json_extract(p.feature_vector, '$.current_price') AS REAL)
                WHEN o.entry_price > 0 THEN o.entry_price
                ELSE 0.0
            END, 0.0
        ) as current_price,
        p.predicted_action as optimal_action,
        p.action_confidence as ml_confidence,
        o.actual_return as return_pct
    FROM predictions p
    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE p.prediction_timestamp >= datetime('now', '-{} days')
    ORDER BY p.prediction_timestamp DESC
    """.format(days)
    
    conn = get_database_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Ensure all numeric columns are properly typed
    numeric_columns = ['sentiment_score', 'sentiment_confidence', 'rsi', 'current_price', 
                      'ml_confidence', 'return_pct']
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    
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
    # Clear cache at startup to ensure fresh data
    st.cache_data.clear()
    
    # Clear any session state that might contain old data
    if 'buy_positions_data' in st.session_state:
        del st.session_state.buy_positions_data
    
    st.title("🤖 ML Trading Dashboard - Enhanced Data")
    st.markdown("**Real-time machine learning trading analysis with enhanced feature engineering**")
    
    # Enhanced cache clearing controls in sidebar
    st.sidebar.title("🔄 Data Control")
    st.sidebar.markdown(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("� Refresh"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("🔥 Force Refresh"):
            st.cache_data.clear()
            if hasattr(st, 'cache_resource'):
                st.cache_resource.clear()
            st.rerun()
    
    # Debug mode for troubleshooting
    debug_mode = st.sidebar.checkbox("🔍 Debug Mode", value=False, help="Show raw data values and database info")
    
    if debug_mode:
        st.sidebar.markdown("### 🔍 Debug Info")
        
        # Show actual database statistics
        try:
            conn = get_database_connection()
            if conn:
                # Get enhanced features counts
                enhanced_query = """
                SELECT 
                    COUNT(*) as total_enhanced_features,
                    COUNT(CASE WHEN ef.sentiment_score > 0 THEN 1 END) as positive_sentiment,
                    COUNT(CASE WHEN eo.optimal_action = 'BUY' THEN 1 END) as buy_count,
                    COUNT(CASE WHEN eo.optimal_action = 'HOLD' THEN 1 END) as hold_count,
                    COUNT(CASE WHEN eo.optimal_action = 'SELL' THEN 1 END) as sell_count,
                    MAX(ef.timestamp) as latest_enhanced
                FROM enhanced_features ef
                LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
                """
                enhanced_result = pd.read_sql_query(enhanced_query, conn)
                
                # Get legacy prediction counts  
                pred_query = """
                SELECT 
                    COUNT(*) as total_predictions,
                    COUNT(CASE WHEN predicted_action = 'BUY' THEN 1 END) as legacy_buy_count,
                    COUNT(CASE WHEN entry_price > 0 THEN 1 END) as valid_entry_prices,
                    MAX(prediction_timestamp) as latest_prediction
                FROM predictions
                """
                pred_result = pd.read_sql_query(pred_query, conn)
                
                # Get outcome counts  
                outcome_query = """
                SELECT COUNT(*) as total_outcomes
                FROM outcomes
                """
                outcome_result = pd.read_sql_query(outcome_query, conn)
                
                conn.close()
                
                st.sidebar.write(f"**Enhanced Tables:**")
                st.sidebar.write(f"Enhanced Features: {enhanced_result['total_enhanced_features'].iloc[0]}")
                st.sidebar.write(f"BUY Actions: {enhanced_result['buy_count'].iloc[0]}")
                st.sidebar.write(f"HOLD Actions: {enhanced_result['hold_count'].iloc[0]}")
                st.sidebar.write(f"SELL Actions: {enhanced_result['sell_count'].iloc[0]}")
                st.sidebar.write(f"Latest Enhanced: {enhanced_result['latest_enhanced'].iloc[0]}")
                
                st.sidebar.write(f"**Legacy Tables:**")
                st.sidebar.write(f"Legacy Predictions: {pred_result['total_predictions'].iloc[0]}")
                st.sidebar.write(f"Valid Entry Prices: {pred_result['valid_entry_prices'].iloc[0]}")
                st.sidebar.write(f"Legacy Outcomes: {outcome_result['total_outcomes'].iloc[0]}")
            else:
                st.sidebar.error("Cannot connect to database")
                
        except Exception as e:
            st.sidebar.error(f"Debug error: {e}")
            # Fallback to old method
            try:
                confidence = compute_enhanced_confidence_metrics()
                st.sidebar.write(f"Features: {confidence['component_summary']['total_features']}")
                st.sidebar.write(f"Outcomes: {confidence['component_summary']['completed_outcomes']}")
                st.sidebar.write(f"Confidence: {confidence['overall_integration']['confidence']:.1%}")
            except Exception as e2:
                st.sidebar.error(f"Fallback debug error: {e2}")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "Overview", 
        "Latest Analysis",
        "Buy Positions Analysis", 
        "ML Performance", 
        "Position Win Rates",
        "Training Data", 
        "Time Series Analysis"
    ])
    
    # Filter options
    st.sidebar.title("Filters")
    show_only_buy = st.sidebar.checkbox("Show only BUY signals", value=False)
    exclude_hold = st.sidebar.checkbox("Exclude HOLD positions", value=False)
    
    if show_only_buy:
        st.sidebar.info("📈 Filtering for BUY/STRONG_BUY signals only")
    elif exclude_hold:
        st.sidebar.info("🚫 Excluding HOLD positions - showing active trades only")
    
    # Load data
    try:
        latest_data = load_latest_combined_data()
        performance_data = load_ml_performance_data()
        training_overview = load_training_overview()
        action_dist = load_action_distribution()
        position_win_rates = load_position_win_rates()
        
        # Apply filters
        if show_only_buy:
            latest_data = latest_data[latest_data['optimal_action'].isin(['BUY', 'STRONG_BUY'])]
            performance_data = performance_data[performance_data['buy_signals'] > 0]  # Only symbols with buy signals
            action_dist = action_dist[action_dist['optimal_action'].isin(['BUY', 'STRONG_BUY'])]
            position_win_rates = position_win_rates[position_win_rates['position'].isin(['BUY', 'STRONG_BUY'])]
        elif exclude_hold:
            latest_data = latest_data[latest_data['optimal_action'] != 'HOLD']
            # Filter performance data to only include symbols with non-HOLD signals
            performance_data = performance_data[(performance_data['buy_signals'] > 0) | (performance_data['sell_signals'] > 0)]
            action_dist = action_dist[action_dist['optimal_action'] != 'HOLD']
            position_win_rates = position_win_rates[position_win_rates['position'] != 'HOLD']
        
        if page == "Overview":
            show_overview(latest_data, performance_data, training_overview, action_dist, show_only_buy, exclude_hold)
        elif page == "Latest Analysis":
            show_latest_analysis(latest_data, show_only_buy, exclude_hold)
        elif page == "Buy Positions Analysis":
            show_buy_positions_analysis()
        elif page == "ML Performance":
            show_ml_performance(performance_data, show_only_buy, exclude_hold)
        elif page == "Position Win Rates":
            show_position_win_rates(position_win_rates, show_only_buy, exclude_hold)
        elif page == "Training Data":
            show_training_data(training_overview, action_dist, show_only_buy, exclude_hold)
        elif page == "Time Series Analysis":
            show_time_series_analysis(show_only_buy, exclude_hold)
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Make sure the database file exists at: data/trading_predictions.db")
        st.info("This dashboard now shows data from the new prediction system.")
    
def show_buy_positions_analysis():
    """Show detailed buy positions analysis"""
    st.subheader("💰 Buy Positions Deep Analysis")
    
    # Load buy positions data
    buy_data = load_buy_positions_detailed()
    
    # Show clear validation message
    if buy_data.empty:
        st.warning("� **No BUY positions found in the database**")
        st.info("📊 **This means:**")
        st.info("• Your ML model has not generated any BUY signals recently")
        st.info("• All recent predictions were HOLD or other actions")
        st.info("• The fake data you saw earlier was a dashboard display bug")
        
        # Show what IS in the database
        try:
            conn = get_database_connection()
            if conn:
                current_query = """
                SELECT predicted_action, COUNT(*) as count 
                FROM predictions 
                GROUP BY predicted_action 
                ORDER BY count DESC
                """
                current_data = pd.read_sql_query(current_query, conn)
                conn.close()
                
                st.write("**📈 Current Prediction Distribution:**")
                st.dataframe(current_data, use_container_width=True)
        except Exception as e:
            st.error(f"Error checking current predictions: {e}")
        
        return
    
    # If we have data, show it
    st.success(f"✅ **Found {len(buy_data)} legitimate BUY position(s) in database**")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_buys = len(buy_data)
        st.metric("Total BUY Signals", total_buys)
    
    with col2:
        closed_positions = buy_data[pd.notna(buy_data['actual_return'])]
        if not closed_positions.empty:
            avg_return = closed_positions['actual_return'].mean()
            st.metric("Avg Return (Closed)", f"{avg_return:.2f}%")
        else:
            st.metric("Avg Return", "Pending", delta="Positions open")
    
    with col3:
        if not closed_positions.empty:
            win_rate = (closed_positions['actual_return'] > 0).mean() * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
        else:
            st.metric("Win Rate", "Pending", delta="Positions open")
    
    with col4:
        avg_confidence = buy_data['action_confidence'].mean()
        st.metric("Avg ML Confidence", f"{avg_confidence:.3f}")
    
    # Show open positions with current performance
    open_positions = buy_data[pd.isna(buy_data['actual_return'])]
    if not open_positions.empty:
        st.subheader("🔄 Open BUY Positions - Live Performance")
        
        # Calculate current performance for open positions
        open_performance = []
        for _, position in open_positions.iterrows():
            entry_price = position.get('entry_price', 0)
            symbol = position['symbol']
            
            if entry_price > 0:
                current_price = get_current_price_yf(symbol)
                if current_price > 0:
                    unrealized_return = ((current_price - entry_price) / entry_price) * 100
                    days_held = (datetime.now() - pd.to_datetime(position['prediction_timestamp'])).days
                    
                    open_performance.append({
                        'Symbol': symbol,
                        'Entry Date': pd.to_datetime(position['prediction_timestamp']).strftime('%Y-%m-%d'),
                        'Entry Price': f"${entry_price:.2f}",
                        'Current Price': f"${current_price:.2f}",
                        'Unrealized Return': f"{unrealized_return:.2f}%",
                        'Days Held': days_held,
                        'ML Confidence': f"{position['action_confidence']:.3f}",
                        'Entry Reason': position['entry_reason'][:50] + "..." if len(position['entry_reason']) > 50 else position['entry_reason']
                    })
        
        if open_performance:
            open_df = pd.DataFrame(open_performance)
            
            # Style the dataframe based on performance
            def style_returns(val):
                if 'Unrealized Return' in val.name:
                    try:
                        num_val = float(val.replace('%', ''))
                        if num_val > 0:
                            return 'color: green; font-weight: bold'
                        elif num_val < 0:
                            return 'color: red; font-weight: bold'
                    except:
                        pass
                return ''
            
            styled_open_df = open_df.style.applymap(lambda x: style_returns(pd.Series([x], index=['Unrealized Return'])).iloc[0] if 'Unrealized Return' in str(x) else '', subset=['Unrealized Return'])
            st.dataframe(styled_open_df, use_container_width=True)
        else:
            st.info("No open positions with entry prices available for performance calculation.")
    
    # Recent buy positions table with reasoning
    st.subheader("📊 Recent BUY Positions with Analysis")
    
    # Format display data
    display_df = buy_data.head(15).copy()
    display_df['Date'] = pd.to_datetime(display_df['prediction_timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    display_df['Symbol'] = display_df['symbol']
    display_df['Confidence'] = display_df['action_confidence'].round(3)
    display_df['Entry Price'] = display_df['entry_price'].fillna(0).round(2)
    display_df['Exit Price'] = display_df['exit_price'].fillna(0).round(2)
    display_df['Return %'] = display_df['actual_return'].fillna(0).round(2)
    display_df['Status'] = display_df.apply(lambda x: 
        "✅ Closed" if pd.notna(x['actual_return']) else "🔄 Open", axis=1)
    
    # Show the table
    st.dataframe(
        display_df[['Date', 'Symbol', 'Confidence', 'Entry Price', 'Exit Price', 
                   'Return %', 'Status', 'entry_reason']],
        use_container_width=True,
        column_config={
            "entry_reason": st.column_config.TextColumn(
                "Entry Reasoning",
                help="Why this BUY position was recommended",
                width="large"
            )
        }
    )
    
    # Detailed position analysis
    st.subheader("🔍 Position-by-Position Analysis")
    
    # Select a specific position for detailed analysis
    position_ids = buy_data['prediction_id'].tolist()
    symbols_dates = [f"{row['symbol']} - {pd.to_datetime(row['prediction_timestamp']).strftime('%Y-%m-%d %H:%M')}" 
                    for _, row in buy_data.iterrows()]
    
    if symbols_dates:
        selected_position = st.selectbox(
            "Select a BUY position for detailed analysis:",
            options=list(zip(position_ids, symbols_dates)),
            format_func=lambda x: x[1]
        )
        
        if selected_position:
            position_id = selected_position[0]
            position_data = buy_data[buy_data['prediction_id'] == position_id].iloc[0]
            
            # Create detailed analysis layout
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**📈 Position Details**")
                st.write(f"**Symbol:** {position_data['symbol']}")
                st.write(f"**Entry Date:** {pd.to_datetime(position_data['prediction_timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**ML Confidence:** {position_data['action_confidence']:.3f}")
                st.write(f"**Entry Price:** ${position_data['entry_price']:.2f}" if pd.notna(position_data['entry_price']) else "**Entry Price:** Pending")
                
                if pd.notna(position_data['exit_price']):
                    st.write(f"**Exit Price:** ${position_data['exit_price']:.2f}")
                    st.write(f"**Return:** {position_data['actual_return']:.2f}%")
                    if position_data['actual_return'] > 0:
                        st.success(f"✅ Profitable position (+{position_data['actual_return']:.2f}%)")
                    else:
                        st.error(f"❌ Loss position ({position_data['actual_return']:.2f}%)")
                else:
                    st.info("🔄 Position still open")
            
            with col2:
                st.write("**🧠 Technical Analysis at Entry**")
                st.write(f"**Sentiment Score:** {position_data['sentiment_score']:.3f}")
                st.write(f"**RSI:** {position_data['rsi']:.1f}")
                st.write(f"**MACD:** {position_data['macd_line']:.3f}")
                st.write(f"**News Articles:** {position_data['news_count']}")
                
                # RSI interpretation
                rsi = position_data['rsi']
                if rsi < 30:
                    st.write("🔵 **RSI Signal:** Oversold - potential bounce opportunity")
                elif rsi > 70:
                    st.write("🔴 **RSI Signal:** Overbought - momentum play")
                else:
                    st.write("🟡 **RSI Signal:** Neutral zone")
            
            # Entry and exit reasoning
            st.write("**💡 Entry Reasoning:**")
            st.info(position_data['entry_reason'])
            
            st.write("**🎯 Exit Analysis:**")
            st.info(position_data['exit_reason'])
    
    # Performance analysis by technical indicators
    st.subheader("📊 BUY Signal Performance by Indicators")
    
    if not closed_positions.empty:
        # Group by RSI ranges
        closed_positions['rsi_range'] = pd.cut(
            closed_positions['rsi'], 
            bins=[0, 30, 50, 70, 100], 
            labels=['Oversold (<30)', 'Low (30-50)', 'High (50-70)', 'Overbought (>70)']
        )
        
        rsi_performance = closed_positions.groupby('rsi_range').agg({
            'actual_return': ['mean', 'count'],
            'action_confidence': 'mean'
        }).round(3)
        
        rsi_performance.columns = ['Avg Return %', 'Position Count', 'Avg Confidence']
        
        st.write("**Performance by RSI Range:**")
        st.dataframe(rsi_performance, use_container_width=True)
        
        # Sentiment performance
        closed_positions['sentiment_range'] = pd.cut(
            closed_positions['sentiment_score'], 
            bins=[-1, -0.1, 0, 0.1, 1], 
            labels=['Negative', 'Slightly Negative', 'Neutral', 'Positive']
        )
        
        sentiment_performance = closed_positions.groupby('sentiment_range').agg({
            'actual_return': ['mean', 'count'],
            'action_confidence': 'mean'
        }).round(3)
        
        sentiment_performance.columns = ['Avg Return %', 'Position Count', 'Avg Confidence']
        
        st.write("**Performance by Sentiment Range:**")
        st.dataframe(sentiment_performance, use_container_width=True)
        
        # Best and worst performing signals
        st.subheader("🏆 Best & Worst BUY Signals")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🥇 Top 5 Best Performing BUY Signals**")
            best_signals = closed_positions.nlargest(5, 'actual_return')[
                ['symbol', 'prediction_timestamp', 'actual_return', 'entry_reason', 'action_confidence']
            ].copy()
            best_signals['Date'] = pd.to_datetime(best_signals['prediction_timestamp']).dt.strftime('%Y-%m-%d')
            best_signals['Return %'] = best_signals['actual_return'].round(2)
            best_signals['Confidence'] = best_signals['action_confidence'].round(3)
            best_signals['Reason'] = best_signals['entry_reason'].apply(lambda x: x[:40] + "..." if len(x) > 40 else x)
            
            st.dataframe(
                best_signals[['symbol', 'Date', 'Return %', 'Confidence', 'Reason']],
                use_container_width=True
            )
        
        with col2:
            st.write("**🥲 Top 5 Worst Performing BUY Signals**")
            worst_signals = closed_positions.nsmallest(5, 'actual_return')[
                ['symbol', 'prediction_timestamp', 'actual_return', 'entry_reason', 'action_confidence']
            ].copy()
            worst_signals['Date'] = pd.to_datetime(worst_signals['prediction_timestamp']).dt.strftime('%Y-%m-%d')
            worst_signals['Return %'] = worst_signals['actual_return'].round(2)
            worst_signals['Confidence'] = worst_signals['action_confidence'].round(3)
            worst_signals['Reason'] = worst_signals['entry_reason'].apply(lambda x: x[:40] + "..." if len(x) > 40 else x)
            
            st.dataframe(
                worst_signals[['symbol', 'Date', 'Return %', 'Confidence', 'Reason']],
                use_container_width=True
            )

def display_evaluation_countdown():
    """Display a prominent countdown widget for the evaluation period"""
    eval_time, time_msg = get_next_evaluation_time()
    
    if eval_time:
        # Create a prominent countdown display
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; margin: 10px 0; text-align: center;">
            <h3 style="color: white; margin: 0;">⏰ Next Evaluation Period</h3>
            <div id="main-countdown" style="font-size: 24px; font-weight: bold; color: #fff; margin: 10px 0;">
                {time_msg}
            </div>
            <p style="color: #e0e0e0; margin: 0; font-size: 14px;">
                Performance metrics will be available at {eval_time.strftime('%Y-%m-%d %H:%M')}
            </p>
        </div>
        <script>
        function updateMainCountdown() {{
            const now = new Date().getTime();
            const evalTime = new Date("{eval_time.isoformat()}").getTime();
            const distance = evalTime - now;
            
            if (distance > 0) {{
                const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((distance % (1000 * 60)) / 1000);
                
                let display = "";
                if (days > 0) display += days + "d ";
                if (hours > 0) display += hours + "h ";
                display += minutes + "m " + seconds + "s";
                
                document.getElementById("main-countdown").innerHTML = display;
            }} else {{
                document.getElementById("main-countdown").innerHTML = "🎉 Evaluation Ready! Refreshing...";
                // Auto-refresh when countdown reaches zero
                setTimeout(function() {{
                    window.location.reload();
                }}, 2000);
            }}
        }}
        updateMainCountdown();
        setInterval(updateMainCountdown, 1000);
        </script>
        """, unsafe_allow_html=True)
        return True
    elif "available" in time_msg:
        st.success(f"✅ {time_msg}")
        return False
    else:
        st.info(f"ℹ️ {time_msg}")
        return False

def get_next_evaluation_time():
    """Calculate when the next evaluation period will be available"""
    try:
        conn = get_database_connection()
        
        # First check if we have any outcomes already available
        outcomes_query = """
        SELECT COUNT(*) as outcome_count
        FROM outcomes o 
        JOIN predictions p ON o.prediction_id = p.prediction_id
        WHERE p.prediction_timestamp >= datetime('now', '-7 days')
        """
        outcomes_result = pd.read_sql_query(outcomes_query, conn)
        has_outcomes = outcomes_result['outcome_count'].iloc[0] > 0
        
        if has_outcomes:
            conn.close()
            return None, "Evaluation data available"
        
        # Get latest predictions info
        query = """
        SELECT 
            MAX(prediction_timestamp) as latest_prediction,
            COUNT(*) as total_predictions,
            MIN(prediction_timestamp) as first_prediction
        FROM predictions
        WHERE prediction_timestamp >= datetime('now', '-48 hours')
        """
        result = pd.read_sql_query(query, conn)
        conn.close()
        
        if result.empty or result['latest_prediction'].iloc[0] is None:
            return None, "No recent predictions found"
        
        latest_prediction = pd.to_datetime(result['latest_prediction'].iloc[0])
        total_predictions = result['total_predictions'].iloc[0]
        first_prediction = pd.to_datetime(result['first_prediction'].iloc[0]) if result['first_prediction'].iloc[0] else None
        
        # Calculate evaluation time (24 hours after latest prediction)
        evaluation_time = latest_prediction + timedelta(hours=24)
        now = datetime.now()
        
        if now >= evaluation_time:
            return None, "Evaluation period has passed - refresh for results"
        
        time_remaining = evaluation_time - now
        hours_remaining = time_remaining.total_seconds() / 3600
        
        # Format the remaining time nicely
        if hours_remaining < 1:
            minutes_remaining = int(time_remaining.total_seconds() / 60)
            if minutes_remaining < 1:
                seconds_remaining = int(time_remaining.total_seconds())
                time_str = f"{seconds_remaining} seconds"
            else:
                time_str = f"{minutes_remaining} minutes"
        elif hours_remaining < 24:
            hours = int(hours_remaining)
            minutes = int((hours_remaining - hours) * 60)
            time_str = f"{hours}h {minutes}m"
        else:
            days = int(hours_remaining / 24)
            remaining_hours = int(hours_remaining % 24)
            time_str = f"{days}d {remaining_hours}h"
        
        # Add context about prediction volume
        context = f" ({total_predictions} predictions)"
        
        return evaluation_time, time_str + context
            
    except Exception as e:
        return None, f"Error calculating evaluation time: {e}"

def show_overview(latest_data, performance_data, training_overview, action_dist, show_only_buy=False, exclude_hold=False):
    """Show overview page"""
    st.header("📊 ML Trading System Overview")
    
    # Check if we have evaluation data
    has_outcomes = not performance_data.empty and not performance_data['avg_return'].isna().all()
    
    # Display countdown if waiting for evaluation
    if not has_outcomes:
        display_evaluation_countdown()
    
    if show_only_buy:
        st.info("📈 Showing only BUY/STRONG_BUY signals")
    elif exclude_hold:
        st.info("🚫 Excluding HOLD positions - showing active trades only")    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total ML Samples", 
            f"{training_overview['total_samples']:,}",
            delta=f"{training_overview['unique_symbols']} symbols"
        )
    
    with col2:
        if performance_data.empty or performance_data['avg_return'].isna().all():
            eval_time, time_msg = get_next_evaluation_time()
            st.metric(
                "Avg Return", 
                "Pending",
                delta=f"Ready in {time_msg}" if eval_time else time_msg
            )
        else:
            avg_return = performance_data['avg_return'].mean()
            st.metric(
                "Avg Return", 
                f"{avg_return:.3f}%",
                delta=f"{performance_data['win_rate_pct'].mean():.1f}% win rate"
            )
    
    with col3:
        if performance_data.empty or performance_data['avg_ml_confidence'].isna().all():
            # Get confidence from predictions table directly
            st.metric(
                "Avg ML Confidence", 
                f"{training_overview['avg_confidence']:.3f}",
                delta="From predictions"
            )
        else:
            st.metric(
                "Avg ML Confidence", 
                f"{performance_data['avg_ml_confidence'].mean():.3f}",
                delta=f"{training_overview['avg_confidence']:.3f} sentiment conf"
            )
    
    with col4:
        # Show true total predictions from enhanced_features table
        st.metric(
            "Total Predictions", 
            f"{training_overview['total_samples']:,}",
            delta=f"Last: {training_overview['latest_date']}"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Trading Action Distribution")
        if not action_dist.empty:
            fig = px.pie(action_dist, values='count', names='optimal_action', 
                        title="ML Trading Recommendations")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No prediction data available yet")
    
    with col2:
        st.subheader("Win Rate by Position Type")
        if not action_dist.empty and action_dist['win_rate_pct'].sum() > 0:
            fig = px.bar(action_dist, x='optimal_action', y='win_rate_pct', 
                        color='win_rate_pct', title="Win Rate % by Trading Action",
                        color_continuous_scale='RdYlGn')
            fig.update_layout(xaxis_title="Trading Action", yaxis_title="Win Rate (%)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            eval_time, time_msg = get_next_evaluation_time()
            if eval_time:
                st.info(f"Win rates will appear in {time_msg} (evaluation at {eval_time.strftime('%H:%M')})")
            else:
                st.info(f"Win rate calculation: {time_msg}")
            # Show confidence instead
            if not action_dist.empty:
                fig = px.bar(action_dist, x='optimal_action', y='avg_confidence', 
                            title="Prediction Confidence by Action",
                            color='avg_confidence', color_continuous_scale='Blues')
                fig.update_layout(xaxis_title="Trading Action", yaxis_title="Avg Confidence")
                st.plotly_chart(fig, use_container_width=True)
    
    # Win Rate Analysis Table
    st.subheader("📊 Win Rate Analysis by Position")
    
    if not action_dist.empty:
        win_rate_df = action_dist.copy()
        win_rate_df['Action'] = win_rate_df['optimal_action'].apply(lambda x: f"{format_action_color(x)} {x}")
        win_rate_df['Total Positions'] = win_rate_df['count']
        win_rate_df['Winning'] = win_rate_df['winning_positions']
        win_rate_df['Losing'] = win_rate_df['losing_positions']
        
        if has_outcomes:
            win_rate_df['Win Rate'] = win_rate_df['win_rate_pct'].apply(lambda x: f"{x}%")
            win_rate_df['Avg Return'] = win_rate_df['avg_return_pct'].apply(lambda x: f"{x}%")
            win_rate_df['Best Return'] = win_rate_df['best_return_pct'].apply(lambda x: f"{x}%")
            win_rate_df['Worst Return'] = win_rate_df['worst_return_pct'].apply(lambda x: f"{x}%")
            
            st.dataframe(
                win_rate_df[['Action', 'Total Positions', 'Winning', 'Losing', 'Win Rate', 'Avg Return', 'Best Return', 'Worst Return']],
                use_container_width=True
            )
        else:
            win_rate_df['Avg Confidence'] = win_rate_df['avg_confidence'].apply(lambda x: f"{x:.3f}")
            eval_time, time_msg = get_next_evaluation_time()
            status_msg = f"Ready in {time_msg}" if eval_time else time_msg
            win_rate_df['Status'] = status_msg
            
            st.dataframe(
                win_rate_df[['Action', 'Total Positions', 'Avg Confidence', 'Status']],
                use_container_width=True
            )
            if eval_time:
                st.info(f"⏰ Win rates and returns will be calculated in **{time_msg}** (at {eval_time.strftime('%Y-%m-%d %H:%M')})")
            else:
                st.info(f"📊 Win rate calculation status: {time_msg}")
    else:
        st.info("No prediction data available yet.")
    
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

def load_buy_positions_detailed():
    """Load detailed information about BUY positions with reasoning"""
    query = """
    SELECT 
        p.prediction_id,
        p.symbol,
        p.prediction_timestamp,
        p.predicted_action,
        p.action_confidence,
        p.feature_vector,
        o.entry_price,
        o.exit_price,
        o.actual_return,
        o.evaluation_timestamp
    FROM predictions p
    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE p.predicted_action = 'BUY'
    ORDER BY p.prediction_timestamp DESC
    """
    
    conn = get_database_connection()
    if conn is None:
        return pd.DataFrame()
        
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Enhanced debugging - show in main area when debug mode is on
        debug_checkbox = st.sidebar.checkbox("🔍 Debug Data Source", value=False)
        if debug_checkbox:
            st.write("**🔍 DEBUG: BUY Positions Query Results**")
            st.write(f"Query returned {len(df)} BUY positions from database")
            
            if not df.empty:
                st.write("**Raw Database Results:**")
                debug_display = df[['symbol', 'prediction_timestamp', 'predicted_action', 'action_confidence']].copy()
                debug_display['Date'] = pd.to_datetime(debug_display['prediction_timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                st.dataframe(debug_display[['symbol', 'Date', 'predicted_action', 'action_confidence']])
                
                st.write("**Feature Vector Status:**")
                has_features = df['feature_vector'].notna().sum()
                st.write(f"Rows with feature vectors: {has_features}/{len(df)}")
                
                if has_features > 0:
                    sample_features = df[df['feature_vector'].notna()]['feature_vector'].iloc[0]
                    try:
                        parsed = json.loads(sample_features)
                        st.write(f"Sample feature vector length: {len(parsed)}")
                        st.write(f"First 5 features: {parsed[:5]}")
                    except:
                        st.write("Error parsing sample feature vector")
            else:
                st.write("❌ **No BUY positions found in database**")
                st.write("This confirms that the fake data was being generated by the dashboard, not from the database.")
        
        # Process feature vectors to extract reasoning
        if not df.empty and 'feature_vector' in df.columns:
            df = extract_buy_reasoning(df)
            
        return df
    except Exception as e:
        st.error(f"Error loading buy positions: {e}")
        return pd.DataFrame()

def get_current_price_yf(symbol):
    """Get current price from Yahoo Finance for entry/exit analysis"""
    if not YFINANCE_AVAILABLE:
        return 0
        
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
        return current_price if current_price and current_price > 0 else 0
    except:
        return 0

def extract_buy_reasoning(df):
    """Extract reasoning for buy decisions from feature vectors"""
    import json
    
    # Initialize reasoning columns
    df['entry_reason'] = ""
    df['exit_reason'] = ""
    df['sentiment_score'] = 0.0
    df['rsi'] = 50.0
    df['macd_line'] = 0.0
    df['news_count'] = 0
    df['current_price'] = 0.0
    
    for idx, row in df.iterrows():
        feature_vector = row.get('feature_vector')
        if feature_vector:
            try:
                features = json.loads(feature_vector)
                if len(features) >= 20:
                    sentiment = float(features[0])
                    sentiment_conf = float(features[1])
                    news_count = int(features[2])
                    rsi = float(features[4])
                    macd = float(features[5])
                    
                    df.at[idx, 'sentiment_score'] = sentiment
                    df.at[idx, 'rsi'] = rsi
                    df.at[idx, 'macd_line'] = macd
                    df.at[idx, 'news_count'] = news_count
                    
                    # Generate entry reasoning based on indicators
                    entry_reasons = []
                    
                    # Sentiment-based reasoning
                    if sentiment > 0.1:
                        entry_reasons.append(f"Strong positive sentiment ({sentiment:.3f})")
                    elif sentiment > 0.05:
                        entry_reasons.append(f"Moderate positive sentiment ({sentiment:.3f})")
                    
                    # Technical analysis reasoning
                    if rsi < 30:
                        entry_reasons.append(f"Oversold RSI ({rsi:.1f}) - potential bounce")
                    elif rsi > 70:
                        entry_reasons.append(f"Strong momentum RSI ({rsi:.1f})")
                    elif 45 <= rsi <= 55:
                        entry_reasons.append(f"Neutral RSI ({rsi:.1f}) - balanced entry")
                    
                    # MACD reasoning
                    if macd > 0.1:
                        entry_reasons.append(f"Bullish MACD signal ({macd:.3f})")
                    elif macd > 0:
                        entry_reasons.append(f"Positive MACD momentum ({macd:.3f})")
                    
                    # News volume reasoning
                    if news_count > 40:
                        entry_reasons.append(f"High news activity ({news_count} articles)")
                    elif news_count > 20:
                        entry_reasons.append(f"Moderate news coverage ({news_count} articles)")
                    
                    # ML confidence reasoning
                    confidence = row.get('action_confidence', 0)
                    if confidence > 0.7:
                        entry_reasons.append(f"High ML confidence ({confidence:.3f})")
                    elif confidence > 0.5:
                        entry_reasons.append(f"Moderate ML confidence ({confidence:.3f})")
                    
                    df.at[idx, 'entry_reason'] = "; ".join(entry_reasons) if entry_reasons else "Standard technical signals"
                    
                    # Exit reasoning (if position is closed)
                    if pd.notna(row.get('exit_price')) and pd.notna(row.get('actual_return')):
                        actual_return = row['actual_return']
                        if actual_return > 0:
                            df.at[idx, 'exit_reason'] = f"Profitable exit (+{actual_return:.2f}% return)"
                        else:
                            df.at[idx, 'exit_reason'] = f"Stop loss triggered ({actual_return:.2f}% return)"
                    else:
                        # For open positions, calculate potential current return
                        entry_price = row.get('entry_price', 0)
                        if entry_price > 0:
                            current_price = get_current_price_yf(row['symbol'])
                            if current_price > 0:
                                potential_return = ((current_price - entry_price) / entry_price) * 100
                                df.at[idx, 'current_price'] = current_price
                                if potential_return > 0:
                                    df.at[idx, 'exit_reason'] = f"Position open - potential +{potential_return:.2f}% return"
                                else:
                                    df.at[idx, 'exit_reason'] = f"Position open - current {potential_return:.2f}% return"
                            else:
                                df.at[idx, 'exit_reason'] = "Position open - monitoring price"
                        else:
                            df.at[idx, 'exit_reason'] = "Position open - awaiting entry price"
                        
            except (json.JSONDecodeError, ValueError, IndexError):
                df.at[idx, 'entry_reason'] = "Technical analysis signals"
                df.at[idx, 'exit_reason'] = "Standard exit strategy"
                
    return df

def show_latest_analysis(latest_data, show_only_buy=False, exclude_hold=False):
    """Show latest analysis page"""
    st.header("📈 Latest Combined Analysis")
    if show_only_buy:
        st.markdown("**Showing only BUY/STRONG_BUY signals - Real-time view of bullish analysis**")
    elif exclude_hold:
        st.markdown("**Excluding HOLD positions - Real-time view of active trading signals**")
    else:
        st.markdown("**Real-time view of all analysis sources for each symbol**")
    
    # Add Buy Positions Analysis section at the top
    if show_only_buy or not exclude_hold:
        show_buy_positions_analysis()
    
    # Detailed table
    st.subheader("Complete Analysis Dashboard")
    
    if show_only_buy and latest_data.empty:
        st.warning("No BUY/STRONG_BUY signals found in current data")
        return
    elif exclude_hold and latest_data.empty:
        st.warning("No active trading signals found (all signals were HOLD)")
        return
    elif show_only_buy:
        st.success(f"Found {len(latest_data)} BUY/STRONG_BUY signals")
    elif exclude_hold:
        st.success(f"Found {len(latest_data)} active trading signals (excluding HOLD)")
    
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

def show_ml_performance(performance_data, show_only_buy=False, exclude_hold=False):
    """Show ML performance metrics"""
    st.header("🧠 ML Model Performance")
    
    if show_only_buy:
        st.info("📈 Showing performance for symbols with BUY signals")
    elif exclude_hold:
        st.info("🚫 Showing performance excluding HOLD positions")
    
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
    elif exclude_hold:
        action_analysis = action_analysis[action_analysis['optimal_action'] != 'HOLD']
    
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

def show_position_win_rates(position_win_rates, show_only_buy=False, exclude_hold=False):
    """Show win rates by position type"""
    st.header("🎯 Position Win Rates Analysis")
    
    if show_only_buy:
        st.info("📈 Showing win rates for BUY positions only")
    elif exclude_hold:
        st.info("� Showing win rates excluding HOLD positions")
    
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

def show_training_data(training_overview, action_dist, show_only_buy=False, exclude_hold=False):
    """Show training data information"""
    st.header("📚 Training Data Overview")
    
    if show_only_buy:
        st.info("📈 Showing training data for BUY signals only")
    elif exclude_hold:
        st.info("� Showing training data excluding HOLD positions")
    
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

def show_time_series_analysis(show_only_buy=False, exclude_hold=False):
    """Show time series analysis"""
    st.header("📊 Time Series Analysis")
    
    if show_only_buy:
        st.info("📈 Time series data filtered for BUY/STRONG_BUY signals")
    elif exclude_hold:
        st.info("🚫 Time series data excluding HOLD positions")
    
    # Date range selector
    days = st.slider("Select time range (days)", 7, 60, 30)
    time_data = load_time_series_data(days)
    
    # Apply filters if selected
    if show_only_buy and not time_data.empty:
        time_data = time_data[time_data['optimal_action'].isin(['BUY', 'STRONG_BUY'])]
    elif exclude_hold and not time_data.empty:
        time_data = time_data[time_data['optimal_action'] != 'HOLD']
    
    if time_data.empty:
        if show_only_buy:
            st.warning("No BUY/STRONG_BUY signals found for the selected time range")
        elif exclude_hold:
            st.warning("No active trading signals found for the selected time range (excluding HOLD)")
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
