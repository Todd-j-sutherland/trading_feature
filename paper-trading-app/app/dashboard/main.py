"""
Main Professional Dashboard for ASX Bank Analytics
Orchestrates all components for a comprehensive trading analysis interface
"""

import os
import sys
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import Settings
from app.dashboard.utils.logging_config import setup_dashboard_logger, log_error_with_context, log_performance_metrics
from app.dashboard.utils.data_manager import DataManager
from app.dashboard.utils.helpers import (
    format_sentiment_score, get_confidence_level, format_timestamp,
    get_trading_recommendation, create_metric_dict, validate_data_completeness
)
from app.dashboard.components.ui_components import UIComponents
from app.dashboard.charts.chart_generator import ChartGenerator

# Try to import optional components
try:
    from app.core.trading.risk_management import PositionRiskAssessor
    POSITION_RISK_AVAILABLE = True
except ImportError:
    POSITION_RISK_AVAILABLE = False

try:
    from app.core.analysis.technical import TechnicalAnalyzer
    from app.core.data.collectors.market_data import ASXDataFeed
    TECHNICAL_ANALYSIS_AVAILABLE = True
except ImportError:
    TECHNICAL_ANALYSIS_AVAILABLE = False

try:
    from app.dashboard.components.ml_progression import render_ml_progression_dashboard, render_ml_progression_sidebar
    ML_PROGRESSION_AVAILABLE = True
except ImportError:
    ML_PROGRESSION_AVAILABLE = False

logger = setup_dashboard_logger(__name__)

