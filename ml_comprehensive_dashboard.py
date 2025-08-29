#!/usr/bin/env python3
"""
🔬 ML Comprehensive Dashboard - Complete Trading Analysis Platform
Integrates all ML analytics, backtesting, and performance analysis tools
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

# Import our modules
import sys
sys.path.append('backtesting')
try:
    from realistic_ml_backtester import RealisticMLBacktester
    REALISTIC_BACKTESTER_AVAILABLE = True
except ImportError:
    REALISTIC_BACKTESTER_AVAILABLE = False
    st.warning("⚠️ Realistic backtester not available. Please ensure realistic_ml_backtester.py is in the same directory.")

try:
    from performance_analytics_module import PerformanceAnalytics
    PERFORMANCE_ANALYTICS_AVAILABLE = True
except ImportError:
    PERFORMANCE_ANALYTICS_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="ML Comprehensive Trading Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        color: #ff7f0e;
        border-bottom: 2px solid #ff7f0e;
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Database connection functions
@st.cache_resource
def get_db_connection():
    """Connect to main trading predictions database"""
    try:
        return sqlite3.connect('data/trading_predictions.db')
    except:
        return None

# Data loading functions
@st.cache_data(ttl=300)
def load_recent_predictions(hours=24):
    """Load recent predictions from database"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT p.*, o.actual_return, o.actual_direction, o.entry_price as outcome_entry_price, 
               o.exit_price, o.evaluation_timestamp
        FROM predictions p
        LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
        WHERE p.prediction_timestamp >= datetime('now', '-{} hours')
        ORDER BY p.prediction_timestamp DESC
        """.format(hours)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading predictions: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_enhanced_features():
    """Load enhanced features from database"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = "SELECT * FROM enhanced_features ORDER BY timestamp DESC LIMIT 100"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def main():
    """Main dashboard application"""
    
    # Header
    st.markdown('<h1 class="main-header">🔬 ML Comprehensive Trading Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("**Complete trading analysis platform with realistic backtesting and performance analytics**")
    
    # Sidebar navigation
    st.sidebar.title("🔬 Navigation")
    selected_section = st.sidebar.selectbox(
        "Choose Section",
        [
            "📊 Live Performance Overview",
            "🧠 Model Training Status",
            "🔬 Realistic Backtester", 
            "📈 Historical Analysis",
            "🎯 Strategy Comparison",
            "⚙️ System Diagnostics"
        ]
    )
    
    # Main content based on selection
    if selected_section == "📊 Live Performance Overview":
        show_live_performance()
    elif selected_section == "🧠 Model Training Status":
        show_model_training_status()
    elif selected_section == "🔬 Realistic Backtester":
        show_realistic_backtester()
    elif selected_section == "📈 Historical Analysis":
        show_historical_analysis()
    elif selected_section == "🎯 Strategy Comparison":
        show_strategy_comparison()
    elif selected_section == "⚙️ System Diagnostics":
        show_system_diagnostics()

def show_live_performance():
    """Show live performance overview"""
    st.markdown('<h2 class="section-header">📊 Live Performance Overview</h2>', unsafe_allow_html=True)
    
    # Time selection
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        hours_back = st.selectbox("Time Period", [1, 6, 12, 24, 48, 168], index=3)
    with col2:
        auto_refresh = st.checkbox("Auto Refresh (5min)", value=False)
    
    # Load recent data
    df = load_recent_predictions(hours_back)
    
    if df.empty:
        st.warning(f"⚠️ No predictions found in the last {hours_back} hours")
        return
    
    # Key metrics
    st.markdown("### 📈 Key Performance Metrics")
    
    # Calculate metrics
    total_predictions = len(df)
    buy_predictions = len(df[df['predicted_action'] == 'BUY'])
    with_outcomes = len(df[df['actual_return'].notna()])
    profitable = len(df[df['actual_return'] > 0]) if with_outcomes > 0 else 0
    
    avg_confidence = df['action_confidence'].mean() if 'action_confidence' in df.columns else 0
    
    # Calculate total profit from actual returns and entry prices
    if with_outcomes > 0 and 'entry_price' in df.columns:
        # Convert returns to dollar profits
        df['calculated_profit'] = df['actual_return'] * df['entry_price'] * 100  # Assuming 100 shares
        total_profit = df['calculated_profit'].sum()
    else:
        total_profit = 0
    
    # Display metrics in columns
    metric_cols = st.columns(6)
    
    with metric_cols[0]:
        st.metric("Total Predictions", total_predictions)
    with metric_cols[1]:
        st.metric("BUY Signals", buy_predictions)
    with metric_cols[2]:
        st.metric("With Outcomes", with_outcomes)
    with metric_cols[3]:
        win_rate = (profitable / with_outcomes * 100) if with_outcomes > 0 else 0
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with metric_cols[4]:
        st.metric("Avg Confidence", f"{avg_confidence:.3f}")
    with metric_cols[5]:
        st.metric("Total Profit", f"${total_profit:.2f}")
    
    # Charts
    if len(df) > 0:
        chart_cols = st.columns(2)
        
        with chart_cols[0]:
            # Confidence distribution
            st.markdown("#### 📊 Confidence Distribution")
            if 'action_confidence' in df.columns:
                fig_conf = px.histogram(
                    df, 
                    x='action_confidence', 
                    title="Prediction Confidence Distribution"
                )
                st.plotly_chart(fig_conf, use_container_width=True)
        
        with chart_cols[1]:
            # Symbol distribution
            st.markdown("#### 🏢 Symbol Distribution")
            symbol_counts = df['symbol'].value_counts()
            fig_symbols = px.pie(
                values=symbol_counts.values,
                names=symbol_counts.index,
                title="Predictions by Symbol"
            )
            st.plotly_chart(fig_symbols, use_container_width=True)
    
    # Recent predictions table
    st.markdown("### 📋 Recent Predictions")
    display_cols = ['symbol', 'predicted_action', 'prediction_timestamp', 'entry_price']
    if 'action_confidence' in df.columns:
        display_cols.append('action_confidence')
    if 'actual_return' in df.columns:
        display_cols.append('actual_return')
    if 'calculated_profit' in df.columns:
        display_cols.append('calculated_profit')
    
    display_df = df[display_cols].head(20).copy()
    if 'prediction_timestamp' in display_df.columns:
        display_df['prediction_timestamp'] = pd.to_datetime(display_df['prediction_timestamp']).dt.strftime('%m-%d %H:%M')
    
    st.dataframe(display_df, use_container_width=True)

def show_realistic_backtester():
    """Show realistic backtester section"""
    st.markdown('<h2 class="section-header">🔬 Realistic Backtester</h2>', unsafe_allow_html=True)
    
    if not REALISTIC_BACKTESTER_AVAILABLE:
        st.error("❌ Realistic backtester not available. Please ensure realistic_ml_backtester.py is in the same directory.")
        return
    
    st.markdown("**Uses actual historical timing and profit data for accurate performance simulation**")
    
    # Configuration section
    st.markdown("### ⚙️ Backtester Configuration")
    
    config_cols = st.columns(3)
    
    with config_cols[0]:
        st.markdown("#### 💼 Position Management")
        position_mode = st.selectbox(
            "Position Management Mode",
            ["one_per_symbol", "unlimited", "max_positions"],
            help="How to manage multiple positions"
        )
        
        max_positions = None
        if position_mode == "max_positions":
            max_positions = st.number_input("Max Positions", min_value=1, value=5)
    
    with config_cols[1]:
        st.markdown("#### 💰 Capital Settings")
        total_capital = st.number_input(
            "Total Capital ($)",
            min_value=1000,
            value=100000,
            step=1000,
            help="Starting capital for backtesting"
        )
        
        position_size = st.number_input(
            "Position Size ($)",
            min_value=100,
            value=10000,
            step=100,
            help="Size of each position"
        )
    
    with config_cols[2]:
        st.markdown("#### 🎯 Risk Settings")
        profit_target = st.number_input(
            "Profit Target ($)",
            min_value=1.0,
            value=5.0,
            step=0.5,
            help="Target profit per trade"
        )
        
        max_hold_time_options = {
            "5 minutes": 5,
            "15 minutes": 15,
            "30 minutes": 30,
            "1 hour": 60,
            "4 hours": 240,
            "1 day": 1440
        }
        
        max_hold_time_label = st.selectbox(
            "Max Hold Time",
            list(max_hold_time_options.keys()),
            index=5
        )
        max_hold_time = max_hold_time_options[max_hold_time_label]
    
    # Run backtester
    if st.button("🚀 Run Realistic Backtest", type="primary"):
        with st.spinner("Running realistic backtest with actual historical data..."):
            try:
                # Create and configure backtester
                backtester = RealisticMLBacktester()
                
                # Load data
                if backtester.load_data():
                    # Configure parameters
                    config = {
                        'position_management': position_mode,
                        'position_size': position_size,
                        'total_capital': total_capital,
                        'profit_target': profit_target,
                        'max_hold_time': max_hold_time
                    }
                    
                    if max_positions and position_mode == "max_positions":
                        config['max_positions'] = max_positions
                    
                    backtester.configure_backtest(**config)
                    
                    # Run backtest
                    results = backtester.run_realistic_backtest()
                    
                    if results and 'metrics' in results:
                        display_realistic_results(results)
                        
                        # Export option
                        if st.button("📊 Export Results"):
                            filename = backtester.export_realistic_results()
                            if filename:
                                st.success(f"✅ Results exported to {filename}")
                    else:
                        st.error("❌ No backtest results available")
                else:
                    st.error("❌ Failed to load data files")
                    st.info("Please ensure these files exist:\n- final_clean_trades_20250828_085247.csv\n- buy_position_timing_analysis_20250828_093638.csv")
                    
            except Exception as e:
                st.error(f"❌ Backtest failed: {str(e)}")

def display_realistic_results(results):
    """Display realistic backtest results"""
    
    metrics = results['metrics']
    trades = results['trade_history']
    
    st.markdown("---")
    st.markdown("### 📊 Realistic Backtest Results")
    
    # Key metrics
    result_cols = st.columns(4)
    
    with result_cols[0]:
        st.metric(
            "Total Return",
            f"{metrics['total_return']:.2f}%",
            delta=f"${metrics['total_profit']:,.2f}"
        )
    
    with result_cols[1]:
        st.metric(
            "Win Rate",
            f"{metrics['win_rate']:.1f}%",
            delta=f"{metrics['winning_trades']}/{metrics['total_trades']} trades"
        )
    
    with result_cols[2]:
        st.metric(
            "Avg Profit",
            f"${metrics['avg_profit']:.2f}",
            delta=f"{metrics['avg_hold_time']:.0f} min avg hold"
        )
    
    with result_cols[3]:
        total_opportunities = len(results.get('merged_df', []))
        execution_rate = (len(trades) / total_opportunities * 100) if total_opportunities > 0 else 0
        st.metric(
            "Execution Rate",
            f"{execution_rate:.1f}%",
            delta=f"{len(trades)} trades executed"
        )
    
    # Detailed analysis charts
    if trades:
        trades_df = pd.DataFrame(trades)
        
        # Create comprehensive chart
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Cumulative Returns', 'Trade Profits', 'Exit Timing', 'Symbol Performance'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 1. Cumulative returns
        trades_df['cumulative_profit'] = trades_df['profit'].cumsum()
        fig.add_trace(
            go.Scatter(
                x=trades_df.index + 1,
                y=trades_df['cumulative_profit'],
                mode='lines+markers',
                name='Cumulative Profit',
                line=dict(color='green')
            ),
            row=1, col=1
        )
        
        # 2. Individual trade profits
        colors = ['green' if p > 0 else 'red' for p in trades_df['profit']]
        fig.add_trace(
            go.Bar(
                x=trades_df.index + 1,
                y=trades_df['profit'],
                name='Trade Profit',
                marker_color=colors,
                showlegend=False
            ),
            row=1, col=2
        )
        
        # 3. Exit timing analysis
        exit_counts = trades_df['exit_interval'].value_counts()
        fig.add_trace(
            go.Bar(
                x=exit_counts.index,
                y=exit_counts.values,
                name='Exit Timing',
                marker_color='blue',
                showlegend=False
            ),
            row=2, col=1
        )
        
        # 4. Symbol performance
        symbol_profits = trades_df.groupby('symbol')['profit'].sum().sort_values(ascending=True)
        fig.add_trace(
            go.Bar(
                y=symbol_profits.index,
                x=symbol_profits.values,
                orientation='h',
                name='Symbol Profit',
                marker_color='purple',
                showlegend=False
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=600, title_text="Realistic Backtest Analysis")
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed tables
        analysis_tabs = st.tabs(["📋 Trade History", "🏢 Symbol Performance", "⏰ Exit Analysis"])
        
        with analysis_tabs[0]:
            display_df = trades_df[['symbol', 'entry_time', 'exit_time', 'profit', 'return_pct', 'exit_reason']].copy()
            display_df['entry_time'] = pd.to_datetime(display_df['entry_time']).dt.strftime('%m-%d %H:%M')
            display_df['exit_time'] = pd.to_datetime(display_df['exit_time']).dt.strftime('%m-%d %H:%M')
            display_df['profit'] = display_df['profit'].round(2)
            display_df['return_pct'] = display_df['return_pct'].round(2)
            st.dataframe(display_df, use_container_width=True)
        
        with analysis_tabs[1]:
            symbol_summary = trades_df.groupby('symbol').agg({
                'profit': ['count', 'sum', 'mean'],
                'return_pct': 'mean',
                'hold_time_minutes': 'mean'
            }).round(2)
            symbol_summary.columns = ['Trades', 'Total Profit', 'Avg Profit', 'Avg Return %', 'Avg Hold (min)']
            st.dataframe(symbol_summary, use_container_width=True)
        
        with analysis_tabs[2]:
            exit_analysis = trades_df.groupby('exit_interval').agg({
                'profit': ['count', 'sum', 'mean'],
                'return_pct': 'mean'
            }).round(2)
            exit_analysis.columns = ['Count', 'Total Profit', 'Avg Profit', 'Avg Return %']
            st.dataframe(exit_analysis, use_container_width=True)

def show_historical_analysis():
    """Show historical analysis section"""
    st.markdown('<h2 class="section-header">📈 Historical Analysis</h2>', unsafe_allow_html=True)
    st.info("Historical analysis features will be added here")

def show_strategy_comparison():
    """Show strategy comparison section"""
    st.markdown('<h2 class="section-header">🎯 Strategy Comparison</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 🔬 Realistic vs Simulated Backtesting Comparison
    
    #### ✅ Realistic Backtester Features:
    - Uses actual historical timing data from your analysis
    - Real profit/loss values from market performance
    - Realistic position constraints (one per symbol)
    - Actual hold times and exit points
    - Conservative execution rate (35.4%)
    - True performance estimates
    
    #### ⚠️ Simulated Backtester Limitations:
    - Uses artificial price movements
    - Optimistic profit assumptions
    - Unrealistic 100% execution rate
    - Perfect timing assumptions
    - May overestimate performance significantly
    - Good for strategy development only
    
    #### 💡 Recommendation:
    **Use the Realistic Backtester for actual performance evaluation** and investment decisions.
    **Use simulated backtesting for strategy development** and theoretical testing.
    """)

def show_system_diagnostics():
    """Show system diagnostics"""
    st.markdown('<h2 class="section-header">⚙️ System Diagnostics</h2>', unsafe_allow_html=True)
    
    # Database connectivity
    st.markdown("### 🔧 Database Connectivity")
    
    st.markdown("#### Main Trading Database")
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions")
            pred_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM outcomes")
            outcome_count = cursor.fetchone()[0]
            
            # Check model performance tables
            try:
                cursor.execute("SELECT COUNT(*) FROM model_performance")
                model_perf_count = cursor.fetchone()[0]
            except:
                model_perf_count = 0
                
            try:
                cursor.execute("SELECT COUNT(*) FROM model_performance_enhanced")
                model_perf_enh_count = cursor.fetchone()[0]
            except:
                model_perf_enh_count = 0
                
            conn.close()
            
            st.success("✅ Main trading database connected")
            st.info(f"📊 Predictions: {pred_count}")
            st.info(f"🎯 Outcomes: {outcome_count}")
            st.info(f"🧠 Model Performance: {model_perf_count}")
            st.info(f"� Enhanced Model Performance: {model_perf_enh_count}")
        except Exception as e:
            st.error(f"❌ Database error: {e}")
    else:
        st.error("❌ Cannot connect to main trading database")
    
    # File availability
    st.markdown("### 📁 Required Files")
    
    required_files = [
        'final_clean_trades_20250828_085247.csv',
        'buy_position_timing_analysis_20250828_093638.csv',
        'realistic_ml_backtester.py',
        'performance_analytics_module.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            st.success(f"✅ {file}")
        else:
            st.error(f"❌ {file} - Not found")
    
    # Module availability
    st.markdown("### 🧩 Module Availability")
    
    modules = [
        ("Realistic Backtester", REALISTIC_BACKTESTER_AVAILABLE),
        ("Performance Analytics", PERFORMANCE_ANALYTICS_AVAILABLE)
    ]
    
    for module_name, available in modules:
        if available:
            st.success(f"✅ {module_name}")
        else:
            st.error(f"❌ {module_name} - Not available")

@st.cache_data(ttl=300)
def load_model_performance():
    """Load model performance data from main trading database"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()
        
        # First, try to get data from standard model_performance table
        try:
            query = """
            SELECT 
                model_version as model_type,
                created_at as training_date,
                accuracy_direction as validation_score,
                accuracy_action as test_score,
                accuracy_direction as precision_score,
                accuracy_action as recall_score,
                '{}' as parameters,
                '{}' as feature_importance
            FROM model_performance 
            ORDER BY created_at DESC
            """
            df_standard = pd.read_sql_query(query, conn)
        except:
            df_standard = pd.DataFrame()
        
        # Try model_performance_v2 table 
        try:
            v2_query = """
            SELECT 
                COALESCE(symbol || '_' || model_version, model_version) as model_type,
                training_date,
                accuracy_direction as validation_score,
                accuracy_action as test_score,
                precision_score,
                recall_score,
                '{}' as parameters,
                '{}' as feature_importance
            FROM model_performance_v2 
            ORDER BY training_date DESC
            """
            df_v2 = pd.read_sql_query(v2_query, conn)
        except:
            df_v2 = pd.DataFrame()
        
        # Also try to get data from enhanced table if it exists
        try:
            enhanced_query = """
            SELECT 
                model_type,
                training_date,
                (direction_accuracy_1h + direction_accuracy_4h + direction_accuracy_1d) / 3 as validation_score,
                direction_accuracy_1h as test_score,
                direction_accuracy_1h as precision_score,
                direction_accuracy_4h as recall_score,
                parameters,
                feature_importance
            FROM model_performance_enhanced 
            ORDER BY training_date DESC
            """
            df_enhanced = pd.read_sql_query(enhanced_query, conn)
        except:
            df_enhanced = pd.DataFrame()
        
        conn.close()
        
        # Combine all dataframes if we have data
        dfs = [df for df in [df_standard, df_v2, df_enhanced] if not df.empty]
        
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
            df = df.sort_values('training_date', ascending=False)
        else:
            df = pd.DataFrame()
        
        return df
        
    except Exception as e:
        st.error(f"Error loading model performance data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_model_files_info():
    """Load information about saved model files"""
    import os
    import json
    from pathlib import Path
    
    models_info = []
    models_dir = Path('data/ml_models/models')
    
    if not models_dir.exists():
        return pd.DataFrame()
    
    try:
        for symbol_dir in models_dir.iterdir():
            if symbol_dir.is_dir():
                symbol = symbol_dir.name
                metadata_file = symbol_dir / 'metadata.json'
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        # Count model files
                        model_files = list(symbol_dir.glob('*_model.pkl'))
                        
                        models_info.append({
                            'symbol': symbol,
                            'trained_at': metadata.get('trained_at', 'Unknown'),
                            'model_version': metadata.get('model_version', 'Unknown'),
                            'models_count': len(model_files),
                            'models': [f.stem.replace('_model', '') for f in model_files],
                            'performance': metadata.get('performance', {})
                        })
                    except Exception as e:
                        models_info.append({
                            'symbol': symbol,
                            'trained_at': 'Error reading metadata',
                            'model_version': 'Unknown',
                            'models_count': 0,
                            'models': [],
                            'performance': {}
                        })
        
        return pd.DataFrame(models_info)
    except Exception as e:
        # Don't show error since this is optional file-based data
        return pd.DataFrame()

def show_model_training_status():
    """Show model training status and metrics"""
    st.markdown('<h2 class="section-header">🧠 Model Training Status</h2>', unsafe_allow_html=True)
    
    # Load data
    performance_df = load_model_performance()
    models_info_df = load_model_files_info()
    
    # Check if we have any training data
    has_db_data = not performance_df.empty
    has_file_data = not models_info_df.empty
    
    if not has_db_data and not has_file_data:
        st.warning("⚠️ No model training data found")
        st.info("""
        **Possible reasons:**
        - Evening routine has not run model training yet
        - No models have been trained recently
        - Training pipeline may need to be executed
        
        **To generate training data:**
        1. Run the evening routine to train models and populate metrics
        2. Training data is automatically saved to trading_predictions.db
        3. Check the model_performance* tables in the main database
        """)
        
        # Show current database status
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Check each model performance table
                tables_info = []
                for table in ['model_performance', 'model_performance_enhanced', 'model_performance_v2']:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        tables_info.append(f"📊 {table}: {count} records")
                    except:
                        tables_info.append(f"❌ {table}: table not found")
                
                conn.close()
                st.markdown("**Current Database Status:**")
                for info in tables_info:
                    st.text(info)
        except:
            st.text("Could not check database status")
        
        return
    
    # Display training status overview
    st.markdown("### 📊 Training Status Overview")
    
    status_cols = st.columns(4)
    
    with status_cols[0]:
        if has_db_data:
            latest_training = pd.to_datetime(performance_df['training_date'].iloc[0]) if len(performance_df) > 0 else None
            if latest_training:
                days_since = (datetime.now() - latest_training).days
                st.metric("Last Training", f"{days_since} days ago", delta=latest_training.strftime('%m-%d %H:%M'))
            else:
                st.metric("Last Training", "No data")
        else:
            st.metric("Last Training", "Check files")
    
    with status_cols[1]:
        if has_file_data:
            total_models = models_info_df['models_count'].sum()
            st.metric("Total Models", total_models)
        else:
            st.metric("Total Models", "0")
    
    with status_cols[2]:
        if has_file_data:
            symbols_trained = len(models_info_df)
            st.metric("Symbols Trained", symbols_trained)
        else:
            st.metric("Symbols Trained", "0")
    
    with status_cols[3]:
        if has_db_data and len(performance_df) > 0:
            avg_accuracy = performance_df['validation_score'].mean()
            st.metric("Avg Validation Score", f"{avg_accuracy:.3f}")
        else:
            st.metric("Avg Validation Score", "N/A")
    
    # Tabs for different views
    if has_db_data or has_file_data:
        tabs = st.tabs(["📋 Recent Training", "🏢 Models by Symbol", "📈 Performance Trends", "🔧 Training Actions"])
        
        with tabs[0]:
            show_recent_training(performance_df, has_db_data)
        
        with tabs[1]:
            show_models_by_symbol(models_info_df, has_file_data)
        
        with tabs[2]:
            show_performance_trends(performance_df, has_db_data)
        
        with tabs[3]:
            show_training_actions()

def show_recent_training(performance_df, has_db_data):
    """Show recent training activity"""
    st.markdown("#### 📋 Recent Training Activity")
    
    if has_db_data and len(performance_df) > 0:
        # Display recent training records
        display_df = performance_df.copy()
        display_df['training_date'] = pd.to_datetime(display_df['training_date']).dt.strftime('%m-%d %H:%M')
        
        # Round numerical columns
        numeric_cols = ['validation_score', 'test_score', 'precision_score', 'recall_score']
        for col in numeric_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].round(3)
        
        st.dataframe(display_df.head(10), use_container_width=True)
        
        # Show parameters and feature importance for latest model
        if len(performance_df) > 0:
            latest = performance_df.iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ⚙️ Latest Model Parameters")
                if latest['parameters'] and latest['parameters'] != 'null':
                    try:
                        import json
                        params = json.loads(latest['parameters']) if isinstance(latest['parameters'], str) else latest['parameters']
                        st.json(params)
                    except:
                        st.text(str(latest['parameters']))
                else:
                    st.info("No parameters data available")
            
            with col2:
                st.markdown("#### 🎯 Feature Importance")
                if latest['feature_importance'] and latest['feature_importance'] != 'null':
                    try:
                        import json
                        importance = json.loads(latest['feature_importance']) if isinstance(latest['feature_importance'], str) else latest['feature_importance']
                        
                        if isinstance(importance, dict):
                            importance_df = pd.DataFrame(list(importance.items()), columns=['Feature', 'Importance'])
                            importance_df = importance_df.sort_values('Importance', ascending=False)
                            
                            fig = px.bar(importance_df.head(10), x='Importance', y='Feature', orientation='h',
                                       title="Top 10 Feature Importance")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.json(importance)
                    except:
                        st.text(str(latest['feature_importance']))
                else:
                    st.info("No feature importance data available")
    else:
        st.info("No database training records found. Check if evening routine has run and is saving to model_performance table.")

def show_models_by_symbol(models_info_df, has_file_data):
    """Show models organized by symbol"""
    st.markdown("#### 🏢 Models by Symbol")
    
    if has_file_data and len(models_info_df) > 0:
        for _, row in models_info_df.iterrows():
            with st.expander(f"📊 {row['symbol']} - {row['models_count']} models"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Model Details:**")
                    st.write(f"**Trained:** {row['trained_at']}")
                    st.write(f"**Version:** {row['model_version']}")
                    st.write(f"**Models:** {', '.join(row['models'])}")
                
                with col2:
                    st.markdown("**Performance:**")
                    if row['performance']:
                        perf = row['performance']
                        if isinstance(perf, dict):
                            for model_type, metrics in perf.items():
                                if isinstance(metrics, dict):
                                    st.write(f"**{model_type}:**")
                                    for metric, value in metrics.items():
                                        if isinstance(value, (int, float)):
                                            st.write(f"  • {metric}: {value:.3f}")
                                        else:
                                            st.write(f"  • {metric}: {value}")
                    else:
                        st.info("No performance data in metadata")
    else:
        st.info("No model files found. Check if models are being saved to data/ml_models/models/")

def show_performance_trends(performance_df, has_db_data):
    """Show performance trends over time"""
    st.markdown("#### 📈 Performance Trends")
    
    if has_db_data and len(performance_df) > 5:
        # Convert training_date to datetime
        performance_df['training_datetime'] = pd.to_datetime(performance_df['training_date'])
        
        # Create performance trend chart
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Validation Score Trend', 'Test Score Trend', 'Precision vs Recall', 'Model Type Distribution'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Validation score trend
        fig.add_trace(
            go.Scatter(
                x=performance_df['training_datetime'],
                y=performance_df['validation_score'],
                mode='lines+markers',
                name='Validation Score',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        
        # Test score trend
        fig.add_trace(
            go.Scatter(
                x=performance_df['training_datetime'],
                y=performance_df['test_score'],
                mode='lines+markers',
                name='Test Score',
                line=dict(color='green')
            ),
            row=1, col=2
        )
        
        # Precision vs Recall scatter
        fig.add_trace(
            go.Scatter(
                x=performance_df['precision_score'],
                y=performance_df['recall_score'],
                mode='markers',
                name='Precision vs Recall',
                marker=dict(color='red', size=8)
            ),
            row=2, col=1
        )
        
        # Model type distribution
        model_counts = performance_df['model_type'].value_counts()
        fig.add_trace(
            go.Bar(
                x=model_counts.index,
                y=model_counts.values,
                name='Model Types',
                marker_color='purple'
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=600, title_text="Model Performance Trends")
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("Need at least 5 training records to show trends. Current records: " + str(len(performance_df) if has_db_data else 0))

def show_training_actions():
    """Show training action buttons and utilities"""
    st.markdown("#### 🔧 Training Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Manual Training:**")
        if st.button("🔄 Trigger Evening Routine", type="primary"):
            with st.spinner("Running evening routine..."):
                try:
                    from app.services.daily_manager import TradingSystemManager
                    mgr = TradingSystemManager()
                    result = mgr.evening_routine()
                    if result:
                        st.success("✅ Evening routine completed successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Evening routine failed")
                except Exception as e:
                    st.error(f"❌ Error running evening routine: {e}")
        
        if st.button("🧠 Train Models Only"):
            with st.spinner("Training models..."):
                try:
                    from ml_training_pipeline import MLTrainingPipeline
                    pipeline = MLTrainingPipeline()
                    result = pipeline.train_all_models()
                    if result:
                        st.success("✅ Model training completed!")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Model training failed")
                except Exception as e:
                    st.error(f"❌ Error training models: {e}")
    
    with col2:
        st.markdown("**Database Actions:**")
        if st.button("📊 Populate Performance DB"):
            st.info("📊 Model performance data comes from the evening routine.")
            st.info("💡 Training metrics are automatically saved to trading_predictions.db when models are trained.")
            st.info("🔄 Run the evening routine to populate model training data.")
        
        if st.button("🔍 Validate Training Setup"):
            with st.spinner("Validating training setup..."):
                validation = validate_training_setup()
                
                st.markdown("**Validation Results:**")
                for check, status in validation.items():
                    icon = "✅" if status['status'] else "❌"
                    st.write(f"{icon} {check}: {status['message']}")

def populate_model_performance_db():
    """This function is no longer needed - data comes from evening routine"""
    return {'success': False, 'error': 'Data is populated automatically by evening routine'}

def validate_training_setup():
    """Validate that training setup is correct"""
    validation = {}
    
    # Check database
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM model_performance")
            count_std = cursor.fetchone()[0]
            try:
                cursor.execute("SELECT COUNT(*) FROM model_performance_enhanced")
                count_enh = cursor.fetchone()[0]
            except:
                count_enh = 0
            try:
                cursor.execute("SELECT COUNT(*) FROM model_performance_v2")
                count_v2 = cursor.fetchone()[0]
            except:
                count_v2 = 0
            conn.close()
            total_records = count_std + count_enh + count_v2
            validation['Database Connection'] = {'status': True, 'message': f'{total_records} total training records found'}
        else:
            validation['Database Connection'] = {'status': False, 'message': 'Cannot connect to trading_predictions.db'}
    except Exception as e:
        validation['Database Connection'] = {'status': False, 'message': str(e)}
    
    # Check models directory (optional)
    import os
    models_exist = os.path.exists('data/ml_models/models')
    validation['Models Directory'] = {'status': models_exist, 'message': 'Found' if models_exist else 'Optional - models can be stored in database only'}
    
    # Check training pipeline
    try:
        from ml_training_pipeline import MLTrainingPipeline
        validation['Training Pipeline'] = {'status': True, 'message': 'Import successful'}
    except Exception as e:
        validation['Training Pipeline'] = {'status': False, 'message': f'Import failed: {e}'}
    
    # Check evening routine
    try:
        from app.services.daily_manager import TradingSystemManager
        validation['Evening Routine'] = {'status': True, 'message': 'Import successful'}
    except Exception as e:
        validation['Evening Routine'] = {'status': False, 'message': f'Import failed: {e}'}
    
    return validation

if __name__ == "__main__":
    main()
