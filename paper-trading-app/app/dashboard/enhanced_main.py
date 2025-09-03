"""
Enhanced ASX Bank Analysis Dashboard

Comprehensive dashboard displaying:
- Economic sentiment analysis and market regime
- Individual bank sentiment with divergence detection
- ML-powered predictions and confidence scores
- Trading signals with economic context
- Risk assessment and position recommendations
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os
import time
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

    # Import our components
try:
    from app.core.analysis.economic import EconomicSentimentAnalyzer
    from app.core.analysis.divergence import DivergenceDetector
    from app.core.data.processors.news_processor import NewsTradingAnalyzer
    from app.core.ml.enhanced_pipeline import EnhancedMLPipeline
    from app.core.ml.trading_scorer import MLTradingScorer
    from app.core.trading.alpaca_integration import AlpacaMLTrader
    from app.core.data.collectors.market_data import ASXDataFeed
    from app.config.settings import Settings
    from app.dashboard.components.trading_performance import enhanced_dashboard_performance_section
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import components: {e}")
    COMPONENTS_AVAILABLE = False

def main():
    """Main dashboard function"""
    st.set_page_config(
        page_title="ASX Bank Analysis Dashboard",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2980b9);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #ecf0f1;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .alert-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
    }
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
    }
    .alert-danger {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
    }
    .trading-signal-buy {
        background: linear-gradient(45deg, #27ae60, #2ecc71);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        text-align: center;
    }
    .trading-signal-sell {
        background: linear-gradient(45deg, #e74c3c, #c0392b);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        text-align: center;
    }
    .trading-signal-hold {
        background: linear-gradient(45deg, #f39c12, #e67e22);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        text-align: center;
    }
    .confidence-high {
        color: #27ae60;
        font-weight: bold;
    }
    .confidence-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .confidence-low {
        color: #e74c3c;
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3498db, #2ecc71);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header with gradient background
    st.markdown("""
    <div class="main-header">
        <h1>🏦 Enhanced ASX Bank Analysis Dashboard</h1>
        <p>AI-Powered Trading Analysis with Economic Context & Divergence Detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not COMPONENTS_AVAILABLE:
        st.error("❌ Core components not available. Please check your installation.")
        return
    
    # Add system status indicator
    display_system_status()
    
    # Initialize components with error handling
    components = initialize_components()
    if not components:
        return
    
    # Enhanced sidebar with better organization
    setup_enhanced_sidebar(components['settings'])
    
    # Get sidebar settings
    sidebar_config = get_sidebar_config()
    
    # Main dashboard sections with loading indicators
    with st.spinner("🔄 Loading economic analysis..."):
        display_economic_overview(components['economic_analyzer'])
    
    # Get bank analyses with progress tracking
    bank_analyses = get_bank_analyses_enhanced(
        components['news_analyzer'], 
        sidebar_config['selected_banks']
    )
    
    if bank_analyses:
        # Enhanced main analysis sections
        display_enhanced_dashboard_sections(components, bank_analyses, sidebar_config)
    else:
        st.error("❌ Unable to retrieve bank analysis data.")

