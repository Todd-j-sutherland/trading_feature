#!/usr/bin/env python3
"""
ML Trading Dashboard - Streamlit interface for ML trading scores and analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add app root to path
app_root = Path(__file__).parent.parent
sys.path.append(str(app_root))

class MLTradingDashboard:
    """Streamlit dashboard for ML trading analysis"""
    
    def __init__(self):
        self.setup_page()
    
    def setup_page(self):
        """Setup Streamlit page configuration"""
        st.set_page_config(
            page_title="ML Trading Dashboard",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("🧠 ML Trading Analysis Dashboard")
        st.markdown("---")
    
    def load_ml_analysis_data(self):
        """Load the latest ML analysis data"""
        try:
            analysis_file = Path('data/ml_analysis/latest_analysis.json')
            
            if not analysis_file.exists():
                return None, "No ML analysis data found. Run 'python -m app.main ml-analyze' first."
            
            with open(analysis_file, 'r') as f:
                data = json.load(f)
            
            return data, None
        except Exception as e:
            return None, f"Error loading analysis data: {e}"
    
    def load_trading_history(self):
        """Load trading execution history"""
        try:
            trading_dir = Path('data/ml_trading')
            if not trading_dir.exists():
                return []
            
            history = []
            for file in trading_dir.glob('execution_*.json'):
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        data['filename'] = file.name
                        history.append(data)
                except:
                    continue
            
            # Sort by timestamp
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return history[:10]  # Last 10 executions
        except Exception as e:
            st.error(f"Error loading trading history: {e}")
            return []
    
    def display_ml_scores_section(self, analysis_data):
        """Display ML trading scores in an organized layout"""
        st.header("📊 ML Trading Scores")
        
        ml_scores = analysis_data.get('ml_scores', {})
        if not ml_scores:
            st.warning("No ML scores available in analysis data.")
            return
        
        # Create dataframe for scores
        scores_data = []
        for bank, scores in ml_scores.items():
            scores_data.append({
                'Bank': bank,
                'ML Score': scores.get('overall_score', 0),
                'Sentiment Score': scores.get('sentiment_score', 0),
                'Technical Score': scores.get('technical_score', 0),
                'Volatility Score': scores.get('volatility_score', 0),
                'Trading Signal': scores.get('trading_signal', 'HOLD'),
                'Confidence': scores.get('confidence', 0)
            })
        
        df_scores = pd.DataFrame(scores_data)
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_score = df_scores['ML Score'].mean()
            st.metric("Average ML Score", f"{avg_score:.3f}")
        
        with col2:
            buy_signals = len(df_scores[df_scores['Trading Signal'] == 'BUY'])
            st.metric("Buy Signals", buy_signals)
        
        with col3:
            sell_signals = len(df_scores[df_scores['Trading Signal'] == 'SELL'])
            st.metric("Sell Signals", sell_signals)
        
        with col4:
            high_confidence = len(df_scores[df_scores['Confidence'] > 0.7])
            st.metric("High Confidence", high_confidence)
        
        # ML Scores Table
        st.subheader("Detailed ML Scores")
        
        # Color code the trading signals
        def color_signal(val):
            if val == 'BUY':
                return 'background-color: #90EE90'
            elif val == 'SELL':
                return 'background-color: #FFB6C1'
            else:
                return 'background-color: #F0F8FF'
        
        styled_df = df_scores.style.applymap(color_signal, subset=['Trading Signal'])
        st.dataframe(styled_df, use_container_width=True)
        
        # ML Scores Visualization
        st.subheader("ML Scores Visualization")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart of overall ML scores
            fig_bar = px.bar(
                df_scores, 
                x='Bank', 
                y='ML Score',
                color='Trading Signal',
                title="ML Scores by Bank",
                color_discrete_map={'BUY': 'green', 'SELL': 'red', 'HOLD': 'blue'}
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Scatter plot of sentiment vs technical scores
            fig_scatter = px.scatter(
                df_scores,
                x='Sentiment Score',
                y='Technical Score',
                size='Confidence',
                color='Trading Signal',
                hover_name='Bank',
                title="Sentiment vs Technical Analysis",
                color_discrete_map={'BUY': 'green', 'SELL': 'red', 'HOLD': 'blue'}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
    
    def display_economic_analysis(self, analysis_data):
        """Display economic sentiment analysis"""
        st.header("🌍 Economic Analysis")
        
        economic_data = analysis_data.get('economic_analysis', {})
        if not economic_data:
            st.warning("No economic analysis data available.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            sentiment = economic_data.get('sentiment', 'Unknown')
            regime = economic_data.get('market_regime', 'Unknown')
            
            st.metric("Economic Sentiment", sentiment)
            st.metric("Market Regime", regime)
        
        with col2:
            # Economic indicators
            indicators = economic_data.get('indicators', {})
            if indicators:
                st.subheader("Key Indicators")
                for indicator, value in indicators.items():
                    if isinstance(value, (int, float)):
                        st.metric(indicator.replace('_', ' ').title(), f"{value:.2f}")
                    else:
                        st.text(f"{indicator.replace('_', ' ').title()}: {value}")
    
    def display_divergence_analysis(self, analysis_data):
        """Display sector divergence analysis"""
        st.header("📈 Sector Divergence Analysis")
        
        divergence_data = analysis_data.get('divergence_analysis', {})
        if not divergence_data:
            st.warning("No divergence analysis data available.")
            return
        
        # Divergence metrics
        divergence_score = divergence_data.get('divergence_score', 0)
        trend_strength = divergence_data.get('trend_strength', 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Divergence Score", f"{divergence_score:.3f}")
        
        with col2:
            st.metric("Trend Strength", f"{trend_strength:.3f}")
        
        # Divergence signals
        signals = divergence_data.get('signals', [])
        if signals:
            st.subheader("Divergence Signals")
            for signal in signals:
                st.text(f"• {signal}")
    
    def display_trading_history(self, history):
        """Display recent trading execution history"""
        st.header("📋 Recent Trading History")
        
        if not history:
            st.info("No trading execution history available.")
            return
        
        # Create summary table
        history_data = []
        for execution in history:
            history_data.append({
                'Timestamp': execution.get('timestamp', 'Unknown'),
                'Mode': 'DRY RUN' if execution.get('dry_run', True) else 'LIVE',
                'Orders': len(execution.get('orders_placed', [])),
                'Total Exposure': execution.get('total_exposure', 0),
                'Status': execution.get('status', 'Unknown')
            })
        
        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True)
        
        # Show detailed view for latest execution
        if history:
            st.subheader("Latest Execution Details")
            latest = history[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Exposure", f"${latest.get('total_exposure', 0):,.2f}")
            
            with col2:
                st.metric("Orders Placed", len(latest.get('orders_placed', [])))
            
            with col3:
                mode = 'DRY RUN' if latest.get('dry_run', True) else 'LIVE'
                st.metric("Execution Mode", mode)
            
            # Show orders if any
            orders = latest.get('orders_placed', [])
            if orders:
                st.subheader("Orders Details")
                orders_df = pd.DataFrame(orders)
                st.dataframe(orders_df, use_container_width=True)
    
    def display_system_status(self):
        """Display ML trading system status"""
        st.header("⚙️ System Status")
        
        try:
            from app.core.commands.ml_trading import MLTradingCommand
            
            ml_command = MLTradingCommand()
            status = ml_command.get_ml_trading_status()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                components_status = "✅" if status.get('components_loaded') else "❌"
                st.metric("Components", components_status)
            
            with col2:
                alpaca_status = "✅" if status.get('alpaca_connected') else "❌"
                st.metric("Alpaca", alpaca_status)
            
            with col3:
                ml_status = "✅" if status.get('ml_models_available') else "❌"
                st.metric("ML Models", ml_status)
            
            with col4:
                system_status = "✅" if status.get('system_ready') else "❌"
                st.metric("System Ready", system_status)
            
            # Account information if available
            if status.get('alpaca_connected'):
                st.subheader("Account Information")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    equity = status.get('account_equity', 0)
                    st.metric("Account Equity", f"${equity:,.2f}")
                
                with col2:
                    buying_power = status.get('buying_power', 0)
                    st.metric("Buying Power", f"${buying_power:,.2f}")
                
                with col3:
                    day_trades = status.get('day_trade_count', 0)
                    st.metric("Day Trades", day_trades)
        
        except Exception as e:
            st.error(f"Error getting system status: {e}")
    
    def run_dashboard(self):
        """Run the main dashboard"""
        # Sidebar
        st.sidebar.header("🎛️ Controls")
        
        # Auto-refresh option
        auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
        if auto_refresh:
            st.rerun()
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.rerun()
        
        # Load data
        analysis_data, error = self.load_ml_analysis_data()
        
        if error:
            st.error(error)
            st.info("To generate ML analysis data, run: `python -m app.main ml-analyze`")
            return
        
        # Display timestamp
        timestamp = analysis_data.get('timestamp', 'Unknown')
        st.sidebar.info(f"Last Analysis: {timestamp}")
        
        # Main dashboard sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 ML Scores", 
            "🌍 Economic", 
            "📈 Divergence", 
            "📋 Trading History", 
            "⚙️ System Status"
        ])
        
        with tab1:
            self.display_ml_scores_section(analysis_data)
        
        with tab2:
            self.display_economic_analysis(analysis_data)
        
        with tab3:
            self.display_divergence_analysis(analysis_data)
        
        with tab4:
            trading_history = self.load_trading_history()
            self.display_trading_history(trading_history)
        
        with tab5:
            self.display_system_status()

def main():
    """Main function for Streamlit app"""
    dashboard = MLTradingDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
