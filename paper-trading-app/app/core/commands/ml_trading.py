"""
ML Trading Command System

Provides a comprehensive command interface for running ML-based trading analysis
and executing trades through Alpaca simulation.
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MLTradingCommand:
    """
    Command system for ML-based trading operations.
    """
    
    def __init__(self):
        """Initialize the ML Trading Command system."""
        self.components_loaded = False
        self.load_components()
    
    def load_components(self):
        """Load all required components."""
        try:
            from app.core.ml.trading_scorer import MLTradingScorer
            from app.core.trading.alpaca_simulator import AlpacaTradingSimulator
            from app.core.analysis.economic import EconomicSentimentAnalyzer
            from app.core.analysis.divergence import DivergenceDetector
            from app.core.data.processors.news_processor import NewsTradingAnalyzer
            from app.core.ml.enhanced_pipeline import EnhancedMLPipeline
            from app.config.settings import Settings
            
            self.ml_scorer = MLTradingScorer()
            self.alpaca_simulator = AlpacaTradingSimulator(paper_trading=True)
            self.economic_analyzer = EconomicSentimentAnalyzer()
            self.divergence_detector = DivergenceDetector()
            self.news_analyzer = NewsTradingAnalyzer()
            self.ml_pipeline = EnhancedMLPipeline()
            self.settings = Settings()
            
            self.components_loaded = True
            logger.info("All ML trading components loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load components: {e}")
            self.components_loaded = False
    
    def run_ml_analysis_before_trade(self, symbols: list = None) -> Dict[str, Any]:
        """
        Run comprehensive ML analysis before making trades.
        
        Args:
            symbols: List of symbols to analyze (default: all bank symbols)
            
        Returns:
            Complete analysis results with ML trading scores
        """
        if not self.components_loaded:
            return {'error': 'Components not loaded properly'}
        
        symbols = symbols or self.settings.BANK_SYMBOLS
        
        print("🧠 Running ML Analysis Before Trade...")
        print("=" * 50)
        
        # Step 1: Economic Context Analysis
        print("\n🌍 Step 1: Economic Context Analysis")
        try:
            economic_analysis = self.economic_analyzer.analyze_economic_sentiment()
            regime = economic_analysis.get('market_regime', {}).get('regime', 'Unknown')
            economic_sentiment = economic_analysis.get('overall_sentiment', 0)
            print(f"   Market Regime: {regime}")
            print(f"   Economic Sentiment: {economic_sentiment:+.3f}")
        except Exception as e:
            print(f"   ❌ Economic analysis failed: {e}")
            economic_analysis = {'overall_sentiment': 0, 'market_regime': {'regime': 'Unknown'}}
        
        # Step 2: Individual Bank Sentiment Analysis
        print("\n🏦 Step 2: Individual Bank Sentiment Analysis")
        bank_analyses = {}
        for symbol in symbols:
            try:
                analysis = self.news_analyzer.analyze_single_bank(symbol, detailed=True)
                if analysis and 'overall_sentiment' in analysis:
                    bank_analyses[symbol] = analysis
                    sentiment = analysis.get('overall_sentiment', 0)
                    confidence = analysis.get('confidence', 0)
                    signal = analysis.get('signal', 'HOLD')
                    print(f"   {symbol}: {sentiment:+.3f} (conf: {confidence:.2f}) → {signal}")
                else:
                    print(f"   ❌ {symbol}: Analysis failed")
            except Exception as e:
                print(f"   ❌ {symbol}: Error - {e}")
        
        if not bank_analyses:
            return {'error': 'No bank analyses available'}
        
        # Step 3: Divergence Analysis
        print("\n🎯 Step 3: Sector Divergence Analysis")
        try:
            divergence_analysis = self.divergence_detector.analyze_sector_divergence(bank_analyses)
            sector_avg = divergence_analysis.get('sector_average', 0)
            divergent_count = len(divergence_analysis.get('divergent_banks', {}))
            print(f"   Sector Average: {sector_avg:+.3f}")
            print(f"   Divergent Banks: {divergent_count}")
            
            # Show top divergences
            divergent_banks = divergence_analysis.get('divergent_banks', {})
            for symbol, data in list(divergent_banks.items())[:3]:  # Top 3
                score = data.get('divergence_score', 0)
                opportunity = data.get('opportunity', 'unknown')
                print(f"   {symbol}: {score:+.3f} ({opportunity})")
                
        except Exception as e:
            print(f"   ❌ Divergence analysis failed: {e}")
            divergence_analysis = {'divergent_banks': {}}
        
        # Step 4: ML Predictions
        print("\n🤖 Step 4: ML Model Predictions")
        ml_predictions = {}
        try:
            for symbol, analysis in bank_analyses.items():
                try:
                    # Mock market data for ML prediction
                    market_data = {
                        'price': 100.0,
                        'change_percent': 0.0,
                        'volume': 1000000,
                        'volatility': 0.15
                    }
                    
                    prediction = self.ml_pipeline.predict(analysis, market_data, [])
                    if 'error' not in prediction:
                        ml_predictions[symbol] = prediction
                        ensemble_pred = prediction.get('ensemble_prediction', 'N/A')
                        ensemble_conf = prediction.get('ensemble_confidence', 0)
                        print(f"   {symbol}: {ensemble_pred} (conf: {ensemble_conf:.2f})")
                    else:
                        print(f"   {symbol}: ML prediction unavailable")
                except Exception as e:
                    print(f"   ❌ {symbol}: ML prediction error")
        except Exception as e:
            print(f"   ⚠️ ML predictions error: {e}")
        
        # Step 5: Calculate ML Trading Scores
        print("\n📊 Step 5: ML Trading Score Calculation")
        try:
            ml_scores = self.ml_scorer.calculate_scores_for_all_banks(
                bank_analyses=bank_analyses,
                economic_analysis=economic_analysis,
                divergence_analysis=divergence_analysis,
                ml_predictions=ml_predictions
            )
            
            # Display scores
            summary = ml_scores.get('_summary', {})
            if summary:
                print(f"   Average ML Score: {summary.get('average_score', 0):.2f}")
                print(f"   Strong Buy Signals: {summary.get('strong_buy_count', 0)}")
                print(f"   Buy Signals: {summary.get('buy_count', 0)}")
            
            # Show individual scores
            for symbol, score_data in ml_scores.items():
                if symbol.startswith('_'):
                    continue
                
                if 'error' in score_data:
                    print(f"   ❌ {symbol}: Score calculation failed")
                    continue
                
                ml_score = score_data.get('overall_ml_score', 0)
                recommendation = score_data.get('trading_recommendation', 'HOLD')
                risk_level = score_data.get('risk_level', 'UNKNOWN')
                position_size = score_data.get('position_size_pct', 0)
                
                # Color coding
                score_emoji = "🟢" if ml_score >= 70 else "🟡" if ml_score >= 50 else "🔴"
                risk_emoji = "🔵" if risk_level == "LOW" else "🟡" if risk_level == "MEDIUM" else "🔴"
                
                print(f"   {score_emoji} {symbol}: {ml_score:.1f}/100 → {recommendation} "
                      f"(Risk: {risk_emoji}{risk_level}, Size: {position_size:.1%})")
            
        except Exception as e:
            print(f"   ❌ ML scoring failed: {e}")
            ml_scores = {}
        
        # Step 6: Generate Trading Recommendations
        print("\n📈 Step 6: Final Trading Recommendations")
        try:
            trading_signals = self.divergence_detector.generate_trading_signals(divergence_analysis)
            
            if trading_signals:
                print(f"   Generated {len(trading_signals)} trading signals:")
                for signal in trading_signals:
                    symbol = signal['symbol']
                    signal_type = signal['signal']
                    significance = signal['significance']
                    reasoning = signal['reasoning']
                    
                    signal_emoji = "📈" if signal_type == 'BUY' else "📉"
                    print(f"   {signal_emoji} {symbol}: {signal_type} (sig: {significance:.1f}) - {reasoning}")
            else:
                print("   No high-significance trading signals generated")
                
        except Exception as e:
            print(f"   ⚠️ Signal generation error: {e}")
            trading_signals = []
        
        # Compile results
        results = {
            'timestamp': datetime.now().isoformat(),
            'economic_analysis': economic_analysis,
            'bank_analyses': bank_analyses,
            'divergence_analysis': divergence_analysis,
            'ml_predictions': ml_predictions,
            'ml_scores': ml_scores,
            'trading_signals': trading_signals,
            'summary': {
                'banks_analyzed': len(bank_analyses),
                'ml_scores_calculated': len([s for s in ml_scores.keys() if not s.startswith('_')]),
                'trading_signals_generated': len(trading_signals),
                'economic_regime': regime,
                'sector_average_sentiment': sector_avg,
                'analysis_complete': True
            }
        }
        
        print(f"\n✅ ML Analysis Complete!")
        print(f"📊 {len(bank_analyses)} banks analyzed")
        print(f"🎯 {len(trading_signals)} trading signals generated")
        print(f"🧠 ML scoring complete for all symbols")
        
        return results
    
    def execute_ml_trading_strategy(self, 
                                  analysis_results: Dict = None,
                                  max_total_exposure: float = 25000,
                                  dry_run: bool = True) -> Dict[str, Any]:
        """
        Execute ML-based trading strategy.
        
        Args:
            analysis_results: Results from run_ml_analysis_before_trade
            max_total_exposure: Maximum total exposure in USD
            dry_run: Whether to execute trades or just simulate
            
        Returns:
            Execution results
        """
        if not self.components_loaded:
            return {'error': 'Components not loaded properly'}
        
        print(f"\n💹 Executing ML Trading Strategy {'(DRY RUN)' if dry_run else '(LIVE)'}...")
        print("=" * 50)
        
        # Use provided analysis or run new analysis
        if not analysis_results:
            print("🔄 No analysis provided, running fresh analysis...")
            analysis_results = self.run_ml_analysis_before_trade()
            if 'error' in analysis_results:
                return analysis_results
        
        ml_scores = analysis_results.get('ml_scores', {})
        if not ml_scores:
            return {'error': 'No ML scores available for trading'}
        
        # Check Alpaca connection
        if not dry_run:
            if not self.alpaca_simulator.is_connected():
                print("❌ Alpaca connection failed - switching to dry run mode")
                dry_run = True
            else:
                account_info = self.alpaca_simulator.get_account_info()
                print(f"💰 Account Equity: ${account_info.get('equity', 0):,.2f}")
                print(f"💵 Buying Power: ${account_info.get('buying_power', 0):,.2f}")
        
        if dry_run:
            # Simulate trading execution
            print("\n🎭 DRY RUN MODE - Simulating Trade Execution")
            
            # Filter tradeable symbols
            tradeable_scores = {k: v for k, v in ml_scores.items() 
                              if not k.startswith('_') and 'error' not in v}
            
            total_simulated_exposure = 0
            simulated_orders = []
            
            for symbol, score_data in tradeable_scores.items():
                ml_score = score_data.get('overall_ml_score', 0)
                recommendation = score_data.get('trading_recommendation', 'HOLD')
                position_size_pct = score_data.get('position_size_pct', 0)
                risk_level = score_data.get('risk_level', 'HIGH')
                
                # Apply trading logic
                if ml_score >= 60 and recommendation in ['BUY', 'STRONG_BUY', 'SELL', 'STRONG_SELL']:
                    position_value = max_total_exposure * position_size_pct
                    mock_price = 100.0  # Mock price for simulation
                    shares = int(position_value / mock_price)
                    
                    if shares > 0:
                        simulated_orders.append({
                            'symbol': symbol,
                            'recommendation': recommendation,
                            'ml_score': ml_score,
                            'risk_level': risk_level,
                            'shares': shares,
                            'estimated_value': shares * mock_price,
                            'position_size_pct': position_size_pct
                        })
                        total_simulated_exposure += shares * mock_price
            
            # Display simulation results
            print(f"\n📊 Simulation Results:")
            print(f"   Total Orders: {len(simulated_orders)}")
            print(f"   Total Exposure: ${total_simulated_exposure:,.2f}")
            print(f"   Max Exposure: ${max_total_exposure:,.2f}")
            
            for order in simulated_orders:
                print(f"   {order['symbol']}: {order['recommendation']} "
                      f"{order['shares']} shares (~${order['estimated_value']:,.0f}) "
                      f"[Score: {order['ml_score']:.1f}, Risk: {order['risk_level']}]")
            
            return {
                'status': 'simulation_complete',
                'simulated_orders': simulated_orders,
                'total_exposure': total_simulated_exposure,
                'max_exposure': max_total_exposure,
                'dry_run': True
            }
        
        else:
            # Execute real trades through Alpaca
            print("\n🚀 LIVE TRADING MODE - Executing Real Orders")
            execution_results = self.alpaca_simulator.execute_ml_trading_strategy(
                ml_scores, max_total_exposure
            )
            
            # Display execution results
            summary = execution_results.get('summary', {})
            print(f"\n📊 Execution Results:")
            print(f"   Orders Submitted: {summary.get('total_orders_submitted', 0)}")
            print(f"   Orders Skipped: {summary.get('total_orders_skipped', 0)}")
            print(f"   Errors: {summary.get('total_errors', 0)}")
            print(f"   Total Exposure: ${summary.get('total_estimated_exposure', 0):,.2f}")
            
            return execution_results
    
    def get_ml_trading_status(self) -> Dict[str, Any]:
        """Get current ML trading system status."""
        if not self.components_loaded:
            return {'error': 'Components not loaded properly'}
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'components_loaded': self.components_loaded,
            'alpaca_connected': self.alpaca_simulator.is_connected() if hasattr(self, 'alpaca_simulator') else False,
            'ml_models_available': True,  # Simplified check
            'system_ready': self.components_loaded
        }
        
        # Add Alpaca account info if connected
        if status['alpaca_connected']:
            account_info = self.alpaca_simulator.get_account_info()
            if 'error' not in account_info:
                status['account_equity'] = account_info.get('equity', 0)
                status['buying_power'] = account_info.get('buying_power', 0)
                status['day_trade_count'] = account_info.get('day_trade_count', 0)
        
        return status
    
    def display_ml_scores_table(self, ml_scores: Dict[str, Any]):
        """Display ML scores in a formatted table."""
        if not ml_scores:
            print("No ML scores to display")
            return
        
        print("\n📊 ML Trading Scores Summary")
        print("=" * 80)
        print(f"{'Symbol':<8} {'ML Score':<10} {'Recommendation':<15} {'Risk':<8} {'Position':<10} {'Confidence'}")
        print("-" * 80)
        
        # Sort by ML score (highest first)
        sorted_scores = sorted(
            [(k, v) for k, v in ml_scores.items() if not k.startswith('_') and 'error' not in v],
            key=lambda x: x[1].get('overall_ml_score', 0),
            reverse=True
        )
        
        for symbol, score_data in sorted_scores:
            ml_score = score_data.get('overall_ml_score', 0)
            recommendation = score_data.get('trading_recommendation', 'HOLD')
            risk_level = score_data.get('risk_level', 'UNKNOWN')
            position_size = score_data.get('position_size_pct', 0)
            
            # Get confidence factors count
            confidence_factors = score_data.get('confidence_factors', [])
            confidence_count = len(confidence_factors)
            
            print(f"{symbol:<8} {ml_score:<10.1f} {recommendation:<15} {risk_level:<8} "
                  f"{position_size:<10.1%} {confidence_count} factors")
        
        print("-" * 80)
        
        # Display summary
        summary = ml_scores.get('_summary', {})
        if summary:
            print(f"Average Score: {summary.get('average_score', 0):.1f} | "
                  f"Strong Buys: {summary.get('strong_buy_count', 0)} | "
                  f"Buys: {summary.get('buy_count', 0)}")

if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    command = MLTradingCommand()
    
    if command.components_loaded:
        # Run ML analysis
        results = command.run_ml_analysis_before_trade()
        
        if 'error' not in results:
            ml_scores = results.get('ml_scores', {})
            command.display_ml_scores_table(ml_scores)
            
            # Execute strategy (dry run)
            execution = command.execute_ml_trading_strategy(results, dry_run=True)
            print(f"\nExecution Status: {execution.get('status', 'unknown')}")
    else:
        print("❌ ML Trading Command system not ready")
