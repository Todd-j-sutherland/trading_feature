#!/usr/bin/env python3
"""
News Analysis Dashboard with Technical Analysis Integration
Professional interactive web dashboard displaying news sentiment analysis and technical indicators for Australian banks
"""

import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
from datetime import datetime
import logging
import sys
# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from app.config.settings import Settings
from app.core.analysis.technical import TechnicalAnalyzer
from app.dashboard.components.professional.data_components import load_sentiment_data, get_latest_analysis, get_current_price
from app.dashboard.components.professional.ui_components import (
    create_professional_header,
    display_confidence_legend,
    display_sentiment_scale,
)
from app.dashboard.views import (
    market_overview,
    individual_bank_analysis,
    technical_analysis,
    position_risk,
    news_sentiment,
    system_status,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import ML Progression Tracker
try:
    from app.core.ml.tracking.progression_tracker import MLProgressionTracker
    from app.dashboard.components.ml_progression import render_ml_progression_dashboard
    ML_TRACKER_AVAILABLE = True
    logger.info("ML Progression Tracker loaded successfully")
except ImportError:
    ML_TRACKER_AVAILABLE = False
    logger.warning("ML Progression Tracker not available")

# Import Position Risk Assessor
try:
    from app.core.trading.risk_management import PositionRiskAssessor
    POSITION_RISK_AVAILABLE = True
    logger.info("Position Risk Assessor loaded successfully")
except ImportError:
    POSITION_RISK_AVAILABLE = False
    logger.warning("Position Risk Assessor not available")

# Page configuration
st.set_page_config(
    page_title="ASX Bank Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for consistent theming */
    :root {
        --primary-color: #2c3e50;
        --secondary-color: #3498db;
        --accent-color: #e74c3c;
        --success-color: #27ae60;
        --warning-color: #f39c12;
        --info-color: #17a2b8;
        --light-gray: #f8f9fa;
        --medium-gray: #6c757d;
        --dark-gray: #343a40;
        --border-color: #dee2e6;
        --shadow: 0 2px 4px rgba(0,0,0,0.1);
        --shadow-hover: 0 4px 8px rgba(0,0,0,0.15);
        --border-radius: 8px;
        --border-radius-lg: 12px;
    }
    
    /* Global font styling */
    .main, .sidebar, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        padding: 2rem;
        border-radius: var(--border-radius-lg);
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: var(--shadow);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-weight: 300;
    }
    
    /* Enhanced metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        text-align: center;
        height: 100%;
    }
    
    .metric-card:hover {
        box-shadow: var(--shadow-hover);
        transform: translateY(-2px);
    }
    
    .metric-card h4 {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--medium-gray);
        margin: 0 0 0.5rem 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }
    
    .metric-subtitle {
        font-size: 0.75rem;
        color: var(--medium-gray);
        margin-top: 0.25rem;
        font-weight: 500;
    }
    
    /* Status indicators */
    .status-positive { color: var(--success-color); }
    .status-negative { color: var(--accent-color); }
    .status-neutral { color: var(--medium-gray); }
    .status-warning { color: var(--warning-color); }
    
    /* Enhanced confidence indicators */
    .confidence-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .confidence-high {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .confidence-medium {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        color: #856404;
        border: 1px solid #ffeeba;
    }
    
    .confidence-low {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    /* Professional section headers */
    .section-header {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius) var(--border-radius) 0 0;
        border-bottom: 3px solid var(--secondary-color);
        margin-bottom: 0;
        box-shadow: var(--shadow);
    }
    
    .section-header h2 {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--primary-color);
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .section-header .subtitle {
        color: var(--medium-gray);
        font-size: 0.875rem;
        font-weight: 400;
        margin-top: 0.25rem;
    }
    
    /* Enhanced bank cards */
    .bank-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius-lg);
        padding: 0;
        margin: 1.5rem 0;
        box-shadow: var(--shadow);
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .bank-card:hover {
        box-shadow: var(--shadow-hover);
        border-color: var(--secondary-color);
    }
    
    .bank-card-header {
        background: linear-gradient(135deg, var(--light-gray) 0%, #e9ecef 100%);
        padding: 1.25rem 1.5rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .bank-card-header h3 {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--primary-color);
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .bank-card-body {
        padding: 1.5rem;
    }
    
    /* Enhanced news items */
    .news-item {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 0.75rem 0;
        transition: all 0.3s ease;
        border-left: 4px solid var(--border-color);
    }
    
    .news-item:hover {
        box-shadow: var(--shadow);
        border-left-color: var(--secondary-color);
    }
    
    .news-item.positive { border-left-color: var(--success-color); }
    .news-item.negative { border-left-color: var(--accent-color); }
    .news-item.neutral { border-left-color: var(--medium-gray); }
    
    /* Enhanced event badges */
    .event-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.375rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0.25rem 0.25rem 0.25rem 0;
    }
    
    .event-positive {
        background: linear-gradient(135deg, var(--success-color) 0%, #229954 100%);
        color: white;
    }
    
    .event-negative {
        background: linear-gradient(135deg, var(--accent-color) 0%, #c0392b 100%);
        color: white;
    }
    
    .event-neutral {
        background: linear-gradient(135deg, var(--medium-gray) 0%, #5a6268 100%);
        color: white;
    }
    
    /* Professional table styling */
    .stDataFrame {
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        overflow: hidden;
    }
    
    /* Enhanced sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--light-gray) 0%, white 100%);
    }
    
    /* Professional buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--secondary-color) 0%, #2980b9 100%);
        color: white;
        border: none;
        border-radius: var(--border-radius);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: var(--shadow);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2980b9 0%, #1f618d 100%);
        box-shadow: var(--shadow-hover);
        transform: translateY(-1px);
    }
    
    /* Enhanced tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--light-gray);
        padding: 0.5rem;
        border-radius: var(--border-radius);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--secondary-color);
        color: white;
        border-color: var(--secondary-color);
    }
    
    /* Legend containers */
    .legend-container {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius-lg);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
    }
    
    .legend-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--primary-color);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Professional alerts */
    .alert {
        padding: 1rem 1.25rem;
        border-radius: var(--border-radius);
        border: 1px solid;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    .alert-info {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-color: #bee5eb;
        color: #0c5460;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        border-color: #ffeeba;
        color: #856404;
    }
    
    .alert-success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-color: #c3e6cb;
        color: #155724;
    }
    
    /* Footer styling */
    .footer {
        background: var(--primary-color);
        color: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        text-align: center;
        margin-top: 2rem;
        font-size: 0.875rem;
    }
    
    /* Loading animations */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
        
        .bank-card-header {
            padding: 1rem;
        }
        
        .bank-card-body {
            padding: 1rem;
        }
    }
    
    /* Position Risk Assessment Enhancements */
    .form-section {
        background: linear-gradient(135deg, var(--light-gray) 0%, #f1f3f4 100%);
        padding: 1.5rem;
        border-radius: var(--border-radius);
        margin-bottom: 1.5rem;
        border: 1px solid var(--border-color);
    }
    
    .form-section h4 {
        color: var(--primary-color);
        margin: 0 0 0.5rem 0;
        font-weight: 600;
    }
    
    .form-section p {
        color: var(--medium-gray);
        margin: 0;
        font-size: 0.9rem;
    }
    
    .position-preview {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
    }
    
    .position-preview h5 {
        color: var(--primary-color);
        margin: 0 0 0.75rem 0;
        font-weight: 600;
    }
    
    .preview-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
        font-size: 0.9rem;
    }
    
    .preview-grid div {
        padding: 0.25rem 0;
    }
    
    .profit {
        color: var(--success-color);
        font-weight: 600;
    }
    
    .loss {
        color: var(--accent-color);
        font-weight: 600;
    }
    
    .low-risk {
        color: var(--success-color);
        font-weight: 600;
    }
    
    .medium-risk {
        color: var(--warning-color);
        font-weight: 600;
    }
    
    .high-risk {
        color: var(--accent-color);
        font-weight: 600;
    }
    
    /* Enhanced Risk Assessment Results */
    .risk-results-container {
        background: white;
        border-radius: var(--border-radius-lg);
        box-shadow: var(--shadow);
        margin: 1.5rem 0;
        overflow: hidden;
    }
    
    .risk-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        padding: 1.5rem;
        text-align: center;
    }
    
    .risk-header h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .risk-summary {
        display: flex;
        justify-content: space-around;
        margin-top: 1rem;
    }
    
    .risk-summary-item {
        text-align: center;
    }
    
    .risk-summary-value {
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    
    .risk-summary-label {
        font-size: 0.85rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

class NewsAnalysisDashboard:
    """Professional dashboard for displaying news analysis and technical analysis results"""
    
    def __init__(self):
        self.data_path = "data/sentiment_history"
        self.settings = Settings()
        self.bank_symbols = self.settings.BANK_SYMBOLS
        self.bank_names = self.settings.BANK_NAMES
        self.tech_analyzer = TechnicalAnalyzer(self.settings)
        self.technical_data = {}
        self.position_risk_available = POSITION_RISK_AVAILABLE
        
        if ML_TRACKER_AVAILABLE:
            self.ml_tracker = MLProgressionTracker()
        else:
            self.ml_tracker = None

    def load_sentiment_data(self):
        return load_sentiment_data(self)

    def get_latest_analysis(self, data):
        return get_latest_analysis(data)

    def get_current_price(self, symbol):
        return get_current_price(symbol)

    def format_sentiment_score(self, score: float) -> tuple:
        """Format sentiment score with color class"""
        if score > 0.2:
            return f"+{score:.3f}", "status-positive"
        elif score < -0.2:
            return f"{score:.3f}", "status-negative"
        else:
            return f"{score:.3f}", "status-neutral"
    
    def get_confidence_level(self, confidence: float) -> tuple:
        """Get confidence level description and CSS class"""
        if confidence >= 0.8:
            return "HIGH", "confidence-high"
        elif confidence >= 0.6:
            return "MEDIUM", "confidence-medium"
        else:
            return "LOW", "confidence-low"

def main():
    """Main function to run the professional dashboard"""
    try:
        dashboard = NewsAnalysisDashboard()
        create_professional_header()

        with st.sidebar:
            st.markdown("""
            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); 
                       border-radius: 10px; margin-bottom: 1.5rem;">
                <h3 style="color: white; margin: 0;">🏦 ASX Bank Analytics</h3>
                <p style="color: #ecf0f1; margin: 0.5rem 0 0 0; font-size: 0.9rem;">Professional Trading Dashboard</p>
            </div>
            """, unsafe_allow_html=True)
            
            selected_view = st.selectbox(
                "📊 Select Analysis View:",
                options=[
                    "📈 Market Overview",
                    "🏦 Individual Bank Analysis", 
                    "📊 Technical Analysis",
                    "🎯 Position Risk Assessor",
                    "📰 News & Sentiment",
                    "🤖 ML Performance Tracking",
                    "⚙️ System Status"
                ],
                index=0,
                key="dashboard_main_nav"
            )

        if selected_view == "📈 Market Overview":
            market_overview.display_market_overview(dashboard)
        elif selected_view == "🏦 Individual Bank Analysis":
            individual_bank_analysis.display_individual_bank_analysis(dashboard)
        elif selected_view == "📊 Technical Analysis":
            technical_analysis.display_technical_analysis(dashboard)
        elif selected_view == "🎯 Position Risk Assessor":
            position_risk.display_position_risk_section(dashboard)
        elif selected_view == "📰 News & Sentiment":
            news_sentiment.display_news_sentiment_analysis(dashboard)
        elif selected_view == "🤖 ML Performance Tracking":
            if ML_TRACKER_AVAILABLE:
                render_ml_progression_dashboard()
            else:
                st.error("ML Performance Tracking is not available.")
        elif selected_view == "⚙️ System Status":
            system_status.display_system_status(dashboard)
            
    except Exception as e:
        st.error(f"❌ Dashboard Error: {str(e)}")
        logger.error(f"Dashboard error: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()