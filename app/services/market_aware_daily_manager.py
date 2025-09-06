"""
Market-Aware Daily Manager Integration
Updates the daily trading routine to use market context analysis
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..core.ml.prediction import MarketAwarePricePredictor, create_market_aware_predictor
from .daily_manager import TradingSystemManager

logger = logging.getLogger(__name__)

class MarketAwareTradingManager(TradingSystemManager):
    """
    Enhanced Trading System Manager with Market Context Awareness
    Extends the base daily manager with market-aware prediction capabilities
    """
    
    def __init__(self, config_path=None, dry_run=False):
        super().__init__(config_path, dry_run)
        self.market_predictor = create_market_aware_predictor()
        
    def enhanced_morning_routine(self):
        """Enhanced morning routine with market-aware predictions"""
        print("🌅 MARKET-AWARE MORNING ROUTINE")
        print("=" * 60)
        
        try:
            # Get market context first
            market_context = self.market_predictor.get_cached_market_context()
            
            print(f"🌐 Market Context Analysis:")
            print(f"   ASX 200 Level: {market_context['current_level']:.1f}")
            print(f"   5-day Trend: {market_context['trend_pct']:+.2f}%")
            print(f"   Market Context: {market_context['context']}")
            print(f"   BUY Threshold: {market_context['buy_threshold']:.1%}")
            print(f"   Confidence Multiplier: {market_context['confidence_multiplier']:.1f}x")
            
            # Alert for market conditions
            if market_context['context'] == 'BEARISH':
                print("⚠️  BEARISH MARKET DETECTED - Using stricter signal criteria")
            elif market_context['context'] == 'BULLISH':
                print("📈 BULLISH MARKET DETECTED - Enhanced opportunities expected")
            
            # Run base morning routine
            super().morning_routine()
            
            # Generate market-aware predictions
            print(f"\n🎯 Generating Market-Aware Trading Signals...")
            predictions = self._generate_market_aware_signals()
            
            if predictions:
                self._display_prediction_summary(predictions, market_context)
                
                # Save predictions to database
                try:
                    self.market_predictor.save_predictions_to_database(predictions)
                    print(f"✅ Saved {len(predictions)} predictions to database")
                except Exception as e:
                    logger.error(f"Failed to save predictions: {e}")
            else:
                print("📊 No trading signals generated")
                
        except Exception as e:
            logger.error(f"Error in enhanced morning routine: {e}")
            print(f"❌ Enhanced morning routine failed: {e}")
            # Fallback to base routine
            super().morning_routine()
    
    def _generate_market_aware_signals(self) -> Dict:
        """Generate trading signals using market-aware prediction system"""
        
        # Sample stock data (in a real system, this would come from data collectors)
        sample_symbols = ["CBA.AX", "WBC.AX", "ANZ.AX", "NAB.AX", "MQG.AX", "SUN.AX", "QBE.AX"]
        portfolio_data = {}
        
        try:
            # For demonstration, we'll use sample data
            # In production, this would fetch real market data
            for symbol in sample_symbols:
                portfolio_data[symbol] = {
                    'current_price': 50.0 + (hash(symbol) % 100),  # Sample price
                    'features': {
                        'technical_score': 55 + (hash(symbol) % 30),  # Sample tech score
                        'sentiment_score': 45 + (hash(symbol) % 20),  # Sample sentiment
                        'volume_ratio': 0.8 + (hash(symbol) % 10) / 20,  # Sample volume
                        'volatility': 0.015 + (hash(symbol) % 10) / 1000,  # Sample volatility
                        'news_confidence': 0.6 + (hash(symbol) % 4) / 10,  # Sample confidence
                        'rsi': 40 + (hash(symbol) % 40),  # Sample RSI
                        'macd_signal': -2 + (hash(symbol) % 4),  # Sample MACD
                        'volume_trend': -0.1 + (hash(symbol) % 20) / 100  # Sample volume trend
                    }
                }
            
            # Generate market-aware predictions
            predictions = self.market_predictor.predict_portfolio_with_market_context(portfolio_data)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating market-aware signals: {e}")
            return {}
    
    def _display_prediction_summary(self, predictions: Dict, market_context: Dict):
        """Display formatted prediction summary"""
        
        if not predictions:
            return
            
        print(f"\n📊 MARKET-AWARE PREDICTION SUMMARY")
        print(f"   Market Context: {market_context['context']}")
        print(f"   Symbols Analyzed: {len(predictions)}")
        
        # Categorize predictions by action
        buy_signals = []
        strong_buy_signals = []
        hold_signals = []
        
        for symbol, prediction in predictions.items():
            details = prediction.supporting_features.get('prediction_details', {})
            action = details.get('recommended_action', 'HOLD')
            
            if action == 'STRONG_BUY':
                strong_buy_signals.append((symbol, prediction))
            elif action == 'BUY':
                buy_signals.append((symbol, prediction))
            else:
                hold_signals.append((symbol, prediction))
        
        # Display results
        print(f"   📈 STRONG BUY: {len(strong_buy_signals)}")
        print(f"   📊 BUY: {len(buy_signals)}")
        print(f"   ⏸️  HOLD: {len(hold_signals)}")
        
        # Show top signals
        if strong_buy_signals:
            print(f"\n🚀 STRONG BUY SIGNALS:")
            for symbol, prediction in strong_buy_signals[:5]:  # Top 5
                details = prediction.supporting_features.get('prediction_details', {})
                print(f"   {symbol}: {prediction.confidence:.1%} confidence")
                print(f"      Price: ${prediction.current_price:.2f} → ${prediction.predicted_price:.2f} ({prediction.price_change_pct:+.1f}%)")
                print(f"      Technical: {details.get('tech_score', 0):.0f} | News: {details.get('news_sentiment', 0):+.2f}")
        
        if buy_signals:
            print(f"\n📈 BUY SIGNALS:")
            for symbol, prediction in buy_signals[:3]:  # Top 3
                details = prediction.supporting_features.get('prediction_details', {})
                print(f"   {symbol}: {prediction.confidence:.1%} confidence")
                print(f"      Price: ${prediction.current_price:.2f} → ${prediction.predicted_price:.2f} ({prediction.price_change_pct:+.1f}%)")
        
        # Market context warnings
        total_buy_signals = len(buy_signals) + len(strong_buy_signals)
        total_signals = len(predictions)
        buy_rate = total_buy_signals / total_signals if total_signals > 0 else 0
        
        if market_context['context'] == 'BEARISH' and buy_rate > 0.3:
            print(f"\n⚠️  WARNING: High BUY signal rate ({buy_rate:.1%}) during BEARISH market")
            print(f"   Manual review recommended for risk management")
        
        print(f"\n💡 Market-aware thresholds applied based on {market_context['context']} conditions")
    
    def quick_market_status(self):
        """Quick market status check"""
        print("🔍 QUICK MARKET STATUS CHECK")
        print("=" * 40)
        
        try:
            market_context = self.market_predictor.get_cached_market_context()
            
            print(f"📊 ASX 200: {market_context['current_level']:.1f} ({market_context['trend_pct']:+.2f}%)")
            print(f"🌐 Market Context: {market_context['context']}")
            print(f"🎯 Current BUY Threshold: {market_context['buy_threshold']:.1%}")
            
            # Market advice
            if market_context['context'] == 'BEARISH':
                print("💡 Advice: Conservative approach recommended")
                print("   • Higher confidence required for BUY signals")
                print("   • Focus on defensive stocks")
                print("   • Consider cash positions")
            elif market_context['context'] == 'BULLISH':
                print("💡 Advice: Growth opportunities available")
                print("   • Lower thresholds for quality stocks")
                print("   • Consider momentum strategies")
                print("   • Monitor for overextension")
            else:
                print("💡 Advice: Balanced approach suitable")
                print("   • Standard criteria applied")
                print("   • Monitor for trend changes")
            
        except Exception as e:
            logger.error(f"Error in market status check: {e}")
            print(f"❌ Market status check failed: {e}")


def create_market_aware_manager(config_path=None, dry_run=False) -> MarketAwareTradingManager:
    """Factory function to create market-aware trading manager"""
    return MarketAwareTradingManager(config_path, dry_run)


# Integration helper functions
def upgrade_daily_manager_to_market_aware():
    """
    Helper function to demonstrate how to upgrade existing daily manager
    """
    print("🔄 Upgrading Daily Manager to Market-Aware System...")
    
    # Create market-aware manager
    manager = create_market_aware_manager()
    
    print("✅ Market-Aware Trading Manager ready")
    print("💡 Available methods:")
    print("   • enhanced_morning_routine() - Morning routine with market context")
    print("   • quick_market_status() - Quick market assessment")
    print("   • _generate_market_aware_signals() - Generate trading signals")
    
    return manager


if __name__ == "__main__":
    # Demo the market-aware manager
    manager = upgrade_daily_manager_to_market_aware()
    manager.quick_market_status()
