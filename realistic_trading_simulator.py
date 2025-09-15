#!/usr/bin/env python3
"""
Realistic Trading Simulator
Simulates how ML predictions would have performed with real trading constraints:
- Only stable market times (accounting for yfinance delays)
- Confidence/risk management thresholds
- One prediction per symbol at a time
- $15,000 per trade position sizing
- Realistic entry/exit timing
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time, timezone
import yfinance as yf
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealisticTradingSimulator:
    """Simulates realistic trading based on ML predictions with proper constraints"""
    
    def __init__(self, db_path="predictions.db", initial_capital=100000):
        self.db_path = Path(db_path)
        self.initial_capital = initial_capital
        self.trade_amount = 15000  # $15,000 per trade
        self.min_confidence = 0.75  # 75% minimum confidence
        
        # Market timing constraints (AEST)
        self.market_open = time(10, 0)   # 10:00 AM
        self.market_close = time(16, 0)   # 4:00 PM
        # Note: Stable trading hours (11:00 AM - 4:00 PM) are handled in is_stable_trading_time()
        
        # Risk management
        self.max_positions = 7  # Max 7 positions (one per major bank)
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.take_profit_pct = 0.10  # 10% take profit
        
        # Trading state
        self.current_positions = {}  # symbol -> position_info
        self.closed_trades = []
        self.portfolio_value = initial_capital
        self.cash_available = initial_capital
        
        logger.info(f"Initialized trading simulator with ${initial_capital:,} capital")
        logger.info(f"Trade size: ${self.trade_amount:,} per position")
        logger.info(f"Minimum confidence: {self.min_confidence:.1%}")
    
    def is_stable_trading_time(self, timestamp: datetime) -> bool:
        """Check if timestamp is during stable trading hours (converted to AEST)"""
        try:
            # Convert UTC timestamp to AEST
            if timestamp.tzinfo is None:
                # Assume UTC if no timezone
                utc_dt = timestamp.replace(tzinfo=timezone.utc)
            else:
                utc_dt = timestamp
            
            # Convert to AEST (UTC+10)
            aest_dt = utc_dt + timedelta(hours=10)
            
            # Check weekday
            if aest_dt.weekday() >= 5:  # Weekend
                return False
            
            # Check time in AEST (11:00 AM - 4:00 PM for broader window)
            trade_time = aest_dt.time()
            start_time = time(11, 0)  # 11:00 AM AEST
            end_time = time(16, 0)    # 4:00 PM AEST
            
            is_stable = start_time <= trade_time <= end_time
            
            if is_stable:
                logger.debug(f"Stable time: {timestamp} UTC -> {aest_dt.strftime('%H:%M')} AEST")
            
            return is_stable
            
        except Exception as e:
            logger.warning(f"Error checking stable time for {timestamp}: {e}")
            return False
    
    def get_predictions_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get filtered predictions data for simulation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT 
                    p.prediction_id,
                    p.symbol,
                    p.prediction_timestamp,
                    p.predicted_action,
                    p.action_confidence,
                    p.entry_price,
                    p.model_version
                FROM predictions p
                WHERE p.prediction_timestamp >= ? 
                AND p.prediction_timestamp <= ?
                AND p.predicted_action IN ('BUY', 'SELL')
                AND p.action_confidence >= ?
                AND p.model_version = 'fixed_price_mapping_v4.0'
                ORDER BY p.prediction_timestamp ASC
                """
                
                df = pd.read_sql_query(query, conn, params=[
                    start_date.isoformat(),
                    end_date.isoformat(),
                    self.min_confidence
                ])
                
                if df.empty:
                    logger.warning("No predictions found for simulation period")
                    return df
                
                # Parse timestamps and filter for stable trading times
                df['prediction_timestamp'] = pd.to_datetime(df['prediction_timestamp'])
                df['is_stable_time'] = df['prediction_timestamp'].apply(self.is_stable_trading_time)
                
                # Filter to stable times only
                stable_df = df[df['is_stable_time']].copy()
                logger.info(f"Found {len(df)} total predictions, {len(stable_df)} during stable trading hours")
                
                return stable_df.reset_index(drop=True)
                
        except Exception as e:
            logger.error(f"Error loading predictions: {e}")
            return pd.DataFrame()
    
    def get_historical_price(self, symbol: str, timestamp: datetime, delay_minutes: int = 15) -> Optional[float]:
        """Get historical price with realistic delay simulation"""
        try:
            # Ensure timestamp is timezone-naive for yfinance compatibility
            if timestamp.tzinfo is not None:
                # Convert to UTC and make naive
                timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
            
            # Add delay to simulate yfinance data lag
            actual_time = timestamp + timedelta(minutes=delay_minutes)
            
            # Get data for the day
            ticker = yf.Ticker(symbol)
            start_date = timestamp.date()
            end_date = start_date + timedelta(days=1)
            
            hist = ticker.history(start=start_date, end=end_date, interval='1m')
            
            if hist.empty:
                logger.warning(f"No price data for {symbol} at {timestamp}")
                return None
            
            # Convert hist index to naive datetime for comparison
            hist_times = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index
            
            # Find closest price to actual_time
            time_diffs = np.abs(hist_times - actual_time)
            closest_idx = np.argmin(time_diffs)
            
            # Add small random variation to simulate bid-ask spread and micro-movements
            # This prevents identical entry/exit prices on same-minute trades
            base_price = float(hist.iloc[closest_idx]['Close'])
            
            # Add 0.01% to 0.1% random variation (typical bid-ask spread)
            variation = np.random.uniform(-0.001, 0.001)  # ±0.1%
            price = base_price * (1 + variation)
            
            logger.debug(f"Price for {symbol} at {actual_time}: ${price:.2f} (base: ${base_price:.2f})")
            return price
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def can_open_position(self, symbol: str, action: str) -> bool:
        """Check if we can open a new position"""
        # Check if symbol already has open position
        if symbol in self.current_positions:
            return False
        
        # Check if we have enough cash
        if self.cash_available < self.trade_amount:
            return False
        
        # Check position limit
        if len(self.current_positions) >= self.max_positions:
            return False
        
        return True
    
    def open_position(self, prediction_row: pd.Series, entry_price: float, entry_time: datetime = None) -> Dict:
        """Open a new trading position"""
        symbol = prediction_row['symbol']
        action = prediction_row['predicted_action']
        confidence = prediction_row['action_confidence']
        # Use provided entry_time or fall back to prediction timestamp
        timestamp = entry_time if entry_time is not None else prediction_row['prediction_timestamp']
        
        # Calculate position size
        shares = int(self.trade_amount / entry_price)
        actual_cost = shares * entry_price
        
        # Update cash
        self.cash_available -= actual_cost
        
        # Calculate stop loss and take profit levels
        if action == 'BUY':
            stop_loss = entry_price * (1 - self.stop_loss_pct)
            take_profit = entry_price * (1 + self.take_profit_pct)
        else:  # SELL (short position)
            stop_loss = entry_price * (1 + self.stop_loss_pct)
            take_profit = entry_price * (1 - self.take_profit_pct)
        
        position = {
            'prediction_id': prediction_row['prediction_id'],
            'symbol': symbol,
            'action': action,
            'entry_time': timestamp,
            'entry_price': entry_price,
            'shares': shares,
            'cost': actual_cost,
            'confidence': confidence,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'model_version': prediction_row['model_version']
        }
        
        self.current_positions[symbol] = position
        
        logger.info(f"OPENED {action} position: {symbol} @ ${entry_price:.2f} "
                   f"({shares} shares, ${actual_cost:,.2f}, {confidence:.1%} confidence)")
        
        return position
    
    def close_position(self, symbol: str, exit_price: float, exit_time: datetime, reason: str) -> Dict:
        """Close an existing position"""
        position = self.current_positions[symbol]
        
        # Calculate P&L
        shares = position['shares']
        entry_price = position['entry_price']
        
        if position['action'] == 'BUY':
            pnl = (exit_price - entry_price) * shares
            return_pct = (exit_price - entry_price) / entry_price
        else:  # SELL (short)
            pnl = (entry_price - exit_price) * shares
            return_pct = (entry_price - exit_price) / entry_price
        
        # Update cash
        exit_value = shares * exit_price
        self.cash_available += exit_value
        
        # Create trade record
        trade = {
            **position,
            'exit_time': exit_time,
            'exit_price': exit_price,
            'exit_value': exit_value,
            'pnl': pnl,
            'return_pct': return_pct,
            'reason': reason,
            'holding_time': exit_time - position['entry_time'],
            'successful': pnl > 0
        }
        
        self.closed_trades.append(trade)
        del self.current_positions[symbol]
        
        # Update portfolio value
        self.portfolio_value = self.cash_available + sum(
            pos['shares'] * exit_price for pos in self.current_positions.values()
        )
        
        logger.info(f"CLOSED {position['action']} position: {symbol} @ ${exit_price:.2f} "
                   f"(P&L: ${pnl:+.2f}, {return_pct:+.2%}, {reason})")
        
        return trade
    
    def check_exit_conditions(self, symbol: str, current_price: float, current_time: datetime) -> Optional[str]:
        """Check if position should be closed based on stop loss, take profit, or time"""
        position = self.current_positions[symbol]
        
        if position['action'] == 'BUY':
            if current_price <= position['stop_loss']:
                return 'Stop Loss'
            elif current_price >= position['take_profit']:
                return 'Take Profit'
        else:  # SELL (short)
            if current_price >= position['stop_loss']:
                return 'Stop Loss'
            elif current_price <= position['take_profit']:
                return 'Take Profit'
        
        # Time-based exit (end of day or max holding period)
        holding_time = current_time - position['entry_time']
        if holding_time >= timedelta(hours=4):  # Max 4 hour hold
            return 'Time Limit'
        
        # Near market close - convert to AEST for comparison
        if current_time.tzinfo is None:
            # Assume UTC if no timezone
            aest_time = current_time + timedelta(hours=10)
        else:
            aest_time = current_time.astimezone(timezone.utc) + timedelta(hours=10)
        
        # Close positions 15 minutes before market close (3:45 PM AEST)
        # But only if we've held the position for at least 30 minutes
        if aest_time.time() >= time(15, 45) and holding_time >= timedelta(minutes=30):
            return 'Market Close'
        
        return None
    
    def simulate_trading(self, start_date: datetime, end_date: datetime) -> Dict:
        """Run the complete trading simulation"""
        logger.info(f"Starting simulation from {start_date.date()} to {end_date.date()}")
        
        # Get predictions data
        predictions_df = self.get_predictions_data(start_date, end_date)
        
        if predictions_df.empty:
            logger.warning("No predictions to simulate")
            return self.get_simulation_results()
        
        # Process each prediction
        for idx, prediction in predictions_df.iterrows():
            symbol = prediction['symbol']
            action = prediction['predicted_action']
            timestamp = prediction['prediction_timestamp']
            confidence = prediction['action_confidence']
            
            # Calculate actual execution time (prediction + 15 min delay)
            actual_entry_time = timestamp + timedelta(minutes=15)
            
            logger.info(f"\nProcessing prediction {idx+1}/{len(predictions_df)}: "
                       f"{action} {symbol} (prediction at {timestamp.strftime('%H:%M UTC')}, "
                       f"execution at {actual_entry_time.strftime('%H:%M UTC')}, {confidence:.1%} confidence)")
            
            # Check if we can open position
            if not self.can_open_position(symbol, action):
                logger.info(f"Cannot open position for {symbol} (existing position or insufficient funds)")
                continue
            
            # Get entry price with delay
            entry_price = self.get_historical_price(symbol, timestamp, delay_minutes=15)
            if not entry_price:
                logger.warning(f"Could not get entry price for {symbol}")
                continue
            
            # Open position with actual execution time
            position = self.open_position(prediction, entry_price, actual_entry_time)
            
            # Monitor position for exits (simulate checking every 15 minutes from actual entry time)
            check_time = actual_entry_time + timedelta(minutes=15)  # First check 15 min after actual entry
            max_check_time = actual_entry_time + timedelta(hours=4)  # Max 4 hours from actual entry
            
            while check_time <= max_check_time and symbol in self.current_positions:
                # Get current price
                current_price = self.get_historical_price(symbol, check_time, delay_minutes=0)
                
                if current_price:
                    # Check exit conditions
                    exit_reason = self.check_exit_conditions(symbol, current_price, check_time)
                    
                    if exit_reason:
                        self.close_position(symbol, current_price, check_time, exit_reason)
                        break
                
                check_time += timedelta(minutes=15)  # Check every 15 minutes
            
            # Force close if still open at end of monitoring period
            if symbol in self.current_positions:
                final_price = self.get_historical_price(symbol, max_check_time)
                if final_price:
                    self.close_position(symbol, final_price, max_check_time, 'End of Period')
        
        # Close any remaining positions
        self.close_remaining_positions(end_date)
        
        logger.info("Simulation completed")
        return self.get_simulation_results()
    
    def close_remaining_positions(self, end_date: datetime):
        """Close any remaining open positions at simulation end"""
        for symbol in list(self.current_positions.keys()):
            final_price = self.get_historical_price(symbol, end_date)
            if final_price:
                self.close_position(symbol, final_price, end_date, 'Simulation End')
    
    def get_simulation_results(self) -> Dict:
        """Calculate and return simulation results"""
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'avg_trade_return': 0,
                'final_portfolio_value': self.initial_capital,
                'trades': []
            }
        
        trades_df = pd.DataFrame(self.closed_trades)
        
        # Calculate metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] <= 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_pnl = trades_df['pnl'].sum()
        total_return = total_pnl / self.initial_capital
        
        best_trade = trades_df['return_pct'].max()
        worst_trade = trades_df['return_pct'].min()
        avg_trade_return = trades_df['return_pct'].mean()
        
        final_portfolio_value = self.initial_capital + total_pnl
        
        results = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'avg_trade_return': avg_trade_return,
            'final_portfolio_value': final_portfolio_value,
            'trades': self.closed_trades
        }
        
        return results
    
    def print_simulation_summary(self, results: Dict):
        """Print a formatted summary of simulation results"""
        print("\n" + "="*60)
        print("🏦 REALISTIC TRADING SIMULATION RESULTS")
        print("="*60)
        
        print(f"📊 PERFORMANCE METRICS:")
        print(f"   Total Trades: {results['total_trades']}")
        print(f"   Winning Trades: {results['winning_trades']} ({results['win_rate']:.1%})")
        print(f"   Losing Trades: {results['losing_trades']}")
        print(f"   Win Rate: {results['win_rate']:.1%}")
        
        print(f"\n💰 FINANCIAL RESULTS:")
        print(f"   Initial Capital: ${self.initial_capital:,}")
        print(f"   Final Portfolio Value: ${results['final_portfolio_value']:,.2f}")
        print(f"   Total P&L: ${results['total_pnl']:+,.2f}")
        print(f"   Total Return: {results['total_return']:+.2%}")
        
        print(f"\n📈 TRADE STATISTICS:")
        print(f"   Best Trade: {results['best_trade']:+.2%}")
        print(f"   Worst Trade: {results['worst_trade']:+.2%}")
        print(f"   Average Trade Return: {results['avg_trade_return']:+.2%}")
        
        # Show recent trades
        if results['trades']:
            print(f"\n🔍 RECENT TRADES:")
            for trade in results['trades'][-5:]:
                action_emoji = "🟢" if trade['action'] == 'BUY' else "🔴"
                result_emoji = "✅" if trade['successful'] else "❌"
                print(f"   {action_emoji} {result_emoji} {trade['symbol']} "
                      f"{trade['action']} @ ${trade['entry_price']:.2f} → ${trade['exit_price']:.2f} "
                      f"({trade['return_pct']:+.2%}, {trade['reason']})")
        
        print("="*60)

