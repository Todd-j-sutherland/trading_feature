"""
Strategy Backtesting Engine
Comprehensive backtesting framework for trading strategies with walk-forward analysis
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyType(Enum):
    SENTIMENT_ONLY = "sentiment_only"
    TECHNICAL_ONLY = "technical_only"
    COMBINED = "combined"
    ML_ENHANCED = "ml_enhanced"
    QUALITY_WEIGHTED = "quality_weighted"

@dataclass
class Trade:
    """
    Individual trade record
    """
    symbol: str
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    signal: str  # BUY/SELL
    confidence: float
    return_pct: float
    return_abs: float
    holding_period: int  # days
    strategy: str

@dataclass
class BacktestResults:
    """
    Comprehensive backtesting results
    """
    strategy_name: str
    start_date: datetime
    end_date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    avg_return_per_trade: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_consecutive_losses: int
    avg_holding_period: float
    trades: List[Trade]
    equity_curve: pd.DataFrame
    monthly_returns: pd.DataFrame

class BacktestingEngine:
    """
    Advanced backtesting engine for trading strategies
    """
    
    def __init__(self, database_path: str = "morning_analysis.db"):
        self.database_path = database_path
        self.risk_free_rate = 0.02  # 2% annual risk-free rate (RBA cash rate)
        
        # Strategy parameters
        self.strategies = {
            'sentiment_only': {
                'buy_threshold': 0.1,
                'sell_threshold': -0.1,
                'confidence_filter': 0.5
            },
            'technical_only': {
                'buy_threshold': 0.1,
                'sell_threshold': -0.1,
                'confidence_filter': 0.5
            },
            'combined': {
                'sentiment_weight': 0.6,
                'technical_weight': 0.4,
                'buy_threshold': 0.1,
                'sell_threshold': -0.1,
                'confidence_filter': 0.6
            },
            'ml_enhanced': {
                'confidence_filter': 0.7,
                'use_ml_confidence': True
            },
            'quality_weighted': {
                'confidence_filter': 0.65,
                'use_quality_weighting': True
            }
        }
        
        # Position sizing rules
        self.position_sizing = {
            'fixed': 10000,  # $10,000 per trade
            'max_positions': 4,  # Max 4 simultaneous positions
            'stop_loss': 0.05,  # 5% stop loss
            'take_profit': 0.15  # 15% take profit
        }
    
    def load_historical_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Load historical features and outcomes for backtesting
        """
        try:
            conn = sqlite3.connect(self.database_path)
            
            query = """
            SELECT 
                ef.symbol,
                ef.timestamp,
                ef.sentiment_score,
                ef.technical_score,
                ef.confidence,
                ef.news_count,
                ef.prediction_signal,
                eo.actual_price_change,
                eo.entry_price,
                eo.exit_price,
                eo.volume_change_percent,
                eo.exit_timestamp
            FROM enhanced_features ef
            LEFT JOIN enhanced_outcomes eo ON ef.symbol = eo.symbol 
                AND date(ef.timestamp) = date(eo.timestamp)
            WHERE ef.timestamp BETWEEN ? AND ?
                AND eo.actual_price_change IS NOT NULL
                AND eo.entry_price IS NOT NULL
                AND eo.exit_price IS NOT NULL
            ORDER BY ef.timestamp ASC
            """
            
            df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            conn.close()
            
            if df.empty:
                logger.warning("No historical data found for the specified period")
                return pd.DataFrame()
            
            # Convert timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['exit_timestamp'] = pd.to_datetime(df['exit_timestamp'])
            
            # Calculate holding period
            df['holding_period'] = (df['exit_timestamp'] - df['timestamp']).dt.days
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return pd.DataFrame()
    
    def generate_signals(self, data: pd.DataFrame, strategy: StrategyType) -> pd.DataFrame:
        """
        Generate trading signals based on strategy type
        """
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
            
        elif strategy == StrategyType.ML_ENHANCED:
            # Use ML predictions with enhanced confidence filtering
            df['signal'] = df['prediction_signal']
            
            # Stricter confidence filter for ML
            df.loc[df['confidence'] < strategy_params['confidence_filter'], 'signal'] = 'HOLD'
            
        elif strategy == StrategyType.QUALITY_WEIGHTED:
            # Use quality-weighted approach (simplified for backtesting)
            # Weight by news count as proxy for information quality
            df['quality_weight'] = np.clip(df['news_count'] / df['news_count'].mean(), 0.5, 2.0)
            df['quality_score'] = (df['sentiment_score'] * df['quality_weight'] + 
                                  df['technical_score']) / 2
            
            df['signal'] = 'HOLD'
            df.loc[df['quality_score'] > 0.1, 'signal'] = 'BUY'
            df.loc[df['quality_score'] < -0.1, 'signal'] = 'SELL'
            
            # Apply confidence filter
            df.loc[df['confidence'] < strategy_params['confidence_filter'], 'signal'] = 'HOLD'
        
        return df
    
    def simulate_trades(self, data: pd.DataFrame) -> List[Trade]:
        """
        Simulate actual trades based on signals
        """
        trades = []
        
        for _, row in data.iterrows():
            if row['signal'] in ['BUY', 'SELL']:
                # Calculate return based on actual price data
                if row['entry_price'] > 0 and row['exit_price'] > 0:
                    return_pct = (row['exit_price'] - row['entry_price']) / row['entry_price']
                    
                    # For SELL signals, invert the return (short position)
                    if row['signal'] == 'SELL':
                        return_pct = -return_pct
                    
                    return_abs = return_pct * self.position_sizing['fixed']
                    
                    trade = Trade(
                        symbol=row['symbol'],
                        entry_date=row['timestamp'],
                        exit_date=row['exit_timestamp'],
                        entry_price=row['entry_price'],
                        exit_price=row['exit_price'],
                        signal=row['signal'],
                        confidence=row['confidence'],
                        return_pct=return_pct,
                        return_abs=return_abs,
                        holding_period=row['holding_period'],
                        strategy=""  # Will be set by caller
                    )
                    
                    trades.append(trade)
        
        return trades
    
    def calculate_performance_metrics(self, trades: List[Trade]) -> Dict:
        """
        Calculate comprehensive performance metrics
        """
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_return': 0.0,
                'avg_return_per_trade': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0
            }
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.return_pct > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Return metrics
        returns = [t.return_pct for t in trades]
        total_return = sum(returns)
        avg_return_per_trade = total_return / total_trades if total_trades > 0 else 0
        
        # Risk metrics
        return_std = np.std(returns) if len(returns) > 1 else 0
        
        # Drawdown calculation
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = cumulative_returns - running_max
        max_drawdown = abs(min(drawdowns)) if len(drawdowns) > 0 else 0
        
        # Risk-adjusted metrics
        if return_std > 0:
            sharpe_ratio = (avg_return_per_trade - self.risk_free_rate/252) / return_std * np.sqrt(252)
            
            # Sortino ratio (downside deviation)
            negative_returns = [r for r in returns if r < 0]
            downside_std = np.std(negative_returns) if len(negative_returns) > 1 else return_std
            sortino_ratio = (avg_return_per_trade - self.risk_free_rate/252) / downside_std * np.sqrt(252)
            
            # Calmar ratio
            calmar_ratio = total_return / max_drawdown if max_drawdown > 0 else 0
        else:
            sharpe_ratio = 0
            sortino_ratio = 0
            calmar_ratio = 0
        
        # Consecutive losses
        consecutive_losses = 0
        max_consecutive_losses = 0
        for trade in trades:
            if trade.return_pct < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        # Average holding period
        avg_holding_period = np.mean([t.holding_period for t in trades])
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_return_per_trade': avg_return_per_trade,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_consecutive_losses': max_consecutive_losses,
            'avg_holding_period': avg_holding_period,
            'return_std': return_std
        }
    
    def run_backtest(self, strategy: StrategyType, 
                    start_date: str, 
                    end_date: str) -> BacktestResults:
        """
        Run comprehensive backtest for a strategy
        """
        try:
            # Load historical data
            data = self.load_historical_data(start_date, end_date)
            
            if data.empty:
                logger.warning("No data available for backtesting")
                return BacktestResults(
                    strategy_name=strategy.value,
                    start_date=datetime.strptime(start_date, '%Y-%m-%d'),
                    end_date=datetime.strptime(end_date, '%Y-%m-%d'),
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    total_return=0.0,
                    avg_return_per_trade=0.0,
                    max_drawdown=0.0,
                    sharpe_ratio=0.0,
                    sortino_ratio=0.0,
                    calmar_ratio=0.0,
                    max_consecutive_losses=0,
                    avg_holding_period=0.0,
                    trades=[],
                    equity_curve=pd.DataFrame(),
                    monthly_returns=pd.DataFrame()
                )
            
            # Generate signals
            data_with_signals = self.generate_signals(data, strategy)
            
            # Simulate trades
            trades = self.simulate_trades(data_with_signals)
            
            # Set strategy name for trades
            for trade in trades:
                trade.strategy = strategy.value
            
            # Calculate performance metrics
            metrics = self.calculate_performance_metrics(trades)
            
            # Create equity curve
            if trades:
                trade_dates = [t.entry_date for t in trades]
                trade_returns = [t.return_pct for t in trades]
                
                equity_curve = pd.DataFrame({
                    'date': trade_dates,
                    'return': trade_returns
                })
                equity_curve['cumulative_return'] = equity_curve['return'].cumsum()
                equity_curve['equity'] = self.position_sizing['fixed'] * (1 + equity_curve['cumulative_return'])
            else:
                equity_curve = pd.DataFrame()
            
            # Create monthly returns
            if trades:
                monthly_data = pd.DataFrame([
                    {'date': t.entry_date, 'return': t.return_pct} for t in trades
                ])
                monthly_data['date'] = pd.to_datetime(monthly_data['date'])
                monthly_data.set_index('date', inplace=True)
                monthly_returns = monthly_data.resample('M')['return'].sum()
                monthly_returns = monthly_returns.to_frame()
            else:
                monthly_returns = pd.DataFrame()
            
            return BacktestResults(
                strategy_name=strategy.value,
                start_date=datetime.strptime(start_date, '%Y-%m-%d'),
                end_date=datetime.strptime(end_date, '%Y-%m-%d'),
                total_trades=metrics['total_trades'],
                winning_trades=metrics['winning_trades'],
                losing_trades=metrics['losing_trades'],
                win_rate=metrics['win_rate'],
                total_return=metrics['total_return'],
                avg_return_per_trade=metrics['avg_return_per_trade'],
                max_drawdown=metrics['max_drawdown'],
                sharpe_ratio=metrics['sharpe_ratio'],
                sortino_ratio=metrics['sortino_ratio'],
                calmar_ratio=metrics['calmar_ratio'],
                max_consecutive_losses=metrics['max_consecutive_losses'],
                avg_holding_period=metrics['avg_holding_period'],
                trades=trades,
                equity_curve=equity_curve,
                monthly_returns=monthly_returns
            )
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            raise
    
    def compare_strategies(self, strategies: List[StrategyType],
                          start_date: str, 
                          end_date: str) -> Dict:
        """
        Compare multiple strategies
        """
        results = {}
        
        for strategy in strategies:
            logger.info(f"Running backtest for {strategy.value}")
            results[strategy.value] = self.run_backtest(strategy, start_date, end_date)
        
        # Create comparison summary
        comparison = []
        for strategy_name, result in results.items():
            comparison.append({
                'strategy': strategy_name,
                'total_trades': result.total_trades,
                'win_rate': result.win_rate,
                'total_return': result.total_return,
                'avg_return_per_trade': result.avg_return_per_trade,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'sortino_ratio': result.sortino_ratio,
                'calmar_ratio': result.calmar_ratio
            })
        
        comparison_df = pd.DataFrame(comparison)
        
        return {
            'individual_results': results,
            'comparison_table': comparison_df,
            'best_strategy': comparison_df.loc[comparison_df['sharpe_ratio'].idxmax(), 'strategy'] if len(comparison_df) > 0 else None
        }

