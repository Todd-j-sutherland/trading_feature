import streamlit as st
import pandas as pd
import logging
import sys
import os

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from app.dashboard.components.professional.ui_components import create_section_header

logger = logging.getLogger(__name__)

def display_technical_analysis(dashboard):
    """Display technical analysis view"""
    create_section_header(
        "Technical Analysis", 
        "Advanced technical indicators and market analysis",
        "📊"
    )
    
    # Technical analysis for all banks
    st.markdown("### 📈 Technical Analysis Summary")
    
    # Create technical summary
    technical_summary = []
    
    for symbol in dashboard.bank_symbols:
        try:
            tech_analysis = dashboard.get_technical_analysis(symbol)
            if tech_analysis and 'current_price' in tech_analysis:
                
                current_price = tech_analysis.get('current_price', 0)
                recommendation = tech_analysis.get('recommendation', 'HOLD')
                momentum_score = tech_analysis.get('momentum', {}).get('score', 0)
                rsi = tech_analysis.get('indicators', {}).get('rsi', 50)
                
                technical_summary.append({
                    'Bank': dashboard.bank_names.get(symbol, symbol),
                    'Symbol': symbol,
                    'Price': f"${current_price:.2f}",
                    'Recommendation': recommendation,
                    'Momentum': f"{momentum_score:.1f}",
                    'RSI': f"{rsi:.1f}",
                    'Status': '🟢' if 'BUY' in recommendation else '🔴' if 'SELL' in recommendation else '🟡'
                })
        except Exception as e:
            logger.warning(f"Error getting technical analysis for {symbol}: {e}")
    
    if technical_summary:
        tech_df = pd.DataFrame(technical_summary)
        st.dataframe(tech_df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Technical analysis data is currently unavailable")