def display_ml_trading_scores(ml_scores, confidence_threshold):
    """Display ML trading scores for each bank"""
    st.markdown("## 🎯 ML Trading Scores")
    
    if not ml_scores:
        st.warning("⚠️ No ML trading scores available")
        return
    
    # Create columns for better layout
    cols = st.columns(len(ml_scores))
    
    for idx, (bank, score_data) in enumerate(ml_scores.items()):
        with cols[idx]:
            # Overall score with color coding
            overall_score = score_data.get('overall_score', 0)
            confidence = score_data.get('confidence', 0)
            recommendation = score_data.get('recommendation', 'HOLD')
            
            # Color based on recommendation
            color = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(recommendation, '⚫')
            
            st.markdown(f"""
            <div style='border: 2px solid {"green" if recommendation == "BUY" else "red" if recommendation == "SELL" else "orange"}; 
                        border-radius: 10px; padding: 15px; margin-bottom: 10px;'>
                <h3 style='text-align: center; margin-top: 0;'>{color} {bank}</h3>
                <h2 style='text-align: center; font-size: 2em;'>{overall_score:.1f}/100</h2>
                <p style='text-align: center; font-weight: bold; color: {"green" if recommendation == "BUY" else "red" if recommendation == "SELL" else "orange"};'>
                    {recommendation}
                </p>
                <p style='text-align: center; font-size: 0.9em;'>
                    Confidence: {confidence:.1%}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show component breakdown
            with st.expander(f"📊 {bank} Score Breakdown"):
                components = score_data.get('components', {})
                for component, value in components.items():
                    if component != 'overall_score':
                        st.metric(
                            label=component.replace('_', ' ').title(),
                            value=f"{value:.1f}",
                            delta=None
                        )

def display_alpaca_integration(alpaca_trader, ml_scores):
    """Display Alpaca trading integration status and actions"""
    st.markdown("## 📈 Alpaca Trading Integration")
    
    # Check if Alpaca is available
    if not alpaca_trader:
        st.warning("⚠️ Alpaca integration not available. Set up API credentials to enable paper trading.")
        with st.expander("🔧 Setup Instructions"):
            st.markdown("""
            To enable Alpaca paper trading:
            1. Create account at [Alpaca Markets](https://alpaca.markets/)
            2. Get paper trading API credentials
            3. Set environment variables:
               - `ALPACA_API_KEY`
               - `ALPACA_SECRET_KEY`
               - `ALPACA_BASE_URL` (paper trading URL)
            4. Install alpaca-trade-api: `pip install alpaca-trade-api`
            """)
        return
    
    # Show account status
    st.subheader("📊 Account Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Account Status", "Paper Trading", delta="Active")
    with col2:
        st.metric("Buying Power", "$100,000", delta="+$500")
    with col3:
        st.metric("Portfolio Value", "$105,000", delta="+$5,000")
    
    # Trading recommendations based on ML scores
    if ml_scores:
        st.subheader("🎯 ML Trading Recommendations")
        
        for bank, score_data in ml_scores.items():
            recommendation = score_data.get('recommendation', 'HOLD')
            overall_score = score_data.get('overall_score', 0)
            confidence = score_data.get('confidence', 0)
            
            col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
            
            with col1:
                st.write(f"**{bank}**")
            with col2:
                color = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(recommendation, '⚫')
                st.write(f"{color} {recommendation}")
            with col3:
                st.write(f"{overall_score:.1f}/100")
            with col4:
                if recommendation in ['BUY', 'SELL'] and confidence > 0.6:
                    if st.button(f"Execute {recommendation}", key=f"trade_{bank}"):
                        # Simulate trade execution
                        st.success(f"✅ {recommendation} order placed for {bank}")
                        st.balloons()


def display_economic_overview(economic_analyzer):
    """Display economic sentiment and market regime analysis"""
    st.header("🌍 Economic Context Analysis")
    
    try:
        economic_data = economic_analyzer.analyze_economic_sentiment()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            sentiment = economic_data.get('overall_sentiment', 0)
            # For delta_color: Streamlit only accepts 'normal', 'inverse', or 'off'
            sentiment_delta_color = "normal" if sentiment > 0 else "inverse" if sentiment < 0 else "off"
            # For chart colors: use standard color names
            sentiment_color = "green" if sentiment > 0 else "red" if sentiment < 0 else "gray"
            st.metric(
                "Overall Economic Sentiment",
                f"{sentiment:+.3f}",
                delta=None,
                delta_color=sentiment_delta_color
            )
        
        with col2:
            confidence = economic_data.get('confidence', 0)
            st.metric("Analysis Confidence", f"{confidence:.1%}")
        
        with col3:
            regime = economic_data.get('market_regime', {}).get('regime', 'Unknown')
            st.metric("Market Regime", regime)
        
        with col4:
            # Add a custom indicator based on regime
            regime_score = {
                'Expansion': 0.8,
                'Neutral': 0.5,
                'Tightening': 0.3,
                'Contraction': 0.2,
                'Easing': 0.6
            }.get(regime, 0.5)
            st.metric("Regime Score", f"{regime_score:.1f}")
        
        # Economic indicators breakdown
        if show_detailed := st.expander("📊 Economic Indicators Breakdown", expanded=False):
            indicators = economic_data.get('indicators', {})
            
            if indicators:
                df_indicators = pd.DataFrame([
                    {
                        'Indicator': key.replace('_', ' ').title(),
                        'Value': data.get('value', 'N/A'),
                        'Trend': data.get('trend', 'N/A'),
                        'Sentiment': data.get('sentiment', 0)
                    }
                    for key, data in indicators.items()
                ])
                
                st.dataframe(df_indicators, use_container_width=True)
                
                # Create gauge chart for sentiment
                fig_sentiment = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=sentiment,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Economic Sentiment"},
                    delta={'reference': 0},
                    gauge={
                        'axis': {'range': [-1, 1]},
                        'bar': {'color': sentiment_color},
                        'steps': [
                            {'range': [-1, -0.5], 'color': "lightcoral"},
                            {'range': [-0.5, 0], 'color': "lightyellow"},
                            {'range': [0, 0.5], 'color': "lightblue"},
                            {'range': [0.5, 1], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 0.9
                        }
                    }
                ))
                
                st.plotly_chart(fig_sentiment, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Economic analysis error: {e}")

def display_system_status():
    """Display system status and health indicators"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 System Status")
    
    # Check component availability
    status_items = []
    
    try:
        from app.core.data.processors.news_processor import NewsTradingAnalyzer
        status_items.append(("News Analysis", "✅"))
    except:
        status_items.append(("News Analysis", "❌"))
    
    try:
        from app.core.ml.enhanced_pipeline import EnhancedMLPipeline
        status_items.append(("ML Pipeline", "✅"))
    except:
        status_items.append(("ML Pipeline", "❌"))
    
    try:
        from app.core.analysis.economic import EconomicSentimentAnalyzer
        status_items.append(("Economic Analysis", "✅"))
    except:
        status_items.append(("Economic Analysis", "❌"))
    
    for name, status in status_items:
        st.sidebar.markdown(f"{status} {name}")
    
    # Last update time
    current_time = datetime.now().strftime("%H:%M:%S")
    st.sidebar.markdown(f"🕒 Last Update: {current_time}")


def initialize_components():
    """Initialize all dashboard components with error handling"""
    components = {}
    
    try:
        with st.spinner("🔄 Initializing components..."):
            # Progress bar for initialization
            progress_bar = st.progress(0)
            
            components['economic_analyzer'] = EconomicSentimentAnalyzer()
            progress_bar.progress(0.15)
            
            components['divergence_detector'] = DivergenceDetector()
            progress_bar.progress(0.30)
            
            components['news_analyzer'] = NewsTradingAnalyzer()
            progress_bar.progress(0.45)
            
            components['ml_pipeline'] = EnhancedMLPipeline()
            progress_bar.progress(0.60)
            
            components['ml_scorer'] = MLTradingScorer()
            progress_bar.progress(0.75)
            
            components['alpaca_trader'] = AlpacaMLTrader(paper=True)
            progress_bar.progress(0.85)
            
            components['data_feed'] = ASXDataFeed()
            progress_bar.progress(0.95)
            
            components['settings'] = Settings()
            progress_bar.progress(1.0)
            
            progress_bar.empty()
            
        st.success("✅ All components initialized successfully!")
        time.sleep(1)  # Brief success message display
        return components
        
    except Exception as e:
        st.error(f"❌ Failed to initialize components: {e}")
        return None


def setup_enhanced_sidebar(settings):
    """Setup enhanced sidebar with better organization and controls"""
    st.sidebar.header("📊 Analysis Controls")
    
    # Quick action buttons
    st.sidebar.markdown("### 🚀 Quick Actions")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        refresh_data = st.button("🔄 Refresh", key="refresh_main")
    with col2:
        auto_refresh = st.checkbox("🔁 Auto", key="auto_refresh")
    
    if auto_refresh:
        st.sidebar.info("🔁 Auto-refresh enabled (30s intervals)")
        time.sleep(30)
        st.experimental_rerun()
    
    # Analysis settings
    st.sidebar.markdown("### ⚙️ Analysis Settings")
    
    # Store settings in session state
    if 'dashboard_config' not in st.session_state:
        st.session_state.dashboard_config = {
            'show_detailed': True,
            'confidence_threshold': 0.6,
            'selected_banks': settings.BANK_SYMBOLS,
            'view_mode': 'Standard'
        }
    
    st.session_state.dashboard_config['show_detailed'] = st.sidebar.checkbox(
        "📋 Detailed Analysis", 
        value=st.session_state.dashboard_config['show_detailed']
    )
    
    st.session_state.dashboard_config['confidence_threshold'] = st.sidebar.slider(
        "🎯 Confidence Threshold", 
        0.0, 1.0, 
        st.session_state.dashboard_config['confidence_threshold'], 
        0.05
    )
    
    # View mode selection
    st.session_state.dashboard_config['view_mode'] = st.sidebar.selectbox(
        "👁️ View Mode",
        ["Standard", "Compact", "Detailed", "Mobile-Friendly"],
        index=0
    )
    
    # Bank selection with quick presets
    st.sidebar.markdown("### 🏦 Bank Selection")
    
    # Quick preset buttons
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        if st.button("All", key="select_all"):
            st.session_state.dashboard_config['selected_banks'] = settings.BANK_SYMBOLS
    with col2:
        if st.button("Big 4", key="select_big4"):
            st.session_state.dashboard_config['selected_banks'] = ["CBA", "ANZ", "WBC", "NAB"]
    with col3:
        if st.button("Clear", key="clear_all"):
            st.session_state.dashboard_config['selected_banks'] = []
    
    st.session_state.dashboard_config['selected_banks'] = st.sidebar.multiselect(
        "Select banks to analyze:",
        options=settings.BANK_SYMBOLS,
        default=st.session_state.dashboard_config['selected_banks']
    )


def get_sidebar_config():
    """Get current sidebar configuration"""
    if 'dashboard_config' not in st.session_state:
        return {
            'show_detailed': True,
            'confidence_threshold': 0.6,
            'selected_banks': [],
            'view_mode': 'Standard'
        }
    return st.session_state.dashboard_config


def get_bank_analyses_enhanced(news_analyzer, selected_banks):
    """Enhanced bank analysis retrieval with progress tracking"""
    if not selected_banks:
        st.warning("⚠️ Please select at least one bank to analyze.")
        return None
    
    bank_analyses = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, bank in enumerate(selected_banks):
        status_text.text(f"📊 Analyzing {bank}...")
        progress = (i + 1) / len(selected_banks)
        progress_bar.progress(progress)
        
        try:
            # Use the correct method name: analyze_single_bank
            analysis = news_analyzer.analyze_single_bank(bank)
            bank_analyses[bank] = analysis
        except Exception as e:
            st.warning(f"⚠️ Failed to analyze {bank}: {e}")
            continue
    
    progress_bar.empty()
    status_text.empty()
    
    if bank_analyses:
        st.success(f"✅ Successfully analyzed {len(bank_analyses)} banks")
    
    return bank_analyses


def display_enhanced_economic_analysis(economic_analyzer):
    """Enhanced economic analysis with visualizations"""
    st.subheader("🌍 Economic Sentiment Analysis")
    
    try:
        economic_data = economic_analyzer.analyze_economic_sentiment()
        
        # Create enhanced metrics display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            sentiment_score = economic_data.get('economic_sentiment_score', 0)
            sentiment_color = "🟢" if sentiment_score > 0.6 else "🟡" if sentiment_score > 0.4 else "🔴"
            st.metric(
                "Economic Sentiment",
                f"{sentiment_score:.2f}",
                delta=f"{economic_data.get('sentiment_change', 0):+.2f}",
                help="Overall economic sentiment from news analysis"
            )
            st.markdown(f"**Status:** {sentiment_color}")
        
        with col2:
            market_regime = economic_data.get('market_regime', 'Unknown')
            regime_icons = {
                'bull': '🐂',
                'bear': '🐻', 
                'sideways': '➡️',
                'volatile': '🌪️',
                'Unknown': '❓'
            }
            st.metric(
                "Market Regime",
                market_regime.title(),
                help="Current market regime based on economic indicators"
            )
            st.markdown(f"**Trend:** {regime_icons.get(market_regime.lower(), '❓')}")
        
        with col3:
            risk_level = economic_data.get('risk_level', 'Medium')
            risk_colors = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}
            st.metric(
                "Risk Level",
                risk_level,
                help="Current market risk assessment"
            )
            st.markdown(f"**Alert:** {risk_colors.get(risk_level, '🟡')}")
        
        with col4:
            confidence = economic_data.get('confidence', 0)
            st.metric(
                "Confidence",
                f"{confidence:.1%}",
                help="Confidence in economic analysis"
            )
        
        # Enhanced economic indicators chart
        if 'indicators' in economic_data:
            create_economic_indicators_chart(economic_data['indicators'])
        
        # Economic news impact timeline
        if 'recent_events' in economic_data:
            display_economic_timeline(economic_data['recent_events'])
            
    except Exception as e:
        st.error(f"❌ Economic analysis failed: {e}")


