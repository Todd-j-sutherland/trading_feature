# UK Region Configuration Module
from typing import Dict, Any

class UKConfig:
    """UK (London Stock Exchange) Configuration Class"""
    
    def __init__(self):
        self.config = UK_CONFIG
    
    def get_config(self) -> Dict[str, Any]:
        """Get UK configuration dictionary"""
        return self.config
    
    def get_market_symbols(self) -> Dict[str, list]:
        """Get UK market symbols"""
        return self.config["market_data"]["symbols"]
    
    def get_trading_hours(self) -> Dict[str, Any]:
        """Get UK trading hours"""
        return self.config["market_data"]["trading_hours"]

def get_uk_config() -> Dict[str, Any]:
    """Get UK configuration (fallback function)"""
    return UK_CONFIG

# UK (London Stock Exchange) Configuration
# For FTSE 100 and major UK financial institutions

UK_CONFIG = {
    "region": {
        "name": "UK",
        "code": "uk",
        "description": "United Kingdom - London Stock Exchange",
        "currency": "GBP",
        "timezone": "Europe/London"
    },
    
    "market_data": {
        "symbols": {
            # Major UK Banks (FTSE 100)
            "big4_banks": [
                "LLOY.L",   # Lloyds Banking Group
                "BARC.L",   # Barclays
                "RBS.L",    # NatWest Group (formerly RBS)
                "HSBA.L"    # HSBC Holdings
            ],
            
            # Additional major financial institutions
            "major_financial": [
                "STAN.L",   # Standard Chartered
                "CBUY.L",   # Cadbury (if listed)
                "PSON.L",   # Pearson
                "VOD.L",    # Vodafone
                "BP.L",     # BP
                "SHEL.L",   # Shell
                "AZN.L",    # AstraZeneca
                "ULVR.L"    # Unilever
            ],
            
            # FTSE 100 Index
            "market_indices": [
                "UKX.L",    # FTSE 100
                "MCX.L",    # FTSE 250
                "ASX.L"     # FTSE All-Share
            ]
        },
        
        "trading_hours": {
            "market_open": "08:00",
            "market_close": "16:30",
            "timezone": "Europe/London",
            "trading_days": [0, 1, 2, 3, 4],  # Monday-Friday
            "holidays": [
                "2024-01-01",  # New Year's Day
                "2024-03-29",  # Good Friday
                "2024-04-01",  # Easter Monday
                "2024-05-06",  # Early May Bank Holiday
                "2024-05-27",  # Spring Bank Holiday
                "2024-08-26",  # Summer Bank Holiday
                "2024-12-25",  # Christmas Day
                "2024-12-26"   # Boxing Day
            ]
        },
        
        "data_sources": {
            "primary_api": "alpha_vantage",
            "backup_apis": ["finnhub", "yahoo_finance"],
            "real_time_provider": "london_stock_exchange",
            "currency_api": "fixer_io"
        },
        
        "cache_settings": {
            "price_cache_ttl": 300,      # 5 minutes during trading
            "daily_cache_ttl": 3600,     # 1 hour for daily data
            "historical_cache_ttl": 86400 # 24 hours for historical
        }
    },
    
    "sentiment": {
        "news_sources": {
            "financial_news": [
                "https://feeds.skynews.com/feeds/rss/business.xml",
                "https://feeds.bbci.co.uk/news/business/rss.xml",
                "https://www.ft.com/rss/companies/financials",
                "https://www.reuters.com/rssfeed/businessNews",
                "https://www.telegraph.co.uk/business/rss.xml"
            ],
            
            "bank_specific": [
                "https://www.lloydsbankinggroup.com/news-and-insights/rss.xml",
                "https://newsroom.barclays.com/rss.xml",
                "https://www.natwestgroup.com/news/rss.xml",
                "https://www.hsbc.com/news-and-media/rss.xml"
            ],
            
            "market_analysis": [
                "https://www.investorschronicle.co.uk/feeds/rss",
                "https://www.thisismoney.co.uk/money/markets/index.html/rss",
                "https://www.sharesmagazine.co.uk/rss.xml"
            ]
        },
        
        "keywords": {
            "positive": [
                "profit", "growth", "bullish", "upgrade", "outperform",
                "dividend", "earnings beat", "strong results", "expansion",
                "merger", "acquisition", "positive outlook", "buy rating",
                "recovery", "resilient", "robust", "beat expectations"
            ],
            
            "negative": [
                "loss", "decline", "bearish", "downgrade", "underperform",
                "cut dividend", "earnings miss", "weak results", "layoffs",
                "regulatory", "fine", "scandal", "sell rating",
                "recession", "volatile", "uncertainty", "missed targets"
            ],
            
            "banking_specific": {
                "positive": [
                    "net interest margin", "loan growth", "credit quality",
                    "capital ratio", "tier 1", "stress test pass",
                    "digital banking", "fintech partnership", "cost savings"
                ],
                "negative": [
                    "bad debt", "loan losses", "compliance", "money laundering",
                    "regulatory capital", "stress test fail", "litigation",
                    "conduct risk", "operational risk"
                ]
            }
        },
        
        "big4_symbols": ["LLOY.L", "BARC.L", "RBS.L", "HSBA.L"],
        
        "cache_settings": {
            "sentiment_cache_ttl": 1800,  # 30 minutes
            "news_cache_ttl": 900         # 15 minutes
        }
    },
    
    "prediction": {
        "ml_config": {
            "model_types": ["ensemble", "lstm", "xgboost"],
            "features": [
                "technical_indicators", "sentiment_score", "volume_analysis",
                "market_correlation", "economic_indicators", "currency_strength"
            ],
            "training_period": 252,  # Trading days (1 year)
            "prediction_horizon": 5,  # 5 trading days
            "retrain_frequency": 30   # Days
        },
        
        "thresholds": {
            "buy_threshold": 0.65,
            "sell_threshold": 0.35,
            "strong_buy": 0.80,
            "strong_sell": 0.20
        },
        
        "risk_management": {
            "max_position_size": 0.1,    # 10% of portfolio
            "stop_loss": 0.05,           # 5%
            "take_profit": 0.15,         # 15%
            "diversification_limit": 0.4  # Max 40% in financial sector
        }
    },
    
    "paper_trading": {
        "initial_capital": 100000,  # £100,000
        "currency": "GBP",
        "commission": {
            "rate": 0.0012,     # 0.12% (typical UK broker)
            "minimum": 5.0,     # £5 minimum
            "maximum": 50.0     # £50 maximum
        },
        
        "trading_rules": {
            "max_daily_trades": 20,
            "max_position_value": 20000,  # £20,000 per position
            "allowed_order_types": ["market", "limit", "stop_loss"],
            "settlement_period": 2        # T+2 settlement
        }
    },
    
    "alerts": {
        "price_movement": {
            "threshold": 0.05,    # 5% price movement
            "timeframe": "1h"     # Within 1 hour
        },
        
        "volume_spike": {
            "multiplier": 3.0,    # 3x average volume
            "timeframe": "30m"    # Within 30 minutes
        },
        
        "sentiment_change": {
            "threshold": 0.3,     # 30% sentiment change
            "timeframe": "2h"     # Within 2 hours
        }
    },
    
    "regulatory": {
        "data_retention": 2555,   # 7 years in days (FCA requirement)
        "reporting_frequency": "daily",
        "compliance_checks": ["MiFID_II", "FCA_rules", "GDPR"],
        "audit_trail": True
    }
}
