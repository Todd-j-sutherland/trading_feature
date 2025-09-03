"""
ML Progression Dashboard Component
Displays historical ML performance progression in the professional dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import logging

# Import the progression tracker
try:
    from app.core.ml.tracking.progression_tracker import MLProgressionTracker
    ML_TRACKING_AVAILABLE = True
except ImportError:
    ML_TRACKING_AVAILABLE = False
    st.warning("ML Progression Tracker not available")

logger = logging.getLogger(__name__)

def render_ml_progression_dashboard():
    """Render the ML progression dashboard section"""
    
    st.header("🤖 Machine Learning Performance Progression")
    
    if not ML_TRACKING_AVAILABLE:
        st.error("ML Progression Tracker is not available. Please check your installation.")
        return
    
    try:
        # Initialize tracker
        tracker = MLProgressionTracker()
        
        # Check if we have data
        if not tracker.prediction_history and not tracker.performance_history:
            st.info("No ML progression data available yet. The system will start collecting data as you use the morning and evening routines.")
            
            # Offer to generate sample data for demonstration
            if st.button("Generate Sample Data for Testing"):
                with st.spinner("Generating sample ML progression data..."):
                    tracker.generate_sample_data(days=30)
                    st.success("Sample data generated! Refresh the page to see the progression charts.")
                    st.rerun()
            return
        
        # Time period selector
        col1, col2 = st.columns([3, 1])
        with col2:
            days = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=2, key="ml_progression_time_period")
        
        # Get progression data
        progression_summary = tracker.get_progression_summary(days=days)
        progression_df = tracker.get_detailed_progression_data(days=days)
        
        # Check if progression_summary has enough data
        if not progression_summary or 'total_predictions' not in progression_summary or 'trading_performance' not in progression_summary:
            st.info("ML progression data is still being collected. Please check back after a few trading cycles.")
            if st.button("Generate Sample Data for Demo"):
                with st.spinner("Generating sample ML progression data..."):
                    tracker.generate_sample_data(days=30)
                    st.success("Sample data generated! Refresh the page to see the progression charts.")
                    st.rerun()
            return

        # Display summary metrics
        st.subheader("📊 Performance Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Predictions", 
                progression_summary.get('total_predictions', 'N/A'),
                delta=f"{progression_summary.get('completed_predictions', 'N/A')} completed"
            )
        
        with col2:
            accuracy_list = progression_summary.get('accuracy_progression', [])
            accuracy = accuracy_list[-1] if accuracy_list else 0
            trend_analysis = progression_summary.get('trend_analysis', {})
            st.metric(
                "Current Accuracy", 
                f"{accuracy:.1%}",
                delta=f"{trend_analysis.get('trend', 'N/A')}"
            )
        
        with col3:
            confidence_list = progression_summary.get('confidence_progression', [])
            confidence = confidence_list[-1] if confidence_list else 0
            trading_performance = progression_summary.get('trading_performance', {})
            st.metric(
                "Average Confidence", 
                f"{confidence:.1%}",
                delta=f"{trading_performance.get('average_confidence', 0):.1%} overall"
            )
        
        with col4:
            trading_performance = progression_summary.get('trading_performance', {})
            success_rate = trading_performance.get('success_rate', 0)
            st.metric(
                "Success Rate", 
                f"{success_rate:.1%}",
                delta=f"{trading_performance.get('successful_trades', 'N/A')}/{trading_performance.get('total_trades', 'N/A')} trades"
            )
        
        # Accuracy and Confidence Progression Chart
        st.subheader("📈 Accuracy & Confidence Progression")
        
        if not progression_df.empty:
            fig_progression = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Prediction Accuracy Over Time', 'Model Confidence Over Time'),
                vertical_spacing=0.1
            )
            
            # Accuracy progression
            fig_progression.add_trace(
                go.Scatter(
                    x=progression_df['date'],
                    y=progression_df['accuracy'] * 100,
                    mode='lines+markers',
                    name='Accuracy %',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=6)
                ),
                row=1, col=1
            )
            
            # Add trend line for accuracy
            if len(progression_df) > 5:
                z = np.polyfit(range(len(progression_df)), progression_df['accuracy'] * 100, 1)
                trend_line = np.poly1d(z)(range(len(progression_df)))
                fig_progression.add_trace(
                    go.Scatter(
                        x=progression_df['date'],
                        y=trend_line,
                        mode='lines',
                        name='Accuracy Trend',
                        line=dict(color='red', dash='dash'),
                        opacity=0.7
                    ),
                    row=1, col=1
                )
            
            # Confidence progression
            fig_progression.add_trace(
                go.Scatter(
                    x=progression_df['date'],
                    y=progression_df['confidence'] * 100,
                    mode='lines+markers',
                    name='Confidence %',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=6)
                ),
                row=2, col=1
            )
            
            # Add model confidence
            fig_progression.add_trace(
                go.Scatter(
                    x=progression_df['date'],
                    y=progression_df['model_confidence'] * 100,
                    mode='lines',
                    name='Model Confidence %',
                    line=dict(color='green', dash='dot'),
                    opacity=0.7
                ),
                row=2, col=1
            )
            
            fig_progression.update_layout(
                height=600,
                title="ML Performance Progression",
                showlegend=True
            )
            
            fig_progression.update_xaxes(title_text="Date", row=2, col=1)
            fig_progression.update_yaxes(title_text="Accuracy (%)", row=1, col=1)
            fig_progression.update_yaxes(title_text="Confidence (%)", row=2, col=1)
            
            st.plotly_chart(fig_progression, use_container_width=True)
        
        # Trading Performance Chart
        st.subheader("💹 Trading Performance Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Success rate over time
            if not progression_df.empty:
                fig_success = go.Figure()
                
                success_rate_pct = (progression_df['successful_trades'] / progression_df['predictions_made'] * 100).fillna(0)
                
                fig_success.add_trace(
                    go.Scatter(
                        x=progression_df['date'],
                        y=success_rate_pct,
                        mode='lines+markers',
                        name='Daily Success Rate',
                        fill='tonexty',
                        line=dict(color='green', width=2),
                        marker=dict(size=4)
                    )
                )
                
                fig_success.add_hline(
                    y=success_rate_pct.mean(),
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Average: {success_rate_pct.mean():.1f}%"
                )
                
                fig_success.update_layout(
                    title="Daily Success Rate",
                    xaxis_title="Date",
                    yaxis_title="Success Rate (%)",
                    height=400
                )
                
                st.plotly_chart(fig_success, use_container_width=True)
        
        with col2:
            # Predictions volume over time
            if not progression_df.empty:
                fig_volume = go.Figure()
                
                fig_volume.add_trace(
                    go.Bar(
                        x=progression_df['date'],
                        y=progression_df['predictions_made'],
                        name='Predictions Made',
                        marker_color='lightblue'
                    )
                )
                
                fig_volume.add_trace(
                    go.Bar(
                        x=progression_df['date'],
                        y=progression_df['successful_trades'],
                        name='Successful Trades',
                        marker_color='green'
                    )
                )
                
                fig_volume.update_layout(
                    title="Trading Volume & Success",
                    xaxis_title="Date",
                    yaxis_title="Number of Trades",
                    height=400,
                    barmode='overlay'
                )
                
                st.plotly_chart(fig_volume, use_container_width=True)
        
        # Model Training Progress
        st.subheader("🧠 Model Training Progress")
        
        if not progression_df.empty and 'training_samples' in progression_df.columns:
            fig_training = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Training Samples Growth', 'Learning Curve'),
                specs=[[{"secondary_y": False}, {"secondary_y": True}]]
            )
            
            # Training samples over time
            fig_training.add_trace(
                go.Scatter(
                    x=progression_df['date'],
                    y=progression_df['training_samples'],
                    mode='lines+markers',
                    name='Training Samples',
                    line=dict(color='purple', width=3),
                    marker=dict(size=6)
                ),
                row=1, col=1
            )
            
            # Learning curve (accuracy vs training samples)
            if len(progression_df) > 1:
                fig_training.add_trace(
                    go.Scatter(
                        x=progression_df['training_samples'],
                        y=progression_df['accuracy'] * 100,
                        mode='markers+lines',
                        name='Learning Curve',
                        line=dict(color='orange', width=2),
                        marker=dict(size=8, color=progression_df['confidence'], 
                                  colorscale='Viridis', showscale=True,
                                  colorbar=dict(title="Confidence"))
                    ),
                    row=1, col=2
                )
            
            fig_training.update_layout(
                height=400,
                title="Model Training Progress"
            )
            
            fig_training.update_xaxes(title_text="Date", row=1, col=1)
            fig_training.update_xaxes(title_text="Training Samples", row=1, col=2)
            fig_training.update_yaxes(title_text="Samples Count", row=1, col=1)
            fig_training.update_yaxes(title_text="Accuracy (%)", row=1, col=2)
            
            st.plotly_chart(fig_training, use_container_width=True)
        
        # Detailed Performance Table
        st.subheader("📋 Detailed Performance Log")
        
        # Display recent predictions
        recent_predictions = [
            p for p in tracker.prediction_history 
            if datetime.fromisoformat(p['timestamp']) >= datetime.now() - timedelta(days=days)
        ]
        
        if recent_predictions:
            # Create table data
            table_data = []
            for pred in recent_predictions[-20:]:  # Show last 20 predictions
                # Safely get sentiment score from either top level or prediction dict
                sentiment_score = 0
                if 'sentiment_score' in pred and isinstance(pred['sentiment_score'], (int, float)):
                    sentiment_score = pred['sentiment_score']
                elif isinstance(pred.get('prediction'), dict) and 'sentiment_score' in pred['prediction']:
                    sentiment_score = pred['prediction'].get('sentiment_score', 0)
                
                # Safely get outcome value
                outcome_text = 'Pending'
                if 'actual_outcome' in pred:
                    outcome = pred['actual_outcome']
                    if isinstance(outcome, dict):
                        # If it's a dictionary, try to get price_change_percent
                        price_change = outcome.get('price_change_percent', 0)
                        outcome_text = f"{price_change:.2f}%"
                    elif isinstance(outcome, (int, float)):
                        # If it's a number, use it directly (convert to percentage)
                        outcome_text = f"{outcome * 100:.2f}%"
                
                table_data.append({
                    'Date': pred['timestamp'][:10],
                    'Time': pred['timestamp'][11:16],
                    'Symbol': pred['symbol'],
                    'Signal': pred['prediction'].get('signal', 'N/A') if isinstance(pred.get('prediction'), dict) else 'N/A',
                    'Confidence': f"{pred['prediction'].get('confidence', 0):.1%}" if isinstance(pred.get('prediction'), dict) else "N/A",
                    'Sentiment': f"{sentiment_score:.3f}",
                    'Status': pred['status'],
                    'Outcome': outcome_text,
                    'Success': '✅' if pred['status'] == 'completed' and tracker._is_successful_prediction(pred) else '❌' if pred['status'] == 'completed' else '⏳'
                })
            
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True, height=400)
        
        # Model Improvement Analysis
        if progression_summary['model_improvement']['trend'] != 'insufficient_data':
            st.subheader("🔬 Model Improvement Analysis")
            
            improvement = progression_summary['model_improvement']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                trend_color = "green" if improvement['trend'] == 'improving' else "red" if improvement['trend'] == 'declining' else "gray"
                st.markdown(f"**Trend:** <span style='color: {trend_color}'>{improvement['trend'].title()}</span>", unsafe_allow_html=True)
            
            with col2:
                st.metric("Accuracy Improvement", f"{improvement['improvement']:+.1%}")
            
            with col3:
                st.metric("Training Sessions", improvement['total_training_sessions'])
            
            # Recommendations
            st.subheader("💡 Recommendations")
            
            if improvement['trend'] == 'improving':
                st.success("🎉 Your ML models are improving! Continue with current strategy.")
            elif improvement['trend'] == 'declining':
                st.warning("⚠️ Model performance is declining. Consider retraining with fresh data or adjusting parameters.")
            else:
                st.info("📊 Model performance is stable. Monitor for continued consistency.")
            
            # Additional insights
            if progression_summary['trading_performance']['success_rate'] > 0.6:
                st.success("✅ Trading success rate is above 60% - excellent performance!")
            elif progression_summary['trading_performance']['success_rate'] > 0.5:
                st.info("📈 Trading success rate is above 50% - good performance with room for improvement.")
            else:
                st.error("📉 Trading success rate is below 50% - consider reviewing strategy or retraining models.")
    
    except Exception as e:
        logger.error(f"Error rendering ML progression dashboard: {e}")
        st.error(f"Error loading ML progression data: {e}")
        
        # Show error details in development
        if st.checkbox("Show error details"):
            st.exception(e)

def render_ml_progression_sidebar():
    """Render ML progression summary in sidebar"""
    
    if not ML_TRACKING_AVAILABLE:
        return
    
    try:
        tracker = MLProgressionTracker()
        
        if tracker.prediction_history:
            st.sidebar.markdown("### 🤖 ML Performance")
            
            # Quick stats
            recent_accuracy = tracker._calculate_recent_accuracy(days=7)
            
            st.sidebar.metric(
                "7-Day Accuracy", 
                f"{recent_accuracy['accuracy']:.1%}",
                delta=f"{recent_accuracy['total_predictions']} predictions"
            )
            
            # Recent predictions count
            today_predictions = len([
                p for p in tracker.prediction_history 
                if p['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))
            ])
            
            st.sidebar.metric("Today's Predictions", today_predictions)
            
            # Model status
            if recent_accuracy['accuracy'] > 0.6:
                st.sidebar.success("Models performing well")
            elif recent_accuracy['accuracy'] > 0.5:
                st.sidebar.info("Models stable")
            else:
                st.sidebar.warning("Models need attention")
    
    except Exception as e:
        logger.error(f"Error rendering ML progression sidebar: {e}")

# Export the functions for use in the main dashboard
__all__ = ['render_ml_progression_dashboard', 'render_ml_progression_sidebar']