def test_backtesting_engine():
    """
    Test the backtesting engine
    """
    print("🎛️ Testing Backtesting Engine")
    print("=" * 50)
    
    engine = BacktestingEngine()
    
    # Test date range (last 30 days)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"Testing period: {start_date} to {end_date}")
    
    # Test strategies
    strategies = [
        StrategyType.SENTIMENT_ONLY,
        StrategyType.TECHNICAL_ONLY,
        StrategyType.COMBINED,
        StrategyType.ML_ENHANCED
    ]
    
    try:
        # Run strategy comparison
        comparison_results = engine.compare_strategies(strategies, start_date, end_date)
        
        print("\n📊 Strategy Comparison Results:")
        print("=" * 70)
        
        comparison_df = comparison_results['comparison_table']
        if not comparison_df.empty:
            for _, row in comparison_df.iterrows():
                print(f"\n🎯 {row['strategy'].upper()}")
                print(f"  Trades: {row['total_trades']}")
                print(f"  Win Rate: {row['win_rate']:.1%}")
                print(f"  Total Return: {row['total_return']:+.1%}")
                print(f"  Avg Return/Trade: {row['avg_return_per_trade']:+.2%}")
                print(f"  Max Drawdown: {row['max_drawdown']:.2%}")
                print(f"  Sharpe Ratio: {row['sharpe_ratio']:.2f}")
                print(f"  Sortino Ratio: {row['sortino_ratio']:.2f}")
        
        best_strategy = comparison_results['best_strategy']
        if best_strategy:
            print(f"\n🏆 Best Strategy (by Sharpe Ratio): {best_strategy.upper()}")
        
        # Show individual strategy details
        for strategy_name, result in comparison_results['individual_results'].items():
            if result.total_trades > 0:
                print(f"\n📋 {strategy_name.upper()} - Detailed Results:")
                print(f"  Sample Trades:")
                for i, trade in enumerate(result.trades[:3]):  # Show first 3 trades
                    print(f"    {i+1}. {trade.symbol} {trade.signal}: {trade.return_pct:+.2%} "
                          f"({trade.entry_date.strftime('%m-%d')} → {trade.exit_date.strftime('%m-%d')})")
        
    except Exception as e:
        print(f"❌ Error in backtesting: {e}")
        print("This might be due to insufficient historical data in the database.")
    
    print("\n✅ Backtesting Engine Test Complete!")

if __name__ == "__main__":
    test_backtesting_engine()
