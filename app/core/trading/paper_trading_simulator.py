#!/usr/bin/env python3
"""
Paper Trading Simulator - Internal API-free Trading System

A comprehensive paper trading system that:
1. Tracks positions in the database
2. Evaluates news + technical + ML data every 4 hours
3. Makes trading decisions and records metrics
4. Can run as a background process

This system replicates broker API functionality without external dependencies.
"""

import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import time
import schedule
import threading
import signal
import sys

# Import our existing components
from app.core.data.sql_manager import TradingDataManager
from app.core.sentiment.two_stage_analyzer import TwoStageAnalyzer
from app.core.ml.trading_scorer import MLTradingScorer
from app.core.analysis.economic import EconomicSentimentAnalyzer
from app.core.analysis.divergence import DivergenceDetector
from app.core.data.processors.news_processor import NewsTradingAnalyzer
from app.config.settings import Settings

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    entry_date: datetime
    position_type: str  # LONG or SHORT
    entry_price: float
    position_size: int
    ml_confidence: float
    sentiment_at_entry: float
    entry_analysis: Dict[str, Any]
    
    # Optional fields (set when position is closed)
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    profit_loss: Optional[float] = None
    return_percentage: Optional[float] = None

class PaperTradingSimulator:
    """
    Paper trading simulator that operates without external broker APIs.
    Uses internal price tracking and position management.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize the paper trading simulator.
        
        Args:
            initial_capital: Starting virtual capital in AUD
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.settings = Settings()
        self.data_manager = TradingDataManager()
        
        # Analysis components
        self.sentiment_analyzer = TwoStageAnalyzer()
        self.news_analyzer = NewsTradingAnalyzer()
        self.ml_scorer = MLTradingScorer()
        self.economic_analyzer = EconomicSentimentAnalyzer()
        self.divergence_detector = DivergenceDetector()
        
        # Trading state
        self.running = False
        self.positions: Dict[str, Position] = {}
        
        # Load existing positions from database
        self._load_open_positions()
        
        logger.info(f"Paper Trading Simulator initialized with ${initial_capital:,.2f} virtual capital")
    
    def _load_open_positions(self):
        """Load open positions from database"""
        try:
            with self.data_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT symbol, entry_date, position_type, entry_price, position_size,
                           ml_confidence, sentiment_at_entry
                    FROM positions 
                    WHERE exit_date IS NULL
                """)
                
                for row in cursor.fetchall():
                    position = Position(
                        symbol=row[0],
                        entry_date=datetime.fromisoformat(row[1]),
                        position_type=row[2],
                        entry_price=row[3],
                        position_size=row[4],
                        ml_confidence=row[5],
                        sentiment_at_entry=row[6],
                        entry_analysis={}  # Historical data not available
                    )
                    self.positions[row[0]] = position
                
                logger.info(f"Loaded {len(self.positions)} open positions from database")
                
        except Exception as e:
            logger.error(f"Error loading positions: {e}")
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.
        In a real system, this would query market data.
        For simulation, we'll use cached data or generate realistic prices.
        """
        try:
            # Try to get recent market data from cache
            with self.data_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT price FROM market_data_cache 
                    WHERE symbol = ? AND timestamp > datetime('now', '-1 hour')
                    ORDER BY timestamp DESC LIMIT 1
                """, (symbol,))
                
                result = cursor.fetchone()
                if result:
                    return float(result[0])
                
                # Fallback: Use historical average or reasonable estimate
                # This would be replaced with real market data in production
                price_estimates = {
                    'CBA.AX': 108.50,
                    'WBC.AX': 23.80,
                    'ANZ.AX': 29.40,
                    'NAB.AX': 35.60,
                    'MQG.AX': 185.20,
                    'QBE.AX': 14.20,
                    'SUN.AX': 10.80
                }
                
                base_price = price_estimates.get(symbol, 50.0)
                
                # Add some realistic price movement based on sentiment
                try:
                    # Get latest sentiment to influence price
                    cursor.execute("""
                        SELECT sentiment_score FROM sentiment_history 
                        WHERE symbol = ? 
                        ORDER BY timestamp DESC LIMIT 1
                    """, (symbol,))
                    
                    sentiment_result = cursor.fetchone()
                    if sentiment_result:
                        sentiment = sentiment_result[0]
                        # Apply sentiment-based price adjustment (±5%)
                        price_adjustment = sentiment * 0.05
                        adjusted_price = base_price * (1 + price_adjustment)
                        return max(adjusted_price, base_price * 0.5)  # Don't go below 50% of base
                
                except Exception:
                    pass
                
                return base_price
                
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return 50.0  # Fallback price
    
    def calculate_position_size(self, symbol: str, ml_confidence: float, available_capital: float) -> int:
        """
        Calculate optimal position size based on ML confidence and risk management.
        
        Args:
            symbol: Stock symbol
            ml_confidence: ML confidence score (0-1)
            available_capital: Available capital for trading
            
        Returns:
            Number of shares to buy/sell
        """
        # Risk management: max position size based on confidence
        max_position_pct = min(0.2, ml_confidence * 0.3)  # Max 20% of capital, scaled by confidence
        max_position_value = available_capital * max_position_pct
        
        # Get current price
        current_price = self.get_current_price(symbol)
        
        # Calculate shares
        position_size = int(max_position_value / current_price)
        
        # Minimum position size
        min_shares = max(1, int(1000 / current_price))  # At least $1000 position
        
        return max(position_size, min_shares)
    
    def evaluate_trading_opportunity(self, symbol: str) -> Dict[str, Any]:
        """
        Comprehensive evaluation combining news, technical analysis, and ML.
        This is the core 4-hour evaluation process.
        
        Args:
            symbol: Stock symbol to evaluate
            
        Returns:
            Complete analysis including trading signal and metrics
        """
        logger.info(f"🔍 Evaluating trading opportunity for {symbol}")
        
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'news_analysis': {},
            'ml_analysis': {},
            'economic_context': {},
            'trading_signal': 'HOLD',
            'confidence': 0.0,
            'recommended_action': None
        }
        
        try:
            # 1. News and Sentiment Analysis
            logger.info(f"   📰 Analyzing news sentiment for {symbol}")
            news_result = self.news_analyzer.analyze_single_bank(symbol, detailed=True)
            
            if news_result and 'overall_sentiment' in news_result:
                analysis['news_analysis'] = {
                    'sentiment_score': news_result['overall_sentiment'],
                    'confidence': news_result.get('confidence', 0.5),
                    'news_count': news_result.get('news_count', 0),
                    'key_themes': news_result.get('key_themes', [])
                }
                logger.info(f"   ✅ News sentiment: {news_result['overall_sentiment']:+.3f}")
            else:
                logger.warning(f"   ⚠️ No news analysis available for {symbol}")
                analysis['news_analysis'] = {'sentiment_score': 0.0, 'confidence': 0.3}
            
            # 2. Economic Context
            logger.info(f"   🌍 Analyzing economic context")
            economic_result = self.economic_analyzer.analyze_economic_sentiment()
            analysis['economic_context'] = economic_result
            
            # 3. ML Analysis and Scoring
            logger.info(f"   🧠 Calculating ML trading score")
            
            # Prepare data for ML scorer
            bank_analyses = {symbol: news_result} if news_result else {}
            divergence_analysis = self.divergence_detector.analyze_sector_divergence(bank_analyses) if bank_analyses else {}
            
            ml_scores = self.ml_scorer.calculate_scores_for_all_banks(
                bank_analyses=bank_analyses,
                economic_analysis=economic_result,
                divergence_analysis=divergence_analysis
            )
            
            if symbol in ml_scores and 'error' not in ml_scores[symbol]:
                ml_analysis = ml_scores[symbol]
                analysis['ml_analysis'] = ml_analysis
                analysis['trading_signal'] = ml_analysis.get('trading_recommendation', 'HOLD')
                analysis['confidence'] = ml_analysis.get('overall_ml_score', 0) / 100.0
                
                logger.info(f"   ✅ ML Score: {ml_analysis.get('overall_ml_score', 0):.1f}/100")
                logger.info(f"   ✅ Recommendation: {ml_analysis.get('trading_recommendation', 'HOLD')}")
            else:
                logger.warning(f"   ⚠️ ML analysis failed for {symbol}")
                analysis['ml_analysis'] = {'error': 'ML analysis failed'}
                analysis['confidence'] = 0.2
            
            # 4. Final Trading Decision
            self._determine_final_action(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error evaluating {symbol}: {e}")
            analysis['error'] = str(e)
            return analysis
    
    def _determine_final_action(self, analysis: Dict[str, Any]) -> None:
        """
        Determine final trading action based on all analysis components.
        
        Args:
            analysis: Complete analysis dictionary (modified in place)
        """
        symbol = analysis['symbol']
        trading_signal = analysis['trading_signal']
        confidence = analysis['confidence']
        
        # Check if we already have a position
        has_position = symbol in self.positions
        
        # Trading logic based on signal and confidence
        if trading_signal in ['BUY', 'STRONG_BUY'] and confidence > 0.6:
            if not has_position:
                analysis['recommended_action'] = 'OPEN_LONG'
            else:
                analysis['recommended_action'] = 'HOLD_LONG'
                
        elif trading_signal in ['SELL', 'STRONG_SELL'] and confidence > 0.6:
            if has_position and self.positions[symbol].position_type == 'LONG':
                analysis['recommended_action'] = 'CLOSE_LONG'
            elif not has_position:
                analysis['recommended_action'] = 'OPEN_SHORT'
            else:
                analysis['recommended_action'] = 'HOLD_SHORT'
                
        elif has_position:
            # Check if we should close due to low confidence or changed conditions
            position = self.positions[symbol]
            hours_held = (datetime.now() - position.entry_date).total_seconds() / 3600
            
            # Close position if held for more than 24 hours with low confidence
            if hours_held > 24 and confidence < 0.4:
                analysis['recommended_action'] = f'CLOSE_{position.position_type}'
            else:
                analysis['recommended_action'] = f'HOLD_{position.position_type}'
        else:
            analysis['recommended_action'] = 'HOLD'
        
        logger.info(f"   🎯 Final action: {analysis['recommended_action']} (confidence: {confidence:.2f})")
    
    def execute_trading_action(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute the recommended trading action.
        
        Args:
            analysis: Complete analysis with recommended action
            
        Returns:
            Trade execution result or None if no action taken
        """
        symbol = analysis['symbol']
        action = analysis['recommended_action']
        confidence = analysis['confidence']
        
        if not action or action == 'HOLD':
            logger.info(f"   ⏸️ No action for {symbol}")
            return None
        
        logger.info(f"   🎯 Executing {action} for {symbol}")
        
        try:
            if action == 'OPEN_LONG':
                return self._open_position(symbol, 'LONG', analysis)
            elif action == 'OPEN_SHORT':
                return self._open_position(symbol, 'SHORT', analysis)
            elif action.startswith('CLOSE_'):
                return self._close_position(symbol, analysis)
            elif action.startswith('HOLD_'):
                logger.info(f"   ⏳ Holding position for {symbol}")
                return None
            else:
                logger.warning(f"   ⚠️ Unknown action: {action}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing {action} for {symbol}: {e}")
            return {'error': str(e)}
    
    def _open_position(self, symbol: str, position_type: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Open a new trading position.
        
        Args:
            symbol: Stock symbol
            position_type: LONG or SHORT
            analysis: Complete analysis data
            
        Returns:
            Trade execution result
        """
        current_price = self.get_current_price(symbol)
        confidence = analysis['confidence']
        
        # Calculate position size
        available_capital = self.current_capital * 0.8  # Keep 20% cash buffer
        position_size = self.calculate_position_size(symbol, confidence, available_capital)
        position_value = position_size * current_price
        
        # Check if we have enough capital
        if position_value > available_capital:
            logger.warning(f"   ❌ Insufficient capital for {symbol}: need ${position_value:,.2f}, have ${available_capital:,.2f}")
            return {'error': 'Insufficient capital'}
        
        # Create position
        position = Position(
            symbol=symbol,
            entry_date=datetime.now(),
            position_type=position_type,
            entry_price=current_price,
            position_size=position_size,
            ml_confidence=confidence,
            sentiment_at_entry=analysis['news_analysis'].get('sentiment_score', 0.0),
            entry_analysis=analysis
        )
        
        # Update capital
        self.current_capital -= position_value
        
        # Store position
        self.positions[symbol] = position
        
        # Save to database
        self._save_position_to_db(position)
        
        result = {
            'action': f'OPENED_{position_type}',
            'symbol': symbol,
            'entry_price': current_price,
            'position_size': position_size,
            'position_value': position_value,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"   ✅ Opened {position_type} position: {position_size} shares @ ${current_price:.2f}")
        logger.info(f"   💰 Position value: ${position_value:,.2f}, Remaining capital: ${self.current_capital:,.2f}")
        
        return result
    
    def _close_position(self, symbol: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Close an existing trading position.
        
        Args:
            symbol: Stock symbol
            analysis: Complete analysis data
            
        Returns:
            Trade execution result
        """
        if symbol not in self.positions:
            logger.warning(f"   ⚠️ No position to close for {symbol}")
            return {'error': 'No position to close'}
        
        position = self.positions[symbol]
        current_price = self.get_current_price(symbol)
        
        # Calculate P&L
        if position.position_type == 'LONG':
            profit_loss = (current_price - position.entry_price) * position.position_size
        else:  # SHORT
            profit_loss = (position.entry_price - current_price) * position.position_size
        
        return_percentage = (profit_loss / (position.entry_price * position.position_size)) * 100
        
        # Update capital
        position_value = position.position_size * current_price
        self.current_capital += position_value
        
        # Update position
        position.exit_date = datetime.now()
        position.exit_price = current_price
        position.exit_reason = f"Signal changed: {analysis['trading_signal']}"
        position.profit_loss = profit_loss
        position.return_percentage = return_percentage
        
        # Update database
        self._update_position_in_db(position)
        
        # Remove from active positions
        del self.positions[symbol]
        
        result = {
            'action': f'CLOSED_{position.position_type}',
            'symbol': symbol,
            'entry_price': position.entry_price,
            'exit_price': current_price,
            'position_size': position.position_size,
            'profit_loss': profit_loss,
            'return_percentage': return_percentage,
            'hold_duration_hours': (position.exit_date - position.entry_date).total_seconds() / 3600,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"   ✅ Closed {position.position_type} position: P&L ${profit_loss:+.2f} ({return_percentage:+.1f}%)")
        logger.info(f"   💰 Total capital: ${self.current_capital:,.2f}")
        
        return result
    
    def _save_position_to_db(self, position: Position):
        """Save position to database"""
        try:
            with self.data_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO positions 
                    (symbol, entry_date, position_type, entry_price, position_size, 
                     ml_confidence, sentiment_at_entry)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    position.symbol,
                    position.entry_date.isoformat(),
                    position.position_type,
                    position.entry_price,
                    position.position_size,
                    position.ml_confidence,
                    position.sentiment_at_entry
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving position to DB: {e}")
    
    def _update_position_in_db(self, position: Position):
        """Update closed position in database"""
        try:
            with self.data_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE positions 
                    SET exit_date = ?, exit_price = ?, exit_reason = ?, 
                        profit_loss = ?, return_percentage = ?
                    WHERE symbol = ? AND exit_date IS NULL
                """, (
                    position.exit_date.isoformat() if position.exit_date else None,
                    position.exit_price,
                    position.exit_reason,
                    position.profit_loss,
                    position.return_percentage,
                    position.symbol
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating position in DB: {e}")
    
    def run_4hour_evaluation(self):
        """
        Run the 4-hour evaluation process for all bank symbols.
        This is the main trading loop.
        """
        logger.info("🚀 Starting 4-hour evaluation process")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        results = {
            'timestamp': start_time.isoformat(),
            'evaluations': {},
            'trades_executed': [],
            'errors': []
        }
        
        # Evaluate each bank symbol
        for symbol in self.settings.BANK_SYMBOLS:
            try:
                logger.info(f"\n📊 Processing {symbol}...")
                
                # Run comprehensive evaluation
                analysis = self.evaluate_trading_opportunity(symbol)
                results['evaluations'][symbol] = analysis
                
                # Execute trading action if recommended
                if analysis.get('recommended_action') and analysis['recommended_action'] != 'HOLD':
                    trade_result = self.execute_trading_action(analysis)
                    if trade_result:
                        results['trades_executed'].append(trade_result)
                
                # Small delay between symbols to avoid overwhelming the system
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"Error processing {symbol}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        # Summary
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n📈 4-Hour Evaluation Complete!")
        logger.info(f"   Duration: {duration:.1f} seconds")
        logger.info(f"   Symbols evaluated: {len(results['evaluations'])}")
        logger.info(f"   Trades executed: {len(results['trades_executed'])}")
        logger.info(f"   Active positions: {len(self.positions)}")
        logger.info(f"   Current capital: ${self.current_capital:,.2f}")
        logger.info(f"   Total portfolio value: ${self.get_portfolio_value():,.2f}")
        
        # Save evaluation results
        self._save_evaluation_results(results)
        
        return results
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value including positions"""
        total_value = self.current_capital
        
        for symbol, position in self.positions.items():
            current_price = self.get_current_price(symbol)
            position_value = position.position_size * current_price
            total_value += position_value
        
        return total_value
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            with self.data_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get completed trades
                cursor.execute("""
                    SELECT COUNT(*) as total_trades,
                           SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                           AVG(profit_loss) as avg_profit_loss,
                           SUM(profit_loss) as total_profit_loss,
                           AVG(return_percentage) as avg_return_pct,
                           MAX(return_percentage) as best_trade_pct,
                           MIN(return_percentage) as worst_trade_pct
                    FROM positions 
                    WHERE exit_date IS NOT NULL
                """)
                
                result = cursor.fetchone()
                
                portfolio_value = self.get_portfolio_value()
                total_return = ((portfolio_value - self.initial_capital) / self.initial_capital) * 100
                
                metrics = {
                    'initial_capital': self.initial_capital,
                    'current_capital': self.current_capital,
                    'portfolio_value': portfolio_value,
                    'total_return_pct': total_return,
                    'total_profit_loss': result[4] if result else 0.0,
                    'total_trades': result[0] if result else 0,
                    'winning_trades': result[1] if result else 0,
                    'win_rate': (result[1] / result[0] * 100) if result and result[0] > 0 else 0,
                    'avg_profit_loss': result[2] if result else 0.0,
                    'avg_return_pct': result[4] if result else 0.0,
                    'best_trade_pct': result[5] if result else 0.0,
                    'worst_trade_pct': result[6] if result else 0.0,
                    'active_positions': len(self.positions),
                    'last_updated': datetime.now().isoformat()
                }
                
                return metrics
                
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {
                'error': str(e),
                'current_capital': self.current_capital,
                'portfolio_value': self.get_portfolio_value()
            }
    
    def _save_evaluation_results(self, results: Dict[str, Any]):
        """Save evaluation results to database for analysis"""
        try:
            with self.data_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create evaluation results table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS evaluation_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        results_json TEXT NOT NULL,
                        trades_count INTEGER,
                        portfolio_value REAL
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO evaluation_results 
                    (timestamp, results_json, trades_count, portfolio_value)
                    VALUES (?, ?, ?, ?)
                """, (
                    results['timestamp'],
                    json.dumps(results, default=str),
                    len(results['trades_executed']),
                    self.get_portfolio_value()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving evaluation results: {e}")
    
    def start_background_trading(self, interval_hours: int = 4):
        """
        Start the background trading process that runs evaluations every N hours.
        
        Args:
            interval_hours: Hours between evaluations (default: 4)
        """
        logger.info(f"🔄 Starting background trading process (every {interval_hours} hours)")
        
        self.running = True
        
        # Schedule the evaluation
        schedule.every(interval_hours).hours.do(self.run_4hour_evaluation)
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("📛 Shutdown signal received")
            self.stop_background_trading()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run initial evaluation
        logger.info("🚀 Running initial evaluation...")
        self.run_4hour_evaluation()
        
        # Main loop
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("📛 Keyboard interrupt received")
            self.stop_background_trading()
    
    def stop_background_trading(self):
        """Stop the background trading process"""
        logger.info("🛑 Stopping background trading process")
        self.running = False

def main():
    """Main function for running the paper trading simulator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Paper Trading Simulator')
    parser.add_argument('--mode', choices=['single', 'background'], default='single',
                      help='Run single evaluation or start background process')
    parser.add_argument('--interval', type=int, default=4,
                      help='Hours between evaluations in background mode')
    parser.add_argument('--capital', type=float, default=100000.0,
                      help='Initial virtual capital')
    parser.add_argument('--performance', action='store_true',
                      help='Show performance metrics and exit')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize simulator
    simulator = PaperTradingSimulator(initial_capital=args.capital)
    
    if args.performance:
        # Show performance metrics
        metrics = simulator.get_performance_metrics()
        print("\n📊 Paper Trading Performance Metrics")
        print("=" * 50)
        print(f"Initial Capital:     ${metrics['initial_capital']:,.2f}")
        print(f"Current Capital:     ${metrics['current_capital']:,.2f}")
        print(f"Portfolio Value:     ${metrics['portfolio_value']:,.2f}")
        print(f"Total Return:        {metrics['total_return_pct']:+.2f}%")
        print(f"Total P&L:           ${metrics['total_profit_loss']:+,.2f}")
        print(f"Total Trades:        {metrics['total_trades']}")
        print(f"Win Rate:            {metrics['win_rate']:.1f}%")
        print(f"Active Positions:    {metrics['active_positions']}")
        return
    
    if args.mode == 'single':
        # Run single evaluation
        results = simulator.run_4hour_evaluation()
        
        # Show summary
        print(f"\n📈 Evaluation Summary:")
        print(f"   Trades executed: {len(results['trades_executed'])}")
        print(f"   Portfolio value: ${simulator.get_portfolio_value():,.2f}")
        
    else:
        # Start background process
        simulator.start_background_trading(interval_hours=args.interval)

if __name__ == '__main__':
    main()