"""
Base Configuration for Multi-Region Trading System

This module contains configuration settings that are common across all regions.
Region-specific configurations will override or extend these base settings.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import time

@dataclass 
class BaseConfig:
    """Base configuration class with universal trading system settings"""
    
    # Technical Indicators Base Parameters
    TECHNICAL_INDICATORS = {
        "RSI": {
            "period": 14,
            "overbought": 70,
            "oversold": 30,
            "smoothing_period": 3
        },
        "MACD": {
            "fast": 12,
            "slow": 26,
            "signal": 9,
            "histogram_threshold": 0.01
        },
        "BOLLINGER_BANDS": {
            "period": 20,
            "std_multiplier": 2,
            "squeeze_threshold": 0.1
        },
        "MOVING_AVERAGES": {
            "short_period": 20,
            "medium_period": 50,
            "long_period": 200
        },
        "VOLUME": {
            "average_period": 30,
            "spike_multiplier": 2.0,
            "low_volume_threshold": 0.5
        }
    }
    
    # Risk Assessment Base Parameters
    RISK_PARAMETERS = {
        "volatility": {
            "low_threshold": 0.015,      # 1.5% daily volatility
            "medium_threshold": 0.025,   # 2.5% daily volatility  
            "high_threshold": 0.040,     # 4.0% daily volatility
            "calculation_period": 30     # 30 days for volatility calculation
        },
        "volume": {
            "normal_threshold": 1.0,     # 1x average volume
            "high_threshold": 1.5,       # 1.5x average volume
            "very_high_threshold": 2.5,  # 2.5x average volume
            "calculation_period": 30     # 30 days for volume average
        },
        "price_movement": {
            "small_change": 0.02,        # 2% price change
            "medium_change": 0.05,       # 5% price change
            "large_change": 0.10,        # 10% price change
            "extreme_change": 0.15       # 15% price change
        }
    }
    
    # Machine Learning Base Configuration
    ML_CONFIG_BASE = {
        "feature_engineering": {
            "technical_features": [
                "rsi", "macd", "bollinger_bands", "moving_averages",
                "volume_ratio", "price_momentum", "volatility"
            ],
            "sentiment_features": [
                "sentiment_score", "news_volume", "news_quality",
                "social_sentiment", "analyst_sentiment"
            ],
            "market_features": [
                "market_sentiment", "sector_performance", "index_correlation",
                "currency_strength", "interest_rates"
            ],
            "fundamental_features": [
                "pe_ratio", "book_value", "dividend_yield",
                "earnings_growth", "revenue_growth"
            ]
        },
        "model_base_params": {
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "min_samples_leaf": 2,
                "random_state": 42
            },
            "gradient_boosting": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 6,
                "subsample": 0.8,
                "random_state": 42
            },
            "neural_network": {
                "hidden_layer_sizes": [100, 50, 25],
                "activation": "relu",
                "solver": "adam",
                "alpha": 0.001,
                "random_state": 42
            }
        },
        "training_params": {
            "test_size": 0.2,
            "validation_size": 0.1,
            "cv_folds": 5,
            "scoring": ["accuracy", "precision", "recall", "f1"],
            "random_state": 42
        },
        "performance_thresholds": {
            "minimum_accuracy": 0.60,
            "minimum_precision": 0.55,
            "minimum_recall": 0.55,
            "minimum_f1": 0.55,
            "overfitting_threshold": 0.1
        }
    }
    
    # Data Quality Base Parameters
    DATA_QUALITY = {
        "news_quality": {
            "minimum_article_length": 100,
            "maximum_article_age_hours": 48,
            "minimum_relevance_score": 0.3,
            "duplicate_similarity_threshold": 0.85
        },
        "market_data_quality": {
            "maximum_data_age_minutes": 15,
            "minimum_volume_threshold": 1000,
            "price_anomaly_threshold": 0.20,  # 20% price jump threshold
            "missing_data_tolerance": 0.05    # 5% missing data tolerance
        },
        "sentiment_quality": {
            "minimum_confidence": 0.6,
            "source_diversity_minimum": 3,
            "maximum_sentiment_age_hours": 24
        }
    }
    
    # Cache Configuration
    CACHE_CONFIG = {
        "market_data_ttl": 300,      # 5 minutes
        "news_data_ttl": 1800,       # 30 minutes
        "sentiment_data_ttl": 3600,  # 1 hour
        "ml_predictions_ttl": 7200,  # 2 hours
        "configuration_ttl": 86400   # 24 hours
    }
    
    # API Rate Limiting
    RATE_LIMITS = {
        "market_data_api": {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "burst_allowance": 10
        },
        "news_api": {
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "burst_allowance": 5
        },
        "prediction_api": {
            "requests_per_minute": 120,
            "requests_per_hour": 2000,
            "burst_allowance": 20
        }
    }
    
    # Logging Configuration
    LOGGING_CONFIG = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "max_file_size": "100MB",
        "backup_count": 5,
        "rotation": "daily"
    }
    
    # Database Configuration
    DATABASE_CONFIG = {
        "connection_pool_size": 10,
        "connection_timeout": 30,
        "query_timeout": 60,
        "retry_attempts": 3,
        "backup_frequency": "daily"
    }
    
    # Monitoring and Alerting
    MONITORING_CONFIG = {
        "health_check_interval": 300,  # 5 minutes
        "performance_metrics_interval": 60,  # 1 minute
        "alert_thresholds": {
            "error_rate": 0.05,        # 5% error rate
            "response_time": 5000,     # 5 seconds
            "memory_usage": 0.85,      # 85% memory usage
            "cpu_usage": 0.80          # 80% CPU usage
        }
    }

# News Source Quality Tiers (Universal Framework)
NEWS_SOURCE_TIERS = {
    "tier_1": {
        "description": "Government & Central Bank Sources",
        "quality_score": 1.0,
        "update_frequency": 60,  # minutes
        "reliability": "highest"
    },
    "tier_2": {
        "description": "Major Financial Media",
        "quality_score": 0.85,
        "update_frequency": 30,  # minutes
        "reliability": "high"
    },
    "tier_3": {
        "description": "General Business News",
        "quality_score": 0.70,
        "update_frequency": 45,  # minutes
        "reliability": "medium-high"
    },
    "tier_4": {
        "description": "Specialized Financial Sources",
        "quality_score": 0.60,
        "update_frequency": 60,  # minutes
        "reliability": "medium"
    },
    "tier_5": {
        "description": "Social Media & Community",
        "quality_score": 0.40,
        "update_frequency": 120,  # minutes
        "reliability": "low"
    }
}

# Universal Financial Sectors
FINANCIAL_SECTORS = {
    "banking": {
        "description": "Commercial and Investment Banks",
        "keywords": ["bank", "banking", "credit", "loan", "mortgage", "deposit"],
        "risk_profile": "medium"
    },
    "insurance": {
        "description": "Insurance Companies",
        "keywords": ["insurance", "insurer", "underwriting", "premium", "claims"],
        "risk_profile": "low-medium"
    },
    "investment": {
        "description": "Investment and Asset Management",
        "keywords": ["investment", "fund", "asset management", "portfolio", "wealth"],
        "risk_profile": "medium-high"
    },
    "fintech": {
        "description": "Financial Technology Companies",
        "keywords": ["fintech", "digital banking", "payments", "blockchain", "crypto"],
        "risk_profile": "high"
    },
    "real_estate": {
        "description": "Real Estate Investment Trusts",
        "keywords": ["REIT", "real estate", "property", "commercial property"],
        "risk_profile": "medium"
    }
}

# Currency Information (for multi-region support)
CURRENCIES = {
    "AUD": {"name": "Australian Dollar", "symbol": "A$", "decimal_places": 2},
    "USD": {"name": "US Dollar", "symbol": "$", "decimal_places": 2},
    "GBP": {"name": "British Pound", "symbol": "£", "decimal_places": 2},
    "JPY": {"name": "Japanese Yen", "symbol": "¥", "decimal_places": 0},
    "EUR": {"name": "Euro", "symbol": "€", "decimal_places": 2},
    "CAD": {"name": "Canadian Dollar", "symbol": "C$", "decimal_places": 2}
}

# Time Zone Information
TIMEZONES = {
    "Australia/Sydney": {"offset": "+10:00", "dst": True},
    "America/New_York": {"offset": "-05:00", "dst": True},
    "Europe/London": {"offset": "+00:00", "dst": True},
    "Asia/Tokyo": {"offset": "+09:00", "dst": False},
    "America/Toronto": {"offset": "-05:00", "dst": True}
}

def get_base_config() -> BaseConfig:
    """Get base configuration instance"""
    return BaseConfig()

def validate_region_config(region_config: Dict[str, Any]) -> List[str]:
    """
    Validate that a region configuration has all required sections
    Returns list of missing sections
    """
    required_sections = [
        "MARKET_CONFIG",
        "NEWS_SOURCES", 
        "BANK_SYMBOLS",
        "TRADING_HOURS"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in region_config:
            missing_sections.append(section)
    
    return missing_sections

def merge_configs(base_config: Dict[str, Any], region_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge base configuration with region-specific configuration
    Region config takes priority over base config
    """
    merged = base_config.copy()
    
    for key, value in region_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Deep merge for dictionary values
            merged[key] = {**merged[key], **value}
        else:
            # Direct override for non-dict values
            merged[key] = value
    
    return merged