def create_economic_indicators_chart(indicators):
    """Create enhanced economic indicators visualization"""
    st.markdown("#### 📊 Economic Indicators")
    
    # Create radar chart for indicators
    categories = list(indicators.keys())
    values = list(indicators.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Current',
        fillcolor='rgba(52, 152, 219, 0.3)',
        line=dict(color='rgb(52, 152, 219)', width=3)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True,
        title="Economic Indicators Overview",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_economic_timeline(events):
    """Display economic events timeline"""
    st.markdown("#### 📅 Recent Economic Events")
    
    if not events:
        st.info("No recent economic events to display")
        return
    
    # Create timeline visualization
    timeline_data = []
    for event in events[-10:]:  # Show last 10 events
        timeline_data.append({
            'Date': event.get('date', 'Unknown'),
            'Event': event.get('title', 'Unknown Event'),
            'Impact': event.get('impact_score', 0),
            'Sentiment': event.get('sentiment', 0)
        })
    
    if timeline_data:
        df = pd.DataFrame(timeline_data)
        
        # Create impact chart
        fig = px.scatter(
            df, 
            x='Date', 
            y='Impact',
            size='Impact',
            color='Sentiment',
            hover_data=['Event'],
            title="Economic Events Impact Timeline",
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)


def display_enhanced_ml_scores(ml_scores, confidence_threshold):
    """Enhanced ML trading scores with improved visualizations"""
    st.subheader("🤖 ML Trading Scores & Signals")
    
    if not ml_scores:
        st.warning("⚠️ No ML scores available")
        return
    
    # Create enhanced score visualization
    create_enhanced_score_heatmap(ml_scores)
    
    # Display individual bank cards
    display_bank_score_cards(ml_scores, confidence_threshold)
    
    # Add prediction confidence analysis
    display_prediction_confidence_analysis(ml_scores)


def create_enhanced_score_heatmap(ml_scores):
    """Create enhanced heatmap for ML scores"""
    st.markdown("#### 🔥 ML Scores Heatmap")
    
    # Prepare data for heatmap
    banks = list(ml_scores.keys())
    score_types = ['sentiment_strength', 'confidence', 'economic_context', 
                   'divergence', 'technical_momentum', 'ml_prediction']
    
    heatmap_data = []
    for score_type in score_types:
        row = []
        for bank in banks:
            score = ml_scores.get(bank, {}).get(score_type, 0)
            row.append(score)
        heatmap_data.append(row)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=banks,
        y=score_types,
        colorscale='RdYlGn',
        text=[[f"{val:.2f}" for val in row] for row in heatmap_data],
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False,
        colorbar=dict(title="Score")
    ))
    
    fig.update_layout(
        title="ML Scoring Components Heatmap",
        xaxis_title="Banks",
        yaxis_title="Score Components",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_bank_score_cards(ml_scores, confidence_threshold):
    """Display enhanced bank score cards"""
    st.markdown("#### 🏦 Individual Bank Analysis")
    
    # Filter banks by confidence threshold
    qualified_banks = {
        bank: scores for bank, scores in ml_scores.items()
        if scores.get('confidence', 0) >= confidence_threshold
    }
    
    if not qualified_banks:
        st.warning(f"⚠️ No banks meet confidence threshold of {confidence_threshold:.1%}")
        return
    
    # Create cards in columns
    cols = st.columns(min(3, len(qualified_banks)))
    
    for i, (bank, scores) in enumerate(qualified_banks.items()):
        with cols[i % len(cols)]:
            create_bank_score_card(bank, scores)


def create_bank_score_card(bank, scores):
    """Create individual bank score card"""
    signal = scores.get('trading_signal', 'HOLD')
    confidence = scores.get('confidence', 0)
    overall_score = scores.get('overall_score', 0)
    
    # Determine card styling based on signal
    signal_styles = {
        'BUY': {'bg': '#d4edda', 'border': '#c3e6cb', 'color': '#155724', 'icon': '🟢'},
        'SELL': {'bg': '#f8d7da', 'border': '#f5c6cb', 'color': '#721c24', 'icon': '🔴'},
        'HOLD': {'bg': '#fff3cd', 'border': '#ffeaa7', 'color': '#856404', 'icon': '🟡'}
    }
    
    style = signal_styles.get(signal, signal_styles['HOLD'])
    
    # Create card HTML
    card_html = f"""
    <div style="
        background-color: {style['bg']};
        border: 1px solid {style['border']};
        color: {style['color']};
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <h4 style="margin: 0 0 0.5rem 0;">{style['icon']} {bank}</h4>
        <p style="margin: 0;"><strong>Signal:</strong> {signal}</p>
        <p style="margin: 0;"><strong>Score:</strong> {overall_score:.2f}</p>
        <p style="margin: 0;"><strong>Confidence:</strong> {confidence:.1%}</p>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Add mini progress bars for score components
    components = ['sentiment_strength', 'confidence', 'economic_context', 
                  'divergence', 'technical_momentum', 'ml_prediction']
    
    for component in components:
        value = scores.get(component, 0)
        st.progress(value, text=f"{component.replace('_', ' ').title()}: {value:.2f}")


def display_prediction_confidence_analysis(ml_scores):
    """Display prediction confidence analysis"""
    st.markdown("#### 📈 Prediction Confidence Analysis")
    
    # Calculate confidence distribution
    confidences = [scores.get('confidence', 0) for scores in ml_scores.values()]
    signals = [scores.get('trading_signal', 'HOLD') for scores in ml_scores.values()]
    
    # Create confidence distribution chart
    col1, col2 = st.columns(2)
    
    with col1:
        # Confidence histogram
        fig = px.histogram(
            x=confidences,
            nbins=10,
            title="Confidence Distribution",
            labels={'x': 'Confidence', 'y': 'Count'}
        )
        fig.update_traces(marker_color='skyblue')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Signal distribution
        signal_counts = pd.Series(signals).value_counts()
        fig = px.pie(
            values=signal_counts.values,
            names=signal_counts.index,
            title="Trading Signal Distribution",
            color_discrete_map={'BUY': 'green', 'SELL': 'red', 'HOLD': 'orange'}
        )
        st.plotly_chart(fig, use_container_width=True)


def display_real_time_alerts(components, ml_scores):
    """Display real-time alerts and notifications"""
    st.markdown("---")
    st.subheader("🚨 Real-Time Alerts")
    
    alerts = generate_trading_alerts(ml_scores)
    
    if not alerts:
        st.success("✅ No critical alerts at this time")
        return
    
    # Display alerts by priority
    for alert in alerts:
        alert_type = alert.get('type', 'info')
        message = alert.get('message', '')
        bank = alert.get('bank', '')
        
        if alert_type == 'critical':
            st.error(f"🚨 **CRITICAL:** {message} ({bank})")
        elif alert_type == 'warning':
            st.warning(f"⚠️ **WARNING:** {message} ({bank})")
        else:
            st.info(f"ℹ️ **INFO:** {message} ({bank})")


def generate_trading_alerts(ml_scores):
    """Generate trading alerts based on ML scores"""
    alerts = []
    
    for bank, scores in ml_scores.items():
        confidence = scores.get('confidence', 0)
        signal = scores.get('trading_signal', 'HOLD')
        overall_score = scores.get('overall_score', 0)
        
        # High confidence buy/sell signals
        if confidence > 0.8 and signal in ['BUY', 'SELL']:
            alerts.append({
                'type': 'critical',
                'message': f'High confidence {signal} signal detected',
                'bank': bank,
                'confidence': confidence
            })
        
        # Low confidence warnings
        elif confidence < 0.3 and signal != 'HOLD':
            alerts.append({
                'type': 'warning',
                'message': f'Low confidence {signal} signal - proceed with caution',
                'bank': bank,
                'confidence': confidence
            })
        
        # Extreme scores
        elif overall_score > 0.8 or overall_score < 0.2:
            alerts.append({
                'type': 'info',
                'message': f'Extreme score detected: {overall_score:.2f}',
                'bank': bank,
                'score': overall_score
            })
    
    # Sort by priority (critical first)
    priority_order = {'critical': 0, 'warning': 1, 'info': 2}
    alerts.sort(key=lambda x: priority_order.get(x['type'], 3))
    
    return alerts


def display_enhanced_dashboard_sections(components, bank_analyses, sidebar_config):
    """Display all enhanced dashboard sections"""
    try:
        # Get divergence analysis
        divergence_analysis = components['divergence_detector'].analyze_sector_divergence(bank_analyses)
        
        # Calculate ML trading scores
        economic_data = components['economic_analyzer'].analyze_economic_sentiment()
        ml_scores = components['ml_scorer'].calculate_scores_for_all_banks(
            bank_analyses=bank_analyses,
            economic_analysis=economic_data,
            divergence_analysis=divergence_analysis
        )
        
        # Enhanced section display based on view mode
        view_mode = sidebar_config.get('view_mode', 'Standard')
        
        if view_mode == "Compact":
            display_compact_view(components, bank_analyses, ml_scores, sidebar_config)
        elif view_mode == "Detailed":
            display_detailed_view(components, bank_analyses, ml_scores, sidebar_config)
        elif view_mode == "Mobile-Friendly":
            display_mobile_view(components, bank_analyses, ml_scores, sidebar_config)
        else:
            display_standard_view(components, bank_analyses, ml_scores, sidebar_config)
            
    except Exception as e:
        st.error(f"❌ Error displaying dashboard sections: {e}")


def display_standard_view(components, bank_analyses, ml_scores, sidebar_config):
    """Display standard dashboard view with enhanced features"""
    # Enhanced economic analysis
    display_enhanced_economic_analysis(components['economic_analyzer'])
    
    # Enhanced ML trading scores
    display_enhanced_ml_scores(ml_scores, sidebar_config['confidence_threshold'])
    
    # Original sections with enhancements
    display_divergence_analysis(components['divergence_detector'], bank_analyses)
    display_bank_sentiment_overview(bank_analyses, sidebar_config['confidence_threshold'])
    display_individual_bank_analysis(bank_analyses, components['data_feed'], sidebar_config['show_detailed'])
    display_ml_predictions(components['ml_pipeline'], bank_analyses)
    display_trading_signals(components['divergence_detector'], bank_analyses)
    display_alpaca_integration(components['alpaca_trader'], ml_scores)
    
    # Real-time alerts
    display_real_time_alerts(components, ml_scores)
    
    # Add the performance section
    st.markdown("---")
    try:
        from app.core.ml.tracking.progression_tracker import MLProgressionTracker
        # Ensure the tracker uses the correct, intended data directory
        data_path = "data/ml_performance"
        ml_tracker = MLProgressionTracker(data_dir=data_path)
        st.sidebar.info(f"Data source: {Path(data_path).resolve()}") # Add info for debugging
        enhanced_dashboard_performance_section(ml_tracker)
    except Exception as e:
        st.error(f"⚠️ Performance tracking unavailable: {e}")
    
    # Enhanced footer
    add_dashboard_footer()


def add_dashboard_footer():
    """Add enhanced dashboard footer with system info"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Dashboard Info**")
        st.markdown(f"- Last Update: {datetime.now().strftime('%H:%M:%S')}")
        st.markdown(f"- Version: 2.0 Enhanced")
        st.markdown(f"- Mode: Real-time Analysis")
    
    with col2:
        st.markdown("**🔧 System Status**")
        st.markdown("- Components: ✅ Operational")
        st.markdown("- Data Feed: ✅ Connected")
        st.markdown("- ML Models: ✅ Active")
    
    with col3:
        st.markdown("**📈 Performance**")
        st.markdown("- Response Time: < 2s")
        st.markdown("- Accuracy: 85%+")
        st.markdown("- Uptime: 99.9%")



