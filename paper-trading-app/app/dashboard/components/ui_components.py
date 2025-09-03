"""
UI Components for the Trading Analysis Dashboard
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime


class UIComponents:
    """Professional UI components for the trading analysis dashboard"""
    
    def __init__(self):
        """Initialize UI components"""
        pass
    
    def load_professional_css(self):
        """Load professional CSS styling for the dashboard"""
        css = """
        <style>
        .main {
            padding: 0rem 1rem;
        }
        .stApp > header {
            background-color: transparent;
        }
        .stApp {
            margin-top: -80px;
        }
        .section-header {
            background: linear-gradient(90deg, #1e3d59, #17a2b8);
            color: white;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 10px;
            font-size: 1.2rem;
            font-weight: bold;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 0.5rem 0;
        }
        .alert-success {
            background-color: #d4edda;
            color: #155724;
            padding: 0.75rem;
            border-radius: 5px;
            border: 1px solid #c3e6cb;
            margin: 0.5rem 0;
        }
        .alert-warning {
            background-color: #fff3cd;
            color: #856404;
            padding: 0.75rem;
            border-radius: 5px;
            border: 1px solid #ffeaa7;
            margin: 0.5rem 0;
        }
        .alert-danger {
            background-color: #f8d7da;
            color: #721c24;
            padding: 0.75rem;
            border-radius: 5px;
            border: 1px solid #f5c6cb;
            margin: 0.5rem 0;
        }
        .bank-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .news-item {
            background: #f8f9fa;
            border-left: 4px solid #17a2b8;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 5px;
        }
        .confidence-legend {
            background: #e9ecef;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    def create_professional_header(self):
        """Create the main dashboard header"""
        st.markdown("""
        <div style="background: linear-gradient(90deg, #1e3d59, #17a2b8); 
                    color: white; 
                    padding: 2rem; 
                    margin-bottom: 2rem; 
                    border-radius: 15px;
                    text-align: center;">
            <h1 style="margin: 0; font-size: 2.5rem;">🚀 Professional Trading Analysis Dashboard</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
                Advanced Market Intelligence & Sentiment Analysis
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def create_section_header(self, title: str, subtitle: str = "", icon: str = ""):
        """Create a section header"""
        title_with_icon = f"{icon} {title}" if icon else title
        subtitle_html = f"<p style='margin: 0; opacity: 0.8;'>{subtitle}</p>" if subtitle else ""
        st.markdown(f"""
        <div class="section-header">
            <h3 style="margin: 0;">{title_with_icon}</h3>
            {subtitle_html}
        </div>
        """, unsafe_allow_html=True)
    
    def display_alert(self, message: str, alert_type: str = "info", title: str = None):
        """Display an alert message"""
        alert_class = f"alert-{alert_type}"
        if alert_type == "error":
            alert_class = "alert-danger"
        
        st.markdown(f"""
        <div class="{alert_class}">
            {message}
        </div>
        """, unsafe_allow_html=True)
    
    def display_confidence_legend(self):
        """Display confidence level legend"""
        st.markdown("""
        <div class="confidence-legend">
            <h4>📊 Confidence Levels</h4>
            <div style="display: flex; justify-content: space-around; margin-top: 1rem;">
                <div><span style="color: #28a745;">●</span> High (80-100%)</div>
                <div><span style="color: #ffc107;">●</span> Medium (60-79%)</div>
                <div><span style="color: #dc3545;">●</span> Low (0-59%)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def display_sentiment_scale(self):
        """Display sentiment scale reference"""
        st.markdown("""
        <div class="confidence-legend">
            <h4>📈 Sentiment Scale</h4>
            <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
                <div><span style="color: #dc3545;">■</span> Very Bearish (-1.0)</div>
                <div><span style="color: #fd7e14;">■</span> Bearish (-0.5)</div>
                <div><span style="color: #6c757d;">■</span> Neutral (0.0)</div>
                <div><span style="color: #20c997;">■</span> Bullish (+0.5)</div>
                <div><span style="color: #28a745;">■</span> Very Bullish (+1.0)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def display_professional_metrics(self, metrics: Dict[str, Any]):
        """Display metrics in a professional layout"""
        if not metrics:
            self.display_alert("No metrics available", "warning")
            return
        
        cols = st.columns(len(metrics))
        for i, (key, value) in enumerate(metrics.items()):
            with cols[i]:
                if isinstance(value, float):
                    formatted_value = f"{value:.3f}"
                elif isinstance(value, int):
                    formatted_value = f"{value:,}"
                else:
                    formatted_value = str(value)
                
                st.metric(
                    label=key.replace('_', ' ').title(),
                    value=formatted_value
                )
    
    def create_bank_card_header(self, symbol: str, bank_name: str):
        """Create a bank-style card header"""
        st.markdown(f"""
        <div class="bank-card">
            <h3 style="margin: 0; display: flex; justify-content: space-between; align-items: center;">
                <span>🏦 {bank_name}</span>
                <span style="font-size: 1.5rem; font-weight: bold;">{symbol}</span>
            </h3>
        </div>
        """, unsafe_allow_html=True)
    
    def close_bank_card(self):
        """Close bank card styling (placeholder for consistency)"""
        pass
    
    def display_news_item(self, 
                         title: str, 
                         content: str, 
                         sentiment: float = 0.0,
                         timestamp: Optional[datetime] = None,
                         source: str = "Unknown"):
        """Display a news item with sentiment"""
        
        # Determine sentiment color
        if sentiment > 0.3:
            sentiment_color = "#28a745"
            sentiment_label = "Bullish"
        elif sentiment < -0.3:
            sentiment_color = "#dc3545"
            sentiment_label = "Bearish"
        else:
            sentiment_color = "#6c757d"
            sentiment_label = "Neutral"
        
        timestamp_str = timestamp.strftime("%H:%M") if timestamp else "Recent"
        
        st.markdown(f"""
        <div class="news-item">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <h5 style="margin: 0; color: #1e3d59;">{title}</h5>
                <div style="text-align: right;">
                    <span style="color: {sentiment_color}; font-weight: bold;">
                        {sentiment_label} ({sentiment:.2f})
                    </span>
                    <br>
                    <small style="color: #6c757d;">{timestamp_str} | {source}</small>
                </div>
            </div>
            <p style="margin: 0; color: #495057;">{content[:200]}{'...' if len(content) > 200 else ''}</p>
        </div>
        """, unsafe_allow_html=True)
