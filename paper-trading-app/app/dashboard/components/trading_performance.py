"""
Trading Performance Component for Enhanced Dashboard
Displays detailed performance metrics and historical tracking
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
from pathlib import Path

def display_trading_performance_log(ml_tracker=None, days_back: int = 30):
    """Display detailed trading performance log similar to professional dashboard"""
    st.header("📋 Detailed Performance Log")
    
    if not ml_tracker:
        st.warning("⚠️ ML tracker not available - performance data cannot be loaded")
        return
    
    try:
        # Get recent predictions from tracker
        recent_predictions = [
            p for p in ml_tracker.prediction_history 
            if datetime.fromisoformat(p['timestamp']) >= datetime.now() - timedelta(days=days_back)
        ]
        
        if not recent_predictions:
            st.info("📊 No recent trading predictions found")
            return
        
        # Create performance table data
        table_data = []
        for pred in recent_predictions[-50:]:  # Show last 50 predictions
            success_indicator = "⏳"  # Pending
            outcome_text = "Pending"
            
            if pred['status'] == 'completed':
                if ml_tracker._is_successful_prediction(pred):
                    success_indicator = "✅"
                else:
                    success_indicator = "❌"
                
                # Get outcome percentage - handle both dict and float formats
                outcome = pred.get('actual_outcome')
                if isinstance(outcome, dict):
                    price_change = outcome.get('price_change_percent', 0)
                    outcome_text = f"{price_change:+.2f}%"
                elif isinstance(outcome, (int, float)):
                    price_change = outcome * 100  # Convert decimal to percentage
                    outcome_text = f"{price_change:+.2f}%"
                elif outcome is None:
                    outcome_text = "No Data"
                else:
                    outcome_text = "Error"
            
            # Safely get sentiment score from either top level or prediction dict
            sentiment_score = 0
            if 'sentiment_score' in pred and isinstance(pred['sentiment_score'], (int, float)):
                sentiment_score = pred['sentiment_score']
            elif isinstance(pred.get('prediction'), dict) and 'sentiment_score' in pred['prediction']:
                sentiment_score = pred['prediction'].get('sentiment_score', 0)
            
            # Safely get signal from prediction dict or top level
            signal = 'N/A'
            if isinstance(pred.get('prediction'), dict):
                signal = pred['prediction'].get('signal', 'N/A')
            elif 'signal' in pred:
                signal = pred.get('signal', 'N/A')
            
            # Safely get confidence from prediction dict or top level
            confidence_text = "N/A"
            if isinstance(pred.get('prediction'), dict):
                confidence = pred['prediction'].get('confidence', 0)
                confidence_text = f"{confidence:.1%}"
            elif 'confidence' in pred:
                confidence = pred.get('confidence', 0)
                confidence_text = f"{confidence:.1%}"
            
            table_data.append({
                'Date': pred['timestamp'][:10],
                'Time': pred['timestamp'][11:16],
                'Symbol': pred['symbol'],
                'Signal': signal,
                'Confidence': confidence_text,
                'Sentiment': f"{sentiment_score:+.3f}",
                'Outcome': outcome_text,
                'Success': success_indicator,
                'Status': pred['status']
            })
        
        # Display the table
        df_performance = pd.DataFrame(table_data)
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            symbol_filter = st.selectbox(
                "Filter by Symbol", 
                ["All"] + list(df_performance['Symbol'].unique())
            )
        
        with col2:
            signal_filter = st.selectbox(
                "Filter by Signal",
                ["All"] + list(df_performance['Signal'].unique())
            )
        
        with col3:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "completed", "pending"]
            )
        
        # Apply filters
        filtered_df = df_performance.copy()
        
        if symbol_filter != "All":
            filtered_df = filtered_df[filtered_df['Symbol'] == symbol_filter]
        
        if signal_filter != "All":
            filtered_df = filtered_df[filtered_df['Signal'] == signal_filter]
        
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['Status'] == status_filter]
        
        # Display filtered table
        st.dataframe(
            filtered_df.drop('Status', axis=1),  # Hide status column for cleaner view
            use_container_width=True,
            height=400
        )
        
        # Performance summary metrics
        completed_predictions = [p for p in recent_predictions if p['status'] == 'completed']
        
        if completed_predictions:
            st.subheader("📊 Performance Summary")
            
            # Calculate success rate
            successful = sum(1 for p in completed_predictions if ml_tracker._is_successful_prediction(p))
            total = len(completed_predictions)
            success_rate = (successful / total) * 100 if total > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Success Rate", f"{success_rate:.1f}%", f"{successful}/{total}")
            
            with col2:
                # Calculate average confidence safely
                confidence_values = []
                for p in completed_predictions:
                    if isinstance(p.get('prediction'), dict):
                        confidence_values.append(p['prediction'].get('confidence', 0))
                    elif 'confidence' in p:
                        confidence_values.append(p.get('confidence', 0))
                
                avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
                st.metric("Avg Confidence", f"{avg_confidence:.1%}")
            
            with col3:
                # Count BUY signals safely
                buy_signals = 0
                for p in completed_predictions:
                    if isinstance(p.get('prediction'), dict):
                        if p['prediction'].get('signal') == 'BUY':
                            buy_signals += 1
                    elif p.get('signal') == 'BUY':
                        buy_signals += 1
                st.metric("Buy Signals", buy_signals)
            
            with col4:
                # Count SELL signals safely
                sell_signals = 0
                for p in completed_predictions:
                    if isinstance(p.get('prediction'), dict):
                        if p['prediction'].get('signal') == 'SELL':
                            sell_signals += 1
                    elif p.get('signal') == 'SELL':
                        sell_signals += 1
                st.metric("Sell Signals", sell_signals)
            
            # Performance by symbol chart
            symbol_performance = {}
            for pred in completed_predictions:
                symbol = pred['symbol']
                if symbol not in symbol_performance:
                    symbol_performance[symbol] = {'successful': 0, 'total': 0}
                
                symbol_performance[symbol]['total'] += 1
                if ml_tracker._is_successful_prediction(pred):
                    symbol_performance[symbol]['successful'] += 1
            
            # Create performance chart
            symbols = list(symbol_performance.keys())
            success_rates = [
                (symbol_performance[symbol]['successful'] / symbol_performance[symbol]['total']) * 100
                for symbol in symbols
            ]
            
            fig_performance = px.bar(
                x=symbols,
                y=success_rates,
                title="Success Rate by Symbol",
                labels={'x': 'Symbol', 'y': 'Success Rate (%)'},
                color=success_rates,
                color_continuous_scale='RdYlGn'
            )
            
            fig_performance.update_layout(height=400)
            st.plotly_chart(fig_performance, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error displaying performance log: {e}")


def display_ml_learning_metrics(ml_tracker=None):
    """Display comprehensive ML learning and improvement metrics"""
    st.header("🧠 Machine Learning Performance Analysis")
    
    if not ml_tracker:
        st.warning("⚠️ ML tracker not available")
        return
    
    try:
        # Get comprehensive data
        performance_data = ml_tracker.performance_history
        model_metrics = ml_tracker.model_metrics_history
        predictions = ml_tracker.prediction_history
        
        if not performance_data:
            st.info("📊 No performance history available")
            return
        
        # === ACCURACY & CONFIDENCE PROGRESSION ===
        st.subheader("📈 Accuracy & Confidence Progression")
        
        # Create detailed progression charts
        dates = [entry['date'] for entry in performance_data[-30:]]  # Last 30 days
        accuracies = [entry.get('accuracy_metrics', {}).get('accuracy', 0) * 100 for entry in performance_data[-30:]]
        confidences = [entry.get('model_confidence', 0) * 100 for entry in performance_data[-30:]]
        success_rates = [(entry['successful_trades'] / entry['total_trades']) * 100 if entry['total_trades'] > 0 else 0 for entry in performance_data[-30:]]
        predictions_count = [entry.get('predictions_made', 0) for entry in performance_data[-30:]]
        
        # Multi-metric progression chart
        fig_progression = go.Figure()
        
        fig_progression.add_trace(go.Scatter(
            x=dates, y=accuracies,
            mode='lines+markers',
            name='Prediction Accuracy',
            line=dict(color='#2E8B57', width=3),
            marker=dict(size=8)
        ))
        
        fig_progression.add_trace(go.Scatter(
            x=dates, y=success_rates,
            mode='lines+markers',
            name='Trading Success Rate',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=6)
        ))
        
        fig_progression.add_trace(go.Scatter(
            x=dates, y=confidences,
            mode='lines+markers',
            name='Model Confidence',
            line=dict(color='#4ECDC4', width=2, dash='dash'),
            marker=dict(size=4),
            yaxis='y2'
        ))
        
        fig_progression.update_layout(
            title='📊 ML Performance Progression (30 Days)',
            xaxis_title='Date',
            yaxis_title='Accuracy & Success Rate (%)',
            yaxis2=dict(
                title='Model Confidence (%)',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            height=450,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_progression, use_container_width=True)
        
        # Key metrics cards
        col1, col2, col3, col4 = st.columns(4)
        
        if performance_data:
            latest = performance_data[-1]
            
            with col1:
                latest_accuracy = latest.get('accuracy_metrics', {}).get('accuracy', 0) * 100
                prev_accuracy = performance_data[-2].get('accuracy_metrics', {}).get('accuracy', 0) * 100 if len(performance_data) > 1 else latest_accuracy
                accuracy_delta = latest_accuracy - prev_accuracy
                st.metric("Current Accuracy", f"{latest_accuracy:.1f}%", f"{accuracy_delta:+.1f}%")
            
            with col2:
                success_rate = (latest['successful_trades'] / latest['total_trades']) * 100 if latest['total_trades'] > 0 else 0
                prev_success = (performance_data[-2]['successful_trades'] / performance_data[-2]['total_trades']) * 100 if len(performance_data) > 1 and performance_data[-2]['total_trades'] > 0 else success_rate
                success_delta = success_rate - prev_success
                st.metric("Success Rate", f"{success_rate:.1f}%", f"{success_delta:+.1f}%")
            
            with col3:
                model_conf = latest.get('model_confidence', 0) * 100
                prev_conf = performance_data[-2].get('model_confidence', 0) * 100 if len(performance_data) > 1 else model_conf
                conf_delta = model_conf - prev_conf
                st.metric("Model Confidence", f"{model_conf:.1f}%", f"{conf_delta:+.1f}%")
            
            with col4:
                total_predictions = sum(entry.get('predictions_made', 0) for entry in performance_data[-7:])  # Last 7 days
                st.metric("7-Day Predictions", total_predictions)
        
        # === MODEL TRAINING PROGRESS ===
        st.subheader("🎯 Model Training Progress")
        
        if model_metrics:
            training_dates = [entry['timestamp'][:10] for entry in model_metrics[-20:]]  # Last 20 training sessions
            validation_accuracies = [entry.get('validation_accuracy', 0) * 100 for entry in model_metrics[-20:]]
            training_samples = [entry.get('training_samples', 0) for entry in model_metrics[-20:]]
            cross_val_scores = [entry.get('cross_validation_score', 0) * 100 for entry in model_metrics[-20:]]
            
            # Training progress chart
            fig_training = go.Figure()
            
            fig_training.add_trace(go.Scatter(
                x=training_dates, y=validation_accuracies,
                mode='lines+markers',
                name='Validation Accuracy',
                line=dict(color='#9B59B6', width=3),
                marker=dict(size=8)
            ))
            
            fig_training.add_trace(go.Scatter(
                x=training_dates, y=cross_val_scores,
                mode='lines+markers',
                name='Cross-Validation Score',
                line=dict(color='#E67E22', width=2),
                marker=dict(size=6)
            ))
            
            fig_training.add_trace(go.Bar(
                x=training_dates, y=training_samples,
                name='Training Samples',
                yaxis='y2',
                opacity=0.3,
                marker_color='lightblue'
            ))
            
            fig_training.update_layout(
                title='🔄 Model Training Evolution',
                xaxis_title='Training Date',
                yaxis_title='Accuracy (%)',
                yaxis2=dict(
                    title='Training Samples',
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                height=400
            )
            
            st.plotly_chart(fig_training, use_container_width=True)
            
            # Training metrics
            col1, col2, col3 = st.columns(3)
            
            latest_model = model_metrics[-1] if model_metrics else {}
            
            with col1:
                val_acc = latest_model.get('validation_accuracy', 0) * 100
                st.metric("Latest Validation Accuracy", f"{val_acc:.2f}%")
            
            with col2:
                cv_score = latest_model.get('cross_validation_score', 0) * 100
                st.metric("Cross-Validation Score", f"{cv_score:.2f}%")
            
            with col3:
                samples = latest_model.get('training_samples', 0)
                st.metric("Training Samples", f"{samples:,}")
        
        # === TRADING PERFORMANCE ANALYSIS ===
        st.subheader("💹 Trading Performance Analysis")
        
        # Performance analysis by time periods
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Performance Breakdown**")
            
            # Calculate performance metrics
            total_trades = sum(entry['total_trades'] for entry in performance_data)
            successful_trades = sum(entry['successful_trades'] for entry in performance_data)
            overall_success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Recent vs historical comparison
            recent_data = performance_data[-7:]  # Last 7 days
            recent_trades = sum(entry['total_trades'] for entry in recent_data)
            recent_successful = sum(entry['successful_trades'] for entry in recent_data)
            recent_success_rate = (recent_successful / recent_trades * 100) if recent_trades > 0 else 0
            
            st.metric("Overall Success Rate", f"{overall_success_rate:.1f}%")
            st.metric("Recent (7d) Success Rate", f"{recent_success_rate:.1f}%", f"{recent_success_rate - overall_success_rate:+.1f}%")
            st.metric("Total Trades", f"{total_trades:,}")
            st.metric("Total Successful", f"{successful_trades:,}")
        
        with col2:
            st.markdown("**📈 Performance Trends**")
            
            # Calculate trends
            if len(performance_data) >= 14:
                week1_data = performance_data[-14:-7]
                week2_data = performance_data[-7:]
                
                week1_success = sum(e['successful_trades'] for e in week1_data) / sum(e['total_trades'] for e in week1_data) * 100 if sum(e['total_trades'] for e in week1_data) > 0 else 0
                week2_success = sum(e['successful_trades'] for e in week2_data) / sum(e['total_trades'] for e in week2_data) * 100 if sum(e['total_trades'] for e in week2_data) > 0 else 0
                
                trend_direction = "📈 Improving" if week2_success > week1_success else "📉 Declining" if week2_success < week1_success else "➡️ Stable"
                st.metric("Weekly Trend", trend_direction)
                st.metric("Week-over-Week Change", f"{week2_success - week1_success:+.1f}%")
            
            # Average confidence trend
            avg_confidence = sum(entry.get('model_confidence', 0) for entry in performance_data[-7:]) / len(performance_data[-7:]) if performance_data else 0
            st.metric("Avg Model Confidence", f"{avg_confidence:.1%}")
        
        # === DETAILED PERFORMANCE LOG ===
        st.subheader("📋 Detailed Performance Log")
        
        # Create detailed performance table
        if performance_data:
            log_data = []
            for entry in performance_data[-14:]:  # Last 14 days
                log_data.append({
                    'Date': entry['date'],
                    'Predictions': entry.get('predictions_made', 0),
                    'Total Trades': entry['total_trades'],
                    'Successful': entry['successful_trades'],
                    'Success Rate': f"{(entry['successful_trades'] / entry['total_trades'] * 100) if entry['total_trades'] > 0 else 0:.1f}%",
                    'Accuracy': f"{entry.get('accuracy_metrics', {}).get('accuracy', 0) * 100:.1f}%",
                    'Model Confidence': f"{entry.get('model_confidence', 0) * 100:.1f}%"
                })
            
            df_log = pd.DataFrame(log_data)
            st.dataframe(df_log, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error displaying ML learning metrics: {e}")
        st.exception(e)


def display_trading_signals_vs_outcomes():
    """Compare trading signals with actual outcomes"""
    st.header("🎯 Signals vs Outcomes Analysis")
    
    # This would analyze how well BUY/SELL signals performed
    # vs actual price movements
    
    st.info("📊 Signal effectiveness analysis would go here")
    # Implementation would load actual trading data and compare
    # signal predictions with real market outcomes


def enhanced_dashboard_performance_section(ml_tracker=None):
    """Complete performance section for enhanced dashboard"""
    
    # Create tabs for different performance views
    tab1, tab2, tab3 = st.tabs(["📋 Performance Log", "🧠 Learning Metrics", "🎯 Signal Analysis"])
    
    with tab1:
        display_trading_performance_log(ml_tracker)
    
    with tab2:
        display_ml_learning_metrics(ml_tracker)
    
    with tab3:
        display_trading_signals_vs_outcomes()
