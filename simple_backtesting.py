"""
Simplified Backtesting Engine  
Works with available sentiment_scores data for strategy validation
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyType(Enum):
    SENTIMENT_ONLY = "sentiment_only"
    TECHNICAL_ONLY = "technical_only"
    COMBINED = "combined"
    HIGH_CONFIDENCE = "high_confidence"

@dataclass
class SimpleBacktestResult:
    """Simplified backtest results"""
    strategy_name: str
    total_signals: int
    buy_signals: int
    sell_signals: int
    avg_confidence: float
    sentiment_stats: Dict
    technical_stats: Dict
    signal_distribution: Dict

class SimpleBacktestingEngine:
    """
    Simplified backtesting engine that works with available sentiment data
    """
    
    def __init__(self, database_path: str = "morning_analysis.db"):
        self.database_path = database_path
        
        # Strategy parameters
        self.strategies = {
            'sentiment_only': {
                'buy_threshold': 0.1,
                'sell_threshold': -0.1,
                'confidence_filter': 0.6
            },
            'technical_only': {
                'buy_threshold': 0.1,
                'sell_threshold': -0.1,
                'confidence_filter': 0.6
            },
            'combined': {
                'sentiment_weight': 0.6,
                'technical_weight': 0.4,
                'buy_threshold': 0.1,
                'sell_threshold': -0.1,
                'confidence_filter': 0.7
            },
            'high_confidence': {
                'buy_threshold': 0.05,
                'sell_threshold': -0.05,
                'confidence_filter': 0.85
            }
        }
    
    def load_historical_data(self) -> pd.DataFrame:
        """Load available sentiment data"""
        try:
            conn = sqlite3.connect(self.database_path)
            df = pd.read_sql_query("SELECT * FROM sentiment_scores ORDER BY timestamp ASC", conn)
            conn.close()
            
            if df.empty:
                logger.warning("No historical data found")
                return pd.DataFrame()
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return pd.DataFrame()
    
    def generate_signals(self, data: pd.DataFrame, strategy: StrategyType) -> pd.DataFrame:
        """Generate trading signals based on strategy"""
        df = data.copy()
        strategy_params = self.strategies[strategy.value]
        
        if strategy == StrategyType.SENTIMENT_ONLY:
            # Use only sentiment for signals
            df['signal'] = 'HOLD'
            df.loc[df['sentiment_score'] > strategy_params['buy_threshold'], 'signal'] = 'BUY'
            df.loc[df['sentiment_score'] < strategy_params['sell_threshold'], 'signal'] = 'SELL'
            
            # Apply confidence filter
            df.loc[df['confidence'] < strategy_params['confidence_filter'], 'signal'] = 'HOLD'
            
        elif strategy == StrategyType.TECHNICAL_ONLY:
            # Use only technical for signals
            df['signal'] = 'HOLD'
            df.loc[df['technical_score'] > strategy_params['buy_threshold'], 'signal'] = 'BUY'
            df.loc[df['technical_score'] < strategy_params['sell_threshold'], 'signal'] = 'SELL'
            
            # Apply confidence filter
            df.loc[df['confidence'] < strategy_params['confidence_filter'], 'signal'] = 'HOLD'
            
        elif strategy == StrategyType.COMBINED:
            # Combine sentiment and technical
            sentiment_weight = strategy_params['sentiment_weight']
            technical_weight = strategy_params['technical_weight']
            
            df['combined_score'] = (sentiment_weight * df['sentiment_score'] + 
                                   technical_weight * df['technical_score'])
            
            df['signal'] = 'HOLD'
            df.loc[df['combined_score'] > strategy_params['buy_threshold'], 'signal'] = 'BUY'
            df.loc[df['combined_score'] < strategy_params['sell_threshold'], 'signal'] = 'SELL'
            
            # Apply confidence filter
            df.loc[df['confidence'] < strategy_params['confidence_filter'], 'signal'] = 'HOLD'
            
        elif strategy == StrategyType.HIGH_CONFIDENCE:
            # High confidence strategy - lower thresholds but higher confidence requirement
            df['signal'] = 'HOLD'
            df.loc[df['sentiment_score'] > strategy_params['buy_threshold'], 'signal'] = 'BUY'
            df.loc[df['sentiment_score'] < strategy_params['sell_threshold'], 'signal'] = 'SELL'
            
            # Strict confidence filter
            df.loc[df['confidence'] < strategy_params['confidence_filter'], 'signal'] = 'HOLD'
        
        return df
    
    def analyze_signals(self, data_with_signals: pd.DataFrame, strategy_name: str) -> SimpleBacktestResult:
        """Analyze the generated signals"""
        try:
            # Count signals
            signal_counts = data_with_signals['signal'].value_counts()
            total_signals = len(data_with_signals[data_with_signals['signal'] != 'HOLD'])
            buy_signals = signal_counts.get('BUY', 0)
            sell_signals = signal_counts.get('SELL', 0)
            
            # Calculate statistics
            if total_signals > 0:
                trading_signals = data_with_signals[data_with_signals['signal'] != 'HOLD']
                avg_confidence = trading_signals['confidence'].mean()
                
                # Sentiment statistics for trading signals
                sentiment_stats = {
                    'mean': trading_signals['sentiment_score'].mean(),
                    'std': trading_signals['sentiment_score'].std(),
                    'min': trading_signals['sentiment_score'].min(),
                    'max': trading_signals['sentiment_score'].max()
                }
                
                # Technical statistics for trading signals
                technical_stats = {
                    'mean': trading_signals['technical_score'].mean(),
                    'std': trading_signals['technical_score'].std(),
                    'min': trading_signals['technical_score'].min(),
                    'max': trading_signals['technical_score'].max()
                }
            else:
                avg_confidence = 0.0
                sentiment_stats = {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
                technical_stats = {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
            
            # Signal distribution by symbol
            signal_distribution = {}
            for symbol in data_with_signals['symbol'].unique():
                symbol_data = data_with_signals[data_with_signals['symbol'] == symbol]
                symbol_signals = symbol_data['signal'].value_counts()
                signal_distribution[symbol] = {
                    'BUY': symbol_signals.get('BUY', 0),
                    'SELL': symbol_signals.get('SELL', 0),
                    'HOLD': symbol_signals.get('HOLD', 0),
                    'total': len(symbol_data)
                }
            
            return SimpleBacktestResult(
                strategy_name=strategy_name,
                total_signals=total_signals,
                buy_signals=buy_signals,
                sell_signals=sell_signals,
                avg_confidence=avg_confidence,
                sentiment_stats=sentiment_stats,
                technical_stats=technical_stats,
                signal_distribution=signal_distribution
            )
            
        except Exception as e:
            logger.error(f"Error analyzing signals: {e}")
            return SimpleBacktestResult(
                strategy_name=strategy_name,
                total_signals=0,
                buy_signals=0,
                sell_signals=0,
                avg_confidence=0.0,
                sentiment_stats={},
                technical_stats={},
                signal_distribution={}
            )
    
    def run_backtest(self, strategy: StrategyType) -> SimpleBacktestResult:
        """Run backtest for a single strategy"""
        try:
            # Load data
            data = self.load_historical_data()
            
            if data.empty:
                logger.warning("No data available for backtesting")
                return SimpleBacktestResult(
                    strategy_name=strategy.value,
                    total_signals=0,
                    buy_signals=0,
                    sell_signals=0,
                    avg_confidence=0.0,
                    sentiment_stats={},
                    technical_stats={},
                    signal_distribution={}
                )
            
            # Generate signals
            data_with_signals = self.generate_signals(data, strategy)
            
            # Analyze results
            results = self.analyze_signals(data_with_signals, strategy.value)
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            raise
    
    def compare_strategies(self, strategies: List[StrategyType]) -> Dict:
        """Compare multiple strategies"""
        results = {}
        comparison_data = []
        
        for strategy in strategies:
            logger.info(f"Running analysis for {strategy.value}")
            result = self.run_backtest(strategy)
            results[strategy.value] = result
            
            # Add to comparison
            comparison_data.append({
                'strategy': strategy.value,
                'total_signals': result.total_signals,
                'buy_signals': result.buy_signals,
                'sell_signals': result.sell_signals,
                'buy_rate': result.buy_signals / result.total_signals if result.total_signals > 0 else 0,
                'sell_rate': result.sell_signals / result.total_signals if result.total_signals > 0 else 0,
                'avg_confidence': result.avg_confidence,
                'avg_sentiment': result.sentiment_stats.get('mean', 0),
                'avg_technical': result.technical_stats.get('mean', 0)
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Find most active strategy
        best_strategy = None
        if len(comparison_df) > 0 and comparison_df['total_signals'].max() > 0:
            best_strategy = comparison_df.loc[comparison_df['total_signals'].idxmax(), 'strategy']
        
        return {
            'individual_results': results,
            'comparison_table': comparison_df,
            'most_active_strategy': best_strategy
        }
    
    def get_strategy_insights(self, results: Dict) -> Dict:
        """Generate insights from strategy comparison"""
        insights = {
            'total_data_points': 0,
            'most_active_strategy': results.get('most_active_strategy', 'None'),
            'strategy_effectiveness': {},
            'recommendations': []
        }
        
        try:
            comparison_df = results['comparison_table']
            
            if comparison_df.empty:
                insights['recommendations'].append("No data available for analysis")
                return insights
            
            # Total data points
            individual_results = results['individual_results']
            if individual_results:
                first_result = list(individual_results.values())[0]
                insights['total_data_points'] = sum(
                    stats['total'] for stats in first_result.signal_distribution.values()
                )
            
            # Strategy effectiveness
            for _, row in comparison_df.iterrows():
                strategy = row['strategy']
                effectiveness = {
                    'signal_rate': (row['buy_signals'] + row['sell_signals']) / max(insights['total_data_points'], 1),
                    'confidence_level': row['avg_confidence'],
                    'sentiment_bias': row['avg_sentiment'],
                    'technical_bias': row['avg_technical']
                }
                insights['strategy_effectiveness'][strategy] = effectiveness
            
            # Generate recommendations
            if comparison_df['total_signals'].max() == 0:
                insights['recommendations'].append("No trading signals generated - consider lowering thresholds")
            else:
                # Most active strategy
                most_active = comparison_df.loc[comparison_df['total_signals'].idxmax()]
                insights['recommendations'].append(
                    f"Most active strategy: {most_active['strategy']} ({most_active['total_signals']} signals)"
                )
                
                # Highest confidence strategy
                highest_conf = comparison_df.loc[comparison_df['avg_confidence'].idxmax()]
                insights['recommendations'].append(
                    f"Highest confidence: {highest_conf['strategy']} ({highest_conf['avg_confidence']:.1%})"
                )
                
                # Balance recommendations
                buy_heavy = comparison_df[comparison_df['buy_rate'] > 0.7]
                if len(buy_heavy) > 0:
                    insights['recommendations'].append(
                        f"Buy-heavy strategies: {', '.join(buy_heavy['strategy'].tolist())}"
                    )
                
                sell_heavy = comparison_df[comparison_df['sell_rate'] > 0.7]
                if len(sell_heavy) > 0:
                    insights['recommendations'].append(
                        f"Sell-heavy strategies: {', '.join(sell_heavy['strategy'].tolist())}"
                    )
        
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            insights['recommendations'].append(f"Error generating insights: {e}")
        
        return insights

def test_simple_backtesting():
    """Test the simplified backtesting engine"""
    print("🎛️ Testing Simplified Backtesting Engine")
    print("=" * 60)
    
    engine = SimpleBacktestingEngine()
    
    # Test all strategies
    strategies = [
        StrategyType.SENTIMENT_ONLY,
        StrategyType.TECHNICAL_ONLY,
        StrategyType.COMBINED,
        StrategyType.HIGH_CONFIDENCE
    ]
    
    try:
        # Run strategy comparison
        comparison_results = engine.compare_strategies(strategies)
        
        print("📊 Strategy Analysis Results:")
        print("=" * 40)
        
        comparison_df = comparison_results['comparison_table']
        if not comparison_df.empty:
            for _, row in comparison_df.iterrows():
                print(f"\n🎯 {row['strategy'].upper().replace('_', ' ')}")
                print(f"  Total Signals: {row['total_signals']}")
                print(f"  Buy Signals: {row['buy_signals']} ({row['buy_rate']:.1%})")
                print(f"  Sell Signals: {row['sell_signals']} ({row['sell_rate']:.1%})")
                print(f"  Avg Confidence: {row['avg_confidence']:.1%}")
                print(f"  Avg Sentiment: {row['avg_sentiment']:+.3f}")
                print(f"  Avg Technical: {row['avg_technical']:+.3f}")
        
        # Get insights
        insights = engine.get_strategy_insights(comparison_results)
        
        print(f"\n💡 Strategy Insights:")
        print(f"Total Data Points: {insights['total_data_points']}")
        print(f"Most Active Strategy: {insights['most_active_strategy']}")
        
        print(f"\nRecommendations:")
        for recommendation in insights['recommendations']:
            print(f"  • {recommendation}")
        
        # Show individual strategy details
        print(f"\n📋 Signal Distribution by Stock:")
        for strategy_name, result in comparison_results['individual_results'].items():
            if result.total_signals > 0:
                print(f"\n  {strategy_name.upper().replace('_', ' ')}:")
                for symbol, dist in result.signal_distribution.items():
                    total = dist['total']
                    buy_pct = dist['BUY'] / total * 100 if total > 0 else 0
                    sell_pct = dist['SELL'] / total * 100 if total > 0 else 0
                    print(f"    {symbol}: {dist['BUY']}B/{dist['SELL']}S/{dist['HOLD']}H "
                          f"(Buy: {buy_pct:.0f}%, Sell: {sell_pct:.0f}%)")
        
    except Exception as e:
        print(f"❌ Error in backtesting: {e}")
    
    print("\n✅ Simplified Backtesting Test Complete!")

if __name__ == "__main__":
    test_simple_backtesting()
