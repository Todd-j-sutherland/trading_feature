#!/usr/bin/env python3
"""
Advanced Paper Trading - Enhanced paper trading with analytics and performance tracking
Provides comprehensive paper trading simulation with ML integration
"""
import json
import os
import sys
sys.path.append('..')  # Add parent directory to path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
# from news_trading_analyzer import NewsTradingAnalyzer  # Optional module - disabled
from app.core.ml.training.pipeline import MLTrainingPipeline
from app.core.data.collectors.market_data import ASXDataFeed
from app.config.settings import Settings

class AdvancedPaperTrader:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        # self.analyzer = NewsTradingAnalyzer()  # Optional - disabled
        self.analyzer = None
        self.ml_pipeline = MLTrainingPipeline()
        self.data_feed = ASXDataFeed()
        
        # Trading state
        self.positions = {}  # symbol -> position info
        self.trade_history = []
        self.daily_pnl = {}
        self.performance_metrics = {}
        
        # Load state
        self.load_trading_state()
        
    def load_trading_state(self):
        """Load trading state from file"""
        state_file = 'data/paper_trading_state.json'
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
                self.current_capital = state.get('current_capital', self.initial_capital)
                self.positions = state.get('positions', {})
                self.trade_history = state.get('trade_history', [])
                self.daily_pnl = state.get('daily_pnl', {})
    
    def save_trading_state(self):
        """Save trading state to file"""
        state = {
            'current_capital': self.current_capital,
            'positions': self.positions,
            'trade_history': self.trade_history,
            'daily_pnl': self.daily_pnl,
            'last_update': datetime.now().isoformat()
        }
        
        os.makedirs('data', exist_ok=True)
        with open('data/paper_trading_state.json', 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            price_data = self.data_feed.get_current_price(symbol)
            return price_data.get('price', 100.0)
        except:
            return 100.0  # Fallback price
    
    def calculate_position_size(self, symbol: str, signal_confidence: float) -> float:
        """Calculate position size based on confidence and risk management"""
        # Risk management: max 10% of capital per trade
        max_position_value = self.current_capital * 0.1
        
        # Scale position size by confidence (0.5 to 1.0 range)
        confidence_multiplier = max(0.5, signal_confidence)
        position_value = max_position_value * confidence_multiplier
        
        current_price = self.get_current_price(symbol)
        position_size = position_value / current_price
        
        return position_size
    
    def execute_trade(self, symbol: str, signal: str, analysis_result: Dict):
        """Execute a paper trade based on signal"""
        current_price = self.get_current_price(symbol)
        timestamp = datetime.now().isoformat()
        
        # Calculate position size
        confidence = analysis_result.get('confidence', 0.5)
        position_size = self.calculate_position_size(symbol, confidence)
        
        trade_record = {
            'symbol': symbol,
            'timestamp': timestamp,
            'signal': signal,
            'price': current_price,
            'confidence': confidence,
            'sentiment_score': analysis_result.get('overall_sentiment', 0),
            'ml_prediction': analysis_result.get('ml_prediction', {}),
            'feature_id': analysis_result.get('ml_feature_id'),
            'status': 'open'
        }
        
        if signal == 'BUY':
            if symbol not in self.positions:
                # Enter new position
                position_value = position_size * current_price
                
                if position_value <= self.current_capital:
                    self.positions[symbol] = {
                        'quantity': position_size,
                        'entry_price': current_price,
                        'entry_timestamp': timestamp,
                        'entry_confidence': confidence,
                        'feature_id': analysis_result.get('ml_feature_id'),
                        'unrealized_pnl': 0
                    }
                    
                    self.current_capital -= position_value
                    trade_record['action'] = 'BUY'
                    trade_record['quantity'] = position_size
                    trade_record['value'] = position_value
                    
                    print(f"📈 BUY: {symbol} @ ${current_price:.2f} ({position_size:.0f} shares)")
                    
                else:
                    print(f"❌ Insufficient capital for {symbol}")
                    return None
            else:
                print(f"⚠️ Already holding {symbol}")
                return None
                
        elif signal == 'SELL':
            if symbol in self.positions:
                # Close position
                position = self.positions[symbol]
                quantity = position['quantity']
                entry_price = position['entry_price']
                
                # Calculate P&L
                pnl = (current_price - entry_price) * quantity
                pnl_percent = (current_price - entry_price) / entry_price * 100
                
                # Update capital
                position_value = quantity * current_price
                self.current_capital += position_value
                
                # Record trade
                trade_record['action'] = 'SELL'
                trade_record['quantity'] = quantity
                trade_record['value'] = position_value
                trade_record['pnl'] = pnl
                trade_record['pnl_percent'] = pnl_percent
                trade_record['entry_price'] = entry_price
                trade_record['entry_timestamp'] = position['entry_timestamp']
                trade_record['hold_duration'] = (datetime.now() - datetime.fromisoformat(position['entry_timestamp'])).total_seconds() / 3600
                
                # Record outcome for ML training
                if position.get('feature_id'):
                    outcome_data = {
                        'symbol': symbol,
                        'signal_timestamp': position['entry_timestamp'],
                        'signal_type': 'BUY',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'exit_timestamp': timestamp,
                        'max_drawdown': min(0, pnl_percent / 100 * 0.7)  # Estimate
                    }
                    
                    try:
                        self.ml_pipeline.record_trading_outcome(position['feature_id'], outcome_data)
                        print(f"📊 ML outcome recorded for {symbol}")
                    except Exception as e:
                        print(f"❌ Error recording ML outcome: {e}")
                
                print(f"📉 SELL: {symbol} @ ${current_price:.2f} - P&L: ${pnl:.2f} ({pnl_percent:.1f}%)")
                
                # Remove position
                del self.positions[symbol]
                
            else:
                print(f"⚠️ No position in {symbol} to sell")
                return None
        
        # Add to trade history
        self.trade_history.append(trade_record)
        self.save_trading_state()
        
        return trade_record
    
    def update_unrealized_pnl(self):
        """Update unrealized P&L for all positions"""
        for symbol, position in self.positions.items():
            current_price = self.get_current_price(symbol)
            entry_price = position['entry_price']
            quantity = position['quantity']
            
            unrealized_pnl = (current_price - entry_price) * quantity
            unrealized_pnl_percent = (current_price - entry_price) / entry_price * 100
            
            position['unrealized_pnl'] = unrealized_pnl
            position['unrealized_pnl_percent'] = unrealized_pnl_percent
            position['current_price'] = current_price
    
    def calculate_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        self.update_unrealized_pnl()
        
        portfolio_value = self.current_capital
        
        for symbol, position in self.positions.items():
            current_price = position.get('current_price', position['entry_price'])
            quantity = position['quantity']
            portfolio_value += current_price * quantity
        
        return portfolio_value
    
    def get_performance_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not self.trade_history:
            return {'status': 'No trades yet'}
        
        # Filter completed trades
        completed_trades = [t for t in self.trade_history if t.get('action') == 'SELL']
        
        if not completed_trades:
            return {'status': 'No completed trades yet'}
        
        # Calculate metrics
        total_trades = len(completed_trades)
        profitable_trades = sum(1 for t in completed_trades if t.get('pnl', 0) > 0)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        total_pnl = sum(t.get('pnl', 0) for t in completed_trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        # Calculate returns
        returns = [t.get('pnl_percent', 0) / 100 for t in completed_trades]
        
        if returns:
            avg_return = sum(returns) / len(returns)
            max_win = max(returns)
            max_loss = min(returns)
            
            # Simple Sharpe ratio (assuming 0% risk-free rate)
            import math
            if len(returns) > 1:
                return_std = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1))
                sharpe_ratio = (avg_return / return_std) * math.sqrt(252) if return_std > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            avg_return = max_win = max_loss = sharpe_ratio = 0
        
        # Portfolio performance
        portfolio_value = self.calculate_portfolio_value()
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        
        return {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl_per_trade': avg_pnl,
            'avg_return_per_trade': avg_return,
            'max_win': max_win,
            'max_loss': max_loss,
            'sharpe_ratio': sharpe_ratio,
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'portfolio_value': portfolio_value,
            'total_return': total_return,
            'active_positions': len(self.positions),
            'unrealized_pnl': sum(p.get('unrealized_pnl', 0) for p in self.positions.values())
        }
    
    def print_performance_report(self):
        """Print comprehensive performance report"""
        metrics = self.get_performance_metrics()
        
        print("\n" + "="*60)
        print("📊 ADVANCED PAPER TRADING PERFORMANCE REPORT")
        print("="*60)
        
        if metrics.get('status'):
            print(f"Status: {metrics['status']}")
            return
        
        print(f"Initial Capital:    ${metrics['initial_capital']:,.2f}")
        print(f"Current Capital:    ${metrics['current_capital']:,.2f}")
        print(f"Portfolio Value:    ${metrics['portfolio_value']:,.2f}")
        print(f"Total Return:       {metrics['total_return']:.2%}")
        print(f"Unrealized P&L:     ${metrics['unrealized_pnl']:,.2f}")
        
        print(f"\nTrading Performance:")
        print(f"Total Trades:       {metrics['total_trades']}")
        print(f"Profitable Trades:  {metrics['profitable_trades']}")
        print(f"Win Rate:           {metrics['win_rate']:.1%}")
        print(f"Avg P&L per Trade:  ${metrics['avg_pnl_per_trade']:,.2f}")
        print(f"Avg Return per Trade: {metrics['avg_return_per_trade']:.2%}")
        print(f"Best Trade:         {metrics['max_win']:.2%}")
        print(f"Worst Trade:        {metrics['max_loss']:.2%}")
        print(f"Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}")
        
        print(f"\nCurrent Positions:  {metrics['active_positions']}")
        
        if self.positions:
            print("\nActive Positions:")
            for symbol, position in self.positions.items():
                print(f"  {symbol}: {position['quantity']:.0f} shares @ ${position['entry_price']:.2f}")
                print(f"    Unrealized P&L: ${position.get('unrealized_pnl', 0):.2f} ({position.get('unrealized_pnl_percent', 0):.1f}%)")
        
        print("="*60)
    
    def run_paper_trading_session(self, symbols: List[str], duration_hours: int = 8):
        """Run a paper trading session"""
        print(f"🚀 Starting paper trading session for {duration_hours} hours")
        print(f"Symbols: {', '.join(symbols)}")
        
        end_time = datetime.now() + timedelta(hours=duration_hours)
        
        while datetime.now() < end_time:
            try:
                for symbol in symbols:
                    # Get analysis
                    result = self.analyzer.analyze_and_track(symbol)
                    
                    # Check for trading signals
                    signal = result.get('signal')
                    
                    if signal and signal != 'HOLD':
                        # Execute trade
                        trade = self.execute_trade(symbol, signal, result)
                        
                        if trade:
                            print(f"✅ Executed: {trade['action']} {trade['symbol']}")
                    
                    # Check for exit conditions (basic: 4-hour hold)
                    self.check_exit_conditions(symbol)
                
                # Print periodic updates
                self.print_performance_report()
                
                # Wait before next cycle
                import time
                time.sleep(1800)  # 30 minutes
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping paper trading session...")
                break
            except Exception as e:
                print(f"❌ Error in trading session: {e}")
                import time
                time.sleep(60)  # Wait 1 minute before retry
    
    def check_exit_conditions(self, symbol: str):
        """Check if positions should be exited"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        entry_time = datetime.fromisoformat(position['entry_timestamp'])
        hold_duration = (datetime.now() - entry_time).total_seconds() / 3600
        
        # Simple exit condition: hold for 4 hours
        if hold_duration >= 4:
            # Get current analysis
            try:
                result = self.analyzer.analyze_single_bank(symbol)
                self.execute_trade(symbol, 'SELL', result)
            except Exception as e:
                print(f"❌ Error executing exit for {symbol}: {e}")

if __name__ == "__main__":
    import argparse
    
    settings = Settings()
    parser = argparse.ArgumentParser(description='Advanced paper trading system')
    parser.add_argument('--symbols', nargs='+', default=settings.BANK_SYMBOLS, 
                       help='Symbols to trade')
    parser.add_argument('--duration', type=int, default=8, help='Trading session duration in hours')
    parser.add_argument('--report-only', action='store_true', help='Show performance report only')
    
    args = parser.parse_args()
    
    trader = AdvancedPaperTrader()
    
    if args.report_only:
        trader.print_performance_report()
    else:
        trader.run_paper_trading_session(args.symbols, args.duration)
