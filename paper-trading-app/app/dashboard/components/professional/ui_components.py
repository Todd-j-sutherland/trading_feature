import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from app.core.analysis.technical import get_market_data

def create_professional_header():
    """Create professional dashboard header"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 ASX Bank Analytics Platform</h1>
        <p>Professional sentiment analysis and technical indicators for Australian banking sector</p>
    </div>
    """, unsafe_allow_html=True)

def create_section_header(title: str, subtitle: str = "", icon: str = ""):
    """Create professional section header"""
    st.markdown(f"""
    <div class="section-header">
        <h2>{icon} {title}</h2>
        {f'<div class="subtitle">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def display_professional_metrics(metrics: list):
    """Display metrics in professional card layout"""
    cols = st.columns(len(metrics))
    
    for i, metric in enumerate(metrics):
        with cols[i]:
            value = metric.get('value', 'N/A')
            delta = metric.get('delta', '')
            status = metric.get('status', 'neutral')
            subtitle = metric.get('subtitle', '')
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>{metric['title']}</h4>
                <div class="metric-value status-{status}">{value}</div>
                {f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ''}
                {f'<div class="metric-subtitle status-{status}">{delta}</div>' if delta else ''}
            </div>
            """, unsafe_allow_html=True)

def create_sentiment_overview_chart(dashboard, all_data: dict) -> go.Figure:
    """Create professional overview chart of all bank sentiments"""
    symbols = []
    scores = []
    confidences = []
    colors = []
    
    for symbol, data in all_data.items():
        latest = dashboard.get_latest_analysis(data)
        if latest:
            symbols.append(dashboard.bank_names.get(symbol, symbol))
            score = latest.get('overall_sentiment', 0)
            confidence = latest.get('confidence', 0)
            
            scores.append(score)
            confidences.append(confidence)
            
            if score > 0.2:
                colors.append('#27ae60')
            elif score < -0.2:
                colors.append('#e74c3c')
            else:
                colors.append('#6c757d')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=symbols,
        y=scores,
        name='Sentiment Score',
        marker=dict(color=colors, line=dict(color='white', width=1)),
        text=[f"{s:.3f}" for s in scores],
        textposition='auto',
        textfont=dict(size=12, family="Inter"),
        hovertemplate='<b>%{x}</b><br>Sentiment: %{y:.3f}<br>Confidence: %{customdata:.2f}<extra></extra>',
        customdata=confidences
    ))
    fig.update_layout(
        title=dict(text="Bank Sentiment Overview", font=dict(size=18, family="Inter", weight=600, color="#2c3e50")),
        xaxis=dict(title=dict(text="Banks", font=dict(size=14, family="Inter")), tickfont=dict(size=12, family="Inter")),
        yaxis=dict(title=dict(text="Sentiment Score", font=dict(size=14, family="Inter")), range=[-1, 1]),
        height=400, showlegend=False, plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Inter")
    )
    return fig

def create_confidence_distribution_chart(dashboard, all_data: dict) -> go.Figure:
    """Create professional confidence distribution chart"""
    symbols = []
    confidences = []
    
    for symbol, data in all_data.items():
        latest = dashboard.get_latest_analysis(data)
        if latest:
            symbols.append(dashboard.bank_names.get(symbol, symbol))
            confidences.append(latest.get('confidence', 0))
    
    colors = []
    for c in confidences:
        if c >= 0.8: colors.append('#27ae60')
        elif c >= 0.6: colors.append('#f39c12')
        else: colors.append('#e74c3c')
    
    fig = go.Figure(go.Bar(
        x=symbols, y=confidences, marker=dict(color=colors),
        text=[f"{c:.2f}" for c in confidences], textposition='auto',
        hovertemplate='<b>%{x}</b><br>Confidence: %{y:.3f}<extra></extra>'
    ))
    fig.update_layout(
        title=dict(text="Analysis Confidence Levels", font=dict(size=18, family="Inter", weight=600, color="#2c3e50")),
        xaxis=dict(title=dict(text="Banks", font=dict(size=14, family="Inter"))),
        yaxis=dict(title=dict(text="Confidence Score", font=dict(size=14, family="Inter")), range=[0, 1]),
        height=400, showlegend=False, plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Inter")
    )
    return fig

def display_confidence_legend():
    """Display professional confidence score legend and decision criteria"""
    st.markdown("""
    <div class="legend-container">
        <div class="legend-title">📊 Confidence Score Legend & Decision Criteria</div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card confidence-high">
            <h4>🟢 HIGH CONFIDENCE (≥0.8)</h4>
            <p><strong>Action:</strong> Strong Buy/Sell Signal</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card confidence-medium">
            <h4>🟡 MEDIUM CONFIDENCE (0.6-0.8)</h4>
            <p><strong>Action:</strong> Moderate Buy/Sell Signal</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card confidence-low">
            <h4>🔴 LOW CONFIDENCE (<0.6)</h4>
            <p><strong>Action:</strong> Hold/Monitor</p>
        </div>
        """, unsafe_allow_html=True)

