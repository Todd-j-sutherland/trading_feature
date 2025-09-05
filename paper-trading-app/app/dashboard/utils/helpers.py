"""
Utility functions for the dashboard
Common helper functions, formatters, and data processors
"""

import os
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

from ..utils.logging_config import setup_dashboard_logger, log_error_with_context

logger = setup_dashboard_logger(__name__)

def format_sentiment_score(score: float) -> Tuple[str, str]:
    """
    Format sentiment score with color class
    
    Args:
        score: Sentiment score (-1 to 1)
    
    Returns:
        Tuple of (formatted_score, css_class)
    """
    try:
        if score > 0.2:
            return f"+{score:.3f}", "status-positive"
        elif score < -0.2:
            return f"{score:.3f}", "status-negative"
        else:
            return f"{score:.3f}", "status-neutral"
    except Exception as e:
        log_error_with_context(logger, e, "formatting sentiment score", score=score)
        return "N/A", "status-neutral"

def get_confidence_level(confidence: float) -> Tuple[str, str]:
    """
    Get confidence level description and CSS class
    
    Args:
        confidence: Confidence score (0 to 1)
    
    Returns:
        Tuple of (level_description, css_class)
    """
    try:
        if confidence >= 0.8:
            return "HIGH", "confidence-high"
        elif confidence >= 0.6:
            return "MEDIUM", "confidence-medium"
        else:
            return "LOW", "confidence-low"
    except Exception as e:
        log_error_with_context(logger, e, "getting confidence level", confidence=confidence)
        return "UNKNOWN", "confidence-low"

def format_timestamp(timestamp: str, format_type: str = "datetime") -> str:
    """
    Format timestamp string for display
    
    Args:
        timestamp: ISO timestamp string
        format_type: Type of formatting ("date", "time", "datetime")
    
    Returns:
        Formatted timestamp string
    """
    if not timestamp or timestamp == 'Unknown':
        return 'Unknown'
    
    try:
        # Parse timestamp
        if 'T' in timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        # Format based on type
        if format_type == "date":
            return dt.strftime('%Y-%m-%d')
        elif format_type == "time":
            return dt.strftime('%H:%M:%S')
        else:  # datetime
            return dt.strftime('%Y-%m-%d %H:%M')
            
    except Exception as e:
        log_error_with_context(logger, e, "formatting timestamp", 
                             timestamp=timestamp, format_type=format_type)
        return timestamp[:16] if len(timestamp) > 16 else timestamp

def get_trading_recommendation(sentiment: float, confidence: float) -> Tuple[str, str]:
    """
    Get trading recommendation based on sentiment and confidence
    
    Args:
        sentiment: Sentiment score (-1 to 1)
        confidence: Confidence level (0 to 1)
    
    Returns:
        Tuple of (recommendation, css_class)
    """
    try:
        # Low confidence = no action
        if confidence < 0.5:
            return "HOLD", "status-neutral"
        
        # High confidence recommendations
        if confidence >= 0.8:
            if sentiment > 0.3:
                return "STRONG BUY", "status-positive"
            elif sentiment < -0.3:
                return "STRONG SELL", "status-negative"
            elif sentiment > 0.1:
                return "BUY", "status-positive"
            elif sentiment < -0.1:
                return "SELL", "status-negative"
            else:
                return "HOLD", "status-neutral"
        
        # Medium confidence recommendations
        else:
            if sentiment > 0.2:
                return "BUY", "status-positive"
            elif sentiment < -0.2:
                return "SELL", "status-negative"
            else:
                return "HOLD", "status-neutral"
                
    except Exception as e:
        log_error_with_context(logger, e, "getting trading recommendation", 
                             sentiment=sentiment, confidence=confidence)
        return "HOLD", "status-neutral"

def calculate_position_size(confidence: float, base_size: float = 1000) -> float:
    """
    Calculate position size based on confidence level
    
    Args:
        confidence: Confidence level (0 to 1)
        base_size: Base position size in dollars
    
    Returns:
        Recommended position size
    """
    try:
        if confidence >= 0.8:
            return base_size * 1.0  # Full position
        elif confidence >= 0.6:
            return base_size * 0.7  # 70% position
        elif confidence >= 0.5:
            return base_size * 0.5  # 50% position
        else:
            return 0.0  # No position
    except Exception as e:
        log_error_with_context(logger, e, "calculating position size", 
                             confidence=confidence, base_size=base_size)
        return 0.0

def validate_data_completeness(data: Dict, required_fields: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that data contains all required fields
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
    
    Returns:
        Tuple of (is_valid, missing_fields)
    """
    missing_fields = []
    
    try:
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        is_valid = len(missing_fields) == 0
        
        if not is_valid:
            logger.warning(f"Data validation failed - Missing fields: {missing_fields}")
        
        return is_valid, missing_fields
        
    except Exception as e:
        log_error_with_context(logger, e, "validating data completeness", 
                             required_fields=required_fields)
        return False, required_fields

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, handling division by zero
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division by zero
    
    Returns:
        Division result or default value
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except Exception as e:
        log_error_with_context(logger, e, "safe division", 
                             numerator=numerator, denominator=denominator)
        return default

def get_color_for_sentiment(sentiment: float, opacity: float = 1.0) -> str:
    """
    Get color code for sentiment value
    
    Args:
        sentiment: Sentiment score (-1 to 1)
        opacity: Color opacity (0 to 1)
    
    Returns:
        RGBA color string
    """
    try:
        if sentiment > 0.2:
            # Green for positive
            return f"rgba(39, 174, 96, {opacity})"
        elif sentiment < -0.2:
            # Red for negative
            return f"rgba(231, 76, 60, {opacity})"
        else:
            # Gray for neutral
            return f"rgba(108, 117, 125, {opacity})"
    except Exception as e:
        log_error_with_context(logger, e, "getting color for sentiment", 
                             sentiment=sentiment, opacity=opacity)
        return f"rgba(108, 117, 125, {opacity})"

def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes
    
    Args:
        file_path: Path to file
    
    Returns:
        File size in MB
    """
    try:
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        return 0.0
    except Exception as e:
        log_error_with_context(logger, e, "getting file size", file_path=file_path)
        return 0.0

def create_metric_dict(title: str, value: str, status: str = "neutral", 
                      subtitle: str = "", delta: str = "") -> Dict[str, str]:
    """
    Create a standardized metric dictionary for display
    
    Args:
        title: Metric title
        value: Metric value
        status: Status class (positive, negative, neutral, warning)
        subtitle: Optional subtitle
        delta: Optional delta/change value
    
    Returns:
        Formatted metric dictionary
    """
    return {
        'title': title,
        'value': value,
        'status': status,
        'subtitle': subtitle,
        'delta': delta
    }

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    try:
        # Remove or replace unsafe characters
        unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = filename
        
        for char in unsafe_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized
        
    except Exception as e:
        log_error_with_context(logger, e, "sanitizing filename", filename=filename)
        return "sanitized_file"
