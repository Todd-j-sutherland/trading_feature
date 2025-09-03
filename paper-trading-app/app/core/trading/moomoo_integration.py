"""
Moomoo Trading Integration for ASX ML-based Trading
Provides paper trading capabilities using Moomoo's OpenAPI for ASX stocks.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Try to import Moomoo SDK
try:
    from moomoo import *
    MOOMOO_AVAILABLE = True
except ImportError:
    MOOMOO_AVAILABLE = False
    logger.warning("Moomoo SDK not available. Install with: pip install moomoo-api")

class MoomooMLTrader:
    """
    Moomoo trading integration with ML scoring system for ASX stocks.
    """
    
    def __init__(self, paper: bool = True, host: str = '127.0.0.1', port: int = 11111):
        """
        Initialize Moomoo ML Trader.
        
        Args:
            paper: Whether to use paper trading (default: True)
            host: OpenD gateway host (default: localhost)
            port: OpenD gateway port (default: 11111)
        """
        self.paper = paper
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.trade_ctx = None
        self.ml_trades = []
        
        if not MOOMOO_AVAILABLE:
            logger.warning("Moomoo SDK not available")
            return
            
        self._initialize_clients()
        self._load_ml_trades()
    
    def _initialize_clients(self):
        """Initialize Moomoo quote and trading clients."""
        try:
            # Initialize quote context for market data
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
            logger.info(f"Connected to Moomoo quote service at {self.host}:{self.port}")
            
            # Initialize trading context for orders
            # Using FUTUAU for Australian market
            self.trade_ctx = OpenSecTradeContext(
                filter_trdmarket=TrdMarket.AU,  # Australian market
                host=self.host, 
                port=self.port,
                security_firm=SecurityFirm.FUTUAU  # Australian Moomoo
            )
            
            logger.info(f"Connected to Moomoo trading service ({'Paper' if self.paper else 'Live'}) - AU Market")
            
        except Exception as e:
            logger.error(f"Failed to initialize Moomoo clients: {e}")
            self.quote_ctx = None
            self.trade_ctx = None
    
    def is_available(self) -> bool:
        """Check if Moomoo trading is available."""
        return MOOMOO_AVAILABLE and self.quote_ctx is not None and self.trade_ctx is not None
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        if not self.is_available():
            return {'error': 'Moomoo not available'}
        
        try:
            # Get account info
            ret, data = self.trade_ctx.accinfo_query(
                trd_env=TrdEnv.SIMULATE if self.paper else TrdEnv.REAL
            )
            
            if ret != RET_OK:
                return {'error': f'Failed to get account info: {data}'}
            
            account_info = data.iloc[0] if not data.empty else {}
            
            return {
                'buying_power': float(account_info.get('max_power_short', 0)),
                'portfolio_value': float(account_info.get('total_assets', 0)),
                'cash': float(account_info.get('cash', 0)),
                'market_val': float(account_info.get('market_val', 0)),
                'currency': account_info.get('currency', 'AUD'),
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
            ret, data = self.trade_ctx.position_list_query(
                trd_env=TrdEnv.SIMULATE if self.paper else TrdEnv.REAL
            )
            
            if ret != RET_OK:
                logger.error(f"Failed to get positions: {data}")
                return []
            
            position_list = []
            for _, position in data.iterrows():
                position_list.append({
                    'code': position.get('code'),
                    'name': position.get('stock_name'),
                    'qty': float(position.get('qty', 0)),
                    'market_val': float(position.get('market_val', 0)),
                    'nominal_price': float(position.get('nominal_price', 0)),
                    'unrealized_pl': float(position.get('unrealized_pl', 0)),
                    'unrealized_plpc': float(position.get('unrealized_plpc', 0)),
                    'today_pl': float(position.get('today_pl', 0)),
                    'currency': position.get('currency', 'AUD')
                })
            
            return position_list
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get latest quote for an ASX symbol.
        
        Args:
            symbol: ASX symbol (e.g., 'CBA.AX')
            
        Returns:
            Quote data dictionary
        """
        if not self.is_available():
            return {'error': 'Moomoo not available'}
        
        try:
            # Convert ASX symbol to Moomoo format (AU.symbol without .AX)
            if '.AX' in symbol:
                moomoo_symbol = f"AU.{symbol.replace('.AX', '')}"
            else:
                moomoo_symbol = f"AU.{symbol}"
            
            # Get market snapshot (includes bid/ask)
            ret, data = self.quote_ctx.get_market_snapshot([moomoo_symbol])
            
            if ret != RET_OK or data.empty:
                return {'error': f'Failed to get quote for {symbol}: {data}'}
            
            quote_data = data.iloc[0]
            
            return {
                'symbol': symbol,
                'moomoo_symbol': moomoo_symbol,
                'cur_price': float(quote_data.get('cur_price', 0)),
                'bid_price': float(quote_data.get('bid_price', 0)),
                'ask_price': float(quote_data.get('ask_price', 0)),
                'volume': int(quote_data.get('volume', 0)),
                'turnover': float(quote_data.get('turnover', 0)),
                'last_price': float(quote_data.get('last_price', 0)),
                'open_price': float(quote_data.get('open_price', 0)),
                'high_price': float(quote_data.get('high_price', 0)),
                'low_price': float(quote_data.get('low_price', 0)),
                'prev_close_price': float(quote_data.get('prev_close_price', 0)),
                'timestamp': datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return {'error': str(e)}
    
    def place_ml_order(self, 
                      symbol: str, 
                      ml_score_data: Dict,
                      portfolio_value: float = 10000.0) -> Dict[str, Any]:
        """
        Place an order based on ML trading score for ASX stocks.
        
        Args:
            symbol: ASX stock symbol (e.g., 'CBA.AX')
            ml_score_data: ML trading score data
            portfolio_value: Portfolio value for position sizing
            
        Returns:
            Order result dictionary
        """
        if not self.is_available():
            return {'error': 'Moomoo not available'}
        
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
            
            # Get current quote
            quote_data = self.get_latest_quote(symbol)
            if 'error' in quote_data:
                return {'error': f'Cannot get quote for {symbol}'}
            
            # Use current price for calculations
            current_price = quote_data.get('cur_price', 0)
            if current_price <= 0:
                return {'error': f'Invalid price for {symbol}'}
            
            # Calculate position size
            position_value = portfolio_value * position_size_pct
            qty = int(position_value / current_price)
            if qty <= 0:
                return {'error': f'Position size too small for {symbol}'}
            
            # Convert to Moomoo symbol format
            moomoo_symbol = quote_data.get('moomoo_symbol')
            if not moomoo_symbol:
                return {'error': f'Invalid symbol format for {symbol}'}
            
            # Determine order side
            if recommendation in ['BUY', 'WEAK_BUY', 'STRONG_BUY']:
                trd_side = TrdSide.BUY
            elif recommendation in ['SELL', 'WEAK_SELL', 'STRONG_SELL']:
                trd_side = TrdSide.SELL
            else:
                return {'status': 'skipped', 'reason': f'Unknown recommendation: {recommendation}'}
            
            # Place market order
            ret, data = self.trade_ctx.place_order(
                price=current_price,  # Use current price for market order
                qty=qty,
                code=moomoo_symbol,
                trd_side=trd_side,
                order_type=OrderType.MARKET,
                trd_env=TrdEnv.SIMULATE if self.paper else TrdEnv.REAL,
                remark=f"ML Score: {ml_score}"
            )
            
            if ret != RET_OK:
                return {'error': f'Failed to place order: {data}'}
            
            order_data = data.iloc[0] if not data.empty else {}
            order_id = order_data.get('order_id', 'unknown')
            
            # Track ML trade
            ml_trade_record = {
                'order_id': str(order_id),
                'symbol': symbol,
                'moomoo_symbol': moomoo_symbol,
                'side': trd_side.name.lower(),
                'qty': qty,
                'ml_score': ml_score,
                'recommendation': recommendation,
                'position_size_pct': position_size_pct,
                'estimated_price': current_price,
                'ml_score_data': ml_score_data,
                'timestamp': datetime.now().isoformat(),
                'status': 'submitted'
            }
            
            self.ml_trades.append(ml_trade_record)
            self._save_ml_trades()
            
            logger.info(f"ML order placed: {trd_side.name} {qty} shares of {symbol} (Score: {ml_score})")
            
            return {
                'status': 'submitted',
                'order_id': str(order_id),
                'symbol': symbol,
                'side': trd_side.name.lower(),
                'qty': qty,
                'ml_score': ml_score,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Error placing ML order for {symbol}: {e}")
            return {'error': str(e)}
    
    def execute_ml_trading_strategy(self, ml_scores: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Execute trading strategy based on ML scores for ASX banks.
        
        Args:
            ml_scores: Dictionary of ML scores {symbol: score_data}
            
        Returns:
            Summary of trading actions
        """
        if not self.is_available():
            return {'error': 'Moomoo not available'}
        
        logger.info("Executing ML trading strategy on ASX banks...")
        
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
        
        # Process each ASX bank
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
                    ret, data = self.trade_ctx.order_list_query(
                        order_id=trade['order_id'],
                        trd_env=TrdEnv.SIMULATE if self.paper else TrdEnv.REAL
                    )
                    
                    if ret == RET_OK and not data.empty:
                        order_info = data.iloc[0]
                        trade['current_status'] = order_info.get('order_status', 'unknown')
                        
                        if order_info.get('dealt_qty', 0) > 0:
                            trade['filled_price'] = float(order_info.get('dealt_avg_price', trade['estimated_price']))
                            
                            # Calculate P&L if we have current price
                            current_quote = self.get_latest_quote(trade['symbol'])
                            if 'error' not in current_quote:
                                current_price = current_quote.get('cur_price', 0)
                                
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
    
    def close_connections(self):
        """Close Moomoo API connections."""
        try:
            if self.quote_ctx:
                self.quote_ctx.close()
            if self.trade_ctx:
                self.trade_ctx.close()
            logger.info("Moomoo connections closed")
        except Exception as e:
            logger.error(f"Error closing Moomoo connections: {e}")
    
    def _save_ml_trades(self):
        """Save ML trades to file."""
        try:
            os.makedirs('data/moomoo', exist_ok=True)
            with open('data/moomoo/ml_trades.json', 'w') as f:
                json.dump(self.ml_trades, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving ML trades: {e}")
    
    def _load_ml_trades(self):
        """Load ML trades from file."""
        try:
            if os.path.exists('data/moomoo/ml_trades.json'):
                with open('data/moomoo/ml_trades.json', 'r') as f:
                    self.ml_trades = json.load(f)
            else:
                self.ml_trades = []
        except Exception as e:
            logger.error(f"Error loading ML trades: {e}")
            self.ml_trades = []

if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Initialize trader
    trader = MoomooMLTrader(paper=True)
    
    if trader.is_available():
        # Get account info
        account = trader.get_account_info()
        print("Account Info:", account)
        
        # Test quote for ASX bank
        quote = trader.get_latest_quote('CBA.AX')
        print("CBA Quote:", quote)
        
        # Mock ML score data
        mock_ml_score = {
            'overall_ml_score': 75.5,
            'trading_recommendation': 'BUY',
            'position_size_pct': 0.05,
            'risk_level': 'MEDIUM'
        }
        
        # Test order placement (paper trading)
        print("\nTesting order placement...")
        order_result = trader.place_ml_order('CBA.AX', mock_ml_score, 10000.0)
        print("Order Result:", order_result)
        
        # Get ML trade performance
        performance = trader.get_ml_trade_performance()
        print("ML Trade Performance:", performance)
        
        # Close connections
        trader.close_connections()
    else:
        print("Moomoo trading not available. Check OpenD installation and connection.")