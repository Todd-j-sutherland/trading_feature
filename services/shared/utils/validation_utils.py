"""Validation utilities for trading services"""

import re
from typing import Optional, List, Any
from datetime import datetime, timedelta


# ASX stock symbol pattern
ASX_SYMBOL_PATTERN = re.compile(r'^[A-Z]{3,4}\.AX$')

# Supported bank symbols for this trading system
SUPPORTED_BANK_SYMBOLS = {
    'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 
    'MQG.AX', 'SUN.AX', 'QBE.AX'
}

# All supported symbols (can be extended)
ALL_SUPPORTED_SYMBOLS = SUPPORTED_BANK_SYMBOLS.union({
    'BOQ.AX', 'BEN.AX', 'AMP.AX', 'IFL.AX', 'MPG.AX'
})


def validate_symbol(symbol: str, strict: bool = False) -> bool:
    """
    Validate stock symbol format
    
    Args:
        symbol: Stock symbol to validate
        strict: If True, only allow supported bank symbols
    
    Returns:
        True if valid, False otherwise
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Check format
    if not ASX_SYMBOL_PATTERN.match(symbol):
        return False
    
    # Check if in supported list (if strict mode)
    if strict:
        return symbol in SUPPORTED_BANK_SYMBOLS
    
    return True


def validate_timestamp(timestamp: Any, max_age_hours: int = 24) -> bool:
    """
    Validate timestamp format and age
    
    Args:
        timestamp: Timestamp to validate (str, datetime, or float)
        max_age_hours: Maximum age in hours
    
    Returns:
        True if valid and recent, False otherwise
    """
    try:
        # Convert to datetime if needed
        if isinstance(timestamp, str):
            # Try ISO format first
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                # Try other common formats
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f'
                ]
                dt = None
                for fmt in formats:
                    try:
                        dt = datetime.strptime(timestamp, fmt)
                        break
                    except ValueError:
                        continue
                if dt is None:
                    return False
        elif isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            return False
        
        # Check age
        max_age = timedelta(hours=max_age_hours)
        age = datetime.now() - dt
        
        return age <= max_age
        
    except Exception:
        return False


def validate_price(price: Any, min_price: float = 0.01, max_price: float = 1000.0) -> bool:
    """
    Validate price value
    
    Args:
        price: Price to validate
        min_price: Minimum allowed price
        max_price: Maximum allowed price
    
    Returns:
        True if valid, False otherwise
    """
    try:
        price_float = float(price)
        return min_price <= price_float <= max_price
    except (ValueError, TypeError):
        return False


def validate_confidence(confidence: Any) -> bool:
    """
    Validate confidence score (must be between 0 and 1)
    
    Args:
        confidence: Confidence score to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        conf_float = float(confidence)
        return 0.0 <= conf_float <= 1.0
    except (ValueError, TypeError):
        return False


