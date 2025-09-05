#!/usr/bin/env python3
"""
News Trading Analyzer - Primary Entry Point
Focuses on news sentiment analysis f            logger.info(f"⚡ Result keys for {symbol}: {list(result.keys())}")
            
            # Extract key metrics
            sentiment_score = result.get('overall_sentiment', 0)
            confidence = result.get('confidence', 0)
            news_count = result.get('news_count', 0)
            
            # Get time context informationng decisions

Core Purpose: Analyze news sources and provide trading sentiment scores
"""

import os
import sys
import logging
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Core imports
from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
from app.core.ml_trading_config import TRADING_CONFIGS
from app.config.settings import Settings
from app.core.trading.position_tracker import TradingOutcomeTracker

# Setup logging
def setup_logging(log_level='INFO'):
    """Setup logging configuration"""
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/news_trading_analyzer.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class NewsTradingAnalyzer:
    """
    Primary news trading analysis system
    
    Purpose: Analyze news sentiment to provide trading recommendations
    Features:
    - Multi-source news collection (RSS, Yahoo Finance, Google News, Reddit)
    - Advanced sentiment analysis (Traditional + Transformers + ML features)
    - Trading strategy recommendations
    - Risk-adjusted scoring
    """
    
    def __init__(self):
        logger.info("🚀 Initializing News Trading Analyzer...")
        self.settings = Settings()
        self.sentiment_analyzer = NewsSentimentAnalyzer()
        
        # Initialize outcome tracker
        if hasattr(self.sentiment_analyzer, 'ml_pipeline'):
            self.outcome_tracker = TradingOutcomeTracker(
                self.sentiment_analyzer.ml_pipeline
            )
        else:
            self.outcome_tracker = None
            logger.warning("ML pipeline not available, outcome tracking disabled")
        
        # Use canonical bank symbols from settings
        self.bank_symbols = self.settings.BANK_SYMBOLS
        
        logger.info("✅ News Trading Analyzer initialized successfully")
    
    def analyze_single_bank(self, symbol: str, detailed: bool = False, keywords: list = None) -> dict:
        """
        Analyze news sentiment for a single bank
        
        Args:
            symbol: Bank symbol (e.g., 'CBA.AX')
            detailed: Whether to include detailed breakdown
            keywords: Optional list of keywords to filter news
            
        Returns:
            Dict with sentiment analysis and trading recommendation
        """
        logger.info(f"📊 Analyzing {symbol}...")
        
        try:
            # Get comprehensive sentiment analysis
            logger.info(f"⚡ Calling sentiment analyzer for {symbol}...")
            result = self.sentiment_analyzer.analyze_bank_sentiment(symbol, keywords=keywords)
            logger.info(f"⚡ Sentiment analyzer returned: {type(result)} for {symbol}")
            
            if not isinstance(result, dict):
                logger.warning(f"⚠️ {symbol}: Invalid sentiment analysis result (not a dict)")
                return {
                    'symbol': symbol,
                    'sentiment_score': 0.0,
                    'confidence': 0.0,
                    'news_count': 0,
                    'signal': 'N/A',
                    'error': 'Invalid sentiment analysis result',
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.info(f"⚡ Result keys for {symbol}: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Extract key metrics
            sentiment_score = result.get('overall_sentiment', 0)
            confidence = result.get('confidence', 0)
            news_count = result.get('news_count', 0)
            
            # Get time context information
            time_context = self._get_analysis_time_context(result)
            
            # Generate trading recommendation
            trading_recommendation = self._get_trading_recommendation(
                sentiment_score, confidence, news_count
            )
            
            # Prepare output
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'sentiment_score': float(sentiment_score),
                'confidence': float(confidence),
                'ml_confidence': result.get('ml_confidence'),  # Add ML confidence
                'news_count': news_count,
                'time_context': time_context,
                'trading_recommendation': trading_recommendation,
                'signal': self._get_trading_signal(sentiment_score, confidence),
                'ml_prediction': result.get('ml_prediction', {}),  # Add ML prediction from sentiment analysis
                'overall_sentiment': float(sentiment_score),  # For dashboard compatibility
                'sentiment_components': result.get('sentiment_components', {}),  # For dashboard compatibility
                'recent_headlines': result.get('recent_headlines', []),  # For dashboard compatibility
                'significant_events': result.get('significant_events', {})  # For dashboard compatibility
            }
            
            if detailed:
                analysis['detailed_breakdown'] = {
                    'sentiment_components': result.get('sentiment_components', {}),
                    'recent_headlines': result.get('recent_headlines', []),
                    'significant_events': result.get('significant_events', {}),
                    'reddit_sentiment': result.get('reddit_sentiment', {}),
                    'ml_trading_details': result.get('ml_trading_details', {}),
                    'news_date_range': time_context.get('news_date_range', {}),
                    'data_freshness': time_context.get('data_freshness', {})
                }
            
            logger.info(f"✅ {symbol}: {analysis['signal']} "
                       f"(Score: {sentiment_score:.3f}, Confidence: {confidence:.3f}) "
                       f"[{time_context.get('news_period', 'Unknown period')}]")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def analyze_and_track(self, symbol: str, keywords: list = None) -> dict:
        """Analyze sentiment and track for ML training"""
        result = self.analyze_single_bank(symbol, detailed=True, keywords=keywords)
        
        # Record signal if it's actionable
        if self.outcome_tracker and result.get('signal') not in ['HOLD', None]:
            trade_id = self.outcome_tracker.record_signal(symbol, result)
            result['trade_id'] = trade_id
            logger.info(f"📝 Recorded trade signal: {trade_id}")
        
        return result
    
    def close_trade(self, trade_id: str, exit_price: float):
        """Close a trade and record outcome"""
        if self.outcome_tracker:
            exit_data = {
                'price': exit_price,
                'timestamp': datetime.now().isoformat()
            }
            self.outcome_tracker.close_trade(trade_id, exit_data)
            logger.info(f"🔚 Trade closed: {trade_id}")
        else:
            logger.warning("Outcome tracker not available")
    
    def analyze_all_banks(self, detailed: bool = False) -> dict:
        """
        Analyze all major Australian banks
        
        Args:
            detailed: Whether to include detailed breakdown for each bank
            
        Returns:
            Dict with analysis for all banks plus market overview
        """
        logger.info("🏦 Analyzing all major Australian banks...")
        
        results = {}
        all_scores = []
        
        for symbol in self.bank_symbols:
            analysis = self.analyze_single_bank(symbol, detailed)
            results[symbol] = analysis
            
            # Only include valid sentiment scores
            if analysis and 'sentiment_score' in analysis and 'error' not in analysis:
                all_scores.append(analysis['sentiment_score'])
        
        # Calculate market overview
        if all_scores:
            market_overview = {
                'average_sentiment': sum(all_scores) / len(all_scores),
                'most_bullish': max(results.items(), key=lambda x: x[1].get('sentiment_score', -999)),
                'most_bearish': min(results.items(), key=lambda x: x[1].get('sentiment_score', 999)),
                'high_confidence_count': sum(1 for r in results.values() 
                                           if r.get('confidence', 0) > 0.7),
                'total_analyzed': len(all_scores)
            }
        else:
            market_overview = {'error': 'No successful analyses'}
        
        return {
            'market_overview': market_overview,
            'individual_analysis': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_trading_recommendation(self, sentiment_score: float, 
                                  confidence: float, news_count: int) -> dict:
        """
        Generate trading strategy recommendation based on analysis
        
        Args:
            sentiment_score: Overall sentiment (-1 to 1)
            confidence: Analysis confidence (0 to 1)
            news_count: Number of news articles analyzed
            
        Returns:
            Dict with strategy recommendation and parameters
        """
        # Determine strategy based on sentiment and confidence
        if confidence > 0.7:
            if sentiment_score > 0.3:
                strategy_type = 'aggressive'
                action = 'BUY'
                reasoning = f"High confidence ({confidence:.2f}) positive sentiment ({sentiment_score:.2f})"
            elif sentiment_score < -0.3:
                strategy_type = 'conservative'
                action = 'SELL'
                reasoning = f"High confidence ({confidence:.2f}) negative sentiment ({sentiment_score:.2f})"
            else:
                strategy_type = 'moderate'
                action = 'HOLD'
                reasoning = f"High confidence ({confidence:.2f}) but neutral sentiment ({sentiment_score:.2f})"
        else:
            strategy_type = 'conservative'
            if sentiment_score > 0.1:
                action = 'WEAK_BUY'
            elif sentiment_score < -0.1:
                action = 'WEAK_SELL'
            else:
                action = 'HOLD'
            reasoning = f"Low confidence ({confidence:.2f}) in analysis"
        
        # Get strategy parameters
        config = TRADING_CONFIGS.get(strategy_type, TRADING_CONFIGS['moderate'])
        
        return {
            'action': action,
            'strategy_type': strategy_type,
            'reasoning': reasoning,
            'parameters': {
                'position_size_multiplier': config['position_size_multiplier'],
                'stop_loss_multiplier': config['stop_loss_multiplier'],
                'take_profit_multiplier': config['take_profit_multiplier'],
                'confidence_threshold': config['min_confidence']
            },
            'data_quality': {
                'news_articles': news_count,
                'confidence_level': confidence,
                'recommendation_strength': abs(sentiment_score) * confidence
            }
        }
    
    def _get_trading_signal(self, sentiment_score: float, confidence: float) -> str:
        """
        Get simple trading signal
        
        Returns:
            Signal string: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
        """
        strength = abs(sentiment_score) * confidence
        
        if sentiment_score > 0.3 and confidence > 0.7:
            return "STRONG_BUY"
        elif sentiment_score > 0.1 and confidence > 0.5:
            return "BUY"
        elif sentiment_score < -0.3 and confidence > 0.7:
            return "STRONG_SELL"
        elif sentiment_score < -0.1 and confidence > 0.5:
            return "SELL"
        else:
            return "HOLD"
    
    def export_analysis(self, analysis_result: dict, filename: str = None) -> str:
        """
        Export analysis results to JSON file
        
        Args:
            analysis_result: Analysis result from analyze_single_bank or analyze_all_banks
            filename: Optional filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_analysis_{timestamp}.json"
        
        # Ensure reports directory exists
        os.makedirs('reports', exist_ok=True)
        filepath = os.path.join('reports', filename)
        
        # Export with pretty formatting
        with open(filepath, 'w') as f:
            json.dump(analysis_result, f, indent=2, default=str)
        
        logger.info(f"📄 Analysis exported to: {filepath}")
        return filepath
    
    def get_enhanced_analysis(self, symbol: str) -> dict:
        """
        Get enhanced analysis including detailed keyword filtering insights
        
        Args:
            symbol: Bank symbol (e.g., 'CBA.AX')
            
        Returns:
            Dict with comprehensive analysis including filtering insights
        """
        logger.info(f"🔍 Running enhanced analysis for {symbol}...")
        
        try:
            # Get standard sentiment analysis
            standard_result = self.analyze_single_bank(symbol, detailed=True)
            
            # Get filtering insights
            filtering_summary = self.sentiment_analyzer.get_filtered_news_summary(symbol)
            
            # Combine results
            enhanced_result = standard_result.copy()
            enhanced_result['filtering_insights'] = filtering_summary
            
            # Add recommendation confidence based on filtering quality
            filtering_efficiency = filtering_summary.get('filtering_summary', {}).get('filtering_efficiency', 0)
            avg_relevance = filtering_summary.get('filtering_summary', {}).get('avg_relevance_score', 0)
            
            # Adjust confidence based on filtering quality
            original_confidence = enhanced_result.get('confidence', 0)
            filtering_boost = min(filtering_efficiency * avg_relevance * 0.2, 0.15)
            enhanced_result['enhanced_confidence'] = min(original_confidence + filtering_boost, 1.0)
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced analysis for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_analysis_time_context(self, sentiment_result: dict) -> dict:
        """
        Extract time context information from sentiment analysis
        
        Args:
            sentiment_result: Result from sentiment analyzer
            
        Returns:
            Dict with time context information
        """
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # Default time context
        time_context = {
            'analysis_timestamp': now.isoformat(),
            'news_period': 'Last 24-48 hours',
            'technical_period': 'Last 3 months',
            'sentiment_window': '24-48 hours',
            'data_freshness': {
                'news_data': 'Real-time to 2 hours old',
                'price_data': 'Real-time',
                'technical_indicators': 'Based on last 3 months'
            }
        }
        
        # Try to get more specific information from the sentiment result
        try:
            # Check if we have recent headlines with dates
            recent_headlines = sentiment_result.get('recent_headlines', [])
            if recent_headlines:
                # Estimate date range from news articles
                time_context['news_articles_found'] = len(recent_headlines)
                time_context['estimated_news_coverage'] = 'Last 1-2 days'
            
            # Check for news count and estimate coverage
            news_count = sentiment_result.get('news_count', 0)
            if news_count > 0:
                if news_count >= 10:
                    time_context['news_period'] = 'Last 48 hours'
                    time_context['coverage_quality'] = 'Good'
                elif news_count >= 5:
                    time_context['news_period'] = 'Last 24 hours'
                    time_context['coverage_quality'] = 'Moderate'
                else:
                    time_context['news_period'] = 'Last 12-24 hours'
                    time_context['coverage_quality'] = 'Limited'
            
            # Add Reddit sentiment timing if available
            reddit_sentiment = sentiment_result.get('reddit_sentiment', {})
            if reddit_sentiment and reddit_sentiment.get('posts_analyzed', 0) > 0:
                time_context['reddit_period'] = 'Last 24 hours'
                time_context['reddit_posts'] = reddit_sentiment.get('posts_analyzed', 0)
            
            # Add technical analysis context with multiple timeframes
            time_context['technical_indicators'] = {
                'short_term': {
                    'period': '3 days',
                    'timeframe': '1-hour bars',
                    'indicators': 'RSI(14), MACD(12,26,9), EMA(9,21)',
                    'purpose': 'Intraday momentum and entry/exit timing'
                },
                'medium_term': {
                    'period': '2 weeks', 
                    'timeframe': '4-hour bars',
                    'indicators': 'RSI(14), MACD(12,26,9), SMA(20,50)',
                    'purpose': 'Short-term trend confirmation'
                },
                'intermediate_term': {
                    'period': '1 month',
                    'timeframe': 'Daily bars', 
                    'indicators': 'RSI(14), MACD(12,26,9), SMA(20,50,100)',
                    'purpose': 'Medium-term trend analysis'
                },
                'long_term': {
                    'period': '3 months',
                    'timeframe': 'Daily bars',
                    'indicators': 'RSI(14), MACD(12,26,9), SMA(50,100,200)',
                    'purpose': 'Long-term trend and major support/resistance'
                }
            }
            
            # Add ML model context if available
            if sentiment_result.get('ml_trading_details'):
                time_context['ml_model_context'] = {
                    'training_period': 'Historical data up to current',
                    'feature_window': 'Last 30 days',
                    'model_freshness': 'Updated continuously'
                }
                
        except Exception as e:
            logger.warning(f"Could not extract detailed time context: {e}")
        
        return time_context

    def _get_technical_analysis_time_context(self, symbol: str) -> dict:
        """
        Get time context for technical analysis across multiple timeframes
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with technical analysis time context for multiple timeframes
        """
        try:
            # Try to import technical analysis if available
            from app.core.analysis.technical import TechnicalAnalyzer, get_market_data
            
            timeframes = {}
            
            # Define timeframe configurations for 1-hour bar trading
            timeframe_configs = [
                {'period': '3d', 'interval': '1h', 'name': 'short_term', 'description': '3 days (1h bars)'},
                {'period': '2wk', 'interval': '4h', 'name': 'medium_term', 'description': '2 weeks (4h bars)'},
                {'period': '1mo', 'interval': '1d', 'name': 'intermediate_term', 'description': '1 month (daily)'},
                {'period': '3mo', 'interval': '1d', 'name': 'long_term', 'description': '3 months (daily)'}
            ]
            
            for config in timeframe_configs:
                try:
                    # Get market data for this timeframe
                    market_data = get_market_data(symbol, period=config['period'], interval=config['interval'])
                    
                    if not market_data.empty:
                        start_date = market_data.index.min()
                        end_date = market_data.index.max()
                        data_points = len(market_data)
                        
                        timeframes[config['name']] = {
                            'period': config['description'],
                            'start_date': start_date.strftime('%Y-%m-%d %H:%M') if 'h' in config['interval'] else start_date.strftime('%Y-%m-%d'),
                            'end_date': end_date.strftime('%Y-%m-%d %H:%M') if 'h' in config['interval'] else end_date.strftime('%Y-%m-%d'),
                            'data_points': data_points,
                            'interval': config['interval'],
                            'period_hours': (end_date - start_date).total_seconds() / 3600,
                            'last_update': end_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'data_quality': 'Good' if data_points > 50 else 'Limited'
                        }
                        
                        # Add specific indicators for each timeframe
                        if config['name'] == 'short_term':
                            timeframes[config['name']]['recommended_indicators'] = [
                                'RSI(14) - 1h', 'MACD(12,26,9) - 1h', 'EMA(9,21) - 1h',
                                'Bollinger Bands(20,2) - 1h', 'Stochastic(14,3,3) - 1h'
                            ]
                        elif config['name'] == 'medium_term':
                            timeframes[config['name']]['recommended_indicators'] = [
                                'RSI(14) - 4h', 'MACD(12,26,9) - 4h', 'SMA(20,50) - 4h',
                                'Support/Resistance levels', 'Volume Profile - 4h'
                            ]
                        elif config['name'] == 'intermediate_term':
                            timeframes[config['name']]['recommended_indicators'] = [
                                'RSI(14) - Daily', 'MACD(12,26,9) - Daily', 'SMA(20,50,100) - Daily',
                                'Fibonacci retracements', 'Trend lines'
                            ]
                        else:  # long_term
                            timeframes[config['name']]['recommended_indicators'] = [
                                'RSI(14) - Daily', 'MACD(12,26,9) - Daily', 'SMA(50,100,200) - Daily',
                                'Major support/resistance', 'Long-term trend channels'
                            ]
                            
                except Exception as e:
                    timeframes[config['name']] = {
                        'period': config['description'],
                        'error': f'Data unavailable: {str(e)}',
                        'status': 'Data fetch failed'
                    }
            
            return {
                'timeframes': timeframes,
                'trading_context': {
                    'primary_timeframe': '1-hour bars',
                    'analysis_approach': 'Multi-timeframe analysis',
                    'entry_signals': 'Based on 1h and 4h confluence',
                    'trend_confirmation': 'Daily and 3-month alignment',
                    'recommended_workflow': [
                        '1. Check 3-month trend direction',
                        '2. Confirm 1-month trend alignment', 
                        '3. Look for 2-week setup patterns',
                        '4. Time entry using 3-day/1-hour signals'
                    ]
                },
                'update_frequency': {
                    '1h_data': 'Every hour during market hours',
                    '4h_data': 'Every 4 hours',
                    'daily_data': 'End of trading day',
                    'last_refresh': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            logger.warning(f"Could not get detailed technical analysis time context: {e}")
            
            # Fallback with estimated timeframes
            return {
                'timeframes': {
                    'short_term': {
                        'period': '3 days (1-hour bars)',
                        'data_points': 'Est. 72 bars',
                        'purpose': 'Intraday momentum and entry timing',
                        'status': 'Estimated - actual data unavailable'
                    },
                    'medium_term': {
                        'period': '2 weeks (4-hour bars)', 
                        'data_points': 'Est. 84 bars',
                        'purpose': 'Short-term trend confirmation',
                        'status': 'Estimated - actual data unavailable'
                    },
                    'intermediate_term': {
                        'period': '1 month (daily bars)',
                        'data_points': 'Est. 22 bars',
                        'purpose': 'Medium-term trend analysis',
                        'status': 'Estimated - actual data unavailable'
                    },
                    'long_term': {
                        'period': '3 months (daily bars)',
                        'data_points': 'Est. 66 bars',
                        'purpose': 'Long-term trend and major levels',
                        'status': 'Estimated - actual data unavailable'
                    }
                },
                'trading_context': {
                    'primary_timeframe': '1-hour bars',
                    'note': 'Technical analysis module not available'
                }
            }
    
    def get_technical_timeframes_analysis(self, symbol: str) -> dict:
        """
        Get detailed technical analysis across multiple timeframes for 1-hour bar trading
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with comprehensive technical analysis timeframes
        """
        logger.info(f"📊 Getting multi-timeframe technical analysis for {symbol}...")
        
        try:
            # Get detailed technical context
            tech_context = self._get_technical_analysis_time_context(symbol)
            
            # Add trading recommendations based on timeframes
            trading_recommendations = {
                'timeframe_hierarchy': {
                    'trend_filter': '3-month daily (long-term trend direction)',
                    'setup_timeframe': '1-month daily (trade setup identification)', 
                    'trigger_timeframe': '2-week 4-hour (entry pattern confirmation)',
                    'execution_timeframe': '3-day 1-hour (precise entry/exit timing)'
                },
                'confluence_rules': {
                    'strong_signal': 'All timeframes aligned (3mo, 1mo, 2wk, 3d)',
                    'moderate_signal': '3+ timeframes aligned',
                    'weak_signal': '2 timeframes aligned',
                    'no_trade': 'Major timeframes conflicting'
                },
                'risk_management': {
                    'stop_loss_reference': '1-hour or 4-hour swing points',
                    'position_sizing': 'Based on daily ATR',
                    'profit_targets': 'Daily/weekly key levels'
                }
            }
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'technical_context': tech_context,
                'trading_framework': trading_recommendations,
                'summary': {
                    'primary_trading_timeframe': '1-hour bars',
                    'analysis_method': 'Top-down multi-timeframe analysis',
                    'data_requirements': 'Minimum 3 months historical data'
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting technical timeframes for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    # ...existing code...

def main():
    """Main entry point with command line interface"""
    parser = argparse.ArgumentParser(description='News Trading Analyzer')
    parser.add_argument('--symbol', '-s', type=str, 
                       help='Analyze specific bank symbol (e.g., CBA.AX)')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Analyze all major banks')
    parser.add_argument('--detailed', '-d', action='store_true',
                       help='Include detailed breakdown in results')
    parser.add_argument('--export', '-e', action='store_true',
                       help='Export results to JSON file')
    parser.add_argument('--enhanced', '-en', action='store_true',
                       help='Use enhanced keyword filtering and analysis')
    parser.add_argument('--filtering-test', '-ft', action='store_true',
                       help='Test the enhanced keyword filtering system')
    parser.add_argument('--technical', '-t', action='store_true',
                       help='Show detailed multi-timeframe technical analysis')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    
    args = parser.parse_args()
    
    # Setup logging with specified level
    global logger
    logger = setup_logging(args.log_level)
    
    # Initialize analyzer
    analyzer = NewsTradingAnalyzer()
    
    try:
        if args.filtering_test:
            # Test the enhanced filtering system
            print("\n🧪 Testing Enhanced Keyword Filtering System")
            print("=" * 60)
            
            from app.utils.keywords import BankNewsFilter
            filter_system = BankNewsFilter()
            
            test_titles = [
                "NAB announces record profit amid rising interest rates",
                "RBA holds cash rate steady at 4.35%",
                "Commonwealth Bank faces ASIC investigation over fees",
                "Westpac launches new digital banking platform",
                "Major scam warning for ANZ customers",
                "Tech stocks surge on Wall Street overnight"  # Should not match
            ]
            
            for title in test_titles:
                result = filter_system.is_relevant_banking_news(title)
                print(f"\nTitle: {title}")
                print(f"Relevant: {result['is_relevant']} (Score: {result['relevance_score']:.2f})")
                print(f"Categories: {', '.join(result['categories'])}")
                if result['matched_keywords']:
                    print(f"Keywords: {', '.join(result['matched_keywords'][:3])}")
            
            print(f"\n✅ Enhanced filtering system test complete!")
            return
        
        elif args.technical:
            # Show detailed technical analysis timeframes
            if not args.symbol:
                args.symbol = 'CBA.AX'  # Default to CBA for technical analysis
            
            tech_analysis = analyzer.get_technical_timeframes_analysis(args.symbol)
            
            print(f"\n{'='*60}")
            print(f"MULTI-TIMEFRAME TECHNICAL ANALYSIS: {args.symbol}")
            print(f"{'='*60}")
            
            # Show trading framework
            framework = tech_analysis.get('trading_framework', {})
            if framework:
                print(f"\n🎯 Trading Framework (1-Hour Bar Strategy):")
                hierarchy = framework.get('timeframe_hierarchy', {})
                for level, description in hierarchy.items():
                    print(f"  {level.replace('_', ' ').title()}: {description}")
                
                print(f"\n📊 Signal Confluence Rules:")
                confluence = framework.get('confluence_rules', {})
                for signal_type, rule in confluence.items():
                    print(f"  {signal_type.replace('_', ' ').title()}: {rule}")
            
            # Show technical context details
            tech_context = tech_analysis.get('technical_context', {})
            timeframes = tech_context.get('timeframes', {})
            
            if timeframes:
                print(f"\n⏰ Available Timeframes:")
                for tf_name, tf_data in timeframes.items():
                    print(f"\n  {tf_name.replace('_', ' ').title()}:")
                    print(f"    Period: {tf_data.get('period', 'N/A')}")
                    if 'data_points' in tf_data:
                        print(f"    Data Points: {tf_data['data_points']}")
                    if 'last_update' in tf_data:
                        print(f"    Last Update: {tf_data['last_update']}")
                    if 'recommended_indicators' in tf_data:
                        print(f"    Indicators: {', '.join(tf_data['recommended_indicators'][:3])}")
                    print(f"    Status: {tf_data.get('data_quality', tf_data.get('status', 'Unknown'))}")
            
            # Show trading context
            trading_context = tech_context.get('trading_context', {})
            if trading_context:
                print(f"\n🔄 Recommended Analysis Workflow:")
                workflow = trading_context.get('recommended_workflow', [])
                for i, step in enumerate(workflow, 1):
                    print(f"  {i}. {step}")
            
        elif args.symbol:
            # Analyze single bank
            if args.enhanced:
                result = analyzer.get_enhanced_analysis(args.symbol)
                
                print(f"\n{'='*60}")
                print(f"ENHANCED NEWS TRADING ANALYSIS: {args.symbol}")
                print(f"{'='*60}")
                print(f"Sentiment Score: {result.get('sentiment_score', 'N/A'):.3f}")
                print(f"Standard Confidence: {result.get('confidence', 'N/A'):.3f}")
                print(f"Enhanced Confidence: {result.get('enhanced_confidence', 'N/A'):.3f}")
                print(f"Trading Signal: {result.get('signal', 'N/A')}")
                print(f"Recommendation: {result.get('trading_recommendation', {}).get('action', 'N/A')}")
                
                # Show time context
                time_context = result.get('time_context', {})
                if time_context:
                    print(f"\n⏰ Analysis Time Context:")
                    print(f"  News Period: {time_context.get('news_period', 'N/A')}")
                    print(f"  News Articles: {result.get('news_count', 'N/A')} articles")
                    print(f"  Coverage Quality: {time_context.get('coverage_quality', 'N/A')}")
                    
                    # Show multi-timeframe technical analysis
                    tech_indicators = time_context.get('technical_indicators', {})
                    if tech_indicators:
                        print(f"\n📊 Multi-Timeframe Technical Analysis:")
                        
                        # Show each timeframe
                        for timeframe_name, timeframe_data in tech_indicators.items():
                            if isinstance(timeframe_data, dict) and 'period' in timeframe_data:
                                print(f"  {timeframe_name.replace('_', ' ').title()}:")
                                print(f"    Period: {timeframe_data.get('period', 'N/A')}")
                                print(f"    Timeframe: {timeframe_data.get('timeframe', 'N/A')}")
                                print(f"    Purpose: {timeframe_data.get('purpose', 'N/A')}")
                
                # Show data freshness
                data_freshness = time_context.get('data_freshness', {})
                if data_freshness:
                    print(f"\n📊 Data Freshness:")
                    print(f"  News Data: {data_freshness.get('news_data', 'N/A')}")
                    print(f"  Price Data: {data_freshness.get('price_data', 'N/A')}")
                    print(f"  Technical Data: {data_freshness.get('technical_indicators', 'N/A')}")
                
                # Show filtering insights
                filtering = result.get('filtering_insights', {})
                if filtering and 'filtering_summary' in filtering:
                    fs = filtering['filtering_summary']
                    print(f"\n📊 Filtering Performance:")
                    print(f"  Articles Found: {fs.get('total_articles_found', 'N/A')}")
                    print(f"  Relevant Articles: {fs.get('relevant_articles', 'N/A')}")
                    print(f"  Filtering Efficiency: {fs.get('filtering_efficiency', 0):.1%}")
                    print(f"  Avg Relevance Score: {fs.get('avg_relevance_score', 0):.3f}")
                
                if filtering and 'high_priority_articles' in filtering:
                    print(f"\n🎯 Top Priority Articles:")
                    for i, article in enumerate(filtering['high_priority_articles'][:3], 1):
                        print(f"  {i}. {article['title'][:60]}...")
                        print(f"     Priority: {article['priority_score']:.3f} | Source: {article['source']}")
            else:
                result = analyzer.analyze_single_bank(args.symbol, args.detailed)
            
            print(f"\n{'='*60}")
            print(f"NEWS TRADING ANALYSIS: {args.symbol}")
            print(f"{'='*60}")
            print(f"Sentiment Score: {result.get('sentiment_score', 'N/A'):.3f}")
            print(f"Confidence: {result.get('confidence', 'N/A'):.3f}")
            print(f"Trading Signal: {result.get('signal', 'N/A')}")
            print(f"Recommendation: {result.get('trading_recommendation', {}).get('action', 'N/A')}")
            print(f"Strategy: {result.get('trading_recommendation', {}).get('strategy_type', 'N/A')}")
            print(f"News Articles: {result.get('news_count', 'N/A')}")
            
            # Show time context for regular analysis too
            time_context = result.get('time_context', {})
            if time_context:
                print(f"\n⏰ Analysis Period: {time_context.get('news_period', 'N/A')}")
                print(f"� Data Freshness: {time_context.get('data_freshness', {}).get('news_data', 'N/A')}")
                
                # Show simplified technical timeframes
                tech_indicators = time_context.get('technical_indicators', {})
                if tech_indicators:
                    print(f"\n📊 Technical Analysis Timeframes:")
                    for tf_name, tf_data in tech_indicators.items():
                        if isinstance(tf_data, dict) and 'period' in tf_data:
                            period = tf_data.get('period', 'N/A')
                            timeframe = tf_data.get('timeframe', 'N/A') 
                            print(f"  {tf_name.replace('_', ' ').title()}: {period} ({timeframe})")
                    print(f"  💡 Use --technical for detailed multi-timeframe analysis")
                
                # Show coverage quality
                coverage_quality = time_context.get('coverage_quality', '')
                if coverage_quality:
                    print(f"📰 News Coverage: {coverage_quality}")
            
            if args.detailed:
                print(f"\nRecent Headlines:")
                headlines = result.get('detailed_breakdown', {}).get('recent_headlines', [])
                for i, headline in enumerate(headlines[:3], 1):
                    if headline:
                        print(f"  {i}. {headline}")
            
        elif args.all:
            # Analyze all banks
            result = analyzer.analyze_all_banks(args.detailed)
            
            print(f"\n{'='*60}")
            print(f"MARKET OVERVIEW - AUSTRALIAN BANKS")
            print(f"{'='*60}")
            
            market = result.get('market_overview', {})
            print(f"Average Sentiment: {market.get('average_sentiment', 'N/A'):.3f}")
            print(f"High Confidence Analyses: {market.get('high_confidence_count', 'N/A')}")
            
            most_bullish = market.get('most_bullish', ['N/A', {}])
            most_bearish = market.get('most_bearish', ['N/A', {}])
            print(f"Most Bullish: {most_bullish[0]} ({most_bullish[1].get('sentiment_score', 'N/A'):.3f})")
            print(f"Most Bearish: {most_bearish[0]} ({most_bearish[1].get('sentiment_score', 'N/A'):.3f})")
            
            print(f"\nIndividual Bank Analysis:")
            print("-" * 60)
            for symbol, analysis in result.get('individual_analysis', {}).items():
                signal = analysis.get('signal', 'N/A')
                score = analysis.get('sentiment_score', 'N/A')
                confidence = analysis.get('confidence', 'N/A')
                if isinstance(score, (int, float)) and isinstance(confidence, (int, float)):
                    print(f"{symbol:<8} | {signal:<12} | Score: {score:>6.3f} | Confidence: {confidence:>6.3f}")
                else:
                    print(f"{symbol:<8} | ERROR")
        
        else:
            # Default: quick analysis of CBA
            print("No specific symbol specified. Analyzing CBA.AX as example...")
            result = analyzer.analyze_single_bank('CBA.AX')
            
            print(f"\nQuick Analysis - CBA.AX:")
            print(f"Signal: {result.get('signal', 'N/A')}")
            print(f"Score: {result.get('sentiment_score', 'N/A'):.3f}")
            print(f"Confidence: {result.get('confidence', 'N/A'):.3f}")
            print(f"\nUse --help for more options")
        
        # Export if requested
        if args.export:
            filepath = analyzer.export_analysis(result)
            print(f"\n📄 Results exported to: {filepath}")
        
        print(f"\n{'='*60}")
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
