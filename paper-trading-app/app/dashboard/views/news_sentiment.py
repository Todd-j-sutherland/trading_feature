import streamlit as st
import sys
import os

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from app.dashboard.components.professional.ui_components import create_section_header

def display_news_sentiment_analysis(dashboard):
    """Display news and sentiment analysis"""
    create_section_header(
        "News & Sentiment Analysis", 
        "Latest news headlines and sentiment impact analysis",
        "📰"
    )
    
    # Load sentiment data
    all_data = dashboard.load_sentiment_data()
    
    # Aggregate recent news from all banks
    recent_news = []
    
    for symbol, data in all_data.items():
        if data:
            latest = dashboard.get_latest_analysis(data)
            if latest and 'recent_headlines' in latest:
                headlines = latest['recent_headlines']
                for headline in headlines[:3]:  # Top 3 from each bank
                    if headline:
                        recent_news.append({
                            'Bank': dashboard.bank_names.get(symbol, symbol),
                            'Headline': headline,
                            'Symbol': symbol,
                            'Sentiment': latest.get('overall_sentiment', 0)
                        })
    
    if recent_news:
        st.markdown("### 📰 Latest Market Headlines")
        
        for news in recent_news[:10]:  # Show top 10
            sentiment = news['Sentiment']
            
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; 
                       border-left: 4px solid {'#27ae60' if sentiment > 0.1 else '#e74c3c' if sentiment < -0.1 else '#f39c12'};">
                <strong>{'🟢' if sentiment > 0.1 else '🔴' if sentiment < -0.1 else '🟡'} {news['Bank']} ({news['Symbol']})</strong><br>
                {news['Headline']}<br>
                <small>Sentiment: {sentiment:+.3f}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No recent news data available")
