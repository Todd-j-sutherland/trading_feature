#!/usr/bin/env python3
"""
Enhanced Technical Analysis Component for Dashboard
Provides isolated testing and integration with the main dashboard
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, List
from technical_analysis_engine import TechnicalAnalysisEngine

class DashboardTechnicalAnalysis:
    """
    Enhanced technical analysis component for the dashboard
    Provides both isolated testing and integration capabilities
    """
    
    def __init__(self, db_path: str = "data/ml_models/training_data.db"):
        self.db_path = db_path
        self.tech_engine = TechnicalAnalysisEngine(db_path)
    
    def test_technical_analysis_isolated(self) -> bool:
        """
        Test technical analysis functionality in isolation
        Returns True if all tests pass
        """
        print("🔧 ISOLATED TECHNICAL ANALYSIS COMPONENT TEST")
        print("=" * 55)
        
        try:
            # Test 1: Database technical data retrieval
            print("\n1. Testing Database Technical Data Retrieval:")
            tech_data = self.get_current_technical_data()
            
            if tech_data:
                print(f"✅ Retrieved technical data for {len(tech_data)} banks")
                for bank in tech_data:
                    signal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(bank['signal'], '⚪')
                    print(f"   {bank['symbol']}: {signal_emoji} Technical={bank['technical_score']:.1f}")
            else:
                print("❌ No technical data retrieved")
                return False
            
            # Test 2: Live technical analysis calculation
            print("\n2. Testing Live Technical Analysis:")
            live_analysis = self.tech_engine.analyze_all_banks()
            
            if live_analysis:
                print(f"✅ Generated live analysis for {len(live_analysis)} banks")
                for analysis in live_analysis:
                    signal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}[analysis['overall_signal']]
                    print(f"   {analysis['symbol']}: {signal_emoji} Score={analysis['technical_score']:.1f}, RSI={analysis['rsi']:.1f}")
            else:
                print("❌ No live analysis generated")
                return False
            
            # Test 3: Technical indicators calculation
            print("\n3. Testing Individual Technical Indicators:")
            test_symbol = "CBA.AX"
            indicators = self.get_technical_indicators(test_symbol)
            
            if indicators:
                print(f"✅ Technical indicators for {test_symbol}:")
                print(f"   RSI: {indicators['rsi']:.1f}")
                print(f"   MACD Histogram: {indicators['macd_histogram']:.4f}")
                print(f"   Price vs SMA20: {indicators['price_vs_sma20']:.2f}%")
                print(f"   Signal Strength: {indicators['signal_strength']:.1f}")
            else:
                print(f"❌ No indicators calculated for {test_symbol}")
                return False
            
            # Test 4: Technical analysis summary
            print("\n4. Testing Technical Analysis Summary:")
            summary = self.get_technical_summary()
            
            if summary:
                print(f"✅ Technical summary generated:")
                print(f"   Average Technical Score: {summary['avg_technical_score']:.1f}")
                print(f"   Signal Distribution: {summary['signal_distribution']}")
                print(f"   Market Condition: {summary['market_condition']}")
            else:
                print("❌ No technical summary generated")
                return False
            
            print("\n✅ ALL TECHNICAL ANALYSIS COMPONENT TESTS PASSED")
            return True
            
        except Exception as e:
            print(f"\n❌ TECHNICAL ANALYSIS COMPONENT TEST FAILED: {e}")
            return False
    
    def get_current_technical_data(self) -> List[Dict]:
        """
        Get current technical data from database for all banks
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get latest technical data for each bank
            cursor = conn.execute("""
                SELECT 
                    s1.symbol,
                    s1.timestamp,
                    s1.technical_score,
                    s1.event_score,
                    s1.reddit_sentiment,
                    s1.sentiment_score,
                    CASE 
                        WHEN s1.technical_score >= 65 THEN 'BUY'
                        WHEN s1.technical_score <= 35 THEN 'SELL'
                        ELSE 'HOLD'
                    END as signal
                FROM sentiment_features s1
                INNER JOIN (
                    SELECT symbol, MAX(timestamp) as max_timestamp
                    FROM sentiment_features
                    GROUP BY symbol
                ) s2 ON s1.symbol = s2.symbol AND s1.timestamp = s2.max_timestamp
                ORDER BY s1.symbol
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            data = []
            for row in results:
                data.append({
                    'symbol': row['symbol'],
                    'timestamp': row['timestamp'],
                    'technical_score': float(row['technical_score'] or 0),
                    'event_score': float(row['event_score'] or 0),
                    'reddit_sentiment': float(row['reddit_sentiment'] or 0),
                    'sentiment_score': float(row['sentiment_score'] or 0),
                    'signal': row['signal']
                })
            
            return data
            
        except Exception as e:
            print(f"Error getting current technical data: {e}")
            return []
    
    def get_technical_indicators(self, symbol: str) -> Dict:
        """
        Get detailed technical indicators for a specific symbol
        """
        try:
            # Get live technical analysis
            analysis = self.tech_engine.calculate_technical_score(symbol)
            
            if analysis['data_quality'] != 'GOOD':
                return {}
            
            # Calculate additional indicators
            current_price = analysis['price_action']['current_price']
            sma_20 = analysis['moving_averages'].get('sma_20', current_price)
            
            price_vs_sma20 = ((current_price - sma_20) / sma_20) * 100 if sma_20 > 0 else 0
            
            return {
                'symbol': symbol,
                'rsi': analysis['rsi'],
                'macd_histogram': analysis['macd']['histogram'],
                'price_vs_sma20': price_vs_sma20,
                'signal_strength': analysis['technical_score'],
                'current_price': current_price,
                'moving_averages': analysis['moving_averages'],
                'overall_signal': analysis['overall_signal'],
                'confidence': analysis['confidence']
            }
            
        except Exception as e:
            print(f"Error getting technical indicators for {symbol}: {e}")
            return {}
    
    def get_technical_summary(self) -> Dict:
        """
        Get overall technical analysis summary for the market
        """
        try:
            # Get current technical data
            current_data = self.get_current_technical_data()
            
            if not current_data:
                return {}
            
            # Calculate summary statistics
            technical_scores = [bank['technical_score'] for bank in current_data]
            avg_technical_score = sum(technical_scores) / len(technical_scores)
            
            # Signal distribution
            signals = [bank['signal'] for bank in current_data]
            signal_distribution = {
                'BUY': signals.count('BUY'),
                'SELL': signals.count('SELL'),
                'HOLD': signals.count('HOLD')
            }
            
            # Determine market condition
            if avg_technical_score >= 60:
                market_condition = "BULLISH"
            elif avg_technical_score <= 40:
                market_condition = "BEARISH"
            else:
                market_condition = "NEUTRAL"
            
            # Calculate technical strength levels
            strength_levels = {
                'strong_buy': len([s for s in technical_scores if s >= 70]),
                'buy': len([s for s in technical_scores if 60 <= s < 70]),
                'hold': len([s for s in technical_scores if 40 < s < 60]),
                'sell': len([s for s in technical_scores if 30 < s <= 40]),
                'strong_sell': len([s for s in technical_scores if s <= 30])
            }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_banks': len(current_data),
                'avg_technical_score': avg_technical_score,
                'signal_distribution': signal_distribution,
                'market_condition': market_condition,
                'strength_levels': strength_levels,
                'bank_details': current_data
            }
            
        except Exception as e:
            print(f"Error generating technical summary: {e}")
            return {}
    
    def update_technical_scores(self) -> bool:
        """
        Update database with fresh technical analysis
        """
        try:
            return self.tech_engine.update_database_technical_scores()
        except Exception as e:
            print(f"Error updating technical scores: {e}")
            return False

def test_dashboard_technical_integration():
    """
    Test the enhanced technical analysis integration with dashboard
    """
    print("🎯 DASHBOARD TECHNICAL ANALYSIS INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Initialize dashboard technical analysis
        dash_tech = DashboardTechnicalAnalysis()
        
        # Run isolated technical analysis tests
        if not dash_tech.test_technical_analysis_isolated():
            return False
        
        # Test integration features
        print("\n🔗 Testing Dashboard Integration Features:")
        
        # Test updating technical scores
        print("\n5. Testing Technical Score Updates:")
        update_success = dash_tech.update_technical_scores()
        
        if update_success:
            print("✅ Technical scores updated successfully")
        else:
            print("❌ Technical score update failed")
            return False
        
        # Test enhanced dashboard display
        print("\n6. Testing Enhanced Dashboard Display:")
        summary = dash_tech.get_technical_summary()
        
        if summary:
            print(f"✅ Enhanced dashboard data ready:")
            print(f"   Market Condition: {summary['market_condition']}")
            print(f"   Average Score: {summary['avg_technical_score']:.1f}")
            print(f"   Signal Distribution: {summary['signal_distribution']}")
            
            # Show strength breakdown
            strength = summary['strength_levels']
            print(f"   Strength Levels:")
            print(f"     Strong Buy: {strength['strong_buy']}")
            print(f"     Buy: {strength['buy']}")
            print(f"     Hold: {strength['hold']}")
            print(f"     Sell: {strength['sell']}")
            print(f"     Strong Sell: {strength['strong_sell']}")
        else:
            print("❌ Enhanced dashboard data generation failed")
            return False
        
        print("\n✅ ALL DASHBOARD TECHNICAL INTEGRATION TESTS PASSED")
        print("🎉 Technical analysis is now fully operational!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ DASHBOARD TECHNICAL INTEGRATION TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    # Run comprehensive technical analysis tests
    success = test_dashboard_technical_integration()
    exit(0 if success else 1)