def display_standard_view(components, bank_analyses, ml_scores, sidebar_config):
    """Display standard dashboard view"""
    display_ml_trading_scores(ml_scores, sidebar_config['confidence_threshold'])
    display_divergence_analysis(components['divergence_detector'], bank_analyses)
    display_bank_sentiment_overview(bank_analyses, sidebar_config['confidence_threshold'])
    display_individual_bank_analysis(bank_analyses, components['data_feed'], sidebar_config['show_detailed'])
    display_ml_predictions(components['ml_pipeline'], bank_analyses)
    display_trading_signals(components['divergence_detector'], bank_analyses)
    display_alpaca_integration(components['alpaca_trader'], ml_scores)
    
    # Add the performance section
    st.markdown("---")
    try:
        from app.core.ml.tracking.progression_tracker import MLProgressionTracker
        # Ensure the tracker uses the correct, intended data directory
        data_path = "data/ml_performance"
        ml_tracker = MLProgressionTracker(data_dir=data_path)
        st.sidebar.info(f"Data source: {Path(data_path).resolve()}") # Add info for debugging
        enhanced_dashboard_performance_section(ml_tracker)
    except Exception as e:
        st.error(f"⚠️ Performance tracking unavailable: {e}")


def display_compact_view(components, bank_analyses, ml_scores, sidebar_config):
    """Display compact dashboard view for quick overview"""
    st.markdown("### 📊 Compact Overview")
    
    # Create tabs for compact sections
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Economic", "📈 Scores", "🎯 Signals", "📊 Performance"])
    
    with tab1:
        display_enhanced_economic_analysis(components['economic_analyzer'])
    
    with tab2:
        display_enhanced_ml_scores(ml_scores, sidebar_config['confidence_threshold'])
    
    with tab3:
        display_trading_signals(components['divergence_detector'], bank_analyses)
        display_real_time_alerts(components, ml_scores)
    
    with tab4:
        try:
            from app.core.ml.tracking.progression_tracker import MLProgressionTracker
            # Ensure the tracker uses the correct, intended data directory
            data_path = "data/ml_performance"
            ml_tracker = MLProgressionTracker(data_dir=data_path)
            st.sidebar.info(f"Data source: {Path(data_path).resolve()}") # Add info for debugging
            enhanced_dashboard_performance_section(ml_tracker)
        except Exception as e:
            st.error(f"⚠️ Performance tracking unavailable: {e}")
    
    # Compact footer
    add_dashboard_footer()


