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

# Import performance analytics module
try:
    from performance_analytics_module import render_performance_analytics
    PERFORMANCE_ANALYTICS_AVAILABLE = True
except ImportError:
    PERFORMANCE_ANALYTICS_AVAILABLE = False
    st.warning("Performance Analytics Module not available. Install required dependencies.")

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
    
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.main_db_path = self.root_dir / "data" / "trading_predictions.db"
        # Initialize analysis_results
        self.analysis_results = {}
        # Load analysis results if available
        self.load_analysis_results()
    
    def load_analysis_results(self):
        """Load the analysis results from data flow analysis"""
        results_file = self.root_dir / "data_flow_analysis_results.json"
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    self.analysis_results = json.load(f)
            except Exception as e:
                # Silently handle file loading errors, use empty dict
                self.analysis_results = {}
        else:
            # File doesn't exist, use empty dict (will show info message in dashboard)
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
            st.info("💡 **Analysis Results Not Available** - Advanced system metrics will appear after running `data_flow_analysis.py`. Basic dashboard functionality is still available.")
            
            # Show basic database metrics instead
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="📁 Main Database", 
                    value="✅ Connected" if self.main_db_path.exists() else "❌ Missing",
                    help="Status of main trading database"
                )
            
            with col2:
                # Count tables in main database
                tables_query = "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
                df = self.query_to_dataframe(tables_query)
                table_count = df.iloc[0]['count'] if not df.empty else 0
                st.metric(
                    label="📊 Database Tables",
                    value=table_count,
                    help="Number of tables in main database"
                )
            
            with col3:
                # Count total predictions
                pred_query = "SELECT COUNT(*) as count FROM predictions"
                df = self.query_to_dataframe(pred_query)
                pred_count = df.iloc[0]['count'] if not df.empty else 0
                st.metric(
                    label="🔮 Total Predictions",
                    value=f"{pred_count:,}",
                    help="Total number of predictions made"
                )
            
            with col4:
                # Count outcomes
                outcome_query = "SELECT COUNT(*) as count FROM outcomes"
                df = self.query_to_dataframe(outcome_query)
                outcome_count = df.iloc[0]['count'] if not df.empty else 0
                st.metric(
                    label="📈 Evaluated Outcomes",
                    value=f"{outcome_count:,}",
                    help="Number of predictions with calculated outcomes"
                )
            
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
            
            # Add data quality filter options
            col1, col2 = st.columns(2)
            with col1:
                show_test_data = st.checkbox("Show Test Data", value=False, help="Include test predictions with 'test_' prefix")
            with col2:
                show_invalid_data = st.checkbox("Show Invalid Data", value=False, help="Include predictions with -9999 error values")
            
            # Build query with filters
            where_conditions = []
            if not show_test_data:
                where_conditions.append("prediction_id NOT LIKE 'test_%'")
            if not show_invalid_data:
                where_conditions.append("action_confidence != -9999 AND predicted_magnitude != -9999")
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            query = f"""
            SELECT 
                symbol,
                prediction_timestamp,
                predicted_action,
                action_confidence,
                entry_price,
                optimal_action,
                model_version,
                CASE 
                    WHEN action_confidence = -9999 THEN '🚨 CONF_ERROR'
                    WHEN predicted_magnitude = -9999 THEN '🚨 MAG_ERROR'
                    WHEN entry_price = 0 THEN '⚠️ PRICE_ERROR'
                    ELSE '✅ VALID'
                END as data_quality
            FROM predictions 
            {where_clause}
            ORDER BY prediction_timestamp DESC 
            LIMIT 20
            """
            df = self.query_to_dataframe(query)
            
            if not df.empty:
                # Show data quality summary
                if 'data_quality' in df.columns:
                    quality_counts = df['data_quality'].value_counts()
                    valid_count = quality_counts.get('✅ VALID', 0)
                    total_count = len(df)
                    quality_pct = (valid_count / total_count) * 100 if total_count > 0 else 0
                    
                    st.info(f"📊 Data Quality: {valid_count}/{total_count} valid predictions ({quality_pct:.1f}%)")
                
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
            self.render_model_training_status()
    
    def render_model_training_status(self):
        """Render model training status with real data from database"""
        try:
            # Load model performance data from all available tables
            training_data = []
            
            # Check model_performance table
            query_std = """
            SELECT 
                model_version as model_type,
                created_at as training_date,
                accuracy_direction as accuracy,
                accuracy_action as test_score,
                total_predictions
            FROM model_performance 
            ORDER BY created_at DESC
            """
            df_std = self.query_to_dataframe(query_std)
            if not df_std.empty:
                df_std['source'] = 'Standard'
                training_data.append(df_std)
            
            # Check model_performance_v2 table
            query_v2 = """
            SELECT 
                COALESCE(symbol || '_' || model_version, model_version) as model_type,
                training_date,
                accuracy_direction as accuracy,
                precision_score,
                recall_score,
                training_samples,
                f1_score
            FROM model_performance_v2 
            ORDER BY training_date DESC
            """
            df_v2 = self.query_to_dataframe(query_v2)
            if not df_v2.empty:
                df_v2['source'] = 'V2'
                training_data.append(df_v2)
            
            # Check model_performance_enhanced table
            query_enh = """
            SELECT 
                model_type,
                training_date,
                (direction_accuracy_1h + direction_accuracy_4h + direction_accuracy_1d) / 3 as accuracy,
                direction_accuracy_1h as test_score,
                training_samples,
                feature_count
            FROM model_performance_enhanced 
            ORDER BY training_date DESC
            """
            df_enh = self.query_to_dataframe(query_enh)
            if not df_enh.empty:
                df_enh['source'] = 'Enhanced'
                training_data.append(df_enh)
            
            if training_data:
                # Combine all training data
                all_training_df = pd.concat(training_data, ignore_index=True, sort=False)
                all_training_df['training_date'] = pd.to_datetime(all_training_df['training_date'])
                all_training_df = all_training_df.sort_values('training_date', ascending=False)
                
                # Training status overview
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    latest_training = all_training_df['training_date'].iloc[0] if len(all_training_df) > 0 else None
                    if latest_training:
                        days_since = (datetime.now() - latest_training).days
                        st.metric("Last Training", f"{days_since} days ago", 
                                delta=latest_training.strftime('%m-%d %H:%M'))
                    else:
                        st.metric("Last Training", "No data")
                
                with col2:
                    total_models = len(all_training_df['model_type'].unique())
                    st.metric("Model Types", total_models)
                
                with col3:
                    avg_accuracy = all_training_df['accuracy'].mean() if 'accuracy' in all_training_df.columns else 0
                    st.metric("Avg Accuracy", f"{avg_accuracy:.3f}")
                
                with col4:
                    total_records = len(all_training_df)
                    st.metric("Training Records", total_records)
                
                # Recent training activity
                st.markdown("#### 📋 Recent Training Activity")
                display_df = all_training_df.head(10).copy()
                display_df['training_date'] = display_df['training_date'].dt.strftime('%m-%d %H:%M')
                
                # Round numerical columns
                numeric_cols = ['accuracy', 'test_score', 'precision_score', 'recall_score', 'f1_score']
                for col in numeric_cols:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].round(3)
                
                st.dataframe(display_df, use_container_width=True)
                
                # Training trends
                if len(all_training_df) > 5:
                    st.markdown("#### 📈 Training Trends")
                    
                    # Create trend chart
                    fig = go.Figure()
                    
                    # Add accuracy trend
                    fig.add_trace(go.Scatter(
                        x=all_training_df['training_date'],
                        y=all_training_df['accuracy'],
                        mode='lines+markers',
                        name='Accuracy',
                        line=dict(color='blue')
                    ))
                    
                    # Add test score if available
                    if 'test_score' in all_training_df.columns and all_training_df['test_score'].notna().any():
                        fig.add_trace(go.Scatter(
                            x=all_training_df['training_date'],
                            y=all_training_df['test_score'],
                            mode='lines+markers',
                            name='Test Score',
                            line=dict(color='green')
                        ))
                    
                    fig.update_layout(
                        title="Model Performance Over Time",
                        xaxis_title="Training Date",
                        yaxis_title="Score",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Model type breakdown
                st.markdown("#### 🏢 Models by Type")
                model_counts = all_training_df['model_type'].value_counts()
                
                if len(model_counts) > 0:
                    fig_pie = px.pie(
                        values=model_counts.values,
                        names=model_counts.index,
                        title="Training Records by Model Type"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            else:
                st.warning("⚠️ No model training data found")
                st.info("""
                **To populate model training data:**
                - Run the evening routine to train models
                - Training metrics are saved to model_performance tables
                - Data is sourced from trading_predictions.db
                
                **Available tables:** model_performance, model_performance_v2, model_performance_enhanced
                """)
                
                # Show table status
                tables_to_check = ['model_performance', 'model_performance_v2', 'model_performance_enhanced']
                st.markdown("**Current Table Status:**")
                
                for table in tables_to_check:
                    try:
                        count_query = f"SELECT COUNT(*) as count FROM {table}"
                        result = self.query_to_dataframe(count_query)
                        count = result['count'].iloc[0] if not result.empty else 0
                        status_icon = "✅" if count > 0 else "❌"
                        st.text(f"{status_icon} {table}: {count} records")
                    except:
                        st.text(f"❌ {table}: table not found or error")
        
        except Exception as e:
            st.error(f"Error loading model training status: {e}")
    
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
        if self.analysis_results is not None and self.analysis_results:
            timestamp = self.analysis_results.get('timestamp', 'Unknown')
            st.info(f"Last analysis: {timestamp}")
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        st.sidebar.title("🎛️ Dashboard Navigation")
        
        # Database selector
        databases = list(self.analysis_results.get('databases', {}).keys()) if self.analysis_results is not None else []
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
        if self.analysis_results is not None:
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
    
    def render_performance_analytics_section(self):
        """Render the performance analytics module section"""
        if PERFORMANCE_ANALYTICS_AVAILABLE:
            # Add section divider
            st.markdown("---")
            
            # Create expandable section for performance analytics
            with st.expander("🚀 **Performance Analytics Module** - Detailed ML Performance Insights", expanded=False):
                st.markdown("""
                <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 0.5rem; border-radius: 5px; color: white; margin: 1rem 0;">
                    <h3>🧠 Advanced ML Performance Analytics</h3>
                    <p>Comprehensive analysis of model performance, prediction accuracy, and system health metrics</p>
                </div>
                """, unsafe_allow_html=True)
                
                try:
                    # Render the performance analytics module
                    db_path = str(self.root_dir / "data" / "trading_predictions.db")
                    render_performance_analytics(db_path)
                except Exception as e:
                    st.error(f"Error loading Performance Analytics Module: {str(e)}")
                    st.info("Please ensure the trading predictions database is available and accessible.")
        else:
            # Show placeholder when module not available
            st.markdown("---")
            st.warning("🚀 Performance Analytics Module not available. Please install required dependencies to enable advanced ML performance insights.")
    
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
        
        # Render Performance Analytics Module
        self.render_performance_analytics_section()

def main():
    """Main function to run the dashboard"""
    # Get the root directory (current working directory where script is run)
    import os
    from pathlib import Path
    root_dir = Path(os.getcwd())
    
    dashboard = TradingDataDashboard(root_dir)
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
