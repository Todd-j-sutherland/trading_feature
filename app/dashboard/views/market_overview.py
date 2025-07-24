import streamlit as st
import pandas as pd
import sys
import os

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from app.dashboard.components.professional.ui_components import (
    create_section_header,
    display_professional_metrics,
    create_sentiment_overview_chart,
    create_confidence_distribution_chart,
    display_confidence_legend,
    display_sentiment_scale,
)

def display_market_overview(dashboard):
    """Display market overview with professional charts"""
    try:
        create_section_header(
            "Market Overview", 
            "Real-time sentiment analysis and market indicators for all ASX banks",
            "📈"
        )
        
        # Load data
        with st.spinner("📊 Loading market data..."):
            all_data = dashboard.load_sentiment_data()
        
        # Debug info
        st.info(f"🔍 Debug: Found {len(all_data)} banks with {sum(len(data) for data in all_data.values())} total data points")
        
        if not any(all_data.values()):
            st.warning("⚠️ No sentiment data available. Please run data collection first.")
            st.markdown("""
            ### 🚀 Getting Started
            
            To see data in this dashboard, you need to run the data collection process:
            
            1. **Run the news collector:**
               ```bash
               python core/news_trading_analyzer.py
               ```
            
            2. **Or run the main analysis:**
               ```bash
               python enhanced_main.py
               ```
            
            3. **Check data directory:**
               - Data should appear in `data/sentiment_history/`
               - Each bank should have a `[SYMBOL]_history.json` file
            """)
            return
        
        # Market summary metrics
        total_banks = len(dashboard.bank_symbols)
        analyzed_banks = sum(1 for data in all_data.values() if data)
        
        latest_sentiments = []
        latest_confidences = []
        
        for data in all_data.values():
            if data:
                latest = dashboard.get_latest_analysis(data)
                if latest:
                    latest_sentiments.append(latest.get('overall_sentiment', 0))
                    latest_confidences.append(latest.get('confidence', 0))
        
        avg_sentiment = sum(latest_sentiments) / len(latest_sentiments) if latest_sentiments else 0
        avg_confidence = sum(latest_confidences) / len(latest_confidences) if latest_confidences else 0
        
        positive_count = sum(1 for s in latest_sentiments if s > 0.1)
        negative_count = sum(1 for s in latest_sentiments if s < -0.1)
        neutral_count = len(latest_sentiments) - positive_count - negative_count
        
        # Display market metrics
        market_metrics = [
            {
                'title': 'Banks Analyzed',
                'value': f"{analyzed_banks}/{total_banks}",
                'status': 'positive' if analyzed_banks == total_banks else 'warning',
                'subtitle': 'Data coverage'
            },
            {
                'title': 'Market Sentiment',
                'value': f"{avg_sentiment:+.3f}",
                'status': 'positive' if avg_sentiment > 0.1 else 'negative' if avg_sentiment < -0.1 else 'neutral',
                'subtitle': 'Average sentiment'
            },
            {
                'title': 'Confidence Level',
                'value': f"{avg_confidence:.2f}",
                'status': 'positive' if avg_confidence > 0.7 else 'warning' if avg_confidence > 0.5 else 'negative',
                'subtitle': 'Analysis quality'
            },
            {
                'title': 'Positive Banks',
                'value': f"{positive_count}",
                'status': 'positive',
                'subtitle': f'vs {negative_count} negative'
            }
        ]
        
        display_professional_metrics(market_metrics)
        
        # ML Progression Summary Section
        if dashboard.ml_tracker:
            st.markdown("---")
            create_section_header(
                "🤖 Machine Learning Performance", 
                "Historical feedback on model improvement as more data is analyzed",
                "🧠"
            )
            
            try:
                # Get ML summary for last 30 days
                ml_summary = dashboard.ml_tracker.get_progression_summary(30)
                
                # Display ML metrics
                ml_metrics = [
                    {
                        'title': 'Total Predictions',
                        'value': f"{ml_summary['total_predictions']}",
                        'status': 'positive',
                        'subtitle': f"{ml_summary['completed_predictions']} completed"
                    },
                    {
                        'title': 'Accuracy Trend',
                        'value': ml_summary['model_improvement']['trend'].title() if ml_summary['model_improvement']['trend'] != 'insufficient_data' else 'N/A',
                        'status': 'positive' if ml_summary['model_improvement']['trend'] == 'improving' else 'warning' if ml_summary['model_improvement']['trend'] == 'stable' else 'negative',
                        'subtitle': 'Model performance'
                    },
                    {
                        'title': 'Success Rate',
                        'value': f"{ml_summary['trading_performance']['success_rate']:.1%}" if ml_summary['trading_performance']['success_rate'] else 'N/A',
                        'status': 'positive' if ml_summary['trading_performance']['success_rate'] > 0.6 else 'warning' if ml_summary['trading_performance']['success_rate'] > 0.4 else 'negative',
                        'subtitle': 'Trading accuracy'
                    },
                    {
                        'title': 'Training Progress',
                        'value': f"{ml_summary['model_improvement']['total_training_sessions']}" if ml_summary['model_improvement']['total_training_sessions'] else 'N/A',
                        'status': 'positive',
                        'subtitle': 'Sessions completed'
                    }
                ]
                
                display_professional_metrics(ml_metrics)
                
                # ML Progression Chart
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("#### 📊 Model Performance Progression")
                    try:
                        ml_chart = dashboard.ml_tracker.create_progression_chart(days=30)
                        st.plotly_chart(ml_chart, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Unable to generate ML progression chart: {str(e)}")
                
                with col2:
                    st.markdown("#### 💡 ML Recommendations")
                    recommendations = ml_summary.get('recommendations', [])
                    if recommendations:
                        for rec in recommendations[:5]:  # Show top 5 recommendations
                            st.markdown(f"• {rec}")
                    else:
                        st.info("🔄 Gathering more data to generate recommendations...")
                    
                    # Additional ML insights
                    st.markdown("#### 📈 Data Growth")
                    data_growth = ml_summary.get('data_volume_growth', 0)
                    if data_growth > 1000:
                        st.success(f"📚 Strong data growth: +{data_growth:,} records")
                    elif data_growth > 100:
                        st.info(f"📊 Moderate growth: +{data_growth:,} records")
                    else:
                        st.warning("⚡ Low data growth - consider increasing collection frequency")
            
            except Exception as e:
                st.warning(f"⚠️ ML progression tracking temporarily unavailable: {str(e)}")
        else:
            st.info("🤖 ML progression tracking not available - install ML tracker module for enhanced insights")
        
        st.markdown("---")
        
        # Professional charts in tabs
        chart_tabs = st.tabs(["📊 Sentiment Overview", "🎯 Confidence Analysis", "📈 Market Trends"])
        
        with chart_tabs[0]:
            sentiment_chart = create_sentiment_overview_chart(dashboard, all_data)
            st.plotly_chart(sentiment_chart, use_container_width=True)
        
        with chart_tabs[1]:
            confidence_chart = create_confidence_distribution_chart(dashboard, all_data)
            st.plotly_chart(confidence_chart, use_container_width=True)
        
        with chart_tabs[2]:
            st.info("📈 Market trends chart will be displayed here based on historical data")
        
        # Professional legends
        display_confidence_legend()
        display_sentiment_scale()
        
    except Exception as e:
        st.error(f"❌ Error in Market Overview: {str(e)}")
        st.write("Debug info:")
        st.write(f"Dashboard type: {type(dashboard)}")
        import traceback
        st.code(traceback.format_exc())
