import streamlit as st
import sys
import os

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from app.dashboard.components.professional.ui_components import (
    create_section_header,
    display_bank_analysis,
)

def display_individual_bank_analysis(dashboard):
    """Display detailed analysis for individual banks"""
    try:
        create_section_header(
            "Individual Bank Analysis", 
            "Comprehensive sentiment, technical, and risk analysis for specific banks",
            "🏦"
        )
        
        # Bank selection
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_bank = st.selectbox(
                "🏦 Select Bank for Detailed Analysis:",
                options=dashboard.bank_symbols,
                format_func=lambda x: f"🏦 {dashboard.bank_names.get(x, x)} ({x})",
                key="individual_bank_analysis_selectbox"
            )
        
        with col2:
            if st.button("🔄 Refresh Analysis", use_container_width=True):
                dashboard.technical_data.pop(selected_bank, None)
                st.cache_data.clear()
                st.rerun()
        
        # Load and display analysis
        all_data = dashboard.load_sentiment_data()
        bank_data = all_data.get(selected_bank, [])
        
        if bank_data:
            display_bank_analysis(dashboard, selected_bank, bank_data)
        else:
            st.warning(f"⚠️ No analysis data available for {dashboard.bank_names.get(selected_bank, selected_bank)}")
            
    except Exception as e:
        st.error(f"❌ Error in Individual Bank Analysis: {str(e)}")
        st.write("Debug info:")
        st.write(f"Dashboard type: {type(dashboard)}")
        st.write(f"Bank symbols available: {hasattr(dashboard, 'bank_symbols')}")
        st.write(f"Bank names available: {hasattr(dashboard, 'bank_names')}")
        import traceback
        st.code(traceback.format_exc())
