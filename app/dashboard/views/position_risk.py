import streamlit as st
from datetime import datetime, timedelta
import sys
import os

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from app.dashboard.components.professional.ui_components import (
    create_section_header,
    display_professional_metrics,
    display_position_recommendations,
    display_risk_breakdown,
    display_market_context,
    display_action_plan,
    display_fallback_risk_assessment,
    create_recovery_probability_chart,
)

def display_position_risk_section(dashboard):
    """Display the Position Risk Assessor section"""
    if not dashboard.position_risk_available:
        st.markdown("""
        <div class="alert alert-warning">
            <strong>⚠️ Position Risk Assessor Unavailable</strong><br>
            The Position Risk Assessor module is not available. Please ensure 
            <code>src/position_risk_assessor.py</code> is properly installed.
        </div>
        """, unsafe_allow_html=True)
        return
    
    create_section_header(
        "Position Risk Assessment", 
        "ML-powered analysis for existing positions and recovery predictions",
        "🎯"
    )
    
    with st.form("position_risk_form"):
        st.markdown("""
        <div class="form-section">
            <h4>📊 Position Details</h4>
            <p>Enter your position information for comprehensive ML-powered risk analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            symbol = st.selectbox(
                "📈 Select Bank:",
                options=list(dashboard.bank_symbols),
                format_func=lambda x: f"🏦 {dashboard.bank_names.get(x, x)} ({x})",
                key="position_tracker_symbol"
            )
        
        with col2:
            entry_price = st.number_input("💰 Entry Price ($):", min_value=0.01, value=100.00, step=0.01, format="%.2f")
        
        with col3:
            current_price = st.number_input("📊 Current Price ($):", min_value=0.01, value=dashboard.get_current_price(symbol) or 99.00, step=0.01, format="%.2f")
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            position_type = st.selectbox("📍 Position Type:", options=['long', 'short'], format_func=lambda x: f"📈 Long" if x == 'long' else f"📉 Short")
        
        with col5:
            entry_date = st.date_input("📅 Entry Date:", value=datetime.now().date() - timedelta(days=7))
        
        with col6:
            position_size = st.number_input("📦 Position Size ($):", min_value=100.0, value=10000.0, step=100.0)
        
        submitted = st.form_submit_button("🎯 Perform Advanced Risk Assessment", use_container_width=True, type="primary")
    
    if submitted:
        with st.spinner("🔄 Analyzing position risk..."):
            try:
                from app.core.trading.risk_management import PositionRiskAssessor
                assessor = PositionRiskAssessor()
                result = assessor.assess_position_risk(
                    symbol=symbol,
                    entry_price=entry_price,
                    current_price=current_price,
                    position_type=position_type,
                    entry_date=datetime.combine(entry_date, datetime.min.time())
                )
                
                if 'error' in result:
                    st.error(f"❌ Error in risk assessment: {result['error']}")
                else:
                    display_risk_assessment_results(dashboard, result, symbol, entry_price, current_price, position_type)
            except Exception as e:
                st.error(f"❌ Error initializing Position Risk Assessor: {str(e)}")
                display_fallback_risk_assessment(dashboard, symbol, entry_price, current_price, position_type)

def display_risk_assessment_results(dashboard, result: dict, symbol: str, entry_price: float, current_price: float, position_type: str):
    """Display comprehensive risk assessment results with enhanced UI"""
    bank_name = dashboard.bank_names.get(symbol, symbol)
    current_return = result.get('current_return_pct', 0)
    position_status = result.get('position_status', 'unknown')
    status_icon = "🟢" if position_status == 'profitable' else "🔴"
    risk_metrics = result.get('risk_metrics', {})
    overall_risk_score = risk_metrics.get('overall_risk_score', 5)
    
    if overall_risk_score <= 3: risk_level, risk_icon = "Low", "🟢"
    elif overall_risk_score <= 6: risk_level, risk_icon = "Medium", "🟡"
    else: risk_level, risk_icon = "High", "🔴"
    
    st.markdown(f"""
    <div class="risk-results-container">
        <div class="risk-header">
            <h3>{status_icon} Position Risk Assessment: {bank_name} ({symbol})</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if 'recovery_predictions' in result:
        st.markdown("### 🔮 Recovery Predictions")
        create_recovery_probability_chart(result['recovery_predictions'])
    
    if 'risk_metrics' in result:
        st.markdown("### ⚠️ Risk Analysis")
        display_risk_breakdown(result['risk_metrics'])
    
    if 'recommendations' in result:
        st.markdown("### 💡 AI Recommendations")
        display_position_recommendations(result['recommendations'])
    
    if 'market_context' in result:
        st.markdown("### 🌍 Market Context")
        display_market_context(result['market_context'], symbol)
    
    if 'recommendations' in result and 'risk_metrics' in result:
        st.markdown("### 🎯 Action Plan")
        display_action_plan(result['recommendations'], current_return, overall_risk_score)