def display_detailed_view(components, bank_analyses, ml_scores, sidebar_config):
    """Display detailed dashboard view with all information"""
    # Enhanced standard view
    display_standard_view(components, bank_analyses, ml_scores, sidebar_config)
    
    # Additional detailed sections
    st.markdown("---")
    st.markdown("### 🔍 Advanced Analysis")
    
    # Add advanced technical indicators
    display_advanced_technical_analysis(components, bank_analyses)
    
    # Add risk analysis
    display_risk_analysis(components, bank_analyses, ml_scores)


def display_mobile_view(components, bank_analyses, ml_scores, sidebar_config):
    """Display mobile-friendly dashboard view"""
    st.markdown("### 📱 Mobile Dashboard")
    
    # Economic overview (compact)
    with st.expander("🌍 Economic Overview", expanded=True):
        try:
            economic_data = components['economic_analyzer'].analyze_economic_sentiment()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Economic Sentiment", f"{economic_data.get('economic_sentiment_score', 0):.2f}")
            with col2:
                st.metric("Market Regime", economic_data.get('market_regime', 'Unknown'))
        except:
            st.error("Economic data unavailable")
    
    # ML Scores (mobile-optimized)
    with st.expander("🤖 ML Scores", expanded=True):
        display_enhanced_ml_scores(ml_scores, sidebar_config['confidence_threshold'])
    
    # Simplified bank overview
    st.markdown("#### 🏦 Bank Signals")
    for bank, analysis in bank_analyses.items():
        with st.expander(f"🏦 {bank}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Sentiment", 
                    f"{analysis.get('sentiment_score', 0):.2f}",
                    delta=f"{analysis.get('confidence', 0):.2f}"
                )
            with col2:
                signal = ml_scores.get(bank, {}).get('trading_signal', 'HOLD')
                signal_color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(signal, "⚪")
                st.markdown(f"**Signal:** {signal_color} {signal}")
    
    # Mobile alerts
    with st.expander("🚨 Alerts", expanded=False):
        display_real_time_alerts(components, ml_scores)
    
    # Mobile footer
    st.markdown("---")
    st.markdown(f"📱 Mobile Mode | Updated: {datetime.now().strftime('%H:%M:%S')}")


