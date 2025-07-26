#!/usr/bin/env python3
"""
Enhanced Multi-Bank Performance Dashboard

Interactive web dashboard showcasing real-time performance of Australian bank symbols
with ML predictions, sentiment analysis, and comprehensive analytics.

Features:
- Real-time price performance
- Sentiment analysis visualization  
- ML prediction tracking
- Sector comparison
- Historical trends
- Interactive charts
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Dashboard configuration
st.set_page_config(
    page_title="Australian Banks ML Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

class BankPerformanceDashboard:
    """Interactive dashboard for bank performance analysis"""
    
    def __init__(self):
        self.db_path = 'data/multi_bank_analysis.db'
        self.load_custom_css()
        
    def load_custom_css(self):
        """Load custom CSS styling"""
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .positive { color: #00C851; font-weight: bold; }
        .negative { color: #ff4444; font-weight: bold; }
        .neutral { color: #ffbb33; font-weight: bold; }
        .bank-name { font-weight: bold; color: #1f77b4; }
        </style>
        """, unsafe_allow_html=True)
    
    def load_data(self):
        """Load data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load main performance data
                performance_df = pd.read_sql_query('''
                    SELECT * FROM bank_performance 
                    ORDER BY timestamp DESC
                ''', conn)
                
                # Load sentiment data
                sentiment_df = pd.read_sql_query('''
                    SELECT * FROM news_sentiment_analysis
                    ORDER BY timestamp DESC
                ''', conn)
                
                return performance_df, sentiment_df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def display_header(self):
        """Display dashboard header"""
        st.markdown('<h1 class="main-header">🏦 Australian Banks ML Performance Dashboard</h1>', 
                   unsafe_allow_html=True)
        st.markdown("---")
    
    def display_overview_metrics(self, df):
        """Display overview metrics"""
        if df.empty:
            st.warning("No data available")
            return
        
        # Get latest data for each bank
        latest_data = df.groupby('symbol').first().reset_index()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Banks Analyzed",
                len(latest_data),
                delta=None
            )
        
        with col2:
            avg_change = latest_data['price_change_1d'].mean()
            st.metric(
                "Avg 1D Change",
                f"{avg_change:.2f}%",
                delta=f"{avg_change:.2f}%"
            )
        
        with col3:
            avg_sentiment = latest_data['sentiment_score'].mean()
            st.metric(
                "Avg Sentiment",
                f"{avg_sentiment:.3f}",
                delta=f"{avg_sentiment:.3f}"
            )
        
        with col4:
            buy_signals = len(latest_data[latest_data['optimal_action'].isin(['BUY', 'STRONG_BUY'])])
            st.metric(
                "Buy Signals",
                buy_signals,
                delta=f"{buy_signals}/{len(latest_data)}"
            )
    
    def display_top_performers(self, df):
        """Display top and bottom performers"""
        if df.empty:
            return
        
        latest_data = df.groupby('symbol').first().reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top Performers (1D)")
            top_performers = latest_data.nlargest(5, 'price_change_1d')
            
            for _, bank in top_performers.iterrows():
                change_class = "positive" if bank['price_change_1d'] > 0 else "negative"
                st.markdown(f"""
                <div class="metric-card">
                    <span class="bank-name">{bank['symbol']}</span> - {bank['bank_name']}<br>
                    <span class="{change_class}">{bank['price_change_1d']:+.2f}%</span> | 
                    ${bank['current_price']:.2f} | 
                    Action: {bank['optimal_action']}
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("📉 Bottom Performers (1D)")
            bottom_performers = latest_data.nsmallest(5, 'price_change_1d')
            
            for _, bank in bottom_performers.iterrows():
                change_class = "positive" if bank['price_change_1d'] > 0 else "negative"
                st.markdown(f"""
                <div class="metric-card">
                    <span class="bank-name">{bank['symbol']}</span> - {bank['bank_name']}<br>
                    <span class="{change_class}">{bank['price_change_1d']:+.2f}%</span> | 
                    ${bank['current_price']:.2f} | 
                    Action: {bank['optimal_action']}
                </div>
                """, unsafe_allow_html=True)
    
    def plot_price_performance(self, df):
        """Plot price performance chart"""
        if df.empty:
            return
        
        latest_data = df.groupby('symbol').first().reset_index()
        
        # Create price performance chart
        fig = px.bar(
            latest_data.sort_values('price_change_1d', ascending=True),
            x='price_change_1d',
            y='symbol',
            color='price_change_1d',
            color_continuous_scale=['red', 'yellow', 'green'],
            title="1-Day Price Performance by Bank",
            labels={'price_change_1d': '1-Day Price Change (%)', 'symbol': 'Bank Symbol'},
            text='price_change_1d'
        )
        
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def plot_sentiment_analysis(self, df):
        """Plot sentiment analysis"""
        if df.empty:
            return
        
        latest_data = df.groupby('symbol').first().reset_index()
        
        # Sentiment vs Price Performance scatter plot
        fig = px.scatter(
            latest_data,
            x='sentiment_score',
            y='price_change_1d',
            size='sentiment_confidence',
            color='sector',
            hover_data=['bank_name', 'optimal_action'],
            title="Sentiment vs Price Performance",
            labels={
                'sentiment_score': 'Sentiment Score',
                'price_change_1d': '1-Day Price Change (%)'
            }
        )
        
        # Add correlation trend line
        fig.add_shape(
            type="line",
            x0=latest_data['sentiment_score'].min(),
            y0=0,
            x1=latest_data['sentiment_score'].max(),
            y1=0,
            line=dict(color="gray", width=1, dash="dash")
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    def plot_sector_comparison(self, df):
        """Plot sector performance comparison"""
        if df.empty:
            return
        
        latest_data = df.groupby('symbol').first().reset_index()
        sector_performance = latest_data.groupby('sector').agg({
            'price_change_1d': 'mean',
            'sentiment_score': 'mean',
            'symbol': 'count'
        }).round(2)
        sector_performance.columns = ['Avg_Price_Change', 'Avg_Sentiment', 'Bank_Count']
        sector_performance = sector_performance.reset_index()
        
        # Create subplot
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Sector Price Performance', 'Sector Sentiment'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Price performance by sector
        fig.add_trace(
            go.Bar(
                x=sector_performance['sector'],
                y=sector_performance['Avg_Price_Change'],
                name='Avg Price Change (%)',
                marker_color='lightblue'
            ),
            row=1, col=1
        )
        
        # Sentiment by sector
        fig.add_trace(
            go.Bar(
                x=sector_performance['sector'],
                y=sector_performance['Avg_Sentiment'],
                name='Avg Sentiment',
                marker_color='lightgreen'
            ),
            row=1, col=2
        )
        
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    def plot_ml_predictions(self, df):
        """Plot ML prediction distribution"""
        if df.empty:
            return
        
        latest_data = df.groupby('symbol').first().reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Action distribution pie chart
            action_counts = latest_data['optimal_action'].value_counts()
            fig_pie = px.pie(
                values=action_counts.values,
                names=action_counts.index,
                title="ML Action Distribution",
                color_discrete_map={
                    'STRONG_BUY': '#00C851',
                    'BUY': '#4CAF50', 
                    'HOLD': '#ffbb33',
                    'SELL': '#ff4444',
                    'STRONG_SELL': '#CC0000'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Prediction confidence distribution
            fig_hist = px.histogram(
                latest_data,
                x='prediction_confidence',
                nbins=10,
                title="ML Prediction Confidence Distribution",
                labels={'prediction_confidence': 'Prediction Confidence'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
    
    def display_detailed_table(self, df):
        """Display detailed data table"""
        if df.empty:
            return
        
        latest_data = df.groupby('symbol').first().reset_index()
        
        # Select and format columns for display
        display_columns = [
            'symbol', 'bank_name', 'sector', 'current_price', 
            'price_change_1d', 'price_change_5d', 'sentiment_score',
            'rsi', 'optimal_action', 'prediction_confidence'
        ]
        
        display_data = latest_data[display_columns].copy()
        
        # Format numeric columns
        display_data['current_price'] = display_data['current_price'].round(2)
        display_data['price_change_1d'] = display_data['price_change_1d'].round(2)
        display_data['price_change_5d'] = display_data['price_change_5d'].round(2)
        display_data['sentiment_score'] = display_data['sentiment_score'].round(3)
        display_data['rsi'] = display_data['rsi'].round(1)
        display_data['prediction_confidence'] = display_data['prediction_confidence'].round(3)
        
        st.subheader("📊 Detailed Bank Analysis")
        
        # Color code the dataframe
        def color_code_row(row):
            colors = []
            for col in row.index:
                if col == 'price_change_1d' or col == 'price_change_5d':
                    if row[col] > 0:
                        colors.append('background-color: #d4edda')  # Green
                    elif row[col] < 0:
                        colors.append('background-color: #f8d7da')  # Red
                    else:
                        colors.append('')
                elif col == 'optimal_action':
                    if row[col] in ['BUY', 'STRONG_BUY']:
                        colors.append('background-color: #d4edda')  # Green
                    elif row[col] in ['SELL', 'STRONG_SELL']:
                        colors.append('background-color: #f8d7da')  # Red
                    else:
                        colors.append('background-color: #fff3cd')  # Yellow
                else:
                    colors.append('')
            return colors
        
        styled_df = display_data.style.apply(color_code_row, axis=1)
        st.dataframe(styled_df, use_container_width=True)
    
    def display_sentiment_news(self, sentiment_df):
        """Display recent sentiment news"""
        if sentiment_df.empty:
            return
        
        st.subheader("📰 Recent Sentiment Analysis")
        
        # Get recent headlines
        recent_news = sentiment_df.head(20)
        
        for _, news in recent_news.iterrows():
            sentiment_class = "positive" if news['sentiment_score'] > 0.1 else "negative" if news['sentiment_score'] < -0.1 else "neutral"
            
            st.markdown(f"""
            <div class="metric-card">
                <strong class="bank-name">{news['symbol']}</strong> | 
                <span class="{sentiment_class}">Sentiment: {news['sentiment_score']:.3f}</span> | 
                Confidence: {news['confidence']:.3f}<br>
                <em>"{news['headline']}"</em><br>
                <small>Category: {news['category']} | {news['timestamp']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    def run_dashboard(self):
        """Run the main dashboard"""
        self.display_header()
        
        # Load data
        performance_df, sentiment_df = self.load_data()
        
        if performance_df.empty:
            st.error("No data available. Please run the data collector first.")
            st.code("python enhanced_ml_system/multi_bank_data_collector.py")
            return
        
        # Sidebar filters
        st.sidebar.header("🔧 Dashboard Controls")
        
        # Refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.rerun()
        
        # Date filter
        if not performance_df.empty:
            min_date = pd.to_datetime(performance_df['timestamp']).min().date()
            max_date = pd.to_datetime(performance_df['timestamp']).max().date()
            
            selected_date = st.sidebar.date_input(
                "Select Analysis Date",
                value=max_date,
                min_value=min_date,
                max_value=max_date
            )
        
        # Symbol filter
        available_symbols = performance_df['symbol'].unique() if not performance_df.empty else []
        selected_symbols = st.sidebar.multiselect(
            "Filter Banks",
            available_symbols,
            default=available_symbols
        )
        
        # Filter data
        if selected_symbols:
            performance_df = performance_df[performance_df['symbol'].isin(selected_symbols)]
            sentiment_df = sentiment_df[sentiment_df['symbol'].isin(selected_symbols)]
        
        # Main dashboard content
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Performance", "💭 Sentiment", "🤖 ML Predictions"])
        
        with tab1:
            st.subheader("📊 Market Overview")
            self.display_overview_metrics(performance_df)
            st.markdown("---")
            self.display_top_performers(performance_df)
        
        with tab2:
            st.subheader("📈 Price Performance Analysis")
            self.plot_price_performance(performance_df)
            st.markdown("---")
            self.plot_sector_comparison(performance_df)
        
        with tab3:
            st.subheader("💭 Sentiment Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                self.plot_sentiment_analysis(performance_df)
            
            with col2:
                st.subheader("📰 Recent Headlines")
                if not sentiment_df.empty:
                    recent_headlines = sentiment_df.groupby('symbol').first().reset_index()
                    for _, news in recent_headlines.head(10).iterrows():
                        sentiment_emoji = "😊" if news['sentiment_score'] > 0.1 else "😟" if news['sentiment_score'] < -0.1 else "😐"
                        st.write(f"{sentiment_emoji} **{news['symbol']}**: {news['headline'][:100]}...")
        
        with tab4:
            st.subheader("🤖 Machine Learning Predictions")
            self.plot_ml_predictions(performance_df)
            st.markdown("---")
            self.display_detailed_table(performance_df)
        
        # Footer
        st.markdown("---")
        st.markdown("*Dashboard last updated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*")
        st.markdown("*Data source: Enhanced ML Multi-Bank Analysis System*")

def main():
    """Main function to run the dashboard"""
    dashboard = BankPerformanceDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
