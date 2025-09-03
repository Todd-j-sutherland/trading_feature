"""
Alpaca Trading Integration for ML-based Trading Simulation

Provides paper trading capabilities using Alpaca's API with ML trading scores.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Try to import Alpaca SDK
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logger.warning("Alpaca SDK not available. Install with: pip install alpaca-trade-api")

class AlpacaMLTrader:
    """
    Alpaca trading integration with ML scoring system.
    """
    
    def __init__(self, paper: bool = True):
        """
        Initialize Alpaca ML Trader.
        
        Args:
            paper: Whether to use paper trading (default: True)
        """
        self.paper = paper
        self.client = None
        self.api_key = None
        self.secret_key = None
        self.base_url = None
        
        if not ALPACA_AVAILABLE:
            logger.warning("Alpaca SDK not available")
            return
            
        self._setup_credentials()
        self._initialize_client()
    
    def _setup_credentials(self):
        """Setup Alpaca API credentials from environment variables."""
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        # Use paper trading URL by default
        if self.paper:
            self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        else:
            self.base_url = os.getenv('ALPACA_BASE_URL', 'https://api.alpaca.markets')
        
        if not all([self.api_key, self.secret_key]):
            logger.warning("Alpaca credentials not found in environment variables")
    
    def _initialize_client(self):
        """Initialize Alpaca trading client."""
        if not all([self.api_key, self.secret_key]):
            return
            
        try:
            self.client = tradeapi.REST(
                key_id=self.api_key,
                secret_key=self.secret_key,
                base_url=self.base_url,
                api_version='v2'
            )
            
            # Test connection
            account = self.client.get_account()
            logger.info(f"Connected to Alpaca ({'Paper' if self.paper else 'Live'}) - Account: {account.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Alpaca trading is available."""
        return ALPACA_AVAILABLE and self.client is not None
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        if not self.is_available():
            return {'error': 'Alpaca not available'}
        
        try:
            account = self.client.get_account()
            
            return {
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity),
                'cash': float(account.cash),
                'day_trade_count': account.day_trade_count,
                'pattern_day_trader': account.pattern_day_trader,
                'status': account.status,
                'paper': self.paper
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {'error': str(e)}
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        if not self.is_available():
            return []
        
        try:
            positions = self.client.get_all_positions()
            
            position_list = []
            for position in positions:
                position_list.append({
                    'symbol': position.symbol,
                    'qty': float(position.qty),
                    'market_value': float(position.market_value),
                    'avg_entry_price': float(position.avg_entry_price),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc),
                    'side': position.side
                })
            
            return position_list
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """Get latest quote for a symbol."""
        if not self.is_available():
            return {'error': 'Alpaca not available'}
        
        try:
            # Remove .AX suffix for Alpaca (US markets)
            us_symbol = symbol.replace('.AX', '')
            
            # Get latest quote using alpaca-trade-api
            quote = self.client.get_latest_quote(us_symbol)
            
            return {
                'symbol': symbol,
                'bid_price': float(quote.bidprice),
                'ask_price': float(quote.askprice),
                'bid_size': quote.bidsize,
                'ask_size': quote.asksize,
                'timestamp': quote.timestamp.isoformat()
            }
                
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return {'error': str(e)}
    
    def place_ml_order(self, 
                      symbol: str, 
                      ml_score_data: Dict,
                      portfolio_value: float = 10000.0) -> Dict[str, Any]:
        """
        Place an order based on ML trading score.
        
        Args:
            symbol: Stock symbol
            ml_score_data: ML trading score data
            portfolio_value: Portfolio value for position sizing
            
        Returns:
            Order result dictionary
        """
        if not self.is_available():
            return {'error': 'Alpaca not available'}
        
        try:
            # Extract trading recommendation and position size
            recommendation = ml_score_data.get('trading_recommendation', 'HOLD')
            position_size_pct = ml_score_data.get('position_size_pct', 0.05)
            ml_score = ml_score_data.get('overall_ml_score', 0)
            
            # Skip if HOLD or low score
            if recommendation == 'HOLD' or ml_score < 40:
                return {
                    'status': 'skipped',
                    'reason': f'Recommendation: {recommendation}, Score: {ml_score}'
                }
            
            # Calculate position size
            position_value = portfolio_value * position_size_pct
            
            # Get current quote
            quote_data = self.get_latest_quote(symbol)
            if 'error' in quote_data:
                return {'error': f'Cannot get quote for {symbol}'}
            
            # Use mid price for calculations
            bid_price = quote_data.get('bid_price', 0)
            ask_price = quote_data.get('ask_price', 0)
            mid_price = (bid_price + ask_price) / 2 if bid_price and ask_price else 0
            
            if mid_price <= 0:
                return {'error': f'Invalid price for {symbol}'}
            
            # Calculate quantity
            qty = int(position_value / mid_price)
            if qty <= 0:
                return {'error': f'Position size too small for {symbol}'}
            
            # Remove .AX suffix for US markets
            us_symbol = symbol.replace('.AX', '')
            
            # Determine order side
            if recommendation in ['BUY', 'WEAK_BUY', 'STRONG_BUY']:
                side = 'buy'
            elif recommendation in ['SELL', 'WEAK_SELL', 'STRONG_SELL']:
                side = 'sell'
            else:
                return {'status': 'skipped', 'reason': f'Unknown recommendation: {recommendation}'}
            
            # Place market order using alpaca-trade-api
            order = self.client.submit_order(
                symbol=us_symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='day'
            )
            
            # Track ML trade
            ml_trade_record = {
                'order_id': str(order.id),
                'symbol': symbol,
                'us_symbol': us_symbol,
                'side': side,
                'qty': qty,
                'ml_score': ml_score,
                'recommendation': recommendation,
                'position_size_pct': position_size_pct,
                'estimated_price': mid_price,
                'ml_score_data': ml_score_data,
                'timestamp': datetime.now().isoformat(),
                'status': 'submitted'
            }
            
            self.ml_trades.append(ml_trade_record)
            self._save_ml_trades()
            
            logger.info(f"ML order placed: {side.value} {qty} shares of {symbol} (Score: {ml_score})")
            
            return {
                'status': 'submitted',
                'order_id': str(order.id),
                'symbol': symbol,
                'side': side.value,
                'qty': qty,
                'ml_score': ml_score,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Error placing ML order for {symbol}: {e}")
            return {'error': str(e)}
    
    def execute_ml_trading_strategy(self, ml_scores: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Execute trading strategy based on ML scores for all banks.
        
        Args:
            ml_scores: Dictionary of ML scores {symbol: score_data}
            
        Returns:
            Summary of trading actions
        """
        if not self.is_available():
            return {'error': 'Alpaca not available'}
        
        logger.info("Executing ML trading strategy...")
        
        # Get account info for position sizing
        account_info = self.get_account_info()
        if 'error' in account_info:
            return {'error': 'Cannot get account info'}
        
        portfolio_value = account_info.get('portfolio_value', 10000.0)
        
        results = {
            'orders_placed': [],
            'orders_skipped': [],
            'errors': [],
            'summary': {}
        }
        
        # Process each bank
        for symbol, score_data in ml_scores.items():
            if symbol.startswith('_'):  # Skip summary entries
                continue
            
            if 'error' in score_data:
                results['errors'].append({
                    'symbol': symbol,
                    'error': score_data['error']
                })
                continue
            
            # Place order based on ML score
            order_result = self.place_ml_order(symbol, score_data, portfolio_value)
            
            if order_result.get('status') == 'submitted':
                results['orders_placed'].append(order_result)
            elif order_result.get('status') == 'skipped':
                results['orders_skipped'].append(order_result)
            else:
                results['errors'].append({
                    'symbol': symbol,
                    'error': order_result.get('error', 'Unknown error')
                })
        
        # Generate summary
        results['summary'] = {
            'total_symbols': len([s for s in ml_scores.keys() if not s.startswith('_')]),
            'orders_placed': len(results['orders_placed']),
            'orders_skipped': len(results['orders_skipped']),
            'errors': len(results['errors']),
            'portfolio_value': portfolio_value,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"ML trading strategy executed: {results['summary']['orders_placed']} orders placed")
        return results
    
    def get_ml_trade_performance(self) -> Dict[str, Any]:
        """
        Get performance statistics for ML-based trades.
        
        Returns:
            Performance metrics dictionary
        """
        if not self.ml_trades:
            return {'message': 'No ML trades recorded'}
        
        try:
            # Load ML trades
            self._load_ml_trades()
            
            # Update trade status and P&L
            updated_trades = []
            total_pl = 0.0
            winning_trades = 0
            losing_trades = 0
            
            for trade in self.ml_trades:
                # Get current order status
                try:
                    order = self.client.get_order_by_id(trade['order_id'])
                    trade['current_status'] = order.status.value
                    
                    if order.filled_at:
                        trade['filled_price'] = float(order.filled_avg_price or trade['estimated_price'])
                        trade['filled_at'] = order.filled_at.isoformat()
                        
                        # Calculate P&L if we have current price
                        current_quote = self.get_latest_quote(trade['symbol'])
                        if 'error' not in current_quote:
                            current_price = (current_quote['bid_price'] + current_quote['ask_price']) / 2
                            
                            if trade['side'] == 'buy':
                                pl = (current_price - trade['filled_price']) * trade['qty']
                            else:
                                pl = (trade['filled_price'] - current_price) * trade['qty']
                            
                            trade['unrealized_pl'] = pl
                            total_pl += pl
                            
                            if pl > 0:
                                winning_trades += 1
                            else:
                                losing_trades += 1
                
                except Exception as e:
                    logger.warning(f"Error updating trade {trade['order_id']}: {e}")
                
                updated_trades.append(trade)
            
            self.ml_trades = updated_trades
            self._save_ml_trades()
            
            # Calculate performance metrics
            total_trades = winning_trades + losing_trades
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            return {
                'total_ml_trades': len(self.ml_trades),
                'completed_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 3),
                'total_unrealized_pl': round(total_pl, 2),
                'avg_ml_score': round(sum(t['ml_score'] for t in self.ml_trades) / len(self.ml_trades), 2),
                'recent_trades': self.ml_trades[-5:] if len(self.ml_trades) > 5 else self.ml_trades
            }
            
        except Exception as e:
            logger.error(f"Error calculating ML trade performance: {e}")
            return {'error': str(e)}
    
    def _save_ml_trades(self):
        """Save ML trades to file."""
        try:
            os.makedirs('data/alpaca', exist_ok=True)
            with open('data/alpaca/ml_trades.json', 'w') as f:
                json.dump(self.ml_trades, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving ML trades: {e}")
    
    def _load_ml_trades(self):
        """Load ML trades from file."""
        try:
            if os.path.exists('data/alpaca/ml_trades.json'):
                with open('data/alpaca/ml_trades.json', 'r') as f:
                    self.ml_trades = json.load(f)
        except Exception as e:
            logger.error(f"Error loading ML trades: {e}")
            self.ml_trades = []

if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Initialize trader
    trader = AlpacaMLTrader(paper=True)
    
    if trader.is_available():
        # Get account info
        account = trader.get_account_info()
        print("Account Info:", account)
        
        # Mock ML score data
        mock_ml_score = {
            'overall_ml_score': 75.5,
            'trading_recommendation': 'BUY',
            'position_size_pct': 0.05,
            'risk_level': 'MEDIUM'
        }
        
        # Test order placement (paper trading)
        print("\nTesting order placement...")
        # Note: This would work with US symbols, ASX symbols need mapping
        # order_result = trader.place_ml_order('AAPL', mock_ml_score, 10000.0)
        # print("Order Result:", order_result)
        
        # Get ML trade performance
        performance = trader.get_ml_trade_performance()
        print("ML Trade Performance:", performance)
    else:
        print("Alpaca trading not available. Check credentials and installation.")