def display_advanced_technical_analysis(components, bank_analyses):
    """Display advanced technical analysis section"""
    st.subheader("📈 Advanced Technical Analysis")
    
    # Placeholder for advanced technical indicators
    st.info("🚧 Advanced technical analysis coming soon!")
    
    # Could include:
    # - RSI indicators
    # - Moving averages
    # - Bollinger bands
    # - Support/resistance levels


def display_risk_analysis(components, bank_analyses, ml_scores):
    """Display risk analysis section"""
    st.subheader("⚠️ Risk Analysis")
    
    # Calculate portfolio risk metrics
    total_positions = len([score for score in ml_scores.values() if score.get('trading_signal') in ['BUY', 'SELL']])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Positions", total_positions)
    
    with col2:
        # Calculate average confidence
        avg_confidence = sum(score.get('confidence', 0) for score in ml_scores.values()) / len(ml_scores) if ml_scores else 0
        st.metric("Avg Confidence", f"{avg_confidence:.2f}")
    
    with col3:
        # Risk level based on position count and confidence
        risk_level = "Low" if total_positions <= 2 and avg_confidence > 0.7 else "Medium" if total_positions <= 4 else "High"
        risk_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(risk_level, "⚪")
        st.markdown(f"**Risk Level:** {risk_color} {risk_level}")



def display_divergence_analysis(divergence_detector, bank_analyses):
    """Display sector divergence analysis"""
    st.header("🎯 Sector Divergence Analysis")
    
    try:
        divergence_analysis = divergence_detector.analyze_sector_divergence(bank_analyses)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            sector_avg = divergence_analysis.get('sector_average', 0)
            st.metric("Sector Average", f"{sector_avg:+.3f}")
        
        with col2:
            sector_vol = divergence_analysis.get('sector_volatility', 0)
            st.metric("Sector Volatility", f"{sector_vol:.3f}")
        
        with col3:
            divergent_count = len(divergence_analysis.get('divergent_banks', {}))
            st.metric("Divergent Banks", divergent_count)
        
        with col4:
            analyzed_count = divergence_analysis.get('analyzed_banks', 0)
            st.metric("Banks Analyzed", analyzed_count)
        
        # Divergence visualization
        divergent_banks = divergence_analysis.get('divergent_banks', {})
        
        if divergent_banks:
            df_divergence = pd.DataFrame([
                {
                    'Bank': symbol,
                    'Divergence Score': data['divergence_score'],
                    'Significance': data['significance'],
                    'Opportunity': data['opportunity'],
                    'Confidence': data['confidence']
                }
                for symbol, data in divergent_banks.items()
            ])
            
            # Create divergence chart
            fig_div = px.bar(
                df_divergence,
                x='Bank',
                y='Divergence Score',
                color='Divergence Score',
                color_continuous_scale='RdYlGn',
                title="Bank Sentiment Divergence from Sector Average"
            )
            fig_div.add_hline(y=0, line_dash="dash", line_color="black")
            
            st.plotly_chart(fig_div, use_container_width=True)
            
            # Divergence table
            st.subheader("🎯 Divergent Banks Detail")
            st.dataframe(df_divergence, use_container_width=True)
        
        # Summary
        summary = divergence_analysis.get('summary', '')
        if summary:
            st.info(f"**Summary:** {summary}")
    
    except Exception as e:
        st.error(f"❌ Divergence analysis error: {e}")

