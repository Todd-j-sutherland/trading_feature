#!/usr/bin/env python3
"""
Live Trading Metrics Dashboard
Real-time display of sentiment analysis, technical indicators, ML confidence, and market context
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Page configuration
st.set_page_config(
    page_title="🔴 LIVE Trading Metrics", 
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for live dashboard styling
st.markdown("""
<style>
    .live-header {
        background: linear-gradient(90deg, #ff4757 0%, #ff3838 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    
    .metric-live {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.8rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .sentiment-positive {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
    }
    
    .sentiment-negative {
        background: linear-gradient(135deg, #ff4757 0%, #ff3838 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
    }
    
    .sentiment-neutral {
        background: linear-gradient(135deg, #ffa726 0%, #ffcc02 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
    }
    
    .technical-strong {
        background: linear-gradient(135deg, #2ed573 0%, #7bed9f 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
    }
    
    .technical-weak {
        background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
    }
    
    .ml-confidence-high {
        background: linear-gradient(135deg, #5352ed 0%, #3742fa 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
    }
    
    .ml-confidence-low {
        background: linear-gradient(135deg, #a4b0be 0%, #747d8c 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

class LiveTradingMetricsDashboard:
    """Live trading metrics dashboard with real-time data"""
    
    def __init__(self, db_path="data/trading_predictions.db"):
        # Check if we're on the remote server with the correct path
        if os.path.exists('/root/test/predictions.db'):
            self.db_path = '/root/test/predictions.db'
        elif os.path.exists('/root/test/data/trading_predictions.db'):
            self.db_path = '/root/test/data/trading_predictions.db'
        else:
            # Fallback to provided path
            self.db_path = db_path
        
    def get_database_connection(self):
        """Get database connection"""
        try:
            return sqlite3.connect(self.db_path)
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None
    
    def get_live_market_context(self):
        """Get current market context and sentiment"""
        conn = self.get_database_connection()
        if not conn:
            return {}
        
        try:
            # Get latest market-aware predictions for context
            market_context_query = """
            SELECT market_context, market_trend_pct, buy_threshold_used, timestamp
            FROM market_aware_predictions 
            ORDER BY timestamp DESC 
            LIMIT 1
            """
            
            context_data = pd.read_sql_query(market_context_query, conn)
            
            if not context_data.empty:
                return {
                    'market_context': context_data.iloc[0]['market_context'],
                    'market_trend_pct': context_data.iloc[0]['market_trend_pct'],
                    'buy_threshold': context_data.iloc[0]['buy_threshold_used'],
                    'last_update': context_data.iloc[0]['timestamp']
                }
            else:
                return {
                    'market_context': 'UNKNOWN',
                    'market_trend_pct': 0,
                    'buy_threshold': 0.65,
                    'last_update': 'No data'
                }
                
        except Exception as e:
            st.error(f"Error getting market context: {e}")
            return {}
        finally:
            conn.close()
    
    def get_live_sentiment_metrics(self):
        """Get current sentiment analysis metrics"""
        conn = self.get_database_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            sentiment_query = """
            SELECT 
                symbol,
                sentiment_score,
                confidence,
                news_count,
                reddit_sentiment,
                event_score,
                sentiment_momentum,
                sentiment_rsi,
                timestamp
            FROM enhanced_features 
            WHERE timestamp >= datetime('now', '-2 hours')
            ORDER BY timestamp DESC
            """
            
            return pd.read_sql_query(sentiment_query, conn)
            
        except Exception as e:
            st.error(f"Error getting sentiment metrics: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_live_technical_metrics(self):
        """Get current technical analysis metrics"""
        conn = self.get_database_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            technical_query = """
            SELECT 
                symbol,
                rsi,
                macd_line,
                macd_signal,
                macd_histogram,
                sma_20,
                sma_50,
                sma_200,
                bollinger_upper,
                bollinger_lower,
                current_price,
                price_change_1d,
                atr_14,
                volume_ratio,
                timestamp
            FROM enhanced_features 
            WHERE timestamp >= datetime('now', '-2 hours')
            ORDER BY timestamp DESC
            """
            
            return pd.read_sql_query(technical_query, conn)
            
        except Exception as e:
            st.error(f"Error getting technical metrics: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_live_ml_confidence_metrics(self):
        """Get current ML model confidence and predictions"""
        conn = self.get_database_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            ml_query = """
            SELECT 
                symbol,
                predicted_action,
                action_confidence,
                prediction_timestamp,
                entry_price
            FROM predictions 
            WHERE prediction_timestamp >= datetime('now', '-4 hours')
            ORDER BY prediction_timestamp DESC
            """
            
            return pd.read_sql_query(ml_query, conn)
            
        except Exception as e:
            st.error(f"Error getting ML metrics: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_market_aware_predictions(self):
        """Get latest market-aware predictions with full context"""
        conn = self.get_database_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            market_predictions_query = """
            SELECT 
                symbol,
                current_price,
                predicted_price,
                price_change_pct,
                confidence,
                market_context,
                market_trend_pct,
                recommended_action,
                tech_score,
                news_sentiment,
                timestamp
            FROM market_aware_predictions 
            ORDER BY timestamp DESC
            LIMIT 20
            """
            
            return pd.read_sql_query(market_predictions_query, conn)
            
        except Exception as e:
            st.error(f"Error getting market-aware predictions: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def render_live_header(self):
        """Render live dashboard header"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S AEST')
        
        st.markdown(f'''
        <div class="live-header">
            <h1>🔴 LIVE TRADING METRICS DASHBOARD</h1>
            <h3>Real-time Market Analysis & Sentiment Tracking</h3>
            <p>Last Updated: {current_time}</p>
        </div>
        ''', unsafe_allow_html=True)
    
    def render_market_context_overview(self):
        """Render market context overview"""
        st.subheader("🌐 Live Market Context")
        
        market_context = self.get_live_market_context()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            context = market_context.get('market_context', 'UNKNOWN')
            if context == 'BULLISH':
                st.markdown('<div class="sentiment-positive">📈 BULLISH MARKET</div>', unsafe_allow_html=True)
            elif context == 'BEARISH':
                st.markdown('<div class="sentiment-negative">📉 BEARISH MARKET</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="sentiment-neutral">📊 NEUTRAL MARKET</div>', unsafe_allow_html=True)
        
        with col2:
            trend = market_context.get('market_trend_pct', 0)
            st.metric(
                "Market Trend (5-day)",
                f"{trend:+.2f}%",
                delta=f"{trend:+.2f}%" if trend != 0 else None
            )
        
        with col3:
            threshold = market_context.get('buy_threshold', 0.65)
            st.metric(
                "Current BUY Threshold",
                f"{threshold:.1%}",
                help="ML confidence required for BUY signals"
            )
        
        with col4:
            last_update = market_context.get('last_update', 'Unknown')
            if isinstance(last_update, str) and last_update != 'Unknown' and last_update != 'No data':
                try:
                    update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    time_ago = datetime.now() - update_time.replace(tzinfo=None)
                    minutes_ago = int(time_ago.total_seconds() / 60)
                    st.metric("Context Age", f"{minutes_ago}m ago")
                except:
                    st.metric("Context Age", "Unknown")
            else:
                st.metric("Context Age", "No data")
    
    def render_sentiment_analysis_live(self):
        """Render live sentiment analysis"""
        st.subheader("📰 Live News Sentiment Analysis")
        
        sentiment_data = self.get_live_sentiment_metrics()
        
        if sentiment_data.empty:
            st.warning("No recent sentiment data available")
            return
        
        # Get latest sentiment for each symbol
        latest_sentiment = sentiment_data.groupby('symbol').first().reset_index()
        
        if latest_sentiment.empty:
            st.warning("No sentiment data to display")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment scores chart
            if len(latest_sentiment) > 0:
                fig = px.bar(
                    latest_sentiment.head(10),
                    x='symbol',
                    y='sentiment_score',
                    color='sentiment_score',
                    color_continuous_scale='RdYlGn',
                    title="Current Sentiment Scores by Symbol"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sentiment data for chart")
        
        with col2:
            # Sentiment confidence vs news count (simplified to avoid size issues)
            if len(latest_sentiment) > 0:
                fig = px.scatter(
                    latest_sentiment.head(10),
                    x='news_count',
                    y='confidence',
                    color='sentiment_score',
                    hover_data=['symbol', 'sentiment_score'],
                    title="Sentiment Confidence vs News Volume"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sentiment data for scatter plot")
        
        # Sentiment summary table
        if len(latest_sentiment) > 0:
            st.write("**Live Sentiment Summary:**")
            display_sentiment = latest_sentiment[['symbol', 'sentiment_score', 'confidence', 'news_count']].head(10)
            display_sentiment['sentiment_score'] = display_sentiment['sentiment_score'].apply(lambda x: f"{x:.3f}")
            display_sentiment['confidence'] = display_sentiment['confidence'].apply(lambda x: f"{x:.1%}")
            
            st.dataframe(display_sentiment, use_container_width=True)
        else:
            st.info("No sentiment summary data available")
    
    def render_technical_analysis_live(self):
        """Render live technical analysis"""
        st.subheader("📊 Live Technical Analysis")
        
        technical_data = self.get_live_technical_metrics()
        
        if technical_data.empty:
            st.warning("No recent technical data available")
            return
        
        # Get latest technical data for each symbol
        latest_technical = technical_data.groupby('symbol').first().reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # RSI levels
            fig = px.bar(
                latest_technical.head(10),
                x='symbol',
                y='rsi',
                color='rsi',
                color_continuous_scale='RdYlGn',
                title="Current RSI Levels"
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
            fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Price vs Moving Averages
            symbols_to_plot = latest_technical.head(5)
            fig = go.Figure()
            
            for _, row in symbols_to_plot.iterrows():
                fig.add_trace(go.Scatter(
                    x=[row['symbol']],
                    y=[row['current_price']],
                    mode='markers',
                    marker=dict(size=12, color='blue'),
                    name=f"{row['symbol']} Current",
                    showlegend=False
                ))
                
                fig.add_trace(go.Scatter(
                    x=[row['symbol']],
                    y=[row['sma_20']],
                    mode='markers',
                    marker=dict(size=8, color='orange', symbol='diamond'),
                    name="SMA-20",
                    showlegend=False
                ))
            
            fig.update_layout(
                title="Current Price vs SMA-20",
                height=400,
                yaxis_title="Price ($)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Technical indicators table
        st.write("**Live Technical Indicators:**")
        display_technical = latest_technical[['symbol', 'rsi', 'current_price', 'price_change_1d', 'volume_ratio']].head(10)
        display_technical['rsi'] = display_technical['rsi'].apply(lambda x: f"{x:.1f}")
        display_technical['current_price'] = display_technical['current_price'].apply(lambda x: f"${x:.2f}")
        display_technical['price_change_1d'] = display_technical['price_change_1d'].apply(lambda x: f"{x:+.2f}%")
        display_technical['volume_ratio'] = display_technical['volume_ratio'].apply(lambda x: f"{x:.1f}x")
        
        st.dataframe(display_technical, use_container_width=True)
    
    def render_ml_confidence_live(self):
        """Render live ML confidence and predictions"""
        st.subheader("🤖 Live ML Confidence & Predictions")
        
        ml_data = self.get_live_ml_confidence_metrics()
        
        if ml_data.empty:
            st.warning("No recent ML predictions available")
            return
        
        # Get latest predictions for each symbol
        latest_ml = ml_data.groupby('symbol').first().reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # ML confidence levels
            fig = px.bar(
                latest_ml.head(10),
                x='symbol',
                y='action_confidence',
                color='predicted_action',
                title="Current ML Confidence by Action"
            )
            fig.add_hline(y=0.65, line_dash="dash", line_color="orange", annotation_text="Minimum Threshold")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Action distribution
            action_counts = latest_ml['predicted_action'].value_counts()
            fig = px.pie(
                values=action_counts.values,
                names=action_counts.index,
                title="Current Prediction Distribution"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # ML predictions table
        st.write("**Live ML Predictions:**")
        display_ml = latest_ml[['symbol', 'predicted_action', 'action_confidence', 'entry_price']].head(10)
        display_ml['action_confidence'] = display_ml['action_confidence'].apply(lambda x: f"{x:.1%}")
        display_ml['entry_price'] = display_ml['entry_price'].apply(lambda x: f"${x:.2f}")
        
        # Color code by confidence level
        def confidence_color(row):
            conf = float(row['action_confidence'].strip('%')) / 100
            if conf >= 0.8:
                return ['background-color: #d4edda'] * len(row)  # High confidence
            elif conf >= 0.65:
                return ['background-color: #fff3cd'] * len(row)  # Medium confidence
            else:
                return ['background-color: #f8d7da'] * len(row)  # Low confidence
        
        styled_ml = display_ml.style.apply(confidence_color, axis=1)
        st.dataframe(styled_ml, use_container_width=True)
    
    def render_market_aware_signals(self):
        """Render market-aware trading signals"""
        st.subheader("🎯 Market-Aware Trading Signals")
        
        market_predictions = self.get_market_aware_predictions()
        
        if market_predictions.empty:
            st.warning("No market-aware predictions available")
            return
        
        # Action summary
        col1, col2, col3, col4 = st.columns(4)
        
        action_counts = market_predictions['recommended_action'].value_counts()
        
        with col1:
            strong_buy = action_counts.get('STRONG_BUY', 0)
            st.metric("🚀 STRONG BUY", strong_buy)
        
        with col2:
            buy = action_counts.get('BUY', 0)
            st.metric("📈 BUY", buy)
        
        with col3:
            hold = action_counts.get('HOLD', 0)
            st.metric("⏸️ HOLD", hold)
        
        with col4:
            sell = action_counts.get('SELL', 0)
            st.metric("📉 SELL", sell)
        
        # Detailed predictions table
        st.write("**Market-Aware Prediction Details:**")
        
        if not market_predictions.empty:
            display_predictions = market_predictions[[
                'symbol', 'recommended_action', 'confidence', 'price_change_pct', 
                'tech_score', 'news_sentiment', 'market_context'
            ]].head(10)
            
            display_predictions['confidence'] = display_predictions['confidence'].apply(lambda x: f"{x:.1%}")
            display_predictions['price_change_pct'] = display_predictions['price_change_pct'].apply(lambda x: f"{x:+.2f}%")
            display_predictions['tech_score'] = display_predictions['tech_score'].apply(lambda x: f"{x:.0f}")
            display_predictions['news_sentiment'] = display_predictions['news_sentiment'].apply(lambda x: f"{x:+.3f}")
            
            # Color code by action
            def action_color(row):
                action = row['recommended_action']
                if action == 'STRONG_BUY':
                    return ['background-color: #d4edda; color: #155724'] * len(row)
                elif action == 'BUY':
                    return ['background-color: #cce7ff; color: #004085'] * len(row)
                elif action == 'SELL':
                    return ['background-color: #f8d7da; color: #721c24'] * len(row)
                else:
                    return ['background-color: #fff3cd; color: #856404'] * len(row)
            
            styled_predictions = display_predictions.style.apply(action_color, axis=1)
            st.dataframe(styled_predictions, use_container_width=True)
    
    def run_dashboard(self):
        """Main dashboard execution"""
        
        # Header
        self.render_live_header()
        
        # Auto-refresh controls
        st.sidebar.title("🔴 Live Controls")
        auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
        refresh_rate = st.sidebar.selectbox("Refresh Rate", [15, 30, 60], index=1)
        
        if auto_refresh:
            time.sleep(refresh_rate)
            st.rerun()
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Now", type="primary"):
            st.rerun()
        
        # Dashboard sections
        show_market_context = st.sidebar.checkbox("Market Context", value=True)
        show_sentiment = st.sidebar.checkbox("Sentiment Analysis", value=True)
        show_technical = st.sidebar.checkbox("Technical Analysis", value=True)
        show_ml_confidence = st.sidebar.checkbox("ML Confidence", value=True)
        show_market_signals = st.sidebar.checkbox("Market-Aware Signals", value=True)
        
        # Render sections
        if show_market_context:
            self.render_market_context_overview()
            st.divider()
        
        if show_sentiment:
            self.render_sentiment_analysis_live()
            st.divider()
        
        if show_technical:
            self.render_technical_analysis_live()
            st.divider()
        
        if show_ml_confidence:
            self.render_ml_confidence_live()
            st.divider()
        
        if show_market_signals:
            self.render_market_aware_signals()
        
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.caption(f"🔴 Live Dashboard - {datetime.now().strftime('%H:%M:%S')}")
        st.sidebar.caption("📊 Real-time Trading Metrics v1.0")

# Main execution
if __name__ == "__main__":
    dashboard = LiveTradingMetricsDashboard()
    dashboard.run_dashboard()
