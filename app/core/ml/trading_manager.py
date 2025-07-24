"""
ML Trading Command System

Provides a comprehensive interface for running ML-based trading analysis and execution.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MLTradingManager:
    """
    Manages the complete ML trading workflow.
    """
    
    def __init__(self):
        """Initialize the ML Trading Manager."""
        self.economic_analyzer = None
        self.divergence_detector = None
        self.news_analyzer = None
        self.ml_scorer = None
        self.alpaca_trader = None
        self.ml_tracker = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all ML trading components."""
        try:
            from app.config.settings import Settings
            self.settings = Settings()
            
            from app.core.analysis.economic import EconomicSentimentAnalyzer
            from app.core.analysis.divergence import DivergenceDetector
            from app.core.data.processors.news_processor import NewsTradingAnalyzer
            from app.core.ml.trading_scorer import MLTradingScorer
            
            self.economic_analyzer = EconomicSentimentAnalyzer()
            self.divergence_detector = DivergenceDetector()
            self.news_analyzer = NewsTradingAnalyzer()
            self.ml_scorer = MLTradingScorer()
            
            # Initialize ML performance tracker
            try:
                from app.core.ml.tracking.progression_tracker import MLProgressionTracker
                self.ml_tracker = MLProgressionTracker()
                logger.info("ML performance tracking initialized")
            except Exception as tracker_error:
                logger.warning(f"ML tracker not available: {tracker_error}")
                self.ml_tracker = None
            
            # Try to initialize Alpaca, but continue if it fails
            try:
                from app.core.trading.alpaca_integration import AlpacaMLTrader
                self.alpaca_trader = AlpacaMLTrader(paper=True)
            except Exception as alpaca_error:
                logger.warning(f"Alpaca integration not available: {alpaca_error}")
                self.alpaca_trader = None
            
            logger.info("ML Trading Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing ML Trading Manager: {e}")
            # Ensure settings is available even if other components fail
            if not hasattr(self, 'settings'):
                from app.config.settings import Settings
                self.settings = Settings()
    
    def run_complete_ml_analysis(self, symbols: list = None) -> Dict[str, Any]:
        """
        Run complete ML analysis for selected symbols.
        
        Args:
            symbols: List of symbols to analyze (default: all bank symbols)
            
        Returns:
            Complete analysis results
        """
        if symbols is None:
            symbols = self.settings.BANK_SYMBOLS
        
        logger.info(f"Running complete ML analysis for {len(symbols)} symbols...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'symbols_analyzed': symbols,
            'economic_analysis': {},
            'bank_analyses': {},
            'divergence_analysis': {},
            'ml_scores': {},
            'trading_recommendations': {},
            'summary': {}
        }
        
        try:
            # 1. Economic Context Analysis
            print("🌍 Analyzing economic context...")
            results['economic_analysis'] = self.economic_analyzer.analyze_economic_sentiment()
            regime = results['economic_analysis'].get('market_regime', {}).get('regime', 'Unknown')
            print(f"   Market Regime: {regime}")
            
            # 2. Individual Bank Sentiment Analysis
            print(f"\n🏦 Analyzing sentiment for {len(symbols)} banks...")
            bank_analyses = {}
            for symbol in symbols:
                try:
                    analysis = self.news_analyzer.analyze_single_bank(symbol, detailed=True)
                    if analysis and 'overall_sentiment' in analysis:
                        bank_analyses[symbol] = analysis
                        sentiment = analysis['overall_sentiment']
                        confidence = analysis['confidence']
                        print(f"   {symbol}: Sentiment {sentiment:+.3f} (Confidence: {confidence:.2f})")
                except Exception as e:
                    print(f"   ❌ {symbol}: Analysis failed - {e}")
            
            results['bank_analyses'] = bank_analyses
            
            # 3. Divergence Analysis
            print(f"\n🎯 Analyzing sector divergence...")
            if bank_analyses:
                divergence_analysis = self.divergence_detector.analyze_sector_divergence(bank_analyses)
                results['divergence_analysis'] = divergence_analysis
                
                sector_avg = divergence_analysis.get('sector_average', 0)
                divergent_count = len(divergence_analysis.get('divergent_banks', {}))
                print(f"   Sector Average: {sector_avg:+.3f}")
                print(f"   Divergent Banks: {divergent_count}")
            
            # 4. ML Trading Scores
            print(f"\n🧠 Calculating ML trading scores...")
            if bank_analyses:
                ml_scores = self.ml_scorer.calculate_scores_for_all_banks(
                    bank_analyses=bank_analyses,
                    economic_analysis=results['economic_analysis'],
                    divergence_analysis=results['divergence_analysis']
                )
                results['ml_scores'] = ml_scores
                
                # Display ML scores
                for symbol, score_data in ml_scores.items():
                    if symbol.startswith('_'):
                        continue
                    
                    if 'error' not in score_data:
                        ml_score = score_data['overall_ml_score']
                        recommendation = score_data['trading_recommendation']
                        risk_level = score_data['risk_level']
                        print(f"   {symbol}: ML Score {ml_score:.1f}/100 | {recommendation} | Risk: {risk_level}")
                    else:
                        print(f"   ❌ {symbol}: ML scoring failed")
            
            # 5. Generate Trading Recommendations
            print(f"\n📈 Generating trading recommendations...")
            trading_recommendations = self._generate_trading_recommendations(results)
            results['trading_recommendations'] = trading_recommendations
            
            # 6. Summary
            results['summary'] = self._generate_summary(results)
            
            # 7. Record ML Performance Metrics
            self._record_ml_performance(results)
            
            print(f"\n✅ Complete ML analysis finished")
            return results
            
        except Exception as e:
            logger.error(f"Error in complete ML analysis: {e}")
            results['error'] = str(e)
            return results
    
    def run_ml_trading_session(self, symbols: list = None, execute_trades: bool = False) -> Dict[str, Any]:
        """
        Run a complete ML trading session with optional trade execution.
        
        Args:
            symbols: List of symbols to analyze
            execute_trades: Whether to actually execute trades via Alpaca
            
        Returns:
            Trading session results
        """
        print("🚀 Starting ML Trading Session...")
        print("=" * 50)
        
        # Run complete analysis
        analysis_results = self.run_complete_ml_analysis(symbols)
        
        if 'error' in analysis_results:
            return {'error': f"Analysis failed: {analysis_results['error']}"}
        
        session_results = {
            'analysis': analysis_results,
            'trading_execution': {},
            'performance': {}
        }
        
        # Execute trades if requested
        if execute_trades:
            print(f"\n💰 Executing trades via Alpaca...")
            
            if self.alpaca_trader.is_available():
                ml_scores = analysis_results.get('ml_scores', {})
                execution_results = self.alpaca_trader.execute_ml_trading_strategy(ml_scores)
                session_results['trading_execution'] = execution_results
                
                orders_placed = execution_results.get('summary', {}).get('orders_placed', 0)
                print(f"   📊 Orders placed: {orders_placed}")
                
                # Get performance update
                performance = self.alpaca_trader.get_ml_trade_performance()
                session_results['performance'] = performance
                
            else:
                print(f"   ❌ Alpaca trading not available")
                session_results['trading_execution'] = {'error': 'Alpaca not available'}
        else:
            print(f"\n📊 Trade execution skipped (dry run)")
        
        # Save results
        self._save_session_results(session_results)
        
        print(f"\n🎯 ML Trading Session Complete!")
        return session_results
    
    def display_ml_scores_summary(self, symbols: list = None):
        """
        Display a summary of ML trading scores for all banks.
        
        Args:
            symbols: List of symbols to display (default: all bank symbols)
        """
        if symbols is None:
            symbols = self.settings.BANK_SYMBOLS
        
        print("🧠 ML Trading Scores Summary")
        print("=" * 40)
        
        try:
            # Run analysis to get ML scores
            results = self.run_complete_ml_analysis(symbols)
            ml_scores = results.get('ml_scores', {})
            
            if not ml_scores:
                print("❌ No ML scores available")
                return
            
            # Display header
            print(f"{'Bank':<8} {'ML Score':<10} {'Recommendation':<12} {'Risk':<8} {'Position %':<10}")
            print("-" * 55)
            
            # Display each bank
            for symbol in symbols:
                if symbol in ml_scores and 'error' not in ml_scores[symbol]:
                    score_data = ml_scores[symbol]
                    ml_score = score_data['overall_ml_score']
                    recommendation = score_data['trading_recommendation']
                    risk_level = score_data['risk_level']
                    position_pct = score_data['position_size_pct'] * 100
                    
                    print(f"{symbol:<8} {ml_score:<10.1f} {recommendation:<12} {risk_level:<8} {position_pct:<10.1f}%")
                else:
                    print(f"{symbol:<8} {'ERROR':<10} {'N/A':<12} {'N/A':<8} {'N/A':<10}")
            
            # Display summary
            summary = ml_scores.get('_summary', {})
            if summary:
                print("\n📊 Summary:")
                print(f"   Average Score: {summary.get('average_score', 0):.1f}")
                print(f"   Highest Score: {summary.get('highest_score', 0):.1f}")
                print(f"   Strong Buy Count: {summary.get('strong_buy_count', 0)}")
                print(f"   Buy Count: {summary.get('buy_count', 0)}")
            
        except Exception as e:
            print(f"❌ Error displaying ML scores: {e}")
    
    def check_before_trade(self, symbol: str) -> Dict[str, Any]:
        """
        Run ML analysis before making a trade for a specific symbol.
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Pre-trade analysis results
        """
        print(f"🔍 Pre-Trade ML Analysis for {symbol}")
        print("=" * 40)
        
        try:
            # Run focused analysis for this symbol
            results = self.run_complete_ml_analysis([symbol])
            
            if symbol not in results.get('ml_scores', {}):
                return {'error': f'No ML score available for {symbol}'}
            
            score_data = results['ml_scores'][symbol]
            
            if 'error' in score_data:
                return {'error': f'ML analysis failed for {symbol}'}
            
            # Extract key information
            pre_trade_info = {
                'symbol': symbol,
                'ml_score': score_data['overall_ml_score'],
                'recommendation': score_data['trading_recommendation'],
                'risk_level': score_data['risk_level'],
                'position_size_pct': score_data['position_size_pct'],
                'confidence_factors': score_data['confidence_factors'],
                'risk_factors': score_data['risk_factors'],
                'component_scores': score_data['component_scores'],
                'economic_regime': results['economic_analysis']['market_regime']['regime'],
                'sector_context': results.get('divergence_analysis', {}).get('summary', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            # Display results
            print(f"ML Score: {pre_trade_info['ml_score']:.1f}/100")
            print(f"Recommendation: {pre_trade_info['recommendation']}")
            print(f"Risk Level: {pre_trade_info['risk_level']}")
            print(f"Position Size: {pre_trade_info['position_size_pct']*100:.1f}%")
            print(f"Economic Regime: {pre_trade_info['economic_regime']}")
            
            if pre_trade_info['confidence_factors']:
                print(f"\n✅ Confidence Factors:")
                for factor in pre_trade_info['confidence_factors']:
                    print(f"   • {factor}")
            
            if pre_trade_info['risk_factors']:
                print(f"\n⚠️ Risk Factors:")
                for factor in pre_trade_info['risk_factors']:
                    print(f"   • {factor}")
            
            print(f"\n📊 Component Scores:")
            for component, score in pre_trade_info['component_scores'].items():
                print(f"   {component.replace('_', ' ').title()}: {score:.1f}")
            
            return pre_trade_info
            
        except Exception as e:
            logger.error(f"Error in pre-trade analysis for {symbol}: {e}")
            return {'error': str(e)}
    
    def _generate_trading_recommendations(self, analysis_results: Dict) -> Dict[str, Any]:
        """Generate comprehensive trading recommendations."""
        recommendations = {
            'strong_buy': [],
            'buy': [],
            'hold': [],
            'sell': [],
            'strong_sell': []
        }
        
        ml_scores = analysis_results.get('ml_scores', {})
        
        for symbol, score_data in ml_scores.items():
            if symbol.startswith('_') or 'error' in score_data:
                continue
            
            recommendation = score_data.get('trading_recommendation', 'HOLD')
            ml_score = score_data.get('overall_ml_score', 0)
            
            rec_data = {
                'symbol': symbol,
                'ml_score': ml_score,
                'risk_level': score_data.get('risk_level', 'UNKNOWN'),
                'position_size': score_data.get('position_size_pct', 0)
            }
            
            if recommendation == 'STRONG_BUY':
                recommendations['strong_buy'].append(rec_data)
            elif recommendation in ['BUY', 'WEAK_BUY']:
                recommendations['buy'].append(rec_data)
            elif recommendation in ['SELL', 'WEAK_SELL']:
                recommendations['sell'].append(rec_data)
            elif recommendation == 'STRONG_SELL':
                recommendations['strong_sell'].append(rec_data)
            else:
                recommendations['hold'].append(rec_data)
        
        return recommendations
    
    def _generate_summary(self, analysis_results: Dict) -> Dict[str, Any]:
        """Generate analysis summary."""
        summary = {
            'symbols_analyzed': len(analysis_results.get('bank_analyses', {})),
            'economic_regime': analysis_results.get('economic_analysis', {}).get('market_regime', {}).get('regime', 'Unknown'),
            'sector_average_sentiment': analysis_results.get('divergence_analysis', {}).get('sector_average', 0),
            'divergent_banks_count': len(analysis_results.get('divergence_analysis', {}).get('divergent_banks', {})),
            'ml_scores_summary': analysis_results.get('ml_scores', {}).get('_summary', {}),
            'total_recommendations': {}
        }
        
        # Count recommendations
        trading_recs = analysis_results.get('trading_recommendations', {})
        summary['total_recommendations'] = {
            'strong_buy': len(trading_recs.get('strong_buy', [])),
            'buy': len(trading_recs.get('buy', [])),
            'hold': len(trading_recs.get('hold', [])),
            'sell': len(trading_recs.get('sell', [])),
            'strong_sell': len(trading_recs.get('strong_sell', []))
        }
        
        return summary
    
    def _record_ml_performance(self, analysis_results: Dict):
        """Record ML performance metrics from analysis results"""
        if not self.ml_tracker:
            return
        
        try:
            # Extract predictions from bank analyses
            predictions_recorded = 0
            bank_analyses = analysis_results.get('bank_analyses', {})
            
            for symbol, analysis in bank_analyses.items():
                if 'overall_sentiment' in analysis:
                    sentiment_score = analysis.get('overall_sentiment', 0.0)
                    
                    # Extract ML trading confidence if available, otherwise use overall confidence
                    ml_confidence = analysis.get('ml_confidence', None)
                    
                    # Debug: Check what keys are available
                    print(f"🔍 Analysis keys for {symbol}: {list(analysis.keys())}")
                    print(f"🔍 ML confidence raw value: {analysis.get('ml_confidence', 'MISSING')}")
                    
                    # Use ML confidence if available, otherwise fallback to overall confidence
                    confidence = ml_confidence if ml_confidence is not None else analysis.get('confidence', 0.8)
                    
                    # Debug logging for confidence tracking
                    print(f"🔍 DEBUG - {symbol}: Sentiment={sentiment_score:.4f}, Overall Conf={analysis.get('confidence', 0.8):.4f}, ML Conf={ml_confidence}, Final={confidence:.4f}")
                    
                    # Convert sentiment score to trading signal
                    if sentiment_score > 0.05:  # Positive sentiment threshold
                        signal = "BUY"
                    elif sentiment_score < -0.05:  # Negative sentiment threshold
                        signal = "SELL"
                    else:
                        signal = "HOLD"  # Neutral sentiment
                    
                    prediction_data = {
                        'signal': signal,
                        'confidence': confidence,
                        'sentiment_score': sentiment_score,
                        'pattern_strength': min(confidence * 0.8, 1.0),  # Derived from confidence
                        'features': {
                            'sentiment': sentiment_score,
                            'news_count': analysis.get('news_count', 0),
                            'volume': 1.0,
                            'volatility': 0.15
                        }
                    }
                    
                    self.ml_tracker.record_prediction(symbol, prediction_data)
                    predictions_recorded += 1
            
            # Record trading performance based on analysis quality
            if predictions_recorded > 0:
                # Estimate performance based on confidence levels
                total_confidence = sum(
                    analysis.get('confidence', 0) 
                    for analysis in bank_analyses.values()
                    if 'confidence' in analysis
                )
                avg_confidence = total_confidence / predictions_recorded if predictions_recorded > 0 else 0.8
                
                # Estimate successful predictions based on confidence
                estimated_successful = int(predictions_recorded * min(avg_confidence, 0.9))
                
                performance_data = {
                    'successful_trades': estimated_successful,
                    'total_trades': predictions_recorded,
                    'average_confidence': round(avg_confidence, 3),
                    'predictions_made': predictions_recorded
                }
                
                self.ml_tracker.record_daily_performance(performance_data)
                logger.info(f"Recorded ML performance: {predictions_recorded} predictions, {avg_confidence:.1%} avg confidence")
            
        except Exception as e:
            logger.warning(f"Could not record ML performance: {e}")
    
    def _save_session_results(self, session_results: Dict):
        """Save session results to file."""
        try:
            import os
            os.makedirs('data/ml_trading_sessions', exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/ml_trading_sessions/session_{timestamp}.json'
            
            with open(filename, 'w') as f:
                json.dump(session_results, f, indent=2)
            
            logger.info(f"Session results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving session results: {e}")

if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    manager = MLTradingManager()
    
    # Display ML scores summary
    manager.display_ml_scores_summary()
    
    # Run pre-trade analysis for a specific symbol
    print("\n" + "="*50)
    pre_trade = manager.check_before_trade('CBA.AX')
    
    # Run complete trading session (dry run)
    print("\n" + "="*50)
    session = manager.run_ml_trading_session(execute_trades=False)