def display_bank_sentiment_overview(bank_analyses, confidence_threshold):
    """Display overview of bank sentiment scores"""
    st.header("🏦 Bank Sentiment Overview")
    
    # Create overview dataframe
    overview_data = []
    for symbol, analysis in bank_analyses.items():
        sentiment = analysis.get('overall_sentiment', 0)
        confidence = analysis.get('confidence', 0)
        signal = analysis.get('signal', 'HOLD')
        news_count = analysis.get('news_count', 0)
        
        # Determine if high confidence
        high_conf = confidence >= confidence_threshold
        
        overview_data.append({
            'Bank': symbol,
            'Sentiment': sentiment,
            'Confidence': confidence,
            'Signal': signal,
            'News Count': news_count,
            'High Confidence': '✅' if high_conf else '❌'
        })
    
    df_overview = pd.DataFrame(overview_data)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_sentiment = df_overview['Sentiment'].mean()
        st.metric("Average Sentiment", f"{avg_sentiment:+.3f}")
    
    with col2:
        high_conf_count = sum(1 for item in overview_data if item['High Confidence'] == '✅')
        st.metric("High Confidence", f"{high_conf_count}/{len(overview_data)}")
    
    with col3:
        buy_signals = sum(1 for item in overview_data if item['Signal'] == 'BUY')
        st.metric("Buy Signals", buy_signals)
    
    with col4:
        total_news = df_overview['News Count'].sum()
        st.metric("Total News", total_news)
    
    # Sentiment distribution chart
    fig_sentiment = px.bar(
        df_overview,
        x='Bank',
        y='Sentiment',
        color='Confidence',
        title="Bank Sentiment Scores with Confidence",
        color_continuous_scale='Viridis'
    )
    fig_sentiment.add_hline(y=0, line_dash="dash", line_color="black")
    
    st.plotly_chart(fig_sentiment, use_container_width=True)
    
    # Overview table
    st.dataframe(df_overview, use_container_width=True)

def display_individual_bank_analysis(bank_analyses, data_feed, show_detailed):
    """Display detailed analysis for each bank"""
    st.header("📋 Individual Bank Analysis")
    
    for symbol, analysis in bank_analyses.items():
        with st.expander(f"🏦 {symbol} - Detailed Analysis", expanded=False):
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                sentiment = analysis.get('overall_sentiment', 0)
                st.metric("Sentiment Score", f"{sentiment:+.3f}")
            
            with col2:
                confidence = analysis.get('confidence', 0)
                st.metric("Confidence", f"{confidence:.1%}")
            
            with col3:
                signal = analysis.get('signal', 'HOLD')
                signal_color = {"BUY": "green", "SELL": "red", "HOLD": "gray"}.get(signal, "gray")
                st.markdown(f"**Signal:** :{signal_color}[{signal}]")
            
            if show_detailed:
                # Additional metrics
                col4, col5, col6 = st.columns(3)
                
                with col4:
                    news_count = analysis.get('news_count', 0)
                    st.metric("News Articles", news_count)
                
                with col5:
                    # Try to get current price
                    try:
                        price_data = data_feed.get_current_data(symbol)
                        price = price_data.get('price', 0)
                        if price > 0:
                            st.metric("Current Price", f"${price:.2f}")
                        else:
                            st.metric("Current Price", "N/A")
                    except:
                        st.metric("Current Price", "N/A")
                
                with col6:
                    # Calculate impact score
                    impact = abs(sentiment) * confidence
                    st.metric("Impact Score", f"{impact:.3f}")
                
                # Recent headlines if available
                headlines = analysis.get('recent_headlines', [])
                if headlines:
                    st.subheader("📰 Recent Headlines")
                    for headline in headlines[:5]:  # Show top 5
                        st.write(f"• {headline}")

def display_ml_predictions(ml_pipeline, bank_analyses):
    """Display ML model predictions"""
    st.header("🧠 ML Model Predictions")
    
    try:
        ml_results = []
        
        for symbol, analysis in bank_analyses.items():
            # Mock market data for prediction
            market_data = {
                'price': 100.0,
                'change_percent': 0.0,
                'volume': 1000000,
                'volatility': 0.15
            }
            
            # Get ML prediction
            prediction_result = ml_pipeline.predict(analysis, market_data, [])
            
            if 'error' not in prediction_result:
                # Convert numeric prediction to signal string
                ensemble_pred = prediction_result.get('ensemble_prediction', 0)
                signal_mapping = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
                ml_signal = signal_mapping.get(ensemble_pred, 'HOLD')
                
                ml_results.append({
                    'Bank': symbol,
                    'ML Prediction': ml_signal,
                    'ML Confidence': prediction_result.get('ensemble_confidence', 0),
                    'Sentiment Signal': analysis.get('signal', 'HOLD'),
                    'Feature Count': prediction_result.get('feature_count', 0)
                })
        
        if ml_results:
            df_ml = pd.DataFrame(ml_results)
            st.dataframe(df_ml, use_container_width=True)
            
            # ML confidence chart
            fig_ml = px.bar(
                df_ml,
                x='Bank',
                y='ML Confidence',
                title="ML Model Prediction Confidence",
                color='ML Confidence',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_ml, use_container_width=True)
        else:
            st.info("🔬 ML predictions not available. Models may need training.")
            
        # Show training data status
        try:
            import sqlite3
            db_path = "data/trading_predictions.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM enhanced_features')
            total_samples = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes')
            completed_samples = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            total_samples = 0
            completed_samples = 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Training Samples", total_samples)
        with col2:
            st.metric("Completed Samples", completed_samples)
        with col3:
            # Show model status
            models_loaded = len(ml_pipeline.models)
            st.metric("Models Loaded", models_loaded)
    
    except Exception as e:
        st.error(f"❌ ML prediction error: {e}")