def validate_sentiment(sentiment: Any) -> bool:
    """
    Validate sentiment score (must be between -1 and 1)
    
    Args:
        sentiment: Sentiment score to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        sentiment_float = float(sentiment)
        return -1.0 <= sentiment_float <= 1.0
    except (ValueError, TypeError):
        return False


def validate_percentage(percentage: Any, min_pct: float = -100.0, max_pct: float = 100.0) -> bool:
    """
    Validate percentage value
    
    Args:
        percentage: Percentage to validate
        min_pct: Minimum allowed percentage
        max_pct: Maximum allowed percentage
    
    Returns:
        True if valid, False otherwise
    """
    try:
        pct_float = float(percentage)
        return min_pct <= pct_float <= max_pct
    except (ValueError, TypeError):
        return False


def validate_trading_action(action: str) -> bool:
    """
    Validate trading action
    
    Args:
        action: Trading action to validate
    
    Returns:
        True if valid, False otherwise
    """
    valid_actions = {'STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL'}
    return action in valid_actions


class ValidationError(Exception):
    """Custom validation error"""
    pass


class DataValidator:
    """Comprehensive data validator for trading services"""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.errors = []
        self.warnings = []
    
    def reset(self):
        """Reset validation state"""
        self.errors.clear()
        self.warnings.clear()
    
    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)
    
    def validate_trading_signal(self, signal_data: dict) -> bool:
        """Validate trading signal data"""
        self.reset()
        
        # Required fields
        required_fields = ['symbol', 'action', 'confidence']
        for field in required_fields:
            if field not in signal_data:
                self.add_error(f"Missing required field: {field}")
        
        # Validate symbol
        if 'symbol' in signal_data:
            if not validate_symbol(signal_data['symbol'], self.strict_mode):
                self.add_error(f"Invalid symbol: {signal_data['symbol']}")
        
        # Validate action
        if 'action' in signal_data:
            if not validate_trading_action(signal_data['action']):
                self.add_error(f"Invalid action: {signal_data['action']}")
        
        # Validate confidence
        if 'confidence' in signal_data:
            if not validate_confidence(signal_data['confidence']):
                self.add_error(f"Invalid confidence: {signal_data['confidence']}")
        
        # Optional fields validation
        if 'current_price' in signal_data:
            if not validate_price(signal_data['current_price']):
                self.add_error(f"Invalid current_price: {signal_data['current_price']}")
        
        if 'sentiment_score' in signal_data:
            if not validate_sentiment(signal_data['sentiment_score']):
                self.add_error(f"Invalid sentiment_score: {signal_data['sentiment_score']}")
        
        if 'timestamp' in signal_data:
            if not validate_timestamp(signal_data['timestamp']):
                self.add_warning(f"Old or invalid timestamp: {signal_data['timestamp']}")
        
        return len(self.errors) == 0
    
    def validate_sentiment_data(self, sentiment_data: dict) -> bool:
        """Validate sentiment analysis data"""
        self.reset()
        
        # Required fields
        required_fields = ['symbol', 'overall_sentiment', 'confidence']
        for field in required_fields:
            if field not in sentiment_data:
                self.add_error(f"Missing required field: {field}")
        
        # Validate symbol
        if 'symbol' in sentiment_data:
            if not validate_symbol(sentiment_data['symbol']):
                self.add_error(f"Invalid symbol: {sentiment_data['symbol']}")
        
        # Validate sentiment
        if 'overall_sentiment' in sentiment_data:
            if not validate_sentiment(sentiment_data['overall_sentiment']):
                self.add_error(f"Invalid sentiment: {sentiment_data['overall_sentiment']}")
        
        # Validate confidence
        if 'confidence' in sentiment_data:
            if not validate_confidence(sentiment_data['confidence']):
                self.add_error(f"Invalid confidence: {sentiment_data['confidence']}")
        
        # Validate news count
        if 'news_count' in sentiment_data:
            try:
                count = int(sentiment_data['news_count'])
                if count < 0:
                    self.add_error(f"Invalid news_count: {count}")
                elif count == 0:
                    self.add_warning("No news articles found")
            except (ValueError, TypeError):
                self.add_error(f"Invalid news_count type: {sentiment_data['news_count']}")
        
        return len(self.errors) == 0
    
    def validate_position_data(self, position_data: dict) -> bool:
        """Validate position data"""
        self.reset()
        
        # Required fields
        required_fields = ['symbol', 'shares', 'entry_price', 'position_size']
        for field in required_fields:
            if field not in position_data:
                self.add_error(f"Missing required field: {field}")
        
        # Validate symbol
        if 'symbol' in position_data:
            if not validate_symbol(position_data['symbol']):
                self.add_error(f"Invalid symbol: {position_data['symbol']}")
        
        # Validate shares
        if 'shares' in position_data:
            try:
                shares = int(position_data['shares'])
                if shares <= 0:
                    self.add_error(f"Invalid shares: {shares}")
            except (ValueError, TypeError):
                self.add_error(f"Invalid shares type: {position_data['shares']}")
        
        # Validate prices
        price_fields = ['entry_price', 'current_price', 'stop_loss', 'profit_target']
        for field in price_fields:
            if field in position_data and position_data[field] is not None:
                if not validate_price(position_data[field]):
                    self.add_error(f"Invalid {field}: {position_data[field]}")
        
        # Validate position size
        if 'position_size' in position_data:
            try:
                size = float(position_data['position_size'])
                if size <= 0:
                    self.add_error(f"Invalid position_size: {size}")
                elif size > 50000:  # Warning for large positions
                    self.add_warning(f"Large position size: ${size:,.0f}")
            except (ValueError, TypeError):
                self.add_error(f"Invalid position_size type: {position_data['position_size']}")
        
        return len(self.errors) == 0
    
    def get_validation_summary(self) -> dict:
        """Get validation summary"""
        return {
            'valid': len(self.errors) == 0,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy()
        }


# Global validator instance
default_validator = DataValidator()


def validate_trading_signal_data(data: dict, strict: bool = False) -> dict:
    """Convenience function to validate trading signal data"""
    validator = DataValidator(strict_mode=strict)
    is_valid = validator.validate_trading_signal(data)
    return validator.get_validation_summary()


def validate_request_data(data: dict, required_fields: List[str]) -> dict:
    """Validate request data has required fields"""
    errors = []
    warnings = []
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None:
            warnings.append(f"Field is None: {field}")
        elif data[field] == "":
            warnings.append(f"Field is empty: {field}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }
