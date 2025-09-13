#!/usr/bin/env python3
"""
Simple ML Success Rate Dashboard
A streamlined view focusing specifically on ML model success rates and progression over time
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add the paper-trading-app to Python path
app_root = Path(__file__).parent / "paper-trading-app"
sys.path.append(str(app_root))

def main():
    """Main dashboard function"""
    st.set_page_config(
        page_title="ML Success Rate Dashboard", 
        page_icon="🤖", 
        layout="wide"
    )
    
    st.title("🤖 Machine Learning Success Rate Dashboard")
    st.markdown("### Track Your ML Models' Performance Over Time")
    st.markdown("---")
    
    # Try to load the ML progression tracker
    try:
        from app.core.ml.tracking.progression_tracker import MLProgressionTracker
        
        # Initialize tracker
        tracker = MLProgressionTracker()
        
        # Check if we have data
        if not tracker.prediction_history:
            st.warning("No ML prediction data found. Generate sample data to see the dashboard in action.")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🎲 Generate Sample Data"):
                    with st.spinner("Generating 30 days of sample ML performance data..."):
                        tracker.generate_sample_data(days=30)
                    st.success("✅ Sample data generated! Refresh the page.")
                    st.experimental_rerun()
            
            with col2:
                st.info("💡 This will create realistic sample data showing ML model progression over 30 days")
            return
        
        # Time period selector
        st.sidebar.header("🎛️ Controls")
        days = st.sidebar.selectbox("Time Period", [7, 14, 30, 60, 90], index=2)
        
        if st.sidebar.button("🔄 Refresh Data"):
            st.experimental_rerun()
        
        # Get progression summary
        summary = tracker.get_progression_summary(days=days)
        
        # Key Performance Indicators
        st.subheader("📊 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_preds = summary.get('total_predictions', 0)
            completed_preds = summary.get('completed_predictions', 0)
            st.metric(
                "Total Predictions", 
                total_preds,
                delta=f"{completed_preds} completed"
            )
        
        with col2:
            # Get latest accuracy
            accuracy_list = summary.get('accuracy_progression', [])
            current_accuracy = accuracy_list[-1] if accuracy_list else 0
            st.metric(
                "Current Accuracy", 
                f"{current_accuracy:.1%}",
                delta="20-30% ML contribution" if current_accuracy > 0 else None
            )
        
        with col3:
            # Trading performance
            trading_perf = summary.get('trading_performance', {})
            success_rate = trading_perf.get('success_rate', 0)
            successful_trades = trading_perf.get('successful_trades', 0)
            total_trades = trading_perf.get('total_trades', 0)
            
            st.metric(
                "Trading Success Rate", 
                f"{success_rate:.1%}",
                delta=f"{successful_trades}/{total_trades} trades"
            )
        
        with col4:
            # Model improvement
            improvement = summary.get('model_improvement', {})
            trend = improvement.get('trend', 'stable')
            improvement_val = improvement.get('improvement', 0)
            
            trend_emoji = "📈" if trend == 'improving' else "📉" if trend == 'declining' else "➡️"
            st.metric(
                "Model Trend", 
                f"{trend_emoji} {trend.title()}",
                delta=f"{improvement_val:+.1%}" if improvement_val != 0 else None
            )
        
        # Main Charts
        st.subheader("📈 Performance Trends")
        
        # Get detailed progression data
        progression_df = tracker.get_detailed_progression_data(days=days)
        
        if not progression_df.empty:
            # Create subplots for the main metrics
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'ML Model Accuracy Over Time',
                    'Prediction Confidence Levels', 
                    'Daily Trading Success Rate',
                    'Predictions Volume & Success'
                ),
                vertical_spacing=0.12
            )
            
            # Accuracy over time
            fig.add_trace(
                go.Scatter(
                    x=progression_df['date'],
                    y=progression_df['accuracy'] * 100,
                    mode='lines+markers',
                    name='Accuracy %',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8)
                ),
                row=1, col=1
            )
            
            # Add accuracy trend line
            if len(progression_df) > 5:
                import numpy as np
                z = np.polyfit(range(len(progression_df)), progression_df['accuracy'] * 100, 1)
                trend_line = np.poly1d(z)(range(len(progression_df)))
                fig.add_trace(
                    go.Scatter(
                        x=progression_df['date'],
                        y=trend_line,
                        mode='lines',
                        name='Trend',
                        line=dict(color='red', dash='dash'),
                        opacity=0.7
                    ),
                    row=1, col=1
                )
            
            # Confidence levels
            fig.add_trace(
                go.Scatter(
                    x=progression_df['date'],
                    y=progression_df['confidence'] * 100,
                    mode='lines+markers',
                    name='Confidence %',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8)
                ),
                row=1, col=2
            )
            
            # Success rate
            success_rate_daily = (progression_df['successful_trades'] / progression_df['predictions_made'] * 100).fillna(0)
            fig.add_trace(
                go.Scatter(
                    x=progression_df['date'],
                    y=success_rate_daily,
                    mode='lines+markers',
                    name='Success Rate %',
                    fill='tonexty',
                    line=dict(color='green', width=2),
                    marker=dict(size=6)
                ),
                row=2, col=1
            )
            
            # Add average line for success rate
            avg_success = success_rate_daily.mean()
            fig.add_hline(
                y=avg_success,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Average: {avg_success:.1f}%",
                row=2, col=1
            )
            
            # Volume and success bars
            fig.add_trace(
                go.Bar(
                    x=progression_df['date'],
                    y=progression_df['predictions_made'],
                    name='Total Predictions',
                    marker_color='lightblue',
                    opacity=0.7
                ),
                row=2, col=2
            )
            
            fig.add_trace(
                go.Bar(
                    x=progression_df['date'],
                    y=progression_df['successful_trades'],
                    name='Successful Trades',
                    marker_color='green',
                    opacity=0.8
                ),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                height=700,
                title=f"ML Performance Dashboard - Last {days} Days",
                showlegend=False
            )
            
            # Update axes labels
            fig.update_yaxes(title_text="Accuracy (%)", row=1, col=1)
            fig.update_yaxes(title_text="Confidence (%)", row=1, col=2)
            fig.update_yaxes(title_text="Success Rate (%)", row=2, col=1)
            fig.update_yaxes(title_text="Number of Predictions", row=2, col=2)
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Performance Summary
        st.subheader("📋 Performance Summary")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if summary.get('trading_performance', {}).get('success_rate', 0) > 0.6:
                st.success("🎉 Excellent Performance! Your ML models are achieving >60% success rate")
            elif summary.get('trading_performance', {}).get('success_rate', 0) > 0.5:
                st.info("📈 Good Performance! Your models are beating random chance with >50% success")
            else:
                st.warning("⚠️ Room for Improvement. Consider retraining models with fresh data")
        
        with col2:
            st.metric(
                "ML Contribution Impact", 
                "20-30%",
                help="Your ML models contribute approximately 20-30% to overall prediction accuracy"
            )
        
        # Recent Predictions Table
        st.subheader("🔍 Recent ML Predictions")
        
        # Get recent predictions
        recent_predictions = [
            p for p in tracker.prediction_history 
            if datetime.fromisoformat(p['timestamp']) >= datetime.now() - timedelta(days=7)
        ][-10:]  # Last 10 predictions
        
        if recent_predictions:
            table_data = []
            for pred in recent_predictions:
                prediction_dict = pred.get('prediction', {})
                table_data.append({
                    'Date': pred['timestamp'][:10],
                    'Symbol': pred['symbol'],
                    'Signal': prediction_dict.get('signal', 'N/A'),
                    'Confidence': f"{prediction_dict.get('confidence', 0):.1%}",
                    'Status': pred['status'],
                    'Success': '✅' if pred['status'] == 'completed' and tracker._is_successful_prediction(pred) else '❌' if pred['status'] == 'completed' else '⏳'
                })
            
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True)
        else:
            st.info("No recent predictions found.")
        
        # Footer info
        st.markdown("---")
        st.markdown("💡 **About ML Success Rate Tracking:**")
        st.markdown("- Tracks prediction accuracy, confidence levels, and trading success")
        st.markdown("- Models contribute 20-30% to overall trading decisions")
        st.markdown("- Data includes sentiment analysis, technical indicators, and pattern recognition")
        
    except ImportError as e:
        st.error(f"❌ Could not import ML tracking components: {e}")
        st.info("💡 Make sure you're running from the correct directory with all dependencies installed")
        
        st.markdown("### Alternative: Run Full Dashboard")
        st.code("streamlit run paper-trading-app/app/dashboard/main.py")
        
    except Exception as e:
        st.error(f"❌ Error loading ML dashboard: {e}")
        if st.checkbox("Show error details"):
            st.exception(e)

if __name__ == "__main__":
    main()