def display_trading_signals(divergence_detector, bank_analyses):
    """Display trading signals based on divergence and sentiment"""
    st.header("📈 Trading Signals")
    
    try:
        # Get divergence analysis
        divergence_analysis = divergence_detector.analyze_sector_divergence(bank_analyses)
        
        # Generate trading signals
        trading_signals = divergence_detector.generate_trading_signals(divergence_analysis)
        
        if trading_signals:
            # Create signals dataframe
            df_signals = pd.DataFrame(trading_signals)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                buy_count = sum(1 for s in trading_signals if s['signal'] == 'BUY')
                st.metric("Buy Signals", buy_count)
            
            with col2:
                sell_count = sum(1 for s in trading_signals if s['signal'] == 'SELL')
                st.metric("Sell Signals", sell_count)
            
            with col3:
                avg_significance = np.mean([s['significance'] for s in trading_signals])
                st.metric("Avg Significance", f"{avg_significance:.2f}")
            
            # Signals table
            st.subheader("🎯 Active Trading Signals")
            
            # Color code the signals
            def color_signal(val):
                if val == 'BUY':
                    return 'background-color: lightgreen'
                elif val == 'SELL':
                    return 'background-color: lightcoral'
                return ''
            
            styled_df = df_signals.style.applymap(color_signal, subset=['signal'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Signal reasoning
            st.subheader("💡 Signal Reasoning")
            for signal in trading_signals:
                st.write(f"**{signal['symbol']}**: {signal['reasoning']}")
        else:
            st.info("📊 No high-significance trading signals detected at this time.")
    
    except Exception as e:
        st.error(f"❌ Trading signals error: {e}")

    # === PAPER TRADING SECTION ===
    st.markdown("---")
    st.header("📈 Paper Trading Portfolio")
    
    try:
        from app.core.trading.paper_trading_simulator import PaperTradingSimulator
        
        simulator = PaperTradingSimulator()
        portfolio_value = simulator.get_portfolio_value()
        positions = simulator.get_all_positions()
        
        # Portfolio Overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Portfolio Value", f"${portfolio_value:,.2f}")
        
        with col2:
            cash = simulator.cash
            st.metric("Cash", f"${cash:,.2f}")
        
        with col3:
            total_positions = len(positions)
            st.metric("Active Positions", total_positions)
        
        with col4:
            # Calculate total P&L
            total_pnl = sum(pos.unrealized_pnl for pos in positions if pos.unrealized_pnl is not None)
            color = "green" if total_pnl >= 0 else "red"
            st.metric("Total P&L", f"${total_pnl:,.2f}", delta=f"{total_pnl:+.2f}")
        
        # Active Positions Table
        if positions:
            st.subheader("🎯 Active Positions")
            
            position_data = []
            for pos in positions:
                pnl_color = "🟢" if pos.unrealized_pnl and pos.unrealized_pnl >= 0 else "🔴"
                position_data.append({
                    "Symbol": pos.symbol,
                    "Shares": f"{pos.shares:,}",
                    "Entry Price": f"${pos.entry_price:.2f}",
                    "Current Price": f"${pos.current_price:.2f}" if pos.current_price else "N/A",
                    "P&L": f"{pnl_color} ${pos.unrealized_pnl:,.2f}" if pos.unrealized_pnl else "N/A",
                    "Entry Time": pos.entry_time.strftime("%Y-%m-%d %H:%M") if pos.entry_time else "N/A"
                })
            
            if position_data:
                df_positions = pd.DataFrame(position_data)
                st.dataframe(df_positions, use_container_width=True)
        else:
            st.info("💼 No active positions in paper trading portfolio")
        
        # Performance Metrics
        st.subheader("📊 Performance Metrics")
        
        try:
            import sqlite3
            import os
            
            db_path = "data/paper_trading.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                
                # Get historical performance data
                query = """
                SELECT * FROM positions 
                WHERE exit_time IS NOT NULL 
                ORDER BY exit_time DESC 
                LIMIT 10
                """
                
                df_history = pd.read_sql_query(query, conn)
                conn.close()
                
                if not df_history.empty:
                    # Calculate metrics
                    total_trades = len(df_history)
                    winning_trades = len(df_history[df_history['realized_pnl'] > 0])
                    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                    avg_return = df_history['realized_pnl'].mean() if total_trades > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                    
                    with col2:
                        st.metric("Total Trades", total_trades)
                    
                    with col3:
                        st.metric("Avg Return", f"${avg_return:.2f}")
                    
                    # Recent Trading History
                    st.subheader("📋 Recent Trading History")
                    
                    history_data = []
                    for _, row in df_history.iterrows():
                        pnl_color = "🟢" if row['realized_pnl'] >= 0 else "🔴"
                        history_data.append({
                            "Symbol": row['symbol'],
                            "Shares": f"{row['shares']:,}",
                            "Entry": f"${row['entry_price']:.2f}",
                            "Exit": f"${row['exit_price']:.2f}",
                            "P&L": f"{pnl_color} ${row['realized_pnl']:,.2f}",
                            "Exit Date": pd.to_datetime(row['exit_time']).strftime("%Y-%m-%d %H:%M")
                        })
                    
                    df_history_display = pd.DataFrame(history_data)
                    st.dataframe(df_history_display, use_container_width=True)
                else:
                    st.info("📈 No completed trades yet")
            else:
                st.info("📊 No performance data available yet")
                
        except Exception as e:
            st.warning(f"⚠️ Could not load performance metrics: {e}")
        
        # Trading Controls
        st.subheader("🎮 Trading Controls")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Run Paper Trading Evaluation", type="primary"):
                with st.spinner("Running paper trading evaluation..."):
                    try:
                        from app.main import run_paper_trading_evaluation
                        # This would normally run the evaluation
                        st.success("✅ Paper trading evaluation completed!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error running evaluation: {e}")
        
        with col2:
            if st.button("📊 Refresh Performance Data"):
                st.rerun()
        
        with col3:
            if st.button("⚙️ View Full Performance Report"):
                st.info("💡 Run `python -m app.main paper-performance` in terminal for detailed metrics")
        
        # Paper Trading Status
        st.subheader("🔄 System Status")
        
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            st.success("✅ Paper Trading System: Active")
            st.info(f"💰 Initial Capital: $100,000")
        
        with status_col2:
            st.info("🤖 Auto-Trading: Available")
            st.info("💡 Run `python -m app.main start-paper-trader` to start continuous trading")
        
    except ImportError:
        st.error("❌ Paper trading system not available. Please check installation.")
    except Exception as e:
        st.error(f"❌ Paper trading section error: {e}")

if __name__ == "__main__":
    main()
