# src/data_feed.py
"""
Data feed module for fetching free market data
Uses yfinance for stock data and web scraping for real-time prices
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json
import logging
from typing import Dict, List, Optional
import time
from functools import lru_cache
import os

# Import from parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config.settings import Settings
# from utils.cache_manager import CacheManager  # Optional caching - disabled for now

# Enhanced data validation import
try:
    from app.core.data_validator import DataValidator, ValidationResult
except ImportError:
    # Fallback if data_validator not available
    DataValidator = None
    ValidationResult = None

logger = logging.getLogger(__name__)

class ASXDataFeed:
    """Fetches market data from free sources"""
    
    def __init__(self):
        self.settings = Settings()
        # Initialize cache (disabled for now)
        self.cache = None  # CacheManager() - disabled
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Add data validation if available
        if DataValidator is not None:
            self.validator = DataValidator()
            self.enable_validation = True
        else:
            self.validator = None
            self.enable_validation = False
    
    def get_current_data(self, symbol: str) -> Dict:
        """Get current price and basic data for a symbol"""
        # Check cache (disabled for now)
        cache_key = f"current_{symbol}"
        cached_data = None  # self.cache.get(cache_key) if self.cache else None
        
        if cached_data:
            return cached_data
        
        try:
            # Try yfinance first
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current data
            current_data = {
                'symbol': symbol,
                'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'volume': info.get('volume', 0),
                'day_high': info.get('dayHigh', 0),
                'day_low': info.get('dayLow', 0),
                'prev_close': info.get('previousClose', 0),
                'open': info.get('open', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            # Calculate change
            if current_data['prev_close'] > 0:
                current_data['change'] = current_data['price'] - current_data['prev_close']
                current_data['change_percent'] = (current_data['change'] / current_data['prev_close']) * 100
            else:
                current_data['change'] = 0
                current_data['change_percent'] = 0
            
            # Cache disabled for now
            # if self.cache: self.cache.set(cache_key, current_data, expiry_minutes=5)
            
            return current_data
            
        except Exception as e:
            logger.error(f"Error fetching current data for {symbol}: {str(e)}")
            # Try alternative method
            return self._get_data_alternative(symbol)
    
    def _get_data_alternative(self, symbol: str) -> Dict:
        """Alternative method using web scraping"""
        try:
            # Remove .AX for some sites
            clean_symbol = symbol.replace('.AX', '')
            
            # Try Google Finance
            url = f"https://www.google.com/finance/quote/{clean_symbol}:ASX"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse price (this is an example - actual selectors may change)
                price_elem = soup.find('div', {'class': 'YMlKec fxKbKc'})
                if price_elem:
                    price = float(price_elem.text.strip().replace(',', ''))
                    
                    return {
                        'symbol': symbol,
                        'price': price,
                        'volume': 0,
                        'day_high': 0,
                        'day_low': 0,
                        'prev_close': 0,
                        'open': 0,
                        'market_cap': 0,
                        'pe_ratio': 0,
                        'dividend_yield': 0,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'web_scraping'
                    }
            
        except Exception as e:
            logger.error(f"Alternative data fetch failed for {symbol}: {str(e)}")
        
        # Return empty data as last resort
        return {
            'symbol': symbol,
            'price': 0,
            'error': 'Data temporarily unavailable',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_historical_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """Get historical price data"""
        cache_key = f"hist_{symbol}_{period}_{interval}"
        cached_data = None  # self.cache.get(cache_key) if self.cache else None
        
        if cached_data is not None:
            df = pd.DataFrame(cached_data)
            # Restore date index if it was cached with reset_index
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
            return df
        
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if not hist.empty:
                # Cache disabled - just return the data
                return hist
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
        
        return pd.DataFrame()
    
    def get_historical_data_validated(self, symbol: str, period: str = '1y') -> tuple:
        """Get historical data with validation"""
        try:
            # Get data using existing method
            data = self.get_historical_data(symbol, period)
            
            if data is None or data.empty:
                if ValidationResult is not None and DataValidator is not None:
                    from app.core.data_validator import DataQuality
                    validation = ValidationResult(
                        False, 
                        DataQuality.INVALID, 
                        ["No data available"], 
                        [], 
                        0.0
                    )
                else:
                    validation = {'error': 'No validation available'}
                return data, validation
            
            # Validate the data if validator is available
            if self.validator is not None:
                validation = self.validator.validate_market_data(data, symbol)
                
                if not validation.is_valid:
                    logger.warning(f"Data validation failed for {symbol}: {validation}")
                else:
                    logger.info(f"Data validation passed for {symbol}: {validation}")
            else:
                # Create a simple validation result if validator not available
                validation = {'is_valid': True, 'quality': 'unknown', 'confidence_score': 1.0}
            
            return data, validation
            
        except Exception as e:
            logger.error(f"Error in validated data fetch for {symbol}: {str(e)}")
            if ValidationResult is not None and DataValidator is not None:
                from app.core.data_validator import DataQuality
                validation = ValidationResult(
                    False, 
                    DataQuality.INVALID, 
                    [str(e)], 
                    [], 
                    0.0
                )
            else:
                validation = {'error': str(e)}
            return None, validation
    
    def get_intraday_data(self, symbol: str) -> pd.DataFrame:
        """Get intraday 5-minute data"""
        return self.get_historical_data(symbol, period="1d", interval="5m")
    
    def get_market_data(self) -> Dict:
        """Get overall market data (ASX indices)"""
        market_data = {}
        
        for index_name, index_symbol in self.settings.MARKET_INDICES.items():
            try:
                ticker = yf.Ticker(index_symbol)
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Open'].iloc[0]
                    
                    market_data[index_name] = {
                        'value': current,
                        'change': current - prev,
                        'change_percent': ((current - prev) / prev) * 100,
                        'trend': 'up' if current > prev else 'down'
                    }
                    
            except Exception as e:
                logger.error(f"Error fetching market data for {index_name}: {str(e)}")
                market_data[index_name] = {'error': str(e)}
        
        # Determine overall market trend
        if 'ASX200' in market_data and 'value' in market_data['ASX200']:
            asx200_change = market_data['ASX200']['change_percent']
            if asx200_change > 0.5:
                market_data['trend'] = 'bullish'
            elif asx200_change < -0.5:
                market_data['trend'] = 'bearish'
            else:
                market_data['trend'] = 'neutral'
        else:
            market_data['trend'] = 'unknown'
        
        return market_data
    
    def get_company_info(self, symbol: str) -> Dict:
        """Get company fundamental data"""
        cache_key = f"info_{symbol}"
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract relevant fundamental data
            company_data = {
                'symbol': symbol,
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'price_to_book': info.get('priceToBook', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'dividend_rate': info.get('dividendRate', 0),
                'payout_ratio': info.get('payoutRatio', 0),
                'profit_margin': info.get('profitMargins', 0),
                'operating_margin': info.get('operatingMargins', 0),
                'roe': info.get('returnOnEquity', 0),
                'roa': info.get('returnOnAssets', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_ratio': info.get('currentRatio', 0),
                'beta': info.get('beta', 0),
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0),
                'analyst_rating': info.get('recommendationKey', ''),
                'analyst_count': info.get('numberOfAnalystOpinions', 0)
            }
            
            # Cache disabled for now - longer as fundamental data doesn't change often
            # self.cache.set(cache_key, company_data, expiry_minutes=240)
            
            return company_data
            
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {str(e)}")
            return {'symbol': symbol, 'error': str(e)}
    
    def get_options_data(self, symbol: str) -> Dict:
        """Get options data for sentiment analysis"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get options expiration dates
            expirations = ticker.options
            
            if expirations:
                # Get nearest expiration
                nearest_expiry = expirations[0]
                
                # Get options chain
                opt_chain = ticker.option_chain(nearest_expiry)
                calls = opt_chain.calls
                puts = opt_chain.puts
                
                # Calculate put/call ratio
                call_volume = calls['volume'].sum()
                put_volume = puts['volume'].sum()
                
                put_call_ratio = put_volume / call_volume if call_volume > 0 else 0
                
                # Calculate implied volatility
                call_iv = calls['impliedVolatility'].mean()
                put_iv = puts['impliedVolatility'].mean()
                
                return {
                    'put_call_ratio': put_call_ratio,
                    'call_volume': call_volume,
                    'put_volume': put_volume,
                    'avg_call_iv': call_iv,
                    'avg_put_iv': put_iv,
                    'sentiment': 'bullish' if put_call_ratio < 0.7 else 'bearish' if put_call_ratio > 1.3 else 'neutral'
                }
                
        except Exception as e:
            logger.error(f"Error fetching options data for {symbol}: {str(e)}")
            
        return {
            'put_call_ratio': 0,
            'sentiment': 'unknown'
        }
    
    def get_insider_trading(self, symbol: str) -> List[Dict]:
        """Get insider trading data (from yfinance)"""
        try:
            ticker = yf.Ticker(symbol)
            insider_trades = ticker.insider_transactions
            
            if isinstance(insider_trades, pd.DataFrame) and not insider_trades.empty:
                # Convert to list of dicts for easier processing
                trades = insider_trades.to_dict('records')
                return trades[-10:]  # Last 10 trades
                
        except Exception as e:
            logger.error(f"Error fetching insider trading for {symbol}: {str(e)}")
            
        return []
    
    def get_institutional_holders(self, symbol: str) -> Dict:
        """Get institutional ownership data"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get institutional holders
            inst_holders = ticker.institutional_holders
            
            if isinstance(inst_holders, pd.DataFrame) and not inst_holders.empty:
                # Calculate metrics
                total_inst_ownership = inst_holders['% Out'].sum()
                top_holder = inst_holders.iloc[0]['Holder'] if len(inst_holders) > 0 else 'Unknown'
                
                return {
                    'institutional_ownership_pct': total_inst_ownership,
                    'top_institutional_holder': top_holder,
                    'number_of_institutions': len(inst_holders),
                    'recent_activity': 'increasing' if total_inst_ownership > 50 else 'stable'
                }
                
        except Exception as e:
            logger.error(f"Error fetching institutional data for {symbol}: {str(e)}")
            
        return {
            'institutional_ownership_pct': 0,
            'recent_activity': 'unknown'
        }
    
    def get_peer_comparison(self, symbol: str) -> Dict:
        """Compare with peer banks"""
        peer_data = {}
        
        for peer in self.settings.BANK_SYMBOLS:
            if peer != symbol:
                try:
                    peer_info = self.get_company_info(peer)
                    peer_data[peer] = {
                        'pe_ratio': peer_info.get('pe_ratio', 0),
                        'dividend_yield': peer_info.get('dividend_yield', 0),
                        'roe': peer_info.get('roe', 0),
                        'price_to_book': peer_info.get('price_to_book', 0)
                    }
                except:
                    continue
        
        return peer_data
    
    def check_dividend_dates(self, symbol: str) -> Dict:
        """Check for upcoming dividend dates"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get dividend history
            dividends = ticker.dividends
            
            if not dividends.empty:
                # Get last dividend
                last_div_date = dividends.index[-1]
                last_div_amount = dividends.iloc[-1]
                
                # Estimate next dividend (usually 6 months for ASX banks)
                next_div_estimate = last_div_date + timedelta(days=180)
                
                return {
                    'last_dividend_date': last_div_date.strftime('%Y-%m-%d'),
                    'last_dividend_amount': last_div_amount,
                    'estimated_next_dividend': next_div_estimate.strftime('%Y-%m-%d'),
                    'days_to_next': (next_div_estimate - datetime.now()).days,
                    'dividend_soon': (next_div_estimate - datetime.now()).days < 30
                }
                
        except Exception as e:
            logger.error(f"Error checking dividend dates for {symbol}: {str(e)}")
            
        return {
            'dividend_soon': False
        }
    
    def get_economic_calendar(self) -> List[Dict]:
        """Get upcoming economic events that might impact banks"""
        # For free version, we'll return static important dates
        # In production, you could scrape from RBA or economic calendar sites
        
        events = []
        current_date = datetime.now()
        
        # RBA meetings are first Tuesday of each month (except January)
        for month in range(current_date.month, current_date.month + 3):
            # Calculate first Tuesday
            first_day = datetime(current_date.year, month % 12 + 1, 1)
            days_ahead = 1 - first_day.weekday()  # Tuesday is 1
            if days_ahead <= 0:
                days_ahead += 7
            first_tuesday = first_day + timedelta(days_ahead)
            
            if first_tuesday > current_date:
                events.append({
                    'date': first_tuesday.strftime('%Y-%m-%d'),
                    'event': 'RBA Interest Rate Decision',
                    'importance': 'High',
                    'impact': 'Major impact on bank margins'
                })
        
        return events