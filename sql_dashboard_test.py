#!/usr/bin/env python3
"""
Remote SQL Dashboard Test
Tests the SQL-first dashboard approach on the remote server
"""

import sys
sys.path.append('/root/test')

import streamlit as st
from sql_data_manager import DashboardDataManagerSQL
import pandas as pd

def main():
    st.set_page_config(page_title="SQL Dashboard Test", layout="wide")
    
    st.title("🔍 SQL-First Dashboard Test")
    st.markdown("Testing direct SQL integration vs JSON files")
    
    # Initialize SQL data manager
    try:
        sql_manager = DashboardDataManagerSQL()
        st.success("✅ SQL Data Manager initialized successfully")
    except Exception as e:
        st.error(f"❌ SQL initialization failed: {e}")
        return
    
    # Get data quality report
    st.header("📊 Data Quality Report")
    
    try:
        quality_report = sql_manager.get_data_quality_report()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Records", 
                quality_report["database_stats"]["total_records"]
            )
        
        with col2:
            st.metric(
                "Today's Records",
                quality_report["database_stats"]["today_records"]
            )
        
        with col3:
            st.metric(
                "Data Quality",
                quality_report["confidence_analysis"]["quality_score"]
            )
        
        # Recent predictions
        st.header("📈 Recent Predictions (SQL Source)")
        
        predictions = sql_manager.get_prediction_log(days_back=1)
        
        if predictions:
            # Convert to display format
            display_data = []
            for pred in predictions[-20:]:  # Show last 20
                display_data.append({
                    "Time": pred["timestamp"][11:16],
                    "Symbol": pred["symbol"],
                    "Signal": pred["prediction"]["signal"],
                    "Confidence": f"{pred['prediction']['confidence']:.1%}",
                    "Sentiment": f"{pred['prediction']['sentiment_score']:+.3f}",
                    "News Count": pred["features"]["news_count"],
                    "Status": pred["status"]
                })
            
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)
            
            # Confidence distribution
            st.header("📊 Confidence Distribution")
            conf_values = [pred["prediction"]["confidence"] for pred in predictions]
            conf_df = pd.DataFrame({"Confidence": conf_values})
            st.bar_chart(conf_df["Confidence"].value_counts())
            
        else:
            st.warning("No predictions found")
        
        # Database statistics
        with st.expander("🔍 Database Statistics"):
            st.json(quality_report)
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    st.markdown("---")
    st.markdown("**Data Source:** Live SQL Database (`data/ml_models/training_data.db`)")

if __name__ == "__main__":
    main()
