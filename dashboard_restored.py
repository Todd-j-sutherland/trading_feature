#!/usr/bin/env python3
"""
Simplified Trading Sentiment Analysis Dashboard for ASX Banks
Single-page dashboard with ML performance, sentiment scores, and technical analysis

Requirements:
- Python 3.12 virtual environment
- Streamlit for UI
- Direct SQL database queries (no JSON files)
- Real-time data only
- Production-ready error handling
"""

# Suppress warnings for cleaner dashboard output
import warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*sklearn.*')
warnings.filterwarnings('ignore', message='.*transformers.*')
warnings.filterwarnings('ignore', message='.*ScriptRunContext.*')
warnings.filterwarnings('ignore', message='.*missing ScriptRunContext.*')

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Configure Streamlit to reduce warnings
import logging
logging.getLogger('streamlit').setLevel(logging.ERROR)

# Add the app directory to the path for MarketAux integration
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Try to import MarketAux with fallback
try:
    from app.core.sentiment.marketaux_integration import MarketAuxManager
except ImportError:
    # Fallback if MarketAux not available
    class MarketAuxManager:
        def __init__(self):
            pass
        def get_sentiment_analysis(self, symbols, strategy="balanced"):
            return []

# Configuration - FIXED: Use correct database path
DATABASE_PATH = "enhanced_ml_system/integration/data/ml_models/enhanced_training_data.db"
ASX_BANKS = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX", "SUN.AX", "QBE.AX"]

class DatabaseError(Exception):
    """Custom exception for database-related errors"""
    pass

class DataError(Exception):
    """Custom exception for data-related errors"""
    pass

def get_database_connection() -> sqlite3.Connection:
    """
    Get database connection with proper error handling
    Raises DatabaseError if connection fails
    """
    db_path = Path(DATABASE_PATH)
    if not db_path.exists():
        raise DatabaseError(f"Database not found: {DATABASE_PATH}")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to connect to database: {e}")

def fetch_ml_performance_metrics() -> Dict:
    """
    Fetch ML model performance metrics from database
    Returns metrics for accuracy, success rate, and predictions
    """
    conn = get_database_connection()
    
    try:
        # Get recent predictions for accuracy calculation - FIXED: Use 30 days
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_predictions,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN sentiment_score > 0.05 THEN 1 END) as buy_signals,
                COUNT(CASE WHEN sentiment_score < -0.05 THEN 1 END) as sell_signals,
                COUNT(CASE WHEN sentiment_score BETWEEN -0.05 AND 0.05 THEN 1 END) as hold_signals
            FROM enhanced_features 
            WHERE timestamp >= date('now', '-30 days')
        """)
        
        row = cursor.fetchone()
        if not row or row['total_predictions'] == 0:
            raise DataError("No prediction data found in the last 30 days")
        
        # Get performance from enhanced outcomes
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as completed_trades,
                AVG(return_pct) as avg_return,
                COUNT(CASE WHEN return_pct > 0 THEN 1 END) as successful_trades,
                MAX(return_pct) as best_trade,
                MIN(return_pct) as worst_trade
            FROM enhanced_outcomes 
            WHERE exit_timestamp IS NOT NULL
            AND prediction_timestamp >= date('now', '-30 days')
        """)
        
        outcomes_row = cursor.fetchone()
        
        # Calculate derived metrics
        success_rate = 0
        if outcomes_row and outcomes_row['completed_trades'] > 0:
            success_rate = (outcomes_row['successful_trades'] / outcomes_row['completed_trades'])
        
        metrics = {
            'total_predictions': row['total_predictions'],
            'avg_confidence': float(row['avg_confidence'] or 0),
            'buy_signals': row['buy_signals'],
            'sell_signals': row['sell_signals'], 
            'hold_signals': row['hold_signals'],
            'completed_trades': outcomes_row['completed_trades'] if outcomes_row else 0,
            'success_rate': success_rate,
            'avg_return': float(outcomes_row['avg_return'] or 0) if outcomes_row else 0,
            'best_trade': float(outcomes_row['best_trade'] or 0) if outcomes_row else 0,
            'worst_trade': float(outcomes_row['worst_trade'] or 0) if outcomes_row else 0
        }
        
        return metrics
        
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to fetch ML performance metrics: {e}")
    finally:
        conn.close()

def fetch_performance_timeline_data(days: int = 30) -> pd.DataFrame:
    """
    Fetch performance timeline data for the success rate chart
    Returns DataFrame with daily success rates and outcome counts
    """
    conn = get_database_connection()
    
    try:
        # Get daily performance data
        cursor = conn.execute("""
            SELECT 
                DATE(prediction_timestamp) as date,
                COUNT(*) as total_outcomes,
                COUNT(CASE WHEN return_pct > 0 THEN 1 END) as successful_outcomes,
                ROUND(
                    CAST(COUNT(CASE WHEN return_pct > 0 THEN 1 END) AS FLOAT) / 
                    CAST(COUNT(*) AS FLOAT) * 100, 1
                ) as success_rate_pct,
                AVG(return_pct) as avg_return_pct,
                COUNT(DISTINCT symbol) as banks_traded
            FROM enhanced_outcomes 
            WHERE prediction_timestamp >= date('now', '-{} days')
            AND exit_timestamp IS NOT NULL
            GROUP BY DATE(prediction_timestamp)
            ORDER BY date ASC
        """.format(days))
        
        results = cursor.fetchall()
        
        if not results:
            return pd.DataFrame(columns=[
                'Date', 'Total_Outcomes', 'Cumulative_Outcomes', 
                'Successful_Outcomes', 'Success_Rate_Pct', 'Avg_Return_Pct', 'Banks_Traded'
            ])
        
        data = []
        cumulative_outcomes = 0
        
        for row in results:
            cumulative_outcomes += row[1]  # total_outcomes
            data.append({
                'Date': pd.to_datetime(row[0]),
                'Total_Outcomes': row[1],
                'Cumulative_Outcomes': cumulative_outcomes,
                'Successful_Outcomes': row[2],
                'Success_Rate_Pct': row[3],
                'Avg_Return_Pct': row[4],
                'Banks_Traded': row[5]
            })
        
        return pd.DataFrame(data)
        
    except sqlite3.Error as e:
        # Return empty DataFrame instead of raising error
        st.warning(f"Could not fetch performance timeline: {e}")
        return pd.DataFrame(columns=[
            'Date', 'Total_Outcomes', 'Cumulative_Outcomes', 
            'Successful_Outcomes', 'Success_Rate_Pct', 'Avg_Return_Pct', 'Banks_Traded'
        ])
    finally:
        conn.close()
