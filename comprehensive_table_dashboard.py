#!/usr/bin/env python3
"""
Comprehensive Table Dashboard

A Streamlit dashboard that displays all table data from each part of the database,
organized by the morning/evening routine data flow with real-time monitoring.
"""

import streamlit as st
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Trading System Data Dashboard", 
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
    .section-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
        margin: 1rem 0;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .data-quality-excellent { border-left-color: #28a745 !important; }
    .data-quality-good { border-left-color: #ffc107 !important; }
    .data-quality-poor { border-left-color: #dc3545 !important; }
    .table-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class TradingDataDashboard:
    """Comprehensive trading system data dashboard"""
    
    def __init__(self):
        self.root_dir = Path(".")
        self.main_db_path = self.root_dir / "data" / "trading_predictions.db"
        self.load_analysis_results()
    
    def load_analysis_results(self):
        """Load the analysis results from data flow analysis"""
        results_file = self.root_dir / "data_flow_analysis_results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                self.analysis_results = json.load(f)
        else:
            st.error("❌ Analysis results not found. Please run data_flow_analysis.py first.")
            self.analysis_results = {}
    
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
            conn.close()
            return pd.DataFrame()
    
    def render_header(self):
        """Render main dashboard header"""
        st.markdown("""
        <div class="main-header">
            <h1>🎯 Trading System Data Dashboard</h1>
            <p>Comprehensive view of all database tables and data flow</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_system_overview(self):
        """Render system overview metrics"""
        st.markdown('<div class="section-header"><h2>📊 System Overview</h2></div>', unsafe_allow_html=True)
        
        if not self.analysis_results:
            st.warning("No analysis results available")
            return
        
        summary = self.analysis_results.get('dashboard_data', {}).get('summary', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📁 Total Databases",
                value=summary.get('total_databases', 0),
                help="Number of SQLite databases discovered"
            )
        
        with col2:
            st.metric(
                label="📊 Total Tables",
                value=summary.get('total_tables', 0),
                help="Total number of database tables"
            )
        
        with col3:
            st.metric(
                label="📈 Total Records",
                value=f"{summary.get('total_records', 0):,}",
                help="Total number of records across all tables"
            )
        
        with col4:
            health = summary.get('data_flow_health', 'UNKNOWN')
            health_color = {
                'EXCELLENT': '🟢',
                'GOOD': '🟡', 
                'FAIR': '🟠',
                'POOR': '🔴',
                'NO_DATA': '⚫'
            }.get(health, '❓')
            
            st.metric(
                label="💊 Data Flow Health",
                value=f"{health_color} {health}",
                help="Overall health of data flow pipeline"
            )
    
    def render_main_tables_status(self):
        """Render main trading tables status"""
        st.markdown('<div class="section-header"><h2>🎯 Main Trading Tables</h2></div>', unsafe_allow_html=True)
        
        # Query main tables
        main_tables = {
            'Predictions': 'SELECT COUNT(*) as count, MAX(prediction_timestamp) as latest FROM predictions',
            'Enhanced Features': 'SELECT COUNT(*) as count, MAX(timestamp) as latest FROM enhanced_features', 
            'Enhanced Outcomes': 'SELECT COUNT(*) as count, MAX(prediction_timestamp) as latest FROM enhanced_outcomes',
            'Outcomes': 'SELECT COUNT(*) as count, MAX(created_at) as latest FROM outcomes',
            'Sentiment Data': 'SELECT COUNT(*) as count, MAX(timestamp) as latest FROM enhanced_features WHERE sentiment_score IS NOT NULL'
        }
        
        col1, col2 = st.columns(2)
        
        for i, (table_name, query) in enumerate(main_tables.items()):
            df = self.query_to_dataframe(query)
            
            if not df.empty:
                count = df.iloc[0]['count']
                latest = df.iloc[0]['latest']
                
                # Determine data quality
                if count > 50:
                    quality_class = "data-quality-excellent"
                    quality_icon = "🟢"
                elif count > 10:
                    quality_class = "data-quality-good"
                    quality_icon = "🟡"
                else:
                    quality_class = "data-quality-poor"
                    quality_icon = "🔴"
                
                container = col1 if i % 2 == 0 else col2
                
                with container:
                    st.markdown(f"""
                    <div class="metric-card {quality_class}">
                        <h4>{quality_icon} {table_name}</h4>
                        <p><strong>Records:</strong> {count:,}</p>
                        <p><strong>Latest:</strong> {latest or 'No data'}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                container = col1 if i % 2 == 0 else col2
                with container:
                    st.markdown(f"""
                    <div class="metric-card data-quality-poor">
                        <h4>🔴 {table_name}</h4>
                        <p><strong>Status:</strong> No data or error</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    def render_morning_routine_data(self):
        """Render morning routine data tables"""
        st.markdown('<div class="section-header"><h2>🌅 Morning Routine Data</h2></div>', unsafe_allow_html=True)
        
        tabs = st.tabs(["📊 Predictions", "🔍 Enhanced Features", "📰 Sentiment Analysis", "📈 Technical Analysis"])
        
        with tabs[0]:
            st.subheader("Recent Predictions")
            query = """
            SELECT 
                symbol,
                prediction_timestamp,
                predicted_action,
                action_confidence,
                entry_price,
                optimal_action
            FROM predictions 
            ORDER BY prediction_timestamp DESC 
            LIMIT 20
            """
            df = self.query_to_dataframe(query)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Predictions by action chart
                action_counts = df['predicted_action'].value_counts()
                fig = px.pie(
                    values=action_counts.values,
                    names=action_counts.index,
                    title="Predictions by Action"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No prediction data available")
        
        with tabs[1]:
            st.subheader("Enhanced Features")
            query = """
            SELECT 
                symbol,
                timestamp as analysis_timestamp,
                sentiment_score,
                rsi,
                macd_line,
                volatility_20d,
                current_price
            FROM enhanced_features 
            ORDER BY timestamp DESC 
            LIMIT 20
            """
            df = self.query_to_dataframe(query)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Feature analysis charts
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'sentiment_score' in df.columns:
                        fig = px.histogram(df, x='sentiment_score', title="Sentiment Score Distribution")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if 'rsi' in df.columns:
                        fig = px.histogram(df, x='rsi', title="RSI Distribution")
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No enhanced features data available")
        
        with tabs[2]:
            st.subheader("Sentiment Features")
            query = """
            SELECT 
                symbol,
                timestamp as created_at,
                sentiment_score,
                confidence as sentiment_confidence,
                news_count,
                reddit_sentiment
            FROM enhanced_features 
            WHERE sentiment_score IS NOT NULL
            ORDER BY timestamp DESC 
            LIMIT 20
            """
            df = self.query_to_dataframe(query)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Sentiment over time
                if len(df) > 1:
                    df['created_at'] = pd.to_datetime(df['created_at'])
                    fig = px.line(df, x='created_at', y='sentiment_score', color='symbol', 
                                title="Sentiment Score Over Time")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sentiment features data available")
        
        with tabs[3]:
            st.subheader("Technical Analysis")
            # Show technical analysis from enhanced features
            query = """
            SELECT 
                symbol,
                timestamp as analysis_timestamp,
                rsi,
                macd_line,
                bollinger_upper,
                bollinger_lower,
                volatility_20d,
                volume_sma20 as volume_ma
            FROM enhanced_features 
            WHERE rsi IS NOT NULL
            ORDER BY timestamp DESC 
            LIMIT 20
            """
            df = self.query_to_dataframe(query)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Technical indicators charts
                symbols = df['symbol'].unique()
                selected_symbol = st.selectbox("Select symbol for technical analysis", symbols)
                
                symbol_data = df[df['symbol'] == selected_symbol].copy()
                if not symbol_data.empty:
                    symbol_data['analysis_timestamp'] = pd.to_datetime(symbol_data['analysis_timestamp'])
                    
                    fig = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=('RSI', 'MACD'),
                        shared_xaxes=True
                    )
                    
                    # RSI
                    fig.add_trace(
                        go.Scatter(x=symbol_data['analysis_timestamp'], y=symbol_data['rsi'], name='RSI'),
                        row=1, col=1
                    )
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=1, col=1)
                    
                    # MACD
                    fig.add_trace(
                        go.Scatter(x=symbol_data['analysis_timestamp'], y=symbol_data['macd_line'], name='MACD'),
                        row=2, col=1
                    )
                    
                    fig.update_layout(height=600, title=f"Technical Indicators for {selected_symbol}")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No technical analysis data available")
    
    def render_evening_routine_data(self):
        """Render evening routine data tables"""
        st.markdown('<div class="section-header"><h2>🌆 Evening Routine Data</h2></div>', unsafe_allow_html=True)
        
        tabs = st.tabs(["📊 Outcomes", "🎯 Enhanced Outcomes", "📈 Performance", "🧠 Model Training"])
        
        with tabs[0]:
            st.subheader("Trading Outcomes")
            query = """
            SELECT 
                outcome_id,
                prediction_id,
                actual_return,
                entry_price,
                exit_price,
                evaluation_timestamp
            FROM outcomes 
            ORDER BY created_at DESC 
            LIMIT 20
            """
            df = self.query_to_dataframe(query)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Performance metrics
                if 'actual_return' in df.columns and df['actual_return'].notna().any():
                    returns = df['actual_return'].dropna()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Average Return", f"{returns.mean():.3f}")
                    with col2:
                        st.metric("Win Rate", f"{(returns > 0).mean():.1%}")
                    with col3:
                        st.metric("Total Trades", len(returns))
                    
                    # Returns distribution
                    fig = px.histogram(returns, title="Returns Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No actual return data available yet")
            else:
                st.info("No outcomes data available")
        
        with tabs[1]:
            st.subheader("Enhanced Outcomes")
            query = """
            SELECT 
                symbol,
                prediction_timestamp,
                optimal_action,
                confidence_score,
                entry_price,
                exit_price_1h,
                exit_price_4h,
                exit_price_1d,
                return_pct
            FROM enhanced_outcomes 
            ORDER BY prediction_timestamp DESC 
            LIMIT 20
            """
            df = self.query_to_dataframe(query)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Enhanced outcomes analysis
                if 'return_pct' in df.columns and df['return_pct'].notna().any():
                    returns = df['return_pct'].dropna()
                    actions = df['optimal_action'].value_counts()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.pie(values=actions.values, names=actions.index, title="Actions Distribution")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.box(df, y='return_pct', x='optimal_action', title="Returns by Action")
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No enhanced outcomes data available")
        
        with tabs[2]:
            st.subheader("Performance Metrics")
            
            # Model performance data - try enhanced table first, fallback to regular
            query = """
            SELECT 
                model_version as model_name,
                training_date,
                COALESCE(direction_accuracy_1d, 0.0) as accuracy,
                COALESCE(precision_score, 0.0) as precision_score,
                COALESCE(recall_score, 0.0) as recall,
                COALESCE(f1_score, 0.0) as f1_score
            FROM model_performance_enhanced 
            ORDER BY training_date DESC 
            LIMIT 10
            """
            df = self.query_to_dataframe(query)
            
            # Fallback to regular model_performance if enhanced is empty
            if df.empty:
                query_fallback = """
                SELECT 
                    model_version as model_name,
                    created_at as training_date,
                    COALESCE(accuracy_action, 0.0) as accuracy,
                    COALESCE(accuracy_direction, 0.0) as precision_score,
                    COALESCE(accuracy_direction, 0.0) as recall,
                    COALESCE(mae_magnitude, 0.0) as f1_score
                FROM model_performance 
                ORDER BY created_at DESC 
                LIMIT 10
                """
                df = self.query_to_dataframe(query_fallback)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Performance over time
                df['training_date'] = pd.to_datetime(df['training_date'])
                fig = px.line(df, x='training_date', y=['accuracy', 'precision_score', 'recall', 'f1_score'],
                            title="Model Performance Over Time")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No model performance data available yet. Performance metrics will appear here after model training runs.")
                st.markdown("""
                **Expected metrics:**
                - **Accuracy**: Overall prediction accuracy
                - **Precision**: True positive rate  
                - **Recall**: Sensitivity of predictions
                - **F1 Score**: Harmonic mean of precision and recall
                
                *Run evening routine to generate performance data*
                """)
        
        with tabs[3]:
            st.subheader("Model Training Status")
            st.info("Model training metrics will be displayed here when evening routine runs")
    
    def render_data_quality_issues(self):
        """Render data quality and consistency issues"""
        st.markdown('<div class="section-header"><h2>⚠️ Data Quality Issues</h2></div>', unsafe_allow_html=True)
        
        if not self.analysis_results:
            st.warning("No analysis results available")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Consistency Issues")
            issues = self.analysis_results.get('consistency_issues', [])
            
            if issues:
                for issue in issues:
                    st.error(f"• {issue}")
            else:
                st.success("✅ No consistency issues found")
        
        with col2:
            st.subheader("🚨 Data Leakage Risks")
            risks = self.analysis_results.get('leakage_risks', [])
            
            if risks:
                for risk in risks:
                    st.warning(f"• {risk}")
                
                st.info("""
                **Recommendations:**
                • Implement idempotent operations with date-based deduplication
                • Add unique constraints on (symbol, date) combinations
                • Use transaction rollback on duplicate detection
                """)
            else:
                st.success("✅ No obvious data leakage risks detected")
    
    def render_real_time_monitoring(self):
        """Render real-time monitoring section"""
        st.markdown('<div class="section-header"><h2>🔄 Real-time Monitoring</h2></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Data", type="primary"):
                st.rerun()
        
        with col2:
            if st.button("📊 Run Analysis", type="secondary"):
                st.info("This would trigger data_flow_analysis.py")
        
        with col3:
            if st.button("🧹 Clean Data", type="secondary"):
                st.info("This would trigger data cleanup routines")
        
        # Last update timestamp
        if self.analysis_results:
            timestamp = self.analysis_results.get('timestamp', 'Unknown')
            st.info(f"Last analysis: {timestamp}")
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        st.sidebar.title("🎛️ Dashboard Navigation")
        
        # Database selector
        databases = list(self.analysis_results.get('databases', {}).keys()) if self.analysis_results else []
        selected_db = st.sidebar.selectbox("📁 Select Database", ["data/trading_predictions.db"] + databases)
        
        # Table selector for detailed view
        st.sidebar.subheader("🔍 Detailed Table View")
        tables = [
            "predictions", "enhanced_features", "enhanced_outcomes", 
            "outcomes", "sentiment_features", "model_performance"
        ]
        selected_table = st.sidebar.selectbox("📊 Select Table", tables)
        
        if st.sidebar.button("📋 View Table Details"):
            st.session_state['view_table'] = selected_table
        
        # Quick stats
        st.sidebar.subheader("📈 Quick Stats")
        if self.analysis_results:
            summary = self.analysis_results.get('dashboard_data', {}).get('summary', {})
            st.sidebar.metric("Total Records", f"{summary.get('total_records', 0):,}")
            st.sidebar.metric("Health Status", summary.get('data_flow_health', 'Unknown'))
        
        # Export options
        st.sidebar.subheader("📤 Export Options")
        if st.sidebar.button("📄 Export Analysis"):
            st.sidebar.info("Analysis results can be found in data_flow_analysis_results.json")
    
    def render_detailed_table_view(self, table_name):
        """Render detailed view of selected table"""
        st.subheader(f"📊 Detailed View: {table_name}")
        
        # Get table schema
        query_schema = f"PRAGMA table_info({table_name})"
        schema_df = self.query_to_dataframe(query_schema)
        
        if not schema_df.empty:
            st.subheader("🏗️ Table Schema")
            st.dataframe(schema_df, use_container_width=True)
        
        # Get all data from table
        query_data = f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 100"
        data_df = self.query_to_dataframe(query_data)
        
        if not data_df.empty:
            st.subheader("📋 Table Data (Latest 100 records)")
            st.dataframe(data_df, use_container_width=True)
            
            # Data summary
            st.subheader("📊 Data Summary")
            st.write(f"Total columns: {len(data_df.columns)}")
            st.write(f"Records shown: {len(data_df)}")
            
            # Column analysis for numeric columns
            numeric_cols = data_df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                st.subheader("🔢 Numeric Column Statistics")
                st.dataframe(data_df[numeric_cols].describe(), use_container_width=True)
        else:
            st.info(f"No data found in table {table_name}")
    
    def run_dashboard(self):
        """Main dashboard function"""
        # Render sidebar
        self.render_sidebar()
        
        # Render header
        self.render_header()
        
        # Check if detailed table view is requested
        if 'view_table' in st.session_state:
            self.render_detailed_table_view(st.session_state['view_table'])
            if st.button("← Back to Dashboard"):
                del st.session_state['view_table']
                st.rerun()
            return
        
        # Render main dashboard sections
        self.render_system_overview()
        self.render_main_tables_status()
        self.render_morning_routine_data()
        self.render_evening_routine_data()
        self.render_data_quality_issues()
        self.render_real_time_monitoring()

def main():
    """Main function to run the dashboard"""
    dashboard = TradingDataDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
