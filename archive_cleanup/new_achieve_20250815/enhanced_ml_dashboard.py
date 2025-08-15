#!/usr/bin/env python3
"""
Updated ML Dashboard to use Enhanced Features Tables
This corrects the database alignment issue by using the right tables
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Enhanced ML Trading Dashboard", layout="wide")

# Database connection
def get_db_connection():
    return sqlite3.connect('data/trading_predictions.db')

# Updated data loading functions to use enhanced tables
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_enhanced_features():
    """Load data from enhanced_features table"""
    conn = get_db_connection()
    query = """
    SELECT * FROM enhanced_features 
    ORDER BY timestamp DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def load_enhanced_outcomes():
    """Load data from enhanced_outcomes table"""
    conn = get_db_connection()
    query = """
    SELECT eo.*, ef.symbol
    FROM enhanced_outcomes eo
    JOIN enhanced_features ef ON eo.feature_id = ef.id
    ORDER BY eo.created_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def load_predictions():
    """Load predictions with non-zero entry prices"""
    conn = get_db_connection()
    query = """
    SELECT * FROM predictions 
    WHERE entry_price > 0
    ORDER BY created_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    st.title("🤖 Enhanced ML Trading Dashboard")
    st.markdown("*Real-time ML predictions with enhanced feature engineering*")
    
    # Load data from enhanced tables
    try:
        features_df = load_enhanced_features()
        outcomes_df = load_enhanced_outcomes()
        predictions_df = load_predictions()
        
        # Data validation
        st.sidebar.markdown("### 📊 Data Status")
        
        # Enhanced features data
        total_features = len(features_df)
        recent_features = len(features_df[features_df['timestamp'] > (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')])
        
        st.sidebar.metric("Total Enhanced Features", total_features)
        st.sidebar.metric("Recent Features (24h)", recent_features)
        
        # Predictions data
        total_predictions = len(predictions_df)
        valid_predictions = len(predictions_df[predictions_df['entry_price'] > 0])
        zero_entry_prices = len(predictions_df[predictions_df['entry_price'] <= 0])
        
        st.sidebar.metric("Total Predictions", total_predictions)
        st.sidebar.metric("Valid Entry Prices", valid_predictions)
        
        if zero_entry_prices > 0:
            st.sidebar.error(f"⚠️ {zero_entry_prices} predictions with zero entry prices!")
        else:
            st.sidebar.success("✅ All predictions have valid entry prices!")
        
        # Enhanced outcomes data
        total_outcomes = len(outcomes_df)
        recent_outcomes = len(outcomes_df[outcomes_df['created_at'] > (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')])
        
        st.sidebar.metric("Total Enhanced Outcomes", total_outcomes)
        st.sidebar.metric("Recent Outcomes (24h)", recent_outcomes)
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Enhanced Features", total_features)
        with col2:
            st.metric("📈 Valid Predictions", valid_predictions)
        with col3:
            st.metric("📊 Enhanced Outcomes", total_outcomes)
        with col4:
            # Calculate consistency
            if total_features > 0 and total_outcomes > 0:
                consistency = min(total_features, total_outcomes) / max(total_features, total_outcomes) * 100
                st.metric("🎯 Data Consistency", f"{consistency:.1f}%")
            else:
                st.metric("🎯 Data Consistency", "N/A")
        
        # Recent data analysis
        if recent_features > 0:
            st.success(f"✅ Fresh data detected: {recent_features} enhanced features in last 24h")
            
            # Show recent predictions if available
            if total_predictions > 0:
                st.subheader("📈 Recent ML Predictions")
                
                # Display recent predictions table
                display_df = predictions_df.head(10)[['symbol', 'predicted_action', 'action_confidence', 'entry_price', 'created_at']]
                display_df['action_confidence'] = display_df['action_confidence'].round(3)
                display_df['entry_price'] = display_df['entry_price'].round(2)
                
                st.dataframe(display_df, use_container_width=True)
                
                # Action distribution
                action_counts = predictions_df['predicted_action'].value_counts()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Action Distribution")
                    fig = px.pie(values=action_counts.values, names=action_counts.index, 
                               title="Predicted Actions")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("💰 Entry Price Analysis")
                    if len(predictions_df[predictions_df['entry_price'] > 0]) > 0:
                        price_df = predictions_df[predictions_df['entry_price'] > 0]
                        fig = px.histogram(price_df, x='entry_price', nbins=20,
                                         title="Entry Price Distribution")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No valid entry prices found")
            
            # Enhanced features analysis
            if total_features > 0:
                st.subheader("🔬 Enhanced Features Analysis")
                
                # Recent features by symbol
                recent_features_df = features_df[features_df['timestamp'] > (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')]
                
                if len(recent_features_df) > 0:
                    symbol_counts = recent_features_df['symbol'].value_counts()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Recent Analysis by Symbol:**")
                        for symbol, count in symbol_counts.items():
                            st.write(f"- {symbol}: {count} analyses")
                    
                    with col2:
                        # Sentiment score distribution
                        if 'sentiment_score' in recent_features_df.columns:
                            avg_sentiment = recent_features_df['sentiment_score'].mean()
                            st.metric("Average Sentiment", f"{avg_sentiment:.3f}")
                        
                        if 'confidence' in recent_features_df.columns:
                            avg_confidence = recent_features_df['confidence'].mean()
                            st.metric("Average Confidence", f"{avg_confidence:.3f}")
                
                # Feature correlation heatmap
                numeric_cols = features_df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 5:
                    st.subheader("🔗 Feature Correlations")
                    
                    # Select key features for correlation
                    key_features = ['sentiment_score', 'confidence', 'current_price', 'rsi', 'volume']
                    available_features = [col for col in key_features if col in numeric_cols]
                    
                    if len(available_features) > 2:
                        corr_matrix = features_df[available_features].corr()
                        
                        fig = px.imshow(corr_matrix, 
                                      text_auto=True, 
                                      aspect="auto",
                                      title="Feature Correlation Matrix")
                        st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("⚠️ No recent enhanced features found. Run the enhanced morning analyzer to generate fresh data.")
            
            # Still show existing data if available
            if total_predictions > 0:
                st.info(f"📊 Showing historical data: {total_predictions} predictions available")
                
                display_df = predictions_df.head(10)[['symbol', 'predicted_action', 'action_confidence', 'entry_price', 'created_at']]
                display_df['action_confidence'] = display_df['action_confidence'].round(3)
                display_df['entry_price'] = display_df['entry_price'].round(2)
                
                st.dataframe(display_df, use_container_width=True)
        
        # Database connectivity test
        st.sidebar.markdown("### 🔧 System Status")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM enhanced_features")
            total_enhanced = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM predictions WHERE entry_price > 0")
            valid_preds = cursor.fetchone()[0]
            conn.close()
            
            st.sidebar.success("✅ Database connected")
            st.sidebar.info(f"Enhanced features: {total_enhanced}")
            st.sidebar.info(f"Valid predictions: {valid_preds}")
            
        except Exception as e:
            st.sidebar.error(f"❌ Database error: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please ensure the enhanced morning analyzer has been run to populate the enhanced_features table.")

if __name__ == "__main__":
    main()