def display_sentiment_scale():
    """Display professional sentiment scale explanation"""
    st.markdown("""
    <div class="legend-container">
        <div class="legend-title">📈 Sentiment Score Scale</div>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(5)
    sentiments = [
        ("Very Negative", "-1.0 to -0.5", "Strong Sell", "negative"),
        ("Negative", "-0.5 to -0.2", "Sell", "negative"),
        ("Neutral", "-0.2 to +0.2", "Hold", "neutral"),
        ("Positive", "+0.2 to +0.5", "Buy", "positive"),
        ("Very Positive", "+0.5 to +1.0", "Strong Buy", "positive")
    ]
    for col, (title, value, subtitle, status) in zip(cols, sentiments):
        col.markdown(f'<div class="metric-card"><h4>{title}</h4><div class="metric-value status-{status}">{value}</div><div class="metric-subtitle">{subtitle}</div></div>', unsafe_allow_html=True)

def display_bank_analysis(dashboard, symbol: str, data: list):
    """Display detailed analysis for a specific bank with professional styling"""
    latest = dashboard.get_latest_analysis(data)
    if not latest:
        st.warning(f"No analysis data available for {dashboard.bank_names.get(symbol, symbol)}")
        return

    bank_name = dashboard.bank_names.get(symbol, symbol)
    st.markdown(f"""
    <div class="bank-card">
        <div class="bank-card-header"><h3>🏦 {bank_name} ({symbol})</h3></div>
        <div class="bank-card-body">
    """, unsafe_allow_html=True)

    sentiment = latest.get('overall_sentiment', 0)
    confidence = latest.get('confidence', 0)
    score_text, score_class = dashboard.format_sentiment_score(sentiment)
    conf_level, conf_class = dashboard.get_confidence_level(confidence)

    metrics = [
        {'title': 'Sentiment Score', 'value': score_text, 'status': score_class.replace('status-', '')},
        {'title': 'Confidence Level', 'value': f"{confidence:.2f}", 'subtitle': f"{conf_level} confidence"},
        {'title': 'News Articles', 'value': str(latest.get('news_count', 0))},
        {'title': 'Last Updated', 'value': latest.get('timestamp', 'Unknown')[:10]}
    ]
    display_professional_metrics(metrics)
    
    if 'recent_headlines' in latest:
        st.markdown("<h4>📰 Recent Market Headlines</h4>", unsafe_allow_html=True)
        for i, headline in enumerate(latest['recent_headlines'][:5]):
            if headline:
                st.markdown(f'<div class="news-item neutral"><strong>#{i+1}</strong> {headline}</div>', unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

def create_recovery_probability_chart(recovery_predictions: dict):
    """Create recovery probability visualization chart"""
    timeframes = list(recovery_predictions.keys())
    probabilities = [recovery_predictions[tf].get('probability', 0) * 100 for tf in timeframes]
    
    colors = []
    for prob in probabilities:
        if prob >= 80: colors.append('#27ae60')
        elif prob >= 60: colors.append('#f39c12')
        else: colors.append('#e74c3c')
    
    fig = go.Figure(go.Bar(
        x=[tf.replace('_', ' ').title() for tf in timeframes],
        y=probabilities,
        marker=dict(color=colors, line=dict(color='white', width=1)),
        text=[f"{p:.1f}%" for p in probabilities],
        textposition='auto',
        textfont=dict(size=12, family="Inter", weight=600),
        hovertemplate='<b>%{x}</b><br>Recovery Probability: %{y:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text="Recovery Probability by Timeframe", font=dict(size=18, family="Inter", weight=600, color="#2c3e50")),
        yaxis=dict(range=[0, 100]),
        height=400, showlegend=False, plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Inter")
    )
    st.plotly_chart(fig, use_container_width=True)

def display_position_recommendations(recommendations: dict):
    """Display AI-generated position recommendations"""
    primary_action = recommendations.get('primary_action', 'MONITOR')
    st.markdown(f"### Primary Recommendation: {primary_action.replace('_', ' ').title()}")

def display_risk_breakdown(risk_metrics: dict):
    """Display detailed risk metrics breakdown"""
    st.markdown("### Risk Analysis Breakdown")
    st.json(risk_metrics)

def display_market_context(market_context: dict, symbol: str):
    """Display market context and environmental factors"""
    st.markdown("### Market Context")
    st.json(market_context)

def display_action_plan(recommendations: dict, current_return: float, risk_score: float):
    """Display comprehensive action plan based on analysis"""
    st.markdown("### Action Plan")

def display_fallback_risk_assessment(dashboard, symbol: str, entry_price: float, current_price: float, position_type: str):
    """Display a simplified heuristic risk assessment when full system unavailable"""
    st.markdown("### Basic Risk Assessment")