def main():
    """Main function to run the trading simulation"""
    # Initialize simulator
    simulator = RealisticTradingSimulator(initial_capital=100000)
    
    # Define simulation period (last 30 days with predictions)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"🚀 Starting Realistic Trading Simulation")
    print(f"📅 Period: {start_date.date()} to {end_date.date()}")
    print(f"💰 Initial Capital: ${simulator.initial_capital:,}")
    print(f"📈 Trade Size: ${simulator.trade_amount:,} per position")
    print(f"🎯 Minimum Confidence: {simulator.min_confidence:.1%}")
    print(f"⏰ Trading Hours: 11:00 AM - 4:00 PM AEST (stable hours)")  # Updated to show actual hours
    
    # Run simulation
    results = simulator.simulate_trading(start_date, end_date)
    
    # Print results
    simulator.print_simulation_summary(results)
    
    # Save results to file
    results_file = Path("realistic_trading_simulation_results.json")
    with open(results_file, 'w') as f:
        # Convert datetime objects to strings for JSON serialization
        json_results = {k: v for k, v in results.items() if k != 'trades'}
        json_results['trades'] = []
        
        for trade in results['trades']:
            json_trade = trade.copy()
            json_trade['entry_time'] = trade['entry_time'].isoformat()
            json_trade['exit_time'] = trade['exit_time'].isoformat()
            json_trade['holding_time'] = str(trade['holding_time'])
            json_results['trades'].append(json_trade)
        
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to {results_file}")
    
    # Provide insights
    print(f"\n💡 INSIGHTS:")
    if results['total_trades'] > 0:
        if results['win_rate'] > 0.6 and results['total_return'] > 0.02:
            print("   🚀 EXCELLENT: Your predictions show strong profitability!")
        elif results['win_rate'] > 0.5 and results['total_return'] > 0:
            print("   ✅ GOOD: Your predictions are profitable with realistic constraints.")
        else:
            print("   ⚠️ NEEDS IMPROVEMENT: Consider higher confidence thresholds or better timing.")
        
        print(f"   📊 Your ML system would have generated ${results['total_pnl']:+,.2f} "
              f"with realistic trading constraints.")
    else:
        print("   📭 No qualifying trades found. Try longer period or lower confidence threshold.")

if __name__ == "__main__":
    main()
