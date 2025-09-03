"""
Alpaca Trading Simulation System

Integrates with Alpaca API for paper trading using ML trading scores.
Provides backtesting and live paper trading capabilities.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

# Try to import Alpaca trade API
try:
    import alpaca_trade_api as tradeapi
    from alpaca_trade_api.rest import APIError
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logger.warning("Alpaca Trade API not available. Install with: pip install alpaca-trade-api")

class AlpacaTradingSimulator:
    """
    Alpaca-based trading simulator using ML trading scores.
    """
    
    def __init__(self, paper_trading: bool = True):
        """
        Initialize Alpaca trading simulator.
        
        Args:
            paper_trading: Whether to use paper trading (default: True)
        """
        self.paper_trading = paper_trading
        self.api = None
        self.account = None
        self.positions = {}
        self.orders = []
        
        if not ALPACA_AVAILABLE:
            logger.error("Alpaca API not available")
            return
        
        # Get API credentials from environment
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_SECRET_KEY')  # Changed from ALPACA_API_SECRET
        base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets' if paper_trading else 'https://api.alpaca.markets')
        
        if not api_key or not api_secret:
            logger.error("Alpaca API credentials not found in environment variables")
            logger.info("Set ALPACA_API_KEY and ALPACA_API_SECRET environment variables")
            return
        
        try:
            self.api = tradeapi.REST(
                api_key,
                api_secret,
                base_url,
                api_version='v2'
            )
            
            # Test connection and get account info
            self.account = self.api.get_account()
            logger.info(f"Connected to Alpaca {'Paper' if paper_trading else 'Live'} Trading")
            logger.info(f"Account equity: ${float(self.account.equity):,.2f}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Alpaca: {e}")
            self.api = None
    
    def is_connected(self) -> bool:
        """Check if connected to Alpaca API."""
        return self.api is not None and self.account is not None
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information."""
        if not self.is_connected():
            return {'error': 'Not connected to Alpaca'}
        
        try:
            account = self.api.get_account()
            return {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'day_trade_count': int(account.daytrade_count),
                'pattern_day_trader': account.pattern_day_trader,
                'trading_blocked': account.trading_blocked,
                'account_blocked': account.account_blocked
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {'error': str(e)}
    
    def get_positions(self) -> Dict[str, Dict]:
        """Get current positions."""
        if not self.is_connected():
            return {'error': 'Not connected to Alpaca'}
        
        try:
            positions = self.api.list_positions()
            position_data = {}
            
            for position in positions:
                symbol = position.symbol
                position_data[symbol] = {
                    'symbol': symbol,
                    'qty': float(position.qty),
                    'side': position.side,
                    'market_value': float(position.market_value),
                    'cost_basis': float(position.cost_basis),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc),
                    'current_price': float(position.current_price) if position.current_price else 0,
                    'lastday_price': float(position.lastday_price) if position.lastday_price else 0
                }
            
            return position_data
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {'error': str(e)}
    
    def convert_asx_to_us_symbol(self, asx_symbol: str) -> str:
        """
        Convert ASX symbol to US equivalent for Alpaca trading.
        
        Note: This is a placeholder. In reality, you'd either:
        1. Trade ASX stocks through a broker that supports them
        2. Trade US bank ETFs as proxies
        3. Use CFDs or other derivatives
        
        For demo purposes, we'll map to US bank stocks.
        """
        symbol_mapping = {
            'CBA.AX': 'BAC',   # Bank of America (proxy for Commonwealth Bank)
            'WBC.AX': 'WFC',   # Wells Fargo (proxy for Westpac)
            'ANZ.AX': 'JPM',   # JPMorgan Chase (proxy for ANZ)
            'NAB.AX': 'C',     # Citigroup (proxy for NAB)
            'MQG.AX': 'GS'     # Goldman Sachs (proxy for Macquarie)
        }
        
        us_symbol = symbol_mapping.get(asx_symbol, asx_symbol.replace('.AX', ''))
        logger.info(f"Mapped {asx_symbol} to {us_symbol} for US trading")
        return us_symbol
    
    def place_ml_based_order(self, 
                           symbol: str, 
                           ml_score_data: Dict,
                           max_position_value: float = 10000) -> Dict[str, Any]:
        """
        Place an order based on ML trading score.
        
        Args:
            symbol: Stock symbol (ASX format)
            ml_score_data: ML trading score data
            max_position_value: Maximum position value in USD
            
        Returns:
            Order result dictionary
        """
        if not self.is_connected():
            return {'error': 'Not connected to Alpaca'}
        
        # Convert ASX symbol to US equivalent
        us_symbol = self.convert_asx_to_us_symbol(symbol)
        
        # Get trading recommendation and position size
        recommendation = ml_score_data.get('trading_recommendation', 'HOLD')
        ml_score = ml_score_data.get('overall_ml_score', 0)
        position_size_pct = ml_score_data.get('position_size_pct', 0.05)
        risk_level = ml_score_data.get('risk_level', 'HIGH')
        
        logger.info(f"Processing ML-based order for {symbol} -> {us_symbol}")
        logger.info(f"Recommendation: {recommendation}, ML Score: {ml_score:.2f}, Risk: {risk_level}")
        
        # Don't trade if score is too low or risk is too high
        if ml_score < 40:
            return {
                'status': 'skipped',
                'reason': f'ML score too low: {ml_score:.2f}',
                'symbol': symbol,
                'us_symbol': us_symbol
            }
        
        if risk_level == 'HIGH' and ml_score < 60:
            return {
                'status': 'skipped',
                'reason': f'High risk with moderate score: {ml_score:.2f}',
                'symbol': symbol,
                'us_symbol': us_symbol
            }
        
        # Only process buy/sell recommendations
        if recommendation not in ['BUY', 'STRONG_BUY', 'SELL', 'STRONG_SELL']:
            return {
                'status': 'skipped',
                'reason': f'No actionable recommendation: {recommendation}',
                'symbol': symbol,
                'us_symbol': us_symbol
            }
        
        try:
            # Get current market price
            quote = self.api.get_latest_quote(us_symbol)
            current_price = float(quote.ask_price) if quote.ask_price else float(quote.bid_price)
            
            if current_price == 0:
                return {
                    'status': 'error',
                    'reason': 'Could not get current price',
                    'symbol': symbol,
                    'us_symbol': us_symbol
                }
            
            # Calculate position size
            account_info = self.get_account_info()
            if 'error' in account_info:
                return account_info
            
            available_cash = min(account_info['buying_power'], max_position_value)
            position_value = available_cash * position_size_pct
            
            # Calculate number of shares
            shares = int(position_value / current_price)
            
            if shares == 0:
                return {
                    'status': 'skipped',
                    'reason': 'Position size too small (less than 1 share)',
                    'symbol': symbol,
                    'us_symbol': us_symbol,
                    'calculated_value': position_value,
                    'current_price': current_price
                }
            
            # Determine order side
            side = 'buy' if recommendation in ['BUY', 'STRONG_BUY'] else 'sell'
            
            # Place the order
            order = self.api.submit_order(
                symbol=us_symbol,
                qty=shares,
                side=side,
                type='market',
                time_in_force='day',
                client_order_id=f"ml_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            order_result = {
                'status': 'submitted',
                'order_id': order.id,
                'symbol': symbol,
                'us_symbol': us_symbol,
                'side': side,
                'qty': shares,
                'estimated_value': shares * current_price,
                'ml_score': ml_score,
                'recommendation': recommendation,
                'risk_level': risk_level,
                'current_price': current_price,
                'position_size_pct': position_size_pct,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Order submitted: {side} {shares} shares of {us_symbol} at ~${current_price:.2f}")
            return order_result
            
        except APIError as e:
            logger.error(f"Alpaca API error: {e}")
            return {
                'status': 'error',
                'reason': f'Alpaca API error: {str(e)}',
                'symbol': symbol,
                'us_symbol': us_symbol
            }
        except Exception as e:
            logger.error(f"Unexpected error placing order: {e}")
            return {
                'status': 'error',
                'reason': f'Unexpected error: {str(e)}',
                'symbol': symbol,
                'us_symbol': us_symbol
            }
    
    def execute_ml_trading_strategy(self, 
                                  ml_scores: Dict[str, Dict],
                                  max_total_exposure: float = 50000) -> Dict[str, Any]:
        """
        Execute trading strategy based on ML scores for multiple banks.
        
        Args:
            ml_scores: Dictionary of ML scores {symbol: score_data}
            max_total_exposure: Maximum total exposure in USD
            
        Returns:
            Execution results
        """
        if not self.is_connected():
            return {'error': 'Not connected to Alpaca'}
        
        logger.info("Executing ML trading strategy...")
        
        results = {
            'orders_submitted': [],
            'orders_skipped': [],
            'errors': [],
            'summary': {}
        }
        
        # Filter out summary data
        bank_scores = {k: v for k, v in ml_scores.items() if not k.startswith('_')}
        
        # Sort by ML score (highest first)
        sorted_banks = sorted(
            bank_scores.items(),
            key=lambda x: x[1].get('overall_ml_score', 0),
            reverse=True
        )
        
        total_exposure = 0
        max_per_position = max_total_exposure / len(sorted_banks) if sorted_banks else max_total_exposure
        
        for symbol, score_data in sorted_banks:
            if total_exposure >= max_total_exposure:
                results['orders_skipped'].append({
                    'symbol': symbol,
                    'reason': 'Maximum total exposure reached'
                })
                continue
            
            # Adjust max position size based on remaining capacity
            remaining_capacity = max_total_exposure - total_exposure
            position_limit = min(max_per_position, remaining_capacity)
            
            order_result = self.place_ml_based_order(symbol, score_data, position_limit)
            
            if order_result.get('status') == 'submitted':
                results['orders_submitted'].append(order_result)
                total_exposure += order_result.get('estimated_value', 0)
            elif order_result.get('status') == 'skipped':
                results['orders_skipped'].append(order_result)
            else:
                results['errors'].append(order_result)
        
        # Generate summary
        results['summary'] = {
            'total_orders_submitted': len(results['orders_submitted']),
            'total_orders_skipped': len(results['orders_skipped']),
            'total_errors': len(results['errors']),
            'total_estimated_exposure': total_exposure,
            'max_exposure_limit': max_total_exposure,
            'execution_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Strategy execution complete: {results['summary']['total_orders_submitted']} orders submitted")
        return results
    
    def get_portfolio_performance(self) -> Dict[str, Any]:
        """Get portfolio performance metrics."""
        if not self.is_connected():
            return {'error': 'Not connected to Alpaca'}
        
        try:
            # Get account info
            account = self.api.get_account()
            
            # Get portfolio history
            portfolio_history = self.api.get_portfolio_history(
                period='1M',
                timeframe='1D'
            )
            
            if not portfolio_history.equity:
                return {'error': 'No portfolio history available'}
            
            # Calculate performance metrics
            initial_value = portfolio_history.equity[0]
            current_value = portfolio_history.equity[-1]
            
            total_return = (current_value - initial_value) / initial_value
            total_return_pct = total_return * 100
            
            # Calculate daily returns
            daily_returns = []
            for i in range(1, len(portfolio_history.equity)):
                daily_return = (portfolio_history.equity[i] - portfolio_history.equity[i-1]) / portfolio_history.equity[i-1]
                daily_returns.append(daily_return)
            
            # Performance metrics
            import numpy as np
            avg_daily_return = np.mean(daily_returns) if daily_returns else 0
            volatility = np.std(daily_returns) if daily_returns else 0
            sharpe_ratio = (avg_daily_return / volatility) * np.sqrt(252) if volatility > 0 else 0
            
            # Max drawdown
            peak = portfolio_history.equity[0]
            max_drawdown = 0
            for value in portfolio_history.equity:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return {
                'current_equity': float(account.equity),
                'initial_equity': initial_value,
                'total_return': round(total_return, 4),
                'total_return_pct': round(total_return_pct, 2),
                'daily_avg_return': round(avg_daily_return * 100, 3),
                'volatility': round(volatility * 100, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown * 100, 2),
                'unrealized_pl': float(account.unrealized_pl),
                'unrealized_plpc': float(account.unrealized_plpc),
                'day_trade_count': int(account.daytrade_count),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio performance: {e}")
            return {'error': str(e)}
    
    def close_all_positions(self) -> Dict[str, Any]:
        """Close all open positions."""
        if not self.is_connected():
            return {'error': 'Not connected to Alpaca'}
        
        try:
            positions = self.api.list_positions()
            
            if not positions:
                return {'message': 'No positions to close'}
            
            closed_positions = []
            errors = []
            
            for position in positions:
                try:
                    # Create close order
                    close_order = self.api.submit_order(
                        symbol=position.symbol,
                        qty=abs(int(float(position.qty))),
                        side='sell' if float(position.qty) > 0 else 'buy',
                        type='market',
                        time_in_force='day',
                        client_order_id=f"close_{position.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                    
                    closed_positions.append({
                        'symbol': position.symbol,
                        'qty': float(position.qty),
                        'market_value': float(position.market_value),
                        'unrealized_pl': float(position.unrealized_pl),
                        'close_order_id': close_order.id
                    })
                    
                except Exception as e:
                    errors.append({
                        'symbol': position.symbol,
                        'error': str(e)
                    })
            
            return {
                'closed_positions': closed_positions,
                'errors': errors,
                'total_closed': len(closed_positions),
                'total_errors': len(errors)
            }
            
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
            return {'error': str(e)}

def setup_alpaca_credentials():
    """Provide instructions for setting up Alpaca credentials."""
    print("""
🏢 Alpaca Trading Setup Instructions:

1. Sign up for Alpaca paper trading account:
   https://alpaca.markets/

2. Get your API credentials from the dashboard

3. Set environment variables:
   export ALPACA_API_KEY="your_api_key_here"
   export ALPACA_API_SECRET="your_api_secret_here"
   export ALPACA_BASE_URL="https://paper-api.alpaca.markets"

4. Install Alpaca API:
   pip install alpaca-trade-api

5. For production trading, change base URL to:
   export ALPACA_BASE_URL="https://api.alpaca.markets"

⚠️  IMPORTANT: Always test with paper trading first!
""")

if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    if not ALPACA_AVAILABLE:
        setup_alpaca_credentials()
    else:
        simulator = AlpacaTradingSimulator(paper_trading=True)
        
        if simulator.is_connected():
            account_info = simulator.get_account_info()
            print(f"Account Info: {json.dumps(account_info, indent=2)}")
        else:
            print("Not connected to Alpaca. Check your credentials.")
