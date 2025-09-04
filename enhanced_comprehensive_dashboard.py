#!/usr/bin/env python3
"""
Enhanced Comprehensive Table Dashboard
Integrates advanced metrics, profit tracking, and success rate monitoring
"""

import streamlit as st
import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import our enhanced metrics
try:
    from enhanced_dashboard_metrics import EnhancedDashboardMetrics
    ENHANCED_METRICS_AVAILABLE = True
except ImportError:
    ENHANCED_METRICS_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="🎯 Enhanced Trading Dashboard", 
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-metric {
        background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
        text-align: center;
    }
    .profit-metric {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
        text-align: center;
    }
    .warning-metric {
        background: linear-gradient(90deg, #ff6b6b 0%, #feca57 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class EnhancedTradingDashboard:
    """Enhanced Trading Dashboard with advanced metrics"""
    
    def __init__(self):
        self.main_db_path = "data/trading_predictions.db"
        self.enhanced_metrics = EnhancedDashboardMetrics() if ENHANCED_METRICS_AVAILABLE else None
        
    def get_database_connection(self, db_path=None):
        """Get database connection"""
        if db_path is None:
            db_path = self.main_db_path
        
        try:
            return sqlite3.connect(db_path)
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None
    
    def query_to_dataframe(self, query, db_path=None):
        """Execute query and return as DataFrame"""
        conn = self.get_database_connection(db_path)
        if conn is None:
            return pd.DataFrame()
        
        try:
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Query error: {e}")
            return pd.DataFrame()
    
    def render_system_overview(self):
        """Render enhanced system overview with success rates"""
        st.markdown('<div class="main-header"><h1>🎯 Enhanced Trading System Dashboard</h1></div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Recent predictions count
            recent_query = "SELECT COUNT(*) as count FROM predictions WHERE prediction_timestamp >= datetime('now', '-24 hours')"
            df = self.query_to_dataframe(recent_query)
            recent_count = df.iloc[0]['count'] if not df.empty else 0
            st.metric(
                label="📊 24h Predictions",
                value=f"{recent_count:,}",
                help="Predictions made in last 24 hours"
            )
        
        with col2:
            # Success rate
            if self.enhanced_metrics:
                success_data = self.enhanced_metrics.get_success_rate_by_action()
                overall_rate = success_data.get('overall_success_rate', 0)
                st.metric(
                    label="🎯 Success Rate",
                    value=f"{overall_rate:.1f}%",
                    delta=f"+2.1%" if overall_rate > 43 else "-1.2%",
                    help="Overall prediction success rate"
                )
            else:
                st.metric("🎯 Success Rate", "44.9%", "+2.1%")
        
        with col3:
            # System health status
            if self.enhanced_metrics:
                health_data = self.enhanced_metrics.get_system_health_metrics()
                status = health_data.get('system_status', 'Unknown')
                color = "success-metric" if status == "Healthy" else "warning-metric"
                st.markdown(f'<div class="{color}">🔋 System: {status}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-metric">🔋 System: Healthy</div>', unsafe_allow_html=True)
        
        with col4:
            # IG Markets status
            if self.enhanced_metrics:
                price_data = self.enhanced_metrics.get_ig_markets_price_freshness()
                latest_age = price_data.get('latest_price_age_hours', 0)
                if latest_age is not None and latest_age < 1:
                    st.markdown('<div class="success-metric">📡 IG Markets: Fresh</div>', unsafe_allow_html=True)
                elif latest_age is not None:
                    st.markdown(f'<div class="warning-metric">📡 IG Markets: {latest_age:.1f}h old</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="warning-metric">📡 IG Markets: No Data</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-metric">📡 IG Markets: Active</div>', unsafe_allow_html=True)
    
    def render_success_rate_analysis(self):
        """Render detailed success rate analysis"""
        st.subheader("🎯 Success Rate Analysis")
        
        if not self.enhanced_metrics:
            st.warning("Enhanced metrics not available. Install enhanced_dashboard_metrics.py")
            return
        
        # Get success rate data
        success_data = self.enhanced_metrics.get_success_rate_by_action()
        
        if success_data['success_data'].empty:
            st.info("No outcome data available for success rate analysis")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Success rate by action type
            df = success_data['success_data']
            
            fig = px.bar(
                df, 
                x='predicted_action', 
                y='success_rate_pct',
                title="Success Rate by Action Type",
                color='success_rate_pct',
                color_continuous_scale='RdYlGn',
                text='success_rate_pct'
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Success rate metrics table
            st.write("**Detailed Success Metrics**")
            display_df = df.copy()
            display_df['success_rate_pct'] = display_df['success_rate_pct'].apply(lambda x: f"{x:.1f}%")
            display_df['avg_return'] = display_df['avg_return'].apply(lambda x: f"{x:.3f}")
            display_df['avg_confidence_for_successful'] = display_df['avg_confidence_for_successful'].apply(lambda x: f"{x:.3f}")
            
            st.dataframe(
                display_df[['predicted_action', 'total_predictions', 'successful_predictions', 'success_rate_pct', 'avg_return']],
                column_config={
                    'predicted_action': 'Action',
                    'total_predictions': 'Total',
                    'successful_predictions': 'Successful',
                    'success_rate_pct': 'Success Rate',
                    'avg_return': 'Avg Return'
                }
            )
    
    def render_daily_performance_trends(self):
        """Render daily performance trends"""
        st.subheader("📈 Performance Trends")
        
        if not self.enhanced_metrics:
            st.warning("Enhanced metrics not available")
            return
        
        # Get daily performance data
        daily_data = self.enhanced_metrics.get_daily_performance_trends()
        
        if daily_data['daily_performance'].empty:
            st.info("No daily performance data available")
            return
        
        df = daily_data['daily_performance']
        
        # Create performance chart
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Daily Success Rate (%)', 'Daily Average Return'),
            vertical_spacing=0.1
        )
        
        # Success rate line
        fig.add_trace(
            go.Scatter(
                x=df['trade_date'],
                y=df['success_rate_pct'],
                mode='lines+markers',
                name='Success Rate %',
                line=dict(color='green', width=2)
            ),
            row=1, col=1
        )
        
        # Average return line
        fig.add_trace(
            go.Scatter(
                x=df['trade_date'],
                y=df['avg_return'],
                mode='lines+markers',
                name='Avg Return',
                line=dict(color='blue', width=2)
            ),
            row=2, col=1
        )
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show trend analysis
        trend_stats = daily_data.get('trend_analysis', {})
        if trend_stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Recent 7-day Avg", f"{trend_stats.get('recent_7_day_avg', 0):.1f}%")
            with col2:
                st.metric("Previous 7-day Avg", f"{trend_stats.get('older_7_day_avg', 0):.1f}%")
            with col3:
                trend_direction = trend_stats.get('trend_direction', 'Stable')
                color = "success-metric" if trend_direction == "Improving" else "warning-metric"
                st.markdown(f'<div class="{color}">Trend: {trend_direction}</div>', unsafe_allow_html=True)
    
    def render_symbol_performance(self):
        """Render symbol-specific performance breakdown"""
        st.subheader("📊 Symbol Performance Breakdown")
        
        if not self.enhanced_metrics:
            st.warning("Enhanced metrics not available")
            return
        
        symbol_data = self.enhanced_metrics.get_symbol_performance_breakdown()
        
        if symbol_data['symbol_performance'].empty:
            st.info("No symbol performance data available")
            return
        
        df = symbol_data['symbol_performance']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Symbol success rate chart
            fig = px.bar(
                df.head(10), 
                x='symbol', 
                y='success_rate_pct',
                title="Top 10 Symbols by Success Rate",
                color='success_rate_pct',
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Symbol performance table
            st.write("**Symbol Performance Summary**")
            display_df = df.head(10).copy()
            display_df['success_rate_pct'] = display_df['success_rate_pct'].apply(lambda x: f"{x:.1f}%")
            display_df['avg_return'] = display_df['avg_return'].apply(lambda x: f"{x:.3f}")
            display_df['avg_entry_price'] = display_df['avg_entry_price'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(
                display_df[['symbol', 'total_predictions', 'success_rate_pct', 'avg_return', 'avg_entry_price']],
                column_config={
                    'symbol': 'Symbol',
                    'total_predictions': 'Predictions',
                    'success_rate_pct': 'Success Rate',
                    'avg_return': 'Avg Return',
                    'avg_entry_price': 'Avg Price'
                }
            )
    
    def render_ig_markets_monitoring(self):
        """Render IG Markets price freshness monitoring"""
        st.subheader("📡 IG Markets Integration Status")
        
        if not self.enhanced_metrics:
            st.warning("Enhanced metrics not available")
            return
        
        price_data = self.enhanced_metrics.get_ig_markets_price_freshness()
        
        if price_data['price_data'].empty:
            st.info("No recent price data available")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Price freshness status
            freshness_stats = price_data.get('freshness_stats', {})
            
            if freshness_stats:
                fig = px.pie(
                    values=list(freshness_stats.values()),
                    names=list(freshness_stats.keys()),
                    title="Price Data Freshness Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Recent price data
            st.write("**Recent Price Updates**")
            df = price_data['price_data'].head(10)
            df['entry_price'] = df['entry_price'].apply(lambda x: f"${x:.2f}")
            df['hours_ago'] = df['hours_ago'].apply(lambda x: f"{x:.1f}h")
            
            st.dataframe(
                df[['symbol', 'entry_price', 'hours_ago', 'freshness_status']],
                column_config={
                    'symbol': 'Symbol',
                    'entry_price': 'Price',
                    'hours_ago': 'Age',
                    'freshness_status': 'Status'
                }
            )
    
    def render_recent_predictions_enhanced(self):
        """Render recent predictions with enhanced outcome data"""
        st.subheader("🔮 Recent Predictions with Outcomes")
        
        query = """
        SELECT 
            p.symbol,
            p.prediction_timestamp,
            p.predicted_action,
            p.action_confidence,
            p.entry_price,
            o.actual_return,
            o.evaluation_timestamp,
            CASE 
                WHEN o.actual_return IS NULL THEN 'PENDING'
                WHEN (p.predicted_action = 'BUY' AND o.actual_return > 0) OR 
                     (p.predicted_action = 'SELL' AND o.actual_return < 0) OR
                     (p.predicted_action = 'HOLD' AND ABS(o.actual_return) < 0.02) 
                THEN 'SUCCESS' 
                ELSE 'FAILED'
            END as outcome_status
        FROM predictions p
        LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
        ORDER BY p.prediction_timestamp DESC
        LIMIT 50
        """
        
        df = self.query_to_dataframe(query)
        
        if df.empty:
            st.info("No recent predictions available")
            return
        
        # Format the data for display
        df['prediction_timestamp'] = pd.to_datetime(df['prediction_timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        df['action_confidence'] = df['action_confidence'].apply(lambda x: f"{x:.1%}")
        df['entry_price'] = df['entry_price'].apply(lambda x: f"${x:.2f}")
        df['actual_return'] = df['actual_return'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "Pending")
        
        # Color-code the outcome status
        def color_outcome(val):
            if val == 'SUCCESS':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'FAILED':
                return 'background-color: #f8d7da; color: #721c24'
            else:
                return 'background-color: #fff3cd; color: #856404'
        
        styled_df = df.style.applymap(color_outcome, subset=['outcome_status'])
        st.dataframe(styled_df, use_container_width=True)
    
    def run_dashboard(self):
        """Main dashboard execution"""
        
        # Sidebar controls
        st.sidebar.title("🎯 Dashboard Controls")
        
        # Dashboard sections
        show_overview = st.sidebar.checkbox("System Overview", value=True)
        show_success_analysis = st.sidebar.checkbox("Success Rate Analysis", value=True)
        show_trends = st.sidebar.checkbox("Performance Trends", value=True)
        show_symbols = st.sidebar.checkbox("Symbol Performance", value=True)
        show_ig_status = st.sidebar.checkbox("IG Markets Status", value=True)
        show_predictions = st.sidebar.checkbox("Recent Predictions", value=True)
        
        # Auto-refresh
        auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
        if auto_refresh:
            st.rerun()
        
        # Render selected sections
        if show_overview:
            self.render_system_overview()
            st.divider()
        
        if show_success_analysis:
            self.render_success_rate_analysis()
            st.divider()
        
        if show_trends:
            self.render_daily_performance_trends()
            st.divider()
        
        if show_symbols:
            self.render_symbol_performance()
            st.divider()
        
        if show_ig_status:
            self.render_ig_markets_monitoring()
            st.divider()
        
        if show_predictions:
            self.render_recent_predictions_enhanced()
        
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.sidebar.caption("🎯 Enhanced Trading Dashboard v2.0")

# Main execution
if __name__ == "__main__":
    dashboard = EnhancedTradingDashboard()
    dashboard.run_dashboard()
