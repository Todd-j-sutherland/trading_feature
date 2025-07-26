#!/usr/bin/env python3
"""
Simplified Trading Sentiment Analysis Dashboard for ASX Banks
Single-page dashboard with ML performance, sentiment scores, and technical analysis

Requirements:
- Python 3.12 virtual environment
- Streamlit for UI
- Direct SQL database queries (no JSON files)
- Real-time data only
- Production-ready error handling
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# Configuration
DATABASE_PATH = "data/ml_models/training_data.db"
ASX_BANKS = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX", "SUN.AX", "QBE.AX"]

class DatabaseError(Exception):
    """Custom exception for database-related errors"""
    pass

class DataError(Exception):
    """Custom exception for data-related errors"""
    pass

def get_database_connection() -> sqlite3.Connection:
    """
    Get database connection with proper error handling
    Raises DatabaseError if connection fails
    """
    db_path = Path(DATABASE_PATH)
    if not db_path.exists():
        raise DatabaseError(f"Database not found: {DATABASE_PATH}")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to connect to database: {e}")

def fetch_ml_performance_metrics() -> Dict:
    """
    Fetch ML model performance metrics from database
    Returns metrics for accuracy, success rate, and predictions
    """
    conn = get_database_connection()
    
    try:
        # Get recent predictions for accuracy calculation
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_predictions,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN sentiment_score > 0.05 THEN 1 END) as buy_signals,
                COUNT(CASE WHEN sentiment_score < -0.05 THEN 1 END) as sell_signals,
                COUNT(CASE WHEN sentiment_score BETWEEN -0.05 AND 0.05 THEN 1 END) as hold_signals
            FROM sentiment_features 
            WHERE timestamp >= date('now', '-7 days')
        """)
        
        row = cursor.fetchone()
        if not row or row['total_predictions'] == 0:
            raise DataError("No prediction data found in the last 7 days")
        
        # Get performance from trading outcomes
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as completed_trades,
                AVG(return_pct) as avg_return,
                COUNT(CASE WHEN return_pct > 0 THEN 1 END) as successful_trades,
                MAX(return_pct) as best_trade,
                MIN(return_pct) as worst_trade
            FROM trading_outcomes 
            WHERE exit_timestamp IS NOT NULL
            AND signal_timestamp >= date('now', '-30 days')
        """)
        
        outcomes_row = cursor.fetchone()
        
        # Calculate derived metrics
        success_rate = 0
        if outcomes_row and outcomes_row['completed_trades'] > 0:
            success_rate = (outcomes_row['successful_trades'] / outcomes_row['completed_trades'])
        
        metrics = {
            'total_predictions': row['total_predictions'],
            'avg_confidence': float(row['avg_confidence'] or 0),
            'buy_signals': row['buy_signals'],
            'sell_signals': row['sell_signals'], 
            'hold_signals': row['hold_signals'],
            'completed_trades': outcomes_row['completed_trades'] if outcomes_row else 0,
            'success_rate': success_rate,
            'avg_return': float(outcomes_row['avg_return'] or 0) if outcomes_row else 0,
            'best_trade': float(outcomes_row['best_trade'] or 0) if outcomes_row else 0,
            'worst_trade': float(outcomes_row['worst_trade'] or 0) if outcomes_row else 0
        }
        
        return metrics
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to fetch ML performance metrics: {e}")
    finally:
        conn.close()

def fetch_current_sentiment_scores() -> pd.DataFrame:
    """
    Fetch latest sentiment scores for all ASX banks
    Returns DataFrame with current sentiment data
    """
    conn = get_database_connection()
    
    try:
        # Get latest sentiment for each bank
        cursor = conn.execute("""
            SELECT 
                s1.symbol,
                s1.timestamp,
                s1.sentiment_score,
                s1.confidence,
                s1.news_count,
                s1.reddit_sentiment,
                s1.event_score,
                s1.technical_score,
                CASE 
                    WHEN s1.sentiment_score > 0.05 THEN 'BUY'
                    WHEN s1.sentiment_score < -0.05 THEN 'SELL'
                    ELSE 'HOLD'
                END as signal
            FROM sentiment_features s1
            INNER JOIN (
                SELECT symbol, MAX(timestamp) as max_timestamp
                FROM sentiment_features
                WHERE symbol IN ({})
                GROUP BY symbol
            ) s2 ON s1.symbol = s2.symbol AND s1.timestamp = s2.max_timestamp
            ORDER BY s1.symbol
        """.format(','.join('?' * len(ASX_BANKS))), ASX_BANKS)
        
        results = cursor.fetchall()
        
        if not results:
            raise DataError("No current sentiment data found for any banks")
        
        # Convert to DataFrame
        data = []
        for row in results:
            data.append({
                'Symbol': row['symbol'],
                'Timestamp': row['timestamp'],
                'Sentiment Score': float(row['sentiment_score'] or 0),
                'Confidence': float(row['confidence'] or 0),
                'Signal': row['signal'],
                'News Count': int(row['news_count'] or 0),
                'Reddit Sentiment': float(row['reddit_sentiment'] or 0),
                'Event Score': float(row['event_score'] or 0),
                'Technical Score': float(row['technical_score'] or 0)
            })
        
        return pd.DataFrame(data)
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to fetch current sentiment scores: {e}")
    finally:
        conn.close()

def fetch_ml_feature_analysis() -> Dict:
    """
    Analyze what features the ML model is using dynamically
    Returns feature importance and usage statistics
    """
    conn = get_database_connection()
    
    try:
        # Get recent feature usage statistics
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_records,
                AVG(CASE WHEN news_count > 0 THEN 1.0 ELSE 0.0 END) as news_usage,
                AVG(CASE WHEN reddit_sentiment IS NOT NULL THEN 1.0 ELSE 0.0 END) as reddit_usage,
                AVG(CASE WHEN event_score IS NOT NULL THEN 1.0 ELSE 0.0 END) as event_usage,
                AVG(CASE WHEN technical_score IS NOT NULL THEN 1.0 ELSE 0.0 END) as technical_usage,
                AVG(news_count) as avg_news_count,
                AVG(ABS(reddit_sentiment)) as avg_reddit_strength,
                AVG(ABS(event_score)) as avg_event_strength,
                AVG(technical_score) as avg_technical_strength,
                ml_features
            FROM sentiment_features 
            WHERE timestamp >= date('now', '-30 days')
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        
        if not row:
            raise DataError("No ML feature data found")
        
        # Parse ML features if available
        ml_features_info = {}
        if row['ml_features']:
            try:
                ml_features_info = json.loads(row['ml_features'])
            except json.JSONDecodeError:
                ml_features_info = {"raw": row['ml_features']}
        
        feature_analysis = {
            'total_records': row['total_records'],
            'feature_usage': {
                'news_analysis': float(row['news_usage'] or 0) * 100,
                'reddit_sentiment': float(row['reddit_usage'] or 0) * 100,
                'event_scoring': float(row['event_usage'] or 0) * 100,
                'technical_indicators': float(row['technical_usage'] or 0) * 100
            },
            'feature_strength': {
                'avg_news_count': float(row['avg_news_count'] or 0),
                'avg_reddit_strength': float(row['avg_reddit_strength'] or 0),
                'avg_event_strength': float(row['avg_event_strength'] or 0),
                'avg_technical_strength': float(row['avg_technical_strength'] or 0)
            },
            'ml_features': ml_features_info
        }
        
        return feature_analysis
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to fetch ML feature analysis: {e}")
    finally:
        conn.close()

def fetch_prediction_timeline() -> pd.DataFrame:
    """
    Fetch prediction timeline with actual outcomes for performance visualization
    Returns DataFrame with predictions and their actual outcomes
    """
    conn = get_database_connection()
    
    try:
        cursor = conn.execute("""
            SELECT 
                tp.created_at as timestamp,
                tp.symbol,
                tp.predicted_signal as signal,
                tp.confidence,
                COALESCE(latest_sf.technical_score, 0) as technical_score,
                tp.sentiment_score,
                tp.actual_outcome,
                tp.status,
                CASE 
                    WHEN tp.actual_outcome IS NOT NULL THEN
                        CASE WHEN (tp.predicted_signal = 'BUY' AND tp.actual_outcome > 0) OR 
                                  (tp.predicted_signal = 'SELL' AND tp.actual_outcome < 0) OR
                                  (tp.predicted_signal = 'HOLD' AND ABS(tp.actual_outcome) < 0.5) 
                        THEN 'CORRECT' ELSE 'WRONG' END
                    ELSE 'PENDING'
                END as accuracy
            FROM trading_predictions tp
            LEFT JOIN (
                SELECT DISTINCT 
                    sf1.symbol,
                    sf1.technical_score
                FROM sentiment_features sf1
                INNER JOIN (
                    SELECT symbol, MAX(timestamp) as max_timestamp
                    FROM sentiment_features
                    GROUP BY symbol
                ) sf2 ON sf1.symbol = sf2.symbol AND sf1.timestamp = sf2.max_timestamp
            ) latest_sf ON tp.symbol = latest_sf.symbol
            WHERE tp.created_at >= datetime('now', '-7 days')
            ORDER BY tp.created_at DESC
        """)
        
        results = cursor.fetchall()
        
        if not results:
            raise DataError("No prediction timeline data found")
        
        data = []
        for row in results:
            data.append({
                'Timestamp': pd.to_datetime(row['timestamp']),
                'Symbol': row['symbol'],
                'Signal': row['signal'],
                'Confidence': float(row['confidence'] or 0),
                'Technical Score': float(row['technical_score'] or 0),
                'Sentiment Score': float(row['sentiment_score'] or 0),
                'Actual Outcome': float(row['actual_outcome'] or 0) if row['actual_outcome'] is not None else None,
                'Status': row['status'],
                'Accuracy': row['accuracy']
            })
        
        return pd.DataFrame(data)
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to fetch prediction timeline: {e}")
    finally:
        conn.close()

def render_ml_performance_section(metrics: Dict):
    """
    Render ML performance metrics section
    """
    st.subheader("🤖 Machine Learning Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Predictions (7d)",
            metrics['total_predictions'],
            help="Total predictions made in the last 7 days"
        )
    
    with col2:
        st.metric(
            "Average Confidence", 
            f"{metrics['avg_confidence']:.1%}",
            help="Average confidence score across all predictions"
        )
    
    with col3:
        st.metric(
            "Success Rate",
            f"{metrics['success_rate']:.1%}",
            help="Percentage of profitable trades in the last 30 days"
        )
    
    with col4:
        st.metric(
            "Completed Trades",
            metrics['completed_trades'],
            help="Number of completed trades with outcomes"
        )
    
    # Signal distribution
    col5, col6 = st.columns(2)
    
    with col5:
        signal_data = {
            'Signal': ['BUY', 'SELL', 'HOLD'],
            'Count': [metrics['buy_signals'], metrics['sell_signals'], metrics['hold_signals']]
        }
        fig = px.bar(signal_data, x='Signal', y='Count', 
                    title="Signal Distribution (7 days)",
                    color='Signal',
                    color_discrete_map={'BUY': 'green', 'SELL': 'red', 'HOLD': 'gray'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col6:
        if metrics['completed_trades'] > 0:
            perf_data = {
                'Metric': ['Average Return', 'Best Trade', 'Worst Trade'],
                'Value': [metrics['avg_return'], metrics['best_trade'], metrics['worst_trade']]
            }
            fig = px.bar(perf_data, x='Metric', y='Value',
                        title="Trading Performance (%)",
                        color='Value',
                        color_continuous_scale=['red', 'gray', 'green'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No completed trades for performance analysis")

def render_sentiment_dashboard(sentiment_df: pd.DataFrame):
    """
    Render current sentiment scores dashboard
    """
    st.subheader("📊 Current Sentiment Scores")
    
    # Create color mapping for signals
    def get_signal_color(signal):
        return {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}[signal]
    
    # Display sentiment table with enhanced formatting
    display_df = sentiment_df.copy()
    display_df['Signal Indicator'] = display_df['Signal'].apply(get_signal_color)
    display_df['Confidence'] = display_df['Confidence'].apply(lambda x: f"{x:.1%}")
    display_df['Sentiment Score'] = display_df['Sentiment Score'].apply(lambda x: f"{x:+.4f}")
    display_df['Last Update'] = pd.to_datetime(display_df['Timestamp']).dt.strftime('%H:%M:%S')
    
    # Select columns for display
    display_cols = ['Symbol', 'Signal Indicator', 'Signal', 'Sentiment Score', 'Confidence', 
                   'News Count', 'Last Update']
    
    st.dataframe(
        display_df[display_cols],
        use_container_width=True,
        hide_index=True
    )
    
    # Sentiment visualization
    col1, col2 = st.columns(2)
    
    with col1:
        # Sentiment scores chart
        fig = px.bar(
            sentiment_df, 
            x='Symbol', 
            y='Sentiment Score',
            color='Signal',
            title="Current Sentiment Scores by Bank",
            color_discrete_map={'BUY': 'green', 'SELL': 'red', 'HOLD': 'gray'}
        )
        fig.add_hline(y=0.05, line_dash="dash", line_color="green", 
                     annotation_text="BUY threshold")
        fig.add_hline(y=-0.05, line_dash="dash", line_color="red",
                     annotation_text="SELL threshold")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Confidence distribution
        fig = px.scatter(
            sentiment_df,
            x='Sentiment Score',
            y='Confidence',
            color='Symbol',
            size='News Count',
            title="Confidence vs Sentiment",
            hover_data=['Signal']
        )
        st.plotly_chart(fig, use_container_width=True)

def render_technical_analysis(sentiment_df: pd.DataFrame):
    """
    Render technical analysis indicators
    """
    st.subheader("📈 Technical Analysis Indicators")
    
    # Technical scores overview
    tech_data = sentiment_df[['Symbol', 'Technical Score', 'Event Score', 'Reddit Sentiment']].copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Technical scores heatmap-style display
        fig = px.imshow(
            tech_data.set_index('Symbol')[['Technical Score', 'Event Score', 'Reddit Sentiment']].T,
            title="Technical Indicators Heatmap",
            color_continuous_scale='RdYlGn',
            aspect='auto'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Combined indicator strength
        tech_data['Combined Strength'] = (
            tech_data['Technical Score'].abs() + 
            tech_data['Event Score'].abs() + 
            tech_data['Reddit Sentiment'].abs()
        ) / 3
        
        fig = px.bar(
            tech_data,
            x='Symbol',
            y='Combined Strength',
            title="Combined Indicator Strength",
            color='Combined Strength',
            color_continuous_scale='viridis'
        )
        st.plotly_chart(fig, use_container_width=True)

def render_ml_features_explanation(feature_analysis: Dict):
    """
    Render dynamic ML features explanation
    """
    st.subheader("🔍 ML Model Feature Analysis")
    
    st.write(f"**Analysis based on {feature_analysis['total_records']} recent predictions**")
    
    # Feature usage statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Feature Usage Rates:**")
        usage = feature_analysis['feature_usage']
        for feature, rate in usage.items():
            st.metric(feature.replace('_', ' ').title(), f"{rate:.1f}%")
    
    with col2:
        st.write("**Feature Strength (Average):**")
        strength = feature_analysis['feature_strength']
        for feature, value in strength.items():
            if 'count' in feature:
                st.metric(feature.replace('_', ' ').title(), f"{value:.1f}")
            else:
                st.metric(feature.replace('_', ' ').title(), f"{value:.3f}")
    
    # Feature importance visualization
    usage_data = pd.DataFrame([
        {'Feature': k.replace('_', ' ').title(), 'Usage Rate': v}
        for k, v in feature_analysis['feature_usage'].items()
    ])
    
    fig = px.bar(
        usage_data,
        x='Feature',
        y='Usage Rate',
        title="ML Feature Usage Rates (%)",
        color='Usage Rate',
        color_continuous_scale='blues'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ML Features details
    if feature_analysis['ml_features']:
        with st.expander("🔧 Detailed ML Features"):
            st.json(feature_analysis['ml_features'])

def render_prediction_timeline(timeline_df: pd.DataFrame):
    """
    Render prediction performance over time
    """
    st.subheader("⏱️ Prediction Timeline (Last 7 Days)")
    
    # Show data availability info
    if not timeline_df.empty:
        latest_prediction = timeline_df['Timestamp'].max()
        oldest_prediction = timeline_df['Timestamp'].min()
        unique_timestamps = timeline_df['Timestamp'].nunique()
        
        if unique_timestamps == 1:
            st.info(f"📅 All {len(timeline_df)} predictions were generated in a batch run on {latest_prediction.strftime('%Y-%m-%d at %H:%M:%S')}")
        else:
            st.info(f"📅 Prediction data available from {oldest_prediction.strftime('%Y-%m-%d %H:%M')} to {latest_prediction.strftime('%Y-%m-%d %H:%M')} ({unique_timestamps} different timestamps)")
    else:
        st.warning("⚠️ No prediction timeline data found in the last 7 days")
        return
    
    # Group by day for overview (or by timestamp if batch)
    timeline_df['Date'] = timeline_df['Timestamp'].dt.date
    unique_dates = timeline_df['Date'].nunique()
    
    if unique_dates == 1:
        # Single batch - show symbol distribution instead
        symbol_stats = timeline_df.groupby('Symbol').agg({
            'Confidence': 'mean',
            'Signal': 'count',
            'Accuracy': lambda x: (x == 'CORRECT').sum()
        }).rename(columns={'Signal': 'Total Predictions', 'Accuracy': 'Correct Predictions'})
        symbol_stats['Success Rate'] = (symbol_stats['Correct Predictions'] / symbol_stats['Total Predictions'] * 100).round(1)
        symbol_stats.reset_index(inplace=True)
        
        # Show symbol performance instead of timeline
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                symbol_stats, 
                x='Symbol', 
                y='Total Predictions',
                title="Predictions per Symbol (Batch Run)",
                color='Success Rate',
                color_continuous_scale='RdYlGn',
                text='Total Predictions'
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                symbol_stats,
                x='Confidence',
                y='Success Rate',
                size='Total Predictions',
                color='Symbol',
                title="Confidence vs Success Rate by Symbol",
                hover_data=['Total Predictions']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Show summary stats for the batch
        st.write("**Batch Run Summary:**")
        col1, col2, col3, col4 = st.columns(4)
        
        total_predictions = len(timeline_df)
        correct_predictions = (timeline_df['Accuracy'] == 'CORRECT').sum()
        avg_confidence = timeline_df['Confidence'].mean()
        success_rate = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        with col1:
            st.metric("Total Predictions", total_predictions)
        with col2:
            st.metric("Correct Predictions", correct_predictions)
        with col3:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col4:
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        
    else:
        # Multiple dates - show normal timeline
        daily_stats = timeline_df.groupby('Date').agg({
            'Confidence': 'mean',
            'Symbol': 'count',
            'Signal': lambda x: (x == 'BUY').sum()
        }).rename(columns={'Symbol': 'Total Predictions', 'Signal': 'Buy Signals'})
        
        daily_stats.reset_index(inplace=True)
        
        # Timeline visualization
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Daily Prediction Volume', 'Average Confidence'),
            vertical_spacing=0.1
        )
        
        fig.add_trace(
            go.Bar(x=daily_stats['Date'], y=daily_stats['Total Predictions'], 
                   name='Total Predictions'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=daily_stats['Date'], y=daily_stats['Confidence'],
                      mode='lines+markers', name='Avg Confidence'),
            row=2, col=1
        )
        
        fig.update_layout(height=500, title_text="Prediction Performance Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent predictions table with outcomes
    st.write("**Sample of Recent Predictions:**")
    recent_df = timeline_df.head(15).copy()
    
    # Helper functions for formatting
    def format_outcome(row):
        if row['Actual Outcome'] is None or pd.isna(row['Actual Outcome']):
            return "Pending"
        outcome = row['Actual Outcome']
        if outcome > 0:
            return f"+{outcome:.2f}%"
        else:
            return f"{outcome:.2f}%"
    
    def format_accuracy(accuracy):
        if accuracy == 'CORRECT':
            return "✅ CORRECT"
        elif accuracy == 'WRONG':
            return "❌ WRONG"
        else:
            return "⏳ PENDING"
    
    # Format recent predictions
    if timeline_df['Timestamp'].nunique() == 1:
        recent_df['Order'] = range(1, len(recent_df) + 1)
        recent_df['Time'] = recent_df['Timestamp'].dt.strftime('%m-%d %H:%M') + ' (#' + recent_df['Order'].astype(str) + ')'
    else:
        recent_df['Time'] = recent_df['Timestamp'].dt.strftime('%m-%d %H:%M')
    
    recent_df['Confidence'] = recent_df['Confidence'].apply(lambda x: f"{x:.1%}")
    recent_df['Tech Score'] = recent_df['Technical Score'].apply(lambda x: f"{x:.1f}")
    recent_df['Sentiment'] = recent_df['Sentiment Score'].apply(lambda x: f"{x:+.3f}")
    recent_df['Outcome'] = recent_df.apply(format_outcome, axis=1)
    recent_df['Result'] = recent_df['Accuracy'].apply(format_accuracy)
    
    display_recent = recent_df[['Time', 'Symbol', 'Signal', 'Confidence', 'Tech Score', 'Sentiment', 'Outcome', 'Result']]
    st.dataframe(display_recent, use_container_width=True, hide_index=True)
    
    # All predictions table in expandable section
    with st.expander(f"📋 **View All {len(timeline_df)} Predictions**", expanded=False):
        st.write("**Complete prediction batch with filtering options:**")
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            symbol_filter = st.selectbox(
                "Filter by Symbol:",
                ["All"] + sorted(timeline_df['Symbol'].unique().tolist()),
                key="symbol_filter"
            )
        
        with col2:
            signal_filter = st.selectbox(
                "Filter by Signal:",
                ["All"] + sorted(timeline_df['Signal'].unique().tolist()),
                key="signal_filter"
            )
        
        with col3:
            accuracy_filter = st.selectbox(
                "Filter by Result:",
                ["All", "CORRECT", "WRONG", "PENDING"],
                key="accuracy_filter"
            )
        
        # Apply filters
        filtered_df = timeline_df.copy()
        
        if symbol_filter != "All":
            filtered_df = filtered_df[filtered_df['Symbol'] == symbol_filter]
        
        if signal_filter != "All":
            filtered_df = filtered_df[filtered_df['Signal'] == signal_filter]
        
        if accuracy_filter != "All":
            filtered_df = filtered_df[filtered_df['Accuracy'] == accuracy_filter]
        
        if len(filtered_df) > 0:
            # Format all predictions
            all_df = filtered_df.copy()
            
            # Add row numbers for batch identification
            if timeline_df['Timestamp'].nunique() == 1:
                # For batch predictions, add global order numbers
                all_df = all_df.reset_index(drop=True)
                all_df['Order'] = range(1, len(all_df) + 1)
                all_df['Time'] = all_df['Timestamp'].dt.strftime('%m-%d %H:%M') + ' (#' + all_df['Order'].astype(str) + ')'
            else:
                all_df['Time'] = all_df['Timestamp'].dt.strftime('%m-%d %H:%M')
            
            all_df['Confidence'] = all_df['Confidence'].apply(lambda x: f"{x:.1%}")
            all_df['Tech Score'] = all_df['Technical Score'].apply(lambda x: f"{x:.1f}")
            all_df['Sentiment'] = all_df['Sentiment Score'].apply(lambda x: f"{x:+.3f}")
            all_df['Outcome'] = all_df.apply(format_outcome, axis=1)
            all_df['Result'] = all_df['Accuracy'].apply(format_accuracy)
            
            # Display summary of filtered results
            st.write(f"**Showing {len(all_df)} predictions** (filtered from {len(timeline_df)} total)")
            if len(all_df) != len(timeline_df):
                correct_filtered = (all_df['Accuracy'] == 'CORRECT').sum()
                success_rate_filtered = (correct_filtered / len(all_df) * 100) if len(all_df) > 0 else 0
                st.write(f"Filtered success rate: **{success_rate_filtered:.1f}%** ({correct_filtered}/{len(all_df)} correct)")
            
            # Display the complete table
            display_all = all_df[['Time', 'Symbol', 'Signal', 'Confidence', 'Tech Score', 'Sentiment', 'Outcome', 'Result']]
            st.dataframe(display_all, use_container_width=True, hide_index=True, height=400)
            
            # Add download option for the filtered data
            csv_data = display_all.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Predictions as CSV",
                data=csv_data,
                file_name=f"predictions_batch_{timeline_df['Timestamp'].iloc[0].strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
            
        else:
            st.warning("No predictions match the selected filters.")

def main():
    """
    Main dashboard application
    """
    # Page configuration
    st.set_page_config(
        page_title="ASX Banks Trading Sentiment Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Header
    st.title("📊 ASX Banks Trading Sentiment Dashboard")
    st.markdown("**Real-time sentiment analysis and ML predictions for Australian bank stocks**")
    st.markdown("---")
    
    # Auto-refresh info
    st.sidebar.header("Dashboard Info")
    st.sidebar.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.sidebar.write(f"**Data Source:** {DATABASE_PATH}")
    st.sidebar.write(f"**Banks Tracked:** {len(ASX_BANKS)}")
    
    # Add data freshness check
    try:
        conn = get_database_connection()
        cursor = conn.execute("SELECT MAX(timestamp) FROM sentiment_features")
        latest_sentiment = cursor.fetchone()[0]
        cursor = conn.execute("SELECT MAX(created_at) FROM trading_predictions")
        latest_prediction = cursor.fetchone()[0]
        conn.close()
        
        st.sidebar.write("**Data Freshness:**")
        if latest_sentiment:
            st.sidebar.write(f"• Sentiment: {latest_sentiment}")
        if latest_prediction:
            st.sidebar.write(f"• Predictions: {latest_prediction}")
    except:
        pass
    
    if st.sidebar.button("🔄 Refresh Data"):
        # Clear Streamlit cache
        st.cache_data.clear()
        st.rerun()
    
    try:
        # Load all data
        with st.spinner("Loading real-time data..."):
            ml_metrics = fetch_ml_performance_metrics()
            sentiment_df = fetch_current_sentiment_scores()
            feature_analysis = fetch_ml_feature_analysis()
            timeline_df = fetch_prediction_timeline()
        
        # Render dashboard sections
        render_ml_performance_section(ml_metrics)
        st.markdown("---")
        
        render_sentiment_dashboard(sentiment_df)
        st.markdown("---")
        
        render_technical_analysis(sentiment_df)
        st.markdown("---")
        
        render_ml_features_explanation(feature_analysis)
        st.markdown("---")
        
        render_prediction_timeline(timeline_df)
        
        # Footer
        st.markdown("---")
        st.markdown("*Dashboard updates automatically when refreshed. All data sourced from live SQL database.*")
        
    except DatabaseError as e:
        st.error(f"🚨 Database Error: {e}")
        st.info("Please check database connectivity and try again.")
        
    except DataError as e:
        st.error(f"📊 Data Error: {e}")
        st.info("The system may be updating data. Please try refreshing in a moment.")
        
    except Exception as e:
        st.error(f"💥 Unexpected Error: {e}")
        st.info("Please contact system administrator if this persists.")
        raise  # Re-raise for debugging in development

if __name__ == "__main__":
    main()