class ProfessionalDashboard:
    """
    Professional Dashboard for ASX Bank Analytics
    
    Provides comprehensive sentiment analysis, technical indicators,
    and risk assessment for Australian banking sector trading
    """
    
    def __init__(self):
        """Initialize the professional dashboard"""
        start_time = datetime.now()
        
        try:
            # Core configuration
            self.settings = Settings()
            self.bank_symbols = self.settings.BANK_SYMBOLS
            self.bank_names = {
                "CBA.AX": "Commonwealth Bank",
                "WBC.AX": "Westpac Banking Corp", 
                "ANZ.AX": "ANZ Banking Group",
                "NAB.AX": "National Australia Bank",
                "MQG.AX": "Macquarie Group",
                "SUN.AX": "Suncorp Group",
                "QBE.AX": "QBE Insurance Group"
            }
            
            # Initialize components
            self.data_manager = DataManager("data/sentiment_history")
            self.ui_components = UIComponents()
            self.chart_generator = ChartGenerator()
            
            # Initialize technical analyzer if available
            if TECHNICAL_ANALYSIS_AVAILABLE:
                self.tech_analyzer = TechnicalAnalyzer()
                self.technical_data = {}  # Cache for technical analysis
            else:
                self.tech_analyzer = None
                self.technical_data = {}
            
            # Initialize position risk assessor if available
            if POSITION_RISK_AVAILABLE:
                try:
                    self.position_risk_assessor = PositionRiskAssessor()
                except Exception as e:
                    logger.warning(f"Could not initialize Position Risk Assessor: {e}")
                    self.position_risk_assessor = None
            else:
                self.position_risk_assessor = None
            
            # Load CSS styling
            self.ui_components.load_professional_css()
            
            # Cache for performance
            self._data_cache = {}
            self._cache_timestamp = None
            
            execution_time = (datetime.now() - start_time).total_seconds()
            log_performance_metrics(logger, "Dashboard Initialization", execution_time, True)
            
            logger.info("Professional Dashboard initialized successfully")
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            log_performance_metrics(logger, "Dashboard Initialization", execution_time, False)
            log_error_with_context(logger, e, "initializing dashboard")
            raise
    
    def run(self):
        """Main dashboard entry point"""
        try:
            logger.info("Starting Professional Dashboard")
            
            # Configure Streamlit page
            st.set_page_config(
                page_title="ASX Bank Analytics Platform",
                page_icon="📊",
                layout="wide",
                initial_sidebar_state="expanded"
            )
            
            # Create main header
            self.ui_components.create_professional_header()
            
            # Load and cache data
            all_data = self._load_data_with_cache()
            
            # Create sidebar with debug info
            self._create_debug_sidebar(all_data)
            
            # Main dashboard content
            self._render_main_content(all_data)
            
            logger.info("Professional Dashboard rendered successfully")
            
        except Exception as e:
            log_error_with_context(logger, e, "running dashboard")
            st.error("An error occurred while loading the dashboard. Please check the logs.")
    
    def _load_data_with_cache(self) -> Dict[str, List[Dict]]:
        """Load sentiment data with caching for performance"""
        try:
            # Check if we need to refresh cache (5 minute timeout)
            current_time = datetime.now()
            if (self._cache_timestamp is None or 
                (current_time - self._cache_timestamp).seconds > 300):
                
                logger.info("Loading fresh sentiment data")
                self._data_cache = self.data_manager.load_sentiment_data(self.bank_symbols)
                self._cache_timestamp = current_time
            else:
                logger.debug("Using cached sentiment data")
            
            return self._data_cache
            
        except Exception as e:
            log_error_with_context(logger, e, "loading data with cache")
            return {}
    
    def _create_debug_sidebar(self, all_data: Dict[str, List[Dict]]):
        """Create sidebar with debugging and system information"""
        try:
            with st.sidebar:
                st.markdown("### 🔧 System Status")
                
                # Data status
                total_records = sum(len(data) for data in all_data.values())
                symbols_with_data = len([s for s, d in all_data.items() if len(d) > 0])
                
                debug_metrics = [
                    create_metric_dict("Data Sources", f"{symbols_with_data}/{len(self.bank_symbols)}", "neutral"),
                    create_metric_dict("Total Records", str(total_records), "positive" if total_records > 0 else "negative"),
                    create_metric_dict("Cache Status", "Active" if self._cache_timestamp else "Empty", 
                                     "positive" if self._cache_timestamp else "warning")
                ]
                
                for metric in debug_metrics:
                    st.metric(
                        label=metric['title'],
                        value=metric['value']
                    )
                
                # Component status
                st.markdown("### 📦 Component Status")
                
                component_status = [
                    ("Technical Analysis", "✅" if TECHNICAL_ANALYSIS_AVAILABLE else "❌"),
                    ("Position Risk Assessor", "✅" if POSITION_RISK_AVAILABLE else "❌"),
                    ("Data Manager", "✅"),
                    ("Chart Generator", "✅"),
                    ("UI Components", "✅")
                ]
                
                for component, status in component_status:
                    st.write(f"{status} {component}")
                
                # Data file status
                st.markdown("### 📁 Data Files")
                data_path = "data/sentiment_history"
                
                if os.path.exists(data_path):
                    files = [f for f in os.listdir(data_path) if f.endswith('_history.json')]
                    st.write(f"📄 {len(files)} data files found")
                    
                    for symbol in self.bank_symbols:
                        file_path = os.path.join(data_path, f"{symbol}_history.json")
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path) / 1024  # KB
                            records = len(all_data.get(symbol, []))
                            st.write(f"✅ {symbol}: {records} records ({file_size:.1f}KB)")
                        else:
                            st.write(f"❌ {symbol}: File missing")
                else:
                    st.write("❌ Data directory not found")
                
                # Refresh button
                if st.button("🔄 Refresh Data"):
                    self._cache_timestamp = None
                    st.experimental_rerun()
                
                # Add ML progression sidebar
                if ML_PROGRESSION_AVAILABLE:
                    render_ml_progression_sidebar()
                
                logger.debug("Debug sidebar created")
                
        except Exception as e:
            log_error_with_context(logger, e, "creating debug sidebar")
    
    def _render_main_content(self, all_data: Dict[str, List[Dict]]):
        """Render main dashboard content"""
        try:
            # Check for data availability
            if not all_data or all(len(data) == 0 for data in all_data.values()):
                self.ui_components.display_alert(
                    "No sentiment data available. Please ensure data files exist in data/sentiment_history/",
                    "warning",
                    "Data Not Found"
                )
                return
            
            # Create main tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Market Overview", 
                "🏦 Bank Analysis", 
                "📈 Technical Analysis",
                "🎯 Position Risk",
                "🤖 ML Progression"
            ])
            
            with tab1:
                self._render_market_overview(all_data)
            
            with tab2:
                self._render_bank_analysis(all_data)
            
            with tab3:
                self._render_technical_analysis(all_data)
            
            with tab4:
                self._render_position_risk(all_data)
                
            with tab5:
                self._render_ml_progression()
            
            with tab3:
                self._render_technical_analysis(all_data)
            
            with tab4:
                self._render_position_risk()
            
            logger.debug("Main content rendered")
            
        except Exception as e:
            log_error_with_context(logger, e, "rendering main content")
    
    def _render_market_overview(self, all_data: Dict[str, List[Dict]]):
        """Render market overview tab"""
        try:
            self.ui_components.create_section_header(
                "Market Overview", 
                "Real-time sentiment analysis across Australian banking sector",
                "📊"
            )
            
            # Overview charts
            col1, col2 = st.columns(2)
            
            with col1:
                sentiment_chart = self.chart_generator.create_sentiment_overview_chart(
                    all_data, self.bank_names
                )
                st.plotly_chart(sentiment_chart, use_container_width=True)
            
            with col2:
                confidence_chart = self.chart_generator.create_confidence_distribution_chart(
                    all_data, self.bank_names
                )
                st.plotly_chart(confidence_chart, use_container_width=True)
            
            # Market summary metrics
            self._display_market_summary_metrics(all_data)
            
            # Display legends
            self.ui_components.display_confidence_legend()
            self.ui_components.display_sentiment_scale()
            
            logger.debug("Market overview rendered")
            
        except Exception as e:
            log_error_with_context(logger, e, "rendering market overview")
    
    def _display_market_summary_metrics(self, all_data: Dict[str, List[Dict]]):
        """Display summary metrics for the market"""
        try:
            # Ensure all_data is a dictionary
            if not isinstance(all_data, dict):
                st.warning("Market data is not in expected format")
                return
                
            # Calculate market-wide metrics
            all_sentiments = []
            all_confidences = []
            high_confidence_count = 0
            positive_sentiment_count = 0
            
            for symbol, data in all_data.items():
                if not data:
                    continue
                
                latest = self.data_manager.get_latest_analysis(data)
                if not latest:
                    continue
                
                sentiment = latest.get('overall_sentiment', 0)
                confidence = latest.get('confidence', 0)
                
                all_sentiments.append(sentiment)
                all_confidences.append(confidence)
                
                if confidence >= 0.8:
                    high_confidence_count += 1
                if sentiment > 0.2:
                    positive_sentiment_count += 1
            
            if all_sentiments:
                avg_sentiment = sum(all_sentiments) / len(all_sentiments)
                avg_confidence = sum(all_confidences) / len(all_confidences)
                
                market_metrics = [
                    create_metric_dict(
                        "Market Sentiment",
                        f"{avg_sentiment:+.3f}",
                        "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral",
                        "Average across all banks"
                    ),
                    create_metric_dict(
                        "Average Confidence",
                        f"{avg_confidence:.2f}",
                        "positive" if avg_confidence > 0.7 else "warning" if avg_confidence > 0.5 else "negative",
                        f"{len(all_sentiments)} banks analyzed"
                    ),
                    create_metric_dict(
                        "High Confidence",
                        f"{high_confidence_count}/{len(all_sentiments)}",
                        "positive" if high_confidence_count > len(all_sentiments) / 2 else "neutral",
                        "Banks with >80% confidence"
                    ),
                    create_metric_dict(
                        "Positive Sentiment",
                        f"{positive_sentiment_count}/{len(all_sentiments)}",
                        "positive" if positive_sentiment_count > len(all_sentiments) / 2 else "neutral",
                        "Banks with positive outlook"
                    )
                ]
                
                self.ui_components.display_professional_metrics(market_metrics)
            
            logger.debug("Market summary metrics displayed")
            
        except Exception as e:
            log_error_with_context(logger, e, "displaying market summary metrics")
    
    def _render_bank_analysis(self, all_data: Dict[str, List[Dict]]):
        """Render individual bank analysis tab"""
        try:
            self.ui_components.create_section_header(
                "Individual Bank Analysis",
                "Detailed sentiment and technical analysis for each bank",
                "🏦"
            )
            
            # Bank selector
            available_banks = [
                symbol for symbol in self.bank_symbols 
                if symbol in all_data and len(all_data[symbol]) > 0
            ]
            
            if not available_banks:
                self.ui_components.display_alert(
                    "No bank data available for analysis",
                    "warning"
                )
                return
            
            selected_bank = st.selectbox(
                "Select a bank for detailed analysis:",
                available_banks,
                format_func=lambda x: self.bank_names.get(x, x),
                key="bank_selector"
            )
            
            if selected_bank:
                self._display_individual_bank_analysis(selected_bank, all_data[selected_bank])
            
            logger.debug(f"Bank analysis rendered for {selected_bank}")
            
        except Exception as e:
            log_error_with_context(logger, e, "rendering bank analysis")
    
    def _display_individual_bank_analysis(self, symbol: str, data: List[Dict]):
        """Display detailed analysis for a specific bank"""
        try:
            latest = self.data_manager.get_latest_analysis(data)
            
            if not latest:
                self.ui_components.display_alert(
                    f"No analysis data available for {self.bank_names.get(symbol, symbol)}",
                    "warning"
                )
                return
            
            bank_name = self.bank_names.get(symbol, symbol)
            
            # Bank card header
            self.ui_components.create_bank_card_header(symbol, bank_name)
            
            # Key metrics
            self._display_bank_key_metrics(latest)
            
            # Charts section
            st.markdown("#### 📈 Historical Analysis")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                historical_chart = self.chart_generator.create_historical_trends_chart(
                    symbol, data, self.bank_names
                )
                st.plotly_chart(historical_chart, use_container_width=True)
            
            with chart_col2:
                correlation_data = self.data_manager.get_correlation_data(symbol, data)
                correlation_chart = self.chart_generator.create_correlation_chart(
                    symbol, correlation_data, self.bank_names
                )
                st.plotly_chart(correlation_chart, use_container_width=True)
            
            # Detailed analysis sections
            self._display_sentiment_components(latest)
            self._display_recent_headlines(latest)
            self._display_significant_events(latest)
            
            # Performance metrics
            performance_metrics = self.data_manager.calculate_performance_metrics(symbol, data)
            if performance_metrics:
                self._display_performance_summary(performance_metrics)
            
            # Close bank card
            self.ui_components.close_bank_card()
            
            logger.debug(f"Individual bank analysis displayed for {symbol}")
            
        except Exception as e:
            log_error_with_context(logger, e, f"displaying bank analysis for {symbol}")
    
    def _display_bank_key_metrics(self, latest: Dict):
        """Display key metrics for a bank"""
        try:
            sentiment = latest.get('overall_sentiment', 0)
            confidence = latest.get('confidence', 0)
            news_count = latest.get('news_count', 0)
            timestamp = latest.get('timestamp', 'Unknown')
            
            score_text, score_class = format_sentiment_score(sentiment)
            conf_level, conf_class = get_confidence_level(confidence)
            time_str = format_timestamp(timestamp)
            
            metrics = [
                create_metric_dict(
                    "Sentiment Score",
                    score_text,
                    score_class.replace('status-', ''),
                    "Current market sentiment"
                ),
                create_metric_dict(
                    "Confidence Level",
                    f"{confidence:.2f}",
                    "positive" if confidence > 0.7 else "warning" if confidence > 0.5 else "negative",
                    f"{conf_level} confidence"
                ),
                create_metric_dict(
                    "News Articles",
                    str(news_count),
                    "positive" if news_count > 5 else "neutral",
                    "Articles analyzed"
                ),
                create_metric_dict(
                    "Last Updated",
                    time_str.split(' ')[0] if ' ' in time_str else time_str,
                    "neutral",
                    time_str.split(' ')[1] if ' ' in time_str else ''
                )
            ]
            
            self.ui_components.display_professional_metrics(metrics)
            
        except Exception as e:
            log_error_with_context(logger, e, "displaying bank key metrics")
    
    def _display_sentiment_components(self, latest: Dict):
        """Display sentiment components breakdown"""
        try:
            if 'sentiment_components' not in latest:
                return
            
            st.markdown("#### 📊 Sentiment Components Analysis")
            components = latest['sentiment_components']
            
            # Ensure components is a dictionary
            if not isinstance(components, dict):
                st.warning("Sentiment components data is not in expected format")
                return
            
            # Create DataFrame for display
            component_data = []
            for component_name, score in components.items():
                status = "🟢" if score > 0 else "🔴" if score < 0 else "🟡"
                component_data.append({
                    'Component': component_name.replace('_', ' ').title(),
                    'Score': f"{score:.3f}",
                    'Status': status,
                    'Impact': 'Positive' if score > 0 else 'Negative' if score < 0 else 'Neutral'
                })
            
            if component_data:
                import pandas as pd
                st.dataframe(pd.DataFrame(component_data), use_container_width=True, hide_index=True)
            
        except Exception as e:
            log_error_with_context(logger, e, "displaying sentiment components")
    
    def _display_recent_headlines(self, latest: Dict):
        """Display recent headlines section"""
        try:
            if 'recent_headlines' not in latest:
                return
            
            st.markdown("#### 📰 Recent Market Headlines")
            headlines = latest['recent_headlines']
            
            for i, headline in enumerate(headlines[:5]):
                if headline:
                    self.ui_components.display_news_item(
                        f"#{i+1} {headline}",
                        "",  # content
                        sentiment=0,  # sentiment score
                        source=""
                    )
            
        except Exception as e:
            log_error_with_context(logger, e, "displaying recent headlines")
    
    def _display_significant_events(self, latest: Dict):
        """Display significant events section"""
        try:
            if 'significant_events' not in latest:
                return
            
            st.markdown("#### 🚨 Significant Market Events")
            events = latest['significant_events']
            
            if 'events_detected' in events and events['events_detected']:
                for event in events['events_detected']:
                    event_type = event.get('type', 'unknown')
                    headline = event.get('headline', 'No headline')
                    sentiment_impact = event.get('sentiment_impact', 0)
                    
                    self.ui_components.display_news_item(
                        headline,
                        "",  # content
                        sentiment=sentiment_impact,
                        source=event_type
                    )
            else:
                self.ui_components.display_alert(
                    "No significant events detected in recent analysis",
                    "info",
                    "Market Status"
                )
            
        except Exception as e:
            log_error_with_context(logger, e, "displaying significant events")
    
    def _display_performance_summary(self, performance_metrics: Dict):
        """Display performance summary metrics"""
        try:
            st.markdown("#### 📈 Performance Summary (Last 30 Days)")
            
            metrics = [
                create_metric_dict(
                    "Avg Sentiment",
                    f"{performance_metrics.get('avg_sentiment', 0):.3f}",
                    "positive" if performance_metrics.get('avg_sentiment', 0) > 0.1 else "negative" if performance_metrics.get('avg_sentiment', 0) < -0.1 else "neutral",
                    "30-day average"
                ),
                create_metric_dict(
                    "Avg Confidence",
                    f"{performance_metrics.get('avg_confidence', 0):.2f}",
                    "positive" if performance_metrics.get('avg_confidence', 0) > 0.7 else "warning" if performance_metrics.get('avg_confidence', 0) > 0.5 else "negative",
                    "Analysis quality"
                ),
                create_metric_dict(
                    "Volatility",
                    f"{performance_metrics.get('sentiment_volatility', 0):.3f}",
                    "negative" if performance_metrics.get('sentiment_volatility', 0) > 0.2 else "warning" if performance_metrics.get('sentiment_volatility', 0) > 0.1 else "positive",
                    "Sentiment stability"
                ),
                create_metric_dict(
                    "Recent Trend",
                    f"{performance_metrics.get('recent_trend', 0):+.3f}",
                    "positive" if performance_metrics.get('recent_trend', 0) > 0.05 else "negative" if performance_metrics.get('recent_trend', 0) < -0.05 else "neutral",
                    "Week over week"
                )
            ]
            
            self.ui_components.display_professional_metrics(metrics)
            
        except Exception as e:
            log_error_with_context(logger, e, "displaying performance summary")
    
    def _render_technical_analysis(self, all_data: Dict[str, List[Dict]]):
        """Render technical analysis tab"""
        try:
            self.ui_components.create_section_header(
                "Technical Analysis",
                "Advanced technical indicators and market data analysis",
                "📈"
            )
            
            if not TECHNICAL_ANALYSIS_AVAILABLE:
                self.ui_components.display_alert(
                    "Technical analysis module is not available. Please ensure all required dependencies are installed.",
                    "warning",
                    "Module Unavailable"
                )
                return
            
            # Technical analysis content would go here
            st.info("Technical analysis implementation in progress...")
            
        except Exception as e:
            log_error_with_context(logger, e, "rendering technical analysis")
    
    def _render_position_risk(self):
        """Render position risk assessment tab"""
        try:
            self.ui_components.create_section_header(
                "Position Risk Assessment",
                "ML-powered analysis for existing positions and recovery predictions",
                "🎯"
            )
            
            if not POSITION_RISK_AVAILABLE:
                self.ui_components.display_alert(
                    "Position Risk Assessor module is not available. Please ensure src/position_risk_assessor.py is properly installed.",
                    "warning",
                    "Module Unavailable"
                )
                return
            
            # Position risk content would go here
            st.info("Position risk assessment implementation in progress...")
            
        except Exception as e:
            log_error_with_context(logger, e, "rendering position risk")
    
    def _render_ml_progression(self):
        """Render ML progression analysis tab"""
        try:
            self.ui_components.create_section_header(
                "Machine Learning Performance Progression",
                "Historical tracking of ML model accuracy, confidence, and trading success",
                "🤖"
            )
            
            if not ML_PROGRESSION_AVAILABLE:
                self.ui_components.display_alert(
                    "ML Progression module is not available. Please ensure the progression tracker is properly installed.",
                    "warning",
                    "Module Unavailable"
                )
                return
            
            # Render the ML progression dashboard
            render_ml_progression_dashboard()
            
        except Exception as e:
            log_error_with_context(logger, e, "rendering ML progression")

def main():
    """Main entry point for the dashboard"""
    try:
        dashboard = ProfessionalDashboard()
        dashboard.run()
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}", exc_info=True)
        st.error("Failed to start the dashboard. Please check the logs for details.")

def run_dashboard():
    """Public function to run the dashboard (called from main.py)"""
    main()

if __name__ == "__main__":
    main()
