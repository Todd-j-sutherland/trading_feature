#!/usr/bin/env python3
"""
Minimal Streamlit Test - Cache Debugging
Run with: streamlit run cache_test.py
"""

import streamlit as st
import time
import sys
sys.path.append('.')

from datetime import datetime
from dashboard import compute_overview_metrics
from enhanced_confidence_metrics import compute_enhanced_confidence_metrics

# Force clear cache
st.cache_data.clear()

st.title("🔍 Cache Debug Test")
st.write(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Force refresh button
if st.button("🔥 Force Refresh"):
    st.cache_data.clear()
    st.rerun()

# Test the functions directly
st.subheader("Direct Function Test")

with st.spinner("Testing functions..."):
    # Call functions directly
    overview = compute_overview_metrics()
    confidence = compute_enhanced_confidence_metrics()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Overview Metrics")
    ml_data = overview['ml']
    st.metric("Win Rate", f"{ml_data['win_rate']:.1%}")
    st.metric("Avg Return", f"{ml_data['avg_return']*100:.1f}%")
    st.metric("Completed Trades", ml_data['outcomes_completed'])
    st.metric("Total Features", ml_data['predictions'])
    
    st.write("**Raw Values:**")
    st.write(f"- win_rate: {ml_data['win_rate']}")
    st.write(f"- avg_return: {ml_data['avg_return']}")

with col2:
    st.subheader("Confidence Metrics")
    overall_conf = confidence['overall_integration']
    st.metric("Overall Confidence", f"{overall_conf['confidence']:.1%}")
    st.metric("Status", overall_conf['status'])
    
    st.write("**Component Summary:**")
    summary = confidence['component_summary']
    st.write(f"- Features: {summary['total_features']}")
    st.write(f"- Outcomes: {summary['completed_outcomes']}")

# Expected values
st.subheader("✅ Expected Values")
st.success(f"""
**These are the correct values that should appear:**
- Win Rate: 65.7%
- Average Return: 44.7%
- Completed Trades: 178
- Overall Confidence: 76.3%

**If you see different values above, there's a caching issue!**
""")

st.subheader("🔧 Troubleshooting")
st.info("""
**If values are wrong:**
1. Click "Force Refresh" button above
2. Press Ctrl+F5 to hard refresh browser
3. Clear browser cache completely
4. Try in incognito/private mode
5. Close and restart Streamlit server
""")

# Auto-refresh every 30 seconds
st.markdown("---")
st.caption("This page auto-refreshes to show live data")
time.sleep(1)
st.rerun()
