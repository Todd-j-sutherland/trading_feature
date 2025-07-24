import streamlit as st
import pandas as pd
import sys
import os

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from app.dashboard.components.professional.ui_components import create_section_header

def display_system_status(dashboard):
    """Display system status and diagnostics"""
    create_section_header(
        "System Status", 
        "Technical system diagnostics and data quality metrics",
        "⚙️"
    )
    
    # System metrics
    st.markdown("### 🔧 System Diagnostics")
    
    # Check data availability
    all_data = dashboard.load_sentiment_data()
    data_quality = []
    
    for symbol in dashboard.bank_symbols:
        symbol_data = all_data.get(symbol, [])
        
        data_quality.append({
            'Bank': dashboard.bank_names.get(symbol, symbol),
            'Symbol': symbol,
            'Records': len(symbol_data),
            'Latest': symbol_data[-1].get('timestamp', 'N/A')[:10] if symbol_data else 'N/A',
            'Status': '✅ Good' if len(symbol_data) > 5 else '⚠️ Limited' if len(symbol_data) > 0 else '❌ No Data'
        })
    
    st.dataframe(pd.DataFrame(data_quality), use_container_width=True, hide_index=True)
    
    # System information
    st.markdown("### ℹ️ System Information")
    
    system_info = {
        'Python Version': sys.version.split()[0],
        'Streamlit Version': st.__version__,
        'Total Banks Monitored': len(dashboard.bank_symbols),
        'Position Risk Assessor': 'Available' if dashboard.position_risk_available else 'Not Available',
        'Technical Analysis': 'Available',
        'Dashboard Version': '2.0.0'
    }
    
    for key, value in system_info.items():
        st.write(f"**{key}:** {value}")
    
    # Show data loading status at bottom
    with st.expander("📊 Data Loading Status", expanded=False):
        all_data_check = dashboard.load_sentiment_data()
        for symbol, data in all_data_check.items():
            bank_name = dashboard.bank_names.get(symbol, symbol)
            status = f"✅ {len(data)} records" if data else "❌ No data"
            st.write(f"**{bank_name}:** {status}")
