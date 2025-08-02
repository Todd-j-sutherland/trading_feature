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
import sys
import os

# Add the app directory to the path for MarketAux integration
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from app.core.sentiment.marketaux_integration import MarketAuxManager

# Configuration
DATABASE_PATH = "data/ml_models/enhanced_training_data.db"
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
            FROM enhanced_features 
            WHERE timestamp >= date('now', '-7 days')
        """)
        
        row = cursor.fetchone()
        if not row or row['total_predictions'] == 0:
            raise DataError("No prediction data found in the last 7 days")
        
        # Get performance from enhanced outcomes
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as completed_trades,
                AVG(return_pct) as avg_return,
                COUNT(CASE WHEN return_pct > 0 THEN 1 END) as successful_trades,
                MAX(return_pct) as best_trade,
                MIN(return_pct) as worst_trade
            FROM enhanced_outcomes 
            WHERE exit_timestamp IS NOT NULL
            AND prediction_timestamp >= date('now', '-30 days')
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

def fetch_performance_timeline_data(days: int = 30) -> pd.DataFrame:
    """
    Fetch performance timeline data for the success rate chart
    Returns DataFrame with daily success rates and outcome counts
    """
    conn = get_database_connection()
    
    try:
        # Get daily performance data
        cursor = conn.execute("""
            SELECT 
                DATE(prediction_timestamp) as date,
                COUNT(*) as total_outcomes,
                COUNT(CASE WHEN return_pct > 0 THEN 1 END) as successful_outcomes,
                ROUND(
                    CAST(COUNT(CASE WHEN return_pct > 0 THEN 1 END) AS FLOAT) / 
                    CAST(COUNT(*) AS FLOAT) * 100, 1
                ) as success_rate_pct,
                AVG(return_pct) as avg_return_pct,
                COUNT(DISTINCT symbol) as banks_traded
            FROM enhanced_outcomes 
            WHERE prediction_timestamp >= date('now', '-{} days')
            AND exit_timestamp IS NOT NULL
            GROUP BY DATE(prediction_timestamp)
            ORDER BY date ASC
        """.format(days))
        
        results = cursor.fetchall()
        
        if not results:
            # Return empty DataFrame with proper structure
            return pd.DataFrame(columns=[
                'Date', 'Total_Outcomes', 'Successful_Outcomes', 
                'Success_Rate_Pct', 'Avg_Return_Pct', 'Banks_Traded'
            ])
        
        data = []
        cumulative_outcomes = 0
        
        for row in results:
            cumulative_outcomes += row['total_outcomes']
            
            data.append({
                'Date': pd.to_datetime(row['date']),
                'Total_Outcomes': row['total_outcomes'],
                'Cumulative_Outcomes': cumulative_outcomes,
                'Successful_Outcomes': row['successful_outcomes'],
                'Success_Rate_Pct': float(row['success_rate_pct'] or 0),
                'Avg_Return_Pct': float(row['avg_return_pct'] or 0),
                'Banks_Traded': row['banks_traded']
            })
        
        return pd.DataFrame(data)
        
    except sqlite3.Error as e:
        # Return empty DataFrame instead of raising error
        st.warning(f"Could not fetch performance timeline: {e}")
        return pd.DataFrame(columns=[
            'Date', 'Total_Outcomes', 'Cumulative_Outcomes', 
            'Successful_Outcomes', 'Success_Rate_Pct', 'Avg_Return_Pct', 'Banks_Traded'
        ])
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
                s1.rsi as technical_score,
                CASE 
                    WHEN s1.sentiment_score > 0.05 THEN 'BUY'
                    WHEN s1.sentiment_score < -0.05 THEN 'SELL'
                    ELSE 'HOLD'
                END as signal
            FROM enhanced_features s1
            INNER JOIN (
                SELECT symbol, MAX(timestamp) as max_timestamp
                FROM enhanced_features
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

def fetch_marketaux_sentiment_comparison() -> pd.DataFrame:
    """
    Fetch MarketAux sentiment data and compare with existing Reddit sentiment
    Returns DataFrame with comparison data
    """
    try:
        # Initialize MarketAux manager
        marketaux_manager = MarketAuxManager()
        
        # Get MarketAux sentiment data
        marketaux_results = marketaux_manager.get_super_batch_sentiment()
        
        # Get current Reddit sentiment from database (which is broken/0.0)
        reddit_df = fetch_current_sentiment_scores()
        
        # Create comparison data
        comparison_data = []
        
        # Convert ASX_BANKS format (CBA.AX) to MarketAux format (CBA)
        bank_mapping = {bank.replace('.AX', ''): bank for bank in ASX_BANKS}
        
        for marketaux_result in marketaux_results:
            symbol = marketaux_result.symbol
            asx_symbol = bank_mapping.get(symbol, f"{symbol}.AX")
            
            # Find corresponding Reddit data
            reddit_row = reddit_df[reddit_df['Symbol'] == asx_symbol]
            reddit_sentiment = reddit_row['Reddit Sentiment'].iloc[0] if not reddit_row.empty else 0.0
            
            # Calculate combined sentiment (70% MarketAux, 30% Reddit due to Reddit reliability issues)
            combined_sentiment = (marketaux_result.sentiment_score * 0.7) + (reddit_sentiment * 0.3)
            
            comparison_data.append({
                'Symbol': symbol,
                'ASX Symbol': asx_symbol,
                'Reddit Sentiment': reddit_sentiment,
                'MarketAux Sentiment': marketaux_result.sentiment_score,
                'Combined Sentiment': combined_sentiment,
                'MarketAux Confidence': marketaux_result.confidence,
                'News Volume': marketaux_result.news_volume,
                'Source Quality': marketaux_result.source_quality,
                'Key News': marketaux_result.highlights[0][:100] + "..." if marketaux_result.highlights else "No news",
                'Sentiment Change': combined_sentiment - reddit_sentiment,
                'Signal Strength': 'Strong' if abs(marketaux_result.sentiment_score) > 0.3 else 'Moderate' if abs(marketaux_result.sentiment_score) > 0.15 else 'Weak',
                'Trading Signal': 'BUY' if combined_sentiment > 0.1 else 'SELL' if combined_sentiment < -0.1 else 'HOLD'
            })
        
        return pd.DataFrame(comparison_data)
        
    except Exception as e:
        st.error(f"Error fetching MarketAux data: {e}")
        # Return empty DataFrame with expected columns if MarketAux fails
        return pd.DataFrame(columns=[
            'Symbol', 'ASX Symbol', 'Reddit Sentiment', 'MarketAux Sentiment', 
            'Combined Sentiment', 'MarketAux Confidence', 'News Volume', 
            'Source Quality', 'Key News', 'Sentiment Change', 'Signal Strength', 'Trading Signal'
        ])

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
                AVG(CASE WHEN rsi IS NOT NULL THEN 1.0 ELSE 0.0 END) as technical_usage,
                AVG(news_count) as avg_news_count,
                AVG(ABS(reddit_sentiment)) as avg_reddit_strength,
                AVG(ABS(event_score)) as avg_event_strength,
                AVG(rsi) as avg_technical_strength,
                feature_version as ml_features
            FROM enhanced_features 
            WHERE timestamp >= date('now', '-30 days')
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        
        if not row:
            raise DataError("No ML feature data found")
        
        # Get detailed feature statistics from SQL instead of JSON
        feature_details = {
            'feature_version': row['ml_features'] or 'Unknown',
            'total_features': 53,  # Based on schema analysis
            'feature_categories': {
                'Sentiment Features': ['sentiment_score', 'confidence', 'news_count', 'reddit_sentiment', 'event_score'],
                'Technical Indicators': ['rsi', 'macd_line', 'macd_signal', 'macd_histogram', 'sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26', 'bollinger_upper', 'bollinger_lower', 'bollinger_width'],
                'Price Features': ['current_price', 'price_change_1h', 'price_change_4h', 'price_change_1d', 'price_change_5d', 'price_change_20d', 'price_vs_sma20', 'price_vs_sma50', 'price_vs_sma200', 'daily_range', 'atr_14', 'volatility_20d'],
                'Volume Features': ['volume', 'volume_sma20', 'volume_ratio', 'on_balance_volume', 'volume_price_trend'],
                'Market Context': ['asx200_change', 'sector_performance', 'aud_usd_rate', 'vix_level', 'market_breadth', 'market_momentum'],
                'Interaction Features': ['sentiment_momentum', 'sentiment_rsi', 'volume_sentiment', 'confidence_volatility', 'news_volume_impact', 'technical_sentiment_divergence'],
                'Time Features': ['asx_market_hours', 'asx_opening_hour', 'asx_closing_hour', 'monday_effect', 'friday_effect', 'month_end', 'quarter_end']
            },
            'usage_stats': {
                'news_analysis': float(row['news_usage'] or 0) * 100,
                'reddit_sentiment': float(row['reddit_usage'] or 0) * 100,
                'event_scoring': float(row['event_usage'] or 0) * 100,
                'technical_indicators': float(row['technical_usage'] or 0) * 100
            }
        }
        
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
            'ml_features': feature_details
        }
        
        return feature_analysis
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to fetch ML feature analysis: {e}")
    finally:
        conn.close()

def fetch_portfolio_correlation_data() -> Dict:
    """
    Fetch portfolio correlation and concentration risk data
    Returns correlation matrix, sector concentration, and risk metrics
    """
    conn = get_database_connection()
    
    try:
        # Get recent sentiment scores for correlation calculation
        cursor = conn.execute("""
            SELECT 
                sf.symbol,
                sf.sentiment_score,
                sf.rsi as technical_score,
                sf.confidence,
                sf.timestamp,
                ROW_NUMBER() OVER (PARTITION BY sf.symbol ORDER BY sf.timestamp DESC) as rn
            FROM enhanced_features sf
            WHERE sf.timestamp >= date('now', '-7 days')
            AND sf.symbol IN ({})
        """.format(','.join('?' * len(ASX_BANKS))), ASX_BANKS)
        
        results = cursor.fetchall()
        
        if not results:
            raise DataError("No recent data for portfolio correlation analysis")
        
        # Create DataFrame for correlation analysis
        data = []
        for row in results:
            data.append({
                'symbol': row['symbol'],
                'sentiment_score': float(row['sentiment_score'] or 0),
                'technical_score': float(row['technical_score'] or 0),
                'confidence': float(row['confidence'] or 0),
                'timestamp': row['timestamp'],
                'rn': row['rn']
            })
        
        df = pd.DataFrame(data)
        
        # Calculate correlation matrices
        sentiment_pivot = df[df['rn'] <= 10].pivot_table(
            index='timestamp', 
            columns='symbol', 
            values='sentiment_score', 
            fill_value=0
        )
        
        technical_pivot = df[df['rn'] <= 10].pivot_table(
            index='timestamp', 
            columns='symbol', 
            values='technical_score', 
            fill_value=0
        )
        
        # Get current signal distribution for concentration analysis
        cursor = conn.execute("""
            SELECT 
                s1.symbol,
                CASE 
                    WHEN s1.sentiment_score > 0.05 THEN 'BUY'
                    WHEN s1.sentiment_score < -0.05 THEN 'SELL'
                    ELSE 'HOLD'
                END as current_signal,
                s1.sentiment_score,
                s1.confidence
            FROM enhanced_features s1
            INNER JOIN (
                SELECT symbol, MAX(timestamp) as max_timestamp
                FROM enhanced_features
                WHERE symbol IN ({})
                GROUP BY symbol
            ) s2 ON s1.symbol = s2.symbol AND s1.timestamp = s2.max_timestamp
        """.format(','.join('?' * len(ASX_BANKS))), ASX_BANKS)
        
        current_signals = cursor.fetchall()
        
        # Calculate portfolio metrics
        sentiment_corr = sentiment_pivot.corr() if len(sentiment_pivot) > 1 else pd.DataFrame()
        technical_corr = technical_pivot.corr() if len(technical_pivot) > 1 else pd.DataFrame()
        
        # Concentration risk analysis
        signal_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        signal_details = []
        
        for signal_row in current_signals:
            signal = signal_row['current_signal']
            signal_counts[signal] += 1
            signal_details.append({
                'symbol': signal_row['symbol'],
                'signal': signal,
                'sentiment_score': float(signal_row['sentiment_score'] or 0),
                'confidence': float(signal_row['confidence'] or 0)
            })
        
        # Calculate concentration risk score (0-100, higher = more risk)
        total_banks = len(ASX_BANKS)
        max_signal_count = max(signal_counts.values())
        concentration_risk = (max_signal_count / total_banks) * 100
        
        # Diversification score (0-100, higher = better diversification)
        signal_distribution = np.array(list(signal_counts.values()))
        diversification_score = 100 - ((np.std(signal_distribution) / np.mean(signal_distribution)) * 100) if np.mean(signal_distribution) > 0 else 0
        diversification_score = max(0, min(100, diversification_score))
        
        return {
            'sentiment_correlation': sentiment_corr,
            'technical_correlation': technical_corr,
            'signal_distribution': signal_counts,
            'signal_details': signal_details,
            'concentration_risk': concentration_risk,
            'diversification_score': diversification_score,
            'avg_correlation': sentiment_corr.values[sentiment_corr.values != 1.0].mean() if not sentiment_corr.empty else 0,
            'max_correlation': sentiment_corr.values[sentiment_corr.values != 1.0].max() if not sentiment_corr.empty else 0,
            'data_points': len(sentiment_pivot)
        }
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to fetch portfolio correlation data: {e}")
    finally:
        conn.close()

def fetch_prediction_timeline() -> pd.DataFrame:
    """
    Fetch prediction timeline with actual outcomes for performance visualization
    Returns DataFrame based on enhanced features and outcomes
    """
    conn = get_database_connection()
    
    try:
        # Get features with outcomes from the enhanced database
        query = """
            SELECT 
                ef.timestamp,
                ef.symbol,
                CASE 
                    WHEN ef.rsi < 30 THEN 'BUY'
                    WHEN ef.rsi > 70 THEN 'SELL'
                    ELSE 'HOLD'
                END as signal,
                CASE 
                    WHEN ef.rsi < 30 OR ef.rsi > 70 THEN 0.8
                    ELSE 0.3
                END as confidence,
                ef.sentiment_score,
                ef.rsi as technical_score,
                eo.return_pct as actual_outcome,
                CASE 
                    WHEN eo.return_pct IS NOT NULL THEN 'COMPLETED'
                    ELSE 'PENDING'
                END as status,
                CASE 
                    WHEN eo.return_pct IS NOT NULL THEN
                        CASE 
                            WHEN (ef.rsi < 30 AND eo.return_pct > 0) OR 
                                 (ef.rsi > 70 AND eo.return_pct < 0) OR
                                 (ef.rsi BETWEEN 30 AND 70 AND ABS(eo.return_pct) < 0.5) 
                            THEN 'CORRECT' 
                            ELSE 'WRONG' 
                        END
                    ELSE 'PENDING'
                END as accuracy
            FROM enhanced_features ef
            LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
            WHERE ef.timestamp >= datetime('now', '-7 days')
            ORDER BY ef.timestamp DESC
            LIMIT 100
        """
        
        cursor = conn.execute(query)
        results = cursor.fetchall()
        
        if not results:
            # Return empty DataFrame with proper structure
            return pd.DataFrame(columns=[
                'Timestamp', 'Symbol', 'Signal', 'Confidence', 
                'Technical Score', 'Sentiment Score', 'Actual Outcome', 
                'Status', 'Accuracy'
            ])
        
        data = []
        for row in results:
            data.append({
                'Timestamp': pd.to_datetime(row[0]),  # timestamp
                'Symbol': row[1],                      # symbol
                'Signal': row[2],                      # signal
                'Confidence': float(row[3] or 0),     # confidence
                'Sentiment Score': float(row[4] or 0), # sentiment_score
                'Technical Score': float(row[5] or 0), # technical_score (rsi)
                'Actual Outcome': float(row[6] or 0) if row[6] is not None else None, # actual_outcome
                'Status': row[7] or 'PENDING',        # status
                'Accuracy': row[8] or 'PENDING'       # accuracy
            })
        
        return pd.DataFrame(data)
        
    except sqlite3.Error as e:
        # Return empty DataFrame instead of raising error
        st.warning(f"Could not fetch prediction timeline: {e}")
        return pd.DataFrame(columns=[
            'Timestamp', 'Symbol', 'Signal', 'Confidence', 
            'Technical Score', 'Sentiment Score', 'Actual Outcome', 
            'Status', 'Accuracy'
        ])
    finally:
        conn.close()

def render_portfolio_correlation_section(correlation_data: Dict):
    """
    Render portfolio correlation and concentration risk analysis
    """
    st.subheader("🔗 Portfolio Risk Management")
    
    # Key metrics overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_color = "🔴" if correlation_data['concentration_risk'] > 70 else "🟡" if correlation_data['concentration_risk'] > 40 else "🟢"
        st.metric(
            "Concentration Risk",
            f"{risk_color} {correlation_data['concentration_risk']:.1f}%",
            help="Higher = more concentrated positions in same direction"
        )
    
    with col2:
        div_color = "🟢" if correlation_data['diversification_score'] > 60 else "🟡" if correlation_data['diversification_score'] > 30 else "🔴"
        st.metric(
            "Diversification Score", 
            f"{div_color} {correlation_data['diversification_score']:.1f}%",
            help="Higher = better signal diversification across banks"
        )
    
    with col3:
        avg_corr = correlation_data['avg_correlation']
        corr_color = "🔴" if abs(avg_corr) > 0.7 else "🟡" if abs(avg_corr) > 0.4 else "🟢"
        st.metric(
            "Avg Correlation",
            f"{corr_color} {avg_corr:.3f}",
            help="Average correlation between bank sentiment scores"
        )
    
    with col4:
        st.metric(
            "Data Points",
            correlation_data['data_points'],
            help="Number of time periods used for correlation analysis"
        )
    
    # Signal distribution and correlation heatmaps
    col1, col2 = st.columns(2)
    
    with col1:
        # Current signal distribution
        signal_data = correlation_data['signal_distribution']
        fig = px.pie(
            values=list(signal_data.values()),
            names=list(signal_data.keys()),
            title="Current Signal Distribution",
            color_discrete_map={'BUY': 'green', 'SELL': 'red', 'HOLD': 'gray'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Risk assessment
        risk_level = "🔴 HIGH" if correlation_data['concentration_risk'] > 70 else "🟡 MEDIUM" if correlation_data['concentration_risk'] > 40 else "🟢 LOW"
        st.write(f"**Portfolio Risk Level**: {risk_level}")
        
        if correlation_data['concentration_risk'] > 60:
            st.warning("⚠️ High concentration risk detected - consider position adjustments")
        elif correlation_data['concentration_risk'] > 40:
            st.info("📊 Moderate concentration - monitor for changes")
        else:
            st.success("✅ Good diversification across signals")
    
    with col2:
        # Sentiment correlation heatmap
        if not correlation_data['sentiment_correlation'].empty:
            fig = px.imshow(
                correlation_data['sentiment_correlation'],
                title="Sentiment Score Correlations (7-day)",
                color_continuous_scale='RdBu_r',
                aspect='auto',
                zmin=-1, zmax=1
            )
            fig.update_layout(
                xaxis_title="Bank",
                yaxis_title="Bank"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Insufficient data for correlation analysis")
    
    # Detailed signal breakdown
    with st.expander("📋 **Detailed Signal Analysis**", expanded=False):
        signal_df = pd.DataFrame(correlation_data['signal_details'])
        
        if not signal_df.empty:
            # Enhanced signal table
            signal_df['Confidence'] = signal_df['confidence'].apply(lambda x: f"{x:.1%}")
            signal_df['Sentiment Score'] = signal_df['sentiment_score'].apply(lambda x: f"{x:+.4f}")
            signal_df['Signal Strength'] = signal_df['sentiment_score'].abs()
            
            # Color coding for signals
            def get_signal_indicator(signal):
                return {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}[signal]
            
            signal_df['Indicator'] = signal_df['signal'].apply(get_signal_indicator)
            
            display_df = signal_df[['symbol', 'Indicator', 'signal', 'Sentiment Score', 'Confidence']].copy()
            display_df.columns = ['Symbol', 'Indicator', 'Signal', 'Sentiment Score', 'Confidence']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Correlation warnings
            if not correlation_data['sentiment_correlation'].empty:
                high_corr_pairs = []
                corr_matrix = correlation_data['sentiment_correlation']
                
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:  # High correlation threshold
                            bank1 = corr_matrix.columns[i]
                            bank2 = corr_matrix.columns[j]
                            high_corr_pairs.append(f"{bank1} ↔ {bank2}: {corr_val:.3f}")
                
                if high_corr_pairs:
                    st.warning("⚠️ **High Correlation Alert**:")
                    for pair in high_corr_pairs:
                        st.write(f"• {pair}")
                    st.write("Consider reducing exposure to highly correlated positions")
        else:
            st.info("No signal data available for detailed analysis")
    
    # Technical correlation (if available)
    if not correlation_data['technical_correlation'].empty:
        with st.expander("🔧 **Technical Correlation Analysis**", expanded=False):
            fig = px.imshow(
                correlation_data['technical_correlation'],
                title="Technical Score Correlations (7-day)",
                color_continuous_scale='RdBu_r',
                aspect='auto',
                zmin=-1, zmax=1
            )
            fig.update_layout(
                xaxis_title="Bank",
                yaxis_title="Bank"
            )
            st.plotly_chart(fig, use_container_width=True)

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
    
    # Performance Timeline Chart
    st.markdown("---")
    st.subheader("📈 Performance Timeline")
    
    # Time scale selector
    time_scale = st.selectbox(
        "Select Time Scale:",
        options=['Daily (30 days)', 'Weekly (12 weeks)', 'Monthly (6 months)'],
        index=0,
        help="Choose the time period and granularity for the performance chart"
    )
    
    # Determine days based on selection
    if 'Daily' in time_scale:
        days = 30
        group_by = 'day'
    elif 'Weekly' in time_scale:
        days = 84  # 12 weeks
        group_by = 'week'
    else:  # Monthly
        days = 180  # 6 months
        group_by = 'month'
    
    # Fetch timeline data
    timeline_data = fetch_performance_timeline_data(days)
    
    if not timeline_data.empty:
        # Create dual-axis chart
        fig = make_subplots(
            specs=[[{"secondary_y": True}]],
            subplot_titles=("AI Performance Over Time",)
        )
        
        # Add success rate line (left y-axis)
        fig.add_trace(
            go.Scatter(
                x=timeline_data['Date'],
                y=timeline_data['Success_Rate_Pct'],
                mode='lines+markers',
                name='Success Rate %',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=6),
                hovertemplate='<b>%{x}</b><br>Success Rate: %{y}%<br><extra></extra>'
            ),
            secondary_y=False,
        )
        
        # Add cumulative outcomes line (right y-axis)
        fig.add_trace(
            go.Scatter(
                x=timeline_data['Date'],
                y=timeline_data['Cumulative_Outcomes'],
                mode='lines+markers',
                name='Total Outcomes',
                line=dict(color='#2ca02c', width=3),
                marker=dict(size=6),
                hovertemplate='<b>%{x}</b><br>Total Outcomes: %{y}<br><extra></extra>'
            ),
            secondary_y=True,
        )
        
        # Set x-axis title
        fig.update_xaxes(title_text="Date")
        
        # Set y-axes titles
        fig.update_yaxes(title_text="Success Rate (%)", color='#1f77b4', secondary_y=False)
        fig.update_yaxes(title_text="Cumulative Outcomes", color='#2ca02c', secondary_y=True)
        
        # Update layout
        fig.update_layout(
            title=f"Performance Timeline ({time_scale})",
            hovermode='x unified',
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        if len(timeline_data) > 1:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_success = timeline_data['Success_Rate_Pct'].mean()
                st.metric("Avg Success Rate", f"{avg_success:.1f}%")
            
            with col2:
                total_outcomes = timeline_data['Cumulative_Outcomes'].iloc[-1]
                st.metric("Total Outcomes", int(total_outcomes))
            
            with col3:
                best_day = timeline_data['Success_Rate_Pct'].max()
                st.metric("Best Day", f"{best_day:.1f}%")
            
            with col4:
                trend = "📈" if timeline_data['Success_Rate_Pct'].iloc[-1] > timeline_data['Success_Rate_Pct'].iloc[0] else "📉"
                st.metric("Trend", trend)
        
    else:
        st.info(f"""
        📊 **Performance timeline data will appear here once outcomes accumulate**
        
        **What you'll see:**
        - 📈 **Blue line**: Daily/weekly success rate percentage  
        - 📊 **Green line**: Cumulative number of trading outcomes
        - 🎛️ **Time scale**: Switch between daily, weekly, and monthly views
        
        **Current status:** System rebuilding - collecting data for future analysis
        """)

def render_marketaux_sentiment_comparison():
    """
    Render sentiment comparison: Reddit vs MarketAux vs Combined
    """
    st.subheader("🔄 Sentiment Analysis Comparison: Before vs After MarketAux")
    st.markdown("**Compare broken Reddit sentiment with professional MarketAux news sentiment**")
    
    try:
        # Get comparison data
        comparison_df = fetch_marketaux_sentiment_comparison()
        
        if comparison_df.empty:
            st.warning("MarketAux data not available. Please check API configuration.")
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            reddit_signals = len(comparison_df[comparison_df['Reddit Sentiment'] != 0])
            st.metric(
                "Reddit Working Signals",
                f"{reddit_signals}/{len(comparison_df)}",
                f"{reddit_signals/len(comparison_df)*100:.0f}%"
            )
        
        with col2:
            marketaux_signals = len(comparison_df[comparison_df['MarketAux Sentiment'] != 0])
            st.metric(
                "MarketAux Active Signals", 
                f"{marketaux_signals}/{len(comparison_df)}",
                f"{marketaux_signals/len(comparison_df)*100:.0f}%"
            )
        
        with col3:
            strong_signals = len(comparison_df[comparison_df['Signal Strength'] == 'Strong'])
            st.metric(
                "Strong Trading Signals",
                strong_signals,
                f"From MarketAux news"
            )
        
        with col4:
            total_news = comparison_df['News Volume'].sum()
            st.metric(
                "News Articles Analyzed",
                int(total_news),
                "Professional sources"
            )
        
        # Comparison visualization
        st.markdown("### 📈 Sentiment Score Comparison")
        
        # Create comparison chart
        fig = go.Figure()
        
        # Add Reddit sentiment (broken system)
        fig.add_trace(go.Bar(
            name='Reddit Sentiment (Broken)',
            x=comparison_df['Symbol'],
            y=comparison_df['Reddit Sentiment'],
            marker_color='lightcoral',
            opacity=0.7
        ))
        
        # Add MarketAux sentiment
        fig.add_trace(go.Bar(
            name='MarketAux Professional News',
            x=comparison_df['Symbol'],
            y=comparison_df['MarketAux Sentiment'],
            marker_color='lightblue',
            opacity=0.8
        ))
        
        # Add combined sentiment
        fig.add_trace(go.Bar(
            name='Combined Sentiment (70% MarketAux + 30% Reddit)',
            x=comparison_df['Symbol'],
            y=comparison_df['Combined Sentiment'],
            marker_color='green',
            opacity=0.9
        ))
        
        fig.update_layout(
            title='Sentiment Score Comparison: Reddit vs MarketAux vs Combined',
            xaxis_title='Bank Symbol',
            yaxis_title='Sentiment Score',
            barmode='group',
            height=400,
            yaxis=dict(range=[-1, 1]),
            hovermode='x unified'
        )
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed comparison table
        st.markdown("### 📋 Detailed Sentiment Analysis")
        
        # Format the data for display
        display_df = comparison_df.copy()
        display_df['Reddit Sentiment'] = display_df['Reddit Sentiment'].apply(lambda x: f"{x:.3f}")
        display_df['MarketAux Sentiment'] = display_df['MarketAux Sentiment'].apply(lambda x: f"{x:.3f}")
        display_df['Combined Sentiment'] = display_df['Combined Sentiment'].apply(lambda x: f"{x:.3f}")
        display_df['Sentiment Change'] = display_df['Sentiment Change'].apply(lambda x: f"{x:+.3f}")
        display_df['MarketAux Confidence'] = display_df['MarketAux Confidence'].apply(lambda x: f"{x:.2f}")
        
        # Add signal indicators
        def get_signal_indicator(signal):
            return {'BUY': '🟢 BUY', 'SELL': '🔴 SELL', 'HOLD': '🟡 HOLD'}[signal]
        
        display_df['Trading Signal'] = display_df['Trading Signal'].apply(get_signal_indicator)
        
        # Select columns for display
        display_columns = [
            'Symbol', 'Reddit Sentiment', 'MarketAux Sentiment', 'Combined Sentiment',
            'Sentiment Change', 'Trading Signal', 'Signal Strength', 'News Volume', 'Key News'
        ]
        
        st.dataframe(
            display_df[display_columns],
            use_container_width=True,
            hide_index=True
        )
        
        # Impact analysis
        st.markdown("### 💡 Impact Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔴 BEFORE (Reddit Only):**")
            reddit_working = len(comparison_df[comparison_df['Reddit Sentiment'] != 0])
            reddit_strength = comparison_df['Reddit Sentiment'].abs().sum()
            st.write(f"• Working signals: {reddit_working}/{len(comparison_df)} stocks")
            st.write(f"• Total signal strength: {reddit_strength:.3f}")
            st.write(f"• Data quality: Social media noise")
            st.write(f"• Reliability: System broken (mostly 0.0 values)")
            st.write(f"• Update frequency: Irregular/broken")
        
        with col2:
            st.markdown("**🟢 AFTER (With MarketAux):**")
            marketaux_working = len(comparison_df[comparison_df['MarketAux Sentiment'] != 0])
            marketaux_strength = comparison_df['MarketAux Sentiment'].abs().sum()
            combined_strength = comparison_df['Combined Sentiment'].abs().sum()
            st.write(f"• Active signals: {marketaux_working}/{len(comparison_df)} stocks")
            st.write(f"• MarketAux signal strength: {marketaux_strength:.3f}")
            st.write(f"• Combined signal strength: {combined_strength:.3f}")
            st.write(f"• Data quality: Professional financial news")
            st.write(f"• Reliability: High (professional sources)")
            st.write(f"• Update frequency: Real-time market hours")
        
        # Trading recommendations
        st.markdown("### 🎯 Trading Recommendations Based on Combined Sentiment")
        
        bullish_stocks = comparison_df[comparison_df['Combined Sentiment'] > 0.1]
        bearish_stocks = comparison_df[comparison_df['Combined Sentiment'] < -0.1]
        neutral_stocks = comparison_df[
            (comparison_df['Combined Sentiment'] >= -0.1) & 
            (comparison_df['Combined Sentiment'] <= 0.1)
        ]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🟢 BULLISH SIGNALS**")
            if not bullish_stocks.empty:
                for _, stock in bullish_stocks.iterrows():
                    st.write(f"• **{stock['Symbol']}**: {stock['Combined Sentiment']:.3f}")
                    st.write(f"  News: {stock['News Volume']} articles")
            else:
                st.write("No bullish signals detected")
        
        with col2:
            st.markdown("**🔴 BEARISH SIGNALS**")
            if not bearish_stocks.empty:
                for _, stock in bearish_stocks.iterrows():
                    st.write(f"• **{stock['Symbol']}**: {stock['Combined Sentiment']:.3f}")
                    st.write(f"  News: {stock['News Volume']} articles")
            else:
                st.write("No bearish signals detected")
        
        with col3:
            st.markdown("**🟡 NEUTRAL/HOLD**")
            if not neutral_stocks.empty:
                for _, stock in neutral_stocks.iterrows():
                    st.write(f"• **{stock['Symbol']}**: {stock['Combined Sentiment']:.3f}")
            else:
                st.write("No neutral signals")
        
    except Exception as e:
        st.error(f"Error rendering sentiment comparison: {e}")
        st.info("MarketAux integration may not be properly configured.")

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
            ml_features = feature_analysis['ml_features']
            
            # Feature version and overview
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Feature Version", ml_features['feature_version'])
            with col2:
                st.metric("Total Features", ml_features['total_features'])
            with col3:
                st.metric("Categories", len(ml_features['feature_categories']))
            
            # Feature categories breakdown
            st.subheader("📊 Feature Categories")
            for category, features in ml_features['feature_categories'].items():
                with st.expander(f"{category} ({len(features)} features)"):
                    # Display features in columns for better readability
                    cols = st.columns(3)
                    for i, feature in enumerate(features):
                        cols[i % 3].write(f"• {feature}")
            
            # Usage statistics
            st.subheader("📈 Feature Usage Statistics")
            usage_stats = ml_features['usage_stats']
            
            usage_df = pd.DataFrame([
                {"Feature Type": "News Analysis", "Usage Rate": usage_stats['news_analysis']},
                {"Feature Type": "Reddit Sentiment", "Usage Rate": usage_stats['reddit_sentiment']},
                {"Feature Type": "Event Scoring", "Usage Rate": usage_stats['event_scoring']},
                {"Feature Type": "Technical Indicators", "Usage Rate": usage_stats['technical_indicators']}
            ])
            
            fig_usage = px.bar(
                usage_df,
                x='Feature Type',
                y='Usage Rate',
                title="Feature Usage Rates (%)",
                color='Usage Rate',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig_usage, use_container_width=True)

def render_prediction_timeline(timeline_df: pd.DataFrame):
    """
    Render prediction performance over time
    """
    st.subheader("⏱️ Prediction Timeline (Last 7 Days)")
    
    # Handle empty data gracefully
    if timeline_df.empty:
        st.info("📊 **No prediction timeline data available yet**")
        st.write("""
        This section will show prediction performance once your system generates more predictions with outcomes.
        
        **What you'll see here once data is available:**
        - ⏱️ Prediction timeline with accuracy tracking
        - 📈 Success rate trends over time  
        - 🎯 Confidence vs performance analysis
        - 📊 Per-symbol prediction statistics
        
        **To generate more data:** Let your system run continuously or execute morning/evening routines.
        """)
        return
    
    # Show data availability info
    latest_prediction = timeline_df['Timestamp'].max()
    oldest_prediction = timeline_df['Timestamp'].min()
    unique_timestamps = timeline_df['Timestamp'].nunique()
    
    if unique_timestamps == 1:
        st.info(f"📅 All {len(timeline_df)} predictions were generated in a batch run on {latest_prediction.strftime('%Y-%m-%d at %H:%M:%S')}")
    else:
        st.info(f"📅 Prediction data available from {oldest_prediction.strftime('%Y-%m-%d %H:%M')} to {latest_prediction.strftime('%Y-%m-%d %H:%M')} ({unique_timestamps} different timestamps)")
    
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
        cursor = conn.execute("SELECT MAX(timestamp) FROM enhanced_features")
        latest_sentiment = cursor.fetchone()[0]
        cursor = conn.execute("SELECT MAX(timestamp) FROM enhanced_outcomes")
        latest_outcome = cursor.fetchone()[0]
        conn.close()
        
        st.sidebar.write("**Data Freshness:**")
        if latest_sentiment:
            st.sidebar.write(f"• Features: {latest_sentiment}")
        if latest_outcome:
            st.sidebar.write(f"• Outcomes: {latest_outcome}")
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
            correlation_data = fetch_portfolio_correlation_data()
        
        # Render dashboard sections
        render_ml_performance_section(ml_metrics)
        st.markdown("---")
        
        render_portfolio_correlation_section(correlation_data)
        st.markdown("---")
        
        # NEW: MarketAux sentiment comparison section
        render_marketaux_sentiment_comparison()
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
